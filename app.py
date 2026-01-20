import flet as ft
import folium
import json
import os
import asyncio
from geopy.geocoders import Nominatim
import webbrowser  
import pathlib
from branca.element import Template, MacroElement

# --- CLASE DE GESTIÓN DE DATOS ---
class MapManager:
    def __init__(self, json_path):
        self.json_path = json_path
        self.geolocator = Nominatim(user_agent="visor_clientes_2026")
        self.map_file = "mapa_clientes.html"

    async def obtener_coordenadas(self, cliente):
        pob = cliente.get("Población ", "").strip()
        dir_calle = cliente.get("Dirección", "").strip()
        prov = cliente.get("Provincia", "").strip()
        full_address = f"{dir_calle}, {pob}, {prov}, España"
        
        try:
            # Ejecutamos en hilo para no bloquear
            loop = asyncio.get_event_loop()
            location = await loop.run_in_executor(None, lambda: self.geolocator.geocode(full_address, timeout=10))
            if location:
                return location.latitude, location.longitude
        except:
            return None, None
        return None, None

    from branca.element import Template, MacroElement # Añade estas importaciones arriba

# ... dentro de la clase MapManager ...

    async def generar_mapa(self):
        if not os.path.exists(self.json_path):
            return False, "Error: No se encuentra el archivo JSON."

        with open(self.json_path, 'r', encoding='utf-8') as f:
            clientes = json.load(f)

        # Definición de colores
        colores_grupos = {
            "NEOPRO": "lightblue",
            "EHLIS": "red",
            "ASIDE": "cadetblue", # El más parecido a marrón en folium estándar
            "CECOFERSA": "darkred",
            "COFERDROZA": "darkblue",
            "EL SABIO": "orange",
            "FACTOR PRO": "orange",
            "GRUPO GCI": "orange"
        }

        actualizado = False
        mapa = folium.Map(location=[40.5, -3.5], zoom_start=9)

        # 1. Creamos los marcadores
        for c in clientes:
            if "lat" not in c or "lon" not in c:
                lat, lon = await self.obtener_coordenadas(c)
                if lat:
                    c["lat"], c["lon"] = lat, lon
                    actualizado = True
                    await asyncio.sleep(1) 

            if "lat" in c:
                grupo_raw = str(c.get("Grupo", "")).upper().strip()
                color_icono = colores_grupos.get(grupo_raw, "gray")
                
                poblacion = c.get("Población ", "N/A")
                
                info_popup = f"""
                <div style='font-family: Arial; font-size: 13px; width: 200px;'>
                    <b style='color: #2c3e50;'>{c.get('Nombre')}</b><br>
                    <hr>
                    <b>Población:</b> {poblacion}<br>
                    <b>Grupo:</b> {c.get('Grupo', 'Sin Grupo')}
                </div>
                """
                folium.Marker(
                    location=[c["lat"], c["lon"]],
                    popup=folium.Popup(info_popup, max_width=300),
                    tooltip=c.get("Nombre"),
                    icon=folium.Icon(color=color_icono, icon="flag")
                ).add_to(mapa)

        # 2. AÑADIR LA LEYENDA (HTML/CSS inyectado en Folium)
        template = """
        {% macro html(this, kwargs) %}
        <div id='maplegend' class='maplegend' 
            style='position: fixed; z-index:9999; border:2px solid grey; background-color:rgba(255, 255, 255, 0.8);
             border-radius:6px; padding: 10px; font-size:14px; right: 20px; bottom: 20px;'>
          <div class='legend-title'>Grupos de Clientes</div>
          <div class='legend-scale'>
            <ul class='legend-labels' style='list-style:none; padding:0; margin:0;'>
              <li><span style='background:lightblue; width:12px; height:12px; display:inline-block;'></span> Neopro</li>
              <li><span style='background:red; width:12px; height:12px; display:inline-block;'></span> Ehlis</li>
              <li><span style='background:cadetblue; width:12px; height:12px; display:inline-block;'></span> Aside</li>
              <li><span style='background:darkred; width:12px; height:12px; display:inline-block;'></span> Cecofersa</li>
              <li><span style='background:darkblue; width:12px; height:12px; display:inline-block;'></span> Coferdroza</li>
              <li><span style='background:orange; width:12px; height:12px; display:inline-block;'></span> El Sabio / Factor Pro / GCI</li>
            </ul>
          </div>
        </div>
        {% endmacro %}
        """

        macro = MacroElement()
        macro._template = Template(template)
        mapa.get_root().add_child(macro)

        if actualizado:
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(clientes, f, ensure_ascii=False, indent=4)

        mapa.save(self.map_file)
        return True, os.path.abspath(self.map_file)

# --- INTERFAZ ---
async def main(page: ft.Page):
    page.title = "Gestión de Rutas 2026"
    page.theme_mode = ft.ThemeMode.DARK
    page.vertical_alignment = "center"
    page.horizontal_alignment = "center"
    
    manager = MapManager("clientes.json")
    
    status_text = ft.Text("Listo", color=ft.Colors.GREY_400)
    loading_ring = ft.ProgressRing(visible=False, width=20, height=20)

    async def on_btn_click(e):
        btn_lanzar.disabled = True
        loading_ring.visible = True
        status_text.value = "Generando mapa..."
        page.update() 

        exito, resultado = await manager.generar_mapa() 

        loading_ring.visible = False
        btn_lanzar.disabled = False
        
        if exito:
            status_text.value = "¡Mapa abierto!"
            # Convertimos la ruta a un formato que Windows entienda perfectamente
            file_url = pathlib.Path(resultado).as_uri()
            
            # Usamos la librería estándar de Python en lugar de page.launch_url
            # Esto evita el error de ShellExecute de Flet
            webbrowser.open(file_url)
        else:
            status_text.value = resultado
        
        page.update()

    btn_lanzar = ft.Button(
        "ABRIR MAPA DE CLIENTES",
        icon=ft.Icons.EXPLORE,
        on_click=on_btn_click,
        width=300,
        height=50
    )

    # Quitamos el await de page.add()
    page.add(
        ft.Container(
            content=ft.Column(
                [
                    ft.Icon(ft.Icons.MAP_ROUNDED, size=80, color=ft.Colors.BLUE_400),
                    ft.Text("Visor Geográfico", size=30, weight="bold"),
                    ft.Text("Madrid - Toledo - Guadalajara", color=ft.Colors.BLUE_200),
                    ft.Divider(height=30, color=ft.Colors.TRANSPARENT),
                    btn_lanzar,
                    ft.Row([loading_ring, status_text], alignment="center")
                ],
                horizontal_alignment="center",
            ),
            padding=40,
            border_radius=20,
            bgcolor=ft.Colors.GREY_900,
        )
    )

if __name__ == "__main__":
    ft.app(target=main)
