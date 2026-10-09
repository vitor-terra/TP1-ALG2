GEOHASH_ALPHABET = ('0','1','2','3','4','5','6','7','8','9','b','c','d','e','f','g','h','j','k','m','n','p','q','r','s','t','u','v','w','x','y','z')
def interpolate(x, y):
    mask = 0b1000000000000000
    res = 0
    for i in range(31,0, -2):
        #breakpoint()
        d1 = (1 << i) if (x & mask) > 0 else 0
        d2 = (1 << (i - 1)) if (y & mask) > 0 else 0
        mask >>= 1
        res += d1 + d2
    return res

def gcs_to_geohash(x, y):
    x_interval = [-180, 0, 180]
    xbin = 0
    for _ in range(15):
        if x >= x_interval[1]:
            xbin += 1
            x_interval = [x_interval[1], (x_interval[2] + x_interval[1])/2, x_interval[2]]
        else:
            x_interval = [x_interval[0], (x_interval[0] + x_interval[1])/2, x_interval[1]]
        print(bin(xbin))
        print(x_interval)
        xbin <<= 1

    y_interval = [-90, 0, 90]
    ybin = 0
    for _ in range(15):
        if y >= y_interval[1]:
            ybin += 1
            y_interval = [y_interval[1], (y_interval[2] + y_interval[1])/2, y_interval[2]]
        else:
            y_interval = [y_interval[0], (y_interval[0] + y_interval[1])/2, y_interval[1]]
        print(bin(ybin))
        print(y_interval)
        ybin <<= 1
    

    return (xbin, ybin)

#x, y = gcs_to_geohash(19, -43)

print(bin(interpolate(0b1111111111111111, 0)))
#print(bin(x))
#print(bin(y))