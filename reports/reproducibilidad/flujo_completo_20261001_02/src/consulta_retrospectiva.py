"""Consulta sin interfaz de casos 2023–2024 ya preparados por 03B.

No incorpora datos nuevos ni calcula pronósticos para fechas futuras. Reutiliza
históricos observados, verifica el dataset registrado y aplica el modelo cerrado.
"""
from dataclasses import dataclass
import re
import pandas as pd
from src.modelo_principal import ModeloPrincipal, cargar_modelo_principal
from src.rutas import ROOT, sha256_archivo


ALCANCE_CONSULTA = (
    'Consulta retrospectiva de casos históricos preparados; '
    'no es un pronóstico para fechas nuevas ni una validación prospectiva.'
)
ADVERTENCIA_SCORE = (
    'El score es una puntuación relativa de priorización, no una probabilidad '
    'calibrada de alto riesgo ni de sufrir un accidente. Uso académico, no operativo.'
)


@dataclass
class ConsultaRetrospectiva:
    modelo: ModeloPrincipal
    datos: pd.DataFrame

    def consultar(self, fecha, localidad, franja):
        if isinstance(fecha, str) and not re.fullmatch(r'\d{4}-\d{2}-\d{2}', fecha):
            raise ValueError('Fecha inválida; use AAAA-MM-DD sin hora ni zona horaria.')
        try:
            fecha = pd.Timestamp(fecha)
        except (TypeError, ValueError) as exc:
            raise ValueError('Fecha inválida; use AAAA-MM-DD.') from exc
        if pd.isna(fecha) or fecha.tzinfo is not None or fecha != fecha.normalize():
            raise ValueError('La fecha debe ser un día sin hora ni zona horaria.')
        # El subconjunto test es la autoridad de fechas disponibles, no se extrapola.
        data = self.datos[self.datos.Periodo.eq('test')]
        fechas = pd.to_datetime(data.Fecha_Acc)
        if data.empty or not fechas.min() <= fecha <= fechas.max():
            raise ValueError('Fecha fuera del periodo retrospectivo disponible (2023–2024).')
        fila = data[(fechas == fecha) & data.Localidad.eq(localidad) & data.Franja_Horaria.eq(franja)]
        if len(fila) != 1:
            raise ValueError('La consulta debe identificar un único caso de localidad y franja válidas.')
        resultado = self.modelo.predecir(fila)
        columnas = ['Fecha_Acc', *self.modelo.registro['variables']]
        salida = fila[columnas].copy()
        for c in resultado:
            salida[c] = resultado[c]
        registro = self.modelo.registro
        evaluacion = registro['datos']['evaluacion']
        salida['Umbral_Score'] = registro['decision']['umbral_score']
        # Columnas, no DataFrame.attrs: la trazabilidad viaja en cada registro JSON/CSV.
        salida['Id_Modelo'] = registro['id_modelo']
        salida['Version_Modelo'] = registro['version']
        salida['Tipo_Evaluacion'] = evaluacion['tipo']
        salida['Evaluacion_Desde'] = evaluacion['desde']
        salida['Evaluacion_Hasta'] = evaluacion['hasta']
        salida['Alcance_Consulta'] = ALCANCE_CONSULTA
        salida['Advertencia_Score'] = ADVERTENCIA_SCORE
        # No se devuelve el conteo/etiqueta observados como si fueran predicciones.
        return salida


def cargar_consulta():
    modelo = cargar_modelo_principal()
    path = ROOT / modelo.registro['datos']['ruta']
    if sha256_archivo(path) != modelo.registro['datos']['sha256']:
        raise ValueError('El dataset no coincide con la versión registrada.')
    data = pd.read_parquet(path)
    if data.duplicated(['Fecha_Acc', 'Localidad', 'Franja_Horaria']).any():
        raise ValueError('El dataset tiene claves duplicadas.')
    return ConsultaRetrospectiva(modelo, data)
