
import networkx as nx
from math import radians, sin, cos, sqrt, asin
import json
import os

# Capitales con coordenadas
capitales = {
    "Aguascalientes": (21.8853, -102.2916),
    "Baja California": (32.5149, -117.0382),
    "Baja California Sur": (24.1426, -110.3128),
    "Campeche": (19.845, -90.5235),
    "Chiapas": (16.7539, -93.1169),
    "Chihuahua": (28.6353, -106.0889),
    "CDMX": (19.4326, -99.1332),
    "Coahuila": (25.438, -100.9733),
    "Colima": (19.2433, -103.7241),
    "Durango": (24.0277, -104.6532),
    "Estado de México": (19.2925, -99.6556),
    "Guanajuato": (21.019, -101.2574),
    "Guerrero": (17.5506, -99.5058),
    "Hidalgo": (20.1011, -98.7591),
    "Jalisco": (20.6597, -103.3496),
    "Michoacán": (19.7008, -101.1844),
    "Morelos": (18.9186, -99.2346),
    "Nayarit": (21.5058, -104.895),
    "Nuevo León": (25.6866, -100.3161),
    "Oaxaca": (17.0732, -96.7266),
    "Puebla": (19.0414, -98.2063),
    "Querétaro": (20.5888, -100.3899),
    "Quintana Roo": (21.1619, -86.8515),
    "San Luis Potosí": (22.1565, -100.9855),
    "Sinaloa": (24.8091, -107.394),
    "Sonora": (29.0729, -110.9559),
    "Tabasco": (18.0069, -92.9006),
    "Tamaulipas": (23.7369, -99.1411),
    "Tlaxcala": (19.3139, -98.2404),
    "Veracruz": (19.1903, -96.153),
    "Yucatán": (20.9674, -89.5926),
    "Zacatecas": (22.7709, -102.5832)
}

def haversine(coord1, coord2):
    from math import radians, sin, cos, sqrt, asin
    lat1, lon1 = map(radians, coord1)
    lat2, lon2 = map(radians, coord2)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    return 2 * asin(sqrt(a)) * 6371

def manhattan_km(coord1, coord2):
    # Manhattan distance: |lat1 - lat2| + |lon1 - lon2|, aproximada en km
    dlat = abs(coord1[0] - coord2[0]) * 111
    dlon = abs(coord1[1] - coord2[1]) * 111
    return dlat + dlon

def obtener_todos_lugares():
    ruta_actual = os.path.dirname(os.path.abspath(__file__))
    ruta_municipios = os.path.join(ruta_actual, "data", "municipios_mx_completo.json")
    with open(ruta_municipios, "r", encoding="utf-8") as f:
        municipios = json.load(f)
    return {**capitales, **municipios}

def construir_grafo():
    G = nx.Graph()
    lugares = obtener_todos_lugares()
    municipios = set(lugares) - set(capitales)

    for lugar, coords in lugares.items():
        G.add_node(lugar, pos=coords)

    lugares_lista = list(lugares.items())
    for i in range(len(lugares_lista)):
        nombre1, coord1 = lugares_lista[i]
        for j in range(i+1, len(lugares_lista)):
            nombre2, coord2 = lugares_lista[j]

            # Usar Manhattan si ambos son municipios
            if nombre1 in municipios and nombre2 in municipios:
                dist = manhattan_km(coord1, coord2)
            else:
                dist = haversine(coord1, coord2)

            if dist <= 3000:
                G.add_edge(nombre1, nombre2, weight=dist)

    return G
