import flet as ft
import folium
import json
import os
import time
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

def main(page: ft.Page):
    page.title = "Mapa de Clientes - Gestión"
    page.theme_mode = ft.ThemeMode.LIGHT

    # --- CONFIGURACIÓN ---
    json_file = 'clientes.json'
    map_html = 'mapa_clientes.html'
    
    # Inicializamos el geocodificador (OpenStreetMap)
    geolocator = Nominatim(user_agent="mi_app_clientes_v1")

    # --- FUNCIONES LÓGICAS ---

    def geocodificar_direccion(direccion_completa):
        """Convierte texto en lat/lon"""
        try:
            location = geolocator.geocode(direccion_completa, timeout=10)
            if location:
                return location.latitude, location.longitude
        except (GeocoderTimedOut, Exception) as e:
            print(f"Error geocodificando {direccion_completa}: {e}")
        return None, None

    def procesar_datos_y_generar_mapa():
        """Lee el JSON, completa coordenadas si faltan y crea el mapa"""
        
        # 1. Cargar datos
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                clientes = json.load(f)
        except FileNotFoundError:
            return None, "No se encontró el archivo clientes.json"

        datos_modificados = False
        
        # 2. Crear mapa base (Centrado en Guadalajara/Madrid aprox)
        m = folium.Map(location=[40.5, -3.5], zoom_start=9)
        
        # 3. Procesar cada cliente
        for cliente in clientes:
            # Si no tiene latitud, intentamos buscarla
            if "lat" not in cliente or "lon" not in cliente:
                print(f"Buscando coordenadas para: {cliente.get('Nombre', 'Sin nombre')}")
                
                # Construimos la dirección completa para mejorar precisión
                # OJO: Uso las claves exactas de tu JSON
                poblacion = cliente.get("Población ", "") # Nota el espacio extra que tenías en tu JSON
                direccion = cliente.get("Dirección", "")
                provincia = cliente.get("Provincia", "")
                
                full_address = f"{direccion}, {poblacion}, {provincia}, España"
                
                lat, lon = geocodificar_direccion(full_address)
                
                if lat and lon:
                    cliente["lat"] = lat
                    cliente["lon"] = lon
                    datos_modificados = True
                    # Pausa pequeña para no saturar el servicio gratuito de mapas
                    time.sleep(1) 
                else:
                    print(f" -- No se pudo localizar: {full_address}")
                    continue # Si no hay coords, no ponemos pin

            # 4. Añadir marcador al mapa
            if "lat" in cliente and "lon" in cliente:
                
                # HTML para el popup (lo que sale al pinchar)
                info_html = f"""
                <div style="font-family: Arial; min-width: 200px;">
                    <h4 style="margin-bottom:5px; color:#333;">{cliente.get('Nombre', 'Cliente')}</h4>
                    <hr>
                    <b>Dir:</b> {cliente.get('Dirección', '')}<br>
                    <b>Pob:</b> {cliente.get('Población ', '')}<br>
                    <b>Tel:</b> {cliente.get('Tlefono', 'N/A')}<br>
                    <b>Grupo:</b> {cliente.get('Grupo', '')}
                </div>
                """
                
                folium.Marker(
                    location=[cliente["lat"], cliente["lon"]],
                    popup=folium.Popup(info_html, max_width=300),
                    tooltip=cliente.get("Nombre"),
                    icon=folium.Icon(color="blue", icon="flag", prefix='fa')
                ).add_to(m)

        # 5. Guardar cambios en el JSON si hubo geocodificación
        if datos_modificados:
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(clientes, f, ensure_ascii=False, indent=4)
            print("JSON actualizado con nuevas coordenadas.")

        # 6. Guardar archivo HTML del mapa
        m.save(map_html)
        return os.path.abspath(map_html), "Mapa generado correctamente"

    # --- INTERFAZ GRÁFICA (FLET) ---
    
    msg_estado = ft.Text("Iniciando...", color=ft.Colors.BLUE)
    
    # Generamos el mapa y obtenemos la ruta
    ruta_mapa, mensaje = procesar_datos_y_generar_mapa()
    msg_estado.value = mensaje

    if ruta_mapa:
        # Leemos el contenido del HTML generado por Folium
        with open(ruta_mapa, "r", encoding="utf-8") as f:
            html_content = f.read()
        
        # Usamos HtmlView en lugar de WebView
        # Esto es más compatible y moderno en Flet
        web_map = ft.HtmlView(
            html_content=html_content,
            expand=True,
        )
    else:
        web_map = ft.Container(content=ft.Text("Error cargando mapa"))

    # Layout idéntico al anterior
    page.add(
        ft.Column(
            [
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.MAP_OUTLINED),
                        ft.Text("Visor de Clientes: Madrid - Toledo - Guadalajara", size=20, weight="bold")
                    ]),
                    padding=10,
                    bgcolor=ft.Colors.SURFACE_VARIANT
                ),
                msg_estado,
                ft.Container(content=web_map, expand=True)
            ],
            expand=True
        )
    )

if __name__ == "__main__":
    # Si quieres que se abra directamente en el navegador, usa ft.AppViewer.WEB_BROWSER
    ft.app(target=main)