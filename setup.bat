@echo off

SET ENV_NAME=WS-PSI-ENV

echo Creando el entorno virtual...
python -m venv %ENV_NAME%

echo Activando el entorno virtual...
call %ENV_NAME%\Scripts\activate

echo Actualizando pip...
python -m pip install --upgrade pip

echo Instalando dependencias de requirements.txt...
pip install -r requirements.txt

echo Instalando dependencia específica de BFV (py-fhe)...
cd Crypto/py-fhe
pip install .

echo Instalación completada.
pause
