import os
import json
import pandas as pd
import matplotlib.pyplot as plt

ruta_carpeta = 'Data/Android-Android/S21Ultra-TabS7FE'

# Dataframe vacío para almacenar los datos
df_total = pd.DataFrame()

# Itera sobre los archivos de la carpeta
for nombre_archivo in os.listdir(ruta_carpeta):
    # Comprueba si el archivo es un archivo JSON
    if nombre_archivo.endswith('.json'):
        # Carga los datos JSON del archivo
        with open(os.path.join(ruta_carpeta, nombre_archivo), 'r') as f:
            data = json.load(f)

        for identificador in data['logs']:
            if 'activities' in data['logs'][identificador]:
                df = pd.json_normalize(data['logs'][identificador]['activities'])
                df_total = pd.concat([df_total, df])

# Convierte las columnas de tiempo a formato datetime
df_total['timestamp'] = pd.to_datetime(df_total['timestamp'], format="%d/%m/%Y %H:%M:%S")

# Calcula el tiempo total
tiempo_total = df_total['timestamp'].max() - df_total['timestamp'].min()

# Agrupa los datos por el código de actividad
grouped = df_total.groupby('activity_code')

# Crea un DataFrame para almacenar los resultados
results = pd.DataFrame()

# Calcula las medias y los picos para cada grupo
for name, group in grouped:
    media_ram = group['Avg_RAM'].mean()
    media_cpu = group['Avg_CPU'].mean()
    media_tiempo = group['time'].mean()
    min_ram = group['Peak_RAM'].min()
    max_ram = group['Peak_RAM'].max()
    min_cpu = group['Peak_CPU'].min()
    max_cpu = group['Peak_CPU'].max()

    results = results.append({'activity_code': name, 'media_ram': media_ram, 'media_cpu': media_cpu,
                              'media_tiempo': media_tiempo, 'min_ram': min_ram, 'max_ram': max_ram,
                              'min_cpu': min_cpu, 'max_cpu': max_cpu}, ignore_index=True)

print(results)

# Diagramas de barras para cada métrica
for column in results.columns:
    if column != 'activity_code':
        results.plot(x='activity_code', y=column, kind='bar', title=column)
        plt.show()
