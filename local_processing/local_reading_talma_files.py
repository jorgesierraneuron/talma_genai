
import pandas as pd
import numpy as np

#-----Funciones para lectura archivos -----#

def read_excel_df(ruta_archivo, header=0, sheet_name=0):
    """
    Carga un archivo Excel en un DataFrame.

    Parámetros:
        ruta_archivo (str): Ruta al archivo Excel.
        header (int, list of int, None): Fila(s) a usar como encabezado(s).
                                         Si es None, no se considera ninguna fila como encabezado.

    Retorna:
        DataFrame: DataFrame cargado desde el archivo Excel.
    """
    return pd.read_excel(ruta_archivo, header=header, sheet_name=sheet_name)


def columns_no_unnamed(df):
    """
    Retorna una lista de nombres de columnas del DataFrame, excluyendo las que contienen 'Unnamed'.
    
    Parámetros:
        df (DataFrame): El DataFrame del que se desea obtener las columnas.

    Retorna:
        list: Lista de nombres de columnas que no contienen 'Unnamed'.
    
    Ejemplo:
        Si el DataFrame tiene columnas ['Unnamed: 0', 'Columna1', 'Columna2'],
        esta función retornará ['Columna1', 'Columna2'].
    """
    return [col for col in df.columns if 'Unnamed' not in col]


def propagar_valores_condicional(df, columna_codigo, columna_condicional):
    """
    Propaga valores no nulos en una columna específica hacia abajo,
    solo si otra columna relacionada tiene valores nulos.

    Parámetros:
        df (DataFrame): El DataFrame que contiene las columnas a procesar.
        columna_codigo (str): Nombre de la columna cuyos valores no nulos serán propagados.
        columna_condicional (str): Nombre de la columna condicional.

    Retorna:
        DataFrame: El DataFrame con la columna `columna_codigo` modificada según la condición.
    """
    temp_col = df[columna_codigo].copy()
    temp_col[df[columna_condicional].isnull()] = temp_col.ffill()
    df[columna_codigo] = temp_col
    
    return df


def generar_funciones_concatenacion(df, columna_excluir):
    """
    Genera un diccionario de funciones de concatenación para todas las columnas
    de un DataFrame, excluyendo una columna específica.

    Parámetros:
        df (DataFrame): El DataFrame que contiene las columnas a procesar.
        columna_excluir (str): El nombre de la columna que se debe excluir del diccionario.

    Retorna:
        dict: Un diccionario donde las claves son los nombres de las columnas
              y los valores son funciones lambda que concatenan los valores no nulos de las columnas.
    """
    def concatenar_strings(col):
        return lambda x: ' '.join(x.dropna().astype(str))  

    return {col: concatenar_strings(col) for col in df.columns if col != columna_excluir}


def concatenar_columnas_intermedias(df, inicio, fin, patron, nueva_columna):
    """
    Filtra y concatena las columnas que contienen un patrón específico entre dos índices,
    y almacena el resultado en una nueva columna.

    Parámetros:
        df (DataFrame): El DataFrame que contiene las columnas a procesar.
        inicio (int): Índice de inicio (excluido del rango).
        fin (int): Índice de fin (excluido del rango).
        patron (str): Patrón que deben contener las columnas para ser seleccionadas.
        nueva_columna (str): Nombre de la nueva columna donde se almacenará el resultado concatenado.

    Retorna:
        DataFrame: El DataFrame con la nueva columna creada y las columnas intermedias eliminadas.
    """

    columnas_intermedias = [
        col for col in df.columns[inicio+1:fin] if patron in str(col)
    ]

    df[nueva_columna] = df[columnas_intermedias].apply(
        lambda x: ' '.join(x.dropna().astype(str).str.strip()), axis=1
    )

    df = df.drop(columns=columnas_intermedias)

    return df

def obtener_columna_intermedia(df, inicio, fin):
    """
    Retorna el nombre de la columna que se encuentra entre dos índices específicos en un DataFrame.

    Parámetros:
        df (DataFrame): El DataFrame que contiene las columnas a evaluar.
        inicio (int): Índice inicial (excluido).
        fin (int): Índice final (incluido solo para determinar el rango).

    Retorna:
        str: Nombre de la columna en el índice intermedio (inicio + 1), 
             o None si el índice intermedio no es válido.
    """
    indice_intermedio = inicio + 1

    if indice_intermedio < fin and indice_intermedio < len(df.columns):
        return df.columns[indice_intermedio]
    
    return None

#--- Fuentes de Informacion ----#

source_paths = ["/content/listado_procesos750050369.xlsx"]

for path in source_paths:

    filename = "PROCESADO" + " " + path.split('/')[-1] 

    if "listado" in path:

        #---- Lectura Informacion Calidad ----#

        df = read_excel_df(path, header=2)
        orden_columnas = columns_no_unnamed(df)
        df = propagar_valores_condicional(df, 'Código', 'Pais')
        funciones_agrupacion = generar_funciones_concatenacion(df, 'Código')

        df['Código'] = df.apply(
            lambda row: f"NULO_{row.name}" if pd.isnull(row['Código']) else row['Código'],
            axis=1
        )

        df = df.groupby('Código', as_index=False).agg(funciones_agrupacion)

        df['Código'] = df['Código'].apply(
            lambda x: np.nan if str(x).startswith('NULO_') else x
        )

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

        #---Reordenacion de columnas ---#

        df = df[orden_columnas]

        #--- Guardado Archivo Calidad --#

        print('Escritura Archivo Calidad')

        df.to_excel(filename, index=False)

    elif "Reporte de Accion" in path:

        #---- Lectura Informacion Calidad (planes de accion) ----#

        df = read_excel_df(path, header=[3])

        #---Seleccion de columnas y eliminacion de falsos nulos---#

        orden_columnas = columns_no_unnamed(df)
        df = df[orden_columnas]
        df = df[df['CODIGO SAC'] != 'CODIGO SAC']
        total_columnas_alternativa = len(df.columns)
        df = df[df.isnull().sum(axis=1) <= total_columnas_alternativa - 1]

        #--- Guardado Archivo Calidad --#

        print('Escritura Archivo Calidad (planes de accion)')

        df.to_excel(filename, index=False)

    elif "BASE DE DATOS UNIFICADA" in path:

        #---- Lectura Informacion Seguridad Operacional ----#

        df = read_excel_df(path, sheet_name = "BASE UNIFICADA")
        columnas = df.columns.tolist()
        
        if 'CODIGO TALMA' in columnas:
            columna_last_index = 'CODIGO TALMA'

        elif 'CODIGO INTERNO' in columnas:
            columna_last_index = 'CODIGO INTERNO'
        
        else:
            print ('No existe una columna codigo talma asociada')

        #--- Filtro para no tomar en cuenta nulos ---#

        ultimo_indice = df[columna_last_index].last_valid_index()
        df = df.loc[:ultimo_indice]

        #--- Guardado Archivo Seguridad Operacional --#

        df.to_excel(filename, index=False)

    else:
        raise Exception("Fuente no reconocida")
    
    
    




