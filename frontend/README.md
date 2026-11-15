# H.E.L.I.O.S. - Frontend Cockpit HUD

## Arquitectura Modular N-Capas

El frontend de **H.E.L.I.O.S.** ha sido completamente modularizado para garantizar un mantenimiento ágil y limpio sin incurrir en sobrecarga de rendimiento, dependencias pesadas de Node.js o consumo innecesario de GPU/RAM.

### Estructura de Directorios

```text
frontend/
├── assemble_index.py        # Compilador y ensamblador modular en Python puro (PEP 8)
├── components/              # Módulos y vistas desacopladas (< 250 líneas por archivo)
│   ├── header.html          # Cabecera de cabina y selector de ventanas
│   ├── toolbar.html         # Barra de telemetría DSN y control de simulación
│   ├── view_biomedical.html # Ventana 1: Resumen biomédico e infografía holográfica 3D
│   ├── view_environmental.html # Ventana 2: Ambiente de cabina y hábitat espacial
│   ├── view_wellness.html   # Ventana 3: Sueño, rutinas, hidratación y acceso a juegos
│   ├── modal_games.html     # Catálogo y modal de los ocho juegos
│   ├── modal_alert.html     # Modal de alerta crítica flotante
│   └── footer.html          # Pie de página y conformidad reglamentaria NASA
├── css/
│   ├── animations.css       # Efectos de escaneo y pulso lumínico
│   └── hud-theme.css        # Sistema de diseño Cyber-HUD espacial oscuro
├── js/
│   ├── controllers/         # Controlador HudController (coordinación DOM)
│   ├── services/            # Servicios de audio procedural, ECG, holograma y telemetría
│   └── state/               # Gestor de estado reactivo StateManager
└── index.html               # Archivo consolidado de producción (generado)
```

### Funcionalidad de las Ventanas

1. **Ventana 1: Biomédica & Holograma**:
   - Resumen anatómico con escaneo continuo de partículas.
   - Indicadores en tiempo real: Frecuencia cardíaca, SpO₂, Presión arterial, Temperatura, Cognición ASTRA y Densidad ósea.
   - Osciloscopio ECG a 60 FPS en derivación II.

2. **Ventana 2: Ambiente & Hábitat**:
   - Ilustraciones raster aportadas por el usuario de Nave Orion, Base Marciana y Estación Espacial, con cinco indicadores de cabina interactivos.
   - Sensores ambientales de cabina en tiempo real: ppCO₂, Radiación, Presión, Temperatura y Humedad.
   - Grafo tensorial matricial de Kronecker ($\mathbb{R}^{12}$) y contramedidas de cabina.

3. **Ventana 3: Bienestar y rutinas**:
   - **Descanso y recuperación**: Indicador circular de cumplimiento de la meta de 8 h, horarios, duración, tiempo en cama, fases interactivas e historial de siete ciclos seleccionables. La duración actual procede del estado del simulador; horarios, fases y noches anteriores se identifican como demostración. El porcentaje representa cumplimiento de duración, sin atribuirle una calidad clínica.
   - **Tareas Diarias Interactivas**: Meditación, estiramiento, ejercicio e hidratación con avance reactivo por clic (+20%).
   - **Juegos**: Botón de acceso a un modal con Laberinto orbital, Serpiente, Rompebloques, Pong, Tres en raya, Memoria, 2048 y Luces fuera.
   - **Estado de Hidratación**: Calibrador tricolor de fluidos (Óptimo, Aviso, Crítico).

4. **Ventana 4: Soporte y evaluaciones**:
   - **Exámenes Extra**: Protocolos guiados a bordo para examen oftálmico (SANS) y barrido sonar acústico.
   - **Correo de Espacio Profundo**: Buzón de enlace DSN con centro de control en Tierra.
   - **Asistente Psicológico H.E.L.I.O.S.**: Guía interactiva de respiración 4-4-6 (inhala, sostén, exhala), soporte emocional y diálogo empático sin sobrecargar con términos automatizados.
   - **Inspección Técnica de Martina**: Consulta de las 15 reglas mediante botones anterior/siguiente, con evaluación, contramedidas, destinatarios y evidencia.

### Distribución sin desplazamiento

Las cuatro vistas ocupan la altura disponible entre cabecera y pie de página. `css/hud-viewport.css` conserva el tema HUD y adapta diagramas, métricas y paneles. `js/controllers/viewport_controller.js` organiza los paneles según el ancho y la altura: en pantallas pequeñas, los botones **Anterior / Siguiente** permiten consultar el contenido completo sin scroll ni recortes. En móvil, los controles de respiración y la telemetría cognitiva tienen su propio panel dentro de Soporte.

El historial de ASTRA se consulta por mensaje. Las reglas técnicas se consultan por regla y, en móvil, por grupos de campos. Los nodos de los diagramas conservan sus acciones y las tarjetas se distribuyen debajo del diagrama cuando no caben a sus lados. `components/view_support.html` se incluye en el ensamblador junto con las otras tres vistas.

El panel de sueño adapta el patrón de resumen, fases e historial de [SOMA](https://soma.pe/experiencia#sueno) al tema HUD, sin reutilizar sus imágenes. `components/panel_sleep.html` se incorpora a Bienestar durante el ensamblado; `sleep_controller.js` coordina los ciclos, la telemetría y las fases de demostración. En móvil y en vistas compactas, las pestañas Resumen / Fases / 7 ciclos mantienen todos los detalles accesibles sin scroll. Las pruebas del perfil se ejecutan con `node --test tests/frontend_sleep.test.cjs`.

### Compilación y Regeneración

### Imágenes de hábitats

Los PNG originales del usuario se conservan en frontend/assets/habitats/ (orion.png, mars-base.png, iss.png). La interfaz usa las copias -transparent.png con canal alfa real y margen recortado. El script frontend/prepare_habitat_assets.ps1 extrae únicamente el fondo blanco conectado al borde y suaviza el contorno; no regenera las ilustraciones. HabitatDiagramService superpone cinco ramas y puntos de referencia, con anclajes propios para cada hábitat. En tableta y escritorio los indicadores rodean la imagen como en el diagrama original; en móvil se conservan las ramas y las etiquetas cortas abren el indicador seleccionado sin scroll. El dibujo anatómico de Biomédica se conserva.

### Juegos ligeros

`games_controller.js` gestiona el diálogo nativo, el teclado, los controles táctiles y la carga dinámica de `js/games/arcade.js` al elegir el primer juego. La colección no añade dependencias, imágenes, audio ni servicios de terceros. Solo se crea una partida a la vez; los cuatro juegos arcade comparten un lienzo de resolución fija de 320 × 320 y actualizan a un máximo de unas 29 veces por segundo. Los juegos de tablero solo renderizan cuando se interactúa con ellos.

Cerrar el modal, volver al catálogo o reiniciar destruye la partida anterior y cancela sus temporizadores y eventos. Al ocultar la pestaña o perder el foco se pausa la partida; una alerta crítica cierra el modal para mostrar el monitoreo. Las flechas y WASD permiten jugar con teclado; también hay botones de dirección, gestos y controles directos sobre el tablero. El tamaño y funcionamiento se verificaron en Chrome con dimensiones de tableta y móvil; no representan una certificación de hardware de NASA.

Las reglas de los juegos se verifican con `node --test tests/frontend_games.test.cjs`. `panel_games.html` y `modal_games.html` se integran durante el ensamblado.

### Compilación y Regeneración

Para compilar y ensamblar nuevamente `frontend/index.html` después de editar cualquier componente en `frontend/components/`:

```powershell
python frontend/assemble_index.py
```
