import csv
#from geopy.geocoders import Nominatim
#from geopy.extra.rate_limiter import RateLimiter
import re
from pyproj import Transformer

#the standard geohash alphabet skips 'a', 'i', 'l' and 'o'
GEOHASH_ALPHABET = ('0','1','2','3','4','5','6','7','8','9','b','c','d','e','f','g','h','j','k','m','n','p','q','r','s','t','u','v','w','x','y','z')

#this is the number of digits the geohashes will go up to
PRECISION = 8

#receives two numbers and returns the result of interleaving their binary representations
def interleave(x, y):
    #mask is 32 bits long to account for a maximum result of 64 bits; it has only a 1 on the digit we are currently adding to the interleave
    #this also means the numbers received by this function must be of at most 32 bits
    mask = 0b10000000000000000000000000000000
    res = 0
    current_bit_index = 63
    while current_bit_index >= 0:
        #digit 1 (d1) is 1 shifted to the left by current_bit_index digits if the result of a bitwise AND (&) between 'x' and the mask is not 0
        #the only digit on the mask that is 1 is the digit we are currently adding to the interleave, so this finds out if that is a 1 or a 0
        #if the current digit being added to the interleave is a 1, d1 then becomes a one followed by current_bit_index zeroes, otherwise it is simply 0
        d1 = (1 << current_bit_index) if (x & mask) > 0 else 0
        
        #we then update current_bit_index for the digit we are going to get from 'y' and do the same thing again
        current_bit_index -= 1
        d2 = (1 << (current_bit_index)) if (y & mask) > 0 else 0
        current_bit_index -= 1

        #we update mask so on the next iteration we can compare to the next digit of both numbers
        mask >>= 1

        #we add d1 and d2 to the result. since d1 and d2 never touch the same digit, this just puts a 1 wherever there is one
        res += d1 + d2
    return res

#receives a longitude and latitude pair and returns the geohash it falls into, with number of digits equal to the value specified in PRECISION
def gcs_to_geohash(lon, lat):
    lon_interval = [-180, 0, 180]

    #the binary number for the longitude that will later be interleaved starts at 0
    lon_bin = 0
    
    #for up to 32 bits we:
    for _ in range(32):
        #if our longitude is greater than or equal to the current mid point (0 for the first iteration)
        if lon >= lon_interval[1]:
            #add one to the binary number
            lon_bin += 1
            #update the interval so that the mid point becomes the left limit, the right limit becomes the previous mid point and the new mid point becomes the average between the new left and right limits
            lon_interval = [lon_interval[1], (lon_interval[2] + lon_interval[1])/2, lon_interval[2]]
        #otherwise we keep the current digit as 0 and update the interval as follows
        else:
            lon_interval = [lon_interval[0], (lon_interval[0] + lon_interval[1])/2, lon_interval[1]]

        #finally we shift the full binary number to the left so we may move on the next digit
        lon_bin <<= 1

    #since we always shift left at the end of the loop, we must shift back right once after the final iteration
    lon_bin >>= 1

    #the same thing is done for the latitude
    lat_interval = [-90, 0, 90]
    lat_bin = 0
    for _ in range(32):
        if lat >= lat_interval[1]:
            lat_bin += 1
            lat_interval = [lat_interval[1], (lat_interval[2] + lat_interval[1])/2, lat_interval[2]]
        else:
            lat_interval = [lat_interval[0], (lat_interval[0] + lat_interval[1])/2, lat_interval[1]]

        lat_bin <<= 1
    lat_bin >>= 1

    #we interleave the two binary numbers generated for longitude and latitude
    bin_geohash = interleave(lon_bin, lat_bin)

    #mask is a 64 digit binary number with 1s at the five digits that represent the current geohash digit
    mask = 0b1111100000000000000000000000000000000000000000000000000000000000
    string_geohash = ""
    for i in range(PRECISION):
        #bin_geohash & mask creates a number that has the five digits we are looking at from bin_geohash and everything else is 0
        #we then shift this number to the right until we have a number that starts with the 5 digits and has everything else as 0. that is used as an index for GEOHASH_ALPHABET
        string_geohash += GEOHASH_ALPHABET[(bin_geohash & mask) >> (59 - (i*5))]
        #we shift the mask for the next five digits
        mask >>= 5
    return string_geohash

