@echo on
title Magic Meet Copilot - MODO DE DEPURACAO

echo.
echo === INICIANDO SCRIPT DE DEPURACAO ===
echo Pressione qualquer tecla para continuar...
echo.
pause
cls

echo === PASSO 1: VERIFICANDO O PYTHON ===
echo Vamos tentar executar o comando 'python --version'.
echo Se o Python estiver instalado e no PATH, voce vera a versao.
echo Se nao, voce vera uma mensagem de erro.
echo.

:: Executamos o comando SEM o '>nul 2>nul' para podermos ver a saida
python --version

echo.
echo Pressione qualquer tecla para continuar...
pause
cls

echo === PASSO 2: VERIFICANDO AMBIENTE VIRTUAL ===
IF NOT EXIST .venv (
    echo A pasta '.venv' nao foi encontrada.
    echo Vamos tentar criar o ambiente virtual com 'python -m venv .venv'.
    python -m venv .venv
) ELSE (
    echo A pasta '.venv' ja existe. Tudo certo.
)
echo.
echo Pressione qualquer tecla para continuar...
pause
cls

echo === PASSO 3: INSTALANDO DEPENDENCIAS ===
echo Vamos tentar ativar o venv e instalar os pacotes...
echo.
call .venv\Scripts\activate
pip install -r requirements.txt
playwright install

echo.
echo Se nao houve erros ate aqui, a configuracao esta completa.
echo Pressione qualquer tecla para iniciar o programa...
pause
cls

echo === PASSO 4: INICIANDO O MAGIC MEET COPILOT ===
echo Executando 'python main.py'...
echo.
python main.py

echo.
echo O programa foi fechado. Pressione qualquer tecla para sair do script.
pause