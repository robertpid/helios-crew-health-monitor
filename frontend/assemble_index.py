"""
H.E.L.I.O.S. - Modular Cockpit HUD Generator and Assembler.

This script assembles the file 'frontend/index.html' from independent, decoupled
HTML components located in 'frontend/components/'.
It keeps individual components under 400 lines without bloating the main file,
preserving pure compatibility with no heavy bundlers (Webpack, Vite) or external
dependencies.

Complies strictly with:
- PEP 8 and static type annotations (Type Hints).
- Traceability through aerospace logging (no print statements).
- Single Responsibility Principle (SRP).
- Safe entry point (`if __name__ == '__main__':`).
"""

import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

# Logging subsystem configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d UTC | %(levelname)-8s | [%(name)s] | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("helios_assembler")


class DashboardAssembler:
    """Assembler of modular views and components for the H.E.L.I.O.S. interface."""

    def __init__(self, frontend_dir: Optional[Path] = None) -> None:
        """
        Initializes the base paths of the frontend and the components directory.

        Args:
            frontend_dir: Path to the 'frontend' directory. If None, it is auto-computed.
        """
        if frontend_dir is None:
            self._frontend_dir = Path(__file__).resolve().parent
        else:
            self._frontend_dir = Path(frontend_dir).resolve()

        self._components_dir = self._frontend_dir / "components"
        self._output_file = self._frontend_dir / "index.html"

    def read_component(self, file_name: str) -> str:
        """
        Reads the content of a partial component file in UTF-8.

        Args:
            file_name: Name of the file inside 'components/'.

        Returns:
            HTML content of the component.

        Raises:
            FileNotFoundError: If the component does not exist.
        """
        component_path = self._components_dir / file_name
        if not component_path.is_file():
            logger.error("Component not found: %s", component_path)
            raise FileNotFoundError(f"Required component does not exist: {component_path}")

        try:
            with open(component_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except OSError as e:
            logger.error("Error reading the file %s: %s", file_name, str(e))
            raise

    def generate_master_template(self) -> str:
        """
        Assembles every partial component in the structural order of the Cockpit HUD.

        Returns:
            String with the complete, formatted HTML5 document.
        """
        logger.info("Loading modular components from %s...", self._components_dir)

        header_html = self.read_component("header.html")
        toolbar_html = self.read_component("toolbar.html")
        view_biomedical = self.read_component("view_biomedical.html")
        view_environmental = self.read_component("view_environmental.html")
        view_wellness = self.read_component("view_wellness.html").replace(
            "<!-- PANEL_SLEEP -->", self.read_component("panel_sleep.html")
        ).replace("<!-- PANEL_GAMES -->", self.read_component("panel_games.html"))
        view_support = self.read_component("view_support.html")
        view_surgeon = self.read_component("view_surgeon.html")
        modal_alert = self.read_component("modal_alert.html")
        modal_login = self.read_component("modal_login.html")
        modal_games = self.read_component("modal_games.html")
        modal_ophthalmic = self.read_component("modal_ophthalmic.html")
        modal_sonar = self.read_component("modal_sonar.html")
        footer_html = self.read_component("footer.html")
        version_tag = int(time.time())

        # Safe assembly of the HTML5 structure with strict indentation
        consolidated_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>H.E.L.I.O.S. - Cockpit HUD &amp; Crew Health Monitor | NASA Space Apps 2026</title>

  <!-- Apple WebKit & PWA optimization for iPadOS and iOS -->
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <meta name="apple-mobile-web-app-title" content="HELIOS HUD">
  <meta name="theme-color" content="#030712">

  <!-- Aerospace typefaces from Google Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@600;800;900&family=Rajdhani:wght@500;600;700&family=Share+Tech+Mono&display=swap" rel="stylesheet">

  <!-- H.E.L.I.O.S. modular N-layer style layer -->
  <link rel="stylesheet" href="/static/css/hud-theme.css?v={version_tag}">
  <link rel="stylesheet" href="/static/css/animations.css?v={version_tag}">
</head>
<body>

  {header_html}

  {toolbar_html}

  <!-- ========================================================================= -->
  <!-- 3. MAIN VIEWPORT WITH THE VIEW CONTAINERS                                 -->
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

  {modal_ophthalmic}

  {modal_sonar}

  {footer_html}

  <!-- ========================================================================= -->
  <!-- 6. LOADING THE N-LAYER ARCHITECTURE MODULES IN JAVASCRIPT                 -->
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
  <script src="/static/js/services/mail_service.js?v={version_tag}"></script>
  <script src="/static/js/services/sensor_watchdog_service.js?v={version_tag}"></script>
  <script src="/static/js/services/ophthalmic_service.js?v={version_tag}"></script>
  <script src="/static/js/services/sonar_service.js?v={version_tag}"></script>
  <script src="/static/js/controllers/wellness_controller.js?v={version_tag}"></script>
  <script src="/static/js/controllers/games_controller.js?v={version_tag}"></script>
  <script src="/static/js/controllers/sleep_controller.js?v={version_tag}"></script>
  <script src="/static/js/controllers/surgeon_controller.js?v={version_tag}"></script>
  <script src="/static/js/controllers/viewport_controller.js?v={version_tag}"></script>
  <script src="/static/js/controllers/hud_controller.js?v={version_tag}"></script>

  <script>
    // Initialization of the modular N-layer HUD ecosystem
    window.addEventListener("DOMContentLoaded", () => {{
      // 1. Instantiate services
      const ecgService = new EcgOscilloscopeService("ecgDisplayCanvas");
      ecgService.initialize();

      const hologramService = new HologramRendererService("particlesCanvas", "svgHologramBody");
      hologramService.initialize();

      window.habitatDiagramService = new HabitatDiagramService();
      window.habitatDiagramService.initialize();
      const habitatHologramService = new HologramRendererService(null, "habitatIllustration");
      habitatHologramService.initialize();

      if (window.fitService?.initialize) {{
        window.fitService.initialize();
      }}

      window.mailService = new MailService(window.soundService, window.authService);
      window.mailService.updateMailUi();
      if (window.authService?.subscribe) {{
        window.authService.subscribe(() => {{
          window.mailService?.updateMailUi();
        }});
      }}

      // 2. Instantiate the wellbeing and routines controller
      const wellnessController = new WellnessController(window.soundService);
      window.wellnessController = wellnessController;

      // 3. Instantiate the main controller with dependency injection
      window.hudController = new HudController(
        window.stateManager,
        ecgService,
        window.telemetryService,
        window.soundService,
        wellnessController,
        window.authService
      );
      window.viewportController = new ViewportController();
      window.viewportController.initialize();
      window.gamesController = new GamesController(window.stateManager);
      window.gamesController.initialize();
      window.sleepController = new SleepController(window.stateManager);
      window.sleepController.initialize();
      window.surgeonController?.initialize?.();
      window.hudController.initialize();
      window.sensorWatchdogService = new SensorWatchdogService(window.stateManager, window.soundService);
      window.sensorWatchdogService.initialize();
    }});
  </script>
</body>
</html>
"""
        return consolidated_html

    def save_index(self) -> Path:
        """
        Generates the consolidated document and writes it to the index.html file.

        Returns:
            Absolute path of the generated file.
        """
        final_html = self.generate_master_template()
        try:
            with open(self._output_file, "w", encoding="utf-8") as f:
                f.write(final_html)
            logger.info("File assembled successfully at: %s (%d bytes)", self._output_file, len(final_html))
            return self._output_file
        except OSError as e:
            logger.error("Error writing the file %s: %s", self._output_file, str(e))
            raise


def assemble_frontend_interface(frontend_directory: Optional[str] = None) -> str:
    """
    Public utility function to invoke the assembly programmatically.

    Args:
        frontend_directory: Optional path to the 'frontend' folder.

    Returns:
        Path of the generated file as a string.
    """
    directory_path = Path(frontend_directory) if frontend_directory else None
    assembler = DashboardAssembler(directory_path)
    result = assembler.save_index()
    return str(result)


if __name__ == "__main__":
    logger.info("Starting the H.E.L.I.O.S. modular compiler/assembler...")
    try:
        output_path = assemble_frontend_interface()
        logger.info("Modular compilation finished with no errors: %s", output_path)
    except Exception as exc:
        logger.error("Failure during the modular assembly: %s", str(exc))
        sys.exit(1)
