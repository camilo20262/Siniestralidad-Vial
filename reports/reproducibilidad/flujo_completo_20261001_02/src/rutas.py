"""Rutas del checkout que contiene este módulo; independientes del directorio activo."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_FILE = ROOT / 'data/raw/base-anuario-de-siniestralidad-2024.xlsx'
DATASET_FILE = ROOT / 'data/processed/dataset_victimas_localidad_franja_fecha.parquet'


def sha256_archivo(path):
    from hashlib import sha256
    digest = sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()
