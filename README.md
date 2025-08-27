# Agente de Marketing YAM

**Versión 1.0**

## 1. Visión General

El Agente de Marketing YAM es un sistema de inteligencia artificial conversacional diseñado para permitir a los usuarios interactuar con bases de datos de marketing en lenguaje natural. Utiliza una arquitectura avanzada de **Agentic RAG** para interpretar preguntas, generar planes de acción dinámicos, consultar datos, realizar cálculos y presentar insights de manera inteligente y calibrada.

Este proyecto está diseñado para ser **altamente modular y fácilmente adaptable** a diferentes Modelos de Lenguaje (LLMs) y bases de datos.

---

## 2. Stack Tecnológico

*   **Orquestación:** LangGraph
*   **Modelo de Lenguaje (Local por defecto):** Ollama (`llama3.2:3b`)
*   **Base de Datos (por defecto):** NeonDB (PostgreSQL)
*   **Interfaz Gráfica:** Streamlit
*   **Lógica de Datos:** Pandas, Psycopg2

---

## 3. Instalación y Ejecución

Sigue estos pasos para poner en marcha el agente en tu entorno local.

### **3.1. Prerrequisitos**

*   Python 3.10+
*   Git
*   [Ollama](https://ollama.com/) instalado y en ejecución.

### **3.2. Pasos de Instalación**

1.  **Clona el repositorio:**
    ```bash
    git clone https://github.com/tu-usuario/tu-repositorio.git
    cd tu-repositorio
    ```

2.  **Crea y activa un entorno virtual:**
    ```bash
    # En Windows
    python -m venv venv
    .\venv\Scripts\activate

    # En macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Instala las dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Descarga el modelo de Ollama por defecto:**
    ```bash
    ollama pull llama3.2:3b
    ```

5.  **Configura tus credenciales:**
    *   Crea un archivo llamado `.env` en la raíz del proyecto.
    *   Copia y pega la siguiente estructura en el archivo `.env` y rellena con tus datos. **Este archivo es privado y no debe subirse a Git.**
      ```env
      # URI de conexión a tu base de datos (ej. NeonDB)
      DATABASE_URI="postgresql://tu_usuario:tu_contraseña@host.aws.neon.tech/neondb"
      
      # (Opcional) Si quieres migrar a OpenAI, necesitarás esta clave
      # OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
      ```

### **3.3. Ejecución del Agente**

1.  **Inicia el servidor de Ollama** en una terminal separada:
    ```bash
    ollama serve
    ```

2.  **Inicia la interfaz de Streamlit** en la terminal de tu proyecto (con el `venv` activado):
    ```bash
    streamlit run ui_streamlit.py
    ```
    Se abrirá una pestaña en tu navegador con la interfaz del agente.

---

## 4. Arquitectura de Prompts y "Método de Razonamiento"

El núcleo de la inteligencia del agente reside en los `prompts` definidos en `prompts.py`. Utilizamos una técnica avanzada de **Cadena de Pensamiento (Chain of Thought) Guiado** para forzar al LLM a seguir un proceso de razonamiento estructurado antes de actuar.

#### **4.1. El `planner_prompt` (El Cerebro del Agente)**
Este prompt es el más importante. Convierte la pregunta del usuario en un plan JSON que dicta todo el flujo de trabajo posterior. Sigue un "Método de Razonamiento" en 3 pasos:
1.  **Clasificación de Intención:** El LLM calibra la pregunta en 3 niveles de profundidad (Dato Directo, Lista Simple, Análisis Profundo).
2.  **Diseño del SQL:** Basado en la intención y en reglas explícitas sobre `JOINs`, selección de columnas y agregaciones, genera la consulta SQL necesaria.
3.  **Diseño de la Presentación:** Decide si se debe mostrar una tabla (`show_table`) o generar un gráfico (`plot_info`) basándose en el nivel de análisis.

Esta estructura estructurada es la clave para obtener respuestas consistentes, calibradas y sin errores lógicos. Los `prompts` están diseñados para ser agnósticos al modelo (funcionan bien con diferentes LLMs) siempre que tengan una capacidad de razonamiento mínima. No deberían necesitar cambios significativos al migrar.

---

## 5. Guía de Migración y Personalización

Este proyecto es modular. Aquí te explicamos cómo cambiar sus componentes clave.

### **5.1. Cambiar el Modelo de Lenguaje (Ej: Migrar de Ollama a GPT-4o)**

Actualmente, el proyecto está configurado para usar un modelo local a través de Ollama. Si deseas utilizar un modelo a través de API como **GPT-4o de OpenAI**, sigue estos pasos:

1.  **Actualiza las dependencias:**
    *   Añade `langchain-openai` a tu archivo `requirements.txt`.
    *   Ejecuta `pip install -r requirements.txt`.

2.  **Añade tu clave de API:**
    *   En tu archivo `.env`, descomenta y añade tu clave de OpenAI:
      ```env
      OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
      ```

3.  **Modifica el archivo `workflow.py`:**
    *   Necesitas cambiar cómo se inicializa el objeto LLM. La lógica de LangGraph, los nodos y los `prompts` **no necesitan cambiar**.

    *   Busca todas las instancias donde se define `ChatOllama` y reemplázalas.

    *   **Código a cambiar en `workflow.py`:**
        *   Reemplaza el `import`:
            ```python
            # QUITA ESTA LÍNEA:
            from langchain_ollama import ChatOllama
            # AÑADE ESTA LÍNEA:
            from langchain_openai import ChatOpenAI
            ```
        *   Dentro de los nodos `generate_plan_node` y `generate_insights_node`, cambia la inicialización del LLM:
            ```python
            # CÓDIGO ACTUAL (OLLAMA):
            llm = ChatOllama(model=settings.OLLAMA_MODEL_NAME, format="json", temperature=0)

            # CÓDIGO NUEVO (OPENAI GPT-4o):
            llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=settings.OPENAI_API_KEY)
            ```
        *   **Importante:** Para `generate_plan_node` (que necesita salida JSON), la forma recomendada con OpenAI es un poco diferente:
            ```python
            # Para el nodo que genera el plan (JSON)
            llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=settings.OPENAI_API_KEY)
            structured_llm = llm.with_structured_output(Plan) # 'Plan' es tu clase Pydantic
            # ... el resto de la cadena usa 'structured_llm'
            ```

### **5.2. Cambiar la Base de Datos (Ej: Migrar a BigQuery)**

El agente utiliza una arquitectura **Agentic RAG + CAG** donde el contexto del esquema de la base de datos se proporciona en el `prompt`. Esto significa que el agente **no hace un "ping" a la base de datos para saber su estructura**, sino que confía en la descripción que le damos. Para cambiar de base de datos, debes:

1.  **Instalar el conector de la nueva BD:**
    *   Por ejemplo, para BigQuery, añade `google-cloud-bigquery` y `pandas-gbq` a `requirements.txt` y ejecuta `pip install -r requirements.txt`.

2.  **Actualiza la conexión en `pc_utils.py`:**
    *   Reemplaza la lógica de `psycopg2` en la función `execute_sql_query()` por la lógica de conexión de tu nueva base de datos.
    *   **Código exacto a cambiar en `pc_utils.py`:**
        ```python
        # CÓDIGO ACTUAL (PostgreSQL):
        import psycopg2
        # ...
        def execute_sql_query(sql_query: str) -> pd.DataFrame:
            conn = psycopg2.connect(settings.DATABASE_URI)
            df = pd.read_sql_query(sql_query, conn)
            # ...
        
        # CÓDIGO NUEVO (EJEMPLO PARA BIGQUERY):
        from google.cloud import bigquery
        # ...
        def execute_sql_query(sql_query: str) -> pd.DataFrame:
            # La autenticación de BigQuery se maneja a menudo a través de variables de entorno (gcloud auth)
            client = bigquery.Client(project=settings.GCP_PROJECT_ID)
            query_job = client.query(sql_query)
            df = query_job.to_dataframe()
            # ...
        ```
    *   Recuerda añadir las nuevas credenciales/configuraciones necesarias (como `GCP_PROJECT_ID`) a tu archivo `settings.py`.

3.  **¡CRÍTICO! Actualiza el esquema en `prompts.py`:**
    *   Ve al archivo `prompts.py` y busca el `PLANNER_PROMPT_TEMPLATE`.
    *   **Reemplaza la descripción del esquema de las tablas PostgreSQL** por la descripción exacta de las tablas de tu nueva base de datos.
    *   Asegúrate de que los nombres de las tablas, columnas, tipos de datos y el **dialecto SQL** (ej. "PostgreSQL" vs "BigQuery SQL") estén correctamente descritos. **El éxito del agente depende al 100% de la precisión de esta sección.**