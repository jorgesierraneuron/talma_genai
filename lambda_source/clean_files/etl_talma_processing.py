
import pandas as pd
import os

from dotenv import load_dotenv
from utils.reports_processing import (read_excel_df, columns_no_unnamed,propagar_valores, generar_funciones_concatenacion, concatenar_columnas_intermedias, obtener_columna_intermedia, 
                                      rellenar_nulos_con_guion, add_timestamp_and_filename)
from utils.db_utils import connect_to_mongo, insert_data_to_mongo

source_paths = [""]

load_dotenv()  

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")

db = connect_to_mongo(MONGO_URI, MONGO_DB_NAME)

for path in source_paths:

    if "listado" in path:

        df = read_excel_df(path, header=2)
        orden_columnas = columns_no_unnamed(df)
        df = propagar_valores(df, 'Código')
        funciones_agrupacion = generar_funciones_concatenacion(df, 'Código')
        df = df.groupby('Código', as_index=False).agg(funciones_agrupacion)

        #---Concatenar columnas intermedias entre 'ACR MODERADO' y 'ACR TOLERADO'---#
        
        inicio = df.columns.get_loc('ACR MODERADO')
        fin = df.columns.get_loc('ACR TOLERADO') - 1
        df = concatenar_columnas_intermedias(df, inicio, fin, 'Unnamed', 'ACR MODERADO_2')

        #--Crear nueva columna fusionada---#

        df['ACR MODERADO_2'] = df['ACR MODERADO'].astype(str) + ' ' + df['ACR MODERADO_2'].astype(str)

        # Obtener columna intermedia entre 'Descripción del Hallazgo' y 'UN'
        inicio_2 = df.columns.get_loc('Descripción del Hallazgo')
        fin_2 = df.columns.get_loc('UN')
        columna_encontrada = obtener_columna_intermedia(df, inicio_2, fin_2)

        #--Fusionar 'Descripción del Hallazgo' con columna intermedia---#

        df['Descripción del Hallazgo_2'] = df['Descripción del Hallazgo'].astype(str) + ' ' + df[columna_encontrada].astype(str)

        #--Eliminar columnas originales--#

        df = df.drop(columns=['ACR MODERADO', 'Descripción del Hallazgo'])

        #--Renombrar columnas finales---#

        df = df.rename(columns={
            'Descripción del Hallazgo_2': 'Descripción del Hallazgo',
            'ACR MODERADO_2': 'ACR MODERADO'
        })

        #---Reordenar columnas y creacion de columnas de carga del archivo y nombre---#

        df = df[orden_columnas]
        df = rellenar_nulos_con_guion(df)
        filename = path.split('/')[-1]
        df = add_timestamp_and_filename(df, filename)
                                        
        #----Carga archivo leido exitosamente-------#
        
        print("Carga archivo procesado a mongo")
        insert_data_to_mongo(db, "data_calidad", df) 

    
    elif "BASE DE DATOS UNIFICADA" in path:

        df = read_excel_df(path, sheet_name = "BASE UNIFICADA")

        columnas = df.columns.tolist()
        columna_last_index = 'CODIGO TALMA' if 'CODIGO TALMA' in columnas else 'CODIGO INTERNO'
        ultimo_indice = df[columna_last_index].last_valid_index()

        #---Filtrar el DataFrame hasta ese índice---#

        df = df.loc[:ultimo_indice]
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')] 

        total_columnas_alternativa = len(df.columns)

        #--Filtrar las filas con más de N valores nulos---#

        df = df[df.isnull().sum(axis=1) <= total_columnas_alternativa - 5]

        #--anexo columnas de fecha carga y nombre del archivo--#

        df = rellenar_nulos_con_guion(df)
        filename = path.split('/')[-1]
        df = add_timestamp_and_filename(df, filename)
                                        
        #----Carga archivo leido exitosamente-------#
        
        print("Carga archivo procesado a mongo")
        insert_data_to_mongo(db, "data_seguridad_operacional", df) 

    else:
        raise Exception("Fuente no reconocida")
    
    
    




