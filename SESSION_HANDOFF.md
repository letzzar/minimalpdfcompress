# SESSION_HANDOFF.md

Estado al final de la última sesión. Leer al empezar, actualizar al terminar.

**Última actualización:** 2026-11-02

## Dónde estamos

El fork está publicado y funcionando en las cinco plataformas. La última
release es
[v1.11.0-fork.1](https://github.com/letzzar/minimalpdfcompress/releases/tag/v1.11.0-fork.1),
publicada el 2026-11-01, con ocho archivos: instalador de Windows, `.deb` para
amd64 y arm64, y los cinco portables. Todos con attestation firmada,
comprobada en el instalador. Es la primera con la interfaz rehecha; la
traducción al español salió en `v1.10.0-fork.4`.

El Director ha probado a mano Windows, macOS y Raspberry Pi con la 1.10:
funcionan.

`APP_VERSION` es **`1.11.0`** desde el 2026-11-01, por decisión del Director.
El `VersionInfoVersion` del instalador estaba clavado a mano en `1.10.0.0` y
ahora sale de `AppVersion`.

**Nada de la interfaz nueva se ha visto fuera de Windows.** CI demuestra que
los cinco objetivos compilan y que los pipelines de compresión funcionan, no
que la ventana se abra bien en macOS o en la Raspberry. Lo siguiente es
probar los binarios de esta release a mano en los tres sistemas, y de paso
pulsar el selector de idioma, que sigue sin que nadie haya visto el aviso de
reinicio.

## Completado

- Auditoría del falso positivo de antivirus de upstream v1.9.7 (38/71). Causa
  aislada: el empaquetado onefile, no el código ni los binarios de terceros.
  Pasando a carpeta standalone: **1/71**. Documentado en `FORK.md`.
- Ghostscript con `-dSAFER` en los cinco puntos de llamada.
- Cuatro bugs funcionales de upstream corregidos, el peor de ellos dejaba
  Lossless, True Lossless y Remove Images copiando el original sin tocar.
- Multiplataforma real: Windows, macOS y Linux en x86-64 y arm64, con `.app` en
  macOS e icono nativo en los tres.
- Ghostscript compilado desde fuente en los cuatro objetivos que no son Windows.
- Dependencias fijadas por SHA-256 por plataforma en `tools/deps.lock.json`.
- CI con matriz de cinco y attestation de procedencia.
- Instaladores: Inno Setup con modo por usuario y para todo el equipo sin pedir
  admin hasta elegir; `.deb` con entrada de menú e icono.
- Aportado a upstream: [PR #63](https://github.com/deminimis/minimalpdfcompress/pull/63)
  (abierto, `MERGEABLE`) y un
  [comentario en el issue #50](https://github.com/deminimis/minimalpdfcompress/issues/50#issuecomment-6550643907).
- **Interfaz traducida al español**, con selector de idioma en Ajustes y aviso
  de reinicio. 141 cadenas de interfaz y 100 textos de ayuda, con paridad de
  claves comprobada. El idioma se detecta del sistema en el primer arranque.
  El `TranslatedCombobox` que estaba planificado resultó innecesario: los
  `Radiobutton` ya separaban `text=` de `value=`, y la única excepción era la
  rotación, que se arregló con una línea.
- **Interfaz modernizada, con las once pestañas repasadas una a una.** El tema
  da profundidad con tres niveles de superficie en vez de con contornos, hay
  una sola escala tipográfica, los campos van rellenos y los interruptores
  tienen indicador propio dibujado como pastilla. La pestaña seleccionada se
  queda a nivel de las demás y se distingue sólo por el color: `clam` la
  desplazaba hacia abajo y hacia los lados, y se corrigió fijando `padding` y
  `expand` iguales en todos los estados. Del repaso salieron dos defectos
  sistemáticos, no casos sueltos: el lienzo de vista previa se creaba con
  `highlightthickness=1` y dibujaba una caja vacía con contorno en Rotar,
  Borrar páginas, Sello y Encabezado; y `ttk.LabelFrame` venía con surco y
  título en tamaño de texto normal, lo que descolocaba las tres secciones de
  Contraseña y «Advanced Settings». Dividir, Índice, Metadatos, PDF a imagen y
  Reparar ya estaban bien y no se tocaron.
- **Un solo deslizador en toda la aplicación.** Quedaban tres `ttk.Scale`
  (escala y opacidad del sello, DPI de PDF a imagen) que `clam` dibujaba como
  una barra con contorno azul y un pulgar rayado en medio; ese era el recuadro
  que se veía en la hoja de contacto. Ahora los cinco son `CustomSlider`.
  Hubo que enseñarle a respetar `DoubleVar`: redondeaba a entero, lo que en la
  opacidad (0,1–1,0) la habría dejado pegada a los extremos.
- **Fuera la regla pálida bajo cada tira de pestañas.** `borderwidth=0` no
  llega al área de cliente del `Notebook`; el borde lo pintan `bordercolor`,
  `lightcolor` y `darkcolor`.
- **Los textos que se quedaban en inglés, traducidos.** `FileSelector` y
  `DropZone` nunca pasaron por `t()`, así que «Input», «Output», «Drag & Drop
  PDF File or Folder Here», «Select File(s)» y «Select Folder» salían en
  inglés en toda la aplicación, y con ellos las cabeceras «File Name»,
  «Pages» y «Size» de las dos listas y el título del selector de color. Un
  barrido por AST (`find_untranslated.py`, en el scratchpad) confirma que ya
  no queda ningún literal visible sin traducir.
- **Cuatro ayudas que no existían.** `gui.py` pedía `drop_zone_compress`,
  `compress_tree`, `compress_add_btn` y `compress_remove_btn`, que no estaban
  en el catálogo; `tooltip()` devolvía `None` y `Tooltip` no muestra nada si
  el texto es vacío, así que los cuatro controles más usados de Comprimir no
  tenían ayuda. Viene de upstream.
- **El `DropZone` pedía «Segoe UI» a pelo**, saltándose `styles.FONT_FAMILY`,
  que es «Helvetica» en macOS y «DejaVu Sans» en Linux. Allí Tk caía a la
  fuente por defecto sin avisar.
- **Marco negro del icono: resuelto.** El arte de upstream traía el fondo
  negro horneado en las cuatro esquinas de fuera de la pastilla redondeada; no
  era Tk maltratando el alfa, como sospeché primero. `tools/make_icons.py`
  regenera `src/assets/icon.png` y `src/pdf.ico` desde `assets/pdf1.png`
  vaciando el fondo por contigüidad desde las esquinas, que sólo borra lo
  conectado al borde y deja intacto el logotipo oscuro del centro. Arregla de
  una vez la ventana, la barra de tareas, el `.exe`, el instalador, el `.icns`
  de macOS y el icono del `.deb`, porque todos salen de esos dos ficheros.
- **Medido en VirusTotal el 1 y el 2 de noviembre de 2026:** instalador **0**
  (de 44 motores que contestaron), zip de Windows **1/68**, `.exe` de dentro
  **1/71**. El único que objeta es Microsoft, con Wacatac`!ml`, y sólo por el
  ejecutable: el instalador lleva los mismos bytes y pasa limpio. DeepInstinct
  y Zillya, que marcaban los artefactos de la 1.10.0, están limpios ahora. Los
  portables de macOS y Linux no se han medido, y tampoco tendría mucho
  sentido: los motores de VirusTotal miran sobre todo a Windows.
- **Qué dispara la detección de Microsoft: medido, no supuesto.** Un
  hola-mundo de Tkinter compilado con la misma cadena (Nuitka 4.3.3,
  `--standalone`, plugin de tk, Python 3.13) y sin una línea de nuestro código
  saca exactamente el mismo `Trojan:Win32/Wacatac.C!ml`, y encima suma a
  McAfeeD. Es la forma del binario que produce Nuitka, sin firmar; no hay nada
  que tocar en el proyecto que lo cambie. El experimento, reproducible paso a
  paso, está en `FORK.md`.

## En curso

Nada a medias.

## Pendiente

- **Sin cobertura automática de las once pestañas de utilidades.** Es la
  carencia más seria; ver `PROYECTO.md`.
- El selector de idioma no se ha probado pulsándolo: se ha verificado que el
  valor persiste y que la app arranca en ambos idiomas, pero el diálogo de
  "hay que reiniciar" no lo ha visto nadie todavía.
- Dos píxeles blancos en las esquinas izquierdas del campo «Entrada», que es
  el único `Entry` de sólo lectura. No son del estado `readonly`: mapear
  `bordercolor`, `lightcolor` y `darkcolor` para ese estado no los quita, así
  que los pinta `Entry.field` de `clam` por su cuenta. Se verían obligados a
  cambiar el `layout` del `Entry`, que es el elemento que da el fondo. A 100 %
  no se aprecian; se dejan.
- El arnés de captura sigue en el scratchpad (`capture.ps1`, `run_tab.py`,
  `sweep.ps1`, `montage.py` y `crop.py`): lanza la app con una pestaña
  concreta, la fotografía en el monitor donde esté la ventana y monta hojas de
  contacto. No está en el repo porque sólo sirve en Windows y necesita ojo
  humano para interpretar el resultado. Lo que sí se ha quedado es
  `tools/check_strings.py`, que no abre ventana.
- `AUDITORIA-v1.9.7.md` sigue sin versionar en la raíz del proyecto. Es el
  informe del falso positivo con el que empezó todo esto; hay que decidir si
  entra al repo, se mueve a `docs/` o se queda fuera.
- `jpegoptim` es la única herramienta que el README sigue pidiendo instalar a
  mano fuera de Windows.
- Firma de código: sigue sin hacerse. Es lo que de verdad termina con las
  heurísticas de aprendizaje automático y con SmartScreen, que es una capa
  aparte y sólo se gana a base de descargas.
- **Esperando respuesta de Microsoft al informe de falso positivo.** Enviado el
  2026-11-02, envío `4e71db95-288b-4a27-ad75-265d3b873530`, como «Incorrect
  detection» sobre `MinimalPDF_Compress.exe` con firmas 1.463.84.0. El estado
  se consulta en
  <https://www.microsoft.com/en-us/wdsi/submission/4e71db95-288b-4a27-ad75-265d3b873530>
  y la respuesta llega al correo del Director. **Queda anotar el desenlace en
  `FORK.md`**, que es donde está el expediente. Si retiran la detección del
  ejecutable, el zip se arregla solo: sólo lo marcan por lo que lleva dentro.
- `src/dependencies/pdf.ico` no lo referencia nada; anotado, no borrado.

## Decisiones tomadas

- `pngquant.org` se abandonó como origen: dos caídas desde los runners, y
  comprobado que no es cosa de Cloudflare ni de los bloqueos de España (resuelve
  a 83.169.2.68, sin cabecera `CF-RAY`). No hay espejo fiable del binario, así
  que se compila desde el código que el propio autor publica en crates.io,
  fijado por hash. Verificado en CI el 2026-11-01.
- Las herramientas opcionales en ejecución también lo son al compilar: si no se
  pueden obtener, se avisa y se sigue. Un hash que no cuadra sigue siendo fatal
  siempre, y por eso va por una excepción distinta.

- `APP_VERSION` lo sube el Director y nadie más. Está en `"1.11.0"`. El número
  de build del fork sigue yendo en la etiqueta, nunca dentro de `APP_VERSION`.
- Cambiar de idioma pide reiniciar; no se reconstruye la interfaz en caliente,
  porque perdería los archivos en cola y las vistas previas.
- El catálogo se indexa por la cadena inglesa, no por identificadores
  inventados: lo no traducido cae a inglés legible en vez de a un nombre de
  clave.
