import os
# A importação do UnstructuredFileLoader foi removida daqui
from langchain_community.document_loaders import PyPDFLoader, TextLoader
# ADICIONADO: Nova importação recomendada pelo LangChain
from langchain_unstructured.document_loaders import UnstructuredLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from src.config import CHROMA_DB_PATH, EMBEDDING_MODEL

# O LOADER_MAPPING não é mais necessário para esta lógica

def get_text_from_file(file_path: str) -> str:
    """
    Extrai o conteúdo de texto de um único arquivo suportado (PDF, TXT, XLSX, etc.).
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"O arquivo especificado não foi encontrado: {file_path}")

    try:
        ext = "." + file_path.rsplit(".", 1)[-1].lower()
        
        if ext in [".txt", ".md", ".mdx"]:
            loader = TextLoader(file_path, encoding='utf-8')
        elif ext == ".pdf":
            loader = PyPDFLoader(file_path)
        else:
            # ALTERADO: Usando o novo UnstructuredLoader
            loader = UnstructuredLoader(file_path)
        
        documents = loader.load()
        full_text = "\n".join(doc.page_content for doc in documents)
        return full_text
    except Exception as e:
        print(f"[ERRO] Falha ao extrair texto do arquivo {file_path}: {e}")
        raise


def get_vector_store() -> Chroma:
    """Inicializa e retorna o Vector Store a partir do disco."""
    embeddings_model = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    vector_store = Chroma(
        persist_directory=CHROMA_DB_PATH,
        embedding_function=embeddings_model
    )
    return vector_store

def process_and_add_file_to_db(file_path: str):
    """
    Processa um único arquivo e o adiciona ao Vector Database.
    """
    try:
        content = get_text_from_file(file_path)
        if not content:
            print(f"-> [AVISO] Nenhum conteúdo textual extraído de: {os.path.basename(file_path)}")
            return
        
        from langchain_core.documents import Document
        documents = [Document(page_content=content)]
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1200,
            chunk_overlap=200,
            length_function=len
        )
        chunks = text_splitter.split_documents(documents)
        
        vector_store = get_vector_store()
        vector_store.add_documents(chunks)
        
        print(f"-> [SUCESSO] Arquivo '{os.path.basename(file_path)}' adicionado.")

    except Exception as e:
        print(f"Não foi possível adicionar o arquivo {os.path.basename(file_path)} ao banco de dados.")
        print(f"❌ ERRO DETALHADO: {e}")