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

print(gcs_to_geohash(10.40744, 57.64911))