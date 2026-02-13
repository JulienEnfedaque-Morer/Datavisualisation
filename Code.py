import pandas as pd
import xml.etree.ElementTree as ET
import folium
from folium.plugins import MarkerCluster
from datetime import datetime

# Coordonnées du centre de la France
lat_centre = 46.2276
lon_centre = 2.2137

# Définir les limites de la France (approximatif)
lat_min, lat_max = 42.0, 51.0
lon_min, lon_max = -5.0, 8.0

couleurs = ['red', 'blue', 'green', 'orange', 'purple', 'pink', 'yellow', 'gray']

# Clusters de zoom
ClustersZoom = {}
min_zoom, max_zoom = 1, 18
max_pdv = 100000

fichier = r"PrixCarburants_annuel_2025.xml"


root = ET.parse(fichier).getroot()
nberreurs = 0
rows = []
for i, pdv in enumerate(root.findall("pdv")):
    if i >= max_pdv:  break

    try:
        tous_les_prix = {}
        for prix in pdv.findall("prix"):
            nomCarb = prix.attrib.get("nom")
            
            maj_str = prix.attrib.get("maj")
            maj_dt = datetime.strptime(maj_str, "%Y-%m-%dT%H:%M:%S")

            if maj_str not in tous_les_prix or maj_dt > tous_les_prix[nomCarb]["maj_dt"]:
                tous_les_prix[nomCarb] = {
                    "maj": maj_str,
                    "maj_dt": maj_dt,
                    "valeur": float(prix.attrib.get("valeur")),
                }
        
        rows.append({
            "pdv_id": pdv.attrib.get("id"),
            "latitude": float(pdv.attrib.get("latitude"))/100000,
            "longitude": float(pdv.attrib.get("longitude"))/100000,
            "cp": pdv.attrib.get("cp"),
            "ville": pdv.findtext("ville"),
            "adresse": pdv.findtext("adresse"),
            "prix": tous_les_prix
        })
    
    except Exception as e:
        nberreurs += 1
    
df_pdv = pd.DataFrame(rows)
print(f"Nombre de pdv traités: {i}, Nombre de pdv utilisés: {len(df_pdv)}, erreurs: {nberreurs}")

print("STATIONS")
print(df_pdv)

# Sauvegarder
#df_pdv.to_csv('pdv_clean.csv', index=False)
#df_prix.to_csv('prix_clean.csv', index=False)
#df_dernier.to_csv('derniers_prix.csv', index=False)

#print("\n✓ Fichiers sauvegardés: pdv_clean.csv, prix_clean.csv, derniers_prix.csv")

carte = folium.Map(
    location=[lat_centre, lon_centre],
    zoom_start=6,  # Zoom initial
    tiles='OpenStreetMap',  # Affiche les routes, les rues, etc.
    max_bounds=True
)

groupesCarburant = {
    'SP95' : { 'object' : folium.FeatureGroup(name='SP95', show=True), 'color' : 'blue'},
    'SP98' : { 'object' : folium.FeatureGroup(name='SP98', show=True), 'color' : 'purple'},
    'E10' : { 'object' : folium.FeatureGroup(name='SP95 E10', show=True), 'color' : 'pink'},
    'Gazole' : { 'object' : folium.FeatureGroup(name='Diesel', show=True), 'color' : 'yellow'},
    'E85' : { 'object' : folium.FeatureGroup(name='Ethanol', show=True), 'color' : 'green'},
    'GPLc' : { 'object' : folium.FeatureGroup(name='GPL', show=True), 'color' : 'red'}
}

# Ajouter les groupes à la carte
for n,g in groupesCarburant.items():
    g["object"].add_to(carte)

# Ajouter des couches de contrôle pour changer les tuiles (styles de carte)
folium.TileLayer('OpenStreetMap').add_to(carte)
folium.TileLayer('CartoDB positron').add_to(carte)
folium.TileLayer('CartoDB voyager').add_to(carte)

# Ajouter le contrôle des couches
folium.LayerControl().add_to(carte)

clustersCarburant = {}

for n,g in groupesCarburant.items():
    clustersCarburant[n] = {}
    for i in range(min_zoom, max_zoom + 1):
        newCluster = MarkerCluster(options={'disableClusteringAtZoom': i}, show=True)
        newCluster.add_to(g["object"])
        clustersCarburant[n][i] = newCluster


#folium.Marker(
#    location=[random.randint(), lon_centre],
#    popup="Add popup text here.",
#    icon=folium.Icon(color="green", icon="ok-sign"),
#).add_to(marker_cluster)

dict_stations = df_pdv.to_dict(orient="records")

for st in dict_stations:
    latitude = float(st['latitude'])
    longitude = float(st['longitude'])
    taille = 15
    tous_les_prix = st['prix']
    pzoom = 12

    #infos = "Prix :"
    
    # Afficher les prix
    for carburant, d in st["prix"].items():
        #infos += "{}: {}€ (maj: {})".format(carburant, d["valeur"], d["maj"])
        
        folium.CircleMarker(
            location=[latitude, longitude],
            radius=taille,
            popup=f"{carburant}: {d['valeur']}€ (maj: {d['maj']})",
            color=groupesCarburant[carburant]["color"],
            fill=True,
            fillColor=groupesCarburant[carburant]["color"],
            fillOpacity=0.6,
            weight=1
        ).add_to(clustersCarburant[carburant][pzoom])
"""
    folium.CircleMarker(
            location=[latitude, longitude],
            radius=taille,
            popup=infos,
            color=groupesCarburant[carburant]["color"],
            fill=True,
            fillColor=groupesCarburant[carburant]["color"],
            fillOpacity=0.6,
            weight=1
        ).add_to(clustersCarburant[carburant][pzoom])
"""

    
# Sauvegarder la carte
carte.save('carte_france.html')
print("Carte sauvegardée dans 'carte_france.html'")

# Afficher la carte dans le notebook
#carte