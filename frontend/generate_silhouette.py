"""
Generator of the H.E.L.I.O.S. holographic anatomical silhouette.

Instead of hand-editing SVG paths thousands of characters long, the figure is
built from a table of anatomical references using the 7.5-head canon, so the
proportions are correct by construction and verifiable.

Each body part is defined as a PROFILE: a list of (y, half-width). The profile is
mirrored about the central axis and smoothed with Catmull-Rom converted to cubic
Bezier curves, producing a continuous contour without the kinks of the previous
figure.

Local canvas of the anatomical group: 320 x 500, central axis at x = 160.
"""

from typing import Final

AXIS_X: Final[float] = 160.0

# ======================================================================================
# 7.5-HEAD CANON
# Crown y = 14, sole of the foot y = 474  ->  height 460, head module H = 61.3
# ======================================================================================
Y_CROWN: Final[float] = 14.0
Y_SOLE: Final[float] = 474.0
H: Final[float] = (Y_SOLE - Y_CROWN) / 7.5

Y_CHIN: Final[float] = Y_CROWN + 1.00 * H     #  75.3
Y_SHOULDER: Final[float] = Y_CROWN + 1.40 * H  #  99.8
Y_CHEST: Final[float] = Y_CROWN + 2.00 * H     # 136.6
Y_WAIST: Final[float] = Y_CROWN + 3.00 * H     # 198.0
Y_HIP: Final[float] = Y_CROWN + 3.50 * H       # 228.6
Y_CROTCH: Final[float] = Y_CROWN + 3.75 * H    # 243.9
Y_KNEE: Final[float] = Y_CROWN + 5.50 * H      # 351.2
Y_ANKLE: Final[float] = Y_CROWN + 7.20 * H     # 455.4


def catmull_rom_to_bezier(points: list[tuple[float, float]], closed: bool = True) -> str:
    """
    Converts a polyline into a smooth SVG path using uniform Catmull-Rom.

    Args:
        points: Control vertices in traversal order.
        closed: Whether the curve should close on itself.

    Returns:
        'd' data string for a <path> element.
    """
    n = len(points)
    if n < 3:
        return ""

    def at(i: int) -> tuple[float, float]:
        if closed:
            return points[i % n]
        return points[max(0, min(n - 1, i))]

    parts = [f"M{points[0][0]:.1f} {points[0][1]:.1f}"]
    total = n if closed else n - 1
    for i in range(total):
        p0, p1, p2, p3 = at(i - 1), at(i), at(i + 1), at(i + 2)
        # Tension 1/6: standard Catmull-Rom tangent
        c1 = (p1[0] + (p2[0] - p0[0]) / 6.0, p1[1] + (p2[1] - p0[1]) / 6.0)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6.0, p2[1] - (p3[1] - p1[1]) / 6.0)
        parts.append(
            f"C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}"
        )
    if closed:
        parts.append("Z")
    return " ".join(parts)


def profile_to_contour(
    profile: list[tuple[float, float]], axis: float = AXIS_X
) -> list[tuple[float, float]]:
    """
    Expands a profile (y, half-width) into a closed symmetric contour.

    It walks the right side top to bottom and returns along the left side.
    """
    right = [(axis + w, y) for y, w in profile]
    left = [(axis - w, y) for y, w in reversed(profile)]
    return right + left


def offset_profile(
    profile: list[tuple[float, float]], center: float
) -> list[tuple[float, float]]:
    """Expands a profile around its own axis (for limbs)."""
    return profile_to_contour(profile, axis=center)


# ======================================================================================
# ANATOMICAL PROFILES  (y, half-width)
# ======================================================================================

# Head: cranial oval with mandibular tapering
HEAD: Final[list[tuple[float, float]]] = [
    (Y_CROWN, 3.0),
    (Y_CROWN + 6, 16.0),
    (Y_CROWN + 16, 23.0),
    (Y_CROWN + 30, 24.0),
    (Y_CROWN + 44, 20.0),
    (Y_CHIN - 4, 12.0),
    (Y_CHIN, 4.0),
]

# Neck and torso: shoulders -> rib cage -> waist -> hip
TORSO: Final[list[tuple[float, float]]] = [
    (Y_CHIN - 2, 11.0),        # base of the neck
    (Y_CHIN + 10, 13.0),       # trapezius
    (Y_SHOULDER, 46.0),        # shoulder line (2H wingspan)
    (Y_SHOULDER + 14, 49.0),   # deltoid
    (Y_CHEST, 44.0),           # pectoral
    (Y_CHEST + 28, 38.0),      # costal arch
    (Y_WAIST, 31.0),           # waist (narrowest point)
    (Y_HIP, 40.0),             # iliac crest
    (Y_CROTCH, 37.0),          # pelvis
]

