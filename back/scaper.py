import json
import requests
from bs4 import BeautifulSoup
import os

def cargar_categorias():
    # Obtener la ruta del directorio actual del script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Construir la ruta completa al archivo categorias.json
    json_path = os.path.join(script_dir, 'categorias.json')
    
    with open(json_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def mostrar_menu_categorias(categorias):
    print("\nSeleccione una categoría:")
    for i, categoria in enumerate(categorias['categorias'], 1):
        print(f"{i}. {categoria['nombre']}")
    
    while True:
        try:
            opcion = int(input("\nIngrese el número de la categoría: "))
            if 1 <= opcion <= len(categorias['categorias']):
                return categorias['categorias'][opcion-1]
            print("Opción no válida")
        except ValueError:
            print("Por favor, ingrese un número válido")

def mostrar_menu_subcategorias(categoria):
    print(f"\nSeleccione una subcategoría de {categoria['nombre']}:")
    for i, subcategoria in enumerate(categoria['subcategorias'], 1):
        print(f"{i}. {subcategoria}")
    
    while True:
        try:
            opcion = int(input("\nIngrese el número de la subcategoría: "))
            if 1 <= opcion <= len(categoria['subcategorias']):
                return categoria['subcategorias'][opcion-1]
            print("Opción no válida")
        except ValueError:
            print("Por favor, ingrese un número válido")

def construir_url(categoria, subcategoria, busqueda):
    # Formatear los componentes de la URL
    categoria_formato = categoria.lower().replace(" ", "-").replace(",", "")
    subcategoria_formato = subcategoria.lower().replace(" ", "-").replace(",", "")
    busqueda_formato = busqueda.replace(" ", "%20")
    
    # Construir la URL
    base_url = "https://listado.mercadolibre.com.co"
    url = f"{base_url}/{categoria_formato}/{subcategoria_formato}/{busqueda}_NoIndex_True?sb=category#D[A:{busqueda_formato}]"
    return url

def scrape_mercadolibre_colombia(url, max_products=50, output_file="back/productos.txt"):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    product_links = []
    current_page = 1

    while len(product_links) < max_products:
        page_url = f"{url}_Desde_{(current_page - 1) * 50 + 1}" if current_page > 1 else url
        response = requests.get(page_url, headers=headers)

        if response.status_code != 200:
            print(f"Error al acceder a la página: {page_url}")
            break

        soup = BeautifulSoup(response.text, "html.parser")
        items = soup.find_all("a", href=True)
        
        for item in items:
            link = item.get("href")
            if "articulo.mercadolibre.com.co" in link and len(product_links) < max_products:
                if link not in product_links:
                    product_links.append(link)
            if len(product_links) >= max_products:
                break

        next_page = soup.find("a", {"title": "Siguiente"})
        if not next_page:
            break

        current_page += 1

    with open(output_file, "w", encoding="utf-8") as file:
        for link in product_links:
            file.write(link + "\n")

    print(f"Se han guardado {len(product_links)} enlaces en el archivo {output_file}.")

def main():
    # Cargar categorías desde el JSON
    categorias = cargar_categorias()
    
    # Mostrar menú de categorías y obtener selección
    categoria_seleccionada = mostrar_menu_categorias(categorias)
    
    # Mostrar menú de subcategorías y obtener selección
    subcategoria_seleccionada = mostrar_menu_subcategorias(categoria_seleccionada)
    
    # Lo que va a buscar el usuario concretamente
    busqueda = input("\n¿Qué deseas buscar?: ")
    
    # Construir URL
    url = construir_url(categoria_seleccionada['nombre'], subcategoria_seleccionada, busqueda)
    print(f"\nURL generada: {url}")
    
    # Realizar el scraping
    print("\nIniciando búsqueda de productos...")
    scrape_mercadolibre_colombia(url)

if __name__ == "__main__":
    main()