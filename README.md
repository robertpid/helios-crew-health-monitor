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

## 4. Estructura del Proyecto

```
nasa-proyecto/
├── helios_simulator/
│   ├── __init__.py                     # Metadatos del paquete
│   ├── config.py                       # Constantes y umbrales NASA-STD-3001
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── enums.py                    # NivelAlerta, PeligroRidge, EstadoConexion
│   │   └── models.py                   # Modelos Pydantic (Entorno, Biometría, Cognición)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── math_noise.py               # Generación gaussiana y fórmulas de decaimiento
│   │   ├── environment_generator.py    # Servicio Cerebro 1 (Cabina y Radiación)
│   │   ├── biometrics_generator.py     # Servicio Cerebro 2 (Fisiología y Fatiga)
│   │   ├── cognition_generator.py      # Servicio Cerebro 4 (ASTRA y Cruces lógicos)
│   │   └── correlation_evaluator.py    # Evaluaciones preliminares y alertas NASA
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   ├── publisher_interface.py      # Contrato abstracto (DIP)
│   │   └── redis_publisher.py          # Implementación Redis con Store-and-Forward
│   └── presentation/
│       ├── __init__.py
│       └── orchestrator.py             # Orquestador del bucle principal
├── tests/
│   ├── __init__.py
│   └── test_helios_simulator.py        # Suite de pruebas unitarias y de integración
├── run_helios.py                       # Script ejecutable principal (Punto de entrada)
├── requirements.txt                    # Dependencias de producción y pruebas
└── README.md                           # Documentación técnica completa
```

---

## 5. Instalación y Puesta en Marcha

### Prerrequisitos
- Python 3.10 o superior (compatible con Python 3.14).
- Servidor Redis local o remoto (opcional durante el arranque; si no está activo, el sistema entra en modo resiliente automáticamente).

### Instalación de Dependencias
```powershell
pip install -r requirements.txt
```

### Ejecución Básica
Para iniciar la transmisión continua cada 2 segundos con destino a Redis (`buzon_telemetria_tierra`):
```powershell
python run_helios.py
```

### Opciones de Línea de Comandos
```powershell
python run_helios.py --help

Opciones principales:
  --redis-host REDIS_HOST       Host de Redis (por defecto: 127.0.0.1)
  --redis-port REDIS_PORT       Puerto de Redis (por defecto: 6379)
  --redis-canal REDIS_CANAL     Canal y cola (por defecto: buzon_telemetria_tierra)
  --dia-mision DIA_MISION       Día de misión espacial (por defecto: 120)
  --intervalo INTERVALO         Intervalo de muestreo en segundos (por defecto: 2.0)
  --max-ciclos MAX_CICLOS       Número de ciclos a ejecutar antes de detenerse
  --simular-demo-crisis         Inyecta de inmediato un escenario crítico con picos multivariados
  --verbose                     Activa trazas de log de depuración (DEBUG)
```

### Demostración de Escenario de Crisis
Para demostrar en vivo cómo el sistema reacciona a una contingencia severa (pico de CO2 $> 3.0$, tormenta solar SPE $+20\text{ mSv}$, déficit de sueño consecutivo, prolongación de latencia verbal y SANS):
```powershell
python run_helios.py --simular-demo-crisis --max-ciclos 5
```

---

## 6. Ejecución de Pruebas Automatizadas

La suite de pruebas valida exhaustivamente los cálculos matemáticos, umbrales de la NASA, tolerancia a fallos del publicador de Redis e inversión de dependencias:

```powershell
pytest -v
```

Resultado de las pruebas:
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
============================= 10 passed in 10 tests =============================
```

---

## 7. Estructura del Payload JSON Inyectado

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

## 8. Referencias Oficiales y Sustento Científico

* **NASA-STD-3001 Vol. 1:** *Crew Health* - Requisito `[V1 4030]`: Dosis de radiación de carrera $< 600\text{ mSv}$, evento SPE $< 250\text{ mSv}$.
* **NASA-STD-3001 Vol. 2:** *Human Factors, Habitability, and Environmental Health* - Requisito `[V2 6004]`: $\text{CO}_2$ promedio de 1 hora $\le 3.0\text{ mmHg}$; Requisito `[V2 6006]`: Presión de cabina entre $95.0$ y $103.0\text{ kPa}$.
* **NASA OCHMO-TB-004:** *Carbon Dioxide Technical Brief* - Umbral asintomático $< 2.5\text{ mmHg}$ promedio de 7 días.
* **NASA HSRB & npj Microgravity (2017):** Pérdida de densidad mineral ósea de $1.0 - 1.5\%$ por mes en ingravidez.
* **The Lancet Neurology (2014):** Barger et al., estudio de sueño en $85$ astronautas ($>4,200$ noches). Déficit crónico de sueño en misiones de larga duración.
* **Eye (2026) / NASA LSAH (N20):** Prevalencia de signos de Síndrome Neuro-ocular (SANS) en el $81\%$ de los astronautas analizados ($52$ de $64$).
