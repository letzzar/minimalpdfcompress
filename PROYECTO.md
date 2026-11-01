# PROYECTO.md — mapa de la aplicación

Documento de trabajo para poder tocar la aplicación por partes sin tener que
releerla entera. Si algo de aquí deja de ser cierto, corregirlo en el mismo
cambio que lo rompió.

## Qué es

Aplicación de escritorio que comprime y manipula PDF en local. Python pone la
interfaz (Tkinter) y la orquestación; el trabajo lo hacen seis ejecutables de
terceros invocados como subprocesos. No abre ninguna conexión de red.

## Mapa de módulos

| Fichero | Líneas | Responsabilidad | Tocar aquí si… |
|---|---:|---|---|
| `src/main.py` | 37 | Arranque: logging, DPI awareness, lanza la GUI | cambia el arranque o el logging global |
| `src/gui.py` | 1963 | **Toda** la interfaz: layout, estado, hilos, vistas previas, ajustes | cualquier cosa visible |
| `src/i18n.py` | 258 | Catálogo de traducción y elección de idioma | añadir o corregir textos traducidos, añadir un idioma |
| `src/backend.py` | 606 | Lógica de las 11 pestañas de utilidades | merge, split, rotar, sellos, metadatos… |
| `src/pdf_optimizer.py` | 654 | Clase `PdfOptimizer`: los cuatro modos de compresión | compresión, lossless, PDF/A, quitar imágenes |
| `src/utils.py` | 129 | Localizar binarios, rutas de recursos, ejecutar subprocesos | invocación de herramientas, rutas, configuración |
| `src/ui_components.py` | 356 | Widgets propios (`CompressionGauge`, `CustomSlider`, `PositionSelector`, `DropZone`…) | comportamiento de un control concreto |
| `src/styles.py` | 115 | Tema claro/oscuro, paletas | colores, tipografías |
| `src/constants.py` | 53 | Versión y constantes compartidas | **cuidado**: sus valores son identificadores lógicos |
| `src/tooltips.py` | 244 | 100 textos de ayuda en inglés y español, más el accesor `tooltip()` | textos de ayuda |

`gui.py` es con diferencia el módulo más grande y concentra responsabilidades
que en otro proyecto estarían separadas. Mientras no haga falta, no se parte:
partirlo es un cambio grande sin red de pruebas que lo respalde.

## Cómo fluye una tarea

1. El usuario pulsa un botón en `gui.py`.
2. `gui.py` reúne los parámetros y lanza un **hilo** con la función de
   `backend.py` o con un método de `PdfOptimizer`.
3. Esa función comunica progreso y resultado por una **cola** (`queue.Queue`).
4. `gui.py` consulta la cola periódicamente y actualiza la interfaz.

La GUI nunca debe bloquearse: cualquier trabajo nuevo que tarde sigue este
patrón.

## Herramientas externas

Todas se resuelven con `utils.find_executable()`: primero `src/bin`, luego el
`PATH`. Todas se invocan con `utils.run_command()`, que acepta **sólo listas** y
ejecuta con `shell=False`.

| Herramienta | Quién la llama | Para qué |
|---|---|---|
| Ghostscript | `pdf_optimizer.py` (3 sitios), `backend.py` (2) | Recomprimir, PDF/A, PDF a imagen, vista previa |
| cpdf | `backend.py`, `pdf_optimizer._post_process_pdf` | Casi todas las utilidades, y el paso final de todos los modos |
| oxipng, ECT, pngquant, jpegoptim | `pdf_optimizer.py` | Optimizar cada imagen incrustada |

Los cinco puntos de llamada a Ghostscript pasan `-dSAFER`. Es un principio no
negociable; ver `CLAUDE.md`.

## Rutas, recursos y configuración

- `resource_path(x)` busca en `_MEIPASS`, el directorio del módulo y
  `app_dir()`, en ese orden. Así el mismo código funciona en checkout, en
  PyInstaller, en carpeta standalone de Nuitka y dentro de un `.app`.
- `app_dir()` es el directorio del ejecutable cuando está compilado.
- `user_config_path("settings.json")`: si hay un `settings.json` junto al
  ejecutable, gana (modo portable); si no, `%APPDATA%` o `~/.config`.
- `subprocess_env()` exporta `GS_LIB` apuntando a los recursos que viajan con la
  app. Sin eso, un Ghostscript compilado por nosotros no encuentra `gs_init.ps`.
