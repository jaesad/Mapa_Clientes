import flet as ft
import folium
import json
import requests
import base64
import os

# --- CONFIGURACIÓN SEGURA ---
GITHUB_TOKEN = os.getenv("MY_GITHUB_TOKEN") 
REPO_OWNER = "jaesad"
REPO_NAME = "Mapa_Clientes"
FILE_JSON = "Clientes.json"

class MapManager:
    def obtener_datos(self):
        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_JSON}"
        headers = {'Authorization': f'token {GITHUB_TOKEN}', 'Accept': 'application/vnd.github.v3.raw'}
        try:
            res = requests.get(url, headers=headers)
            if res.status_code == 200:
                # Si el repo es público o usamos el raw, a veces viene como texto plano
                return res.json()
            return []
        except:
            return []

    def crear_mapa_html(self, provincia_filtro):
        clientes = self.obtener_datos()
        mapa = folium.Map(location=[40.4167, -3.7037], zoom_start=6)
        
        colores = {"NEOPRO": "lightblue", "EHLIS": "red", "ASIDE": "black", "CECOFERSA": "purple"}

        for c in clientes:
            if not isinstance(c, dict): continue
            prov = str(c.get("Provincia", "")).upper()
            if provincia_filtro == "TODAS" or provincia_filtro in prov:
                try:
                    lat = float(str(c.get("lat")).replace(',', '.'))
                    lon = float(str(c.get("lon")).replace(',', '.'))
                    color = colores.get(str(c.get("Grupo", "")).upper(), "green")
                    folium.Marker([lat, lon], popup=c['Nombre'], 
                                  icon=folium.Icon(color=color, icon="flag")).add_to(mapa)
                except: continue
        
        return mapa._repr_html_()

async def main(page: ft.Page):
    page.title = "Mapa de Clientes 2026"
    page.horizontal_alignment = "center"
    page.vertical_alignment = "center"
    page.theme_mode = "dark"
    
    manager = MapManager()
    
    status = ft.Text("Selecciona provincia y pulsa el botón", color="grey")
    loading = ft.ProgressBar(visible=False, width=300)

    async def mostrar_mapa(e):
        loading.visible = True
        status.value = "Generando mapa..."
        page.update()
        
        try:
            # 1. Generamos el HTML
            html_content = manager.crear_mapa_html(selector.value)
            
            # 2. Lo convertimos a Base64 para que el navegador lo entienda como una URL
            b64_html = base64.b64encode(html_content.encode()).decode()
            data_url = f"data:text/html;base64,{b64_html}"
            
            # 3. LANZAMOS LA URL (Esto abre el mapa en una pestaña nueva del móvil)
            await page.launch_url(data_url)
            
            status.value = "¡Mapa abierto en pestaña nueva!"
        except Exception as ex:
            status.value = f"Error: {str(ex)}"
        
        loading.visible = False
        page.update()

    selector = ft.Dropdown(
        label="Provincia",
        width=300,
        options=[ft.dropdown.Option("TODAS"), ft.dropdown.Option("MADRID"), 
                 ft.dropdown.Option("TOLEDO"), ft.dropdown.Option("GUADALAJARA")],
        value="TODAS"
    )

    page.add(
        ft.Icon(ft.Icons.MAP_ROUNDED, size=50, color="blue"),
        ft.Text("Visor de Clientes", size=24, weight="bold"),
        selector,
        ft.ElevatedButton("ABRIR MAPA INTERACTIVO", on_click=mostrar_mapa, icon=ft.Icons.OPEN_IN_BROWSER),
        loading,
        status
    )

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))    
    ft.run(main, port=port)