#returns how many digits of a geohash we must use to search the area defined by a radius
def find_prefix_length_given_radius(radius):
    #these are all fixed numbers based on roughly how big a geohash cell is based on its digits
    if radius <= 0:
        raise ValueError(f"Use apenas números maiores do que 0.")
    
    if radius < 19:
        return 8
    elif radius < 143:
        return 7
    elif radius < 608:
        return 6
    elif radius < 4600:
        return 5
    elif radius < 19400:
        return 4
    #above 30000 would likely fall outside of Belo Horizonte, so we limit our search here, even though 3 digits represents an area bigger than that
    elif radius <= 30000:
        return 3
    
    raise ValueError(f"Área de busca grande demais. Tente uma área de no máximo 30000 metros.")

#this was the function used to make 'atividades_economicas_curado.csv' from the original csv file which contained information about all sorts of economic activities, rather than just restaurants
#it read all 'CNAE' values from the original 'bares.csv' and wrote to the new file only the businesses that matched a CNAE from 'bares.csv' while keeping the column that shows its geographic position
#this also translated the geographic position to latitude and longitude as well as geohash and wrote that to the new file
def treat_data():
    CNAES = set()

    with open("bares.csv", "r", encoding="utf-8") as data:
        bares = csv.DictReader(data)             
        for row in bares:
            CNAES.add(row['CNAE_PRINCIPAL'])

    with open("atividades_economicas.csv", "r", encoding="utf-8-sig") as data:
        with open("atividades_economicas_curado.csv", "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["_id", "NOME", "NOME_FANTASIA","GEOMETRIA", "LONGITUDE", "LATITUDE", "GEOHASH", "NOME_BAIRRO", "DESC_LOGRADOURO", "NOME_LOGRADOURO", "NUMERO_IMOVEL", "COMPLEMENTO"])

            to_gcs = Transformer.from_crs("EPSG:31983", "EPSG:4326", always_xy=True)

            estabelecimentos = csv.DictReader(data)             
            for row in estabelecimentos:
                if row['CNAE_PRINCIPAL'] in CNAES:
                    s = re.match(r"POINT \(([\d.]+) ([\d.]+)\)", row["GEOMETRIA"]) 
                    longitude, latitude = to_gcs.transform(float(s[1]), float(s[2]))
                    geohash = gcs_to_geohash(longitude, latitude)
                    writer.writerow([row["_id"], row["NOME"], row["NOME_FANTASIA"], f"{float(s[1])} {float(s[2])}", longitude, latitude, geohash, row["NOME_BAIRRO"], row["DESC_LOGRADOURO"], row["NOME_LOGRADOURO"], row["NUMERO_IMOVEL"], row["COMPLEMENTO"]])


#this just reads the file with all the restaurant data and turns it into a dictionary
def setup_restaurant_dict():
    bares_dict = {}
    i = 0
    with open("atividades_economicas_curado.csv", "r", encoding="utf-8-sig") as data:
        bares = csv.DictReader(data)
        for row in bares:
            row["_id"] = i
            bares_dict[row['_id']] = row
            i += 1
    return bares_dict


#this function returns a list with all the adjacent cells to the one being searched (as well as the original cell) 
def find_adjacent(lon, lat, geohash_length):

    bits = 5 * geohash_length
    w = 360 / (2 ** ((bits + 1) // 2))
    h = 180 / 2 ** (bits // 2)

    adjacent_cells = set()

    adjacent_cells.add(gcs_to_geohash(lon, lat)[:geohash_length])
    adjacent_cells.add(gcs_to_geohash(lon, lat + h)[:geohash_length])
    adjacent_cells.add(gcs_to_geohash(lon, lat - h)[:geohash_length])
    adjacent_cells.add(gcs_to_geohash(lon - w, lat - h)[:geohash_length])
    adjacent_cells.add(gcs_to_geohash(lon - w, lat)[:geohash_length])
    adjacent_cells.add(gcs_to_geohash(lon - w, lat + h)[:geohash_length])
    adjacent_cells.add(gcs_to_geohash(lon + w, lat - h)[:geohash_length])
    adjacent_cells.add(gcs_to_geohash(lon + w, lat)[:geohash_length])
    adjacent_cells.add(gcs_to_geohash(lon + w, lat + h)[:geohash_length])

    return adjacent_cells

if __name__ == "__main__":
    treat_data()
    bares = setup_restaurant_dict()


#BELOW IS THE VERSION FOR COLLECTING RESTAURANT LOCATION DATA USING A GEOLOCATION LIBRARY
#I DECIDED NOT TO USE THIS VERSION AS IT WAS FAIRLY IMPRECISE (NOT FINDING DATA BEYOND STREET, MISSING CERTAIN LOOKUPS COMPLETELY, ETC)
#IT TAKES SEVERAL HOURS TO RUN SO BE CAREFUL EXECUTING THIS

#IF YOU WANT TO RUN THIS CODE YOU MUST ALSO INSTALL GEOPY WITH 'pip install geopy'


#geolocator = Nominatim(user_agent="Geocode BH Bares")
#geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1.1, max_retries=5, error_wait_seconds=5)
#with open("bares.csv", "r", encoding="utf-8") as data:
#    bares = csv.DictReader(data)
#
#    with open("nao_encontrados.txt", "w", encoding="utf-8") as f1:
#
#        with open("encontrados.csv", "w", encoding="utf-8", newline="") as f2:
#            w2 = csv.writer(f2)
#            w2.writerow(bares.fieldnames)
#
#            with open("coordenadas.csv", "w", encoding="utf-8", newline="") as f3:
#                w3 = csv.writer(f3)
#                w3.writerow(["_id", "NOME", "NOME_FANTASIA", "LONGITUDE", "LATITUDE", "GEOHASH"])
#                
#                for row in bares:
#
#                    if row["DESC_LOGRADOURO"] == "AVE":
#                        desc_logradouro = "Avenida "
#                    elif row["DESC_LOGRADOURO"] == "RUA":
#                        desc_logradouro = "Rua "
#                    elif row["DESC_LOGRADOURO"] == "ROD":
#                        desc_logradouro = "Rodovia "
#                    elif row["DESC_LOGRADOURO"] == "PCA":
#                        desc_logradouro = "Praça "
#                    elif row["DESC_LOGRADOURO"] == "ALA":
#                        desc_logradouro = "Alameda "
#                    elif row["DESC_LOGRADOURO"] == "EST":
#                        desc_logradouro = "Estrada "
#                    elif row["DESC_LOGRADOURO"] == "BEC":
#                        desc_logradouro = "Beco "
#                    elif row["DESC_LOGRADOURO"] == "TRV":
#                        desc_logradouro = "Travessa "
#                    elif row["DESC_LOGRADOURO"] == "VIA":
#                        desc_logradouro = "Via "
#                    elif row["DESC_LOGRADOURO"] == "VDP":
#                        continue
#                    else:
#                        print(row)
#                        continue
#
#                    string = desc_logradouro + row["NOME_LOGRADOURO"].title() + ", " + row["NUMERO_IMOVEL"] + ", " + row["NOME_BAIRRO"].title()  + ", Belo Horizonte, MG, Brasil"
#                    location = geocode(string)
#
#                    if location is None:
#                        string = desc_logradouro + row["NOME_LOGRADOURO"].title() + ", " + row["NUMERO_IMOVEL"] + ", Belo Horizonte, MG, Brasil"
#                        location = geocode(string)
#
#                    if location is None:
#                        f1.write(f"{string} ------- {row}\n")
#
#                    else:
#                        geohash = gcs_to_geohash(location.longitude, location.latitude)
#                        print(f"Encontrado {string}, Geohash = {geohash}")
#                        w2.writerow(row.values())
#                        w3.writerow([row["_id"], row["NOME"], row["NOME_FANTASIA"], location.longitude, location.latitude, geohash])