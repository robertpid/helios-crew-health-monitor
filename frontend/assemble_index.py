"""
H.E.L.I.O.S. - Generador y Ensamblador Modular del Cockpit HUD.

Este script ensambla el archivo 'frontend/index.html' a partir de componentes HTML
independientes y desacoplados ubicados en 'frontend/components/'.
Permite mantener componentes individuales de menos de 400 líneas sin sobrecargar
el archivo principal, manteniendo compatibilidad pura sin requerir bundlers pesados
(Webpack, Vite) ni dependencias externas.

Cumple estrictamente con:
- PEP 8 y anotaciones de tipo estático (Type Hints).
- Sistema de trazabilidad con logging aeroespacial (sin sentencias print).
- Principio de Responsabilidad Única (SRP).
- Punto de entrada seguro (`if __name__ == '__main__':`).
"""

import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

# Configuración del subsistema de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d UTC | %(levelname)-8s | [%(name)s] | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("helios_assembler")


class DashboardAssembler:
    """Ensamblador de vistas y componentes modulares para la interfaz H.E.L.I.O.S."""

    def __init__(self, frontend_dir: Optional[Path] = None) -> None:
        """
        Inicializa las rutas base del frontend y del directorio de componentes.

        Args:
            frontend_dir: Ruta al directorio 'frontend'. Si es None, se autocalcula.
        """
        if frontend_dir is None:
            self._frontend_dir = Path(__file__).resolve().parent
        else:
            self._frontend_dir = Path(frontend_dir).resolve()

        self._components_dir = self._frontend_dir / "components"
        self._output_file = self._frontend_dir / "index.html"

    def leer_componente(self, nombre_archivo: str) -> str:
        """
        Lee el contenido de un archivo de componente parcial en formato UTF-8.

        Args:
            nombre_archivo: Nombre del archivo dentro de 'components/'.

        Returns:
            Contenido HTML del componente.

        Raises:
            FileNotFoundError: Si el componente no existe.
        """
        ruta_componente = self._components_dir / nombre_archivo
        if not ruta_componente.is_file():
            logger.error("Componente no encontrado: %s", ruta_componente)
            raise FileNotFoundError(f"Componente requerido no existe: {ruta_componente}")

        try:
            with open(ruta_componente, "r", encoding="utf-8") as f:
                return f.read().strip()
        except OSError as e:
            logger.error("Error al leer el archivo %s: %s", nombre_archivo, str(e))
            raise

    def generar_plantilla_maestra(self) -> str:
        """
        Ensambla todos los componentes parciales en el orden estructural del Cockpit HUD.

        Returns:
            Cadena de texto con el documento HTML5 completo y formateado.
        """
        logger.info("Cargando componentes modulares desde %s...", self._components_dir)

        header_html = self.leer_componente("header.html")
        toolbar_html = self.leer_componente("toolbar.html")
        view_biomedical = self.leer_componente("view_biomedical.html")
        view_environmental = self.leer_componente("view_environmental.html")
        view_wellness = self.leer_componente("view_wellness.html").replace(
            "<!-- PANEL_SLEEP -->", self.leer_componente("panel_sleep.html")
        ).replace("<!-- PANEL_GAMES -->", self.leer_componente("panel_games.html"))
        view_support = self.leer_componente("view_support.html")
        view_surgeon = self.leer_componente("view_surgeon.html")
        modal_alert = self.leer_componente("modal_alert.html")
        modal_login = self.leer_componente("modal_login.html")
        modal_games = self.leer_componente("modal_games.html")
        modal_oftalmico = self.leer_componente("modal_oftalmico.html")
        modal_sonar = self.leer_componente("modal_sonar.html")
        footer_html = self.leer_componente("footer.html")
        version_tag = int(time.time())

        # Ensamblaje seguro de la estructura HTML5 con indentación estricta
        html_consolidado = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>H.E.L.I.O.S. - Cockpit HUD &amp; Crew Health Monitor | NASA Space Apps 2026</title>
  
  <!-- Optimización Apple WebKit & PWA para iPadOS e iOS -->
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <meta name="apple-mobile-web-app-title" content="HELIOS HUD">
  <meta name="theme-color" content="#030712">
  
  <!-- Tipografías Aeroespaciales de Google Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@600;800;900&family=Rajdhani:wght@500;600;700&family=Share+Tech+Mono&display=swap" rel="stylesheet">
  
  <!-- H.E.L.I.O.S. Capa de Estilos N-Capas Modular -->
  <link rel="stylesheet" href="/static/css/hud-theme.css?v={version_tag}">
  <link rel="stylesheet" href="/static/css/animations.css?v={version_tag}">
