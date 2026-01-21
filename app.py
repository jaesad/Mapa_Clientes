import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import os
import json

# --- CONFIGURACIÓN SEGURA ---
# Streamlit leerá esto de las "Secrets" o "Environment Variables" en Render
GITHUB_TOKEN = os.getenv("MY_GITHUB_TOKEN") 
REPO_OWNER = "jaesad"
REPO_NAME = "Mapa_Clientes"
FILE_JSON = "Clientes.json"

def obtener_datos():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_JSON}"
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3.raw'
    }
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            return res.json()
        return []
    except Exception as e:
        st.error(f"Error al conectar con GitHub: {e}")
        return []

# Configuración de la página
st.set_page_config(page_title="Visor de Clientes 2026", layout="wide")

st.title("📍 Visor de Clientes Interactivo")
st.sidebar.header("Filtros")

# Selector de provincia
provincia_seleccionada = st.sidebar.selectbox(
    "Selecciona una Provincia",
    ["TODAS", "MADRID", "TOLEDO", "GUADALAJARA", "CUENCA", "CIUDAD REAL", "ALBACETE"]
)

if st.sidebar.button("ACTUALIZAR MAPA"):
    with st.spinner("Cargando datos de clientes..."):
        clientes = obtener_datos()
        
        # Crear mapa base centrado en España
        m = folium.Map(location=[40.4167, -3.7037], zoom_start=6)
        
        colores = {
            "NEOPRO": "lightblue",
            "EHLIS": "red",
            "ASIDE": "black",
            "CECOFERSA": "purple"
        }

        # Añadir marcadores
        puntos_añadidos = 0
        for c in clientes:
            if not isinstance(c, dict): continue
            
            prov_cliente = str(c.get("Provincia", "")).upper()
            
            if provincia_seleccionada == "TODAS" or provincia_seleccionada in prov_cliente:
                try:
                    lat = float(str(c.get("lat")).replace(',', '.'))
                    lon = float(str(c.get("lon")).replace(',', '.'))
                    grupo = str(c.get("Grupo", "")).upper()
                    color = colores.get(grupo, "green")
                    
                    folium.Marker(
                        [lat, lon],
                        popup=f"<b>{c['Nombre']}</b><br>Grupo: {grupo}",
                        tooltip=c['Nombre'],
                        icon=folium.Icon(color=color, icon="info-sign")
                    ).add_to(m)
                    puntos_añadidos += 1
                except:
                    continue
        
        if puntos_añadidos > 0:
            st.success(f"Se han encontrado {puntos_añadidos} clientes en {provincia_seleccionada}")
            # Mostrar el mapa de forma nativa
            st_folium(m, width="100%", height=600)
        else:
            st.warning("No se encontraron clientes para esta selección.")
else:
    st.info("Usa el menú de la izquierda para filtrar y pulsa 'ACTUALIZAR MAPA'")