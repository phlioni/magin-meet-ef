# src/services/database_operations.py

import os
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_unstructured.document_loaders import UnstructuredLoader

def get_text_from_file(file_path: str) -> str:
    """
    Extrai o conteúdo de texto de um único arquivo suportado (PDF, TXT, etc.).
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"O arquivo especificado não foi encontrado: {file_path}")

    try:
        # Usa a extensão para determinar o loader apropriado
        ext = os.path.splitext(file_path)[1].lower()

        if ext in [".txt", ".md"]:
            loader = TextLoader(file_path, encoding='utf-8')
        elif ext == ".pdf":
            loader = PyPDFLoader(file_path)
        else:
            # O UnstructuredLoader é ótimo para lidar com outros formatos (docx, xlsx, etc.)
            loader = UnstructuredLoader(file_path)

        documents = loader.load()
        full_text = "\n".join(doc.page_content for doc in documents)
        return full_text
    except Exception as e:
        print(f"[ERRO] Falha ao extrair texto do arquivo {file_path}: {e}")
        # Retorna uma string de erro em vez de levantar uma exceção para não parar o fluxo principal
        return f"Erro ao processar o arquivo {os.path.basename(file_path)}."