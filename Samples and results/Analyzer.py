import os
import json
import pandas as pd
import matplotlib.pyplot as plt
from numpy import nan

file_to_be_analyzed = 'dj-psi-ca.json'
output_folder = file_to_be_analyzed.split('.')[0].upper()
fp = 'Data/WS-Android-M1Max-S21Ultra/'
folder_path = fp + output_folder


with open(fp + file_to_be_analyzed, 'r') as f:  # r porque se va a leer
    data = json.load(f)
    # Crear un DataFrame vacío para almacenar los datos
    df_activities = pd.DataFrame()

    # Iterar sobre cada identificador en los datos
    for identificador in data['logs']:
        if 'activities' in data['logs'][identificador]:
            # Extraer las actividades para el identificador actual
            activities = data['logs'][identificador]['activities']

            # Convertir las actividades en un DataFrame
            df = pd.json_normalize(activities.values())

            # Agregar una columna para el identificador actual
            df['id'] = identificador

            # Concatenar el DataFrame actual con el DataFrame que contiene todas las actividades
            df_activities = pd.concat([df_activities, df], ignore_index=True)

# Convierte las columnas de tiempo a formato datetime
df_activities['timestamp'] = pd.to_datetime(df['timestamp'], format="%d/%m/%Y %H:%M:%S")

# Calcula el tiempo total
tiempo_total = df_activities['timestamp'].max() - df_activities['timestamp'].min()
print(f'Tiempo total: {tiempo_total}')

# Agrupa los datos por el código de actividad
grouped = df_activities.groupby('activity_code')

# Crea un DataFrame para almacenar los resultados
results = pd.DataFrame(
    columns=['device_type', 'activity_code', 'media_tiempo', 'media_ram', 'min_ram', 'max_ram', 'media_cpu',
             'min_cpu', 'max_cpu', 'instance_ram', 'instance_cpu', 'instance_min_ram', 'instance_max_ram',
             'instance_min_cpu', 'instance_max_cpu', 'cpu_time', 'min_cpu_time', 'max_cpu_time'])

