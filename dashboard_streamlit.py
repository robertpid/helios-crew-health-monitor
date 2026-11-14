"""
H.E.L.I.O.S. - Streamlit Cockpit Dashboard (NASA Space Apps 2026).
Interfaz visual interactiva con monitor de cuerpo holográfico y hábitat espacial.
"""

import json
import time
import requests
import streamlit as st
import pandas as pd
import numpy as np

# Configuración de página de Streamlit
st.set_page_config(
    page_title="H.E.L.I.O.S. - Crew Health & Habitat Monitor",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilos CSS Aeroespaciales Futuristas (Sci-Fi Dark Theme)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600;900&family=Rajdhani:wght@600;700&family=Share+Tech+Mono&display=swap');

    /* Fondo general */
    .stApp {
        background-color: #060a14;
        color: #e2e8f0;
        font-family: 'Rajdhani', sans-serif;
    }

    /* Títulos HUD */
    h1, h2, h3 {
        font-family: 'Orbitron', monospace !important;
        color: #00f0ff !important;
        letter-spacing: 2px;
        text-shadow: 0 0 10px rgba(0, 240, 255, 0.4);
    }

    /* Métricas */
    [data-testid="stMetricValue"] {
        font-family: 'Share Tech Mono', monospace !important;
        color: #00f0ff !important;
        font-size: 32px !important;
    }
    [data-testid="stMetricLabel"] {
        font-family: 'Orbitron', sans-serif !important;
        font-size: 11px !important;
        color: #798da3 !important;
        letter-spacing: 1px;
    }

    /* Cajas y Paneles */
    .hud-box {
        background: #0d1527;
        border: 1px solid rgba(0, 240, 255, 0.25);
        border-radius: 8px;
        padding: 18px;
        margin-bottom: 16px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
    }

    /* Modal Alerta Crítica Réplica Boceto */
    .critical-alert-box {
        background: #120a14;
        border: 2px solid #ff2255;
        box-shadow: 0 0 30px rgba(255, 34, 85, 0.5);
        border-radius: 10px;
        padding: 24px;
        margin-bottom: 24px;
        text-align: center;
    }
    .critical-title {
        font-family: 'Orbitron', monospace;
        color: #ff2255;
        font-size: 24px;
        font-weight: 900;
        letter-spacing: 2px;
        text-shadow: 0 0 15px #ff2255;
        margin-bottom: 6px;
    }
    .critical-sub {
        font-family: 'Share Tech Mono', monospace;
        color: #cbd5e1;
        margin-bottom: 16px;
        font-size: 14px;
    }
    .critical-item {
        font-family: 'Share Tech Mono', monospace;
        color: #ffd2dc;
        font-size: 14px;
        line-height: 1.8;
        text-align: left;
    }
    .critical-item strong {
        color: #ff2255;
    }
</style>
""", unsafe_allow_html=True)

# Barra lateral (Sidebar de Control)
with st.sidebar:
    st.markdown("### 🛰️ CONTROL DE MISIÓN")
    habitat_seleccionado = st.selectbox(
        "Hábitat Operacional:",
        [
            "Nave de Tránsito a Marte (Deep Space)",
            "Estación Espacial Internacional (ISS)",
            "Base Marciana (Superficie 0.38g)",
            "Base Lunar Artemis (0.16g)",
        ],
        index=0
    )

    st.markdown("---")
    st.markdown("### ⚡ SIMULADOR DE DEMO")
    modo_crisis = st.toggle("Activar Escenario de Crisis (Día 95)", value=False)
    
    st.markdown("---")
    st.markdown("### 📡 ENLACE TERRESTRE (DSN)")
    if "Marte" in habitat_seleccionado:
        st.info("Retraso de señal: **14 a 22 minutos**.\n\n*Modo autónomo Edge AI activo (Store-and-Forward).*")
    elif "Lunar" in habitat_seleccionado:
        st.info("Retraso de señal: **1.3 segundos**.")
    else:
        st.success("Retraso de señal: **< 0.5 segundos (LEO)**.")

    st.markdown("---")
    st.caption("NASA Space Apps 2026 · H.E.L.I.O.S. v2.1")

# Header Principal
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown("# H.E.L.I.O.S. CREW HEALTH MONITOR")
    st.markdown("**SISTEMA DE SOPORTE VITAL DE ESPACIO PROFUNDO · SOL 120**")
with col_h2:
    if modo_crisis:
        st.markdown("""
        <div style="background:rgba(255,34,85,0.2); border:1px solid #ff2255; padding:10px; border-radius:6px; text-align:center;">
            <span style="font-family:'Orbitron'; font-size:16px; color:#ff2255; font-weight:bold;">ASTRONAUTA A01: CRÍTICO</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background:rgba(0,255,136,0.2); border:1px solid #00ff88; padding:10px; border-radius:6px; text-align:center;">
            <span style="font-family:'Orbitron'; font-size:16px; color:#00ff88; font-weight:bold;">ASTRONAUTA A01: ESTABLE</span>
        </div>
        """, unsafe_allow_html=True)

# MODAL / BANNER DE ALERTA CRÍTICA (RÉPLICA DEL BOCETO DEL USUARIO)
if modo_crisis:
    st.markdown("""
    <div class="critical-alert-box">
        <div class="critical-title">! CRITICAL ALERT</div>
        <div class="critical-sub">4 parameter(s) detected out of range</div>
        <div style="background:rgba(0,0,0,0.5); padding:16px 20px; border-radius:6px; margin-bottom:16px;">
            <div class="critical-item"><strong>[CRITICAL]</strong> HEART RATE 132 bpm – check sensor and rest</div>
            <div class="critical-item"><strong>[CRITICAL]</strong> SpO₂ 88 % – check sensor and oxygen</div>
            <div class="critical-item"><strong>[CRITICAL]</strong> CO₂ 3.8 mmHg (3200 ppm) – increase ventilation</div>
            <div class="critical-item"><strong>[CRITICAL]</strong> TEMPERATURE 38.4 °C – thermal control</div>
        </div>
        <div style="text-align:left; background:rgba(0,240,255,0.06); border:1px solid #00f0ff; padding:14px; border-radius:6px; font-family:'Share Tech Mono';">
            <strong style="color:#00f0ff; font-family:'Orbitron'; font-size:11px;">ACCIONES PRIORITARIAS INMEDIATAS (MÁXIMO 3):</strong><br>
            1. Colocación de mascarilla de O₂ y reposo absoluto en estación de descanso.<br>
            2. Elevar ciclo forzado de remoción de CO₂ en módulo de cabina.<br>
            3. Registro en búfer local y alerta de prioridad médica hacia Tierra.
        </div>
    </div>
    """, unsafe_allow_html=True)

# TABS PRINCIPALES (LAS 2 VENTANAS SOLICITADAS + MATRIZ DE DECISIONES)
tab1, tab2, tab3 = st.tabs([
    "🩺 VENTANA 1: BIOMÉDICA & HOLOGRAMA HUMANO",
    "🚀 VENTANA 2: AMBIENTE DE CABINA & HÁBITAT",
    "📋 VENTANA 3: MATRIZ DE DECISIONES (15 CRUCES)",
])

# ==============================================================================
# TAB 1: VENTANA BIOMÉDICA & HOLOGRAMA CORPORAL
# ==============================================================================
with tab1:
    col_holo, col_vitals = st.columns([1.1, 1])

    with col_holo:
        st.markdown("### 🧬 RESUMEN ANATÓMICO HOLOGRAMA")
        st.caption("Bio-Monitor Astroskin (CSA) · Escaneo 3D continuo de tripulante")

        # Representación visual estilizada del holograma humano
        st.markdown("""
        <div style="display:flex; justify-content:center; align-items:center; background:radial-gradient(circle at center, rgba(0,240,255,0.08) 0%, transparent 70%); border:1px dashed rgba(0,240,255,0.3); border-radius:8px; padding:20px; min-height:480px; position:relative;">
            <svg width="280" height="420" viewBox="0 0 280 420">
                <!-- Silueta Holográfica -->
                <circle cx="140" cy="50" r="28" fill="rgba(0,240,255,0.15)" stroke="#00f0ff" stroke-width="2"></circle>
                <line x1="140" y1="78" x2="140" y2="190" stroke="#00f0ff" stroke-width="2" stroke-dasharray="2 2"></line>
                <!-- Clavícula y Brazos -->
                <line x1="90" y1="100" x2="190" y2="100" stroke="#00f0ff" stroke-width="2"></line>
                <line x1="90" y1="100" x2="55" y2="180" stroke="#00f0ff" stroke-width="2"></line>
                <line x1="55" y1="180" x2="35" y2="250" stroke="#00f0ff" stroke-width="2"></line>
                <line x1="190" y1="100" x2="225" y2="180" stroke="#00f0ff" stroke-width="2"></line>
                <line x1="225" y1="180" x2="245" y2="250" stroke="#00f0ff" stroke-width="2"></line>
                <!-- Pelvis y Piernas -->
                <path d="M110 190 L170 190 L160 220 L120 220 Z" fill="rgba(0,240,255,0.1)" stroke="#00f0ff" stroke-width="2"></path>
                <line x1="120" y1="220" x2="110" y2="310" stroke="#00f0ff" stroke-width="3"></line>
                <line x1="110" y1="310" x2="105" y2="395" stroke="#00f0ff" stroke-width="2.5"></line>
                <line x1="160" y1="220" x2="170" y2="310" stroke="#00f0ff" stroke-width="3"></line>
                <line x1="170" y1="310" x2="175" y2="395" stroke="#00f0ff" stroke-width="2.5"></line>
                
                <!-- Nodos Vitales Pulsantes -->
                <!-- Cerebro -->
                <circle cx="140" cy="50" r="7" fill="#00f0ff" stroke="#fff" stroke-width="1.5"></circle>
                <!-- Corazón -->
                <circle cx="140" cy="125" r="9" fill="#ff2255" stroke="#fff" stroke-width="2"></circle>
                <!-- Pulmones -->
                <circle cx="120" cy="115" r="5" fill="#00ff88"></circle>
                <circle cx="160" cy="115" r="5" fill="#00ff88"></circle>
                <!-- Huesos (Fémur) -->
                <circle cx="110" cy="310" r="6" fill="#ffaa00"></circle>
                <circle cx="170" cy="310" r="6" fill="#ffaa00"></circle>

                <!-- Callout Leader Lines -->
                <polyline points="140,50 80,30 30,30" fill="none" stroke="#00f0ff" stroke-width="1.5"></polyline>
                <polyline points="140,125 70,125 20,125" fill="none" stroke="#ff2255" stroke-width="1.5"></polyline>
                <polyline points="160,115 210,105 250,105" fill="none" stroke="#00ff88" stroke-width="1.5"></polyline>
                <polyline points="170,310 215,330 255,330" fill="none" stroke="#ffaa00" stroke-width="1.5"></polyline>
            </svg>
        </div>
        """, unsafe_allow_html=True)

        col_c1, col_c2, col_c3 = st.columns(3)
        col_c1.info("**CEREBRO (ASTRA)**\n\nLatencia: " + ("850 ms" if modo_crisis else "210 ms"))
        col_c2.error("**CORAZÓN**\n\nPulso: " + ("132 lpm" if modo_crisis else "76 lpm"))
        col_c3.warning("**ESCUDO ÓSEO**\n\nPérdida: -1.8%\nARED: 80%")

    with col_vitals:
        st.markdown("### 📊 INDICADORES EN TIEMPO REAL")
        
        m1, m2 = st.columns(2)
        m1.metric("FRECUENCIA CARDÍACA", "132 lpm" if modo_crisis else "76 lpm", delta="+56 lpm" if modo_crisis else "0 lpm", delta_color="inverse")
        m2.metric("SATURACIÓN SpO₂", "88 %" if modo_crisis else "98 %", delta="-10 %" if modo_crisis else "0 %", delta_color="normal")

        m3, m4 = st.columns(2)
        m3.metric("PRESIÓN ARTERIAL", "145/95 mmHg" if modo_crisis else "118/76 mmHg")
        m4.metric("TEMPERATURA CORPORAL", "38.4 °C" if modo_crisis else "36.6 °C", delta="+1.8 °C" if modo_crisis else "0.0 °C", delta_color="inverse")

        m5, m6 = st.columns(2)
        m5.metric("VARIABILIDAD CARDÍACA (HRV)", "18 ms (Baja)" if modo_crisis else "42 ms (Óptima)")
        m6.metric("DESMINERALIZACIÓN ÓSEA", "-1.8 %", delta="Modelo HSRB Sol 120")

        # Gráfica ilustrativa de Electrocardiograma (ECG)
        st.markdown("#### ⚡ ELECTROCARDIOGRAMA ILUSTRATIVO (DERIVACIÓN II)")
        tiempo = np.linspace(0, 4 * np.pi, 200)
        ecg_onda = np.sin(tiempo * (2.2 if modo_crisis else 1.2)) + 0.15 * np.random.randn(200)
        # Inyectar pico QRS
        ecg_onda[::25] += 2.8 if modo_crisis else 2.0
        st.line_chart(pd.DataFrame({"ECG (mV)": ecg_onda}), height=140)

# ==============================================================================
# TAB 2: VENTANA AMBIENTE & HÁBITAT ESPACIAL
# ==============================================================================
with tab2:
    col_env1, col_env2 = st.columns([1, 1])

    with col_env1:
        st.markdown("### 🌌 MONITOREO DEL HÁBITAT & CLIMA ESPACIAL")
        st.caption("ECLSS / Dosimetría RAD / Control Térmico y Presurización")

        st.markdown(f"""
        <div style="background:#0a1224; border:1px solid #00f0ff; border-radius:8px; padding:20px; text-align:center;">
            <h4 style="color:#00f0ff; margin-bottom:10px;">HÁBITAT: {habitat_seleccionado.upper()}</h4>
            <p style="color:#cbd5e1; font-family:'Share Tech Mono';">
                • Estado de Presurización: <strong>ESTABLE (95 - 103 kPa)</strong><br>
                • Sistema de Convección Forzada: <strong>ACTIVO</strong><br>
                • Blindaje Radiológico: <strong>MONITOREADO POR RAD</strong>
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("#### 🔬 MATRIZ DE CRUCE SINÉRGICO DE KRONECKER (R^12)")
        aristas = [
            "CO2xPulso", "CO2xSueño", "CO2xHueso", "CO2xSANS",
            "RadxPulso", "RadxSueño", "RadxHueso", "RadxSANS",
            "PresxPulso", "PresxSueño", "PresxHueso", "PresxSANS"
        ]
        pesos = [0.0] * 12
        if modo_crisis:
            pesos[3] = 9.2  # CO2 x SANS
            pesos[0] = 7.5  # CO2 x Pulso
            st.error("Arista Crítica Activada: **CO2_CON_HIPERTENSION_INTRACRANEAL_SANS (Severidad: 9.2/10)**")
        else:
            st.success("Grafo Matricial: **Sin sinergias adversas activadas (Peligro: 0.0/10)**")

        df_kronecker = pd.DataFrame({
            "Arista de Interacción": aristas,
            "Severidad Ponderada": pesos
        })
        st.bar_chart(df_kronecker.set_index("Arista de Interacción"), height=220)

    with col_env2:
        st.markdown("### 🎛️ SENSORES AMBIENTALES DE CABINA")

        e1, e2 = st.columns(2)
        e1.metric("CO₂ DE CABINA", "3.8 mmHg" if modo_crisis else "1.8 mmHg", delta="Límite: 3.0 mmHg", delta_color="inverse" if modo_crisis else "normal")
        e2.metric("DOSIS RADIACIÓN", "85.0 mSv", delta="14.1% límite carrera (600 mSv)")

        e3, e4 = st.columns(2)
        e3.metric("PRESIÓN CABINA", "101.3 kPa", delta="Nominal NASA V2 6006")
        e4.metric("TEMPERATURA CABINA", "21.8 °C", delta="Confort 18-27 °C")

        e5, e6 = st.columns(2)
        e5.metric("HUMEDAD RELATIVA", "45.0 %", delta="Confort 40-60%")
        e6.metric("EVENTO SOLAR SPE", "TORMENTA ACTIVA" if modo_crisis else "S0 QUIETO", delta_color="inverse" if modo_crisis else "normal")

        st.markdown("#### 📋 CONTRAMEDIDAS AMBIENTALES PRIORIZADAS")
        if modo_crisis:
            st.warning("""
            1. **Reforzar absorción de CO₂:** Activar segundo tren de cartuchos de hidróxido de litio / aminas.
            2. **Ventilación dirigida:** Verificar que los ventiladores de cabina no tengan obstrucciones.
            3. **Dosimetría horaria:** Monitorear flujo de protones solares cada 60 minutos.
            """)
        else:
            st.info("Parámetros ambientales óptimos. Sin contramedidas requeridas.")

# ==============================================================================
# TAB 3: MATRIZ DE DECISIONES DE MARTINA (15 CRUCES CRÍTICOS)
# ==============================================================================
with tab3:
    st.markdown("### 📖 MATRIZ DE DECISIONES DEL CEREBRO CENTRAL (MARTINA NOV 2026)")
    st.caption("15 Cruces Críticos de Datos Multivariados · Máximo 3 Contramedidas por Alerta")

    # Cargar datos desde FastAPI local si está activo o usar catálogo estático
    matriz_data = [
        {"ID": "CX-01", "Nivel": "🔴 CRÍTICA", "Dominio": "Seguridad Inmediata", "Evaluación Preliminar": "Exposición radiológica aguda en curso", "Contramedidas (Máx 3)": "1) Refugio de tormenta. 2) Posponer EVA. 3) Dosis horaria.", "Base": "NOAA SWPC; NASA V1 4030"},
        {"ID": "CX-02", "Nivel": "🔴 CRÍTICA", "Dominio": "Seguridad Inmediata", "Evaluación Preliminar": "Falla de soporte vital atmosférico", "Contramedidas (Máx 3)": "1) Mascarillas O2. 2) Revisar remoción CO2. 3) Procedimiento emergencia.", "Base": "NASA-STD-3001 [V2 6004]"},
        {"ID": "CX-03", "Nivel": "🟠 ALERTA", "Dominio": "Cognición", "Evaluación Preliminar": "Incongruencia cognitiva por fatiga ambiental", "Contramedidas (Máx 3)": "1) Bajar CO2 en cabina de sueño. 2) Bloqueo 8.5h descanso. 3) PVT-B antes de tareas.", "Base": "Barger 2014; Law 2014"},
        {"ID": "CX-04", "Nivel": "🟡 PRECAUCIÓN", "Dominio": "Cognición", "Evaluación Preliminar": "Deuda de sueño no percibida", "Contramedidas (Máx 3)": "1) Gráfica objetiva de lapsos. 2) 2 noches recuperación. 3) Evitar luz azul.", "Base": "Van Dongen 2003"},
        {"ID": "CX-05", "Nivel": "🟠 ALERTA", "Dominio": "Cognición", "Evaluación Preliminar": "Alerta reducida por hipnótico", "Contramedidas (Máx 3)": "1) Notificar médico. 2) Reasignar tarea crítica. 3) Doble verificación.", "Base": "Barger 2014 Lancet"},
        {"ID": "CX-06", "Nivel": "🟠 ALERTA", "Dominio": "Cognición", "Evaluación Preliminar": "Sobrecarga fisiológica por estrés", "Contramedidas (Máx 3)": "1) Redistribuir tareas. 2) Descanso 2h sin pantallas. 3) Ejercicio aeróbico.", "Base": "NASA BHP; HRV -20%"},
        {"ID": "CX-07", "Nivel": "🟠 ALERTA", "Dominio": "Ambiente", "Evaluación Preliminar": "Síntomas compatibles con CO2 elevado", "Contramedidas (Máx 3)": "1) Módulo con mejor ventilación. 2) Elevar remoción CO2. 3) Registro cada 4h.", "Base": "Law 2014 (excluye días 1-7)"},
        {"ID": "CX-08", "Nivel": "🟡 PRECAUCIÓN", "Dominio": "Ambiente", "Evaluación Preliminar": "Sueño alterado por ambiente térmico", "Contramedidas (Máx 3)": "1) Ajustar termostato (20-22°C). 2) Revisar ventilación. 3) Ropa de dormir.", "Base": "NASA-STD-3001 [V2 6003]"},
        {"ID": "CX-09", "Nivel": "🟠 ALERTA", "Dominio": "Hueso/Nutrición", "Evaluación Preliminar": "Pérdida ósea en ventana crítica", "Contramedidas (Máx 3)": "1) Reprogramar sentadilla/peso muerto ARED. 2) Snack proteína. 3) Avisar médico.", "Base": "npj Microgravity 2020"},
        {"ID": "CX-10", "Nivel": "🟠 ALERTA", "Dominio": "Hueso/Nutrición", "Evaluación Preliminar": "Riesgo de cálculos renales", "Contramedidas (Máx 3)": "1) Líquidos 2.0-2.5 L/día. 2) Reducir sodio. 3) Avisar médico (citrato potasio).", "Base": "NASA NTRS Goodenow 2022"},
        {"ID": "CX-11", "Nivel": "🟡 PRECAUCIÓN", "Dominio": "Hueso/Nutrición", "Evaluación Preliminar": "Deficiencia de vitamina D", "Contramedidas (Máx 3)": "1) Recordatorio diario 800 UI/día. 2) Registro en panel.", "Base": "NASA Nutritional Smith 2012"},
        {"ID": "CX-12", "Nivel": "🟠 ALERTA", "Dominio": "Hueso/Nutrición", "Evaluación Preliminar": "Balance calórico negativo", "Contramedidas (Máx 3)": "1) Ajustar menú calórico. 2) Proteína post-ejercicio. 3) Revisión nutricionista.", "Base": "NASA HRP Pérdida >2%"},
        {"ID": "CX-13", "Nivel": "🟡 PRECAUCIÓN", "Dominio": "Hueso/Nutrición", "Evaluación Preliminar": "Descarga mecánica en Marte", "Contramedidas (Máx 3)": "1) Aumentar carga en hábitat. 2) Rutina de saltos/impacto.", "Base": "NASA JPL Polvo Marciano"},
        {"ID": "CX-14", "Nivel": "🟠 ALERTA", "Dominio": "Conducta", "Evaluación Preliminar": "Retraimiento por aislamiento", "Contramedidas (Máx 3)": "1) Video privado familia. 2) Tarea grupal/plantas. 3) Notificar psicología.", "Base": "NASA Behavioral Protocol"},
        {"ID": "CX-15", "Nivel": "🟡 PRECAUCIÓN", "Dominio": "Conducta", "Evaluación Preliminar": "Disminución de motivación", "Contramedidas (Máx 3)": "1) Mensaje de progreso. 2) Reducir meta del día. 3) Soporte psicológico.", "Base": "Gao 2022 Voz & HNR"},
    ]
    st.dataframe(pd.DataFrame(matriz_data), use_container_width=True, hide_index=True)

# Footer reglamentario
st.markdown("---")
st.markdown("""
<div style="display:flex; justify-content:space-between; font-family:'Share Tech Mono'; font-size:12px; color:#798da3;">
    <div>DATOS SIMULADOS | EVALUACIÓN PRELIMINAR (NO PRESUNTIVA) | PROTOTIPO CONCEPTUAL NASA SPACE APPS 2026</div>
    <div>CREW VIEW / RESUMEN &nbsp;·&nbsp; MEDICAL VIEW: ECG, HISTORIAL Y ALERTAS</div>
</div>
""", unsafe_allow_html=True)
