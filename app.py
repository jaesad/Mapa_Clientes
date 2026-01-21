import flet as ft
import folium
import json
import os
import asyncio
import webbrowser
import pathlib
from geopy.geocoders import Nominatim
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
            loop = asyncio.get_event_loop()
            location = await loop.run_in_executor(None, lambda: self.geolocator.geocode(full_address, timeout=10))
            if location: return location.latitude, location.longitude
        except: return None, None
        return None, None

    async def generar_mapa(self, provincia_filtro="TODAS"):
        if not os.path.exists(self.json_path):
            return False, "Error: No se encuentra el archivo JSON."

        with open(self.json_path, 'r', encoding='utf-8') as f:
            clientes = json.load(f)

        colores_grupos = {
            "NEOPRO": "lightblue", "EHLIS": "red", "ASIDE": "black",
            "CECOFERSA": "purple", "COFERDROZA": "darkblue",
            "EL SABIO": "orange", "FACTOR PRO": "orange", "GRUPO GCI": "orange"
        }

        # Configuración de centros por provincia
        centros = {
            "MADRID": [40.4167, -3.7037],
            "TOLEDO": [39.8628, -4.0273],
            "GUADALAJARA": [40.6333, -3.1667],
            "TODAS": [40.2, -3.7]
        }
        
        centro = centros.get(provincia_filtro, centros["TODAS"])
        zoom = 10 if provincia_filtro != "TODAS" else 8
        mapa = folium.Map(location=centro, zoom_start=zoom)

        actualizado = False
        for c in clientes:
            prov_cliente = str(c.get("Provincia", "")).upper().strip()
            
            # FILTRO DE PROVINCIA
            if provincia_filtro != "TODAS" and prov_cliente != provincia_filtro:
                continue

            if "lat" not in c or "lon" not in c:
                lat, lon = await self.obtener_coordenadas(c)
                if lat:
                    c["lat"], c["lon"] = lat, lon
                    actualizado = True
                    await asyncio.sleep(1)

            if "lat" in c:
                # 2. Lógica para asignar VERDE si no hay grupo
                grupo_raw = str(c.get("Grupo", "")).strip()
                
                if grupo_raw == "" or grupo_raw.upper() == "NAN":
                    color_icono = "green"
                    grupo_display = "Sin Grupo"
                else:
                    color_icono = colores_grupos.get(grupo_raw.upper(), "green") # Verde por defecto
                    grupo_display = grupo_raw

                nombre = c.get('Nombre', 'Cliente')
                direccion = c.get('Dirección', 'No disponible')
                poblacion = c.get('Población ', 'No disponible')
                
                info_popup = f"""
                <div style='font-family: Arial; font-size: 13px; width: 220px;'>
                    <b style='color: #2c3e50; font-size: 15px;'>{nombre}</b><br>
                    <hr style='margin: 8px 0;'>
                    <b>Dirección:</b> {direccion}<br>
                    <b>Población:</b> {poblacion}<br>
                    <b>Grupo:</b> {grupo_display}
                </div>"""
                
                folium.Marker(
                    location=[c["lat"], c["lon"]],
                    popup=folium.Popup(info_popup, max_width=320),
                    tooltip=nombre,
                    icon=folium.Icon(color=color_icono, icon="flag")
                ).add_to(mapa)

        # 2. AÑADIR LA LEYENDA ACTUALIZADA
        template = """
        {% macro html(this, kwargs) %}
        <div id='maplegend' class='maplegend' 
            style='position: fixed; z-index:9999; border:2px solid grey; background-color:rgba(255, 255, 255, 0.8);
             border-radius:6px; padding: 10px; font-size:13px; right: 20px; bottom: 20px; font-family: Arial;'>
        <div style='font-weight: bold; margin-bottom: 5px;'>Grupos de Clientes</div>
        <div class='legend-scale'>
            <ul class='legend-labels' style='list-style:none; padding:0; margin:0;'>
              <li><span style='background:lightblue; width:12px; height:12px; display:inline-block; border:1px solid #666;'></span> Neopro</li>
              <li><span style='background:red; width:12px; height:12px; display:inline-block; border:1px solid #666;'></span> Ehlis</li>
              <li><span style='background:black; width:12px; height:12px; display:inline-block; border:1px solid #666;'></span> Aside</li>
              <li><span style='background:purple; width:12px; height:12px; display:inline-block; border:1px solid #666;'></span> Cecofersa</li>
              <li><span style='background:darkblue; width:12px; height:12px; display:inline-block; border:1px solid #666;'></span> Coferdroza</li>
              <li><span style='background:orange; width:12px; height:12px; display:inline-block; border:1px solid #666;'></span> Sabio / Factor Pro / GCI</li>
              <li><span style='background:green; width:12px; height:12px; display:inline-block; border:1px solid #666;'></span> Sin Grupo / Otros</li>
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
    page.title = "Gestor de Mapas 2026"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width, page.window_height = 500, 600
    page.vertical_alignment = "center"
    page.horizontal_alignment = "center"
    
    manager = MapManager("clientes.json")
    
    # Selector de Provincia
    selector_provincia = ft.Dropdown(
        label="Selecciona Provincia",
        width=300,
        options=[
            ft.dropdown.Option("TODAS"),
            ft.dropdown.Option("MADRID"),
            ft.dropdown.Option("TOLEDO"),
            ft.dropdown.Option("GUADALAJARA"),
        ],
        value="TODAS",
    )
    
    status_text = ft.Text("Listo", color=ft.Colors.GREY_400)
    loading_ring = ft.ProgressRing(visible=False, width=20, height=20)

    async def on_btn_click(e):
        btn_lanzar.disabled = True
        loading_ring.visible = True
        status_text.value = f"Generando mapa de {selector_provincia.value}..."
        page.update()

        exito, resultado = await manager.generar_mapa(selector_provincia.value)

        loading_ring.visible = False
        btn_lanzar.disabled = False
        
        if exito:
            status_text.value = "Mapa abierto correctamente"
            file_url = pathlib.Path(resultado).as_uri()
            webbrowser.open(file_url)
        else:
            status_text.value = resultado
        page.update()

    btn_lanzar = ft.Button(
        "GENERAR Y ABRIR MAPA",
        icon=ft.Icons.EXPLORE,
        on_click=on_btn_click,
        width=300,
        height=50
    )

    page.add(
        ft.Container(
            content=ft.Column(
                [
                    ft.Icon(ft.Icons.LOCATION_ON, size=60, color=ft.Colors.BLUE_400),
                    ft.Text("Filtro Geográfico", size=25, weight="bold"),
                    ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                    selector_provincia,
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
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