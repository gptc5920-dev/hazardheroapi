from math import asin, cos, radians, sin, sqrt
def distance_km(lat1,lon1,lat2,lon2):
    dlat=radians(float(lat2)-float(lat1)); dlon=radians(float(lon2)-float(lon1)); a=sin(dlat/2)**2+cos(radians(float(lat1)))*cos(radians(float(lat2)))*sin(dlon/2)**2
    return 6371*2*asin(sqrt(a))
