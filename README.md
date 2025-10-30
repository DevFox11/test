1. Instalar la librería:

    cd hidra
    pip install -e .

2. Configurar PostgreSQL:
    sql

    CREATE DATABASE multitenant_db;

3. Ejecutar la API:

    cd mi_api
    pip install -r requirements.txt
    uvicorn main:app --reload