"""User interface translation.

The catalogue is keyed by the English source string rather than by invented
identifiers. That way a string nobody has translated yet falls back to readable
English instead of to something like `settings.output.prefix_label`, and adding
a new label to the interface only requires filling in the Spanish side.

The language has to be chosen before any widget is built, because Tkinter has
no practical way to relabel a built interface: `load_saved_language()` reads it
straight out of settings.json for that reason, before the GUI exists.
"""
import json
import locale
import logging
import os
import sys

DEFAULT_LANGUAGE = "en"
LANGUAGES = {"en": "English", "es": "Español"}

_current = DEFAULT_LANGUAGE


def set_language(code):
    global _current
    _current = code if code in LANGUAGES else DEFAULT_LANGUAGE
    return _current


def get_language():
    return _current


def t(text):
    """Translate a user-visible string, falling back to the English original."""
    if _current == DEFAULT_LANGUAGE:
        return text
    return TRANSLATIONS.get(_current, {}).get(text, text)


def system_language():
    """Best guess at the operating system's language, for a first run."""
    candidates = []
    if sys.platform == "win32":
        try:
            import ctypes
            lcid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            candidates.append(locale.windows_locale.get(lcid, ""))
        except Exception:
            pass
    candidates += [os.environ.get(name, "") for name in
                   ("LC_ALL", "LC_MESSAGES", "LANG", "LANGUAGE")]
    for value in candidates:
        code = value.replace("-", "_").split("_")[0].split(".")[0].lower()
        if code in LANGUAGES:
            return code
    return DEFAULT_LANGUAGE


def load_saved_language(settings_path):
    """Pick the language before the interface is built.

    A missing or unreadable settings file is normal on a first run, so it falls
    back to the system language rather than complaining.
    """
    code = None
    try:
        with open(settings_path, "r", encoding="utf-8") as handle:
            code = json.load(handle).get("general", {}).get("language")
    except (OSError, ValueError, AttributeError) as exc:
        logging.debug(f"No saved language ({exc}); using the system one.")
    return set_language(code or system_language())


