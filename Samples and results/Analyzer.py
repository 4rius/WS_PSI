import os
import json

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import ticker
from numpy import nan


def analyze_activities(ftba, fp):
    output_folder = ftba.split('.')[0].upper()
    folder_path = fp + output_folder

    with open(fp + ftba, 'r') as f:  # r porque se va a leer
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

    # Ordena el DataFrame por el timestamp
    df_activities = df_activities.sort_values('timestamp')

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
            group = group.query(
                "`Avg_CPU` != '0%' & `Avg_CPU` != 'N/A' & `Peak_CPU` != '0%' & `Peak_instance_CPU` != '0%'")
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
            group['Peak_RAM'] = pd.to_numeric(group['Peak_RAM'],
                                              errors='coerce')  # Para que no de error si no es numérico
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
            results.loc[len(results)] = [device_type, name, media_tiempo, media_ram, min_ram, max_ram, media_cpu,
                                         min_cpu,
                                         max_cpu,
                                         instance_ram, instance_cpu, instance_min_ram, instance_max_ram,
                                         instance_min_cpu,
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
                plt.title(
                    column.replace('_', ' ').upper() + ' per Activity Code - ' + ' - '.join(results['device_type']))

                # Mostrar los resultados al lado de la barra
                for i, value in enumerate(filtered_results[column]):
                    plt.text(value, i, str(round(value, 3)))

                plt.tight_layout()
                # Guardar el gráfico
                plt.savefig(os.path.join(folder_path, column.replace('_', '') + '_plot.png'))
                plt.close()

    # Crear una figura y ejes para el gráfico
    fig, axs = plt.subplots(7, 1, figsize=(12, 30))

    # Iterar sobre cada grupo de actividad
    for name, group in grouped:
        timestamps = group['timestamp']
        time_taken = group['time']
        ram_usage = group['Avg_RAM']
        cpu_usage = group['Avg_CPU'] if 'Avg_CPU' in group else None
        instance_ram_usage = group['Avg_instance_RAM'] if 'Avg_instance_RAM' in group else None
        instance_cpu_usage = group['Avg_instance_CPU'] if 'Avg_instance_CPU' in group else None
        app_avg_ram = group['App_Avg_RAM'] if 'App_Avg_RAM' in group else None
        app_cpu_time = group['CPU_time'] if 'CPU_time' in group else None

        # Calcular el tiempo en minutos
        tiempo_en_minutos = (timestamps.max() - timestamps.min()).seconds / 60
        # Crear un array de tiempo en minutos para el eje x
        tiempo_en_minutos = np.linspace(0, tiempo_en_minutos, len(time_taken))

        # Se ordenan los datos para que salgan de mayor a menor en el eje y
        time_taken = time_taken.sort_values(ascending=True)
        ram_usage = ram_usage.sort_values(ascending=True)
        cpu_usage = cpu_usage.sort_values(ascending=True) if cpu_usage is not None else None
        instance_ram_usage = instance_ram_usage.sort_values(ascending=True) if instance_ram_usage is not None else None
        instance_cpu_usage = instance_cpu_usage.sort_values(ascending=True) if instance_cpu_usage is not None else None
        app_avg_ram = app_avg_ram.sort_values(ascending=True) if app_avg_ram is not None else None
        app_cpu_time = app_cpu_time.sort_values(ascending=True) if app_cpu_time is not None else None

        # Se dibujan los gráficos
        axs[0].plot(tiempo_en_minutos, time_taken, label=f'Activity {name}')
        axs[0].set_title('Tiempo de Ejecución')

        axs[1].plot(tiempo_en_minutos, ram_usage, label=f'Activity {name}')
        axs[1].set_title('Consumo de RAM (Promedio)')
        # Ajustar los ticks del eje Y para mostrar solo los valores más relevantes
        axs[1].yaxis.set_major_locator(ticker.MaxNLocator(nbins=10))

        if cpu_usage is not None:
            axs[2].plot(tiempo_en_minutos, cpu_usage, label=f'Activity {name}')
            axs[2].set_title('Uso de CPU (Promedio)')
            axs[2].yaxis.set_major_locator(ticker.MaxNLocator(nbins=10))

        if app_cpu_time is not None:
            axs[3].plot(tiempo_en_minutos, app_cpu_time, label=f'Activity {name}')
            axs[3].set_title('Tiempo de CPU de las actividades (Promedio)')
            axs[3].yaxis.set_major_locator(ticker.MaxNLocator(nbins=10))

        if app_avg_ram is not None:
            axs[4].plot(tiempo_en_minutos, app_avg_ram, label=f'Activity {name}')
            axs[4].set_title('Consumo de RAM de la aplicación (Promedio)')
            axs[4].yaxis.set_major_locator(ticker.MaxNLocator(nbins=10))

        if instance_cpu_usage is not None:
            axs[5].plot(tiempo_en_minutos, instance_cpu_usage, label=f'Activity {name}')
            axs[5].set_title('Uso de CPU de la instancia (Promedio)')
            axs[5].yaxis.set_major_locator(ticker.MaxNLocator(nbins=10))

        if instance_ram_usage is not None:
            axs[6].plot(tiempo_en_minutos, instance_ram_usage, label=f'Activity {name}')
            axs[6].set_title('Consumo de RAM de la instancia (Promedio)')
            axs[6].yaxis.set_major_locator(ticker.MaxNLocator(nbins=10))

    # Añadir etiquetas a los ejes y leyendas
    for ax in axs:
        ax.set_xlabel('Tiempo (minutos)')
        ax.set_ylabel('Value')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

    # Guardar la figura
    plt.tight_layout()
    plt.savefig(os.path.join(folder_path, 'activity_plots.png'))


if __name__ == '__main__':
    files = ['paillier-domain.json', 'paillier-ope.json', 'paillier-psi-ca.json', 'dj-ope.json', 'dj-domain.json',
             'dj-psi-ca.json', 'mixed.json', 'dj-ope-512.json', 'paillier-ope-4096.json']

    folders = ['Data/Android-Android/S21Ultra-TabS7FE/', 'Data/Android-Android/TabS7FE-S21Ultra/',
               'Data/Android-Win/', 'Data/Win-Android/', 'Data/Android-WS-S21Ultra-M1Max/',
               'Data/WS-Android-M1Max-S21Ultra/', 'Data/Win-Mac/', 'Data/Mac-Win/']  # Mac-Mac is pending
    for file in files:
        for folder in folders:
            if os.path.exists(folder + file):
                analyze_activities(file, folder)
