import dash_table
from controls import table_df, table_columns

component = dash_table.DataTable(
    id='contracts-table',
    columns=table_columns,
    data=table_df.to_dict('records'),
    filter_action='custom',
    style_data = {
        'overflow': 'hidden',
        'textOverflow': 'ellipsis',
        'maxWidth': 0
    },
    tooltip_data=[
        {
            column: {'value': str(value), 'type': 'markdown'}
            for column, value in row.items()
        } for row in table_df.to_dict('rows')
    ],
    row_selectable="multi",
    selected_rows=[],
)