SPANISH = {
    # Tabs
    "Compress": "Comprimir",
    "Utilities": "Utilidades",
    "Settings": "Ajustes",
    "Merge": "Unir",
    "Split/Extract": "Dividir/Extraer",
    "Rotate": "Rotar",
    "Delete Pages": "Borrar páginas",
    "Password": "Contraseña",
    "Stamp/Watermark": "Sello/Marca de agua",
    "Header/Footer": "Encabezado/Pie",
    "Table of Contents": "Índice",
    "Metadata": "Metadatos",
    "PDF to Image": "PDF a imagen",
    "PDF Repair": "Reparar PDF",

    # Compression modes
    "Compression": "Compresión",
    "Lossless": "Sin pérdida",
    "PDF/A": "PDF/A",
    "Remove Images": "Quitar imágenes",
    "Mode": "Modo",
    "Resolution (DPI)": "Resolución (PPP)",
    "Image Quality": "Calidad de imagen",
    "Levels (2-8)": "Niveles (2-8)",

    # Common labels
    "Input": "Entrada",
    "Browse": "Examinar",
    "Add Files": "Añadir archivos",
    "Clear All": "Vaciar lista",
    "Remove": "Quitar",
    "Move Up": "Subir",
    "Move Down": "Bajar",
    "Folder:": "Carpeta:",
    "Prefix:": "Prefijo:",
    "Suffix:": "Sufijo:",
    "Position:": "Posición:",
    "Opacity:": "Opacidad:",
    "Scale:": "Escala:",
    "Size:": "Tamaño:",
    "Color": "Color",
    "Pick Color": "Elegir color",
    "Font:": "Fuente:",
    "Font Size:": "Cuerpo:",
    "Text:": "Texto:",
    "Title:": "Título:",
    "Image": "Imagen",
    "Text": "Texto",
    "Image File:": "Archivo de imagen:",
    "Page Range:": "Intervalo de páginas:",
    "Pages to Delete": "Páginas a borrar",
    "Custom:": "Personalizado:",
    "Start at:": "Empezar en:",
    "Preview N/A": "Sin vista previa",
    "e.g., 1, 3-5, 8-end": "p. ej., 1, 3-5, 8-end",
    "Page Number (e.g., 1)": "Número de página (p. ej., 1)",
    "Page X of Y (e.g., 1 of 10)": "Página X de Y (p. ej., 1 de 10)",

    # Output
    "Output Folder": "Carpeta de salida",
    "Output Format": "Formato de salida",
    "Output File Naming": "Nombre del archivo de salida",
    "Default Output": "Salida por omisión",
    "Use Default Output Folder": "Usar la carpeta de salida por omisión",
    "Add Date (YYYY-MM-DD)": "Añadir fecha (AAAA-MM-DD)",
    "Add Time (HH-MM-SS)": "Añadir hora (HH-MM-SS)",
    "Don't save if larger than original": "No guardar si resulta mayor que el original",
    "Delete original file if compressed": "Borrar el original si se ha comprimido",

    # Split
    "Split Mode": "Modo de división",
    "Split to Single Pages": "Dividir en páginas sueltas",
    "Split Every N Pages. N =": "Dividir cada N páginas. N =",
    "Custom Range(s):": "Intervalo(s) personalizado(s):",

    # Rotation
    "Rotation Angle": "Ángulo de rotación",
    "No Rotation": "Sin rotación",
    "90° Right (Clockwise)": "90° a la derecha (horario)",
    "180°": "180°",
    "90° Left (Counter-Clockwise)": "90° a la izquierda (antihorario)",

    # Passwords
    "Encrypt PDF": "Cifrar PDF",
    "Decrypt PDF": "Descifrar PDF",
    "User Password:": "Contraseña de usuario:",
    "Owner Password:": "Contraseña de propietario:",
    "Current Password:": "Contraseña actual:",
    "Show Passwords": "Mostrar las contraseñas",
    "Permissions (when using User Password)": "Permisos (al usar contraseña de usuario)",
    "Allow Printing": "Permitir imprimir",
    "Allow Copy & Extract": "Permitir copiar y extraer",
    "Allow Modification": "Permitir modificar",
    "Allow Annotations & Forms": "Permitir anotaciones y formularios",

    # Stamp and header/footer
    "Stamp on Top": "Sello por encima",
    "Header/Footer Options": "Opciones de encabezado y pie",
    "Enable Bates Numbering (%Bates)": "Activar numeración Bates (%Bates)",
    "Use Dot Leaders": "Usar puntos de relleno",
    "Don't Bookmark the ToC": "No añadir marcador al índice",

    # Advanced compression options
    "Advanced Settings": "Opciones avanzadas",
    "Darken Text": "Oscurecer el texto",
    "Convert to Grayscale": "Convertir a escala de grises",
    "Convert to CMYK (for printing)": "Convertir a CMYK (para imprenta)",
    "Strip All Metadata": "Eliminar todos los metadatos",
    "Linearize for Fast Web View": "Linearizar para vista web rápida",
    "Lossless Image Encoding (Flate)": "Codificación de imagen sin pérdida (Flate)",
    "True Lossless (preserves JPEGs)": "Sin pérdida real (conserva los JPEG)",
    "Preserve OCR Layer / Fonts": "Conservar la capa OCR y las fuentes",
    "Detect Duplicate Images": "Detectar imágenes duplicadas",
    "Quantize Colors (Posterize)": "Cuantizar colores (posterizar)",
    "Use Bicubic Sampling (Higher Quality)": "Remuestreo bicúbico (más calidad)",
    "Only Downsample Larger Images (Recommended)": "Remuestrear solo las imágenes grandes (recomendado)",
    "Remove Interactive (Compression)": "Quitar elementos interactivos (compresión)",
    "Remove Open Action": "Quitar la acción de apertura",
    "Fast Mode (lower compression)": "Modo rápido (menos compresión)",
    "Safe Mode (prevents graphic artifacts)": "Modo seguro (evita artefactos gráficos)",
    "Compress PDF/A Output": "Comprimir la salida PDF/A",

    # Settings tab
    "Appearance": "Apariencia",
    "Dark Mode": "Modo oscuro",
    "Language": "Idioma",
    "Logging": "Registro",
    "Enable File Logging (app.log)": "Guardar registro en archivo (app.log)",
    "Updates": "Actualizaciones",
    "Check for Updates": "Buscar actualizaciones",
    "Buy me a coffee": "Invítame a un café",
    "If you enjoy using my app, please consider supporting its development.":
        "Si te resulta útil la aplicación, puedes apoyar su desarrollo.",
    "Restart required": "Hay que reiniciar",
    "The language will change the next time you open the application.":
        "El idioma cambiará la próxima vez que abras la aplicación.",

    # Repair
    "This tool attempts to repair corrupted or damaged PDF files by rebuilding them. Results may vary.":
        "Esta herramienta intenta reparar archivos PDF dañados reconstruyéndolos. El resultado puede variar.",

    # Action buttons
    "PROCESS PDF": "PROCESAR PDF",
    "MERGE PDFS": "UNIR LOS PDF",
    "SPLIT PDF": "DIVIDIR PDF",
    "ROTATE PDF": "ROTAR PDF",
    "DELETE PAGES": "BORRAR PÁGINAS",
    "ENCRYPT PDF": "CIFRAR PDF",
    "DECRYPT PDF": "DESCIFRAR PDF",
    "APPLY STAMP": "APLICAR SELLO",
    "ADD HEADER/FOOTER": "AÑADIR ENCABEZADO/PIE",
    "GENERATE TOC": "GENERAR ÍNDICE",
    "SAVE METADATA (OVERWRITE)": "GUARDAR METADATOS (SOBRESCRIBE)",
    "CONVERT TO IMAGES": "CONVERTIR A IMÁGENES",
    "ATTEMPT REPAIR": "INTENTAR REPARAR",
    "Merge Files": "Archivos a unir",

    # Status and dialogs
    "Ready": "Listo",
    "Starting...": "Empezando...",
    "Busy": "Ocupado",
    "Error": "Error",
    "Input Error": "Error en los datos",
    "No Files": "Sin archivos",
    "Tool Not Found": "Herramienta no encontrada",
    "Confirm Overwrite": "Confirmar sobrescritura",
    "A process is already running.": "Ya hay un proceso en marcha.",
    "No PDF files were found in that folder.": "No se han encontrado archivos PDF en esa carpeta.",
    "Please add files to merge and specify an output path.":
        "Añade los archivos que quieres unir e indica la ruta de salida.",
    "Please add one or more PDF files to the list.":
        "Añade uno o más archivos PDF a la lista.",
    "Please select a valid PDF file first.":
        "Selecciona antes un archivo PDF válido.",
    "Please select an input file and an output path/directory.":
        "Selecciona un archivo de entrada y una ruta o carpeta de salida.",
    "Please specify an output folder.": "Indica una carpeta de salida.",
    "This will modify the metadata of the original file. Are you sure you want to continue?":
        "Esto modificará los metadatos del archivo original. ¿Seguro que quieres continuar?",
}

TRANSLATIONS = {"es": SPANISH}
