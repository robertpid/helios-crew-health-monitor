"""
Inyecta la silueta generada en el componente de la Ventana 1.

Sustituye el bloque <g id="bodyAnatomyGroup"> completo y recalcula las líneas
guía para que sus anclajes coincidan con las nuevas referencias anatómicas.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from generar_silueta import (  # noqa: E402
    EJE_X,
    CENTRO_RODILLA,
    ORGANOS,
    construir_grupo_anatomico,
    construir_organos,
)

RUTA = Path(__file__).resolve().parent / "components" / "view_biomedical.html"
DESPLAZAMIENTO = (180, 10)  # transform del grupo anatómico

# Retícula del marco (lienzo 680x500). La figura canónica ocupa x 277..403, más
# estrecha que la anterior, así que las tarjetas se ensanchan y se acercan para
# no dejar huecos muertos: canal izq. x 10..242, canal der. x 438..670.
TERMINAL_IZQ, TERMINAL_DER = 248, 432
BUS_IZQ = 262


def g(x: float, y: float) -> tuple[float, float]:
    """Convierte coordenadas locales del cuerpo a coordenadas del lienzo."""
    return x + DESPLAZAMIENTO[0], y + DESPLAZAMIENTO[1]


def construir_lineas_guia() -> tuple[str, dict[str, float]]:
    """Genera las cinco líneas guía ancladas a los órganos y sus alturas de tarjeta."""
    _, y_cer = g(0, ORGANOS["cerebro"]["cy"])
    _, y_cor = g(0, ORGANOS["corazon"]["cy"])
    _, y_hid = g(0, ORGANOS["hidratacion"]["cy"])
    _, y_pul = g(0, ORGANOS["pulmones"]["cy"] - 16)
    _, y_hue = g(0, ORGANOS["rodilla_y"]["cy"])

    x_cer, _ = g(EJE_X - 20, 0)      # lóbulo izquierdo del encéfalo
    x_cor, _ = g(150, 0)             # borde izquierdo del miocardio
    x_hid, _ = g(140, 0)             # riñón izquierdo
    x_pul, _ = g(192, 0)             # lóbulo pulmonar derecho
    x_hue, _ = g(EJE_X + CENTRO_RODILLA, 0)  # rodilla derecha

    # La tarjeta de hidratación baja para no chocar con la de corazón.
    y_tarjeta_hid = y_hid + 40

    bloques = [
        ("cerebro", "var(--c-cyan)", f"{x_cer:.0f},{y_cer:.0f} {TERMINAL_IZQ},{y_cer:.0f}",
         (TERMINAL_IZQ, y_cer), (x_cer, y_cer)),
        ("corazon", "var(--c-red)", f"{x_cor:.0f},{y_cor:.0f} {TERMINAL_IZQ},{y_cor:.0f}",
         (TERMINAL_IZQ, y_cor), (x_cor, y_cor)),
        ("hidratacion", "var(--c-blue)",
         f"{x_hid:.0f},{y_hid:.0f} {BUS_IZQ},{y_hid:.0f} {BUS_IZQ},{y_tarjeta_hid:.0f} {TERMINAL_IZQ},{y_tarjeta_hid:.0f}",
         (TERMINAL_IZQ, y_tarjeta_hid), (x_hid, y_hid)),
        ("pulmones", "var(--c-green)", f"{x_pul:.0f},{y_pul:.0f} {TERMINAL_DER},{y_pul:.0f}",
         (TERMINAL_DER, y_pul), (x_pul, y_pul)),
        ("huesos", "var(--c-amber)", f"{x_hue:.0f},{y_hue:.0f} {TERMINAL_DER},{y_hue:.0f}",
         (TERMINAL_DER, y_hue), (x_hue, y_hue)),
    ]

    partes = ["""        <!-- LÍNEAS GUÍA — generadas por frontend/aplicar_silueta.py
             Canal izquierdo x 10..242 (terminal 248) · cuerpo x 277..403 · canal derecho x 438..670 (terminal 432).
             La ordenada de cada terminal es el centro exacto de su tarjeta. -->"""]
    for organo, color, puntos, (tx, ty), (ax, ay) in bloques:
        partes.append(
            f'        <g class="organ-connector-line" data-organ-line="{organo}" pointer-events="none">\n'
            f'          <polyline points="{puntos}" fill="none" stroke="{color}" stroke-width="2"\n'
            f'                    stroke-linejoin="round" filter="drop-shadow(0 0 5px {color})"></polyline>\n'
            f'          <circle cx="{ax:.0f}" cy="{ay:.0f}" r="4.5" fill="{color}" stroke="#eaf2f8" stroke-width="1.5"></circle>\n'
            f'          <circle cx="{tx:.0f}" cy="{ty:.0f}" r="3" fill="{color}"></circle>\n'
            f'        </g>'
        )

    alturas = {
        "cerebro": y_cer, "corazon": y_cor, "hidratacion": y_tarjeta_hid,
        "pulmones": y_pul, "huesos": y_hue,
    }
    return "\n".join(partes), alturas


def main() -> None:
    texto = RUTA.read_text(encoding="utf-8")

    # El bloque generado se delimita con marcadores propios para que el script
    # sea idempotente: la segunda ejecución reemplaza su propia salida.
    ABRE = "<!-- ===== INICIO BLOQUE GENERADO: SILUETA Y GUÍAS ===== -->"
    CIERRA = "<!-- ===== FIN BLOQUE GENERADO ===== -->"

    lineas, alturas = construir_lineas_guia()
    bloque = (
        f"        {ABRE}\n"
        + construir_grupo_anatomico()
        + construir_organos()
        + "\n"
        + lineas.lstrip("\n")
        + f"\n        {CIERRA}\n      "
    )

    if ABRE in texto:
        ini = texto.index(ABRE) - 8
        fin = texto.index(CIERRA) + len(CIERRA) + len("\n      ")
        texto = texto[:ini] + bloque + texto[fin:]
    else:
        # Primera pasada: delimitar desde el comentario previo al grupo
        # anatómico hasta el cierre del SVG.
        ini = texto.rindex("<!--", 0, texto.index('<g id="bodyAnatomyGroup"'))
        fin = texto.index("</svg>", ini)
        texto = texto[:ini] + bloque + texto[fin:]

    # --- 3. Realinear la altura de cada tarjeta al centro de su guía ---------
    for organo, y in alturas.items():
        pct = y / 500.0 * 100.0
        texto = re.sub(
            rf'(data-organ-card="{organo}"[^>]*?style="top:)[\d.]+%',
            rf'\g<1>{pct:.2f}%',
            texto,
            flags=re.S,
        )

    RUTA.write_text(texto, encoding="utf-8")

    print("Silueta inyectada en view_biomedical.html")
    print("\nAlturas de tarjeta realineadas:")
    for organo, y in alturas.items():
        print(f"  {organo:<14} y={y:6.1f} u  ->  top {y / 500 * 100:.2f}%")


if __name__ == "__main__":
    main()