</head>
<body>

  {header_html}

  {toolbar_html}

  <!-- ========================================================================= -->
  <!-- 3. VIEWPORT PRINCIPAL CON CONTENEDORES DE VENTANA                         -->
  <!-- ========================================================================= -->
  <main class="main-viewport">

    {view_biomedical}

    {view_environmental}

    {view_wellness}

    {view_support}

    {view_surgeon}

  </main>

  {modal_alert}

  {modal_login}

  {modal_games}

  {modal_oftalmico}

  {modal_sonar}

  {footer_html}

  <!-- ========================================================================= -->
  <!-- 6. CARGA DE MÓDULOS DE ARQUITECTURA N-CAPAS EN JAVASCRIPT                 -->
  <!-- ========================================================================= -->
  <script src="/static/js/state/state_manager.js?v={version_tag}"></script>
  <script src="/static/js/services/auth_service.js?v={version_tag}"></script>
  <script src="/static/js/services/sound_service.js?v={version_tag}"></script>
  <script src="/static/js/services/codebook_service.js?v={version_tag}"></script>
  <script src="/static/js/services/telemetry_service.js?v={version_tag}"></script>
  <script src="/static/js/services/ecg_service.js?v={version_tag}"></script>
  <script src="/static/js/services/habitat_diagram_service.js?v={version_tag}"></script>
  <script src="/static/js/services/hologram_service.js?v={version_tag}"></script>
  <script src="/static/js/services/fit_service.js?v={version_tag}"></script>
  <script src="/static/js/services/oftalmico_service.js?v={version_tag}"></script>
  <script src="/static/js/services/sonar_service.js?v={version_tag}"></script>
  <script src="/static/js/controllers/wellness_controller.js?v={version_tag}"></script>
  <script src="/static/js/controllers/games_controller.js?v={version_tag}"></script>
  <script src="/static/js/controllers/sleep_controller.js?v={version_tag}"></script>
  <script src="/static/js/controllers/surgeon_controller.js?v={version_tag}"></script>
  <script src="/static/js/controllers/viewport_controller.js?v={version_tag}"></script>
  <script src="/static/js/controllers/hud_controller.js?v={version_tag}"></script>

  <script>
    // Inicialización del ecosistema HUD N-Capas Modular
    window.addEventListener("DOMContentLoaded", () => {{
      // 1. Instanciar Servicios
      const ecgService = new EcgOscilloscopeService("ecgDisplayCanvas");
      ecgService.inicializar();

      const hologramService = new HologramRendererService("particlesCanvas", "svgHologramBody");
      hologramService.inicializar();

      window.habitatDiagramService = new HabitatDiagramService();
      window.habitatDiagramService.inicializar();
      const habitatHologramService = new HologramRendererService(null, "habitatIllustration");
      habitatHologramService.inicializar();

      if (window.fitService?.inicializar) {{
        window.fitService.inicializar();
      }}

      // 2. Instanciar Controlador de Bienestar y Rutinas
      const wellnessController = new WellnessController(window.soundService);
      window.wellnessController = wellnessController;

      // 3. Instanciar Controlador Principal con Inyección de Dependencias
      window.hudController = new HudController(
        window.stateManager,
        ecgService,
        window.telemetryService,
        window.soundService,
        wellnessController,
        window.authService
      );
      window.viewportController = new ViewportController();
      window.viewportController.inicializar();
      window.gamesController = new GamesController(window.stateManager);
      window.gamesController.inicializar();
      window.sleepController = new SleepController(window.stateManager);
      window.sleepController.inicializar();
      window.surgeonController?.inicializar?.();
      window.hudController.inicializar();
    }});
  </script>
</body>
</html>
"""
        return html_consolidado

    def guardar_index(self) -> Path:
        """
        Genera el documento consolidado y lo escribe en el archivo index.html.

        Returns:
            Ruta absoluta del archivo generado.
        """
        html_final = self.generar_plantilla_maestra()
        try:
            with open(self._output_file, "w", encoding="utf-8") as f:
                f.write(html_final)
            logger.info("Archivo ensamblado con éxito en: %s (%d bytes)", self._output_file, len(html_final))
            return self._output_file
        except OSError as e:
            logger.error("Error al escribir el archivo %s: %s", self._output_file, str(e))
            raise


def ensamblar_interfaz_frontend(directorio_frontend: Optional[str] = None) -> str:
    """
    Función de utilidad pública para invocar el ensamblaje programáticamente.

    Args:
        directorio_frontend: Ruta opcional a la carpeta 'frontend'.

    Returns:
        Ruta como string del archivo generado.
    """
    directorio_path = Path(directorio_frontend) if directorio_frontend else None
    assembler = DashboardAssembler(directorio_path)
    resultado = assembler.guardar_index()
    return str(resultado)


if __name__ == "__main__":
    logger.info("Iniciando compilador/ensamblador modular de H.E.L.I.O.S....")
    try:
        ruta_salida = ensamblar_interfaz_frontend()
        logger.info("Compilación modular finalizada sin errores: %s", ruta_salida)
    except Exception as exc:
        logger.error("Fallo durante el ensamblado modular: %s", str(exc))
        sys.exit(1)
