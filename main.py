import sys
import os
import traceback
from tkinter import messagebox
from dotenv import load_dotenv

# --- BLOCO DE CONFIGURAÇÃO DE CAMINHOS ---
# Este bloco define o 'base_path', que é a pasta raiz da aplicação.

if getattr(sys, 'frozen', False):
    # Rodando como executável (.exe)
    base_path = os.path.dirname(sys.executable)
    # Define o caminho para os navegadores do Playwright
    os.environ['PLAYWRIGHT_BROWSERS_PATH'] = os.path.join(base_path, '.local-browsers')
else:
    # Rodando como script (.py)
    base_path = os.path.dirname(os.path.abspath(__file__))


# 1. Carrega o arquivo .env
dotenv_path = os.path.join(base_path, '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)

# 2. Define a variável de ambiente para as credenciais do Google
google_creds_path = os.path.join(base_path, 'google_credentials.json')
if os.path.exists(google_creds_path):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = google_creds_path
else:
    # Este é um fallback, o erro principal será capturado na própria aplicação
    print(f"AVISO: O arquivo de credenciais do Google não foi encontrado em {google_creds_path}")

# --- FIM DO BLOCO DE CONFIGURAÇÃO ---


# Importa a GUI somente APÓS a configuração das variáveis.
from src.gui import App

if __name__ == "__main__":
    try:
        app = App()
        app.mainloop()
    except Exception as e:
        error_message = f"Ocorreu um erro fatal e a aplicação precisa ser fechada.\n\n"
        error_message += f"Erro: {str(e)}\n\n"
        error_message += f"Detalhes Técnicos:\n{traceback.format_exc()}"
        messagebox.showerror("Erro Crítico - Magic Meet Copilot", error_message)
        sys.exit(1)