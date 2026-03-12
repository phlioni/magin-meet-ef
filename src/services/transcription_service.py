# src/services/transcription_service.py

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
    devices = []
    try:
        sd_devices = sd.query_devices()
        for i, dev in enumerate(sd_devices):
            if dev['max_input_channels'] > 0:
                name_lower = dev['name'].lower()
                if 'mapeador' in name_lower or 'mapper' in name_lower:
                    continue
                if 'output' in name_lower and 'stereo mix' not in name_lower and 'mixagem estéreo' not in name_lower:
                    continue
                
                devices.append({
                    'index': i,
                    'name': dev['name'][:50],
                    'is_loopback': False,
                    'source': 'sounddevice',
                    'hostapi': dev.get('hostapi', -1),
                })
    except Exception as e:
        print(f"Erro ao listar dispositivos sounddevice: {e}")

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

    def set_audio_source(self, mic_device_index=None):
        self.mic_device_index = mic_device_index

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
        print("🎤 Abrindo dispositivo de áudio...")
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
            print("✅ Dispositivo de áudio aberto.")
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
                print(f"❌ Falha crítica ao abrir dispositivo: {default_e}")
                raise default_e

    def _stop_audio_streams(self):
        if hasattr(self, 'audio_stream') and self.audio_stream:
            try:
                self.audio_stream.stop()
                self.audio_stream.close()
            except Exception:
                pass
            self.audio_stream = None

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
            
            if self._audio_buff.qsize() > 10:
                try: self._audio_buff.get_nowait()
                except queue.Empty: pass
                
            self._audio_buff.put(b_data)
            
            if self.on_audio_level:
                try:
                    audio_data = np.frombuffer(b_data, dtype=np.int16)
                    rms = np.sqrt(np.mean(np.square(audio_data.astype(np.float32)[::10])))
                    self.on_audio_level(rms)
                except Exception:
                    pass