"""
Generador de la silueta anatómica holográfica de H.E.L.I.O.S.

En lugar de editar a mano rutas SVG de miles de caracteres, la figura se
construye desde una tabla de referencias anatómicas con el canon de 7,5 cabezas,
de modo que las proporciones son correctas por construcción y verificables.

Cada parte del cuerpo se define como un PERFIL: una lista de (y, semiancho).
El perfil se refleja respecto al eje central y se suaviza con Catmull-Rom
convertido a curvas de Bézier cúbicas, produciendo un contorno continuo sin
los quiebres de la figura anterior.

Lienzo local del grupo anatómico: 320 x 500, eje central en x = 160.
"""

from typing import Final

EJE_X: Final[float] = 160.0

# ======================================================================================
# CANON DE 7,5 CABEZAS
# Corona y = 14, planta del pie y = 474  ->  altura 460, módulo cefálico H = 61.3
# ======================================================================================
Y_CORONA: Final[float] = 14.0
Y_PLANTA: Final[float] = 474.0
H: Final[float] = (Y_PLANTA - Y_CORONA) / 7.5

Y_MENTON: Final[float] = Y_CORONA + 1.00 * H   #  75.3
Y_HOMBRO: Final[float] = Y_CORONA + 1.40 * H   #  99.8
Y_PECHO: Final[float] = Y_CORONA + 2.00 * H    # 136.6
Y_CINTURA: Final[float] = Y_CORONA + 3.00 * H  # 198.0
Y_CADERA: Final[float] = Y_CORONA + 3.50 * H   # 228.6
Y_ENTREPIERNA: Final[float] = Y_CORONA + 3.75 * H  # 243.9
Y_RODILLA: Final[float] = Y_CORONA + 5.50 * H  # 351.2
Y_TOBILLO: Final[float] = Y_CORONA + 7.20 * H  # 455.4


def catmull_rom_a_bezier(puntos: list[tuple[float, float]], cerrado: bool = True) -> str:
    """
    Convierte una polilínea en una ruta SVG suave mediante Catmull-Rom uniforme.

    Args:
        puntos: Vértices de control en orden de recorrido.
        cerrado: Si la curva debe cerrarse sobre sí misma.

    Returns:
        Cadena de datos 'd' para un elemento <path>.
    """
    n = len(puntos)
    if n < 3:
        return ""

    def en(i: int) -> tuple[float, float]:
        if cerrado:
            return puntos[i % n]
        return puntos[max(0, min(n - 1, i))]

    partes = [f"M{puntos[0][0]:.1f} {puntos[0][1]:.1f}"]
    total = n if cerrado else n - 1
    for i in range(total):
        p0, p1, p2, p3 = en(i - 1), en(i), en(i + 1), en(i + 2)
        # Tensión 1/6: tangente de Catmull-Rom estándar
        c1 = (p1[0] + (p2[0] - p0[0]) / 6.0, p1[1] + (p2[1] - p0[1]) / 6.0)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6.0, p2[1] - (p3[1] - p1[1]) / 6.0)
        partes.append(
            f"C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}"
        )
    if cerrado:
        partes.append("Z")
    return " ".join(partes)


def perfil_a_contorno(
    perfil: list[tuple[float, float]], eje: float = EJE_X
) -> list[tuple[float, float]]:
    """
    Expande un perfil (y, semiancho) a un contorno cerrado simétrico.

    Recorre el lado derecho de arriba abajo y vuelve por el izquierdo.
    """
    derecha = [(eje + w, y) for y, w in perfil]
    izquierda = [(eje - w, y) for y, w in reversed(perfil)]
    return derecha + izquierda


def perfil_desplazado(
    perfil: list[tuple[float, float]], centro: float
) -> list[tuple[float, float]]:
    """Expande un perfil alrededor de un eje propio (para extremidades)."""
    return perfil_a_contorno(perfil, eje=centro)


