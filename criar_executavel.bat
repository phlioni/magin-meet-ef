@echo off
echo ========================================================
echo   CRIANDO EXECUTAVEL BUSINESS ANALYST COPILOT
echo ========================================================

:: 1. Ativar o ambiente virtual (garanta que o .venv existe)
call venv\Scripts\activate

:: 2. Instalar o PyInstaller se nao estiver instalado
pip install pyinstaller

:: 3. Limpar builds anteriores para evitar erros
rmdir /s /q build
rmdir /s /q dist
rmdir /s /q "BusinessAnalystCopilot_Dist"

:: 4. Gerar o executável
:: --clean: Limpa cache
:: --noconfirm: Sobrescreve sem perguntar
:: --onefile: Gera um unico arquivo .exe
:: --windowed: Nao abre a tela preta do console (se quiser ver erros, remova isso)
:: --name: Nome do arquivo final
:: --icon: Define icone (opcional, remova se nao tiver icon.ico)
echo.
echo [1/3] Compilando o codigo Python...
pyinstaller --clean --noconfirm --onefile --windowed --name "BusinessAnalystCopilot" main.py

:: 5. Criar a pasta final de entrega
echo.
echo [2/3] Organizando arquivos para distribuicao...
mkdir "BusinessAnalystCopilot_Dist"

:: 6. Copiar o executavel
copy "dist\BusinessAnalystCopilot.exe" "BusinessAnalystCopilot_Dist\"

:: 7. Copiar a pasta templates (CRITICO: O código exige isso)
xcopy "templates" "BusinessAnalystCopilot_Dist\templates\" /E /I /Y

:: 8. Copiar configurações (CRITICO: O código exige isso)
:: Se voce quiser enviar ja configurado, mantenha estas linhas.
:: Se for para um cliente configurar, voce pode criar um .env de exemplo.
copy ".env" "BusinessAnalystCopilot_Dist\"
copy "google_credentials.json" "BusinessAnalystCopilot_Dist\"

echo.
echo [3/3] Processo finalizado!
echo ========================================================
echo A pasta "BusinessAnalystCopilot_Dist" esta pronta.
echo Zipe esta pasta e envie para a outra pessoa.
echo ========================================================
pause