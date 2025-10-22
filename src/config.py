# src/config.py

import os
import sys  # <--- ADICIONE ESTA LINHA
from dotenv import load_dotenv

load_dotenv()

# --- Caminhos Essenciais do Projeto ---
# Define o diretório raiz do projeto, funcionando tanto como script quanto como .exe
if getattr(sys, 'frozen', False):
    PROJECT_ROOT = os.path.dirname(sys.executable)
else:
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Caminho para a pasta de templates
TEMPLATES_PATH = os.path.join(PROJECT_ROOT, "templates")

# --- Modelos da OpenAI ---
# Mantemos o modelo de LLM, pois ainda é usado para a análise
LLM_MODEL = "gpt-4o"

# --- Chave de API ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("A variável de ambiente OPENAI_API_KEY não foi definida. Crie um arquivo .env e adicione-a.")