# Calcula las medias y los picos para cada grupo
for name, group in grouped:
    # Comunes
    media_tiempo = group['time'].mean()

    # El valor device_type vendrá en Details o type porque no se unificó el nombre antes de algunas pruebas
    if 'Details' in group and group['Details'].iloc[0] is not nan:
        device_type = group['Details'].iloc[0]
    else:
        device_type = group['type'].iloc[0]

    # Específicos Android
    if 'Android' in device_type:
        # Elimina "MB" de las columnas de RAM y convierte a números
        group['Avg_RAM'] = group['Avg_RAM'].str.replace(' MB', '').astype(float)
        group['Peak_RAM'] = group['Peak_RAM'].str.replace(' MB', '').astype(float)
        media_ram = group['Avg_RAM'].mean()
        group['App_Avg_RAM'] = group['App_Avg_RAM'].str.replace(' MB', '').astype(float)
        group['App_Peak_RAM'] = group['App_Peak_RAM'].str.replace(' MB', '').astype(float)
        min_ram = group['Avg_RAM'].min()
        max_ram = group['Peak_RAM'].max()
        instance_ram = group['App_Avg_RAM'].mean()
        instance_min_ram = group['App_Avg_RAM'].min()
        instance_max_ram = group['App_Peak_RAM'].max()
        group['CPU_time'] = group['CPU_time'].str.replace(' ms', '').astype(float)
        cpu_time = group['CPU_time'].mean()
        min_cpu_time = group['CPU_time'].min()
        max_cpu_time = group['CPU_time'].max()

    # Específicos Python
    else:
        # Filtrar los valores de CPU que son 0% o N/A
        group = group.query("`Avg_CPU` != '0%' & `Avg_CPU` != 'N/A' & `Peak_CPU` != '0%' & `Peak_instance_CPU` != '0%'")
        group['Avg_CPU'] = group['Avg_CPU'].fillna('').astype(str).str.split(' ').str[0]
        group['Avg_CPU'] = group['Avg_CPU'].str.replace('%', '').astype(float)
        group['Peak_CPU'] = group['Peak_CPU'].str.replace('%', '').astype(float)
        group['Avg_instance_RAM'] = group['Avg_instance_RAM'].str.replace(' MB', '').astype(float)
        group['Peak_instance_RAM'] = group['Peak_instance_RAM'].str.replace(' MB', '').astype(float)
        group['Avg_instance_CPU'] = group['Avg_instance_CPU'].str.replace('%', '').astype(float)
        group['Peak_instance_CPU'] = group['Peak_instance_CPU'].str.replace('%', '').astype(float)
        # La Avg_RAM viene como 11956.39 MB / 32679.41 MB - 36.59%, hay que coger solo el primer valor y quitando MB
        group['Avg_RAM'] = group['Avg_RAM'].fillna('').astype(str).str.split(' ').str[0]
        group['Avg_RAM'] = pd.to_numeric(group['Avg_RAM'], errors='coerce')
        group['Peak_RAM'] = group['Peak_RAM'].fillna('').astype(str).str.replace(' MB', '').astype(float)
        group['Peak_RAM'] = pd.to_numeric(group['Peak_RAM'], errors='coerce')  # Para que no de error si no es numérico
        media_ram = group['Avg_RAM'].mean()
        min_ram = group['Avg_RAM'].min()
        max_ram = group['Peak_RAM'].max()
        instance_ram = group['Avg_instance_RAM'].mean()
        instance_min_ram = group['Avg_instance_RAM'].min()
        instance_max_ram = group['Peak_instance_RAM'].max()
        instance_cpu = group['Avg_instance_CPU'].mean()
        instance_min_cpu = group['Avg_instance_CPU'].min()
        instance_max_cpu = group['Peak_instance_CPU'].max()
        media_cpu = group['Avg_CPU'].mean()
        min_cpu = group['Avg_CPU'].min()
        max_cpu = group['Peak_CPU'].max()

    # Añade los resultados al DataFrame
    if 'Android' not in device_type:
        results.loc[len(results)] = [device_type, name, media_tiempo, media_ram, min_ram, max_ram, media_cpu, min_cpu,
                                     max_cpu,
                                     instance_ram, instance_cpu, instance_min_ram, instance_max_ram, instance_min_cpu,
                                     instance_max_cpu, None, None, None]
    else:
        results.loc[len(results)] = [device_type, name, media_tiempo, media_ram, min_ram, max_ram, None, None, None,
                                     instance_ram, None, instance_min_ram, instance_max_ram, None,
                                     None, cpu_time, min_cpu_time, max_cpu_time]

# Para guardar los gráficos y los resultados
if not os.path.exists(folder_path):
    os.makedirs(folder_path)

with open(os.path.join(folder_path, 'results.txt'), 'a') as f:
    f.write(f'Tiempo total: {tiempo_total}\n')

# Guardamos los resultados en un archivo de texto en la carpeta de resultados
for index, row in results.iterrows():
    print(row)
    with open(os.path.join(folder_path, 'results.txt'), 'a') as f:  # a porque se va a añadir
        f.write(str(row) + '\n')

# Iterar sobre las columnas del DataFrame de resultados
for column in results.columns:
    if column != 'activity_code' and column != 'device_type':
        # Filtrar NaN antes de nada, para poder seguir teniendo gráficas de los que tengamos datos
        filtered_results = results.dropna(subset=[column])

        if not filtered_results.empty:  # Verificar que haya datos después de filtrar NaN
            # Crear el gráfico
            plt.figure(figsize=(15, 5))  # Ajustar tamaño del gráfico
            plt.barh(filtered_results['activity_code'], filtered_results[column], color='lightgreen')
            plt.xlabel(column.replace('_', ' ').upper())
            plt.ylabel('Activity Code')
            # Concatenar en el título ambos tipos de dispositivos, cada uno representa una barra distinta
            plt.title(column.replace('_', ' ').upper() + ' per Activity Code - ' + ' - '.join(results['device_type']))

            # Mostrar los resultados al lado de la barra
            for i, value in enumerate(filtered_results[column]):
                plt.text(value, i, str(round(value, 3)))

            plt.tight_layout()
            # Guardar el gráfico
            plt.savefig(os.path.join(folder_path, column.replace('_', '') + '_plot.png'))
            plt.close()
