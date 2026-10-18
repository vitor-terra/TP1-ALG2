import geo
import trie
import osmnx as ox

from dash import Dash, html, dcc, Input, Output, State
import dash_leaflet as dl



app = Dash(__name__)

BARES = geo.setup_restaurant_dict()
GRAFO = ox.load_graphml('bh.graphml')

T = trie.Trie()
driver_positions = []



#value is the restaurants index in BARES
def make_search_options():
    options = []

    for bar in BARES:
        pop_name = None
        if BARES[bar]['NOME_FANTASIA'] != '':
            pop_name = BARES[bar]['NOME_FANTASIA']
        name = BARES[bar]['NOME']
        address = f'BAIRRO {BARES[bar]['NOME_BAIRRO']}, {BARES[bar]['DESC_LOGRADOURO']} {BARES[bar]['NOME_LOGRADOURO']}, NUMERO {BARES[bar]['NUMERO_IMOVEL']}'
        if BARES[bar]['COMPLEMENTO'] != '':
            address += f', {BARES[bar]['COMPLEMENTO']}'


        if pop_name is not None:
            search_component = f'{pop_name} {name} {address}'
            label_component = html.Div([
                html.Div(
                    pop_name, style={'fontWeight' : 600},
                ),
                html.Div(
                    f'{name}, {address}', style={'fontSize': '12px', 'opacity' : 0.7}
                ),
            ])
        else:
            search_component = f'{name} {address}'
            label_component = html.Div([
                html.Div(
                    name, style={'fontWeight' : 600}
                ),
                html.Div(
                    address, style={'fontSize': '12px', 'opacity' : 0.7}
                )
            ])

        options.append({'label' : label_component, 'value' : bar, 'title' : address, 'search' : search_component})

    return options



app.layout = html.Div(
    [
        html.Div([

            html.Div([
                #NUMBER OF DRIVERS BUTTON
                dcc.Input(id='number_of_drivers', type='number', min=1, placeholder='Número de Motoristas a Gerar', style= {'width' : '300px'}),      
                dcc.Button('Gerar Motoristas', id='generate_drivers_button'),
            ], style= {'display' : 'flex', 'gap' : '10px'}),

            html.Div([

                html.Div([
                    #MAX DISTANCE / RESTAURANT DROPDOWN
                    dcc.Input(id='maximum_distance_input', type='number', min=1, max=30000, placeholder='Distância Máxima para Busca de Motoristas', style= {'width' : '330px', 'alignItems' : 'right'}),
                    dcc.Dropdown(id='restaurants_dropdown', options=make_search_options(), placeholder='Escolha um Restaurante')
                ],style = {'display' : 'flex', 'flexDirection' : 'column','gap' : '8px'},),

                html.Div([
                    #SEARCH BUTTON
                    dcc.Button('Buscar', id='driver_distance_search_button', disabled=True, style= {'width' : '300px', 'alignItems' : 'right'}),
                ],style = {'display' : 'flex','gap' : '8px'},),

            ], style = {'marginLeft' : 'auto', 'display' : 'flex', 'gap' : '8px'})
            
            ],style = {'display' : 'flex', 'gap' : '8px', 'alignItems' : 'center'},),   

        dl.Map(
                #MAP
                id='map', center=[-19.92, -43.94], zoom=12,
                children=[dl.TileLayer(), dl.LayerGroup(id='nearby_driver_markers'), dl.LayerGroup(id='no_good_driver_markers'), dl.LayerGroup(id='restaurant_marker')],
                style={'height': '700px', 'marginTop' : '16px'},
            ),
    ])



@app.callback(
    Output('driver_distance_search_button', 'disabled'),
    Input('maximum_distance_input', 'value'),
    Input('restaurants_dropdown', 'value')
)
def toggle_search_button(dist, restaurant):
    return dist is None or restaurant is None



@app.callback(
    Output('nearby_driver_markers', 'children'),
    Input('generate_drivers_button', 'n_clicks'),
    State('number_of_drivers', 'value'),
    prevent_initial_call = True
)
def get_drivers(generate_drivers_button, number_of_drivers):

    if number_of_drivers is None:
        return []
    
    driver_positions = T.generate_drivers(number_of_drivers, 500, BARES, GRAFO, 111)

    markers = []

    for driver in driver_positions:
        lat = driver['lat']
        lon = driver['lon']
        markers.append(dl.CircleMarker(center=[lat, lon], radius=4, color='red', children=dl.Tooltip(f'Escolha um restaurante para saber a distância')))

    return markers



@app.callback(
    Output('restaurant_marker', 'children'),
    Input('restaurants_dropdown', 'value'),
    prevent_initial_call = True
)
def show_restaurant_marker(restaurant):
    if restaurant is None:
        return []
    
    r = BARES[restaurant]

    if r['NOME_FANTASIA'] != '':
        tooltip = r['NOME_FANTASIA']
    else:
        tooltip = r['NOME']

    return [dl.CircleMarker(center=[r['LATITUDE'], r['LONGITUDE']], radius=6, color='green', children=dl.Tooltip(tooltip))]


#
@app.callback(
    #Output()
)
def show_drivers_in_radius():
    pass

if __name__ == "__main__":

    app.run(debug=True)