# ======================================================================================
# PERFILES ANATÓMICOS  (y, semiancho)
# ======================================================================================

# Cabeza: óvalo craneal con afinamiento mandibular
CABEZA: Final[list[tuple[float, float]]] = [
    (Y_CORONA, 3.0),
    (Y_CORONA + 6, 16.0),
    (Y_CORONA + 16, 23.0),
    (Y_CORONA + 30, 24.0),
    (Y_CORONA + 44, 20.0),
    (Y_MENTON - 4, 12.0),
    (Y_MENTON, 4.0),
]

# Cuello y torso: hombros -> caja torácica -> cintura -> cadera
TORSO: Final[list[tuple[float, float]]] = [
    (Y_MENTON - 2, 11.0),        # base del cuello
    (Y_MENTON + 10, 13.0),       # trapecio
    (Y_HOMBRO, 46.0),            # línea de hombros (2H de envergadura)
    (Y_HOMBRO + 14, 49.0),       # deltoides
    (Y_PECHO, 44.0),             # pectoral
    (Y_PECHO + 28, 38.0),        # arco costal
    (Y_CINTURA, 31.0),           # cintura (punto más estrecho)
    (Y_CADERA, 40.0),            # cresta ilíaca
    (Y_ENTREPIERNA, 37.0),       # pelvis
]

# Brazo: deltoides -> bíceps -> codo -> antebrazo -> muñeca -> mano
BRAZO: Final[list[tuple[float, float]]] = [
    (Y_HOMBRO + 4, 15.0),
    (Y_PECHO, 14.0),             # bíceps
    (Y_PECHO + 34, 11.5),        # codo
    (Y_CINTURA + 6, 10.0),       # antebrazo
    (Y_CADERA + 10, 7.5),        # muñeca
    (Y_ENTREPIERNA + 16, 9.5),   # mano
    (Y_ENTREPIERNA + 34, 5.0),   # dedos
]
CENTRO_BRAZO: Final[float] = 48.0   # desplazamiento desde el eje

# Pierna: muslo -> rodilla -> gemelo -> tobillo -> pie
PIERNA: Final[list[tuple[float, float]]] = [
    (Y_ENTREPIERNA - 12, 19.0),  # inserción del muslo
    (Y_ENTREPIERNA + 30, 18.0),  # muslo
    (Y_RODILLA - 40, 15.0),      # sobre la rodilla
    (Y_RODILLA, 13.0),           # rodilla
    (Y_RODILLA + 34, 14.0),      # gemelo
    (Y_TOBILLO - 30, 8.5),       # pantorrilla baja
    (Y_TOBILLO, 6.5),            # tobillo
    (Y_PLANTA - 4, 8.0),         # empeine
]
# Separación suficiente para que ambas piernas no se fundan en el eje central.
CENTRO_PIERNA: Final[float] = 22.0


def construir_rutas() -> dict[str, str]:
    """Genera todas las rutas 'd' de la figura anatómica."""
    return {
        "cabeza": catmull_rom_a_bezier(perfil_a_contorno(CABEZA)),
        "torso": catmull_rom_a_bezier(perfil_a_contorno(TORSO)),
        "brazo_izq": catmull_rom_a_bezier(perfil_desplazado(BRAZO, EJE_X - CENTRO_BRAZO)),
        "brazo_der": catmull_rom_a_bezier(perfil_desplazado(BRAZO, EJE_X + CENTRO_BRAZO)),
        "pierna_izq": catmull_rom_a_bezier(perfil_desplazado(PIERNA, EJE_X - CENTRO_PIERNA)),
        "pierna_der": catmull_rom_a_bezier(perfil_desplazado(PIERNA, EJE_X + CENTRO_PIERNA)),
    }