# Arm: deltoid -> biceps -> elbow -> forearm -> wrist -> hand
ARM: Final[list[tuple[float, float]]] = [
    (Y_SHOULDER + 4, 15.0),
    (Y_CHEST, 14.0),           # biceps
    (Y_CHEST + 34, 11.5),      # elbow
    (Y_WAIST + 6, 10.0),       # forearm
    (Y_HIP + 10, 7.5),         # wrist
    (Y_CROTCH + 16, 9.5),      # hand
    (Y_CROTCH + 34, 5.0),      # fingers
]
ARM_OFFSET: Final[float] = 48.0   # displacement from the axis

# Leg: thigh -> knee -> calf -> ankle -> foot
LEG: Final[list[tuple[float, float]]] = [
    (Y_CROTCH - 12, 19.0),     # thigh insertion
    (Y_CROTCH + 30, 18.0),     # thigh
    (Y_KNEE - 40, 15.0),       # above the knee
    (Y_KNEE, 13.0),            # knee
    (Y_KNEE + 34, 14.0),       # calf
    (Y_ANKLE - 30, 8.5),       # lower calf
    (Y_ANKLE, 6.5),            # ankle
    (Y_SOLE - 4, 8.0),         # instep
]
# Enough separation so both legs do not merge at the central axis.
LEG_OFFSET: Final[float] = 22.0


def build_paths() -> dict[str, str]:
    """Generates every 'd' path of the anatomical figure."""
    return {
        "head": catmull_rom_to_bezier(profile_to_contour(HEAD)),
        "torso": catmull_rom_to_bezier(profile_to_contour(TORSO)),
        "left_arm": catmull_rom_to_bezier(offset_profile(ARM, AXIS_X - ARM_OFFSET)),
        "right_arm": catmull_rom_to_bezier(offset_profile(ARM, AXIS_X + ARM_OFFSET)),
        "left_leg": catmull_rom_to_bezier(offset_profile(LEG, AXIS_X - LEG_OFFSET)),
        "right_leg": catmull_rom_to_bezier(offset_profile(LEG, AXIS_X + LEG_OFFSET)),
    }


def proportions_report() -> str:
    """Checks that the figure respects the canon and reports the dimensions."""
    height = Y_SOLE - Y_CROWN
    # The biacromial wingspan is measured at the outer edge of the deltoid, which
    # is defined by the arm, not the torso.
    upper_arm_half_width = ARM[0][1]
    shoulder_wingspan = (ARM_OFFSET + upper_arm_half_width) * 2
    leg_separation = (LEG_OFFSET - max(w for _, w in LEG)) * 2
    lines = [
        f"Head module H           : {H:.1f} u",
        f"Total height            : {height:.1f} u  ({height / H:.2f} heads)",
        f"Biacromial wingspan     : {shoulder_wingspan:.1f} u  ({shoulder_wingspan / H:.2f} H · canon 2.0)",
        f"Separation between legs : {leg_separation:.1f} u  ({'positive clearance' if leg_separation > 0 else 'THEY OVERLAP'})",
        f"Crotch (midpoint)       : y={Y_CROTCH:.1f}  ({(Y_CROTCH - Y_CROWN) / height * 100:.1f}% of the height · canon 50%)",
        f"Knee                    : y={Y_KNEE:.1f}  ({(Y_KNEE - Y_CROWN) / H:.2f} H · canon 5.5)",
        f"Waist / shoulder        : {min(w for y, w in TORSO[2:]) / max(w for y, w in TORSO):.2f}  (canon ~0.63)",
    ]
    return "\n".join(lines)


# ======================================================================================
# ORGAN REFERENCES, REALIGNED TO THE NEW CANON
# The previous figure placed the crotch at 61.5% of the height (canon 50%), so
# every viscera hung too low relative to the thorax.
# ======================================================================================
ORGANS: Final[dict[str, dict[str, float]]] = {
    "brain":     {"cx": 160, "cy": 44,  "rx": 26, "ry": 24},
    "lungs":     {"cx": 160, "cy": 138, "rx": 32, "ry": 30},
    "heart":     {"cx": 163, "cy": 141, "rx": 16, "ry": 18},
    "hydration": {"cx": 160, "cy": 187, "rx": 26, "ry": 12},
    "knee_y":    {"cx": 0,   "cy": 351, "rx": 0,  "ry": 0},
}
KNEE_OFFSET: Final[float] = LEG_OFFSET  # 22 u on each side of the axis


