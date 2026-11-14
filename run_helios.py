"""
Punto de entrada principal para el simulador de telemetría HELIOS.

Orquestador de soporte vital para misiones de espacio profundo hacia Marte (Día 120).
Inyecta un payload JSON cada 2 segundos al servidor Redis local en 'buzon_telemetria_tierra'.

Uso:
    python run_helios.py
    python run_helios.py --redis-host 127.0.0.1 --dia-mision 120 --intervalo 2.0
    python run_helios.py --simular-demo-crisis
"""

import argparse
import logging
import sys

from helios_simulator.config import LimitesNasaConfig, MisionConfig, RedisConfig
from helios_simulator.infrastructure.redis_publisher import RedisTelemetryPublisher
from helios_simulator.presentation.orchestrator import TelemetriaOrchestrator


def configurar_subsistema_logging(nivel_verboso: bool = False) -> None:
    """
    Configura el formateador estándar del módulo logging según las directrices de ingeniería.

    Args:
        nivel_verboso: Si es True, eleva el nivel a DEBUG.
    """
    formato_aeroespacial = (
        "%(asctime)s.%(msecs)03d UTC | %(levelname)-8s | [%(name)s] | %(message)s"
    )
    nivel = logging.DEBUG if nivel_verboso else logging.INFO

    logging.basicConfig(
        level=nivel,
        format=formato_aeroespacial,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )


def parsear_argumentos_mision() -> argparse.Namespace:
    """
    Parsea los parámetros operacionales recibidos por línea de comandos.

    Returns:
        Espacio de nombres con las opciones configuradas.
    """
    parser = argparse.ArgumentParser(
        description="HELIOS Telemetry Simulator - Deep Space Life Support System (NASA-STD-3001)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--redis-host",
        type=str,
        default="127.0.0.1",
        help="Dirección IP o hostname del servidor Redis local.",
    )
    parser.add_argument(
        "--redis-port",
        type=int,
        default=6379,
        help="Puerto de escucha de Redis.",
    )
    parser.add_argument(
        "--redis-canal",
        type=str,
        default="buzon_telemetria_tierra",
        help="Canal Pub/Sub y nombre de buzón en Redis.",
    )
    parser.add_argument(
        "--dia-mision",
        type=int,
        default=120,
        help="Día transcurrido de la misión hacia Marte (por defecto: Día 120).",
    )
    parser.add_argument(
        "--intervalo",
        type=float,
        default=2.0,
        help="Frecuencia de inyección de telemetría en segundos.",
    )
    parser.add_argument(
        "--max-ciclos",
        type=int,
        default=None,
        help="Número máximo de ciclos antes de finalizar (útil para pruebas automatizadas).",
    )
    parser.add_argument(
        "--simular-demo-crisis",
        action="store_true",
        help="Inyecta una secuencia de contingencia severa: pico de CO2, tormenta solar y estrés.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Habilita registros de depuración detallados.",
    )

    return parser.parse_args()


def main() -> None:
    """
    Punto de entrada seguro del productor de telemetría sintética.
    Aplica Inversión de Dependencias (DIP) inyectando el publicador al orquestador.
    """
    argumentos = parsear_argumentos_mision()
    configurar_subsistema_logging(nivel_verboso=argumentos.verbose)

    logger = logging.getLogger("helios_simulator.main")
    logger.info("================================================================================")
    logger.info("  HELIOS DEEP SPACE LIFE SUPPORT TELEMETRY PRODUCER - NASA SPACE APPS 2026")
    logger.info("  Estándar: NASA-STD-3001 | Marco: RIDGE | Destino: Redis ('%s')", argumentos.redis_canal)
    logger.info("================================================================================")

    # 1. Configuración de Capa de Infraestructura
    config_redis = RedisConfig(
        host=argumentos.redis_host,
        port=argumentos.redis_port,
        canal_publicacion=argumentos.redis_canal,
        cola_publicacion=f"{argumentos.redis_canal}_queue",
    )
    publicador_redis = RedisTelemetryPublisher(config=config_redis)

    # 2. Configuración de Dominio y Misión
    config_mision = MisionConfig(
        dia_mision_default=argumentos.dia_mision,
        intervalo_emision_segundos=argumentos.intervalo,
    )
    config_limites = LimitesNasaConfig()

    # 3. Inversión de Dependencias: Inyección del Publicador al Orquestador
    orquestador = TelemetriaOrchestrator(
        publicador=publicador_redis,
        config_mision=config_mision,
        config_limites=config_limites,
    )

    # 4. Modo de Demostración de Contingencia (si se solicita)
    if argumentos.simular_demo_crisis:
        logger.warning("MODO DEMO DE CONTINGENCIA MULTIVARIADA ACTIVADO.")
        orquestador.inicializar_enlaces()
        payload_crisis = orquestador.producir_muestra(
            forzar_pico_co2=True,
            forzar_tormenta_solar=True,
            forzar_deficiencia_sueno=True,
            forzar_taquicardia=True,
            forzar_incongruencia=True,
        )
        publicador_redis.publicar_telemetria(payload_crisis)
        logger.info("Muestra de contingencia inyectada con éxito. Código de alertas:")
        for alerta in payload_crisis.evaluaciones_preliminares:
            logger.warning(" -> [%s] %s: %s", alerta.nivel.value, alerta.codigo, alerta.descripcion)

    # 5. Ejecución del Bucle Continuo (cada 2 segundos)
    orquestador.ejecutar_bucle(max_ciclos=argumentos.max_ciclos)


if __name__ == "__main__":
    main()
