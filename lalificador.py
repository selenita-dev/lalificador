import os
import re
import sys
import platform
import shutil
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

SIGLAS_DEFAULT = "XXX"
FILES_TO_RENAME = []


def get_directory_date_from_file(file_path):
    parent_name = file_path.parent.name
    match = re.match(r"(\d{4})\.(\d{2})", parent_name)
    if match:
        return f"{match.group(1)}-{match.group(2)}"
    else:
        return datetime.now().strftime("%Y-%m")


def format_filename(file_path, fecha, prefijo):
    name = file_path.stem
    ext = file_path.suffix.lower()
    base = name

    pattern = re.compile(
        r"^\d{4}-\d{2}\s"               # Fecha YYYY-MM espacio
        r"\d{3}\.\s"                    # Número 3 dígitos y punto espacio
        r"([A-Z][a-z0-9]*_)*"           # Palabras con guiones bajos (cero o más)
        r"[A-Z][a-z0-9]*\s"             # Última palabra (sin guión bajo al final), espacio
        r"(\([^)]+\)\s)?"               # Comentario opcional entre paréntesis, espacio
        r"(F\.[A-Za-z0-9]{1,5}\s)?"     # Código F.XXXXX opcional, espacio
        r"[A-Z0-9]{2,}$"                # Prefijo final obligatorio
    )

    match = pattern.match(name)

    if match: return name + ext

    match = re.match(r"^([0-9]{1,3})\.\s*(.*)$", name)
    if not match:
        clean = re.sub(r"[0-9]{4}-[0-9]{2}|" + re.escape(prefijo), "", name, flags=re.IGNORECASE)
        clean = re.sub(r"\s+", " ", clean).strip()
        return f"{fecha} {clean} {prefijo.upper()}{ext}"

    raw_num, rest = match.groups()
    num = f"{int(raw_num):03d}"

    # Extraer paréntesis (si hay)
    parentesis_match = re.search(r"\(([^)]*)\)", rest)
    parentesis = f"({parentesis_match.group(1).strip()})" if parentesis_match else ""

    # Extraer código F. incluso si está pegado a otras palabras
    fcode = ""
    fcode_search = re.search(r"F\.([A-Za-z0-9]{1,5})", rest)
    if fcode_search:
        cod = fcode_search.group(1)
        if cod.isdigit():
            fcode = f"F.{int(cod):05d}"
        else:
            fcode = f"F.{cod.upper().zfill(5)}"
        rest = re.sub(r"F\.([A-Za-z0-9]{1,5})", "", rest)

    # Eliminar paréntesis del texto libre
    libre = re.sub(r"\([^)]*\)", "", rest)
    libre = re.sub(r"[0-9]{4}-[0-9]{2}|" + re.escape(prefijo), "", libre, flags=re.IGNORECASE)
    libre = re.sub(r"[^\w]+", " ", libre).strip()
    libre = re.sub(r"\s+", " ", libre).title().replace(" ", "_")

    parts = [f"{fecha} {num}. {libre}".strip("._")]
    if parentesis:
        parts.append(parentesis)
    if fcode:
        parts.append(fcode)
    parts.append(prefijo.upper())
    return " ".join(parts) + ext


def check_and_collect(file_path, fecha, prefijo):
    suggestion = format_filename(file_path, fecha, prefijo)
    if file_path.name != suggestion:
        FILES_TO_RENAME.append((file_path, suggestion))


def scan_directory(directory, siglas):
    FILES_TO_RENAME.clear()
    for root, _, files in os.walk(directory):
        for fname in files:
            path = Path(root) / fname
            if path.resolve() == Path(__file__).resolve():
                continue
            fecha = get_directory_date_from_file(path)
            check_and_collect(path, fecha, siglas or SIGLAS_DEFAULT)


def apply_changes():
    for old_path, new_name in FILES_TO_RENAME:
        new_path = old_path.parent / new_name
        shutil.move(str(old_path), str(new_path))
    messagebox.showinfo("Completado", "Cambios aplicados con éxito.")


