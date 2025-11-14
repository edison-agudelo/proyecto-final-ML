#!/usr/bin/env bash
# Actualizar pip
pip install --upgrade pip

# Instalar dependencias normales
pip install -r requirements.txt

# Evitar errores de compilación de MySQL
pip install mysqlclient==2.2.0

# Para evitar problemas con setuptools
pip install --upgrade setuptools wheel
