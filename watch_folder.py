import os
import sys
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Adiciona o diretório raiz do projeto ao path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.config import HOT_FOLDER_PATH
# --- LINHA CORRIGIDA ---
# O import agora inclui o caminho completo a partir de 'src'
from src.services.database_operations import process_and_add_file_to_db

class NewFileHandler(FileSystemEventHandler):
    """Um handler de eventos para quando novos arquivos são criados."""
    def on_created(self, event):
        if not event.is_directory:
            # Ignora arquivos ocultos
            if os.path.basename(event.src_path).startswith('.'):
                return
            
            print(f"\n[DETECÇÃO] Novo arquivo detectado: {event.src_path}")
            # Aguarda um pouco para garantir que o arquivo foi completamente escrito no disco
            time.sleep(2)
            process_and_add_file_to_db(event.src_path)

def start_monitoring():
    """Inicia o monitoramento da hot folder."""
    # Garante que a hot folder exista
    os.makedirs(HOT_FOLDER_PATH, exist_ok=True)

    event_handler = NewFileHandler()
    observer = Observer()
    observer.schedule(event_handler, HOT_FOLDER_PATH, recursive=False)

    print("="*50)
    print("🚀 MONITORAMENTO ATIVO 🚀")
    print(f"Observando a pasta: {os.path.abspath(HOT_FOLDER_PATH)}")
    print("Qualquer novo arquivo adicionado aqui será processado automaticamente.")
    print("Pressione CTRL+C para parar.")
    print("="*50)

    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[INFO] Monitoramento interrompido pelo usuário.")
        observer.stop()
    observer.join()

if __name__ == "__main__":
    start_monitoring()