def run_gui():
    global text_box

    root = tk.Tk()
    root.title("Lalificador")
    root.geometry("1024x768")

    # Detecta plataforma
    is_windows = platform.system() == "Windows"

    # Manejo dinámico de la ruta al ícono (funciona también en el .exe)

    if getattr(sys, 'frozen', False):
       base_path = sys._MEIPASS
    else:
       base_path = os.path.abspath(".")

    icon_ico = os.path.join(base_path, "icon.ico")
    icon_png = os.path.join(base_path, "icon.png")

    try:
       if is_windows:
          root.iconbitmap(icon_ico)
       else:
          img = tk.PhotoImage(file=icon_png)
          root.iconphoto(True, img)
    except Exception as e:
       print(f"No se pudo establecer el icono: {e}")

    frame = ttk.Frame(root, padding=10)
    frame.pack(fill="both", expand=True)

    dir_var = tk.StringVar()
    siglas_var = tk.StringVar(value=SIGLAS_DEFAULT)

    def seleccionar_directorio():
        path = filedialog.askdirectory()
        if path:
            dir_var.set(path)

    def mostrar_ejemplos():
        ejemplos = (
            "Ejemplos del patrón válido:\n\n"
            "- 35. Agua (06 Bim 2024).pdf\n"
            "- 35. Agua Pago (06 Bim 2024).pdf\n"
            "- 35.Agua (06 Bim casa) Pago.pdf\n"
            "- 35. Agua (06 Bim 2024) F.0354.PDF\n"
            "- 01. Digital server (06 Bim 2024) F.114.PDF\n"
            "- 2. Asociacion Hoteles y Moteles VM F.A450.xml\n"
            "\nPor partes esperadas:\n\n"
            "- Número de 1 a 3 dígitos seguido de un punto. Ej: 01.\n"
            "- Texto libre, puede ir en diferentes partes del nombre del archivo.\n"
            "- Comentario entre paréntesis (opcional).\n"
            "- Código de factura, siempre con 'F.', F.XXXXX (opcional).\n"
            "\nTodos los nombres se transformarán a este patrón:\n"
            "- 2025-03 035. Agua (06 Bim 2024) F.00354 HBO.pdf\n"
            "- 2025-03 002. Asociacion_Hoteles_Y_Moteles_VM F.0A450 HBO.xml"  
        )

        top = tk.Toplevel()
        top.title("Ejemplos de nombre válido")
        top.geometry("800x600")

        text = tk.Text(top, wrap="word", font=("Consolas", 11))
        text.insert("1.0", ejemplos)
        text.config(state="disabled")
        text.pack(fill="both", expand=True, padx=10, pady=10)

        ttk.Button(top, text="Cerrar", command=top.destroy).pack(pady=5)

    def ejecutar():
        if not dir_var.get():
            messagebox.showerror("Error", "Selecciona un directorio primero.")
            return
        scan_directory(dir_var.get(), siglas_var.get())
        if not FILES_TO_RENAME:
            text_box.config(state="normal")
            text_box.delete("1.0", tk.END)
            text_box.insert(tk.END, "✅ No hay archivos que renombrar.")
            text_box.config(state="disabled")
            return
        sorted_files = sorted(FILES_TO_RENAME, key=lambda x: x[0].name)
        output = "\n".join([f"❌ {p.name} -> ✅ {n}" for p, n in sorted_files])
        text_box.config(state="normal")
        text_box.delete("1.0", tk.END)
        text_box.insert(tk.END, output)
        text_box.config(state="disabled")

    def confirmar():
        if not FILES_TO_RENAME:
            messagebox.showwarning("Primero analiza", "Debes analizar antes de aplicar cambios.")
            return
        if messagebox.askyesno("Confirmar", f"Se aplicarán {len(FILES_TO_RENAME)} cambios. ¿Continuar?"):
            apply_changes()
            ejecutar()

    ttk.Label(frame, text="Directorio:").grid(row=0, column=0, sticky="w")
    dir_entry = ttk.Entry(frame, textvariable=dir_var, width=60)
    dir_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
    ttk.Button(frame, text="📂 Seleccionar", command=seleccionar_directorio).grid(row=0, column=2, padx=5)

    ttk.Label(frame, text="Siglas:").grid(row=1, column=0, sticky="w")
    ttk.Entry(frame, textvariable=siglas_var, width=20).grid(row=1, column=1, padx=5, sticky="w")

    ttk.Label(frame, text="Patrón esperado:").grid(row=2, column=0, sticky="w")
    ttk.Label(frame, text="1. Texto libre (comentario) mas texto libre F.XXXXX.ext").grid(row=2, column=1, padx=5, sticky="w")
    ttk.Button(frame, text="📘 Ver Ejemplos", command=mostrar_ejemplos).grid(row=2, column=2, padx=5)

    ttk.Button(frame, text="🔍 Analizar", command=ejecutar).grid(row=3, column=0, pady=10)
    ttk.Button(frame, text="✅ Aplicar Cambios", command=confirmar).grid(row=3, column=1, pady=10, sticky="w")

    text_frame = ttk.Frame(frame)
    text_frame.grid(row=4, column=0, columnspan=3, sticky="nsew")
    frame.rowconfigure(4, weight=1)
    frame.columnconfigure(1, weight=1)

    text_box = tk.Text(text_frame, wrap="none", font=("Consolas", 10))
    text_box.pack(side="left", fill="both", expand=True)

    scrollbar_y = ttk.Scrollbar(text_frame, orient="vertical", command=text_box.yview)
    scrollbar_y.pack(side="right", fill="y")
    text_box.config(yscrollcommand=scrollbar_y.set)

    scrollbar_x = ttk.Scrollbar(frame, orient="horizontal", command=text_box.xview)
    scrollbar_x.grid(row=5, column=0, columnspan=3, sticky="ew")
    text_box.config(xscrollcommand=scrollbar_x.set)

    root.mainloop()


if __name__ == "__main__":
    run_gui()