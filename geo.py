import csv
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import re
from pyproj import Transformer

GEOHASH_ALPHABET = ('0','1','2','3','4','5','6','7','8','9','b','c','d','e','f','g','h','j','k','m','n','p','q','r','s','t','u','v','w','x','y','z')
PRECISION = 8

def interleave(x, y):
    mask = 0b10000000000000000000000000000000
    res = 0
    current_bit_index = 63
    while current_bit_index >= 0:
        d1 = (1 << current_bit_index) if (x & mask) > 0 else 0
        current_bit_index -= 1
        d2 = (1 << (current_bit_index)) if (y & mask) > 0 else 0
        current_bit_index -= 1
        mask >>= 1
        res += d1 + d2
    return res

def gcs_to_geohash(lon, lat):
    lon_interval = [-180, 0, 180]
    lon_bin = 0
    for _ in range(32):
        if lon >= lon_interval[1]:
            lon_bin += 1
            lon_interval = [lon_interval[1], (lon_interval[2] + lon_interval[1])/2, lon_interval[2]]
        else:
            lon_interval = [lon_interval[0], (lon_interval[0] + lon_interval[1])/2, lon_interval[1]]

        lon_bin <<= 1
    lon_bin >>= 1

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

    bin_geohash = interleave(lon_bin, lat_bin)
    mask = 0b1111100000000000000000000000000000000000000000000000000000000000
    string_geohash = ""
    for i in range(PRECISION):
        string_geohash += GEOHASH_ALPHABET[(bin_geohash & mask) >> (59 - (i*5))]
        mask >>= 5
    return string_geohash

def geohash_to_gcs(geohash):
    pass

#Os thersholds são um pouco diferentes
def find_prefix_length_given_radius(radius):
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
    elif radius < 30000:
        return 3
    
    raise ValueError(f"Área de busca grande demais. Tente uma área de no máximo 30000 metros.")

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

CNAES = set()

with open("bares.csv", "r", encoding="utf-8") as data:
    bares = csv.DictReader(data)             
    for row in bares:
        CNAES.add(row['CNAE_PRINCIPAL'])

with open("atividades_economicas.csv", "r", encoding="utf-8-sig") as data:
    with open("atividades_economicas_curado.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["_id", "NOME", "NOME_FANTASIA","GEOMETRIA", "LONGITUDE", "LATITUDE", "GEOHASH"])

        to_gcs = Transformer.from_crs("EPSG:31983", "EPSG:4326", always_xy=True)

        estabelecimentos = csv.DictReader(data)             
        for row in estabelecimentos:
            if row['CNAE_PRINCIPAL'] in CNAES:
                s = re.match(r"POINT \(([\d.]+) ([\d.]+)\)", row["GEOMETRIA"]) 
                longitude, latitude = to_gcs.transform(float(s[1]), float(s[2]))
                geohash = gcs_to_geohash(longitude, latitude)
                writer.writerow([row["_id"], row["NOME"], row["NOME_FANTASIA"], row["GEOMETRIA"], longitude, latitude, geohash])



#with open("20240926_atividade_economica.csv", "r", encoding="utf-8") as raw_data:
#    data = csv.DictReader(raw_data)
#
#    geohash_data =  {}
#    breakpoint()
#    for row in data:
#        print(row)
#    pass
#print(gcs_to_geohash(10.40744, 57.64911))