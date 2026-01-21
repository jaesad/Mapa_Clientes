import flet as ft
import folium
import json
import requests
import base64
import os

# --- CONFIGURACIÓN ---
# He puesto tus datos de GitHub para que funcione nada más desplegar
GITHUB_TOKEN = os.getenv("MY_GITHUB_TOKEN") 
REPO_OWNER = "jaesad"
REPO_NAME = "Mapa_Clientes"
FILE_JSON = "Clientes.json"

# Verificación de seguridad para la consola
if not GITHUB_TOKEN:
    print("ERROR: No se ha encontrado la Variable de Entorno MY_GITHUB_TOKEN")
    
class MapManager:
    def obtener_datos(self):
        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_JSON}"
        headers = {
            'Authorization': f'token {GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3.raw'
        }
        try:
            res = requests.get(url, headers=headers)
            if res.status_code == 200:
                clientes = res.json()
                # Si GitHub devuelve un string, lo cargamos como JSON
                if isinstance(clientes, str):
                    return json.loads(clientes)
                return clientes
            return []
        except Exception as e:
            print(f"Error descargando datos: {e}")
            return []

    def crear_mapa_html(self, provincia_filtro):
        clientes = self.obtener_datos()
        # Centro de España
        mapa = folium.Map(location=[40.4167, -3.7037], zoom_start=6)
        
        colores = {
            "NEOPRO": "lightblue", 
            "EHLIS": "red", 
            "ASIDE": "black", 
            "CECOFERSA": "purple"
        }

        for c in clientes:
            if not isinstance(c, dict): continue
            prov = str(c.get("Provincia", "")).upper()
            
            if provincia_filtro == "TODAS" or provincia_filtro in prov:
                try:
                    lat = float(str(c.get("lat")).replace(',', '.'))
                    lon = float(str(c.get("lon")).replace(',', '.'))
                    grupo = str(c.get("Grupo", "")).upper()
                    color = colores.get(grupo, "green")
                    
                    folium.Marker(
                        [lat, lon], 
                        popup=f"<b>{c['Nombre']}</b>",
                        tooltip=c['Nombre'],
                        icon=folium.Icon(color=color, icon="flag")
                    ).add_to(mapa)
                except:
                    continue
        
        # Esta línea es la clave: convierte el mapa en texto HTML para mostrarlo en la web
        return mapa._repr_html_()

async def main(page: ft.Page):
    page.title = "Visor Clientes Online"
    page.theme_mode = "dark"
    page.padding = 20
    
    manager = MapManager()
    
    # Este componente mostrará el mapa dinámicamente
    mapa_web = ft.Html(value="", expand=True)
    
    # Texto de estado
    status = ft.Text("Selecciona una provincia y pulsa Ver Mapa", size=12, color="grey")
    loading = ft.ProgressBar(visible=False, width=400)

    async def mostrar_mapa(e):
        loading.visible = True
        status.value = "Cargando datos de GitHub y generando mapa..."
        page.update()
        
        # Generamos el HTML del mapa
        html_content = manager.crear_mapa_html(selector.value)
        
        # Lo "inyectamos" en la interfaz
        mapa_web.value = html_content
        
        loading.visible = False
        status.value = f"Mostrando clientes de: {selector.value}"
        page.update()

    selector = ft.Dropdown(
        label="Provincia",
        width=250,
        options=[
            ft.dropdown.Option("TODAS"),
            ft.dropdown.Option("MADRID"),
            ft.dropdown.Option("TOLEDO"),
            ft.dropdown.Option("GUADALAJARA"),
        ],
        value="TODAS"
    )

    page.add(
        ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.MAP_SHARP, color="blue"),
                ft.Text("Buscador de Clientes 2026", size=20, weight="bold")
            ], alignment="center"),
            ft.Row([selector, ft.ElevatedButton("VER MAPA", on_click=mostrar_mapa, icon=ft.Icons.SEARCH)], alignment="center"),
            loading,
            status,
            ft.Container(content=mapa_web, expand=True, border=ft.border.all(1, "grey"), border_radius=10)
        ], expand=True)
    )

# Configuración para servidores en la nube (Render/Heroku/Fly.io)
if __name__ == "__main__":
    # El puerto lo asigna el servidor automáticamente
    port = int(os.getenv("PORT", 8080))
    ft.run(main, port=port)