def informe_proporciones() -> str:
    """Comprueba que la figura respeta el canon y reporta las cotas."""
    altura = Y_PLANTA - Y_CORONA
    # La envergadura biacromial se mide al borde externo del deltoides, que lo
    # define el brazo, no el torso.
    semiancho_brazo_alto = BRAZO[0][1]
    envergadura_hombros = (CENTRO_BRAZO + semiancho_brazo_alto) * 2
    separacion_piernas = (CENTRO_PIERNA - max(w for _, w in PIERNA)) * 2
    lineas = [
        f"Módulo cefálico H        : {H:.1f} u",
        f"Altura total             : {altura:.1f} u  ({altura / H:.2f} cabezas)",
        f"Envergadura biacromial   : {envergadura_hombros:.1f} u  ({envergadura_hombros / H:.2f} H · canon 2.0)",
        f"Separación entre piernas : {separacion_piernas:.1f} u  ({'holgura positiva' if separacion_piernas > 0 else 'SE SOLAPAN'})",
        f"Entrepierna (mitad)      : y={Y_ENTREPIERNA:.1f}  ({(Y_ENTREPIERNA - Y_CORONA) / altura * 100:.1f}% de la altura · canon 50%)",
        f"Rodilla                  : y={Y_RODILLA:.1f}  ({(Y_RODILLA - Y_CORONA) / H:.2f} H · canon 5.5)",
        f"Cintura / hombro         : {min(w for y, w in TORSO[2:]) / max(w for y, w in TORSO):.2f}  (canon ~0.63)",
    ]
    return "\n".join(lineas)


# ======================================================================================
# REFERENCIAS DE ÓRGANOS, REALINEADAS AL NUEVO CANON
# La figura anterior situaba la entrepierna al 61.5% de la altura (canon 50%),
# por lo que todas las vísceras colgaban demasiado bajas respecto al tórax.
# ======================================================================================
ORGANOS: Final[dict[str, dict[str, float]]] = {
    "cerebro":     {"cx": 160, "cy": 44,  "rx": 26, "ry": 24},
    "pulmones":    {"cx": 160, "cy": 138, "rx": 32, "ry": 30},
    "corazon":     {"cx": 163, "cy": 141, "rx": 16, "ry": 18},
    "hidratacion": {"cx": 160, "cy": 187, "rx": 26, "ry": 12},
    "rodilla_y":   {"cx": 0,   "cy": 351, "rx": 0,  "ry": 0},
}
CENTRO_RODILLA: Final[float] = CENTRO_PIERNA  # 22 u a cada lado del eje


def _mult(d: str, campos: dict[str, float]) -> str:
    """Interpola referencias numéricas en una plantilla de ruta."""
    return d.format(**campos)


