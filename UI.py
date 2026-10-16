import trie
import geo
import osmnx as ox
import random
from pyproj import Transformer

BARES = geo.setup_restaurant_dict()
GRAFO = ox.load_graphml('bh.graphml')

def generate_drivers(total_drivers, sigma, seed = None):

    if seed is not None:
        random.seed(seed)

    drivers_per_bar, remainder = divmod(total_drivers, len(BARES))

    drivers_in_each_bar = [drivers_per_bar] * len(BARES)

    #Remaining drivers are simply split randomly between restaurants
    for _ in range(remainder):
        random_bar = random.randint(0, len(BARES)-1)
        drivers_in_each_bar[random_bar] += 1

    #Since it doesnt matter which bar "generated" each driver, this list does not care about that at all. It simply stores positions where there are drivers
    driver_positions = []

    #These lists will store each drivers position in the system used by the csv file.
    #This is convenient as they are simply meters from the equator under a projection system
    #Doing this allows us to generate noise more easily later
    driver_xs = []
    driver_ys = []


    for bar in BARES:
        bar_x, bar_y = BARES[bar]['GEOMETRIA'].split()
        bar_x = float(bar_x)
        bar_y = float(bar_y)

        for driver in range(drivers_in_each_bar[bar]):
            x_driver = bar_x + random.gauss(0, sigma)
            y_driver = bar_y + random.gauss(0, sigma)

            #Due to the way the libraries being used work, it is better to do the rest of the position treatment outside the loop
            driver_xs.append(x_driver)
            driver_ys.append(y_driver)

    #Here we finally convert the points to longitude and latitude
    to_gcs = Transformer.from_crs("EPSG:31983", "EPSG:4326", always_xy=True)
    driver_lons, driver_lats = to_gcs.transform(driver_xs, driver_ys)

    snapped_nodes = ox.distance.nearest_nodes(GRAFO, X=driver_lons, Y=driver_lats)

    T = trie.Trie()

    driver_id = 0
    for node in snapped_nodes:

        driver_lon = GRAFO.nodes[node]['x']
        driver_lat = GRAFO.nodes[node]['y']
        driver_geohash = geo.gcs_to_geohash(driver_lon, driver_lat)

        driver_positions.append({'lon' : driver_lon, 'lat' : driver_lat, 'geohash' : driver_geohash})
        T.insert(current_node=T.root, geohash=driver_geohash, driver_id=driver_id)
        driver_id += 1    

    return T, driver_positions
    


if __name__ == "__main__":
    T, driver_positions = generate_drivers(50, 500, seed='gaagagasaga')
    #breakpoint()