def _mult(d: str, fields: dict[str, float]) -> str:
    """Interpolates numeric references into a path template."""
    return d.format(**fields)


def build_anatomical_group() -> str:
    """Emits the complete SVG group: halo, silhouette, skeleton and organs."""
    r = build_paths()
    body_parts = [r["head"], r["torso"], r["left_arm"], r["right_arm"],
                  r["left_leg"], r["right_leg"]]

    halo = "\n".join(f'              <path d="{d}"></path>' for d in body_parts)
    silhouette = "\n".join(f'              <path d="{d}"></path>' for d in body_parts)
    pattern = "\n".join(f'              <path d="{d}"></path>' for d in body_parts)

    ry, rx = ORGANS["knee_y"]["cy"], KNEE_OFFSET
    k_left, k_right = AXIS_X - rx, AXIS_X + rx

    # --- Segmented spine: cervical, thoracic, lumbar, sacrum ---
    vertebrae = []
    segments = [(Y_CHIN + 2, Y_SHOULDER, 7, 2.0, "#cfeffa"),
                (Y_SHOULDER, Y_WAIST, 12, 2.6, "var(--c-cyan-ink)"),
                (Y_WAIST, Y_HIP, 5, 3.0, "#cfeffa")]
    for y0, y1, n, rad, col in segments:
        for i in range(n):
            y = y0 + (y1 - y0) * (i + 0.5) / n
            vertebrae.append(
                f'              <circle cx="160" cy="{y:.1f}" r="{rad}" fill="{col}"></circle>'
            )
    spine = "\n".join(vertebrae)

    # --- Rib cage: pairs of curved ribs ---
    ribs = []
    for i in range(7):
        y = Y_SHOULDER + 10 + i * 11.5
        width = 26 + i * 2.6 - (0 if i < 5 else (i - 4) * 7)
        drop = 13 + i * 1.2
        ribs.append(
            f'              <path d="M156 {y:.1f} C{160 - width * 0.55:.1f} {y + drop * 0.35:.1f} '
            f'{160 - width:.1f} {y + drop * 0.7:.1f} {160 - width - 3:.1f} {y + drop:.1f}"></path>'
        )
        ribs.append(
            f'              <path d="M164 {y:.1f} C{160 + width * 0.55:.1f} {y + drop * 0.35:.1f} '
            f'{160 + width:.1f} {y + drop * 0.7:.1f} {160 + width + 3:.1f} {y + drop:.1f}"></path>'
        )
    cage = "\n".join(ribs)

    return f"""        <!-- ANATOMICAL SILHOUETTE — generated by frontend/generate_silhouette.py
             7.5-head canon: H={H:.1f}u · wingspan 2.05H · crotch at 50%.
             Do not edit by hand: modify the profile tables and regenerate. -->

        <g id="bodyAnatomyGroup" transform="translate(180, 10)">

          <!-- 1. VOLUMETRIC HALO -->
          <g pointer-events="none" fill="none" stroke="var(--c-cyan)" stroke-width="6"
             opacity="0.16" style="filter:blur(6px);">
{halo}
          </g>

          <!-- 2. BODY SILHOUETTE -->
          <g id="bodyContour" pointer-events="none" fill="url(#bodySkinGrad)"
             stroke="var(--c-cyan-ink)" stroke-width="1.4" stroke-linejoin="round" opacity="0.9">
{silhouette}
          </g>

          <!-- 3. TOMOGRAPHIC SCAN PATTERN -->
          <g pointer-events="none" fill="url(#holoScanLinesPattern)">
{pattern}
          </g>

          <!-- 4. SKELETAL SYSTEM -->
          <g id="skeletalSystem" pointer-events="none" stroke="rgba(190, 235, 250, 0.40)"
             stroke-width="1.1" fill="none">
            <!-- Clavicles -->
            <path d="M160 {Y_SHOULDER + 2:.1f} Q138 {Y_SHOULDER - 1:.1f} 120 {Y_SHOULDER + 8:.1f}" stroke-width="1.5"></path>
            <path d="M160 {Y_SHOULDER + 2:.1f} Q182 {Y_SHOULDER - 1:.1f} 200 {Y_SHOULDER + 8:.1f}" stroke-width="1.5"></path>
            <!-- Sternum -->
            <line x1="160" y1="{Y_SHOULDER + 4:.1f}" x2="160" y2="{Y_CHEST + 24:.1f}" stroke="url(#boneSpineGrad)" stroke-width="2.2"></line>
            <!-- Rib cage -->
            <g opacity="0.5" stroke="rgba(150, 225, 250, 0.55)" stroke-width="1.2">
{cage}
            </g>
            <!-- Pelvic girdle -->
            <path d="M160 {Y_HIP - 4:.1f} C142 {Y_HIP - 12:.1f} 126 {Y_HIP - 8:.1f} 122 {Y_HIP + 6:.1f}
                     C119 {Y_HIP + 18:.1f} 130 {Y_CROTCH + 2:.1f} 142 {Y_CROTCH + 4:.1f}
                     Q152 {Y_CROTCH + 6:.1f} 160 {Y_CROTCH - 2:.1f}
                     Q168 {Y_CROTCH + 6:.1f} 178 {Y_CROTCH + 4:.1f}
                     C190 {Y_CROTCH + 2:.1f} 201 {Y_HIP + 18:.1f} 198 {Y_HIP + 6:.1f}
                     C194 {Y_HIP - 8:.1f} 178 {Y_HIP - 12:.1f} 160 {Y_HIP - 4:.1f} Z"
                  fill="rgba(23, 159, 179, 0.10)" stroke="var(--c-cyan)" stroke-width="1.3"></path>
          </g>

          <g id="spineVertebrae" pointer-events="none">
{spine}
          </g>

          <!-- 5. TOMOGRAPHIC DEPTH RINGS (BACKGROUND LAYER) -->
          <g stroke="rgba(23, 159, 179, 0.28)" stroke-dasharray="2 4" fill="none" pointer-events="none">
            <ellipse cx="160" cy="44" rx="26" ry="7"></ellipse>
            <ellipse cx="160" cy="138" rx="42" ry="10"></ellipse>
            <ellipse cx="160" cy="196" rx="32" ry="8"></ellipse>
            <ellipse cx="{k_left}" cy="{ry}" rx="15" ry="5"></ellipse>
            <ellipse cx="{k_right}" cy="{ry}" rx="15" ry="5"></ellipse>
          </g>
"""


