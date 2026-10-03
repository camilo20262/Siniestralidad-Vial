"""Construye una sola vez agregados descriptivos nuevos; no modifica el cierre."""
import json
from datetime import datetime, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from dashboard.data import preparar_actores, FLAGS, KEYS, REPORTS
from src.preparacion import USECOLS
from src.rutas import ROOT, sha256_archivo


def main():
    dest = ROOT / 'data/dashboard'
    if dest.exists() and any(dest.iterdir()):
        raise SystemExit('Ya existen agregados. No se sobrescriben automáticamente.')
    source = json.loads((ROOT / 'data/raw/procedencia_excel.json').read_text())
    raw_path = ROOT / source['archivo_local']
    if sha256_archivo(raw_path) != source['sha256_local']:
        raise ValueError('La fuente no coincide con la copia congelada.')
    raw = pd.read_excel(raw_path, sheet_name='Siniestros', usecols=[*USECOLS, *FLAGS.values()])
    actors, events = preparar_actores(raw)
    reg = json.loads((ROOT / 'models/victimas/modelo_principal.json').read_text())
    if sha256_archivo(ROOT / reg['datos']['ruta']) != reg['datos']['sha256']:
        raise ValueError('Dataset principal alterado.')
    grid = pd.read_parquet(ROOT / reg['datos']['ruta'])
    grid['Fecha_Acc'] = pd.to_datetime(grid.Fecha_Acc)
    counts = events.groupby(KEYS).size().rename('Conteo').reset_index()
    comparison = grid.merge(counts, on=KEYS, how='outer', validate='one_to_one')
    if not comparison.Num_Accidentes.eq(comparison.Conteo.fillna(0)).all():
        raise ValueError('Los eventos no reproducen el conteo del dataset cerrado.')
    # Los totales por actor se contrastan con el EDA ya guardado.
    reference = pd.read_csv(ROOT / 'reports/eda_victimas/actores_por_localidad.csv').set_index('Localidad')
    for actor in FLAGS:
        actual = actors[actors.Actor.eq(actor)].groupby('Localidad').Siniestros.sum().reindex(reference.index, fill_value=0)
        if not actual.eq(reference[actor]).all():
            raise ValueError(f'Los conteos de {actor} difieren del EDA.')
    dest.mkdir(parents=True, exist_ok=True)
    actors.to_parquet(dest / 'siniestros_actores.parquet', index=False)
    files = ['data/dashboard/siniestros_actores.parquet', 'data/reference/localidades_sdp_referencia.geojson',
             *[f'reports/evaluation_victimas/{name}.csv' for name in REPORTS]]
    manifest = {'fecha_utc': datetime.now(timezone.utc).isoformat(), 'fuente_sha256': source['sha256_local'],
                'siniestros': len(events), 'modelo': reg['id_modelo'],
                'unidad': 'Siniestros con participación del actor; categorías no excluyentes, no personas.',
                'valores_indicadores': {k: events[v].fillna('Sin información').value_counts().to_dict() for k,v in FLAGS.items()},
                'archivos': {name: sha256_archivo(ROOT / name) for name in files}}
    (dest / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'siniestros': len(events), 'agregados': len(actors), 'coincide_con_eda': True}, ensure_ascii=False))


if __name__ == '__main__':
    main()
