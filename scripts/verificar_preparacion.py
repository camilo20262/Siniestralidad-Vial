"""Reconstruye en memoria desde el Excel y compara exactamente; nunca sobrescribe."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from src.preparacion import USECOLS, preparar_dataset
from src.rutas import RAW_FILE, DATASET_FILE, sha256_archivo


def verificar():
    antes = {str(p): sha256_archivo(p) for p in (RAW_FILE, DATASET_FILE)}
    original = pd.read_excel(RAW_FILE, sheet_name='Siniestros', usecols=USECOLS)
    reconstruido = preparar_dataset(original)
    oficial = pd.read_parquet(DATASET_FILE)
    pd.testing.assert_frame_equal(reconstruido, oficial, check_exact=True)
    assert antes == {str(p): sha256_archivo(p) for p in (RAW_FILE, DATASET_FILE)}
    return {'resultado': 'correcto', 'filas': len(reconstruido), 'columnas': len(reconstruido.columns),
            'igualdad': 'exacta: valores, etiquetas, orden y tipos', 'archivos_sobrescritos': 0,
            'modelos_reentrenados': 0, 'sha256_dataset': antes[str(DATASET_FILE)]}


if __name__ == '__main__':
    print(json.dumps(verificar(), ensure_ascii=False, indent=2))
