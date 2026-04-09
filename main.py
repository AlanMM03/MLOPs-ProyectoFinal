import pandas as pd
import joblib
from google.cloud import bigquery
from google.cloud import storage

# ==========================================
# 0. CONFIGURACIÓN DE VARIABLES (REEMPLAZA AQUÍ)
# ==========================================
PROJECT_ID_PROCESAMIENTO = 'mlops-fp-procesamiento'
DATASET_PROCESAMIENTO = 'data_processing'

PROJECT_ID_PRODUCCION = 'mlops-fp-produccion'
DATASET_PRODUCCION = 'predicciones_dataset'

BUCKET_NAME = 'mlops-fp-modelo/modelo-linear-regression'
MODEL_FILENAME = 'linear_regression.joblib'

# ==========================================
# 1. LEER LOS DATOS PROCESADOS
# ==========================================
print("1. Extrayendo datos de la tabla temporal...")
bq_client = bigquery.Client(project=PROJECT_ID_PROCESAMIENTO)

query_datos = f"""
    SELECT *
    FROM `{PROJECT_ID_PROCESAMIENTO}.{DATASET_PROCESAMIENTO}.TABLE_OUTPUT`
"""
df_input = bq_client.query(query_datos).to_dataframe()
print(f"Datos extraídos: {df_input.shape[0]} registros.")

# ==========================================
# 2. CARGAR EL MODELO DESDE CLOUD STORAGE
# ==========================================
print("2. Descargando modelo desde Cloud Storage...")
storage_client = storage.Client(project=PROJECT_ID_PROCESAMIENTO)
bucket = storage_client.bucket(BUCKET_NAME)
blob = bucket.blob(MODEL_FILENAME)

# Descargamos el archivo temporalmente al entorno de ejecución
blob.download_to_filename(MODEL_FILENAME)

# Cargamos el modelo en memoria
modelo = joblib.load(MODEL_FILENAME)
print("Modelo cargado exitosamente.")

# ==========================================
# 3. EJECUTAR PREDICCIONES
# ==========================================
print("3. Generando predicciones...")
# Hacemos la predicción sobre las features del dataframe
predicciones = modelo.predict(df_input)

# Creamos un nuevo dataframe con las predicciones para insertarlo
df_resultados = df_input.copy()
df_resultados['prediccion_propension'] = predicciones

# ==========================================
# 4. GUARDAR RESULTADOS EN EL PROYECTO DE PRODUCCIÓN
# ==========================================
print("4. Guardando resultados en BigQuery de Producción...")
bq_client_prod = bigquery.Client(project=PROJECT_ID_PRODUCCION)

# Tabla principal
table_id_principal = f"{PROJECT_ID_PRODUCCION}.{DATASET_PRODUCCION}.ba_modelo_propension_inscripcion"

# Insertamos el dataframe directamente a la tabla
job_config = bigquery.LoadJobConfig(
    write_disposition="WRITE_APPEND" # Añade los datos si la tabla existe
)

job_principal = bq_client_prod.load_table_from_dataframe(
    df_resultados, table_id_principal, job_config=job_config
)
job_principal.result() # Esperamos a que termine el trabajo

print(f"Predicciones guardadas en la tabla {table_id_principal}")