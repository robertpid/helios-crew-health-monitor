# HELIOS Simulator (v2.1.0)
## Productor de Telemetría Sintética de Soporte Vital para Espacio Profundo
### Misión Espacial a Marte (Día 120) · NASA Space Apps 2026

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Pydantic v2](https://img.shields.io/badge/pydantic-v2.10%2B-green.svg)](https://docs.pydantic.dev/)
[![Redis](https://img.shields.io/badge/redis-pub%2Fsub%20%2B%20queue-red.svg)](https://redis.io/)
[![NASA Standards](https://img.shields.io/badge/standards-NASA--STD--3001%20%7C%20RIDGE-orange.svg)](https://www.nasa.gov/hrp/hazards)
[![Code Style](https://img.shields.io/badge/code%20style-PEP%208%20%7C%20Clean%20Code-black.svg)](https://peps.python.org/pep-0008/)

---

## 1. Visión del Sistema y Misión Operativa

`helios_simulator` es un motor de telemetría biomédica y ambiental de borde (**Edge AI**) desarrollado para sistemas de soporte vital en misiones tripuladas de espacio profundo (ej. Tránsito Tierra-Marte, **Sol 120**).

En misiones interplanetarias, el retraso de comunicación con la Tierra (**Peligro D de RIDGE**, de hasta 22 minutos por vía) hace inviable depender de estaciones terrestres para la toma de decisiones inmediata. Este módulo genera periódicamente (cada 2 segundos) un payload enriquecido con validaciones matemáticas, ruidos estocásticos fisiológicos y cruces multivariados entre peligros que se inyecta en el bus local de mensajería **Redis** en el canal y cola `buzon_telemetria_tierra`.

---

## 2. Cumplimiento de Restricciones y Arquitectura N-Capas (N-Tier)

El sistema implementa una estricta separación de responsabilidades dividida en 4 capas desacopladas:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       CAPA DE PRESENTACIÓN (Main / CLI)                     │
│  [run_helios.py] ──> [TelemetriaOrchestrator]                               │
│  Orquesta el bucle de 2 segundos, parseo de flags CLI y manejo de señales.  │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Inyección de Dependencias (DIP)
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                    CAPA DE SERVICIOS (Lógica de Negocio)                    │
│  • GeneradorEntorno (Cerebro 1: CO2, Radiación SPE, Presión)                │
│  • GeneradorBiometria (Cerebro 2: FC, Sueño circadiano, Pérdida ósea HSRB)  │
│  • GeneradorCognicion (Cerebro 4: ASTRA, Latencia verbal, SANS, Estrés)     │
│  • EvaluadorCorrelacionService (Matriz de alertas y estándares NASA)        │
│  • math_noise.py (Modelado gaussiano, distribución normal, DRY)             │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Construye y valida
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                         CAPA DE DOMINIO (Modelos)                           │
│  • EntornoModel · BiometriaModel · CognicionModel                           │
│  • AlertaEvaluacionPreliminar · TelemetriaPayload                           │
│  • Enums: NivelAlerta, PeligroRidge, EstadoConexion                         │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Contrato TelemetryPublisherInterface
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                   CAPA DE INFRAESTRUCTURA (Repository/Publisher)            │
│  • RedisTelemetryPublisher: Conexión persistente, Pub/Sub, Colas FIFO      │
│  • Store-and-Forward: Buffer local tolerante a caídas de red                │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Principios SOLID Aplicados
1. **SRP (Single Responsibility Principle):**
   - Los modelos (`domain/models.py`) únicamente definen esquemas, tipos y validaciones inmutables.
   - Las clases generadoras (`services/`) únicamente computan la física y fisiología aeroespacial.
   - `RedisTelemetryPublisher` (`infrastructure/`) se encarga de la conectividad, serialización y resiliencia de transporte.
   - `TelemetriaOrchestrator` (`presentation/`) coordina el tiempo y las dependencias sin mezclar lógica de red o matemáticas.
2. **DIP (Dependency Inversion Principle):**
   - El orquestador depende exclusivamente de la abstracción `TelemetryPublisherInterface`. La infraestructura concreta de Redis es inyectada en el arranque, facilitando pruebas con mocks y adaptabilidad futura (ej. MQTT, WebSockets o ZeroMQ).
3. **Léxico Médico Estricto:**
   - Cumplimiento de directrices aeroespaciales de telemedicina: se evita cualquier terminología clínica presuntiva. En su lugar, el sistema emplea formalmente **`evaluacion_preliminar`** y **`alerta`**, alineándose con los lineamientos de la NASA.
4. **Clean Code & Resiliencia:**
   - Tipado estático total (`Type Hinting`).
   - Logging estructurado con `logging` (prohibido `print()` de depuración).
   - Patrón **Store-and-Forward**: ante la pérdida del servidor Redis, los mensajes se encolan en un buffer FIFO en memoria y se transmiten automáticamente al restablecerse la conexión.

---

## 3. Reglas de Negocio Aeroespacial (NASA-STD-3001 & RIDGE)

### Simulación del "Día 120"
Para el día 120 de misión a Marte, los parámetros reflejan el desgaste acumulado en microgravedad:

#### Cerebro 1: Entorno de Cabina
* **Dióxido de Carbono (`co2_mmHg`):**
  - Rango nominal: $1.0 - 2.2\text{ mmHg}$.
  - Inyección de picos $> 3.0\text{ mmHg}$ que superan el estándar **NASA-STD-3001 Vol. 2 [V2 6004]** (límite de 1 hora $\le 3\text{ mmHg}$).
  - Monitoreo de umbral de síntomas a partir de $2.3\text{ mmHg}$ y umbral de 7 días de $2.5\text{ mmHg}$ (NASA OCHMO-TB-004).
* **Radiación Acumulada (`radiacion_acumulada_mSv`):**
  - Base inicial al Día 120: $50.0\text{ mSv} + (120 \times 0.35\text{ mSv/día}) \approx 92.0\text{ mSv}$.
  - Tasa diaria: $0.2 - 0.5\text{ mSv/día}$ (datos reales de detectores en ISS / NTRS Simonsen et al., 2025).
  - **1% de probabilidad de Tormenta Solar (SPE):** inyección repentina de $+20\text{ mSv}$ por evento (referenciado contra el límite de evento solar $< 250\text{ mSv}$ y límite de carrera $< 600\text{ mSv}$ según NASA-STD-3001 Vol. 1 [V1 4030]).
* **Presión de Cabina (`presion_cabina_kpa`):**
  - Intervalo nominal regulado entre $95.0\text{ kPa}$ y $103.0\text{ kPa}$ conforme a **NASA-STD-3001 Vol. 2 [V2 6006]**.

#### Cerebro 2: Biometría Fisiológica
* **Ritmo Cardíaco (`ritmo_cardiaco_bpm`):**
  - Línea base de $65 \pm 5\text{ bpm}$, modulada al alza bajo estrés ambiental o hipoxia/hipercapnia.
* **Horas de Sueño y Riesgo de Fatiga (`horas_sueno_ultimo_ciclo`):**
  - Promedio de $6.0\text{ h}$ (estudio *The Lancet Neurology*, 2014; $N=85$ astronautas en ISS).
  - Si el tripulante acumula **3 ciclos consecutivos con $< 6.0\text{ h}$ de descanso**, se activa automáticamente la bandera `alerta_riesgo_fatiga = True`.
* **Pérdida de Masa Ósea (`perdida_osea_pct`):**
  - Modelo de desmineralización: $\text{Pérdida}(\%) = \left(\frac{\text{Día}}{30}\right) \times 1.5\%$.
  - En el **Día 120**, la pérdida calculada es exactamente **$6.0\%$** (respaldado por estudios de cosmonautas en Mir y NASA Human System Risk Board, *npj Microgravity*).

#### Cerebro 4: Psicología y Cognición (ASTRA)
* **Latencia de Voz (`latencia_voz_ms`):**
  - Base nominal: $\sim 200\text{ ms}$.
  - **CRUCE LÓGICO MULTIVARIADO:** Si $\text{CO}_2 > 2.5\text{ mmHg}$ o $\text{horas\_sueño} < 6.0\text{ h}$, la latencia se dispara a un rango entre **$600\text{ ms}$ y $900\text{ ms}$**, simulando letargo y deterioro psicomotor.
* **Densidad Léxica (`densidad_lexica_score`):**
  - Puntuación entre $0.0$ y $1.0$.
  - **INCONGRUENCIA COGNITIVA (Estrés Oculto):** En ocasiones el astronauta intenta disimular el estrés: frecuencia cardíaca elevada ($> 95\text{ bpm}$), pero con densidad léxica sostenida en $\sim 0.80$ ("fingiendo estar bien").
* **SANS Síntoma de Visión (`sans_sintoma_vision`):**
  - Booleano activado bajo alto estrés, hipercapnia o sobrecarga hemodinámica, modelando la prevalencia del **$81\%$** reportada en el programa **LSAH** (Lifetime Surveillance of Astronaut Health) de la NASA debido al desplazamiento de $1000 - 1500\text{ ml}$ de fluidos hacia el cráneo.

---

## 4. Simulador Analítico Multihábitat de 120 Días (4 Entornos Operacionales)

Además del emisor de telemetría reactiva en tiempo real cada 2 segundos, el sistema incorpora el motor analítico `SimuladorMultihabitat120Dias` en [multi_habitat_simulator.py](file:///c:/Users/Home/nasa-proyecto/helios_simulator/services/multi_habitat_simulator.py). Este módulo genera series temporales completas de **120 días** para comparar la evolución de cada signo vital y variable ambiental en los 4 hábitats del vuelo espacial:

```
                                  ┌───────────────────────────┐
                                  │   SIMULADOR MULTIHÁBITAT  │
                                  │   Series de 120 días      │
                                  └─────────────┬─────────────┘
                ┌───────────────────────┬───────┴───────────────┬───────────────────────┐
                ▼                       ▼                       ▼                       ▼
    ┌───────────────────────┐ ┌───────────────────┐ ┌───────────────────────┐ ┌───────────────────┐
    │  ESTACIÓN ESPACIAL    │ │    BASE LUNAR     │ │     NAVE ESPACIAL     │ │   BASE DE MARTE   │
    │  ISS / LEO (0.00g)    │ │ Artemis (0.166g)  │ │ Deep Space (0.00g)    │ │ Superficie (0.38g)│
    │  Retardo: < 1 seg     │ │ Retardo: 1.3 seg  │ │ Retardo: 15 min       │ │ Retardo: 20 min   │
    │  Rad: 0.35 mSv/d      │ │ Rad: 1.35 mSv/d   │ │ Rad: 1.80 mSv/d       │ │ Rad: 0.67 mSv/d   │
    │  P.Ósea: 6.0%         │ │ P.Ósea: 5.0%      │ │ P.Ósea: 6.0%          │ │ P.Ósea: 3.7%      │
    └───────────────────────┘ └───────────────────┘ └───────────────────────┘ └───────────────────┘
```

### Sustento de Datos y Parámetros Comparativos por Hábitat:
1. **Estación Espacial Internacional (ISS / LEO):**
   - **Gravedad:** Microgravedad ($0.0\text{ g}$).
   - **Radiación Diaria:** $0.2 - 0.5\text{ mSv/día}$ (media $0.35\text{ mSv/día}$, Simonsen et al., 2025; RadLab). Protegida por la magnetosfera terrestre; acumula $\sim 56\text{ mSv}$ al Día 120 ($9.4\%$ del límite de carrera).
   - **Retardo de Enlace:** $< 1\text{ segundo}$ (tiempo real con Houston).
   - **Pérdida Ósea:** Tasa máxima de microgravedad $1.5\%$ mensual ($6.0\%$ a los 120 días).
2. **Base Lunar (Artemis Base Camp - Superficie Lunar):**
   - **Gravedad:** $0.166\text{ g}$ ($1/6\text{ g}$).
   - **Radiación Diaria:** $\sim 1.35\text{ mSv/día}$ ($\approx 60\text{ }\mu\text{Sv/h}$ medido en Chang'e 4 por el instrumento LND). Sin magnetosfera protectora; acumula $\sim 268\text{ mSv}$ al Día 120 ($44.7\%$ del presupuesto de carrera) debido a tormentas solares frecuentes sin filtro atmosférico.
   - **Retardo de Enlace:** $1.3\text{ segundos}$ por sentido.
   - **Pérdida Ósea:** Parcialmente atenuada por $1/6\text{ g}$: $\sim 1.25\%$ mensual ($5.0\%$ acumulado a los 120 días).
3. **Nave Espacial de Tránsito (Deep Space Transit a Marte):**
   - **Gravedad:** Microgravedad estricta ($0.0\text{ g}$).
   - **Radiación Diaria:** $\sim 1.80\text{ mSv/día}$ (medición directa del instrumento RAD del rover Curiosity en tránsito a Marte; Hassler et al., *Science* 2013). Acumula más de $300\text{ mSv}$ en 120 días ($50.5\%$ del límite de carrera en solo 4 meses).
   - **Retardo de Enlace:** Progresivo, promediando $15\text{ minutos}$ en tránsito medio (Peligro D de RIDGE).
   - **Pérdida Ósea:** $6.0\%$ acumulado a 120 días.
   - **SANS y Fatiga:** Máxima prevalencia de SANS y $23$ días con alerta de fatiga acumulada por confinamiento severo.
4. **Base de Superficie de Marte (Hábitat Marciano):**
   - **Gravedad:** $0.38\text{ g}$ ($3/8\text{ g}$).
   - **Radiación Diaria:** $\sim 0.67\text{ mSv/día}$ en superficie (Curiosity RAD en Gale Crater; el planeta bloquea el $50\%$ de los rayos cósmicos y la atmósfera provee blindaje leve). Acumula $\sim 125\text{ mSv}$ ($21.0\%$ de carrera).
   - **Retardo de Enlace:** $20+\text{ minutos}$ de retraso por vía.
   - **Duración del Sol:** $24\text{ h } 39\text{ min}$ ($24.65\text{ h}$). Provoca desincronización circadiana en la tripulación.
   - **Pérdida Ósea:** Atenuada significativamente a $\sim 0.93\%$ mensual ($3.7\%$ acumulado a los 120 soles).

### Eficiencia y Procesamiento Vectorizado (Clean Code)
El simulador opera **100% vectorizado con NumPy y Pandas**. No utiliza iteraciones por fila (`iterrows()` o `itertuples()` prohibidos). Genera $480$ observaciones completas y genera los artefactos en menos de 0.1 segundos.

### Ejecución de la Simulación Multihábitat:
```powershell
python run_simulacion_120_dias.py --dias 120 --directorio-salida datos_generados
```
Genera automáticamente:
- `datos_generados/telemetria_120_dias_cuatro_habitats.csv` (104 KB)
- `datos_generados/telemetria_120_dias_cuatro_habitats.parquet` (45 KB)
- `datos_generados/telemetria_120_dias_cuatro_habitats.jsonl` (435 KB)

---

## 5. Estructura del Proyecto

```
nasa-proyecto/
├── helios_simulator/
│   ├── __init__.py                     # Metadatos del paquete
│   ├── config.py                       # Constantes, perfiles multihábitat y umbrales NASA-STD-3001
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── enums.py                    # EntornoMision, NivelAlerta, PeligroRidge, EstadoConexion
│   │   └── models.py                   # Modelos Pydantic (Entorno, Biometría, Cognición)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── math_noise.py               # Generación gaussiana y fórmulas de decaimiento
│   │   ├── environment_generator.py    # Servicio Cerebro 1 (Cabina y Radiación)
│   │   ├── biometrics_generator.py     # Servicio Cerebro 2 (Fisiología y Fatiga)
│   │   ├── cognition_generator.py      # Servicio Cerebro 4 (ASTRA y Cruces lógicos)
│   │   ├── correlation_evaluator.py    # Evaluaciones preliminares y alertas NASA
│   │   └── multi_habitat_simulator.py  # Motor analítico vectorizado 120 días (4 hábitats)
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   ├── publisher_interface.py      # Contrato abstracto (DIP)
│   │   └── redis_publisher.py          # Implementación Redis con Store-and-Forward
│   └── presentation/
│       ├── __init__.py
│       └── orchestrator.py             # Orquestador del bucle principal
├── tests/
│   ├── __init__.py
│   ├── test_helios_simulator.py        # Suite de pruebas unitarias de telemetría reactiva
│   └── test_multi_habitat_120_dias.py  # Suite de pruebas analíticas de 120 días multihábitat
├── datos_generados/                    # Salida de datasets (CSV, Parquet, JSONL)
├── run_helios.py                       # Script ejecutable principal (Punto de entrada reactivo)
├── run_simulacion_120_dias.py          # Script ejecutable para simulación de 120 días
├── requirements.txt                    # Dependencias de producción y pruebas
└── README.md                           # Documentación técnica completa
```

---

## 6. Instalación y Puesta en Marcha

### Prerrequisitos
- Python 3.10 o superior (compatible con Python 3.14).
- Servidor Redis local o remoto (opcional durante el arranque; si no está activo, el sistema entra en modo resiliente automáticamente).

### Instalación de Dependencias
```powershell
pip install -r requirements.txt
```

### Ejecución Básica (Telemetría reactiva cada 2 segundos):
Para iniciar la transmisión continua cada 2 segundos con destino a Redis (`buzon_telemetria_tierra`):
```powershell
python run_helios.py
```

### Ejecución de Simulación de 120 Días (4 Hábitats):
Para generar el dataset multivariado completo de 120 días para Estación Espacial, Base Lunar, Nave y Base de Marte:
```powershell
python run_simulacion_120_dias.py --dias 120 --directorio-salida datos_generados
```

---

## 7. Ejecución de Pruebas Automatizadas

La suite de pruebas valida exhaustivamente los cálculos matemáticos, umbrales de la NASA, tolerancia a fallos del publicador de Redis, inversión de dependencias y las series temporales de 120 días:

```powershell
pytest -v
```

Resultado de las 17 pruebas:
```
tests/test_helios_simulator.py::test_calcular_perdida_osea_dia_120 PASSED
tests/test_helios_simulator.py::test_ruido_gaussiano_y_acotamiento PASSED
tests/test_helios_simulator.py::test_generador_entorno_pico_co2_nasa_v2_6004 PASSED
tests/test_helios_simulator.py::test_generador_entorno_tormenta_solar PASSED
tests/test_helios_simulator.py::test_generador_biometria_alerta_fatiga_3_ciclos PASSED
tests/test_helios_simulator.py::test_generador_cognicion_cruce_latencia_voz PASSED
tests/test_helios_simulator.py::test_generador_cognicion_incongruencia_estres_oculto PASSED
tests/test_helios_simulator.py::test_evaluador_correlacion_alertas_nasa PASSED
tests/test_helios_simulator.py::test_redis_publisher_buffer_tolerancia_fallos PASSED
tests/test_helios_simulator.py::test_orquestador_con_inyeccion_dependencias PASSED
tests/test_multi_habitat_120_dias.py::test_generacion_120_dias_un_habitat PASSED
tests/test_multi_habitat_120_dias.py::test_generacion_consolidada_cuatro_habitats PASSED
tests/test_multi_habitat_120_dias.py::test_perdida_osea_ponderada_por_gravedad PASSED
tests/test_multi_habitat_120_dias.py::test_gradiente_radiacion_entre_habitats PASSED
tests/test_multi_habitat_120_dias.py::test_cruce_latencia_verbal_vectorizado PASSED
tests/test_multi_habitat_120_dias.py::test_incongruencia_estres_oculto PASSED
tests/test_multi_habitat_120_dias.py::test_exportacion_dataset PASSED
============================= 17 passed in 17 tests =============================
```

---

## 8. Estructura del Payload JSON Inyectado

Ejemplo de payload transmitido a Redis en cada ciclo de 2 segundos:

```json
{
  "timestamp": "2026-11-14T15:37:32.503912Z",
  "id_mision": "ARES-VI-MARS-EXPEDITION",
  "dia_mision": 120,
  "astronauta_id": "ASTRO-HELIOS-01",
  "entorno": {
    "co2_mmHg": 3.78,
    "radiacion_acumulada_mSv": 92.45,
    "radiacion_tasa_diaria_mSv": 0.362,
    "presion_cabina_kpa": 101.15,
    "temperatura_cabina_c": 21.42,
    "evento_solar_activo": false
  },
  "biometria": {
    "ritmo_cardiaco_bpm": 83.2,
    "horas_sueno_ultimo_ciclo": 4.9,
    "ciclos_sueno_insuficiente_consecutivos": 3,
    "alerta_riesgo_fatiga": true,
    "perdida_osea_pct": 6.0,
    "presion_sistolica_mmHg": 132.4,
    "presion_diastolica_mmHg": 84.8,
    "spo2_pct": 98.1
  },
  "cognicion": {
    "latencia_voz_ms": 702.5,
    "densidad_lexica_score": 0.44,
    "incongruencia_estres_oculto": false,
    "sans_sintoma_vision": true
  },
  "evaluaciones_preliminares": [
    {
      "codigo": "ALERTA-CO2-MAX-V2-6004",
      "nivel": "CRITICA",
      "peligro_ridge": "E - Ambientes hostiles y cerrados",
      "estandar_referencia": "NASA-STD-3001 Vol.2 [V2 6004]",
      "descripcion": "Concentración de CO2 (3.78 mmHg) sobrepasa el límite normativo de 3.0 mmHg. Riesgo inminente de cefalea y letargo operativo.",
      "cruce_multivariado": false
    },
    {
      "codigo": "ALERTA-FATIGA-CRONICA-HSRB",
      "nivel": "ADVERTENCIA",
      "peligro_ridge": "I - Aislamiento y confinamiento",
      "estandar_referencia": "NASA HSRB & The Lancet Neurology (2014)",
      "descripcion": "Riesgo de fatiga severa activado: 3 ciclos consecutivos con sueño menor a 6.0 horas (último: 4.9h).",
      "cruce_multivariado": false
    },
    {
      "codigo": "ALERTA-CRUCE-LATENCIA-COGNITIVA",
      "nivel": "ADVERTENCIA",
      "peligro_ridge": "D - Distancia de la Tierra",
      "estandar_referencia": "NASA OCHMO-TB-004 & Protocolo ASTRA",
      "descripcion": "Enlentecimiento cognitivo detectado: latencia verbal en 702.5 ms (normal: ~200 ms). Disparado por cruce sinérgico de CO2 3.78 mmHg y sueño deficitario 4.9h.",
      "cruce_multivariado": true
    },
    {
      "codigo": "ALERTA-SANS-SINTOMA-VISION",
      "nivel": "ADVERTENCIA",
      "peligro_ridge": "G - Campos de gravedad alterados",
      "estandar_referencia": "NASA Lifetime Surveillance of Astronaut Health (LSAH 2026)",
      "descripcion": "Sintomatología neuro-ocular de SANS reportada (visión borrosa / cefalea). Correlacionada con desplazamiento cefálico de fluidos (1000-1500 ml) y estrés sistémico.",
      "cruce_multivariado": true
    }
  ],
  "porcentaje_presupuesto_radiacion_carrera": 15.41,
  "metadatos_sistema": {
    "modulo_productor": "helios_simulator",
    "arquitectura": "Edge AI N-Capas",
    "frecuencia_muestreo_hz": 0.5,
    "intervalo_segundos": 2.0,
    "ciclo_muestra_id": 2,
    "canal_redis": "buzon_telemetria_tierra",
    "enlace_estado": "DESCONECTADO"
  }
}
```

---

## 9. Referencias Oficiales y Sustento Científico

* **NASA-STD-3001 Vol. 1:** *Crew Health* - Requisito `[V1 4030]`: Dosis de radiación de carrera $< 600\text{ mSv}$, evento SPE $< 250\text{ mSv}$.
* **NASA-STD-3001 Vol. 2:** *Human Factors, Habitability, and Environmental Health* - Requisito `[V2 6004]`: $\text{CO}_2$ promedio de 1 hora $\le 3.0\text{ mmHg}$; Requisito `[V2 6006]`: Presión de cabina entre $95.0$ y $103.0\text{ kPa}$.
* **NASA OCHMO-TB-004:** *Carbon Dioxide Technical Brief* - Umbral asintomático $< 2.5\text{ mmHg}$ promedio de 7 días.
* **NASA HSRB & npj Microgravity (2017):** Pérdida de densidad mineral ósea de $1.0 - 1.5\%$ por mes en ingravidez.
* **The Lancet Neurology (2014):** Barger et al., estudio de sueño en $85$ astronautas ($>4,200$ noches). Déficit crónico de sueño en misiones de larga duración.
* **Eye (2026) / NASA LSAH (N20):** Prevalencia de signos de Síndrome Neuro-ocular (SANS) en el $81\%$ de los astronautas analizados ($52$ de $64$).

---

## 10. H.E.L.I.O.S. Motor de Inferencia Central (`main.py`)

### 10.1 Arquitectura Edge AI Ligera (Sin PyTorch ni Graph Databases)

El módulo central de inferencia (`main.py`) ejecuta un runtime ultra-ligero desarrollado específicamente para computadoras de abordo aeroespaciales tolerantes a radiación (SBCs con recursos limitados de RAM y sin GPU acelerada).

```
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │                       REDIS QUEUE / INGESTION ASÍNCRONA                     │
 │  RPOP 'buzon_telemetria_tierra' (redis.asyncio)                             │
 └──────────────────────────────────────┬──────────────────────────────────────┘
                                        │ Payload JSON deserializado
 ┌──────────────────────────────────────▼──────────────────────────────────────┐
 │                     INFERENCE ENGINE (Orquestador Central)                  │
 │                                                                             │
 │  ┌─────────────────────────┐             ┌───────────────────────────────┐  │
 │  │ Cerebro 1: Motor Amb.   │             │ Cerebro 2: Motor Biométrico   │  │
 │  │ Reglas Heurísticas R^3  │             │ Desviación Línea Base R^4     │  │
 │  │ [CO2, Radiación, Pres.] │             │ [Pulso, Sueño, Hueso, SANS]   │  │
 │  └────────────┬────────────┘             └───────────────┬───────────────┘  │
 │               │                                          │                  │
 │               └──────────────────┬───────────────────────┘                  │
 │                                  │                                          │
 │               ┌──────────────────▼───────────────────────┐                  │
 │               │ Cerebro 3: Grafo y Fusión Espacial       │                  │
 │               │ Producto Tensorial de Kronecker (np.kron)│                  │
 │               │ V_kron = v_amb ⊗ v_bio in R^12           │                  │
 │               │ P = V_kron ⊙ W  =>  k* = argmax(P)       │                  │
 │               └──────────────────┬───────────────────────┘                  │
 │                                  │                                          │
 │               ┌──────────────────▼───────────────────────┐                  │
 │               │ Cerebro 4: ASTRA Cognitivo Vectorial     │                  │
 │               │ Similitud Coseno (np.dot / normas)       │                  │
 │               │ Detección de Incongruencia Cognitiva     │                  │
 │               └──────────────────┬───────────────────────┘                  │
 │                                  │                                          │
 └──────────────────────────────────┼──────────────────────────────────────────┘
                                    │
 ┌──────────────────────────────────▼──────────────────────────────────────────┐
 │                         FASTAPI REST API (Puerto 8000)                      │
 │  • GET  /api/v1/fusion/resultado (Consolidado de los 4 cerebros)            │
 │  • GET  /api/v1/alertas          (Evaluaciones preliminares activas)        │
 │  • POST /api/v1/inferir          (Evaluación directa en < 2 ms)             │
 └─────────────────────────────────────────────────────────────────────────────┘
```

### 10.2 Modelado de Grafo de Decisiones mediante Producto Tensorial de Kronecker

En lugar de requerir motores de grafos basados en disco como Neo4j, el acoplamiento de interacción entre $3$ estresores ambientales y $4$ biomarcadores fisiológicos se formula algebraicamente:

$$\mathbf{V}_{\text{kron}} = \mathbf{v}_{\text{amb}} \otimes \mathbf{v}_{\text{bio}} \in \mathbb{R}^{12}$$

Donde cada posición $k = 4i + j$ representa una arista sinérgica de decisión ponderada por el vector clínico $\mathbf{W} \in \mathbb{R}^{12}$:

$$\mathbf{P} = \mathbf{V}_{\text{kron}} \odot \mathbf{W}$$
$$k^* = \arg\max(\mathbf{P})$$

Si $P_{k^*} \ge \text{umbral}$ (ej. $6.5$), el sistema dispara la bandera de **estrés fisiológico severo** e identifica la arista dominante en tiempo $\mathcal{O}(1)$.

### 10.3 Detección de Incongruencia Cognitiva (Cerebro 4 - ASTRA)

ASTRA construye el vector cognitivo normalizado $\mathbf{C}_{\text{norm}} = [\text{latencia} / 200.0, \text{densidad} / 1.0]$ y calcula la **Similitud Coseno** respecto a la línea base $\mathbf{B}_{\text{norm}} = [1.0, 1.0]$:

$$\cos(\theta) = \frac{\mathbf{C}_{\text{norm}} \cdot \mathbf{B}_{\text{norm}}}{\|\mathbf{C}_{\text{norm}}\|_2 \|\mathbf{B}_{\text{norm}}\|_2}$$

* **Regla de Incongruencia:** Si la similitud cae abruptamente (latencia en 600–900 ms) pero las métricas físicas están nominales, o si el cuerpo está en taquicardia ($>95\text{ bpm}$) pero el astronauta formaliza su dicción ($\ge 0.75$), Cerebro 4 dictamina:
  `{"alerta_astra": "Incongruencia Cognitiva Detectada. Evaluación preliminar: Posible ocultamiento de fatiga."}`

### 10.4 Ejecución del Servidor FastAPI

```bash
# Iniciar el motor de inferencia central
python main.py

# Documentación OpenAPI interactiva disponible en:
# http://127.0.0.1:8000/docs
```

---

## 11. Frontend Cockpit HUD de Soporte Vital (Arquitectura N-Capas)

Siguiendo los bocetos de cabina de la misión y los estándares de diseño visual HUD aeroespacial, se desarrolló la interfaz interactiva completa con **arquitectura desacoplada en N-Capas** (HTML5 Semántico, CSS3 Cyber-Hologram, SVG interactivo, WebGL/Canvas y Vanilla JavaScript modular):

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. CAPA DE PRESENTACIÓN (UI / DOM & Canvas)                                 │
│    • frontend/index.html: Estructura semántica, SVG anatómico y Hábitat.   │
│    • frontend/css/hud-theme.css: Paleta espacial (#050811, #00f0ff, #00ff88)│
│    • frontend/css/animations.css: Barridos láser, pulsos cardíacos (60 FPS) │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Eventos DOM / Rendering
┌──────────────────────────────────────▼──────────────────────────────────────┐
│ 2. CAPA DE CONTROLADORES (Orquestación Frontend)                            │
│    • frontend/js/controllers/hud_controller.js:                              │
│      Coordina el flujo de datos entre la capa de estado, servicios y DOM.   │
│      Gestiona tabs (Biomédica vs Ambiental), modal crítico y simulación.    │
└──────────────────┬──────────────────────────────────────┬───────────────────┘
                   │ Suscribe cambios                     │ Consume APIs
┌──────────────────▼──────────────────┐ ┌─────────────────▼───────────────────┐
│ 3. CAPA DE ESTADO (State Manager)   │ │ 4. CAPA DE SERVICIOS (Services)     │
│    • state/state_manager.js:        │ │ • services/telemetry_service.js:    │
│      Patrón Observer reactivo.      │ │   Llamadas REST asíncronas a FastAPI│
│      Almacena telemetría activa,    │ │ • services/ecg_service.js:          │
│      modo de crisis y hábitat.      │ │   Osciloscopio P-Q-R-S-T en Canvas. │
│                                     │ │ • services/hologram_service.js:     │
│                                     │ │   Partículas cuánticas y SVG nodes. │
│                                     │ │ • services/sound_service.js:        │
│                                     │ │   Audio procedural Web Audio API    │
│                                     │ │   (0 KB peso, sintetizado puro).    │
└─────────────────────────────────────┘ └─────────────────────────────────────┘
```

### 11.1 Características de las Ventanas Principales

1. **Ventana 1: Biomédica & Holograma Anatómico:**
   - **Holograma 3D Futurista:** Representación anatómica en SVG con barrido láser continuo, partículas cuánticas flotantes y nodos interactivos de órganos (Cerebro, Corazón, Pulmones, Riñones, Masa Ósea).
   - **Osciloscopio ECG a 60 FPS:** Trazo electrocardiográfico continuo de onda médica $P-Q-R-S-T$ sincronizado en tiempo real con la frecuencia cardíaca.
   - **Tiles de Telemetría Biomédica:** Frecuencia cardíaca, $\text{SpO}_2$, Presión arterial, Temperatura corporal y Desmineralización ósea.

2. **Ventana 2: Ambiente & Hábitat Espacial (3 Hábitats Dinámicos):**
   - **Selector de 3 Hábitats Dedicados:**
     * `🛰️ NAVE ESPACIAL` (Orion Deep Space Vehicle): Tránsito interplanetario ($0.00\text{ g}$, $85.0\text{ mSv}$, ECLSS Scrubber, escudo SPE).
     * `🔴 BASE MARCIANA` (Domo Geodésico de Superficie): Hábitat en Marte ($0.38\text{ g}$, $42.0\text{ mSv}$, Biorreactor MOXIE, blindaje de regolito).
     * `🛸 ESTACIÓN ESPACIAL` (ISS / Orbital Gateway): Órbita microgravitatoria ($0.00\text{ g}$, $22.5\text{ mSv}$, sistema CDRA, blindaje Whipple).
   - **Monitores Atmosféricos:** Concentración de $\text{CO}_2$, Radiación acumulada (mSv), Presión de cabina (kPa), Temperatura, Humedad y Evento solar.
   - **Heatmap de la Matriz de Kronecker ($3 \times 4$):** Visualización interactiva en tiempo real del acoplamiento entre los 3 estresores ambientales y los 4 biomarcadores fisiológicos calculados por el Cerebro 3.

3. **Ventana 3: Bienestar, Rutinas & Asistente Psicológico (Protocolo NASA-BHP / Sistema ASTRA):**
   - **Evaluación Psicológica Operacional:** Protocolo interactivo de 3 preguntas estandarizadas de salud mental y alerta operacional (NASA Behavioral Health & Performance).
   - **Entrada Multimodal (Voz & Texto):** Dictado por voz en tiempo real con Web Speech API nativa, entrada de texto y chips de respuesta rápida.
   - **Métricas Vectoriales ASTRA en Tiempo Real:**
     * **Latencia Verbal ($\Delta t$ en ms):** Mide el tiempo de reacción psicomotora frente a la línea base nominal (200 ms).
     * **Densidad Léxica ($D \in [0.1, 1.0]$):** Evalúa la riqueza léxica y penaliza respuestas evasivas o monosilábicas.
     * **Similitud Coseno:** Álgebra lineal pura en $\mathbb{R}^2$ contra el vector de línea base dinámica.
   - **Cruce Fisiológico Multivariado:** Detecta incongruencias cognitivas (ej. fingir calma verbal con taquicardia $>95\text{ bpm}$ o latencia prolongada $>500\text{ ms}$ por fatiga oculta).
   - **Guía de Respiración Táctica 4-4-6:** Marcapasos respiratorio visual y auditivo para relajación inmediata y reducción de cortisol.
   - **Gamificación Aeroespacial:** Barra de experiencia acumulada (+25 EXP por tarea y reporte completado) y niveles de tripulante.

4. **Sistema de Audio Procedural Ultra-Ligero (`SoundService`):**
   - **0 KB de Descargas:** Sintetizado puramente mediante la **Web Audio API** nativa del navegador (sin archivos MP3/WAV pesados ni lag de red).
   - **Efectos Táctiles Sci-Fi:** Clicks de interfaz, transiciones de frecuencia armónica al cambiar de hábitat, pulso de alarma en modo crisis y latido cardíaco de baja frecuencia.
   - **Control de Silenciado:** Botón táctico `🔊 AUDIO: ACTIVO` / `🔇 AUDIO: MUTE` en la barra de control para alternar el sonido al instante.

### 11.2 Modal de Alerta Crítica y Contramedidas de la NASA

Replicando fielmente el diseño del prototipo de cabina, cuando el motor detecta parámetros fuera de rango o estrés severo:
- Emerge una ventana modal central con brillo holográfico rojo neón (`#ff2255`).
- Expone el conteo exacto de anomalías detectadas.
- Prioriza estrictamente un **máximo de 3 contramedidas inmediatas** (`CX-01` a `CX-15`) extraídas de la Matriz de Decisiones de la NASA para no saturar al astronauta en contingencia.
- Permite abrir el reporte completo de telemetría y contramedidas.

### 11.3 Instrucciones de Ejecución

```bash
# 1. Ejecutar el servidor central FastAPI
python main.py

# 2. Abrir en el navegador:
# http://127.0.0.1:8000/dashboard
# (o directamente http://127.0.0.1:8000/)

# 3. Alternativa Streamlit interactiva:
streamlit run dashboard_streamlit.py
```


