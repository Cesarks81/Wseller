from customtkinter import *
from threading import Thread
import os
import SCRAPPER
import json

# -----------   INSTANCIACIÓN DE VARIABLES
anchoButtom = 150
altoButtom = 47
contador_activo = False
segundos_transcurridos = 0

# -----------   INSTANCIACIÓN DE GUI + CONFIGURACIÓN 
app = CTk()
app.geometry("1400x900")
app.title("W-SELLER")
app.resizable(False, False)
app.config(background="#CCD5F4")

textBusqueda = StringVar()
ia_var = BooleanVar(value=True)
premium_var = BooleanVar(value=True)
# -----------   CLASE PARA MOSTRAR PRODUCTOS
class DataBlock:
    def __init__(self, box, data):
        self.box = box
        self.data = data

        # Número de filas existentes para añadir debajo
        current_rows = box.grid_size()[1]  # grid_size() -> (cols, rows)

        for i, producto in enumerate(data):
            titulo = producto.get("titulo", "")
            precio = producto.get("precio", "")
            url = producto.get("url", "")
            estado = producto.get("estado", "")

            CTkLabel(
                box,
                text=titulo,
                anchor="w",
                width=700,
                height=20,
                font=("Arial", 20, "bold")
            ).grid(row=current_rows + i, column=0, sticky="w", pady=2)

            CTkLabel(
                box,
                text=precio,
                anchor="w",
                width=200,
                height=20,
                font=("Arial", 20, "bold")
            ).grid(row=current_rows + i, column=1, sticky="w", pady=2)

            CTkButton(
                box,
                text="🌐",
                bg_color="black",
                width=50,
                command=lambda url=url: os.system(f"start {url}")
            ).grid(row=current_rows + i, column=2, sticky="w", pady=2)

            CTkLabel(
                box,
                text=f" ---> {str(estado)}" if estado is not None else "",
                anchor="w",
                width=200,
                height=20,
                font=("Arial", 20, "bold")
            ).grid(row=current_rows + i, column=3, sticky="w", pady=2)

        print(f"{len(data)} productos añadidos a la interfaz.")


# -----------   CRONÓMETRO
def iniciar_cronometro():
    global contador_activo, segundos_transcurridos
    contador_activo = True
    segundos_transcurridos = 0
    actualizar_cronometro(0)

def actualizar_cronometro(segundos):
    global contador_activo, segundos_transcurridos

    if not contador_activo:
        return  # Si el scrapper terminó, no seguimos contando

    segundos_transcurridos = segundos
    timer_labelDinamic.configure(text=f"{segundos}s")
    app.after(1000, lambda: actualizar_cronometro(segundos + 1))

def marcar_scraper_terminado():
    global contador_activo
    contador_activo = False
    timer_labelDinamic.configure(text=f"Terminado en {segundos_transcurridos}s")


# -----------   FUNCIONALIDAD DEL BOTÓN / SCRAPPER
def getUrl(link, use_ia, use_notPremium):
    # ⚠️ Esta función se ejecuta en un THREAD
    answer = SCRAPPER.scrape_wallapop(link, use_ia, intensidad=2)

    # Esta función se ejecuta en el hilo principal (GUI)
    def actualizar_gui_despues_scraper():
        # 1) Parar contador y mostrar tiempo final
        marcar_scraper_terminado()

        # 2) Procesar la respuesta
        if answer is None or (isinstance(answer, str) and not answer.strip()):
            print("La respuesta del scrapper/IA está vacía o es None:")
            return

        # 🔹 Si ya es una lista/dict de Python, NO usamos json.loads
        if isinstance(answer, (list, dict)):
            data = answer
        else:
            # Aquí asumimos que es un string que debería ser JSON (viene de Gemini)
            answer_clean = (
                str(answer)
                .strip()
                .replace("```json", "")
                .replace("```", "")
            )

            start = answer_clean.find("[")
            end = answer_clean.rfind("]") + 1
            if start != -1 and end != -1:
                answer_clean = answer_clean[start:end]

            try:
                data = json.loads(answer_clean)   # ← lista de productos (dicts)

            except Exception as e:
                print("Error al convertir a JSON:", e)
                print("Contenido recibido (repr):", repr(answer_clean))
                return
        if use_notPremium.get():
            data = [p for p in data if p.get("estado") != "Perfil top"]
        # Llegados aquí, data SIEMPRE es una lista/dict Python
        print("JSON/Lista parseado correctamente.")
        try:
            countProductdinamic.configure(text=str(len(data)))
        except TypeError:
            # por si data es un dict en algún caso raro
            countProductdinamic.configure(text=str(len(list(data))))

        # Limpiar resultados anteriores del frame
        for widget in box.winfo_children():
            widget.destroy()

        # Pintar los productos en la interfaz
        DataBlock(box, data)

    # Pedimos al hilo principal que actualice la GUI
    app.after(0, actualizar_gui_despues_scraper)
   


def threadGetUrl(link):
    # Arrancamos el scrapper en un hilo aparte
    Thread(target=lambda: getUrl(link, ia_var.get(), premium_var), daemon=True).start()


# -----------   MAQUETADO DE LA GUI
entry = CTkEntry(
    app,
    width=anchoButtom + 100,
    height=altoButtom,
    placeholder_text="Bienvenido César busca aquí tu producto:",
    textvariable=textBusqueda
)
entry.place(x=50, y=40)

searchButton = CTkButton(
    app,
    width=anchoButtom,
    height=altoButtom,
    font=("Calibri", 15, "bold"),
    bg_color="#CCD5F4",
    text="BUSCAR",
    command=lambda: (iniciar_cronometro(), threadGetUrl(textBusqueda.get()))
)
searchButton.place(x=1200, y=40)

# Cronómetro
timer_frame = CTkFrame(app, fg_color="#343638", corner_radius=10)
timer_frame.place(x=350, y=40)   # posición del bloque del cronómetro

timer_label = CTkLabel(
    timer_frame,
    text="TIEMPO ESPERADO (35S PROMEDIO)",   # texto inicial
    font=("Calibri", 15, "bold")
)
timer_label.pack(padx=15, pady=10)
timer_labelDinamic = CTkLabel(
    timer_frame,
    text="TIEMPO PROMEDIO: 35s",   # texto inicial
    font=("Calibri", 15, "bold")
)
timer_labelDinamic.pack(padx=15, pady=10)

# Caja scrollable para productos
box = CTkScrollableFrame(app, width=1260, height=650)
box.place(x=50, y=200)

# Contador de productos encontrados
countProductFrame = CTkFrame(app, fg_color="#343638", corner_radius=10)
countProductFrame.place(x=600, y=40)

countProduct = CTkLabel(
    countProductFrame,
    text="PRODUCTOS ENCONTRADOS:",
    font=("Calibri", 15, "bold")
)
countProduct.pack(padx=15, pady=10)
countProductdinamic = CTkLabel(
    countProductFrame,
    text="---",
    font=("Calibri", 15, "bold")
)
countProductdinamic.pack(padx=15, pady=10)

# Filtro de IA
ia_checkbox = CTkCheckBox(
    app,
    text="Búsqueda con IA",
    variable=ia_var,
    onvalue=True,
    offvalue=False,
    font=("Calibri", 14, "bold")
)
ia_checkbox.place(x=860, y=40)

# Filtro NotPremium
premium_checkbox = CTkCheckBox(
    app,
    text="Without Top",
    variable=premium_var,
    onvalue=True,
    offvalue=False,
    font=("Calibri", 14, "bold")
)
premium_checkbox.place(x=860, y=80)

# -----------   ACTUALIZADO DE GUI
app.mainloop()
