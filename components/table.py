import dash_table
from controls import df_small

component = dash_table.DataTable(
    id='contracts-table',
    columns=[{"name": i, "id": i} for i in df_small.columns],
    data=df_small.to_dict('records'),
)
