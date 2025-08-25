import os
from dotenv import load_dotenv

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# --- Configuración de la Base de Datos NeonDB ---
DATABASE_URI = os.getenv("DATABASE_URI")

# Verificación para asegurar que la URI se cargó correctamente
if not DATABASE_URI:
    raise ValueError("ERROR: No se encontró la variable DATABASE_URI en el archivo .env. Por favor, configúrala con tu URI de conexión a NeonDB.")

# --- ¡NUEVO! Configuración del Modelo de Lenguaje ---
# Aquí defines qué modelo de Ollama quieres que use toda la aplicación.
# Cambia este valor si quieres probar con otro modelo.
OLLAMA_MODEL_NAME = "llama3.2:3b" # <-- ¡MODELO CAMBIADO!

print(f"✅ Settings loaded. Model: {OLLAMA_MODEL_NAME}. Ready to connect to NeonDB.")