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
│   ├── view_wellness.html   # Ventana 3: Bienestar, rutinas, gamificación y asistente
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
   - Corte estructural interactivo de Nave Orion, Base Marciana y Estación Espacial.
   - Sensores ambientales de cabina en tiempo real: ppCO₂, Radiación, Presión, Temperatura y Humedad.
   - Grafo tensorial matricial de Kronecker ($\mathbb{R}^{12}$) y contramedidas de cabina.

3. **Ventana 3: Bienestar y rutinas**:
   - **Horas de Sueño / Día**: Historial circadiano semanal de 7 días (L, M, X, J, V, S, D) con línea meta de 8 h.
   - **Tareas Diarias Interactivas**: Meditación, estiramiento, ejercicio e hidratación con avance reactivo por clic y asignación de experiencia (+25 EXP).
   - **Puntaje de Gamificación**: Nivel del astronauta, barra de experiencia dinámica y medallas/insignias aeroespaciales.
   - **Estado de Hidratación**: Calibrador tricolor de fluidos (Óptimo, Aviso, Crítico).

4. **Ventana 4: Soporte y evaluaciones**:
   - **Exámenes Extra**: Protocolos guiados a bordo para examen oftálmico (SANS) y barrido sonar acústico.
   - **Correo de Espacio Profundo**: Buzón de enlace DSN con centro de control en Tierra.
   - **Asistente Psicológico H.E.L.I.O.S.**: Guía interactiva de respiración 4-4-6 (inhala, sostén, exhala), soporte emocional y diálogo empático sin sobrecargar con términos automatizados.
   - **Inspección Técnica de Martina**: Consulta de las 15 reglas mediante botones anterior/siguiente, con evaluación, contramedidas, destinatarios y evidencia.

### Distribución sin desplazamiento

Las cuatro vistas ocupan la altura disponible entre cabecera y pie de página. `css/hud-viewport.css` conserva el tema HUD y adapta diagramas, métricas y paneles. `js/controllers/viewport_controller.js` organiza los paneles según el ancho y la altura: en pantallas pequeñas, los botones **Anterior / Siguiente** permiten consultar el contenido completo sin scroll ni recortes. En móvil, los controles de respiración y la telemetría cognitiva tienen su propio panel dentro de Soporte.

El historial de ASTRA se consulta por mensaje. Las reglas técnicas se consultan por regla y, en móvil, por grupos de campos. Los nodos de los diagramas conservan sus acciones y las tarjetas se distribuyen debajo del diagrama cuando no caben a sus lados. `components/view_support.html` se incluye en el ensamblador junto con las otras tres vistas.

### Compilación y Regeneración

Para compilar y ensamblar nuevamente `frontend/index.html` después de editar cualquier componente en `frontend/components/`:

```powershell
python frontend/assemble_index.py
```
