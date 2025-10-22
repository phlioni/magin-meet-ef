@echo off
title Magic Meet Copilot - Builder

:: --- ETAPA DE SEGURANCA ---
:: Forca o encerramento de qualquer instancia anterior do programa que possa estar presa.
echo Encerrando qualquer processo antigo do MagicMeetCopilotPro...
taskkill /F /IM "MagicMeetCopilotPro.exe" /T >nul 2>&1

:: Pausa rapida para garantir que os arquivos foram liberados pelo sistema operacional.
timeout /t 2 /nobreak >nul

echo.
echo Limpando builds anteriores...
rmdir /s /q build
rmdir /s /q dist

echo.
echo Iniciando o processo de build com PyInstaller...
echo Este processo pode levar varios minutos.
:: Comando final com todas as correcoes (ChromaDB e Tiktoken)
.\venv\Scripts\pyinstaller.exe --noconfirm --log-level=INFO ^
    --name="MagicMeetCopilotPro" ^
    --windowed ^
    --add-data="%~dp0src;src" ^
    --add-data="%~dp0templates;templates" ^
    --add-data="%~dp0.env;." ^
    --add-data="%~dp0google_credentials.json;." ^
    --add-data=".\venv\Lib\site-packages\tiktoken;tiktoken" ^
    --add-data="%~dp0chroma_db;chroma_db" ^
    --hidden-import="chromadb.telemetry.product.posthog" ^
    --hidden-import="chromadb.api.rust" ^
    main.py

echo.
echo --------------------------------------------------------------------
echo  Build concluido com sucesso!
echo  A aplicacao esta na pasta: 'dist\MagicMeetCopilotPro'
echo --------------------------------------------------------------------
echo.
pause