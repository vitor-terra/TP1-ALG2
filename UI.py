import geo
import trie
import osmnx as ox
import networkx as nx

from dash import Dash, html, dcc, Input, Output, State
import dash_leaflet as dl



app = Dash(__name__)

BARES = geo.setup_restaurant_dict()

GRAFO = ox.load_graphml('bh.graphml')
GRAFO = ox.routing.add_edge_speeds(GRAFO)
GRAFO = ox.routing.add_edge_travel_times(GRAFO)
GRAFO_INVERSO = GRAFO.reverse(copy=False)

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



#restaurant should be the entire row in BARES, not the id
#max_travel_time gets received in minutes for user convenience, so it must be converted to seconds
def get_etas(restaurant, driver_ids, driver_positions, max_travel_time=None):

    if max_travel_time is not None:
        cutoff_minutes = max_travel_time * 60
    else:
        cutoff_minutes = max_travel_time
    
    restaurant_node = ox.distance.nearest_nodes(GRAFO, X=float(restaurant['LONGITUDE']), Y=float(restaurant['LATITUDE']))
    etas = nx.single_source_dijkstra_path_length(GRAFO_INVERSO, restaurant_node, weight='travel_time', cutoff=cutoff_minutes)

    etas_dict = {}

    for ids in driver_ids:
        etas_dict[ids] = etas.get(driver_positions[ids]['node'])
        if etas_dict[ids] is not None:
            etas_dict[ids] = round(etas.get(driver_positions[ids]['node'])/60, 2)

    return etas_dict



app.layout = html.Div(
    [
        html.Div([

            html.Div([
                #NUMBER OF DRIVERS BUTTON
                dcc.Input(id='number_of_drivers', type='number', min=1, placeholder='Número de Motoristas a Gerar', style= {'width' : '300px'}),      
                dcc.Button('Gerar Motoristas', id='generate_drivers_button'),
            ], style= {'display' : 'flex', 'gap' : '10px'}),

            html.Div([
#
                html.Div([
                    #MAX DISTANCE / RESTAURANT DROPDOWN
                    dcc.Input(id='maximum_distance_input', type='number', min=1, max=30000, placeholder='Distância Máxima para Busca de Motoristas', style= {'width' : '330px', 'alignItems' : 'right'}),
                    dcc.Input(id='maximum_travel_time', type='number', placeholder='Tempo Máximo de Viagem em Minutos. Vazio = Sem Limite', style= {'width' : '330px', 'alignItems' : 'right'}),
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

    global driver_positions
    
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
def show_restaurant_marker(restaurant_id):
    if restaurant_id is None:
        return []
    
    r = BARES[restaurant_id]

    if r['NOME_FANTASIA'] != '':
        tooltip = r['NOME_FANTASIA']
    else:
        tooltip = r['NOME']

    return [dl.CircleMarker(center=[r['LATITUDE'], r['LONGITUDE']], radius=6, color='green', children=dl.Tooltip(tooltip))]



@app.callback(
    Output('nearby_driver_markers', 'children', allow_duplicate=True),
    Output('no_good_driver_markers', 'children'),
    Input('driver_distance_search_button', 'n_clicks'),
    State('maximum_distance_input', 'value'),
    State('restaurants_dropdown', 'value'),
    State('maximum_travel_time', 'value'),
    prevent_initial_call = True
)
def show_drivers_in_radius(search_button, max_dist, restaurant_id, max_travel_time):
    drivers_in_range = T.get_drivers_within_range(max_dist, BARES[restaurant_id], driver_positions)
    drivers_out_of_range = []
    for driver_id in range(len(driver_positions)):
        if driver_id in drivers_in_range:
            continue
        drivers_out_of_range.append(driver_id)


    in_range_markers = []
    out_of_range_markers = []

    etas = get_etas(BARES[restaurant_id], drivers_in_range, driver_positions, max_travel_time)

    for driver_id in drivers_in_range:
        lat = driver_positions[driver_id]['lat']
        lon = driver_positions[driver_id]['lon']

        if etas[driver_id] is not None:
            eta_text = f'{etas[driver_id]} Minutos'
        else:
            eta_text = 'Este motorista não chegará ao restaurate no tempo desejado.'

        in_range_markers.append(dl.CircleMarker(center=[lat, lon], radius=4, color='red', children=dl.Tooltip(f'{driver_positions[driver_id]['dist']:.2f} Metros de distância. Tempo Esperado de Chegada: {eta_text}')))

    for driver_id in drivers_out_of_range:
        lat = driver_positions[driver_id]['lat']
        lon = driver_positions[driver_id]['lon']
        out_of_range_markers.append(dl.CircleMarker(center=[lat, lon], radius=4, color='gray'))

    return in_range_markers, out_of_range_markers

if __name__ == "__main__":

    app.run(debug=True)
