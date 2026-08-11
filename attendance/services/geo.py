"""不依赖地图服务的 Haversine 球面距离计算。"""

from math import asin,cos,radians,sin,sqrt
def haversine_m(lat1,lng1,lat2,lng2):
 dlat=radians(float(lat2)-float(lat1)); dlng=radians(float(lng2)-float(lng1)); a=sin(dlat/2)**2+cos(radians(float(lat1)))*cos(radians(float(lat2)))*sin(dlng/2)**2
 return 6371000*2*asin(sqrt(a))
