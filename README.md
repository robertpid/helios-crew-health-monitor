# HELIOS Simulator (v2.1.0)
## Synthetic Life Support Telemetry Producer for Deep Space
### Space Mission to Mars (Day 120) · NASA Space Apps 2026

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Pydantic v2](https://img.shields.io/badge/pydantic-v2.10%2B-green.svg)](https://docs.pydantic.dev/)
[![Redis](https://img.shields.io/badge/redis-pub%2Fsub%20%2B%20queue-red.svg)](https://redis.io/)
[![NASA Standards](https://img.shields.io/badge/standards-NASA--STD--3001%20%7C%20RIDGE-orange.svg)](https://www.nasa.gov/hrp/hazards)
[![Code Style](https://img.shields.io/badge/code%20style-PEP%208%20%7C%20Clean%20Code-black.svg)](https://peps.python.org/pep-0008/)

---

## 1. System Vision and Operational Mission

`helios_simulator` is a biomedical and environmental edge telemetry engine (**Edge AI**) developed for life support systems on crewed deep space missions (e.g. Earth-Mars transit, **Sol 120**).

On interplanetary missions, the communication delay with Earth (**RIDGE Hazard D**, up to 22 minutes one way) makes it infeasible to depend on ground stations for immediate decision making. This module periodically (every 2 seconds) generates a payload enriched with mathematical validations, stochastic physiological noise and multivariate crossovers between hazards, and injects it into the local **Redis** messaging bus on the channel and queue `earth_telemetry_mailbox`.

---

## 2. Constraint Compliance and N-Tier Architecture

The system implements a strict separation of responsibilities split across 4 decoupled layers:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       PRESENTATION LAYER (Main / CLI)                       │
│  [run_helios.py] ──> [TelemetryOrchestrator]                                │
│  Drives the 2-second loop, CLI flag parsing and signal handling.            │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Dependency Injection (DIP)
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                     SERVICES LAYER (Business Logic)                         │
│  • EnvironmentGenerator (Brain 1: CO2, SPE radiation, Pressure)             │
│  • BiometricsGenerator (Brain 2: HR, circadian sleep, HSRB bone loss)       │
│  • CognitionGenerator (Brain 4: ASTRA, verbal latency, SANS, stress)        │
│  • CorrelationEvaluatorService (Alert matrix and NASA standards)            │
│  • math_noise.py (Gaussian modeling, normal distribution, DRY)              │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Builds and validates
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                         DOMAIN LAYER (Models)                               │
│  • EnvironmentModel · BiometricsModel · CognitionModel                      │
│  • PreliminaryAssessmentAlert · TelemetryPayload                            │
│  • Enums: AlertLevel, RidgeHazard, ConnectionState                          │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ TelemetryPublisherInterface contract
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                   INFRASTRUCTURE LAYER (Repository/Publisher)               │
│  • RedisTelemetryPublisher: Persistent connection, Pub/Sub, FIFO queues     │
│  • Store-and-Forward: Local buffer tolerant to network drops                │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Applied SOLID Principles
1. **SRP (Single Responsibility Principle):**
   - The models (`domain/models.py`) only define schemas, types and immutable validations.
   - The generator classes (`services/`) only compute aerospace physics and physiology.
   - `RedisTelemetryPublisher` (`infrastructure/`) handles connectivity, serialization and transport resilience.
   - `TelemetryOrchestrator` (`presentation/`) coordinates timing and dependencies without mixing in network logic or mathematics.
2. **DIP (Dependency Inversion Principle):**
   - The orchestrator depends exclusively on the `TelemetryPublisherInterface` abstraction. The concrete Redis infrastructure is injected at startup, making testing with mocks easy and leaving room for future adaptation (e.g. MQTT, WebSockets or ZeroMQ).
3. **Strict Medical Lexicon:**
   - Compliance with aerospace telemedicine guidelines: any presumptive clinical terminology is avoided. Instead, the system formally uses **`preliminary_assessment`** and **`alert`**, aligning with NASA guidance.
4. **Clean Code & Resilience:**
   - Full static typing (`Type Hinting`).
   - Structured logging with `logging` (debug `print()` is forbidden).
   - **Store-and-Forward** pattern: if the Redis server is lost, messages are queued in an in-memory FIFO buffer and transmitted automatically once the connection is restored.

---

## 3. Aerospace Business Rules (NASA-STD-3001 & RIDGE)

### "Day 120" Simulation
For day 120 of the mission to Mars, the parameters reflect the cumulative wear of microgravity:

#### Brain 1: Cabin Environment
* **Carbon Dioxide (`co2_mmHg`):**
  - Nominal range: $1.0 - 2.2\text{ mmHg}$.
  - Injection of peaks $> 3.0\text{ mmHg}$ that exceed the **NASA-STD-3001 Vol. 2 [V2 6004]** standard (1-hour limit $\le 3\text{ mmHg}$).
  - Monitoring of the symptom threshold from $2.3\text{ mmHg}$ and the 7-day threshold of $2.5\text{ mmHg}$ (NASA OCHMO-TB-004).
* **Cumulative Radiation (`cumulative_radiation_mSv`):**
  - Initial base at Day 120: $50.0\text{ mSv} + (120 \times 0.35\text{ mSv/day}) \approx 92.0\text{ mSv}$.
  - Daily rate: $0.2 - 0.5\text{ mSv/day}$ (real detector data from the ISS / NTRS Simonsen et al., 2025).
  - **1% probability of a Solar Storm (SPE):** sudden injection of $+20\text{ mSv}$ per event (referenced against the solar event limit $< 250\text{ mSv}$ and the career limit $< 600\text{ mSv}$ per NASA-STD-3001 Vol. 1 [V1 4030]).
* **Cabin Pressure (`cabin_pressure_kpa`):**
  - Nominal interval regulated between $95.0\text{ kPa}$ and $103.0\text{ kPa}$ per **NASA-STD-3001 Vol. 2 [V2 6006]**.

#### Brain 2: Physiological Biometrics
* **Heart Rate (`heart_rate_bpm`):**
  - Baseline of $65 \pm 5\text{ bpm}$, modulated upward under environmental stress or hypoxia/hypercapnia.
* **Sleep Hours and Fatigue Risk (`last_cycle_sleep_hours`):**
  - Average of $6.0\text{ h}$ (*The Lancet Neurology* study, 2014; $N=85$ astronauts on the ISS).
  - If the crew member accumulates **3 consecutive cycles with $< 6.0\text{ h}$ of rest**, the `fatigue_risk_alert = True` flag is raised automatically.
* **Bone Mass Loss (`bone_loss_pct`):**
  - Demineralization model: $\text{Loss}(\%) = \left(\frac{\text{Day}}{30}\right) \times 1.5\%$.
  - On **Day 120**, the computed loss is exactly **$6.0\%$** (backed by studies of Mir cosmonauts and the NASA Human System Risk Board, *npj Microgravity*).

#### Brain 4: Psychology and Cognition (ASTRA)
* **Voice Latency (`voice_latency_ms`):**
  - Nominal base: $\sim 200\text{ ms}$.
  - **MULTIVARIATE LOGICAL CROSSOVER:** If $\text{CO}_2 > 2.5\text{ mmHg}$ or $\text{sleep\_hours} < 6.0\text{ h}$, the latency spikes to a range between **$600\text{ ms}$ and $900\text{ ms}$**, simulating lethargy and psychomotor deterioration.
* **Lexical Density (`lexical_density_score`):**
  - Score between $0.0$ and $1.0$.
  - **COGNITIVE INCONGRUENCE (Hidden Stress):** Occasionally the astronaut tries to mask stress: elevated heart rate ($> 95\text{ bpm}$) but with lexical density sustained at $\sim 0.80$ ("pretending to be fine").
* **SANS Vision Symptom (`sans_vision_symptom`):**
  - Boolean raised under high stress, hypercapnia or hemodynamic overload, modeling the **$81\%$** prevalence reported in NASA's **LSAH** (Lifetime Surveillance of Astronaut Health) program due to the shift of $1000 - 1500\text{ ml}$ of fluids toward the skull.

---

## 4. 120-Day Multi-Habitat Analytical Simulator (4 Operational Environments)

Beyond the reactive telemetry emitter every 2 seconds, the system includes the `MultiHabitat120DaySimulator` analytical engine in `helios_simulator/services/multi_habitat_simulator.py`. This module generates complete **120-day** time series to compare the evolution of each vital sign and environmental variable across the 4 spaceflight habitats:

```
                                  ┌───────────────────────────┐
                                  │  MULTI-HABITAT SIMULATOR  │
                                  │  120-day series           │
                                  └─────────────┬─────────────┘
                ┌───────────────────────┬───────┴───────────────┬───────────────────────┐
                ▼                       ▼                       ▼                       ▼
    ┌───────────────────────┐ ┌───────────────────┐ ┌───────────────────────┐ ┌───────────────────┐
    │    SPACE STATION      │ │    LUNAR BASE     │ │      SPACECRAFT       │ │     MARS BASE     │
    │  ISS / LEO (0.00g)    │ │ Artemis (0.166g)  │ │ Deep Space (0.00g)    │ │ Surface (0.38g)   │
    │  Delay: < 1 sec       │ │ Delay: 1.3 sec    │ │ Delay: 15 min         │ │ Delay: 20 min     │
    │  Rad: 0.35 mSv/d      │ │ Rad: 1.35 mSv/d   │ │ Rad: 1.80 mSv/d       │ │ Rad: 0.67 mSv/d   │
    │  BoneLoss: 6.0%       │ │ BoneLoss: 5.0%    │ │ BoneLoss: 6.0%        │ │ BoneLoss: 3.7%    │
    └───────────────────────┘ └───────────────────┘ └───────────────────────┘ └───────────────────┘
```

### Data Basis and Comparative Parameters per Habitat:
1. **International Space Station (ISS / LEO):**
   - **Gravity:** Microgravity ($0.0\text{ g}$).
   - **Daily Radiation:** $0.2 - 0.5\text{ mSv/day}$ (mean $0.35\text{ mSv/day}$, Simonsen et al., 2025; RadLab). Shielded by Earth's magnetosphere; accumulates $\sim 56\text{ mSv}$ by Day 120 ($9.4\%$ of the career limit).
   - **Link Delay:** $< 1\text{ second}$ (real time with Houston).
   - **Bone Loss:** Maximum microgravity rate of $1.5\%$ monthly ($6.0\%$ at 120 days).
2. **Lunar Base (Artemis Base Camp - Lunar Surface):**
   - **Gravity:** $0.166\text{ g}$ ($1/6\text{ g}$).
   - **Daily Radiation:** $\sim 1.35\text{ mSv/day}$ ($\approx 60\text{ }\mu\text{Sv/h}$ measured on Chang'e 4 by the LND instrument). No protective magnetosphere; accumulates $\sim 268\text{ mSv}$ by Day 120 ($44.7\%$ of the career budget) because of frequent solar storms with no atmospheric filter.
   - **Link Delay:** $1.3\text{ seconds}$ one way.
   - **Bone Loss:** Partially attenuated by $1/6\text{ g}$: $\sim 1.25\%$ monthly ($5.0\%$ accumulated at 120 days).
3. **Transit Spacecraft (Deep Space Transit to Mars):**
   - **Gravity:** Strict microgravity ($0.0\text{ g}$).
   - **Daily Radiation:** $\sim 1.80\text{ mSv/day}$ (direct measurement by the RAD instrument on the Curiosity rover in transit to Mars; Hassler et al., *Science* 2013). Accumulates more than $300\text{ mSv}$ in 120 days ($50.5\%$ of the career limit in just 4 months).
   - **Link Delay:** Progressive, averaging $15\text{ minutes}$ at mid transit (RIDGE Hazard D).
   - **Bone Loss:** $6.0\%$ accumulated at 120 days.
   - **SANS and Fatigue:** Maximum SANS prevalence and $23$ days with a cumulative fatigue alert from severe confinement.
4. **Mars Surface Base (Martian Habitat):**
   - **Gravity:** $0.38\text{ g}$ ($3/8\text{ g}$).
   - **Daily Radiation:** $\sim 0.67\text{ mSv/day}$ on the surface (Curiosity RAD in Gale Crater; the planet blocks $50\%$ of cosmic rays and the atmosphere provides mild shielding). Accumulates $\sim 125\text{ mSv}$ ($21.0\%$ of the career budget).
   - **Link Delay:** $20+\text{ minutes}$ of delay one way.
   - **Sol Duration:** $24\text{ h } 39\text{ min}$ ($24.65\text{ h}$). Causes circadian desynchronization in the crew.
   - **Bone Loss:** Significantly attenuated to $\sim 0.93\%$ monthly ($3.7\%$ accumulated at 120 sols).

### Efficiency and Vectorized Processing (Clean Code)
The simulator operates **100% vectorized with NumPy and Pandas**. It uses no per-row iteration (`iterrows()` or `itertuples()` are forbidden). It generates $480$ complete observations and produces the artifacts in under 0.1 seconds.

### Running the Multi-Habitat Simulation:
```powershell
python run_simulation_120_days.py --days 120 --output-directory generated_data
```
Automatically generates:
- `generated_data/telemetry_120_days_four_habitats.csv` (114 KB)
- `generated_data/telemetry_120_days_four_habitats.parquet` (55 KB)
- `generated_data/telemetry_120_days_four_habitats.jsonl` (506 KB)

---

## 5. Project Structure

```
helios-crew-health-monitor/
├── helios_simulator/
│   ├── __init__.py                     # Package metadata
│   ├── config.py                       # Constants, multi-habitat profiles and NASA-STD-3001 thresholds
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── enums.py                    # MissionEnvironment, AlertLevel, RidgeHazard, ConnectionState
│   │   └── models.py                   # Pydantic models (Environment, Biometrics, Cognition)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── math_noise.py               # Gaussian generation and decay formulas
│   │   ├── environment_generator.py    # Brain 1 service (Cabin and Radiation)
│   │   ├── biometrics_generator.py     # Brain 2 service (Physiology and Fatigue)
│   │   ├── cognition_generator.py      # Brain 4 service (ASTRA and logical crossovers)
│   │   ├── correlation_evaluator.py    # Preliminary assessments and NASA alerts
│   │   └── multi_habitat_simulator.py  # Vectorized 120-day analytical engine (4 habitats)
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   ├── publisher_interface.py      # Abstract contract (DIP)
│   │   └── redis_publisher.py          # Redis implementation with Store-and-Forward
│   └── presentation/
│       ├── __init__.py
│       └── orchestrator.py             # Main loop orchestrator
├── helios_inference/
│   ├── brains/                         # The 4 inference brains (environmental, biometric, fusion, ASTRA)
│   ├── domain/                         # Inference models, decision rules and the telemetry codebook
│   ├── services/                       # Inference engine, decision matrix and compactor
│   ├── infrastructure/                 # Asynchronous Redis consumer
│   └── api/                            # telemetry_router.py · psychology_router.py
├── tests/
│   ├── __init__.py
│   ├── test_helios_simulator.py        # Reactive telemetry unit test suite
│   ├── test_helios_inference.py        # Inference engine and FastAPI endpoint suite
│   ├── test_multi_habitat_120_days.py  # 120-day multi-habitat analytical suite
│   └── test_telemetry_compactor.py     # Compaction and lossless reconstruction suite
├── generated_data/                     # Dataset output (CSV, Parquet, JSONL)
├── run_helios.py                       # Main executable script (reactive entry point)
├── run_simulation_120_days.py          # Executable script for the 120-day simulation
├── requirements.txt                    # Production and test dependencies
└── README.md                           # Complete technical documentation
```

---

## 6. Installation and Startup

### Prerequisites
- Python 3.10 or higher (compatible with Python 3.14).
- Local or remote Redis server (optional at startup; if it is not running, the system enters resilient mode automatically).

### Installing Dependencies
```powershell
pip install -r requirements.txt
```

### Basic Run (reactive telemetry every 2 seconds):
To start the continuous transmission every 2 seconds targeting Redis (`earth_telemetry_mailbox`):
```powershell
python run_helios.py
```

### Running the 120-Day Simulation (4 Habitats):
To generate the complete 120-day multivariate dataset for the Space Station, Lunar Base, Spacecraft and Mars Base:
```powershell
python run_simulation_120_days.py --days 120 --output-directory generated_data
```

---

## 7. Running the Automated Tests

The test suite exhaustively validates the mathematical computations, NASA thresholds, Redis publisher fault tolerance, dependency inversion, the 120-day time series, the inference engine and the HTTP contract of the API:

```powershell
pytest -v
```

Result of the 56 tests:
```
tests/test_helios_inference.py::TestEnvironmentalBrain          3 passed
tests/test_helios_inference.py::TestBiometricBrain              2 passed
tests/test_helios_inference.py::TestKroneckerFusionGraphBrain   2 passed
tests/test_helios_inference.py::TestAstraCognitiveBrain         3 passed
tests/test_helios_inference.py::TestInferenceEngineOrchestrator 1 passed
tests/test_helios_inference.py::TestFastAPIEndpoints            8 passed
tests/test_helios_inference.py::TestDecisionMatrixEvaluator     3 passed
tests/test_helios_simulator.py                                 10 passed
tests/test_multi_habitat_120_days.py                            7 passed
tests/test_telemetry_compactor.py                              17 passed
=============================== 56 passed ===============================
```

---

## 8. Structure of the Injected JSON Payload

Example of the payload transmitted to Redis on each 2-second cycle:

```json
{
  "timestamp": "2026-11-14T15:37:32.503912Z",
  "mission_id": "ARES-VI-MARS-EXPEDITION",
  "mission_day": 120,
  "astronaut_id": "ASTRO-HELIOS-01",
  "environment": {
    "co2_mmHg": 3.78,
    "cumulative_radiation_mSv": 92.45,
    "daily_radiation_rate_mSv": 0.362,
    "cabin_pressure_kpa": 101.15,
    "cabin_temperature_c": 21.42,
    "solar_event_active": false
  },
  "biometrics": {
    "heart_rate_bpm": 83.2,
    "last_cycle_sleep_hours": 4.9,
    "consecutive_insufficient_sleep_cycles": 3,
    "fatigue_risk_alert": true,
    "bone_loss_pct": 6.0,
    "systolic_pressure_mmHg": 132.4,
    "diastolic_pressure_mmHg": 84.8,
    "spo2_pct": 98.1
  },
  "cognition": {
    "voice_latency_ms": 702.5,
    "lexical_density_score": 0.44,
    "hidden_stress_incongruence": false,
    "sans_vision_symptom": true
  },
  "preliminary_assessments": [
    {
      "code": "ALERT-CO2-MAX-V2-6004",
      "level": "CRITICAL",
      "ridge_hazard": "E - Hostile and closed environments",
      "reference_standard": "NASA-STD-3001 Vol.2 [V2 6004]",
      "description": "CO2 concentration (3.78 mmHg) exceeds the normative limit of 3.0 mmHg. Imminent risk of headache and operational lethargy.",
      "multivariate_crossover": false
    },
    {
      "code": "ALERT-CHRONIC-FATIGUE-HSRB",
      "level": "WARNING",
      "ridge_hazard": "I - Isolation and confinement",
      "reference_standard": "NASA HSRB & The Lancet Neurology (2014)",
      "description": "Severe fatigue risk activated: 3 consecutive cycles with sleep under 6.0 hours (last: 4.9h).",
      "multivariate_crossover": false
    },
    {
      "code": "ALERT-COGNITIVE-LATENCY-CROSSOVER",
      "level": "WARNING",
      "ridge_hazard": "D - Distance from Earth",
      "reference_standard": "NASA OCHMO-TB-004 & ASTRA Protocol",
      "description": "Cognitive slowing detected: verbal latency at 702.5 ms (normal: ~200 ms). Triggered by the synergistic crossover of CO2 3.78 mmHg and sleep deficit 4.9h.",
      "multivariate_crossover": true
    },
    {
      "code": "ALERT-SANS-VISION-SYMPTOM",
      "level": "WARNING",
      "ridge_hazard": "G - Altered gravity fields",
      "reference_standard": "NASA Lifetime Surveillance of Astronaut Health (LSAH 2026)",
      "description": "SANS neuro-ocular symptoms reported (blurred vision / headache). Correlated with cephalic fluid shift (1000-1500 ml) and systemic stress.",
      "multivariate_crossover": true
    }
  ],
  "career_radiation_budget_pct": 15.41,
  "system_metadata": {
    "producer_module": "helios_simulator",
    "architecture": "N-Layer Edge AI",
    "sampling_frequency_hz": 0.5,
    "interval_seconds": 2.0,
    "sample_cycle_id": 2,
    "redis_channel": "earth_telemetry_mailbox",
    "link_status": "DISCONNECTED"
  }
}
```

---

## 9. Official References and Scientific Basis

* **NASA-STD-3001 Vol. 1:** *Crew Health* - Requirement `[V1 4030]`: Career radiation dose $< 600\text{ mSv}$, SPE event $< 250\text{ mSv}$.
* **NASA-STD-3001 Vol. 2:** *Human Factors, Habitability, and Environmental Health* - Requirement `[V2 6004]`: 1-hour average $\text{CO}_2 \le 3.0\text{ mmHg}$; Requirement `[V2 6006]`: Cabin pressure between $95.0$ and $103.0\text{ kPa}$.
* **NASA OCHMO-TB-004:** *Carbon Dioxide Technical Brief* - Asymptomatic threshold $< 2.5\text{ mmHg}$ 7-day average.
* **NASA HSRB & npj Microgravity (2017):** Bone mineral density loss of $1.0 - 1.5\%$ per month in weightlessness.
* **The Lancet Neurology (2014):** Barger et al., sleep study across $85$ astronauts ($>4,200$ nights). Chronic sleep deficit on long-duration missions.
* **Eye (2026) / NASA LSAH (N20):** Prevalence of Neuro-ocular Syndrome (SANS) signs in $81\%$ of the astronauts analyzed ($52$ of $64$).

---

## 10. H.E.L.I.O.S. Central Inference Engine (`main.py`)

### 10.1 Lightweight Edge AI Architecture (No PyTorch, No Graph Databases)

The central inference module (`main.py`) runs an ultra-light runtime developed specifically for radiation-tolerant aerospace onboard computers (SBCs with limited RAM and no accelerated GPU).

```
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │                       REDIS QUEUE / ASYNCHRONOUS INGESTION                  │
 │  RPOP 'earth_telemetry_mailbox' (redis.asyncio)                             │
 └──────────────────────────────────────┬──────────────────────────────────────┘
                                        │ Deserialized JSON payload
 ┌──────────────────────────────────────▼──────────────────────────────────────┐
 │                     INFERENCE ENGINE (Central Orchestrator)                 │
 │                                                                             │
 │  ┌─────────────────────────┐             ┌───────────────────────────────┐  │
 │  │ Brain 1: Env. Engine    │             │ Brain 2: Biometric Engine     │  │
 │  │ Heuristic Rules R^3     │             │ Baseline Deviation R^4        │  │
 │  │ [CO2, Radiation, Pres.] │             │ [Pulse, Sleep, Bone, SANS]    │  │
 │  └────────────┬────────────┘             └───────────────┬───────────────┘  │
 │               │                                          │                  │
 │               └──────────────────┬───────────────────────┘                  │
 │                                  │                                          │
 │               ┌──────────────────▼───────────────────────┐                  │
 │               │ Brain 3: Graph and Spatial Fusion        │                  │
 │               │ Kronecker Tensor Product (np.kron)       │                  │
 │               │ V_kron = v_env ⊗ v_bio in R^12           │                  │
 │               │ P = V_kron ⊙ W  =>  k* = argmax(P)       │                  │
 │               └──────────────────┬───────────────────────┘                  │
 │                                  │                                          │
 │               ┌──────────────────▼───────────────────────┐                  │
 │               │ Brain 4: ASTRA Cognitive Vector          │                  │
 │               │ Cosine Similarity (np.dot / norms)       │                  │
 │               │ Cognitive Incongruence Detection         │                  │
 │               └──────────────────┬───────────────────────┘                  │
 │                                  │                                          │
 └──────────────────────────────────┼──────────────────────────────────────────┘
                                    │
 ┌──────────────────────────────────▼──────────────────────────────────────────┐
 │                         FASTAPI REST API (Port 8000)                        │
 │  • GET  /api/v1/fusion/result (Consolidated output of the 4 brains)         │
 │  • GET  /api/v1/alerts        (Active preliminary assessments)              │
 │  • POST /api/v1/infer         (Direct assessment in < 2 ms)                 │
 └─────────────────────────────────────────────────────────────────────────────┘
```

### 10.2 Decision Graph Modeling via the Kronecker Tensor Product

Instead of requiring disk-based graph engines such as Neo4j, the interaction coupling between $3$ environmental stressors and $4$ physiological biomarkers is formulated algebraically:

$$\mathbf{V}_{\text{kron}} = \mathbf{v}_{\text{env}} \otimes \mathbf{v}_{\text{bio}} \in \mathbb{R}^{12}$$

Where each position $k = 4i + j$ represents a synergistic decision edge weighted by the clinical vector $\mathbf{W} \in \mathbb{R}^{12}$:

$$\mathbf{P} = \mathbf{V}_{\text{kron}} \odot \mathbf{W}$$
$$k^* = \arg\max(\mathbf{P})$$

If $P_{k^*} \ge \text{threshold}$ (e.g. $6.5$), the system raises the **severe physiological stress** flag and identifies the dominant edge in $\mathcal{O}(1)$ time.

### 10.3 Cognitive Incongruence Detection (Brain 4 - ASTRA)

ASTRA builds the normalized cognitive vector $\mathbf{C}_{\text{norm}} = [\text{latency} / 200.0, \text{density} / 1.0]$ and computes the **Cosine Similarity** against the baseline $\mathbf{B}_{\text{norm}} = [1.0, 1.0]$:

$$\cos(\theta) = \frac{\mathbf{C}_{\text{norm}} \cdot \mathbf{B}_{\text{norm}}}{\|\mathbf{C}_{\text{norm}}\|_2 \|\mathbf{B}_{\text{norm}}\|_2}$$

* **Incongruence Rule:** If the similarity drops abruptly (latency at 600–900 ms) but the physical metrics are nominal, or if the body is tachycardic ($>95\text{ bpm}$) while the astronaut formalizes their diction ($\ge 0.75$), Brain 4 concludes:
  `{"astra_alert": "Cognitive Incongruence Detected. Preliminary assessment: Possible fatigue masking."}`

### 10.4 Running the FastAPI Server

```bash
# Start the central inference engine
python main.py

# Interactive OpenAPI documentation available at:
# http://127.0.0.1:8000/docs
```

---

## 11. Life Support Cockpit HUD Frontend (N-Layer Architecture)

Following the mission's cockpit mockups and aerospace HUD visual design standards, the complete interactive interface was developed with a **decoupled N-layer architecture** (semantic HTML5, CSS3 Cyber-Hologram, interactive SVG, WebGL/Canvas and modular Vanilla JavaScript):

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. PRESENTATION LAYER (UI / DOM & Canvas)                                   │
│    • frontend/index.html: Semantic structure, anatomical SVG and Habitat.   │
│    • frontend/css/hud-theme.css: Space palette (#050811, #00f0ff, #00ff88)  │
│    • frontend/css/animations.css: Laser sweeps, heartbeats (60 FPS)         │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ DOM events / Rendering
┌──────────────────────────────────────▼──────────────────────────────────────┐
│ 2. CONTROLLERS LAYER (Frontend Orchestration)                               │
│    • frontend/js/controllers/hud_controller.js:                             │
│      Coordinates the data flow between the state layer, services and DOM.   │
│      Manages tabs (Biomedical vs Environmental), critical modal, simulation.│
└──────────────────┬──────────────────────────────────────┬───────────────────┘
                   │ Subscribes to changes                │ Consumes APIs
┌──────────────────▼──────────────────┐ ┌─────────────────▼───────────────────┐
│ 3. STATE LAYER (State Manager)      │ │ 4. SERVICES LAYER (Services)        │
│    • state/state_manager.js:        │ │ • services/telemetry_service.js:    │
│      Reactive Observer pattern.     │ │   Async REST calls to FastAPI       │
│      Stores active telemetry,       │ │ • services/ecg_service.js:          │
│      crisis mode and habitat.       │ │   P-Q-R-S-T oscilloscope on Canvas. │
│                                     │ │ • services/hologram_service.js:     │
│                                     │ │   Quantum particles and SVG nodes.  │
│                                     │ │ • services/sound_service.js:        │
│                                     │ │   Procedural Web Audio API audio    │
│                                     │ │   (0 KB weight, purely synthesized).│
└─────────────────────────────────────┘ └─────────────────────────────────────┘
```

### 11.1 Features of the Main Views

1. **View 1: Biomedical & Anatomical Hologram:**
   - **Futuristic 3D Hologram:** Anatomical representation in SVG with a continuous laser sweep, floating quantum particles and interactive organ nodes (Brain, Heart, Lungs, Kidneys, Bone Mass).
   - **60 FPS ECG Oscilloscope:** Continuous $P-Q-R-S-T$ medical waveform trace synchronized in real time with the heart rate.
   - **Biomedical Telemetry Tiles:** Heart rate, $\text{SpO}_2$, Blood pressure, Body temperature and Bone demineralization.

2. **View 2: Environment & Space Habitat (3 Dynamic Habitats):**
   - **Selector of 3 Dedicated Habitats:**
     * `🛰️ SPACECRAFT` (Orion Deep Space Vehicle): Interplanetary transit ($0.00\text{ g}$, $85.0\text{ mSv}$, ECLSS Scrubber, SPE shield).
     * `🔴 MARS BASE` (Geodesic Surface Dome): Habitat on Mars ($0.38\text{ g}$, $42.0\text{ mSv}$, MOXIE bioreactor, regolith shielding).
     * `🛸 SPACE STATION` (ISS / Orbital Gateway): Microgravity orbit ($0.00\text{ g}$, $22.5\text{ mSv}$, CDRA system, Whipple shielding).
   - **Atmospheric Monitors:** $\text{CO}_2$ concentration, Cumulative radiation (mSv), Cabin pressure (kPa), Temperature, Humidity and Solar event.
   - **Kronecker Matrix Display ($3 \times 4$):** Interactive real-time visualization of the coupling between the 3 environmental stressors and the 4 physiological biomarkers computed by Brain 3.

3. **View 3: Wellbeing, Routines & Psychological Assistant (NASA-BHP Protocol / ASTRA System):**
   - **Operational Psychological Assessment:** Interactive protocol of 3 standardized mental health and operational alertness questions (NASA Behavioral Health & Performance).
   - **Multimodal Input (Voice & Text):** Real-time voice dictation with the native Web Speech API, text entry and quick-response chips.
   - **Real-Time ASTRA Vector Metrics:**
     * **Verbal Latency ($\Delta t$ in ms):** Measures the psychomotor reaction time against the nominal baseline (200 ms).
     * **Lexical Density ($D \in [0.1, 1.0]$):** Evaluates lexical richness and penalizes evasive or monosyllabic answers.
     * **Cosine Similarity:** Pure linear algebra in $\mathbb{R}^2$ against the dynamic baseline vector.
   - **Multivariate Physiological Crossover:** Detects cognitive incongruences (e.g. feigning verbal calm with tachycardia $>95\text{ bpm}$, or prolonged latency $>500\text{ ms}$ from hidden fatigue).
   - **4-4-6 Tactical Breathing Guide:** Visual and auditory breathing pacer for immediate relaxation and cortisol reduction.
   - **Aerospace Gamification:** Accumulated experience bar (+25 XP per completed task and report) and crew member levels.

4. **Ultra-Light Procedural Audio System (`SoundService`):**
   - **0 KB of Downloads:** Synthesized purely through the browser's native **Web Audio API** (no heavy MP3/WAV files or network lag).
   - **Sci-Fi Tactile Effects:** Interface clicks, harmonic frequency transitions when switching habitats, alarm pulse in crisis mode and a low-frequency heartbeat.
   - **Mute Control:** Tactical `🔊 AUDIO: ON` / `🔇 AUDIO: MUTE` button in the control bar to toggle sound instantly.

### 11.2 Critical Alert Modal and NASA Countermeasures

Faithfully replicating the cockpit prototype design, when the engine detects out-of-range parameters or severe stress:
- A central modal window emerges with a neon red holographic glow (`#ff2255`).
- It exposes the exact count of detected anomalies.
- It strictly prioritizes a **maximum of 3 immediate countermeasures** (`CX-01` to `CX-15`) drawn from NASA's Decision Matrix so the astronaut is not saturated during a contingency.
- It allows opening the full telemetry and countermeasures report.

### 11.3 Run Instructions

```bash
# 1. Run the central FastAPI server
python main.py

# 2. Open in the browser:
# http://127.0.0.1:8000/dashboard
# (or directly http://127.0.0.1:8000/)

# 3. Interactive Streamlit alternative:
streamlit run dashboard_streamlit.py
```
