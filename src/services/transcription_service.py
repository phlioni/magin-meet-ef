# src/services/transcription_service.py
# Estratégia: dois streams (mic via sounddevice + sistema via PyAudioWPatch WASAPI loopback)
# com mixagem PCM em thread dedicada. Saída única 16 kHz mono para Google Speech-to-Text.

import os
import sys
import queue
import threading
import time
import numpy as np
from dotenv import load_dotenv

import sounddevice as sd
from google.cloud import speech

load_dotenv()

# Constantes de áudio
SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_DURATION_MS = 100
CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION_MS / 1000)
GOOGLE_STREAM_LIMIT_SECONDS = 290


def list_audio_devices():
    """Lista dispositivos de entrada (microfones e Stereo Mix / Mixagem Estéreo)."""
    devices = []
    try:
        sd_devices = sd.query_devices()
        for i, dev in enumerate(sd_devices):
            if dev['max_input_channels'] > 0:
                name_lower = dev['name'].lower()
                if 'mapeador' in name_lower or 'mapper' in name_lower:
                    continue
                # Incluir Stereo Mix / Mixagem Estéreo (entrada que captura saída do sistema)
                if 'output' in name_lower and 'stereo mix' not in name_lower and 'mixagem estéreo' not in name_lower:
                    continue
                is_loopback = 'stereo mix' in name_lower or 'mixagem estéreo' in name_lower
                devices.append({
                    'index': i,
                    'name': dev['name'][:50],
                    'is_loopback': is_loopback,
                    'source': 'sounddevice',
                    'hostapi': dev.get('hostapi', -1),
                })
    except Exception as e:
        print(f"Erro ao listar dispositivos sounddevice: {e}")
    return devices


def list_loopback_devices():
    """Lista dispositivos WASAPI loopback (áudio do sistema) no Windows via PyAudioWPatch."""
    devices = []
    try:
        import pyaudiowpatch as pyaudio
        with pyaudio.PyAudio() as p:
            wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
            default_speakers = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
            if not default_speakers.get("isLoopbackDevice"):
                for loopback in p.get_loopback_device_info_generator():
                    if default_speakers["name"] in loopback["name"]:
                        default_speakers = loopback
                        break
            if default_speakers.get("isLoopbackDevice"):
                devices.append({
                    'index': int(default_speakers["index"]),
                    'name': default_speakers["name"][:50],
                    'is_loopback': True,
                    'source': 'pyaudiowpatch',
                    'defaultSampleRate': int(default_speakers["defaultSampleRate"]),
                    'maxInputChannels': int(default_speakers["maxInputChannels"]),
                })
            for loopback in p.get_loopback_device_info_generator():
                idx = int(loopback["index"])
                if any(d['index'] == idx for d in devices):
                    continue
                devices.append({
                    'index': idx,
                    'name': loopback["name"][:50],
                    'is_loopback': True,
                    'source': 'pyaudiowpatch',
                    'defaultSampleRate': int(loopback["defaultSampleRate"]),
                    'maxInputChannels': int(loopback["maxInputChannels"]),
                })
    except OSError:
        pass  # WASAPI não disponível (ex.: não Windows)
    except Exception as e:
        print(f"Erro ao listar dispositivos loopback (PyAudioWPatch): {e}")
    return devices


