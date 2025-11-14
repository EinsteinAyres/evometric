@echo off
REM --- Configuração de Caminho ---
REM Define o caminho completo para a pasta do projeto.
REM O underscore '_' foi mantido, conforme o seu caminho anterior.
set "PROJECT_DIR=C:\Users\ayres\Projetos_Python\EvoMetric"

REM Navega para o diretório do projeto
cd /d "%PROJECT_DIR%"

echo.
echo ====================================
echo Iniciando EvoMetric...
echo ====================================

REM Tenta executar o script Python.
REM Se o comando 'python' falhar, o erro será exibido antes do PAUSE.
python task_adder.py

echo.
echo Processo de interface concluido.
echo Verifique o console acima para mensagens de erro.
pause