# 📁 Lalificador

Lalificador es una herramienta de escritorio que sugiere y aplica renombramientos de archivos según un patrón estandarizado, diseñada para organizar archivos administrativos o de facturación.

---

## 🚀 Características

-  Interfaz gráfica intuitiva con Tkinter.
-  Análisis automático del nombre de archivo según 5 componentes.
-  Aplicación de renombramientos en lote.
-  Muestra antes de aplicar los cambios.
-  Compatible con Windows y Linux.
-  Generación de `.exe` con ícono personalizado.

---

## 📥 Requisitos

### Python 3.x

Instala Python desde:

-  https://www.python.org (Windows)
-  O usa tu gestor de paquetes en Linux (`apt`, `dnf`, `brew`, etc.)

### Dependencias

No se necesitan librerías externas. Usa solo módulos estándar (`tkinter`, `os`, `re`, `shutil`, etc.)

---

## ▶️ Uso en modo desarrollo

### Linux o Windows con Python instalado:

```bash
python3 lalificador.py
```

---

## 🖼️ Añadir un ícono a la ventana

### Paso 1: Archivos necesarios

Coloca en la misma carpeta:

-  `icon.ico` → Para `.exe` y Windows.
-  `icon.png` → Para Linux (barra de título).

El programa detecta el sistema y carga el ícono adecuado.

---

## 🏗️ Compilar `.exe` para Windows

### Paso 1: Instalar PyInstaller

```bash
pip install pyinstaller
```

### Paso 2: Ejecutar el empaquetado

```bash
pyinstaller --onefile --windowed \
  --icon=icon.ico \
  --add-data "icon.ico;." \
  --add-data "icon.png;." \
  lalificador.py
```

Esto generará `dist/lalificador.exe`

---

## 🧠 Estructura del nombre de archivo

El patrón correcto incluye 5 partes:

```
001. Nombre_Formateado (Paréntesis Opcional) F.XXXXX AAAA-MM SIGLAS.extensión
```

Ejemplos:

-  `35. Agua (06 Bim 2024).pdf` → `035. Agua (06 Bim 2024) 2025-03 HBO.pdf`
-  `2. Asociacion Hoteles VM F.A450.xml` → `002. Asociacion_Hoteles_VM F.0A450 2025-03 HBO.xml`

---

## 📦 Archivos generados por PyInstaller

Tras compilar, encontrarás:

-  `dist/lalificador.exe` → ejecutable final
-  `build/` → archivos temporales
-  `lalificador.spec` → configuración de build

Puedes eliminar `build/` si no lo necesitas.

---

## 📄 Licencia

Este proyecto es de uso personal/empresarial y puede adaptarse libremente. No se ofrece garantía alguna.

---

¿Dudas o sugerencias? ¡Puedes mejorar el script o compartir ideas!
