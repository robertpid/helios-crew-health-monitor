"""
Utilidades matemáticas y de modelado estocástico (DRY).

Centraliza las rutinas de generación de ruido gaussiano, fluctuaciones fisiológicas
y modelos de decaimiento conforme a los lineamientos aeroespaciales de simulación.
"""

import math
import random


def generar_ruido_gaussiano(
    valor_medio: float,
    desviacion_estandar: float,
    limite_inferior: float | None = None,
    limite_superior: float | None = None,
) -> float:
    """
    Genera un valor con distribución normal acotado opcionalmente entre límites.

    Args:
        valor_medio: Media de la distribución.
        desviacion_estandar: Desviación estándar del ruido.
        limite_inferior: Cota inferior opcional.
        limite_superior: Cota superior opcional.

    Returns:
        Valor flotante ajustado y acotado.
    """
    valor = random.gauss(valor_medio, desviacion_estandar)
    if limite_inferior is not None and valor < limite_inferior:
        valor = limite_inferior
    if limite_superior is not None and valor > limite_superior:
        valor = limite_superior
    return round(valor, 3)


def evaluar_probabilidad_evento(probabilidad: float) -> bool:
    """
    Determina si un evento estocástico ocurre dada su probabilidad uniforme.

    Args:
        probabilidad: Valor entre 0.0 y 1.0 que define la tasa de ocurrencia.

    Returns:
        True si el evento se activó, False en caso contrario.
    """
    if probabilidad <= 0.0:
        return False
    if probabilidad >= 1.0:
        return True
    return random.random() < probabilidad


def calcular_perdida_osea_acumulada(
    dia_mision: int,
    tasa_mensual_pct: float = 1.5,
) -> float:
    """
    Calcula la estimación de pérdida ósea acumulada según los estudios del
    Human System Risk Board de la NASA y datos de cosmonautas en Mir (1.0% a 1.5% mensual).

    Fórmula: (dia_mision / 30) * tasa_mensual_pct

    Args:
        dia_mision: Días transcurridos en ambiente de microgravedad.
        tasa_mensual_pct: Porcentaje promedio de pérdida por mes (30 días).

    Returns:
        Porcentaje estimado de pérdida de masa ósea.
    """
    if dia_mision <= 0:
        return 0.0
    perdida = (dia_mision / 30.0) * tasa_mensual_pct
    return round(perdida, 3)


def redondear_telemetria(valor: float, decimales: int = 2) -> float:
    """
    Normaliza y redondea valores de telemetría para transmisión serializada.

    Args:
        valor: Número decimal crudo.
        decimales: Cantidad de dígitos decimales significativos.

    Returns:
        Flotante redondeado.
    """
    if math.isnan(valor) or math.isinf(valor):
        return 0.0
    return round(valor, decimales)
