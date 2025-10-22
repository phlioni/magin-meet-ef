import os
from dotenv import load_dotenv

load_dotenv()

# Caminhos do Projeto
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CHROMA_DB_PATH = os.path.join(PROJECT_ROOT, "chroma_db")
HOT_FOLDER_PATH = os.path.join(PROJECT_ROOT, "hot_folder_for_rag")
TEMPLATES_PATH = os.path.join(PROJECT_ROOT, "templates")
OUTPUT_PROPOSALS_PATH = os.path.join(PROJECT_ROOT, "output_proposals")

# Modelos da OpenAI
EMBEDDING_MODEL = "text-embedding-3-small"
LLM_MODEL = "gpt-4o"

# Chave de API
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("A variável de ambiente OPENAI_API_KEY não foi definida. Crie um arquivo .env e adicione-a.")