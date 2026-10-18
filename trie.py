import geo
import random
from pyproj import Transformer
import osmnx as ox
from haversine import haversine, Unit

def get_graph():
    G = ox.graph_from_place('Belo Horizonte, Minas Gerais, Brazil', network_type='drive')
    ox.save_graphml(G, 'bh.graphml')

def longest_common_prefix(str1, str2):
    count = 0
    for i in range(min(len(str1), len(str2))):
        if str1[i] == str2[i]:
            count += 1
        else:
            break
    return count


class Node():
    #__slots__ = ("geohash", "children", "drivers")
    
    def __init__(self, geohash = None, children = None, drivers = None):
        self.geohash = geohash                                      #the rest of the geohash on that node
        self.children = children if children is not None else {}    #each dict element is {"first letter of the rest of the geohash on that node" : Node()} ex: "a" : Node(geohash = "abcd")
        self.drivers = drivers if drivers is not None else []       #all drivers on that geohash square (their id)


class Trie():
    def __init__(self):
        self.root = Node(geohash="")

    #Inserts a driver and its respective geohash on the trie
    def insert(self, current_node, geohash, driver_id):
        for key in current_node.children:
            if geohash[0] == key:
                if geohash != current_node.children[key].geohash:

                    lcp = longest_common_prefix(geohash, current_node.children[key].geohash)

                    if lcp == len(current_node.children[key].geohash):
                        return self.insert(current_node.children[key], geohash[lcp:], driver_id)

                    if lcp < len(current_node.children[key].geohash):
                        current_node.children[key].children = {
                            current_node.children[key].geohash[lcp] : Node(current_node.children[key].geohash[lcp:], current_node.children[key].children, current_node.children[key].drivers),
                            geohash[lcp] : Node(geohash[lcp:], {}, [driver_id])
                            }
                        current_node.children[key].geohash = geohash[:lcp]
                        current_node.children[key].drivers = []
                        return True
                else:
                    current_node.children[key].drivers.append(driver_id)
                    return True

        current_node.children[geohash[0]] = Node(geohash, {}, [driver_id])
        return True

    #Gets all drivers on a specific geohash
    def get_drivers(self, geohash):
        node = self.root
        while geohash:
            child = node.children.get(geohash[0])
            if child is None or not geohash.startswith(child.geohash):
                return []
            geohash = geohash[len(child.geohash):]
            node = child
        return node.drivers

    #Gets all drivers on an "incomplete" geohash 
    #'12345' would return drivers under geohashes '12345d', '12345c' etc, for all such geohashes in the trie
    def prefix_search(self, geohash, start = None):

        if start is None:
            start = self.root

        #Name change for clarity
        node = start

        while geohash:
            child = node.children.get(geohash[0])
            if child is None or not longest_common_prefix(geohash, child.geohash) == min(len(geohash), len(child.geohash)):
                return []
            geohash = geohash[len(child.geohash):]
            node = child

        drivers = []
        if node.children:
            for c in node.children:
                drivers += (self.prefix_search("", node.children[c]))
        else:
            return node.drivers

        return drivers 

    #restaurant should be the row refering to the restaurant in the restaurant dictionary
    def get_drivers_within_range(self, meters, restaurant, driver_positions):

        prefix_length = geo.find_prefix_length_given_radius(meters)

        restaurant_lon = float(restaurant['LONGITUDE'])
        restaurant_lat = float(restaurant['LATITUDE'])

        prefixes = geo.find_adjacent(restaurant_lon, restaurant_lat, prefix_length)

        potential_drivers = []
        for p in prefixes:
            potential_drivers += self.prefix_search(p)

        #breakpoint()

        drivers = []

        for driver in potential_drivers:
            driver_lon = driver_positions[driver]['lon']
            driver_lat = driver_positions[driver]['lat']

            distance = haversine((restaurant_lat, restaurant_lon), (driver_lat, driver_lon), unit=Unit.METERS)

            driver_positions[driver]['dist'] = distance

            if distance <= meters:
                drivers.append(driver)

        return drivers
        #breakpoint()

    def generate_drivers(self, total_drivers, sigma, BARES, GRAFO, seed = None):

        if seed is not None:
            random.seed(seed)

        #This resets the trie
        self.root = Node(geohash="")

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


        driver_id = 0
        for node in snapped_nodes:

            driver_lon = GRAFO.nodes[node]['x']
            driver_lat = GRAFO.nodes[node]['y']
            driver_geohash = geo.gcs_to_geohash(driver_lon, driver_lat)

            driver_positions.append({'lon' : driver_lon, 'lat' : driver_lat, 'x' : driver_xs[driver_id], 'y' : driver_ys[driver_id], 'geohash' : driver_geohash, 'node' : node})
            self.insert(current_node=self.root, geohash=driver_geohash, driver_id=driver_id)
            driver_id += 1    

        return driver_positions



if __name__ == "__main__":   
    BARES = geo.setup_restaurant_dict()
    GRAFO = ox.load_graphml('bh.graphml')

    T = Trie()
    driver_positions = T.generate_drivers(500, 500, BARES, GRAFO, 'toda vez que eu viajava pela estrada de ouro fino')
    T.get_drivers_within_range(500, BARES[1], driver_positions)
    breakpoint()
