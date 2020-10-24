import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px

import settings

# TODO: connect to database, reading from csv by the moment
# df = pd.read_csv('data/SECOP_I_Contratos.csv', nrows = 10000)
df = pd.read_csv('data/reduced_data.csv')

# define dict and options for "grupo"
grupo_dict = dict(zip(df['ID Grupo'].unique(), df['Nombre Grupo'].unique()))
grupo_options = [{"label": v, "value": k} for k, v in grupo_dict.items()]

estado_proceso_dict = {e: e for e in sorted(df['Estado del Proceso'].unique())}
estado_proceso_options = [{"label": v, "value": k}
                          for k, v in estado_proceso_dict.items()]

tipo_proceso_dict = dict(zip(df['ID Tipo de Proceso'].unique(), df['Tipo de Proceso'].unique()))
tipo_proceso_options = [{"label": v, "value": k} for k, v in tipo_proceso_dict.items()]

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

engine = create_engine(settings.DATABASE['CONNECTION'], max_overflow=20)

DB = pd.read_sql(
    '''
SELECT municipioentrega, procesoestatus, count(procesocuantia) FROM secop1contrato
WHERE municipioentrega != 'No definido' and contratotipo ='Prestación de Servicios'
group by municipioentrega, contratotipo, procesoestatus
HAVING COUNT(procesocuantia) > 10000
ORDER BY COUNT(procesocuantia) DESC
    ''', engine.connect())


db2=pd.read_sql(
'''
SELECT fechacargasecop, count(procesocuantia)  FROM secop1contrato
group by fechacargasecop
 ''', engine.connect())


plot_grf=px.line(db2,x="fechacargasecop",y="count", title='Contratos cargados en SECOP por año',
        labels={'count':'Cantidad','fechacargasecop':'Año'})


DB3=pd.read_sql(
'''
SELECT annosecop,A.grupoid, nombregrupo, count(A.grupoid) FROM secop1general C
JOIN secop1grupo A ON C.grupoid=A.grupoid
group by annosecop,nombregrupo, A.grupoid
HAVING count(A.grupoid) > 10000
ORDER BY count(A.grupoid) DESC
 ''', engine.connect())


min_graf= px.bar(DB3, y="count",x="annosecop", color='nombregrupo',
       title='Grupos mas frecuentes por año',
       labels={'count':'Cantidad','annosecop':'Año'}).update_layout(legend_title_text='Nombre Grupo')
