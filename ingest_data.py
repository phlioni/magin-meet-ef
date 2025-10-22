import os
import sys
import argparse

# Adiciona o diretório raiz do projeto ao path para poder importar de 'src'
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# --- LINHA CORRIGIDA ---
# O import agora inclui o caminho completo a partir de 'src'
from src.services.database_operations import process_and_add_file_to_db
from src.config import CHROMA_DB_PATH

def main(data_folder: str):
    """
    Script para a ingestão inicial em massa de documentos.
    Lê todos os arquivos de um diretório especificado e os adiciona ao DB.
    """
    if not os.path.isdir(data_folder):
        print(f"[ERRO] O caminho especificado não é um diretório válido: {data_folder}")
        return

    print(f"Iniciando a ingestão de dados do diretório: {data_folder}")
    print(f"Banco de dados será salvo em: {CHROMA_DB_PATH}")

    # Garante que o diretório do DB exista
    os.makedirs(CHROMA_DB_PATH, exist_ok=True)

    files_to_process = []
    for root, _, filenames in os.walk(data_folder):
        for filename in filenames:
            # Ignora arquivos ocultos (ex: .DS_Store)
            if not filename.startswith('.'):
                files_to_process.append(os.path.join(root, filename))

    if not files_to_process:
        print(f"[AVISO] Nenhum arquivo encontrado no diretório especificado: {data_folder}")
        return

    total_files = len(files_to_process)
    print(f"Total de {total_files} arquivos encontrados. Iniciando processamento...")

    for i, file_path in enumerate(files_to_process):
        print(f"\n--- Processando arquivo {i+1}/{total_files} ---")
        process_and_add_file_to_db(file_path)

    print("\n[SUCESSO] Ingestão inicial de dados concluída!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script de ingestão de dados em massa para a base de conhecimento RAG."
    )
    parser.add_argument(
        "data_folder",
        type=str,
        help="O caminho completo para a pasta contendo os arquivos iniciais (PDFs, TXT, etc.)."
    )
    args = parser.parse_args()
    main(args.data_folder)