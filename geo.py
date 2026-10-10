GEOHASH_ALPHABET = ('0','1','2','3','4','5','6','7','8','9','b','c','d','e','f','g','h','j','k','m','n','p','q','r','s','t','u','v','w','x','y','z')
PRECISION = 8

def interpolate(x, y):
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

def gcs_to_geohash(x, y):
    x_interval = [-180, 0, 180]
    xbin = 0
    for _ in range(32):
        if x >= x_interval[1]:
            xbin += 1
            x_interval = [x_interval[1], (x_interval[2] + x_interval[1])/2, x_interval[2]]
        else:
            x_interval = [x_interval[0], (x_interval[0] + x_interval[1])/2, x_interval[1]]

        xbin <<= 1
    xbin >>= 1

    y_interval = [-90, 0, 90]
    ybin = 0
    for _ in range(32):
        if y >= y_interval[1]:
            ybin += 1
            y_interval = [y_interval[1], (y_interval[2] + y_interval[1])/2, y_interval[2]]
        else:
            y_interval = [y_interval[0], (y_interval[0] + y_interval[1])/2, y_interval[1]]

        ybin <<= 1
    ybin >>= 1

    bin_geohash = interpolate(xbin, ybin)
    mask = 0b1111100000000000000000000000000000000000000000000000000000000000
    string_geohash = ""
    for i in range(PRECISION):
        string_geohash += GEOHASH_ALPHABET[(bin_geohash & mask) >> (59 - (i*5))]
        mask >>= 5
    return string_geohash

print(gcs_to_geohash(19, -43))