import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px
import plotly.graph_objects as go

import settings


# create database connection
engine = create_engine(settings.DATABASE['CONNECTION'], max_overflow=20)

# READ FILES
df = pd.read_csv('data/reduced_data.csv')

# PDF pikles
filename_files = 'data/df_files4B_pandas.pickle'
df_files = pd.read_pickle(filename_files)

# define dict and options for "grupo"
grupo_df = pd.read_sql_table('secop1grupo', engine)
grupo_dict = dict(zip(grupo_df['grupoid'], grupo_df['nombregrupo']))
grupo_options = [{"label": v, "value": k} for k, v in grupo_dict.items()]

# TODO: create "estado_proceso" table
estado_proceso_dict = {e: e for e in sorted(df['Estado del Proceso'].unique())}
estado_proceso_options = [{"label": v, "value": k} for k, v in estado_proceso_dict.items()]

# define dict and options for "tipo de proceso"
tipo_proceso_df = pd.read_sql_table('secop1proceso', engine)
tipo_proceso_dict = dict(zip(tipo_proceso_df['procesoid'], tipo_proceso_df['procesotipo']))
tipo_proceso_options = [{"label": v, "value": k} for k, v in tipo_proceso_dict.items()]


DB = pd.read_sql(
    '''
    SELECT municipioentrega, procesoestatus, count(procesocuantia) FROM secop1contrato
    WHERE municipioentrega != 'No definido' and contratotipo ='Prestación de Servicios'
    group by municipioentrega, contratotipo, procesoestatus
    HAVING COUNT(procesocuantia) > 20000
    ORDER BY COUNT(procesocuantia) DESC
    ''', engine)


db2 = pd.read_sql(
    '''
    SELECT fechacargasecop, count(procesocuantia)
    FROM secop1contrato
    group by fechacargasecop
    ''', engine)


plot_grf=px.line(db2,x="fechacargasecop",y="count", title='Contratos cargados en SECOP por año',
        labels={'count':'Cantidad','fechacargasecop':'Año'})


DB3=pd.read_sql(
    '''
    SELECT annosecop,A.grupoid, nombregrupo, count(A.grupoid) FROM secop1general C
    JOIN secop1grupo A ON C.grupoid=A.grupoid
    group by annosecop,nombregrupo, A.grupoid
    HAVING count(A.grupoid) > 10000
    ORDER BY count(A.grupoid) DESC
    ''', engine)


min_graf= px.bar(DB3, y="count",x="annosecop", color='nombregrupo',
       title='Grupos mas frecuentes por año',
       labels={'count':'Cantidad','annosecop':'Año'}).update_layout(legend_title_text='Nombre Grupo')


# TODO: select reduced columns
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

# TODO: Files (pending)
def get_pivot_heatmap(df, values, margins):
    df_pivot = pd.pivot_table(data=df,
                              index='document_type_nombre',
                              columns='process_name',
                              values=values,
                              aggfunc='sum',
                              margins=margins)    
    return df_pivot

def df_to_plotly(df):
    return {'z': df.values.tolist(),
            'x': df.columns.tolist(),
            'y': df.index.tolist()}

def plot_pages(df):
    df_pivot = get_pivot_heatmap(df, 'pages', margins=False)
    data = df_to_plotly(df_pivot)
    fig = go.Figure(data=go.Heatmap(z=data['z'], 
                                    x=data['x'],
                                    y=data['y'],
                                    colorscale = 'Viridis',
                                    ))

    fig.update_layout(
        title="Quantity of pages by document' type and process' type",
        height=750,
        margin={'b':300, 'l':100}
    )
    return fig

def plot_size(df):
    df_pivot = get_pivot_heatmap(df, 'file_size_MB', margins=False)
    data = df_to_plotly(df_pivot)
    fig = go.Figure(data=go.Heatmap(z=data['z'], 
                                    x=data['x'],
                                    y=data['y'],
                                    colorscale = 'Viridis',
                                    ))

    fig.update_layout(
        title="Storage size in MB by document' type and process' type",
        height=750,
        margin={'b':300, 'l':100}
    )
    return fig

quantity_files_fig = plot_pages(df_files)
size_files_fig = plot_size(df_files)
