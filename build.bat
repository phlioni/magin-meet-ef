@echo off
title Business Analyst Copilot - Builder

:: --- ETAPA DE SEGURANCA ---
:: Forca o encerramento de qualquer instancia anterior do programa.
echo Encerrando qualquer processo antigo do BusinessAnalystCopilot...
taskkill /F /IM "BusinessAnalystCopilot.exe" /T >nul 2>&1

:: Pausa para garantir que os arquivos foram liberados.
timeout /t 2 /nobreak >nul

echo.
echo Limpando builds anteriores...
rmdir /s /q build
rmdir /s /q dist

echo.
echo Iniciando o processo de build com PyInstaller...
echo Este processo pode levar varios minutos.

:: Comando final com o novo nome e dependências limpas
.\venv\Scripts\pyinstaller.exe --noconfirm --log-level=INFO ^
    --name="BusinessAnalystCopilot" ^
    --windowed ^
    --add-data="%~dp0src;src" ^
    --add-data="%~dp0templates;templates" ^
    --add-data="%~dp0.env;." ^
    --add-data="%~dp0google_credentials.json;." ^
    main.py

echo.
echo --------------------------------------------------------------------
echo  Build concluido com sucesso!
echo  A aplicacao esta na pasta: 'dist\BusinessAnalystCopilot'
echo --------------------------------------------------------------------
echo.
pause