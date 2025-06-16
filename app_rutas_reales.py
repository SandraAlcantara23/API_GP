from flask import Flask, render_template, request
from rutas_manhattan import construir_grafo, capitales, obtener_todos_lugares
import networkx as nx
import folium
import random
import openrouteservice
from openrouteservice import convert

app = Flask(__name__)

@app.route('/')
def index():
    lugares = obtener_todos_lugares()
    return render_template("index_mejorado.html", lugares=sorted(lugares.keys()))

@app.route('/ruta', methods=['GET', 'POST'])
def ruta():
    if request.method == 'GET':
        lugares = obtener_todos_lugares()
        return render_template("index_mejorado.html", lugares=sorted(lugares.keys()))

    origen = request.form['origen']
    destino = request.form['destino']
    tipo_ruta = request.form.get('tipo_ruta', 'corta')
    tipos_marcados = request.form.getlist('mostrar_pois')

    G = construir_grafo()
    nodos_municipios = set(G.nodes) - set(capitales.keys())

    try:
        if tipo_ruta == 'rapida':
            for u, v, d in G.edges(data=True):
                if u in nodos_municipios and v in nodos_municipios:
                    velocidad = 40
                elif u in nodos_municipios or v in nodos_municipios:
                    velocidad = 60
                else:
                    velocidad = 80
                d['tiempo'] = d['weight'] / velocidad
            peso = 'tiempo'
        elif tipo_ruta == 'evitar_peajes':
            for u, v, d in G.edges(data=True):
                d['penalizado'] = d['weight'] + (20 if d.get('peaje', False) else 0)
            peso = 'penalizado'
        else:
            peso = 'weight'

        camino = nx.dijkstra_path(G, origen, destino, weight=peso)
        distancia_total = sum(G[camino[i]][camino[i + 1]]['weight'] for i in range(len(camino) - 1))

        tiempo_total_horas = 0
        tiempos_por_tramo = []

        for i in range(len(camino) - 1):
            a, b = camino[i], camino[i + 1]
            dist = G[a][b]['weight']
            if a in nodos_municipios and b in nodos_municipios:
                velocidad = 40
            elif a in nodos_municipios or b in nodos_municipios:
                velocidad = 60
            else:
                velocidad = 80

            t_horas = dist / velocidad
            tiempo_total_horas += t_horas
            t_h = int(t_horas)
            t_m = int((t_horas - t_h) * 60)
            tiempos_por_tramo.append(f"{a} → {b}: {round(dist, 1)} km, {t_h}h {t_m}min")

        horas = int(tiempo_total_horas)
        minutos = int((tiempo_total_horas - horas) * 60)

        # Crear mapa
        mapa = folium.Map(location=[20, -99], zoom_start=6)

        # Cliente de OpenRouteService
        client = openrouteservice.Client(key='5b3ce3597851110001cf624840ed8e401f1d4266be633afbc6408e60')

        for i in range(len(camino) - 1):
            a = camino[i]
            b = camino[i + 1]
            coord_a = G.nodes[a]['pos']
            coord_b = G.nodes[b]['pos']
            folium.Marker(location=coord_a, popup=a, icon=folium.Icon(color='blue')).add_to(mapa)

            try:
                coords = ((coord_a[1], coord_a[0]), (coord_b[1], coord_b[0]))
                ruta = client.directions(coords)
                geometry = ruta['routes'][0]['geometry']
                decoded = convert.decode_polyline(geometry)
                puntos = [(p[1], p[0]) for p in decoded['coordinates']]
                folium.PolyLine(locations=puntos, color='blue').add_to(mapa)
            except Exception as e:
                print(f"Error con tramo {a} → {b}: {e}")
                folium.PolyLine(locations=[coord_a, coord_b], color='red').add_to(mapa)

        # Último marcador
        folium.Marker(location=G.nodes[camino[-1]]['pos'], popup=camino[-1], icon=folium.Icon(color='blue')).add_to(mapa)

        # POIs
        pois = []
        for lugar in camino:
            lat, lon = G.nodes[lugar]['pos']
            for tipo in tipos_marcados:
                for _ in range(2):
                    offset_lat = lat + random.uniform(-0.1, 0.1)
                    offset_lon = lon + random.uniform(-0.1, 0.1)
                    color = 'green' if tipo == 'Gasolinera' else 'orange' if tipo == 'Restaurante' else 'purple'
                    folium.Marker(
                        location=[offset_lat, offset_lon],
                        popup=f"{tipo} en {lugar}",
                        icon=folium.Icon(color=color)
                    ).add_to(mapa)
                    pois.append({'tipo': tipo, 'estado': lugar, 'descripcion': f"{tipo} cercana"})

        mapa.save("static/mapa.html")

        # Calcular gasolina y casetas
        rendimiento_km_por_litro = 12  # km/l
        precio_gasolina = 24  # MXN/litro
        gasolina_gastada = distancia_total / rendimiento_km_por_litro
        costo_gasolina = gasolina_gastada * precio_gasolina

        # Estimar casetas: 1 cada 100 km, costo estimado $100
        casetas_probables = int(distancia_total // 100)
        costo_casetas = casetas_probables * 100

        return render_template(
            "resultado.html",
            camino=camino,
            distancia=round(distancia_total, 2),
            tiempo_total=f"{horas}h {minutos}min",
            tiempos_por_tramo=tiempos_por_tramo,
            pois=pois,
            gasolina_litros=round(gasolina_gastada, 2),
            costo_gasolina=round(costo_gasolina, 2),
            casetas=casetas_probables,
            costo_casetas=costo_casetas
        )

    except Exception as e:
        return f"No se encontró ruta válida. Error: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True)
