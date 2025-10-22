@echo off
title Magic Meet Copilot - Verificador e Inicializador

:: Etapa 1: Verificar se a versão CORRETA do Python está instalada.
echo Verificando instalacao do Python 3.11...
python --version 2>&1 | findstr "Python 3.11" >nul
IF ERRORLEVEL 1 (
    echo.
    echo --------------------------------------------------------------------
    echo  ERRO: Python 3.11 nao encontrado!
    echo.
    echo  Esta aplicacao requer o Python 3.11 para funcionar corretamente.
    echo  Por favor, instale a versao correta a partir do site oficial:
    echo  https://www.python.org/downloads/release/python-3119/
    echo.
    echo  IMPORTANTE: Na instalacao, marque a caixa "Add Python to PATH".
    echo --------------------------------------------------------------------
  
    echo.
    pause
    exit /b
)
echo Python 3.11 encontrado!
echo.

:: Etapa 2: Criar venv se não existir
IF NOT EXIST venv (
    echo Criando ambiente virtual com Python 3.11...
    py -3.11 -m venv venv
)

:: Etapa 3: Instalar dependências
echo Verificando e instalando dependencias...
echo (Este processo pode levar alguns minutos na primeira vez)
.\venv\Scripts\pip.exe install -r requirements.txt
.\venv\Scripts\playwright.exe install

:: ETAPA 4: VERIFICAR E EXECUTAR A CARGA INICIAL (RAG) SE NECESSARIO
IF NOT EXIST chroma_db (
    echo.
    echo --------------------------------------------------------------------
    echo  PRIMEIRA EXECUCAO DETECTADA
    echo.
    echo  Vamos criar sua base de conhecimento (RAG) agora.
    echo  Processando os arquivos da pasta 'hot_folder_for_rag'...
    echo  Aguarde, este processo pode levar um tempo dependendo da
    echo  quantidade de arquivos.
    echo --------------------------------------------------------------------
    echo.
    
    :: Executa o script de ingestao, apontando para a pasta correta
    .\venv\Scripts\python.exe ingest_data.py "hot_folder_for_rag"
    
    echo.
    echo --------------------------------------------------------------------
    echo  Base de conhecimento criada com sucesso!
    echo --------------------------------------------------------------------
    echo.
)

:: Etapa 5: Rodar a aplicação
echo Iniciando Magic Meet Copilot...
.\venv\Scripts\python.exe main.py