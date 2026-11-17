"""
H.E.L.I.O.S. - Streamlit Cockpit Dashboard (NASA Space Apps 2026).
Interactive visual interface with a holographic body monitor and space habitat.
"""

import json
import time
import requests
import streamlit as st
import pandas as pd
import numpy as np

# Streamlit page configuration
st.set_page_config(
    page_title="H.E.L.I.O.S. - Crew Health & Habitat Monitor",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Futuristic aerospace CSS styles (Sci-Fi Dark Theme)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600;900&family=Rajdhani:wght@600;700&family=Share+Tech+Mono&display=swap');

    /* General background */
    .stApp {
        background-color: #060a14;
        color: #e2e8f0;
        font-family: 'Rajdhani', sans-serif;
    }

    /* HUD headings */
    h1, h2, h3 {
        font-family: 'Orbitron', monospace !important;
        color: #00f0ff !important;
        letter-spacing: 2px;
        text-shadow: 0 0 10px rgba(0, 240, 255, 0.4);
    }

    /* Metrics */
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

    /* Boxes and panels */
    .hud-box {
        background: #0d1527;
        border: 1px solid rgba(0, 240, 255, 0.25);
        border-radius: 8px;
        padding: 18px;
        margin-bottom: 16px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
    }

    /* Critical alert modal, mockup replica */
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

# Sidebar (Control panel)
with st.sidebar:
    st.markdown("### 🛰️ MISSION CONTROL")
    selected_habitat = st.selectbox(
        "Operational Habitat:",
        [
            "Transit Spacecraft to Mars (Deep Space)",
            "International Space Station (ISS)",
            "Mars Base (Surface 0.38g)",
            "Artemis Lunar Base (0.16g)",
        ],
        index=0
    )

    st.markdown("---")
    st.markdown("### ⚡ DEMO SIMULATOR")
    crisis_mode = st.toggle("Activate Crisis Scenario (Day 95)", value=False)

    st.markdown("---")
    st.markdown("### 📡 EARTH LINK (DSN)")
    if "Mars" in selected_habitat:
        st.info("Signal delay: **14 to 22 minutes**.\n\n*Autonomous Edge AI mode active (Store-and-Forward).*")
    elif "Lunar" in selected_habitat:
        st.info("Signal delay: **1.3 seconds**.")
    else:
        st.success("Signal delay: **< 0.5 seconds (LEO)**.")

    st.markdown("---")
    st.caption("NASA Space Apps 2026 · H.E.L.I.O.S. v2.1")

# Main header
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown("# H.E.L.I.O.S. CREW HEALTH MONITOR")
    st.markdown("**DEEP SPACE LIFE SUPPORT SYSTEM · SOL 120**")
with col_h2:
    if crisis_mode:
        st.markdown("""
        <div style="background:rgba(255,34,85,0.2); border:1px solid #ff2255; padding:10px; border-radius:6px; text-align:center;">
            <span style="font-family:'Orbitron'; font-size:16px; color:#ff2255; font-weight:bold;">ASTRONAUT A01: CRITICAL</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background:rgba(0,255,136,0.2); border:1px solid #00ff88; padding:10px; border-radius:6px; text-align:center;">
            <span style="font-family:'Orbitron'; font-size:16px; color:#00ff88; font-weight:bold;">ASTRONAUT A01: STABLE</span>
        </div>
        """, unsafe_allow_html=True)

# CRITICAL ALERT MODAL / BANNER (REPLICA OF THE MOCKUP)
if crisis_mode:
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
            <strong style="color:#00f0ff; font-family:'Orbitron'; font-size:11px;">IMMEDIATE PRIORITY ACTIONS (MAXIMUM 3):</strong><br>
            1. Don the O₂ mask and take absolute rest in the sleep station.<br>
            2. Raise the forced CO₂ removal cycle in the cabin module.<br>
            3. Log to the local buffer and raise a medical priority alert to Earth.
        </div>
    </div>
    """, unsafe_allow_html=True)

# MAIN TABS (THE 2 REQUESTED VIEWS + DECISION MATRIX)
tab1, tab2, tab3 = st.tabs([
    "🩺 VIEW 1: BIOMEDICAL & HUMAN HOLOGRAM",
    "🚀 VIEW 2: CABIN ENVIRONMENT & HABITAT",
    "📋 VIEW 3: DECISION MATRIX (15 CROSSOVERS)",
])

# ==============================================================================
# TAB 1: BIOMEDICAL VIEW & BODY HOLOGRAM
# ==============================================================================
with tab1:
    col_holo, col_vitals = st.columns([1.1, 1])

    with col_holo:
        st.markdown("### 🧬 HOLOGRAM ANATOMICAL SUMMARY")
        st.caption("Bio-Monitor Astroskin (CSA) · Continuous 3D crew member scan")

        # Stylized visual representation of the human hologram
        st.markdown("""
        <div style="display:flex; justify-content:center; align-items:center; background:radial-gradient(circle at center, rgba(0,240,255,0.08) 0%, transparent 70%); border:1px dashed rgba(0,240,255,0.3); border-radius:8px; padding:20px; min-height:480px; position:relative;">
            <svg width="280" height="420" viewBox="0 0 280 420">
                <!-- Holographic silhouette -->
                <circle cx="140" cy="50" r="28" fill="rgba(0,240,255,0.15)" stroke="#00f0ff" stroke-width="2"></circle>
                <line x1="140" y1="78" x2="140" y2="190" stroke="#00f0ff" stroke-width="2" stroke-dasharray="2 2"></line>
                <!-- Clavicle and arms -->
                <line x1="90" y1="100" x2="190" y2="100" stroke="#00f0ff" stroke-width="2"></line>
                <line x1="90" y1="100" x2="55" y2="180" stroke="#00f0ff" stroke-width="2"></line>
                <line x1="55" y1="180" x2="35" y2="250" stroke="#00f0ff" stroke-width="2"></line>
                <line x1="190" y1="100" x2="225" y2="180" stroke="#00f0ff" stroke-width="2"></line>
                <line x1="225" y1="180" x2="245" y2="250" stroke="#00f0ff" stroke-width="2"></line>
                <!-- Pelvis and legs -->
                <path d="M110 190 L170 190 L160 220 L120 220 Z" fill="rgba(0,240,255,0.1)" stroke="#00f0ff" stroke-width="2"></path>
                <line x1="120" y1="220" x2="110" y2="310" stroke="#00f0ff" stroke-width="3"></line>
                <line x1="110" y1="310" x2="105" y2="395" stroke="#00f0ff" stroke-width="2.5"></line>
                <line x1="160" y1="220" x2="170" y2="310" stroke="#00f0ff" stroke-width="3"></line>
                <line x1="170" y1="310" x2="175" y2="395" stroke="#00f0ff" stroke-width="2.5"></line>

                <!-- Pulsing vital nodes -->
                <!-- Brain -->
                <circle cx="140" cy="50" r="7" fill="#00f0ff" stroke="#fff" stroke-width="1.5"></circle>
                <!-- Heart -->
                <circle cx="140" cy="125" r="9" fill="#ff2255" stroke="#fff" stroke-width="2"></circle>
                <!-- Lungs -->
                <circle cx="120" cy="115" r="5" fill="#00ff88"></circle>
                <circle cx="160" cy="115" r="5" fill="#00ff88"></circle>
                <!-- Bones (Femur) -->
                <circle cx="110" cy="310" r="6" fill="#ffaa00"></circle>
                <circle cx="170" cy="310" r="6" fill="#ffaa00"></circle>

                <!-- Callout leader lines -->
                <polyline points="140,50 80,30 30,30" fill="none" stroke="#00f0ff" stroke-width="1.5"></polyline>
                <polyline points="140,125 70,125 20,125" fill="none" stroke="#ff2255" stroke-width="1.5"></polyline>
                <polyline points="160,115 210,105 250,105" fill="none" stroke="#00ff88" stroke-width="1.5"></polyline>
                <polyline points="170,310 215,330 255,330" fill="none" stroke="#ffaa00" stroke-width="1.5"></polyline>
            </svg>
        </div>
        """, unsafe_allow_html=True)

        col_c1, col_c2, col_c3 = st.columns(3)
        col_c1.info("**BRAIN (ASTRA)**\n\nLatency: " + ("850 ms" if crisis_mode else "210 ms"))
        col_c2.error("**HEART**\n\nPulse: " + ("132 bpm" if crisis_mode else "76 bpm"))
        col_c3.warning("**BONE SHIELD**\n\nLoss: -1.8%\nARED: 80%")

    with col_vitals:
        st.markdown("### 📊 REAL-TIME INDICATORS")

        m1, m2 = st.columns(2)
        m1.metric("HEART RATE", "132 bpm" if crisis_mode else "76 bpm", delta="+56 bpm" if crisis_mode else "0 bpm", delta_color="inverse")
        m2.metric("SpO₂ SATURATION", "88 %" if crisis_mode else "98 %", delta="-10 %" if crisis_mode else "0 %", delta_color="normal")

        m3, m4 = st.columns(2)
        m3.metric("BLOOD PRESSURE", "145/95 mmHg" if crisis_mode else "118/76 mmHg")
        m4.metric("BODY TEMPERATURE", "38.4 °C" if crisis_mode else "36.6 °C", delta="+1.8 °C" if crisis_mode else "0.0 °C", delta_color="inverse")

        m5, m6 = st.columns(2)
        m5.metric("HEART RATE VARIABILITY (HRV)", "18 ms (Low)" if crisis_mode else "42 ms (Optimal)")
        m6.metric("BONE DEMINERALIZATION", "-1.8 %", delta="HSRB model Sol 120")

        # Illustrative electrocardiogram (ECG) chart
        st.markdown("#### ⚡ ILLUSTRATIVE ELECTROCARDIOGRAM (LEAD II)")
        time_axis = np.linspace(0, 4 * np.pi, 200)
        ecg_wave = np.sin(time_axis * (2.2 if crisis_mode else 1.2)) + 0.15 * np.random.randn(200)
        # Inject the QRS spike
        ecg_wave[::25] += 2.8 if crisis_mode else 2.0
        st.line_chart(pd.DataFrame({"ECG (mV)": ecg_wave}), height=140)

# ==============================================================================
# TAB 2: ENVIRONMENT & SPACE HABITAT VIEW
# ==============================================================================
with tab2:
    col_env1, col_env2 = st.columns([1, 1])

    with col_env1:
        st.markdown("### 🌌 HABITAT & SPACE WEATHER MONITORING")
        st.caption("ECLSS / RAD dosimetry / Thermal control and pressurization")

        st.markdown(f"""
        <div style="background:#0a1224; border:1px solid #00f0ff; border-radius:8px; padding:20px; text-align:center;">
            <h4 style="color:#00f0ff; margin-bottom:10px;">HABITAT: {selected_habitat.upper()}</h4>
            <p style="color:#cbd5e1; font-family:'Share Tech Mono';">
                • Pressurization status: <strong>STABLE (95 - 103 kPa)</strong><br>
                • Forced convection system: <strong>ACTIVE</strong><br>
                • Radiological shielding: <strong>MONITORED BY RAD</strong>
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("#### 🔬 KRONECKER SYNERGISTIC CROSSOVER MATRIX (R^12)")
        edges = [
            "CO2xPulse", "CO2xSleep", "CO2xBone", "CO2xSANS",
            "RadxPulse", "RadxSleep", "RadxBone", "RadxSANS",
            "PresxPulse", "PresxSleep", "PresxBone", "PresxSANS"
        ]
        weights = [0.0] * 12
        if crisis_mode:
            weights[3] = 9.2  # CO2 x SANS
            weights[0] = 7.5  # CO2 x Pulse
            st.error("Critical Edge Activated: **CO2_WITH_SANS_INTRACRANIAL_HYPERTENSION (Severity: 9.2/10)**")
        else:
            st.success("Matrix Graph: **No adverse synergies activated (Hazard: 0.0/10)**")

        df_kronecker = pd.DataFrame({
            "Interaction Edge": edges,
            "Weighted Severity": weights
        })
        st.bar_chart(df_kronecker.set_index("Interaction Edge"), height=220)

    with col_env2:
        st.markdown("### 🎛️ CABIN ENVIRONMENTAL SENSORS")

        e1, e2 = st.columns(2)
        e1.metric("CABIN CO₂", "3.8 mmHg" if crisis_mode else "1.8 mmHg", delta="Limit: 3.0 mmHg", delta_color="inverse" if crisis_mode else "normal")
        e2.metric("RADIATION DOSE", "85.0 mSv", delta="14.1% of career limit (600 mSv)")

        e3, e4 = st.columns(2)
        e3.metric("CABIN PRESSURE", "101.3 kPa", delta="Nominal NASA V2 6006")
        e4.metric("CABIN TEMPERATURE", "21.8 °C", delta="Comfort 18-27 °C")

        e5, e6 = st.columns(2)
        e5.metric("RELATIVE HUMIDITY", "45.0 %", delta="Comfort 40-60%")
        e6.metric("SPE SOLAR EVENT", "STORM ACTIVE" if crisis_mode else "S0 QUIET", delta_color="inverse" if crisis_mode else "normal")

        st.markdown("#### 📋 PRIORITIZED ENVIRONMENTAL COUNTERMEASURES")
        if crisis_mode:
            st.warning("""
            1. **Reinforce CO₂ absorption:** Activate the second train of lithium hydroxide / amine cartridges.
            2. **Directed ventilation:** Verify that the cabin fans are free of obstructions.
            3. **Hourly dosimetry:** Monitor the solar proton flux every 60 minutes.
            """)
        else:
            st.info("Environmental parameters optimal. No countermeasures required.")

# ==============================================================================
# TAB 3: MARTINA'S DECISION MATRIX (15 CRITICAL CROSSOVERS)
# ==============================================================================
with tab3:
    st.markdown("### 📖 CENTRAL BRAIN DECISION MATRIX (MARTINA NOV 2026)")
    st.caption("15 Critical Multivariate Data Crossovers · Maximum 3 Countermeasures per Alert")

    # Load data from the local FastAPI if active, or use the static catalog
    matrix_data = [
        {"ID": "CX-01", "Level": "🔴 CRITICAL", "Domain": "Immediate Safety", "Preliminary Assessment": "Acute radiological exposure in progress", "Countermeasures (Max 3)": "1) Storm shelter. 2) Postpone EVA. 3) Hourly dose.", "Basis": "NOAA SWPC; NASA V1 4030"},
        {"ID": "CX-02", "Level": "🔴 CRITICAL", "Domain": "Immediate Safety", "Preliminary Assessment": "Atmospheric life support failure", "Countermeasures (Max 3)": "1) O2 masks. 2) Inspect CO2 removal. 3) Emergency procedure.", "Basis": "NASA-STD-3001 [V2 6004]"},
        {"ID": "CX-03", "Level": "🟠 ALERT", "Domain": "Cognition", "Preliminary Assessment": "Cognitive incongruence from environmental fatigue", "Countermeasures (Max 3)": "1) Lower CO2 in the sleep cabin. 2) Block 8.5h rest. 3) PVT-B before tasks.", "Basis": "Barger 2014; Law 2014"},
        {"ID": "CX-04", "Level": "🟡 CAUTION", "Domain": "Cognition", "Preliminary Assessment": "Unperceived sleep debt", "Countermeasures (Max 3)": "1) Objective lapse chart. 2) 2 recovery nights. 3) Avoid blue light.", "Basis": "Van Dongen 2003"},
        {"ID": "CX-05", "Level": "🟠 ALERT", "Domain": "Cognition", "Preliminary Assessment": "Reduced alertness from hypnotic", "Countermeasures (Max 3)": "1) Notify surgeon. 2) Reassign critical task. 3) Double check.", "Basis": "Barger 2014 Lancet"},
        {"ID": "CX-06", "Level": "🟠 ALERT", "Domain": "Cognition", "Preliminary Assessment": "Physiological overload from stress", "Countermeasures (Max 3)": "1) Redistribute tasks. 2) 2h rest with no screens. 3) Aerobic exercise.", "Basis": "NASA BHP; HRV -20%"},
        {"ID": "CX-07", "Level": "🟠 ALERT", "Domain": "Environment", "Preliminary Assessment": "Symptoms consistent with elevated CO2", "Countermeasures (Max 3)": "1) Module with better ventilation. 2) Raise CO2 removal. 3) Log every 4h.", "Basis": "Law 2014 (excludes days 1-7)"},
        {"ID": "CX-08", "Level": "🟡 CAUTION", "Domain": "Environment", "Preliminary Assessment": "Sleep degraded by thermal environment", "Countermeasures (Max 3)": "1) Adjust thermostat (20-22°C). 2) Inspect ventilation. 3) Sleepwear.", "Basis": "NASA-STD-3001 [V2 6003]"},
        {"ID": "CX-09", "Level": "🟠 ALERT", "Domain": "Bone/Nutrition", "Preliminary Assessment": "Bone loss in the critical window", "Countermeasures (Max 3)": "1) Reschedule ARED squat/deadlift. 2) Protein snack. 3) Notify surgeon.", "Basis": "npj Microgravity 2020"},
        {"ID": "CX-10", "Level": "🟠 ALERT", "Domain": "Bone/Nutrition", "Preliminary Assessment": "Kidney stone risk", "Countermeasures (Max 3)": "1) Fluids 2.0-2.5 L/day. 2) Reduce sodium. 3) Notify surgeon (potassium citrate).", "Basis": "NASA NTRS Goodenow 2022"},
        {"ID": "CX-11", "Level": "🟡 CAUTION", "Domain": "Bone/Nutrition", "Preliminary Assessment": "Vitamin D deficiency", "Countermeasures (Max 3)": "1) Daily reminder 800 IU/day. 2) Log in the panel.", "Basis": "NASA Nutritional Smith 2012"},
        {"ID": "CX-12", "Level": "🟠 ALERT", "Domain": "Bone/Nutrition", "Preliminary Assessment": "Negative caloric balance", "Countermeasures (Max 3)": "1) Adjust caloric menu. 2) Post-exercise protein. 3) Nutritionist review.", "Basis": "NASA HRP Loss >2%"},
        {"ID": "CX-13", "Level": "🟡 CAUTION", "Domain": "Bone/Nutrition", "Preliminary Assessment": "Mechanical unloading on Mars", "Countermeasures (Max 3)": "1) Increase load in the habitat. 2) Jump/impact routine.", "Basis": "NASA JPL Martian Dust"},
        {"ID": "CX-14", "Level": "🟠 ALERT", "Domain": "Behavior", "Preliminary Assessment": "Withdrawal from isolation", "Countermeasures (Max 3)": "1) Private family video. 2) Group/plant task. 3) Notify psychology.", "Basis": "NASA Behavioral Protocol"},
        {"ID": "CX-15", "Level": "🟡 CAUTION", "Domain": "Behavior", "Preliminary Assessment": "Declining motivation", "Countermeasures (Max 3)": "1) Progress message. 2) Reduce the day's goal. 3) Psychological support.", "Basis": "Gao 2022 Voice & HNR"},
    ]
    st.dataframe(pd.DataFrame(matrix_data), use_container_width=True, hide_index=True)

# Regulatory footer
st.markdown("---")
st.markdown("""
<div style="display:flex; justify-content:space-between; font-family:'Share Tech Mono'; font-size:12px; color:#798da3;">
    <div>SIMULATED DATA | PRELIMINARY ASSESSMENT (NON-PRESUMPTIVE) | NASA SPACE APPS 2026 CONCEPT PROTOTYPE</div>
    <div>CREW VIEW / SUMMARY &nbsp;·&nbsp; MEDICAL VIEW: ECG, HISTORY AND ALERTS</div>
</div>
""", unsafe_allow_html=True)
