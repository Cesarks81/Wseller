from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import requests
import IA

answere = ""


def click_cargar_mas(driver):
    """Hace click en el botón 'Cargar más' dentro del shadow DOM, si existe."""
    try:
        # 1. Buscar TODOS los walla-button y quedarnos con el que tiene text="Cargar más"
        hosts = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "walla-button"))
        )

        host_cargar_mas = None
        for h in hosts:
            if h.get_attribute("text") == "Cargar más":
                host_cargar_mas = h
                break

        if host_cargar_mas is None:
            print("No se encontró el walla-button de 'Cargar más'")
            return False

        # 2. Entrar al shadowRoot
        shadow_root = driver.execute_script("return arguments[0].shadowRoot", host_cargar_mas)

        # 3. Obtener el botón real
        load_more_button = shadow_root.find_element(By.CSS_SELECTOR, "button")

        # 4. Asegurarnos de que está en pantalla y hacer click por JS
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", load_more_button)
        driver.execute_script("arguments[0].click();", load_more_button)

        print("Click en 'Cargar más'")
        return True

    except Exception as e:
        print("No se pudo hacer click en 'Cargar más':", e)
        return False


def scrape_wallapop(link, use_ia, intensidad):
    """Extrae los productos de un enlace de búsqueda de Wallapop y los guarda en productos.json."""

    chrome_options = Options()
    chrome_options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    )
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    chrome_options.add_argument("--headless")

    xpathFichaProducto = "//a[contains(@class, 'item-card_ItemCard--vertical')]"

    driver = webdriver.Chrome(options=chrome_options)
    driver.get(f"https://www.wallapop.com/app/search?keywords={link}")

    try:
        boton_rechazar = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="onetrust-reject-all-handler"]'))
        )
        boton_rechazar.click()
        print("Botón de cookies rechazado.")
    except:
        print("No se encontró el botón de cookies o ya estaba cerrado.")

    productos = []

    try:
        # 🔥 Si la intensidad es mayor que 1, intentamos cargar más resultados
        # Por ejemplo, si intensidad=3, intentamos hacer click 2 veces.
        if intensidad > 1:
            for _ in range(intensidad - 1):
                ok = click_cargar_mas(driver)
                if not ok:
                    break
                # pequeña espera para que carguen los nuevos productos
                time.sleep(2)

        # Ahora sí, buscamos todos los productos visibles
        elementos = WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.XPATH, xpathFichaProducto))
        )

        print(f"\nSe encontraron {len(elementos)} productos:\n")

        for e in elementos:
            texto = e.text.strip()
            lineas = [l.strip() for l in texto.split("\n") if l.strip() and l.strip() != "-------------"]

            if not lineas:
                continue

            estado = None
            descuento = None
            precio = None
            titulo = None
            etiqueta = None

            for linea in lineas:
                if "%" in linea:
                    descuento = linea
                elif "€" in linea and not descuento:
                    precio = linea
                elif any(k in linea for k in ["Envío", "persona"]):
                    etiqueta = linea
                elif any(k in linea for k in ["Perfil top", "Reservado", "Vendido", "Destacado"]):
                    estado = linea
                elif not any(x in linea for x in ["€", "%", "Envío", "persona", "Perfil top", "Reservado", "Vendido", "Destacado"]):
                    titulo = linea

            url = e.get_attribute("href")

            producto = {
                "url": url,
                "titulo": titulo,
                "precio": precio,
                "etiqueta": etiqueta,
                "estado": estado,
                "descuento": descuento
            }

            productos.append(producto)

        #  Preparar petición a la IA (si la usas)
        if use_ia:
            productos_json = json.dumps(productos, ensure_ascii=False)
            peticion = f"""
Analiza estos productos y elimina los que no sean realmente sobre: "{link}".

Devuélveme SOLO un array JSON válido, sin texto fuera del JSON.
Cada producto con las claves:
"url", "titulo", "precio", "etiqueta", "estado", "descuento".

Productos:
{productos_json}
"""
            answere = IA.genAsk(peticion)
        else:
            answere = productos

        return answere

    except Exception as ex:
        print("Error durante la extracción:", ex)
        return None
    finally:
        driver.quit()
