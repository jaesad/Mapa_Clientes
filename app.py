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

@st.cache_data(ttl=600) # Guardamos los datos 10 min para que la búsqueda sea instantánea
def obtener_datos():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_JSON}"
    headers = {'Authorization': f'token {GITHUB_TOKEN}', 'Accept': 'application/vnd.github.v3.raw'}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            return res.json()
        return []
    except:
        return []

# --- INTERFAZ STREAMLIT ---
st.set_page_config(page_title="Visor Clientes",
                   page_icon="https://raw.githubusercontent.com/jaesad/Mapa_Clientes/main/logo.png", 
                   layout="wide")
st.title("📍 Visor de Clientes con GPS")

# --- SIDEBAR ---
st.sidebar.header("Filtros")
provincia = st.sidebar.selectbox("Provincia", ["TODAS", "MADRID", "TOLEDO", "GUADALAJARA"])
# Al cambiar el texto aquí, todo el mapa se actualizará solo
busqueda = st.sidebar.text_input("Buscar por nombre:", "")

st.sidebar.markdown("---")
st.sidebar.subheader("Leyenda de Grupos")

colores_dict = {
    "NEOPRO": "lightblue",
    "EHLIS": "red",
    "ASIDE": "cadetblue",
    "CECOFERSA": "darkred",
    "COFERDROZA": "darkblue",
    "EL SABIO": "orange",
    "FACTOR PRO": "orange",
    "GRUPO GCI": "orange",
    "OTROS": "green"
}

for grupo, color in colores_dict.items():
    st.sidebar.markdown(
        f'<div style="display: flex; align-items: center; margin-bottom: 5px;"><div style="width: 15px; height: 15px; background-color: {color}; border-radius: 50%; margin-right: 10px; border: 1px solid gray;"></div><span style="font-size: 14px;">{grupo}</span></div>', 
        unsafe_allow_html=True
    )

# --- LÓGICA DEL MAPA ---
clientes = obtener_datos()

if clientes:
    m = folium.Map(location=[40.4167, -3.7037], zoom_start=6)
    coordenadas = []
    puntos_encontrados = 0

    for c in clientes:
        if not isinstance(c, dict): continue
        
        # Limpiamos los datos para comparar
        nombre_c = str(c.get('Nombre', '')).upper()
        prov_c = str(c.get("Provincia", "")).upper()
        termino_busqueda = busqueda.upper()
        
        # FILTRO DINÁMICO
        if (provincia == "TODAS" or provincia in prov_c) and (termino_busqueda in nombre_c):
            try:
                lat = float(str(c.get("lat")).replace(',', '.'))
                lon = float(str(c.get("lon")).replace(',', '.'))
                
                direccion = c.get('Dirección', 'S/D')
                poblacion = c.get('Población ', 'S/P')
                grupo_raw = str(c.get("Grupo", "OTROS")).upper()
                color_puntero = colores_dict.get(grupo_raw, "green")
                
                url_gps = f"https://www.google.com/maps/dir/?api=1&destination={lat},{lon}"
                
                html_popup = f"""
                <div style="font-family: Arial; min-width: 180px;">
                    <h4 style="margin:0; color: black; font-weight: bold;">{nombre_c}</h4>
                    <p style="margin:5px 0; font-size:12px;">
                        <b>📍 Ciudad:</b> {poblacion}<br>
                        <b>🏠 Dir:</b> {direccion}<br>
                        <b>🏷️ Grupo:</b> {grupo_raw}
                    </p>
                    <a href="{url_gps}" target="_blank" 
                       style="background-color: #1D3557; color: white; padding: 10px; 
                              text-decoration: none; border-radius: 5px; font-weight: bold; 
                              display: block; text-align: center; margin-top: 10px;">
                       🚗 CÓMO LLEGAR
                    </a>
                </div>
                """
                
                folium.Marker(
                    [lat, lon], 
                    popup=folium.Popup(html_popup, max_width=250),
                    tooltip=nombre_c,
                    icon=folium.Icon(color=color_puntero, icon="info-sign")
                ).add_to(m)
                
                coordenadas.append([lat, lon])
                puntos_encontrados += 1
            except:
                continue

    # Si hay puntos, ajustamos el zoom y mostramos el mapa
    if coordenadas:
        m.fit_bounds(coordenadas)
        st.success(f"Encontrados {puntos_encontrados} clientes")
        st_folium(m, width="100%", height=600, returned_objects=[], key="mapa_dinamico")
    else:
        st.warning("No se han encontrado clientes con ese nombre en esa provincia.")
else:
    st.error("No se han podido cargar los datos de GitHub.")