def construir_grupo_anatomico() -> str:
    """Emite el grupo SVG completo: halo, silueta, esqueleto y órganos."""
    r = construir_rutas()
    partes_cuerpo = [r["cabeza"], r["torso"], r["brazo_izq"], r["brazo_der"],
                     r["pierna_izq"], r["pierna_der"]]

    halo = "\n".join(f'              <path d="{d}"></path>' for d in partes_cuerpo)
    silueta = "\n".join(f'              <path d="{d}"></path>' for d in partes_cuerpo)
    trama = "\n".join(f'              <path d="{d}"></path>' for d in partes_cuerpo)

    ry, rx = ORGANOS["rodilla_y"]["cy"], CENTRO_RODILLA
    k_izq, k_der = EJE_X - rx, EJE_X + rx

    # --- Columna vertebral segmentada: cervical, torácica, lumbar, sacro ---
    vertebras = []
    tramos = [(Y_MENTON + 2, Y_HOMBRO, 7, 2.0, "#cfeffa"),
              (Y_HOMBRO, Y_CINTURA, 12, 2.6, "var(--c-cyan-ink)"),
              (Y_CINTURA, Y_CADERA, 5, 3.0, "#cfeffa")]
    for y0, y1, n, rad, col in tramos:
        for i in range(n):
            y = y0 + (y1 - y0) * (i + 0.5) / n
            vertebras.append(
                f'              <circle cx="160" cy="{y:.1f}" r="{rad}" fill="{col}"></circle>'
            )
    columna = "\n".join(vertebras)

    # --- Caja torácica: pares de costillas curvadas ---
    costillas = []
    for i in range(7):
        y = Y_HOMBRO + 10 + i * 11.5
        ancho = 26 + i * 2.6 - (0 if i < 5 else (i - 4) * 7)
        caida = 13 + i * 1.2
        costillas.append(
            f'              <path d="M156 {y:.1f} C{160 - ancho * 0.55:.1f} {y + caida * 0.35:.1f} '
            f'{160 - ancho:.1f} {y + caida * 0.7:.1f} {160 - ancho - 3:.1f} {y + caida:.1f}"></path>'
        )
        costillas.append(
            f'              <path d="M164 {y:.1f} C{160 + ancho * 0.55:.1f} {y + caida * 0.35:.1f} '
            f'{160 + ancho:.1f} {y + caida * 0.7:.1f} {160 + ancho + 3:.1f} {y + caida:.1f}"></path>'
        )
    caja = "\n".join(costillas)

    return f"""        <!-- SILUETA ANATÓMICA — generada por frontend/generar_silueta.py
             Canon de 7,5 cabezas: H={H:.1f}u · envergadura 2.05H · entrepierna al 50%.
             No editar a mano: modificar las tablas de perfiles y regenerar. -->

        <g id="bodyAnatomyGroup" transform="translate(180, 10)">

          <!-- 1. HALO VOLUMÉTRICO -->
          <g pointer-events="none" fill="none" stroke="var(--c-cyan)" stroke-width="6"
             opacity="0.16" style="filter:blur(6px);">
{halo}
          </g>

          <!-- 2. SILUETA CORPORAL -->
          <g id="bodyContour" pointer-events="none" fill="url(#bodySkinGrad)"
             stroke="var(--c-cyan-ink)" stroke-width="1.4" stroke-linejoin="round" opacity="0.9">
{silueta}
          </g>

          <!-- 3. TRAMA DE ESCANEO TOMOGRÁFICO -->
          <g pointer-events="none" fill="url(#holoScanLinesPattern)">
{trama}
          </g>

          <!-- 4. SISTEMA ESQUELÉTICO -->
          <g id="skeletalSystem" pointer-events="none" stroke="rgba(190, 235, 250, 0.40)"
             stroke-width="1.1" fill="none">
            <!-- Clavículas -->
            <path d="M160 {Y_HOMBRO + 2:.1f} Q138 {Y_HOMBRO - 1:.1f} 120 {Y_HOMBRO + 8:.1f}" stroke-width="1.5"></path>
            <path d="M160 {Y_HOMBRO + 2:.1f} Q182 {Y_HOMBRO - 1:.1f} 200 {Y_HOMBRO + 8:.1f}" stroke-width="1.5"></path>
            <!-- Esternón -->
            <line x1="160" y1="{Y_HOMBRO + 4:.1f}" x2="160" y2="{Y_PECHO + 24:.1f}" stroke="url(#boneSpineGrad)" stroke-width="2.2"></line>
            <!-- Caja torácica -->
            <g opacity="0.5" stroke="rgba(150, 225, 250, 0.55)" stroke-width="1.2">
{caja}
            </g>
            <!-- Cintura pélvica -->
            <path d="M160 {Y_CADERA - 4:.1f} C142 {Y_CADERA - 12:.1f} 126 {Y_CADERA - 8:.1f} 122 {Y_CADERA + 6:.1f}
                     C119 {Y_CADERA + 18:.1f} 130 {Y_ENTREPIERNA + 2:.1f} 142 {Y_ENTREPIERNA + 4:.1f}
                     Q152 {Y_ENTREPIERNA + 6:.1f} 160 {Y_ENTREPIERNA - 2:.1f}
                     Q168 {Y_ENTREPIERNA + 6:.1f} 178 {Y_ENTREPIERNA + 4:.1f}
                     C190 {Y_ENTREPIERNA + 2:.1f} 201 {Y_CADERA + 18:.1f} 198 {Y_CADERA + 6:.1f}
                     C194 {Y_CADERA - 8:.1f} 178 {Y_CADERA - 12:.1f} 160 {Y_CADERA - 4:.1f} Z"
                  fill="rgba(23, 159, 179, 0.10)" stroke="var(--c-cyan)" stroke-width="1.3"></path>
          </g>

          <g id="spineVertebrae" pointer-events="none">
{columna}
          </g>

          <!-- 5. ANILLOS DE PROFUNDIDAD TOMOGRÁFICA (CAPA DE FONDO) -->
          <g stroke="rgba(23, 159, 179, 0.28)" stroke-dasharray="2 4" fill="none" pointer-events="none">
            <ellipse cx="160" cy="44" rx="26" ry="7"></ellipse>
            <ellipse cx="160" cy="138" rx="42" ry="10"></ellipse>
            <ellipse cx="160" cy="196" rx="32" ry="8"></ellipse>
            <ellipse cx="{k_izq}" cy="{ry}" rx="15" ry="5"></ellipse>
            <ellipse cx="{k_der}" cy="{ry}" rx="15" ry="5"></ellipse>
          </g>
"""


