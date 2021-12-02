import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px

df = pd.read_csv('case-us-state.csv')

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# radioItem list for the layout (long_code.py lines 13-45)
radio_list = []
for s,v in zip(['AZ','FL','GA','IA','ME','MI','NC','NV','OH','PA','TX','WI'],
               [11,29,16,6,4,16,15,6,18,20,38,10]):
    radio_list.append(
        html.Div([
            html.Label(f'{s}-{v}: ', style={'display':'inline', 'fontSize':15}),
            dcc.RadioItems(
                id=f'radiolist-{s}',
                options=[
                    {"label": "Dem", "value": "Democratic"},
                    {"label": "Rep", "value": "Republican"},
                    {"label": "Rep/Dem", "value": "Republican/Democratic"},
                ],
                value='Republican/Democratic',
                inputStyle={'margin-left': '10px'},
                labelStyle={'display': 'inline-block'},
                style={'display':'inline'}
            ),
        ], style={'textAlign':'end'})
    )
print(radio_list)


# Input list for the callback (long_code.py lines 48-52)
input_list = []
for x in ['AZ','FL','GA','IA','ME','MI','NC','NV','OH','PA','TX','WI']:
    input_list.append(
        Input(component_id=f'radiolist-{x}', component_property='value')
    )


app.layout = html.Div([
    dbc.Row([
        dbc.Col(html.H1("USA COVID-19 Case 2020", style={'textAlign':'center'}), width=12)
    ]),
    dbc.Row([
        dbc.Col(radio_list, xs=4, sm=4, md=4, lg=2, xl=2),
        dbc.Col(dcc.Graph(id='my-choropleth', figure={},
                          config={'displayModeBar':False}), xs=8, sm=8, md=8, lg=6, xl=6),
        dbc.Col(dcc.Graph(id='my-bar', figure={},
                          config={'displayModeBar': False}), xs=6, sm=6, md=6, lg=4, xl=4)

    ], className="g-0")
])


# must have Dash version 1.16.0 or higher
@app.callback(
    Output(component_id='my-choropleth', component_property='figure'),
    Output(component_id='my-bar', component_property='figure'),
    input_list
)
def update_graph(az, fl, ga, ia, me, mi, nc, nv, oh, pa, tx, wi):
    dff = df.copy()  # assign party to dataframe (long_code.py lines 55-57)
    for st,radio_value_chosen in zip(
            ['AZ','FL','GA','IA','ME','MI','NC','NV','OH','PA','TX','WI'],
            [az, fl, ga, ia, me, mi, nc, nv, oh, pa, tx, wi]):
        dff.loc[dff.state == st, 'party'] = radio_value_chosen

    # build map figure
    fig_map = px.choropleth(
        dff, locations="state", hover_name='cases',
        locationmode="USA-states", color="party",
        scope="usa", color_discrete_map={'Democratic': 'blue',
                                         'Republican': 'red',
                                         'Republican/Democratic': 'green'})

    # build histogram figure
    dff = dff[dff.party != 'Republican/Democratic']
    fig_bar = px.histogram(dff, x='party', y='deaths', color='party',
                           range_y=[0,100000000], color_discrete_map={'Democratic': 'blue',
                                                                'Republican': 'red'}
                           )

    return fig_map, fig_bar


if __name__ == '__main__':
    app.run_server(debug=False)

    
