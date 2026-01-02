import folium
from funciones import make_avoid_multipolygon
import pandas as pd

c = pd.read_csv("oriente avoid.csv")
c = c[["lat","lon"]].values.tolist()

x = make_avoid_multipolygon(c)

m = folium.Map(location=[6.1138, -75.3145], zoom_start=11.3)

all_vertices = []
for polygon_coords in x['coordinates']:
    for ring in polygon_coords:
        for vertex in ring:
            lat_lon = [vertex[1], vertex[0]]
            all_vertices.append(lat_lon)

unique_vertices = set(tuple(p) for p in all_vertices)

for lat, lon in unique_vertices:
    folium.Marker(location=[lat, lon], 
                  icon=folium.Icon(color='red', icon='glyphicon glyphicon-remove')).add_to(m)
folium.GeoJson(x).add_to(m)

m.save("Multipolygon.html")