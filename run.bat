@echo off
title Business Analyst Copilot - Verificador e Inicializador

:: Etapa 1: Verificar se a versão CORRETA do Python está instalada.
echo Verificando instalacao do Python...
python --version 2>&1 | findstr "Python 3" >nul
IF ERRORLEVEL 1 (
    echo.
    echo --------------------------------------------------------------------
    echo  ERRO: Python nao encontrado!
    echo.
    echo  Esta aplicacao requer Python 3.8+ para funcionar.
    echo  Por favor, instale a versao mais recente a partir do site oficial:
    echo  https://www.python.org/downloads/
    echo.
    echo  IMPORTANTE: Na instalacao, marque a caixa "Add Python to PATH".
    echo --------------------------------------------------------------------
    echo.
    pause
    exit /b
)
echo Python encontrado!
echo.

:: Etapa 2: Criar venv se não existir
IF NOT EXIST venv (
    echo Criando ambiente virtual...
    python -m venv venv
)

:: Etapa 3: Instalar dependências
echo Verificando e instalando dependencias...
echo (Este processo pode levar alguns minutos na primeira vez)
.\venv\Scripts\pip.exe install -r requirements.txt

:: Etapa 4: Rodar a aplicação
echo Iniciando Business Analyst Copilot...
.\venv\Scripts\python.exe main.py