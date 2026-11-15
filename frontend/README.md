# H.E.L.I.O.S. - Frontend Cockpit HUD

## Modular N-Layer Architecture

The **H.E.L.I.O.S.** frontend has been fully modularized to guarantee agile, clean maintenance without incurring performance overhead, heavy Node.js dependencies or unnecessary GPU/RAM consumption.

### Directory Structure

```text
frontend/
├── assemble_index.py        # Modular compiler and assembler in pure Python (PEP 8)
├── components/              # Decoupled modules and views (< 250 lines per file)
│   ├── header.html          # Cockpit header and view selector
│   ├── toolbar.html         # DSN telemetry bar and simulation controls
│   ├── view_biomedical.html # View 1: Biomedical summary and 3D holographic infographic
│   ├── view_environmental.html # View 2: Cabin environment and space habitat
│   ├── view_wellness.html   # View 3: Sleep, routines, hydration and game access
│   ├── modal_games.html     # Catalog and modal for the eight games
│   ├── modal_alert.html     # Floating critical alert modal
│   └── footer.html          # Footer and NASA regulatory compliance
├── css/
│   ├── animations.css       # Scan and light pulse effects
│   └── hud-theme.css        # Dark space Cyber-HUD design system
├── js/
│   ├── controllers/         # HudController (DOM coordination)
│   ├── services/            # Procedural audio, ECG, hologram and telemetry services
│   └── state/               # Reactive StateManager state manager
└── index.html               # Consolidated production file (generated)
```

### View Functionality

1. **View 1: Biomedical & Hologram**:
   - Anatomical summary with a continuous particle scan.
   - Real-time indicators: Heart rate, SpO₂, Blood pressure, Temperature, ASTRA cognition and Bone density.
   - 60 FPS ECG oscilloscope on lead II.

2. **View 2: Environment & Habitat**:
   - User-supplied raster illustrations of the Orion spacecraft, Mars Base and Space Station, with five interactive cabin indicators.
   - Real-time cabin environmental sensors: ppCO₂, Radiation, Pressure, Temperature and Humidity.
   - Kronecker tensor matrix graph ($\mathbb{R}^{12}$) and cabin countermeasures.

3. **View 3: Wellbeing and routines**:
   - **Rest and recovery**: Circular indicator of attainment against the 8 h goal, schedules, duration, time in bed, interactive phases and a history of seven selectable cycles. The current duration comes from the simulator state; schedules, phases and previous nights are labelled as a demonstration. The percentage represents duration attainment, without attributing clinical quality to it.
   - **Interactive Daily Tasks**: Meditation, stretching, exercise and hydration with reactive progress per click (+20%).
   - **Games**: Access button to a modal with Orbital maze, Snake, Breakout, Pong, Tic-tac-toe, Memory, 2048 and Lights out.
   - **Hydration Status**: Three-color fluid gauge (Optimal, Warning, Critical).

4. **View 4: Support and assessments**:
   - **Extra Exams**: Guided onboard protocols for the ophthalmic exam (SANS) and the acoustic sonar sweep.
   - **Deep Space Mail**: DSN link mailbox with the ground control center.
   - **H.E.L.I.O.S. Psychological Assistant**: Interactive 4-4-6 breathing guide (inhale, hold, exhale), emotional support and empathetic dialogue without overloading the user with automated jargon.
   - **Martina's Technical Inspection**: Look up the 15 rules with previous/next buttons, including the assessment, countermeasures, recipients and evidence.

### Scroll-free layout

The four views occupy the available height between the header and the footer. `css/hud-viewport.css` preserves the HUD theme and adapts diagrams, metrics and panels. `js/controllers/viewport_controller.js` organizes the panels by width and height: on small screens, the **Previous / Next** buttons let you review the full content without scrolling or clipping. On mobile, the breathing controls and the cognitive telemetry get their own panel inside Support.

The ASTRA history is browsed message by message. The technical rules are browsed rule by rule and, on mobile, by groups of fields. The diagram nodes keep their actions and the cards are laid out below the diagram when they do not fit at its sides. `components/view_support.html` is included in the assembler alongside the other three views.

The sleep panel adapts the summary, phases and history pattern from [SOMA](https://soma.pe/experiencia#sueno) to the HUD theme, without reusing its images. `components/panel_sleep.html` is folded into Wellbeing during assembly; `sleep_controller.js` coordinates the cycles, the telemetry and the demonstration phases. On mobile and in compact views, the Summary / Phases / 7 cycles tabs keep every detail accessible without scrolling. The profile tests run with `node --test tests/frontend_sleep.test.cjs`.

### Habitat images

The user's original PNGs are kept in frontend/assets/habitats/ (orion.png, mars-base.png, iss.png). The interface uses the -transparent.png copies with a real alpha channel and a trimmed margin. The script frontend/prepare_habitat_assets.ps1 extracts only the white background connected to the edge and smooths the contour; it does not regenerate the illustrations. HabitatDiagramService overlays five branches and reference points, with its own anchors for each habitat. On tablet and desktop the indicators surround the image as in the original diagram; on mobile the branches are preserved and the short labels open the selected indicator without scrolling. The anatomical drawing in Biomedical is preserved.

### Lightweight games

`games_controller.js` manages the native dialog, the keyboard, the touch controls and the dynamic loading of `js/games/arcade.js` when the first game is chosen. The collection adds no dependencies, images, audio or third-party services. Only one match exists at a time; the four arcade games share a fixed 320 × 320 canvas and refresh at most about 29 times per second. The board games only render when interacted with.

Closing the modal, returning to the catalog or restarting destroys the previous match and cancels its timers and events. Hiding the tab or losing focus pauses the match; a critical alert closes the modal to show the monitoring. Arrows and WASD allow keyboard play; there are also direction buttons, gestures and direct controls on the board. The size and behavior were verified in Chrome at tablet and mobile dimensions; they do not represent a NASA hardware certification.

The game rules are verified with `node --test tests/frontend_games.test.cjs`. `panel_games.html` and `modal_games.html` are integrated during assembly.

### Compilation and Regeneration

To compile and reassemble `frontend/index.html` after editing any component in `frontend/components/`:

```powershell
python frontend/assemble_index.py
```
