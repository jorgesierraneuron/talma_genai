import pandas as pd
from datetime import datetime
import pytz

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


def propagar_valores(df, columna):
    """
    Propaga los valores no nulos en una columna específica hacia abajo utilizando forward fill (ffill).
    
    Parámetros:
        df (DataFrame): El DataFrame que contiene la columna a procesar.
        columna (str): El nombre de la columna cuyos valores no nulos serán propagados.

    Retorna:
        DataFrame: El DataFrame con la columna modificada, donde los valores no nulos han sido propagados hacia abajo.
    """
    df[columna] = df[columna].ffill()
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

def add_timestamp_and_filename(data_frame, filename):
    """
    Agrega una columna con el timestamp actual (hora de Colombia) y otra columna con el nombre del archivo.

    Parámetros:
        data_frame (DataFrame): DataFrame al que se le agregarán las columnas.
        filename (str): Nombre del archivo que se agregará como columna.

    Retorna:
        DataFrame: DataFrame con las nuevas columnas agregadas.
    """
    # Zona horaria de Colombia
    timezone = pytz.timezone('America/Bogota')

    # Obtener el timestamp actual en la zona horaria de Colombia
    timestamp = datetime.now(timezone).strftime('%Y-%m-%d %H:%M:%S')

    # Agregar las columnas al DataFrame
    data_frame['fecha_de_carga_archivo_talma'] = timestamp
    data_frame['nombre_del_archivo'] = filename

    return data_frame

def rellenar_nulos_con_guion(df):
    """
    Rellena los valores NaN, 'NaN' y NaT en todas las columnas de un DataFrame con '-'.

    Parameters:
    df (pd.DataFrame): DataFrame a procesar.

    Returns:
    pd.DataFrame: DataFrame procesado.
    """
    # Reemplazar valores NaN, 'NaN' y NaT con '-'
    return df.replace([pd.NA, 'NaN', pd.NaT], '-').fillna('NaN')