- `src/bin`, `src/lib`, `src/Resource`, `src/iccprofiles` están en `.gitignore` y
  los reproduce `tools/fetch_deps.py` desde `tools/deps.lock.json`.

## Las pestañas

Principal: **Compress**, con cuatro modos (`Compression`, `Lossless`, `PDF/A`,
`Remove Images`) implementados en `PdfOptimizer`.

Utilidades, declaradas en `gui.py:421` y cada una con su `_build_*_tab`:
merge, split, rotate, delete, password, stamp, page_number, toc, metadata,
convert, repair.

Añadir una pestaña = una entrada en esa lista + su método `_build_*_tab` + la
función de trabajo en `backend.py`.

## Empaquetado y distribución

| Paso | Herramienta |
|---|---|
| Dependencias de terceros | `tools/fetch_deps.py` ← `tools/deps.lock.json` |
| Compilar | `build.py` (Nuitka, **standalone**, `.app` en macOS) |
| Instalador | `tools/package.py` → Inno Setup (`.exe`) o `dpkg-deb` (`.deb`) |
| Publicar | etiqueta `v1.10.0-fork.N` → `.github/workflows/build.yml` |

CI construye cinco objetivos: `windows-x86_64`, `linux-x86_64`,
`linux-aarch64`, `macos-x86_64`, `macos-aarch64`. Ghostscript se compila desde
fuente en los cuatro que no son Windows.

## Estado y deuda conocida

Lo que hay que tener presente antes de prometer nada:

- **No hay suite de pruebas unitarias.** `tools/smoke_test.py` es la única red, y
  cubre cinco trabajos de compresión. **Las once pestañas de utilidades no
  tienen ninguna cobertura automática**: merge, split, rotate, delete, password,
  stamp, cabecera/pie, índice, metadatos, PDF a imagen y reparación se verifican
  sólo a mano. Es la carencia más seria del proyecto.
- **Los textos mostrados son identificadores lógicos.** Sigue siendo cierto y
  sigue siendo la trampa principal del código: `gui.py` compara
  `mode == "Compression"` y `backend.py` traduce `POS_TOP_LEFT` a argumentos de
  cpdf. La traducción no lo cambió, lo rodeó: los `Radiobutton` ya separaban
  `text=` de `value=`, así que sólo se traduce lo que se ve. Al añadir
  cualquier control nuevo hay que mantener esa separación.
- **La interfaz está traducida, el idioma se elige en Ajustes y requiere
  reiniciar.** Tkinter no permite reetiquetar una interfaz ya construida y
  reconstruirla perdería los archivos en cola, así que el cambio se difiere a
  propósito. `i18n.load_saved_language()` se llama desde `main.py` antes de
  crear el primer widget.
- Tres `text=` son f-strings con variables (`"({dpi} DPI)"`, `"{escala}%"`) y
  se han dejado sin traducir: no llevan palabras.
- **Sin firma de código** en ninguna plataforma. Es lo único que queda para
  eliminar la última detección de antivirus (1/71, Microsoft, heurística de ML).
- **Sin cpdf en Linux arm64**: upstream lo enlaza contra GLIBC 2.42. Se saltan la
  linearización y el squeeze final.
- **Sin build nativo de Windows arm64**: Ghostscript no publica binario arm64
  para Windows.
- `src/dependencies/pdf.ico` está en el repositorio y **no lo referencia nada**.
  Parece un resto de upstream. No lo borro porque no es parte de ningún encargo;
  queda anotado.
- El `.app` de macOS y los `.deb` se han verificado en CI, no en hardware real
  más allá de las pruebas que hiciste tú.

## Dónde tocar para lo típico

| Quiero… | Empezar por |
|---|---|
| Cambiar un texto visible | `gui.py` (`text=`) o `tooltips.py` |
| Añadir una opción de compresión | `pdf_optimizer.py` + el `_build_compress_tab` de `gui.py` |
| Añadir una utilidad nueva | lista de `gui.py:421`, `_build_*_tab`, función en `backend.py` |
| Cambiar cómo se invoca una herramienta | `utils.run_command` y el punto de llamada |
| Añadir o actualizar un binario de terceros | `tools/deps.lock.json` (con su hash) |
| Cambiar el aspecto | `styles.py`, y `ui_components.py` si es un control concreto |
| Cambiar el empaquetado | `build.py`, `tools/package.py`, `packaging/` |
