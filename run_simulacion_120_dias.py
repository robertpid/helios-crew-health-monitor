"""
Script de ejecución para la simulación de series temporales de 120 días.

Simula de forma vectorizada cada signo vital y variable ambiental para:
1. Estación Espacial Internacional (ISS / LEO)
2. Base Lunar (Artemis Base Camp)
3. Nave Espacial (Tránsito en Espacio Profundo a Marte)
4. Base de Marte (Hábitat Marciano en Superficie)

Exporta artefactos analíticos (CSV, Parquet, JSONL) y presenta un resumen comparativo.

Uso:
    python run_simulacion_120_dias.py
    python run_simulacion_120_dias.py --dias 120 --directorio-salida datos_generados
"""

import argparse
import logging
from pathlib import Path
import sys

from helios_simulator.config import LimitesNasaConfig
from helios_simulator.services.multi_habitat_simulator import SimuladorMultihabitat120Dias


def configurar_logging(verbose: bool = False) -> None:
    """Configura el subsistema de logging estándar para auditoría aeroespacial."""
    nivel = logging.DEBUG if verbose else logging.INFO
    formato = "%(asctime)s.%(msecs)03d UTC | %(levelname)-8s | [%(name)s] | %(message)s"
    logging.basicConfig(
        level=nivel,
        format=formato,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def parsear_argumentos() -> argparse.Namespace:
    """Parsea los argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(
        description="Simulador de Telemetría Multihábitat de 120 Días (Space Apps 2026)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--dias",
        type=int,
        default=120,
        help="Duración del período de misión en días o soles.",
    )
    parser.add_argument(
        "--directorio-salida",
        type=str,
        default="datos_generados",
        help="Carpeta donde se almacenarán los archivos CSV, Parquet y JSONL.",
    )
    parser.add_argument(
        "--semilla",
        type=int,
        default=42,
        help="Semilla del generador pseudoaleatorio.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Activa trazas detalladas de depuración.",
    )
    return parser.parse_args()


def main() -> None:
    """Punto de entrada principal para la simulación de 120 días multihábitat."""
    argumentos = parsear_argumentos()
    configurar_logging(verbose=argumentos.verbose)

    logger = logging.getLogger("helios.simulador_120_dias")
    logger.info("================================================================================")
    logger.info("   SIMULADOR DE TELEMETRÍA ESPACIAL DE 120 DÍAS - CUATRO HÁBITATS (NASA RIDGE)  ")
    logger.info("   Estándar: NASA-STD-3001 | ISS vs Luna vs Nave Tránsito vs Base Marte          ")
    logger.info("================================================================================")

    simulador = SimuladorMultihabitat120Dias(
        config_limites=LimitesNasaConfig(),
        semilla_aleatoria=argumentos.semilla,
    )

    logger.info("Iniciando generación de datos vectorizados para un período de %d días...", argumentos.dias)
    master_df = simulador.simular_todos_los_habitats(total_dias=argumentos.dias)

    # Exportación a disco en formatos estructurados
    rutas = simulador.exportar_dataset(
        df=master_df,
        directorio_destino=argumentos.directorio_salida,
        nombre_base=f"telemetria_{argumentos.dias}_dias_cuatro_habitats",
    )

    # Resumen comparativo de fin de misión
    tabla_resumen = simulador.generar_resumen_comparativo(master_df)

    logger.info("--------------------------------------------------------------------------------")
    logger.info("RESUMEN COMPARATIVO AL DÍA %d DE MISIÓN:", argumentos.dias)
    logger.info("--------------------------------------------------------------------------------")
    registros_resumen = tabla_resumen.reset_index().to_dict(orient="records")
    for reg in registros_resumen:
        logger.info(
            "Hábitat: %-18s | g=%.3f | Retardo=%5.1f min | Rad.Acum=%6.1f mSv (%5.1f%% carrera) | P.Ósea=%4.1f%% | Fatiga=%2d d | SANS=%2d d",
            reg["entorno_mision"],
            reg["gravedad_g"],
            reg["retardo_tierra_min"],
            reg["radiacion_final_mSv"],
            reg["presupuesto_radiacion_final_pct"],
            reg["perdida_osea_final_pct"],
            int(reg["dias_con_alerta_fatiga"]),
            int(reg["dias_con_sans_vision"]),
        )

    logger.info("--------------------------------------------------------------------------------")
    logger.info("Artefactos generados exitosamente:")
    for formato, ruta in rutas.items():
        logger.info(" -> [%s]: %s (Tamaño: %d bytes)", formato.upper(), Path(ruta).resolve(), Path(ruta).stat().st_size)
    logger.info("================================================================================")


if __name__ == "__main__":
    main()
