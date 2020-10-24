import pandas as pd

# TODO: connect to database, reading from csv by the moment
# df = pd.read_csv('data/SECOP_I_Contratos.csv', nrows = 10000)
df = pd.read_csv('data/reduced_data.csv')

# define dict and options for "grupo"
grupo_dict = dict(zip(df['ID Grupo'].unique(), df['Nombre Grupo'].unique()))
grupo_options = [{"label": v, "value": k} for k, v in grupo_dict.items()]

estado_proceso_dict = {e: e for e in sorted(df['Estado del Proceso'].unique())}
estado_proceso_options = [{"label": v, "value": k} for k, v in estado_proceso_dict.items()]

columns_small = [
    'UID', 'Anno Cargue SECOP', 'Anno Firma del Contrato', 'Fecha de Cargue en el SECOP',
    'Nivel Entidad', 'Nombre de la Entidad', 'NIT de la Entidad',
    'ID Tipo de Proceso', 'Estado del Proceso', 
    'ID Regimen de Contratacion', 'ID Objeto a Contratar',
    'Municipio Obtencion', 'Municipio Entrega', 'Cuantia Proceso', 
    'ID Grupo', 'ID Familia', 'ID Clase'
]
columns_small = df.columns

# df_small = df.copy()
df_small = df[columns_small].copy()
