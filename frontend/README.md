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

3. **Ventana 3: Bienestar, Rutinas & Asistente**:
   - **Horas de Sueño / Día**: Historial circadiano semanal de 7 días (L, M, X, J, V, S, D) con línea meta de 8 h.
   - **Tareas Diarias Interactivas**: Meditación, estiramiento, ejercicio e hidratación con avance reactivo por clic y asignación de experiencia (+25 EXP).
   - **Puntaje de Gamificación**: Nivel del astronauta, barra de experiencia dinámica y medallas/insignias aeroespaciales.
   - **Estado de Hidratación**: Calibrador tricolor de fluidos (Óptimo, Aviso, Crítico).
   - **Exámenes Extra**: Protocolos guiados a bordo para examen oftálmico (SANS) y barrido sonar acústico.
   - **Correo de Espacio Profundo**: Buzón de enlace DSN con centro de control en Tierra.
   - **Asistente Psicológico H.E.L.I.O.S.**: Guía interactiva de respiración 4-4-6 (inhala, sostén, exhala), soporte emocional y diálogo empático sin sobrecargar con términos automatizados.
   - **Inspección Técnica de Martina**: Cajón desplegable con la matriz formal de 15 cruces de datos críticos y contramedidas priorizadas (máximo 3 acciones).

### Compilación y Regeneración

Para compilar y ensamblar nuevamente `frontend/index.html` después de editar cualquier componente en `frontend/components/`:

```powershell
python frontend/assemble_index.py
```
