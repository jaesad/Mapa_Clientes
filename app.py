import streamlit as st
import folium
from streamlit_folium import st_folium
from folium.plugins import LocateControl  # Plugin oficial para GPS
import requests
import os

# Creamos la memoria persistente para la sesión actual
if 'lista_negra' not in st.session_state:
    st.session_state.lista_negra = []

# --- CONFIGURACIÓN ---
# Render leerá esto desde sus "Environment Variables"
GITHUB_TOKEN = os.getenv("MY_GITHUB_TOKEN")
REPO_OWNER = "jaesad"
REPO_NAME = "Mapa_Clientes"
FILE_JSON = "Clientes.json"

@st.cache_data(ttl=600)
def obtener_datos():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_JSON}"
    headers = {'Authorization': f'token {GITHUB_TOKEN}', 'Accept': 'application/vnd.github.v3.raw'}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            return res.json()
        return None # Cambiamos a None para distinguir error de lista vacía
    except:
        return None

# --- INTERFAZ ---
st.set_page_config(page_title="Visor Clientes", layout="wide")
if 'clientes_con_x' not in st.session_state:
    st.session_state.clientes_con_x = []
st.title("📍 Visor de Clientes con GPS")

clientes = obtener_datos()

if clientes is not None:
    # --- FILTROS ---
    provincia = st.sidebar.selectbox("Provincia", ["TODAS", "MADRID", "TOLEDO", "GUADALAJARA"])
    busqueda = st.sidebar.text_input("Buscar por nombre:", "")

    # --- GESTIÓN DE CLIENTES CON X ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("📓 Registro de Visitas")
    
    nombres_para_x = sorted([str(c.get('Nombre', '')).upper() for c in clientes if isinstance(c, dict)])
    
    # El multiselect ahora se sincroniza con session_state
    clientes_con_x = st.sidebar.multiselect(
        "Marcar con X (Negro):", 
        options=nombres_para_x,
        default=st.session_state.lista_negra,
        key="selector_x"
    )
    
    # Guardamos la selección para que no se pierda al cambiar de provincia
    st.session_state.lista_negra = clientes_con_x

    # Botón para descargar el archivo de texto
    if st.session_state.lista_negra:
        texto_descarga = "\n".join(st.session_state.lista_negra)
        st.sidebar.download_button(
            label="💾 Descargar lista para borrar",
            data=texto_descarga,
            file_name="clientes_a_borrar.txt",
            mime="text/plain"
        )
        
        if st.sidebar.button("🗑️ Limpiar lista actual"):
            st.session_state.lista_negra = []
            st.rerun()

    # --- LEYENDA (Debajo de todo) ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("Leyenda de Grupos")
    # Colores
    colores_leyenda = {
        "NEOPRO": "lightblue", "EHLIS": "red", "ASIDE": "cadetblue",
        "CECOFERSA": "darkred", "COFERDROZA": "darkblue", "EL SABIO": "orange",
        "FACTOR PRO": "orange", "GRUPO GCI": "orange", "OTROS": "green"
    }
    for grupo, color in colores_leyenda.items():
        # Creamos el HTML para el circulito de color y el nombre
        st.sidebar.markdown(
            f"""
            <div style="display: flex; align-items: center; margin-bottom: 5px;">
                <div style="
                    width: 15px; 
                    height: 15px; 
                    background-color: {color}; 
                    border-radius: 50%; 
                    margin-right: 10px; 
                    border: 1px solid gray;">
                </div>
                <span style="font-size: 14px;">{grupo}</span>
            </div>
            """, 
            unsafe_allow_html=True
        )
    # Mapa (España por defecto)
    m = folium.Map(location=[40.4167, -3.7037], zoom_start=6)

    # 🌟 ACTIVA EL GPS AUTOMÁTICO
    # auto_start=True hace que el mapa te busque en cuanto se abra
    LocateControl(auto_start=True, fly_to=True).add_to(m)

    coordenadas = []
    puntos_encontrados = 0

    for c in clientes:
        if not isinstance(c, dict): continue
        
        # 1. Extraemos los datos básicos primero
        nombre_c = str(c.get('Nombre', '')).upper()
        prov_c = str(c.get("Provincia", "")).upper()
        
        # Filtro dinámico (Provincia y Búsqueda por texto)
        if (provincia == "TODAS" or provincia in prov_c) and (busqueda.upper() in nombre_c):
            try:
                lat = float(str(c.get("lat")).replace(',', '.'))
                lon = float(str(c.get("lon")).replace(',', '.'))
                
                direccion = c.get('Dirección', 'S/D')
                poblacion = c.get('Población ', 'S/P')
                grupo_raw = str(c.get("Grupo", "OTROS")).upper()
                
                # 2. DEFINIMOS EL POPUP (Esto tiene que ir antes del Marker)
                url_gps = f"https://www.google.com/maps/dir/?api=1&destination={lat},{lon}"
                
                html_popup = f"""
                <div style="font-family: Arial; min-width: 180px;">
                    <h4 style="margin:0; color: black; font-weight: bold;">{nombre_c}</h4>
                    <p style="margin:5px 0; font-size:12px;">
                        <b>📍 Ciudad:</b> {poblacion}<br>
                        <b>🏷️ Grupo:</b> {grupo_raw}
                    </p>
                    <p style="color: red; font-size: 10px;">Para marcar con X, búscalo en la lista de la izquierda.</p>
                    <a href="{url_gps}" target="_blank" style="...">🚗 CÓMO LLEGAR</a>
                </div>
                """

                # 3. LÓGICA DE LA "X" NEGRA
                marcar_negro = nombre_c in clientes_con_x
                
                if marcar_negro:
                    color_puntero = "black"
                    icono_puntero = "times" # La X
                    prefijo = "fa"
                else:
                    grupo_raw = str(c.get("Grupo", "OTROS")).upper()
                    color_puntero = colores_leyenda.get(grupo_raw, "green")
                    icono_puntero = "info-sign"
                    prefijo = "glyphicon"

                folium.Marker(
                    [lat, lon],
                    popup=folium.Popup(html_popup, max_width=250),
                    tooltip=f"{'❌ ' if marcar_negro else ''}{nombre_c}",
                    icon=folium.Icon(color=color_puntero, icon=icono_puntero, prefix=prefijo)
                ).add_to(m)
                
                coordenadas.append([lat, lon])
                puntos_encontrados += 1
            except Exception as e:
                continue

    # Mostrar Mapa
    if coordenadas:
        # 1. Si el usuario está BUSCANDO algo concreto (nombre o provincia), 
        #    forzamos la vista a esos clientes.
        if busqueda != "" or provincia != "TODAS":
            m.fit_bounds(coordenadas)
        
        # 2. Si NO hay filtros, el mapa se quedará esperando a que 
        #    el 'LocateControl' te encuentre y haga el "vuelo" a tu casa.
        
        st.success(f"Encontrados {puntos_encontrados} clientes")
        st_folium(m, width="100%", height=600, key="mapa_final")
    else:
        # Si no hay resultados, mostramos el mapa igual para que veas tu GPS
        st_folium(m, width="100%", height=600, key="mapa_vacio")
        st.warning("No se han encontrado clientes con ese nombre.")
else:
    st.error("Error 401: Render no puede conectar con GitHub. Revisa el Token en 'Environment Variables'.")