class TranscriptionService:
    def __init__(self, on_transcription_update, on_error=None, on_audio_level=None):
        self.client = None
        self.on_transcription_update = on_transcription_update
        self.on_error = on_error
        self.on_audio_level = on_audio_level
        self._audio_buff = queue.Queue()
        self.is_running = False
        self.thread = None
        self.audio_stream = None
        self.final_transcripts = []
        self.mic_device_index = None
        # Captura mic + sistema (dois streams + mixagem)
        self.capture_system_audio = False
        self.system_device_index = None
        self._system_device_info = None  # dict com defaultSampleRate, maxInputChannels
        self._mic_queue = None
        self._system_queue = None
        self._system_raw_queue = queue.Queue()
        self._pyaudio_instance = None
        self._system_stream = None
        self._system_thread = None
        self._mixer_thread = None
        self._system_buffer = bytearray()

    def set_audio_source(self, mic_device_index=None, system_device_index=None, capture_system_audio=False, system_device_info=None):
        self.mic_device_index = mic_device_index
        self.system_device_index = system_device_index
        self.capture_system_audio = bool(capture_system_audio)
        self._system_device_info = system_device_info

    def _audio_generator(self):
        while self.is_running:
            try:
                audio_chunk = self._audio_buff.get(timeout=0.2)
                yield speech.StreamingRecognizeRequest(audio_content=audio_chunk)
            except queue.Empty:
                pass

    def _listen_print_loop(self, responses):
        try:
            for response in responses:
                if not self.is_running:
                    break
                if not response.results:
                    continue
                result = response.results[0]
                if not result.alternatives:
                    continue

                transcript = result.alternatives[0].transcript

                if result.is_final:
                    self.final_transcripts.append(transcript)
                    full_text = " ".join(self.final_transcripts) + " "
                    self.on_transcription_update(full_text)
                else:
                    temp_text = " ".join(self.final_transcripts) + " " + transcript
                    self.on_transcription_update(temp_text)
        except Exception as e:
            if self.is_running:
                error_msg = str(e).lower()
                if "time exceeded" in error_msg or "out of range" in error_msg:
                    print("⏰ Stream atingiu o limite de tempo. Reconectando...")
                    return
                if "503" in error_msg or "unavailable" in error_msg:
                    print("⚠️ Serviço do Google instável (503). Tentando reconectar...")
                    return
                
                print(f"❌ Erro ao processar resposta do Google: {e}")
                if self.on_error:
                    self.on_error(f"Erro na transcrição: {e}")

    def start_streaming(self):
        if self.is_running:
            return
        self.final_transcripts = []
        self.is_running = True
        self._audio_buff = queue.Queue()
        self.thread = threading.Thread(target=self._run_with_reconnection)
        self.thread.daemon = True
        self.thread.start()

    def stop_streaming(self):
        if not self.is_running:
            return
        self.is_running = False
        self._stop_audio_streams()

    def _run_with_reconnection(self):
        try:
            try:
                self.client = speech.SpeechClient()
                has_cloud_client = True
            except Exception as e:
                print(f"⚠️ Aviso: Não foi possível conectar ao Google Cloud ({e}). O VU meter funcionará, mas sem transcrição.")
                if self.on_error:
                    self.on_error("API Google Speech indisponível. Capturando áudio apenas para teste.")
                has_cloud_client = False

            self._start_audio_streams()

            while self.is_running:
                try:
                    if has_cloud_client:
                        self._run_single_stream()
                    else:
                        try:
                            self._audio_buff.get(timeout=1.0)
                        except queue.Empty:
                            pass
                except Exception as e:
                    if not self.is_running:
                        break
                    error_msg = str(e)
                    if "time exceeded" in error_msg.lower() or "out of range" in error_msg.lower():
                        print("🔄 Reconectando stream de transcrição...")
                        time.sleep(0.3)
                        continue
                    elif "403" in error_msg:
                        has_cloud_client = False
                        print(f"❌ Erro de permissão Google API (Billing?). Entrando em modo Teste Local.")
                        if self.on_error:
                            self.on_error("Erro de Faturamento Google (403). Áudio local ativo.")
                    else:
                        raise

        except Exception as e:
            print(f"❌ Erro fatal na thread de transcrição: {e}")
            if self.on_error:
                self.on_error(f"Erro fatal: {e}")
            self.on_transcription_update(f"[ERRO DE ÁUDIO]: {e}\nVerifique se o dispositivo está correto.")
        finally:
            self._stop_audio_streams()
            print("-> Thread de transcrição finalizada.")
            self.is_running = False

    def _start_audio_streams(self):
        if self.capture_system_audio:
            self._mic_queue = queue.Queue()
            self._system_queue = queue.Queue()
            self._system_buffer = bytearray()
            self._start_system_loopback_stream()
        use_mixer = self.capture_system_audio

        if use_mixer:
            self._mixer_thread = threading.Thread(target=self._run_mixer_thread, daemon=True)
            self._mixer_thread.start()

        print("🎤 Abrindo dispositivo de áudio (microfone)...")
        audio_kwargs = {
            'samplerate': SAMPLE_RATE,
            'blocksize': CHUNK_SIZE,
            'channels': CHANNELS,
            'dtype': 'int16',
            'callback': self._audio_callback,
        }
        try:
            if self.mic_device_index is not None:
                audio_kwargs['device'] = self.mic_device_index
            self.audio_stream = sd.RawInputStream(**audio_kwargs)
            self.audio_stream.start()
            print("✅ Dispositivo de áudio (microfone) aberto.")
        except Exception as e:
            print(f"⚠️ Erro ao abrir dispositivo {self.mic_device_index}: {e}")
            print("🔄 Tentando usar o dispositivo padrão do sistema (Fallback)...")
            self.mic_device_index = None
            audio_kwargs.pop('device', None)
            try:
                self.audio_stream = sd.RawInputStream(**audio_kwargs)
                self.audio_stream.start()
                print("✅ Dispositivo de áudio padrão aberto com sucesso.")
            except Exception as default_e:
                if use_mixer:
                    self._stop_system_loopback_stream()
                print(f"❌ Falha crítica ao abrir dispositivo: {default_e}")
                raise default_e

    def _start_system_loopback_stream(self):
        """Abre stream WASAPI loopback (PyAudioWPatch) e thread que resampleia para 16 kHz mono."""
        try:
            import pyaudiowpatch as pyaudio
            self._pyaudio_instance = pyaudio.PyAudio()
            info = self._system_device_info
            if not info:
                wasapi_info = self._pyaudio_instance.get_host_api_info_by_type(pyaudio.paWASAPI)
                default_speakers = self._pyaudio_instance.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
                if not default_speakers.get("isLoopbackDevice"):
                    for loopback in self._pyaudio_instance.get_loopback_device_info_generator():
                        if default_speakers["name"] in loopback["name"]:
                            default_speakers = loopback
                            break
                info = {
                    'index': int(default_speakers["index"]),
                    'defaultSampleRate': int(default_speakers["defaultSampleRate"]),
                    'maxInputChannels': int(default_speakers["maxInputChannels"]),
                }
            rate = info['defaultSampleRate']
            channels = info['maxInputChannels']
            device_index = self.system_device_index if self.system_device_index is not None else info['index']

            def callback(in_data, frame_count, time_info, status):
                if self.is_running and in_data:
                    self._system_raw_queue.put((bytes(in_data), rate, channels))
                return (in_data, pyaudio.paContinue)

            self._system_stream = self._pyaudio_instance.open(
                format=pyaudio.paInt16,
                channels=channels,
                rate=rate,
                frames_per_buffer=1024,
                input=True,
                input_device_index=device_index,
                stream_callback=callback,
            )
            self._system_stream.start_stream()
            self._system_thread = threading.Thread(target=self._run_system_resample_thread, args=(rate, channels), daemon=True)
            self._system_thread.start()
            print("✅ Áudio do sistema (loopback) aberto.")
        except Exception as e:
            print(f"⚠️ Erro ao abrir áudio do sistema (loopback): {e}")
            if self.on_error:
                self.on_error(f"Áudio do sistema indisponível: {e}. Apenas microfone será usado.")
            self.capture_system_audio = False

    def _run_system_resample_thread(self, rate, channels):
        """Lê do stream bruto, resampleia para 16 kHz mono, coloca em _system_queue."""
        # Para 100 ms a 16 kHz: 1600 amostras. Em rate original: rate/100 amostras. Ex: 48k -> 4800 frames.
        ratio = rate / SAMPLE_RATE  # ex: 3.0 para 48k -> 16k
        frame_size = int(CHUNK_SIZE * ratio)  # amostras mono equivalentes
        byte_per_frame = 2 * channels
        need_bytes = frame_size * byte_per_frame
        buf = bytearray()
        while self.is_running:
            try:
                data, r, ch = self._system_raw_queue.get(timeout=0.2)
                buf.extend(data)
            except queue.Empty:
                continue
            while len(buf) >= need_bytes:
                chunk = bytes(buf[:need_bytes])
                del buf[:need_bytes]
                arr = np.frombuffer(chunk, dtype=np.int16)
                if ch == 2:
                    arr = arr.reshape(-1, 2).mean(axis=1).astype(np.int16)
                if r != SAMPLE_RATE:
                    # Downsample: ex 48k -> 16k, ratio=3
                    step = r / SAMPLE_RATE
                    indices = (np.arange(CHUNK_SIZE) * step).astype(np.int64)
                    arr = arr[indices]
                self._system_queue.put(arr.tobytes())

    def _run_mixer_thread(self):
        """Combina chunks de microfone e sistema (com clipping) e coloca em _audio_buff."""
        while self.is_running:
            try:
                mic_chunk = self._mic_queue.get(timeout=0.2)
            except queue.Empty:
                continue
            try:
                system_chunk = self._system_queue.get_nowait()
            except queue.Empty:
                system_chunk = np.zeros(CHUNK_SIZE, dtype=np.int16).tobytes()
            mic_arr = np.frombuffer(mic_chunk, dtype=np.int16)
            sys_arr = np.frombuffer(system_chunk, dtype=np.int16)
            if len(sys_arr) < CHUNK_SIZE:
                sys_arr = np.pad(sys_arr, (0, CHUNK_SIZE - len(sys_arr)), constant_values=0)
            mixed = np.clip(mic_arr.astype(np.int32) + sys_arr[:CHUNK_SIZE].astype(np.int32), -32768, 32767).astype(np.int16)
            if self._audio_buff.qsize() > 10:
                try:
                    self._audio_buff.get_nowait()
                except queue.Empty:
                    pass
            self._audio_buff.put(mixed.tobytes())
            if self.on_audio_level:
                try:
                    rms = np.sqrt(np.mean(np.square(mixed.astype(np.float32)[::10])))
                    self.on_audio_level(rms)
                except Exception:
                    pass

    def _stop_system_loopback_stream(self):
        if getattr(self, '_system_thread') and self._system_thread:
            self._system_thread = None
        if getattr(self, '_system_stream') and self._system_stream:
            try:
                self._system_stream.stop_stream()
                self._system_stream.close()
            except Exception:
                pass
            self._system_stream = None
        if getattr(self, '_pyaudio_instance') and self._pyaudio_instance:
            try:
                self._pyaudio_instance.terminate()
            except Exception:
                pass
            self._pyaudio_instance = None

    def _stop_audio_streams(self):
        self._stop_system_loopback_stream()
        if hasattr(self, 'audio_stream') and self.audio_stream:
            try:
                self.audio_stream.stop()
                self.audio_stream.close()
            except Exception:
                pass
            self.audio_stream = None
        self._mic_queue = None
        self._system_queue = None

    def _run_single_stream(self):
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=SAMPLE_RATE,
            language_code="pt-BR",
            enable_automatic_punctuation=True,
            use_enhanced=True,
            model="latest_long",
        )
        streaming_config = speech.StreamingRecognitionConfig(
            config=config,
            interim_results=True,
        )

        while not self._audio_buff.empty():
            try: self._audio_buff.get_nowait()
            except queue.Empty: break

        print("🔗 Conectando ao Google Speech-to-Text...")
        audio_stream_generator = self._audio_generator()
        responses = self.client.streaming_recognize(streaming_config, audio_stream_generator)
        print("✅ Conexão estabelecida. Transcrevendo...")
        self._listen_print_loop(responses)

    def _audio_callback(self, indata, frames, time_info, status):
        if status:
            print(f"Status do áudio: {status}")
        if self.is_running:
            b_data = bytes(indata)
            if self.capture_system_audio and self._mic_queue is not None:
                self._mic_queue.put(b_data)
            else:
                if self._audio_buff.qsize() > 10:
                    try:
                        self._audio_buff.get_nowait()
                    except queue.Empty:
                        pass
                self._audio_buff.put(b_data)
                if self.on_audio_level:
                    try:
                        audio_data = np.frombuffer(b_data, dtype=np.int16)
                        rms = np.sqrt(np.mean(np.square(audio_data.astype(np.float32)[::10])))
                        self.on_audio_level(rms)
                    except Exception:
                        pass