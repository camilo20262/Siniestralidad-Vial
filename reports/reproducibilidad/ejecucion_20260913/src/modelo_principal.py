"""Entrada de referencia para la versión académica cerrada del modelo.

Recibe las variables ya preparadas por 03B. No construye históricos ni realiza
pronósticos a varios días; aplica el pipeline y el umbral del registro oficial.
"""

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn

ROOT = Path(__file__).resolve().parents[1]
REGISTRO = ROOT / 'models/victimas/modelo_principal.json'


@dataclass
class ModeloPrincipal:
    pipeline: object
    registro: dict

    def predecir(self, datos: pd.DataFrame) -> pd.DataFrame:
        """Devuelve score y alerta con el mismo índice del DataFrame recibido."""
        columnas = self.registro['variables']
        if not datos.columns.is_unique:
            raise ValueError('Las columnas de entrada deben tener nombres únicos.')
        faltan = sorted(set(columnas) - set(datos.columns))
        if faltan:
            raise ValueError(f'Faltan variables preparadas por 03B: {faltan}')
        X = datos.loc[:, columnas]
        if X.empty or X.isna().any().any():
            raise ValueError('La entrada debe contener filas y no tener valores faltantes.')
        for columna, permitidas in self.registro['categorias'].items():
            if not X[columna].isin(permitidas).all():
                raise ValueError(f'Categorías fuera del universo evaluado en {columna}.')
        numericas = [c for c in columnas if c not in self.registro['categorias']]
        if not all(pd.api.types.is_numeric_dtype(X[c]) for c in numericas):
            raise ValueError('Las variables numéricas deben llegar como números.')
        if not np.isfinite(X[numericas].to_numpy(dtype=float)).all():
            raise ValueError('Las variables numéricas deben ser finitas.')
        binarias = [c for c in numericas if c.startswith(('Es_', 'Sin_Historial_'))]
        if not X[binarias].isin([0, 1]).all().all():
            raise ValueError('Los indicadores deben ser 0 o 1.')
        if not X['Mes'].isin(range(1, 13)).all():
            raise ValueError('Mes debe ser un entero de 1 a 12.')
        historicas = [c for c in numericas if c.startswith('Accidentes_')]
        if (X[historicas] < 0).any().any():
            raise ValueError('Los históricos de siniestros no pueden ser negativos.')
        score = self.pipeline.predict_proba(X)[:, 1]
        decision = self.registro['decision']
        return pd.DataFrame({
            decision['columna_score']: score,
            decision['columna_alerta']: (score >= decision['umbral_score']).astype(int),
        }, index=datos.index)


def cargar_modelo_principal() -> ModeloPrincipal:
    """Carga el artefacto local registrado y comprueba su integridad y esquema."""
    registro = json.loads(REGISTRO.read_text(encoding='utf-8'))
    version = registro['versiones']['entrenamiento_declarado']['scikit_learn']
    if sklearn.__version__ != version:
        raise RuntimeError(f'El artefacto requiere scikit-learn {version}; actual: {sklearn.__version__}.')
    artefacto = ROOT / registro['artefacto']['ruta']
    if sha256(artefacto.read_bytes()).hexdigest() != registro['artefacto']['sha256']:
        raise ValueError('El modelo cambió desde el cierre. Reevalúe y actualice su versión.')
    pipeline = joblib.load(artefacto)
    if pipeline.feature_names_in_.tolist() != registro['variables']:
        raise ValueError('El esquema del pipeline no coincide con el registro.')
    if pipeline.classes_.tolist() != [0, 1]:
        raise ValueError('Las clases del pipeline no son [0, 1].')
    if pipeline.named_steps['modelo'].get_params(deep=False) != registro['hiperparametros']:
        raise ValueError('Los hiperparámetros no coinciden con el registro.')
    return ModeloPrincipal(pipeline=pipeline, registro=registro)
