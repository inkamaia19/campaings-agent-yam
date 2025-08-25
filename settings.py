import os
from dotenv import load_dotenv

load_dotenv()

# --- Configuración de la Base de Datos ---
DATABASE_URI = os.getenv("DATABASE_URI")
if not DATABASE_URI:
    raise ValueError("ERROR: No se encontró la variable DATABASE_URI en el archivo .env.")

# --- Configuración del Modelo de Lenguaje ÚNICO ---
# Toda la aplicación usará este modelo.
OLLAMA_MODEL_NAME = "llama3.2:3b"

print(f"✅ Settings loaded. Using single model: {OLLAMA_MODEL_NAME}. Ready to connect to NeonDB.")