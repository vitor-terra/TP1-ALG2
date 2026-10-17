import geo
import trie
import random
from dash import Dash, html, dcc, Input, Output, State
import dash_leaflet as dl


app = Dash(__name__)

app.layout = html.Div(
    [
        html.Div([

            html.Div([
                dcc.Input(id='number_of_drivers', type='number', min=1, placeholder='Número de Motoristas a Gerar', style= {'width' : '300px'}),      
                dcc.Button('Gerar Motoristas', id='generate_drivers_button'),
            ], style= {'display' : 'flex', 'gap' : '10px'}),

            html.Div([

                html.Div([
                    dcc.Input(id='maximum_distance_input', type='number', min=1, max=30000, placeholder='Distância Máxima para Busca de Motoristas', style= {'width' : '330px', 'alignItems' : 'right'}),
                    dcc.Dropdown(id='restaurants_dropdown', options=[1,2,3,4,5], placeholder='Escolha um Restaurante')
                ],style = {'display' : 'flex', 'flexDirection' : 'column','gap' : '8px'},),

                html.Div([
                    dcc.Button('Buscar', id='driver_distance_search_button', disabled=True, style= {'width' : '300px', 'alignItems' : 'right'}),
                ],style = {'display' : 'flex','gap' : '8px'},),

            ], style = {'marginLeft' : 'auto', 'display' : 'flex', 'gap' : '8px'})
            
            ],style = {'display' : 'flex', 'gap' : '8px', 'alignItems' : 'center'},),   

    dl.Map(
            id='map', center=[-19.92, -43.94], zoom=12,
            children=[dl.TileLayer(), dl.LayerGroup(id='points')],
            style={'height': '450px', 'marginTop' : '16px'},
        ),
    ])

@app.callback(
    Output('driver_distance_search_button', 'disabled'),
    Input('maximum_distance_input', 'value'),
    Input('restaurants_dropdown', 'value')
)
def toggle_search_button(dist, restaurant):
    return dist is None or restaurant is None

if __name__ == "__main__":

    app.run(debug=True)
