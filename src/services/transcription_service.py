# src/services/transcription_service.py

import os
from google.cloud import speech
import sounddevice as sd  # <-- USA A BIBLIOTECA CORRETA
import queue
import threading
from dotenv import load_dotenv

def set_google_credentials():
    # Esta função é chamada pelo main.py
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not credentials_path or not os.path.exists(credentials_path):
         print("❌ AVISO: GOOGLE_APPLICATION_CREDENTIALS não configurada corretamente.")

class TranscriptionService:
    def __init__(self, on_transcription_update):
        self.client = None
        self.on_transcription_update = on_transcription_update
        self._buff = queue.Queue()
        self.is_running = False
        self.thread = None
        self.stream = None
        self.final_transcripts = []

    def _audio_generator(self):
        while self.is_running:
            chunk = self._buff.get()
            if chunk is None:
                return
            yield speech.StreamingRecognizeRequest(audio_content=chunk)

    def _listen_print_loop(self, responses):
        try:
            for response in responses:
                if not self.is_running: break
                if not response.results: continue
                result = response.results[0]
                if not result.alternatives: continue
                
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
                print(f"❌ Erro ao processar resposta do Google: {e}")
            self.stop_streaming()

    def start_streaming(self):
        if self.is_running: return
        self.final_transcripts = []
        self.is_running = True
        self.thread = threading.Thread(target=self._run)
        self.thread.daemon = True
        self.thread.start()

    def stop_streaming(self):
        if not self.is_running: return
        self.is_running = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        self._buff.put(None)

    def _run(self):
        try:
            self.client = speech.SpeechClient()
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code="pt-BR",
                enable_automatic_punctuation=True
            )
            streaming_config = speech.StreamingRecognitionConfig(
                config=config, interim_results=True
            )
            
            def audio_callback(indata, frames, time, status):
                if status:
                    print(f"Status do áudio: {status}")
                self._buff.put(bytes(indata))

            samplerate = 16000
            print("🎤 Tentando abrir o microfone padrão com sounddevice...")
            self.stream = sd.RawInputStream(
                samplerate=samplerate,
                blocksize=4096,
                channels=1,
                dtype='int16',
                callback=audio_callback
            )
            
            with self.stream:
                print("✅ Microfone aberto. Iniciando comunicação com o Google...")
                audio_stream_generator = self._audio_generator()
                requests = (req for req in audio_stream_generator)
                responses = self.client.streaming_recognize(streaming_config, requests)
                print("✅ Comunicação estabelecida. Ouvindo...")
                self._listen_print_loop(responses)

        except Exception as e:
            print(f"❌ Erro fatal na thread de transcrição: {e}")
            self.on_transcription_update(f"[ERRO DE MICROFONE]: {e}\nVerifique se um microfone está conectado e permitido.")
        finally:
            print("-> Thread de transcrição finalizada.")
            self.is_running = False