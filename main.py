import sys
import os
import traceback
from tkinter import messagebox
from dotenv import load_dotenv

# --- BLOCO DE CONFIGURAÇÃO DE CAMINHOS ---
# Este bloco define o 'base_path', que é a pasta raiz da aplicação,
# funcionando tanto como script (.py) quanto como executável (.exe).

if getattr(sys, 'frozen', False):
    # Rodando como executável compilado pelo PyInstaller
    base_path = os.path.dirname(sys.executable)
else:
    # Rodando como um script Python normal
    base_path = os.path.dirname(os.path.abspath(__file__))

# 1. Carrega o arquivo .env a partir do caminho base
dotenv_path = os.path.join(base_path, '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)

# 2. Define a variável de ambiente para as credenciais do Google
google_creds_path = os.path.join(base_path, 'google_credentials.json')
if os.path.exists(google_creds_path):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = google_creds_path
else:
    # A ausência deste arquivo será tratada dentro do serviço de transcrição,
    # mas um aviso no console pode ajudar na depuração.
    print(f"AVISO: O arquivo 'google_credentials.json' não foi encontrado em {google_creds_path}")

# --- FIM DO BLOCO DE CONFIGURAÇÃO ---


# Importa a GUI somente APÓS a configuração das variáveis de ambiente.
from src.gui import App

if __name__ == "__main__":
    try:
        app = App()
        app.mainloop()
    except Exception as e:
        # Cria uma mensagem de erro detalhada para facilitar a depuração
        error_message = f"Ocorreu um erro fatal e a aplicação precisa ser fechada.\n\n"
        error_message += f"Erro: {str(e)}\n\n"
        error_message += f"Detalhes Técnicos:\n{traceback.format_exc()}"
        
        # Exibe a mensagem de erro em uma caixa de diálogo
        messagebox.showerror("Erro Crítico - Business Analyst Copilot", error_message)
        sys.exit(1) # Encerra o processo com um código de erro