def build_organs() -> str:
    """
    Emits the five interactive organ nodes over the new references.

    Each group keeps exactly its class, data-organ and handlers: the HUD
    controller and the hologram service depend on them.
    The hit geometry is static and hugs the visible shape; the animated layer
    sits inside with pointer-events="none" so the heartbeat does not shift the
    edge under the cursor.
    """
    k = ORGANS["knee_y"]["cy"]
    ki, kd = AXIS_X - KNEE_OFFSET, AXIS_X + KNEE_OFFSET
    y_hip = Y_HIP + 14

    def node(organ: str, body: str, node_id: str = "") -> str:
        """The id is mandatory where the controller looks it up by getElementById."""
        attr_id = f' id="{node_id}"' if node_id else ""
        return (
            f'          <g class="organ-node"{attr_id} data-organ="{organ}"\n'
            f'             onmouseenter="window.hudController.focusOrgan(\'{organ}\')"\n'
            f'             onmouseleave="window.hudController.unfocusOrgan()">\n'
            f'{body}\n'
            f'          </g>\n'
        )

    lungs = node("lungs", f"""            <ellipse cx="140" cy="139" rx="16" ry="31" fill="transparent" pointer-events="all"></ellipse>
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

    viscera = ("""          <g id="abdominalViscera" opacity="0.6" pointer-events="none">
            <path d="M136 168 C136 163 147 163 156 167 C156 178 152 187 143 188 C138 188 136 179 136 168 Z"
                  fill="rgba(189, 133, 12, 0.20)" stroke="var(--c-amber)" stroke-width="1"></path>
            <path d="M165 167 C173 165 180 169 180 177 C180 184 175 191 168 191 C164 191 164 184 165 174 Z"
                  fill="rgba(23, 159, 179, 0.16)" stroke="var(--c-cyan)" stroke-width="1"></path>
          </g>\n""")

    heart = node("heart", f"""            <ellipse cx="163" cy="142" rx="16" ry="20" fill="transparent" pointer-events="all"></ellipse>
            <g class="pulse-organ-heart" pointer-events="none">
              <path d="M159 126 C159 119 164 115 169 117 C173 119 173 123 171 128" stroke="var(--c-red-ink)" stroke-width="2.2" fill="none"></path>
              <line x1="165" y1="116" x2="165" y2="110" stroke="var(--c-red-ink)" stroke-width="1.4"></line>
              <path class="organ-interactive-path" d="M157 130 C151 128 148 133 148 140 C148 148 154 157 160 164 C162 166 165 166 167 162 C173 154 178 145 176 135 C174 129 168 127 163 131 C161 132 159 132 157 130 Z"
                    fill="url(#organHeartGrad)" stroke="var(--c-red)" stroke-width="1.6"
                    filter="drop-shadow(0 0 10px var(--glow-red))"></path>
              <path d="M162 134 Q163 144 160 155 M162 141 Q168 147 171 153" stroke="#ffe9a0" stroke-width="1" fill="none" opacity="0.8"></path>
              <circle cx="161" cy="145" r="2.6" fill="#ffffff" filter="drop-shadow(0 0 5px #fff)"></circle>
            </g>""", node_id="nodeHeart")

    kidneys = node("hydration", """            <ellipse cx="160" cy="187" rx="26" ry="12" fill="transparent" pointer-events="all"></ellipse>
            <path class="organ-interactive-path" d="M143 179 C147 179 149 183 149 188 C149 193 146 196 142 196 C139 196 138 191 139 186 C139 182 141 179 143 179 Z"
                  fill="url(#kidneyGrad)" stroke="var(--c-blue)" stroke-width="1.3"
                  filter="drop-shadow(0 0 6px var(--glow-blue))"></path>
            <circle cx="144" cy="178" r="1.9" fill="var(--c-amber)"></circle>
            <path class="organ-interactive-path" d="M177 179 C173 179 171 183 171 188 C171 193 174 196 178 196 C181 196 182 191 181 186 C181 182 179 179 177 179 Z"
                  fill="url(#kidneyGrad)" stroke="var(--c-blue)" stroke-width="1.3"
                  filter="drop-shadow(0 0 6px var(--glow-blue))"></path>
            <circle cx="176" cy="178" r="1.9" fill="var(--c-amber)"></circle>""")

    brain = node("brain", """            <circle cx="160" cy="44" r="25" fill="transparent" pointer-events="all"></circle>
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

    bones = node("bones", f"""            <circle cx="{ki}" cy="{k}" r="21" fill="transparent" pointer-events="all"></circle>
            <circle cx="{kd}" cy="{k}" r="21" fill="transparent" pointer-events="all"></circle>
            <line class="organ-interactive-path" x1="148" y1="{y_hip}" x2="{ki}" y2="{k}" stroke="url(#boneSpineGrad)" stroke-width="4" stroke-linecap="round"></line>
            <line x1="{ki}" y1="{k}" x2="{ki - 3}" y2="{Y_ANKLE:.0f}" stroke="rgba(190, 235, 250, 0.55)" stroke-width="2.6" stroke-linecap="round"></line>
            <circle cx="{ki}" cy="{k}" r="6.5" fill="rgba(189, 133, 12, 0.40)" stroke="var(--c-amber)" stroke-width="1.8" filter="drop-shadow(0 0 7px var(--glow-amber))"></circle>
            <circle cx="{ki}" cy="{k}" r="2.2" fill="#fff"></circle>
            <line class="organ-interactive-path" x1="172" y1="{y_hip}" x2="{kd}" y2="{k}" stroke="url(#boneSpineGrad)" stroke-width="4" stroke-linecap="round"></line>
            <line x1="{kd}" y1="{k}" x2="{kd + 3}" y2="{Y_ANKLE:.0f}" stroke="rgba(190, 235, 250, 0.55)" stroke-width="2.6" stroke-linecap="round"></line>
            <circle cx="{kd}" cy="{k}" r="6.5" fill="rgba(189, 133, 12, 0.40)" stroke="var(--c-amber)" stroke-width="1.8" filter="drop-shadow(0 0 7px var(--glow-amber))"></circle>
            <circle cx="{kd}" cy="{k}" r="2.2" fill="#fff"></circle>""")

    return ("""
          <!-- 6. INTERACTIVE ORGANS (TOP LAYER) -->
""" + lungs + viscera + heart + kidneys + brain + bones + "        </g>\n")


if __name__ == "__main__":
    print(proportions_report())
    print()
    for name, d in build_paths().items():
        print(f"{name}: {len(d)} characters")
    print()
    print("References to anchor organs and leader lines (local / global +180,+10):")
    for name, o in ORGANS.items():
        if name == "knee_y":
            print(f"  knees          local ({AXIS_X - KNEE_OFFSET:.0f}|{AXIS_X + KNEE_OFFSET:.0f}, {o['cy']:.0f})"
                  f"  global ({AXIS_X + KNEE_OFFSET + 180:.0f}, {o['cy'] + 10:.0f})")
        else:
            print(f"  {name:<14} local ({o['cx']:.0f}, {o['cy']:.0f})"
                  f"  global ({o['cx'] + 180:.0f}, {o['cy'] + 10:.0f})")
