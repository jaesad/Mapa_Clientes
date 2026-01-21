import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import os

# --- CONFIGURACIÓN ---
GITHUB_TOKEN = os.getenv("MY_GITHUB_TOKEN")  
REPO_OWNER = "jaesad"
REPO_NAME = "Mapa_Clientes"
FILE_JSON = "Clientes.json"

def obtener_datos():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_JSON}"
    headers = {'Authorization': f'token {GITHUB_TOKEN}', 'Accept': 'application/vnd.github.v3.raw'}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            datos = res.json()
            # ESTO TE DIRÁ EN PANTALLA SI HAY DATOS
            st.sidebar.write(f"✅ Datos cargados: {len(datos)} registros")
            return datos
        else:
            st.sidebar.error(f"❌ Error GitHub: {res.status_code}")
            return []
    except Exception as e:
        st.sidebar.error(f"❌ Error conexión: {e}")
        return []

# --- INTERFAZ STREAMLIT ---
st.set_page_config(page_title="Visor Clientes", layout="wide")
st.title("📍 Visor de Clientes")

# Sidebar
provincia = st.sidebar.selectbox("Provincia", ["TODAS", "MADRID", "TOLEDO", "GUADALAJARA"])
boton_cargar = st.sidebar.button("VER MAPA")

if boton_cargar:
    with st.spinner("Generando mapa..."):
        clientes = obtener_datos()
        
        m = folium.Map(location=[40.4167, -3.7037], zoom_start=6)
        colores = {"NEOPRO": "lightblue", "EHLIS": "red", "ASIDE": "black", "CECOFERSA": "purple"}

        # --- CAMBIO AQUÍ: Creamos una lista para guardar las coordenadas ---
        coordenadas = [] 

        for c in clientes:
            if not isinstance(c, dict): continue
            prov_c = str(c.get("Provincia", "")).upper()
            if provincia == "TODAS" or provincia in prov_c:
                try:
                    lat = float(str(c.get("lat")).replace(',', '.'))
                    lon = float(str(c.get("lon")).replace(',', '.'))
                    
                    folium.Marker(
                        [lat, lon], 
                        popup=c.get('Nombre', 'Cliente'),
                        icon=folium.Icon(color=colores.get(str(c.get("Grupo")).upper(), "green"))
                    ).add_to(m)
                    
                    # Guardamos la coordenada para el zoom
                    coordenadas.append([lat, lon]) 
                except: continue
        
        # --- PUNTO 1: ZOOM AUTOMÁTICO ---
        if coordenadas:
            # Esta línea calcula el recuadro que envuelve a todos los puntos y ajusta el mapa
            m.fit_bounds(coordenadas) 
            st.success(f"📍 Mostrando {len(coordenadas)} clientes")
        else:
            st.warning("No se han encontrado clientes para esta selección.")

        # Mostrar el mapa
        st_folium(m, width=700, height=500, returned_objects=[], key="mapa_final")
else:
    st.info("Selecciona una provincia en el panel lateral y pulsa 'VER MAPA'.")