def construir_organos() -> str:
    """
    Emite los cinco nodos de órgano interactivos sobre las nuevas referencias.

    Cada grupo conserva exactamente su clase, data-organ y manejadores: el
    controlador del HUD y el servicio del holograma dependen de ellos.
    La geometría de impacto es estática y ceñida a la forma visible; la capa
    animada va dentro con pointer-events="none" para que el latido no desplace
    el borde bajo el cursor.
    """
    k = ORGANOS["rodilla_y"]["cy"]
    ki, kd = EJE_X - CENTRO_RODILLA, EJE_X + CENTRO_RODILLA
    y_cadera = Y_CADERA + 14

    def nodo(organo: str, cuerpo: str, id_nodo: str = "") -> str:
        """El id es obligatorio donde el controlador lo busca por getElementById."""
        attr_id = f' id="{id_nodo}"' if id_nodo else ""
        return (
            f'          <g class="organ-node"{attr_id} data-organ="{organo}"\n'
            f'             onmouseenter="window.hudController.enfocarOrgano(\'{organo}\')"\n'
            f'             onmouseleave="window.hudController.desenfocarOrgano()">\n'
            f'{cuerpo}\n'
            f'          </g>\n'
        )

    pulmones = nodo("pulmones", f"""            <ellipse cx="140" cy="139" rx="16" ry="31" fill="transparent" pointer-events="all"></ellipse>
            <ellipse cx="181" cy="139" rx="16" ry="31" fill="transparent" pointer-events="all"></ellipse>
            <g class="pulse-lungs" pointer-events="none">
              <path class="organ-interactive-path" d="M153 112 C141 110 130 116 127 129 C124 142 124 157 127 168 C130 174 138 175 145 172 C151 167 154 157 154 144 Z"
                    fill="url(#organLungGrad)" stroke="var(--c-green)" stroke-width="1.5"
                    filter="drop-shadow(0 0 7px var(--glow-green))"></path>
              <path d="M152 126 Q143 134 136 144 M144 136 Q138 150 134 160" stroke="rgba(230,255,245,0.55)" stroke-width="0.9" fill="none"></path>
              <path class="organ-interactive-path" d="M168 112 C180 110 191 116 194 129 C197 142 197 157 194 168 C191 174 183 175 176 172 C171 165 168 153 166 140 Z"
                    fill="url(#organLungGrad)" stroke="var(--c-green)" stroke-width="1.5"
                    filter="drop-shadow(0 0 7px var(--glow-green))"></path>
              <path d="M169 126 Q178 134 185 144 M177 136 Q183 150 187 160" stroke="rgba(230,255,245,0.55)" stroke-width="0.9" fill="none"></path>
            </g>""")

    viscera = ("""          <g id="visceraAbdominal" opacity="0.6" pointer-events="none">
            <path d="M136 168 C136 163 147 163 156 167 C156 178 152 187 143 188 C138 188 136 179 136 168 Z"
                  fill="rgba(189, 133, 12, 0.20)" stroke="var(--c-amber)" stroke-width="1"></path>
            <path d="M165 167 C173 165 180 169 180 177 C180 184 175 191 168 191 C164 191 164 184 165 174 Z"
                  fill="rgba(23, 159, 179, 0.16)" stroke="var(--c-cyan)" stroke-width="1"></path>
          </g>\n""")

    corazon = nodo("corazon", f"""            <ellipse cx="163" cy="142" rx="16" ry="20" fill="transparent" pointer-events="all"></ellipse>
            <g class="pulse-organ-heart" pointer-events="none">
              <path d="M159 126 C159 119 164 115 169 117 C173 119 173 123 171 128" stroke="var(--c-red-ink)" stroke-width="2.2" fill="none"></path>
              <line x1="165" y1="116" x2="165" y2="110" stroke="var(--c-red-ink)" stroke-width="1.4"></line>
              <path class="organ-interactive-path" d="M157 130 C151 128 148 133 148 140 C148 148 154 157 160 164 C162 166 165 166 167 162 C173 154 178 145 176 135 C174 129 168 127 163 131 C161 132 159 132 157 130 Z"
                    fill="url(#organHeartGrad)" stroke="var(--c-red)" stroke-width="1.6"
                    filter="drop-shadow(0 0 10px var(--glow-red))"></path>
              <path d="M162 134 Q163 144 160 155 M162 141 Q168 147 171 153" stroke="#ffe9a0" stroke-width="1" fill="none" opacity="0.8"></path>
              <circle cx="161" cy="145" r="2.6" fill="#ffffff" filter="drop-shadow(0 0 5px #fff)"></circle>
            </g>""", id_nodo="nodeHeart")

    riñones = nodo("hidratacion", """            <ellipse cx="160" cy="187" rx="26" ry="12" fill="transparent" pointer-events="all"></ellipse>
            <path class="organ-interactive-path" d="M143 179 C147 179 149 183 149 188 C149 193 146 196 142 196 C139 196 138 191 139 186 C139 182 141 179 143 179 Z"
                  fill="url(#kidneyGrad)" stroke="var(--c-blue)" stroke-width="1.3"
                  filter="drop-shadow(0 0 6px var(--glow-blue))"></path>
            <circle cx="144" cy="178" r="1.9" fill="var(--c-amber)"></circle>
            <path class="organ-interactive-path" d="M177 179 C173 179 171 183 171 188 C171 193 174 196 178 196 C181 196 182 191 181 186 C181 182 179 179 177 179 Z"
                  fill="url(#kidneyGrad)" stroke="var(--c-blue)" stroke-width="1.3"
                  filter="drop-shadow(0 0 6px var(--glow-blue))"></path>
            <circle cx="176" cy="178" r="1.9" fill="var(--c-amber)"></circle>""")

    cerebro = nodo("cerebro", """            <circle cx="160" cy="44" r="25" fill="transparent" pointer-events="all"></circle>
            <path class="organ-interactive-path" d="M158 24 C150 23 142 28 140 37 C138 43 140 49 143 53 C139 57 141 64 147 66 C152 68 156 66 158 63 Z"
                  fill="url(#organBrainGrad)" stroke="var(--c-cyan-ink)" stroke-width="1.4"
                  filter="drop-shadow(0 0 9px var(--glow-cyan))"></path>
            <path d="M145 34 Q152 37 156 33 M143 45 Q151 43 157 47 M146 56 Q152 58 157 54" stroke="#eafcff" stroke-width="0.9" fill="none" opacity="0.75"></path>
            <path class="organ-interactive-path" d="M162 24 C170 23 178 28 180 37 C182 43 180 49 177 53 C181 57 179 64 173 66 C168 68 164 66 162 63 Z"
                  fill="url(#organBrainGrad)" stroke="var(--c-cyan-ink)" stroke-width="1.4"
                  filter="drop-shadow(0 0 9px var(--glow-cyan))"></path>
            <path d="M164 33 Q169 37 175 34 M163 47 Q169 43 177 45 M163 54 Q168 58 174 56" stroke="#eafcff" stroke-width="0.9" fill="none" opacity="0.75"></path>
            <line x1="160" y1="24" x2="160" y2="64" stroke="#eafcff" stroke-width="1.2"></line>
            <circle cx="160" cy="44" r="2.9" fill="var(--c-cyan-ink)" stroke="#fff" stroke-width="1"></circle>
            <path d="M149 52 Q160 49 171 52" stroke="var(--c-green)" stroke-width="2.2" fill="none" filter="drop-shadow(0 0 5px var(--glow-green))"></path>""")

    huesos = nodo("huesos", f"""            <circle cx="{ki}" cy="{k}" r="21" fill="transparent" pointer-events="all"></circle>
            <circle cx="{kd}" cy="{k}" r="21" fill="transparent" pointer-events="all"></circle>
            <line class="organ-interactive-path" x1="148" y1="{y_cadera}" x2="{ki}" y2="{k}" stroke="url(#boneSpineGrad)" stroke-width="4" stroke-linecap="round"></line>
            <line x1="{ki}" y1="{k}" x2="{ki - 3}" y2="{Y_TOBILLO:.0f}" stroke="rgba(190, 235, 250, 0.55)" stroke-width="2.6" stroke-linecap="round"></line>
            <circle cx="{ki}" cy="{k}" r="6.5" fill="rgba(189, 133, 12, 0.40)" stroke="var(--c-amber)" stroke-width="1.8" filter="drop-shadow(0 0 7px var(--glow-amber))"></circle>
            <circle cx="{ki}" cy="{k}" r="2.2" fill="#fff"></circle>
            <line class="organ-interactive-path" x1="172" y1="{y_cadera}" x2="{kd}" y2="{k}" stroke="url(#boneSpineGrad)" stroke-width="4" stroke-linecap="round"></line>
            <line x1="{kd}" y1="{k}" x2="{kd + 3}" y2="{Y_TOBILLO:.0f}" stroke="rgba(190, 235, 250, 0.55)" stroke-width="2.6" stroke-linecap="round"></line>
            <circle cx="{kd}" cy="{k}" r="6.5" fill="rgba(189, 133, 12, 0.40)" stroke="var(--c-amber)" stroke-width="1.8" filter="drop-shadow(0 0 7px var(--glow-amber))"></circle>
            <circle cx="{kd}" cy="{k}" r="2.2" fill="#fff"></circle>""")

    return ("""
          <!-- 6. ÓRGANOS INTERACTIVOS (CAPA SUPERIOR) -->
""" + pulmones + viscera + corazon + riñones + cerebro + huesos + "        </g>\n")


if __name__ == "__main__":
    print(informe_proporciones())
    print()
    for nombre, d in construir_rutas().items():
        print(f"{nombre}: {len(d)} caracteres")
    print()
    print("Referencias para anclar órganos y líneas guía (locales / globales +180,+10):")
    for nombre, o in ORGANOS.items():
        if nombre == "rodilla_y":
            print(f"  rodillas       local ({EJE_X - CENTRO_RODILLA:.0f}|{EJE_X + CENTRO_RODILLA:.0f}, {o['cy']:.0f})"
                  f"  global ({EJE_X + CENTRO_RODILLA + 180:.0f}, {o['cy'] + 10:.0f})")
        else:
            print(f"  {nombre:<14} local ({o['cx']:.0f}, {o['cy']:.0f})"
                  f"  global ({o['cx'] + 180:.0f}, {o['cy'] + 10:.0f})")
