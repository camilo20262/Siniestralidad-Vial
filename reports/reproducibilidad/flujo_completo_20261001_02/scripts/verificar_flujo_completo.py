"""Reconstruye 02B → 03B → 04B → 04C → 05B → dashboard en una copia nueva.

Reentrena únicamente en la copia. No promueve modelos ni despliega públicamente.
La comprobación HTTP no sustituye una revisión visual ni la aceptación por usuarios.
"""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import reproducir_cadena_aislada as chain

NAMES = ['02B_EDA_y_Analisis_Espacial_Con_Victimas.ipynb', *chain.NAMES]
EXTRA_INPUTS = [
    'data/raw/procedencia_excel.json',
    'data/reference/localidades_sdp_referencia.geojson',
    'data/reference/localidades_sdp_referencia_metadata.json',
    '.python-version', 'scripts/preparar_dashboard.py',
    'scripts/verificar_dashboard.py', 'scripts/verificar_dashboard_http.py',
    'scripts/verificar_flujo_completo.py', 'scripts/reproducir_cadena_aislada.py']


def destination(name):
    if not name or name in {'.', '..'} or '/' in name or '\\' in name or Path(name).name != name:
        raise ValueError('Use un nombre de carpeta, no una ruta.')
    run = ROOT/'reports/reproducibilidad'/name
    if run.exists():
        raise FileExistsError(f'No se reutilizan ni sobrescriben ensayos: {run}')
    return run


def preflight():
    for relative in [*EXTRA_INPUTS, 'data/raw/base-anuario-de-siniestralidad-2024.xlsx']:
        if not (ROOT/relative).is_file():
            raise FileNotFoundError(relative)
    source = json.loads((ROOT/'data/raw/procedencia_excel.json').read_text())
    if chain.digest(ROOT/source['archivo_local']) != source['sha256_local']:
        raise ValueError('Excel ausente, puntero LFS o fuente alterada.')
    geo = json.loads((ROOT/'data/reference/localidades_sdp_referencia_metadata.json').read_text())
    if chain.digest(ROOT/'data/reference/localidades_sdp_referencia.geojson') != geo['sha256']:
        raise ValueError('La cartografía no coincide con la instantánea registrada.')


def run_script(run, script, *arguments):
    chain.announce(run, f'Ejecutando {script}')
    log_path = run/(Path(script).stem+'.log')
    with log_path.open('x') as log:
        subprocess.run([str(run/'.venv/bin/python'), str(run/script), *arguments], cwd=run,
                       env={**os.environ, 'SINIESTRALIDAD_ROOT': str(run)},
                       stdout=log, stderr=subprocess.STDOUT, check=True, timeout=600)


def compare_eda(run):
    folder = Path('reports/eda_victimas')
    expected = {p.name for p in (ROOT/folder).glob('*.csv')}
    rebuilt = {p.name for p in (run/folder).glob('*.csv')}
    if not expected or expected != rebuilt:
        raise ValueError(f'Inventario EDA distinto: faltan {expected-rebuilt}; sobran {rebuilt-expected}')
    tables = [chain.compare_table(run, str(folder/name)) for name in sorted(expected)]
    checks = json.loads((run/folder/'verificacion_actividad_3_1.json').read_text())
    official = json.loads((ROOT/folder/'verificacion_actividad_3_1.json').read_text())
    figures = sorted(p.name for p in (run/folder).glob('*.png'))
    expected_figures = sorted(p.name for p in (ROOT/folder).glob('*.png'))
    same_conclusion = (run/folder/'conclusion_ejecutiva.md').read_text() == (ROOT/folder/'conclusion_ejecutiva.md').read_text()
    return {'tablas': tables, 'controles_iguales': checks == official,
            'conclusion_igual': same_conclusion, 'figuras_generadas': figures,
            'inventario_figuras_igual': figures == expected_figures,
            'nota_figuras': 'Inventario verificado; no se exige identidad de píxeles.',
            'equivalente': all(t['equivalente'] for t in tables) and checks == official
                          and same_conclusion and figures == expected_figures}


def equivalent(result):
    return (all(x['equivalente'] for x in result['tablas'])
            and all(all(x['coincidencias'].values()) for x in result['seleccion'])
            and all(x['mismo_esquema'] and x['mismos_hiperparametros'] for x in result['modelos']))


def execute(run):
    stages = []
    result = {'estado': 'en_progreso', 'alcance': 'Reconstrucción aislada con reentrenamiento y HTTP local'}
    try:
        preflight()
        chain.setup(run, names=NAMES, extra_inputs=EXTRA_INPUTS, extra_folders=['dashboard'])
        for name in NAMES:
            if name.startswith('05B'):
                chain.local_registry(run)
            stages.append(chain.execute_notebook(run, name))
            chain.write_json(run/'ejecuciones_notebooks.json', stages)
            if name.startswith('03B'):
                relative = Path('data/processed/dataset_victimas_localidad_franja_fecha.parquet')
                actual, expected = chain.pd.read_parquet(run/relative), chain.pd.read_parquet(ROOT/relative)
                chain.pd.testing.assert_frame_equal(actual, expected, check_exact=True)
                result['dataset'] = {'coincidencia_exacta': True, 'filas': len(actual), 'columnas': len(actual.columns)}
                chain.write_json(run/'comparacion_dataset.json', result['dataset'])
        # Incorporar ahora las evidencias de 05B regeneradas; nunca copiarlas del oficial.
        chain.local_registry(run)
        result['eda'] = compare_eda(run)
        result['modelado_evaluacion'] = chain.compare_results(run)
        chain.write_json(run/'comparacion_eda.json', result['eda'])
        if not result['eda']['equivalente'] or not equivalent(result['modelado_evaluacion']):
            raise ValueError('La reconstrucción difiere; no se valida el dashboard contra artefactos divergentes.')
        run_script(run, 'scripts/preparar_dashboard.py')
        result['agregados_dashboard'] = chain.compare_table(run, 'data/dashboard/siniestros_actores.parquet',
                                                         ['Fecha_Acc', 'Localidad', 'Franja_Horaria', 'Actor'])
        if not result['agregados_dashboard']['equivalente']:
            raise ValueError('Agregados del dashboard distintos al cierre.')
        run_script(run, 'scripts/verificar_dashboard.py', '--salida', str(run/'verificacion_dashboard.json'))
        result['dashboard'] = json.loads((run/'verificacion_dashboard.json').read_text())
        run_script(run, 'scripts/verificar_dashboard_http.py', '--salida', str(run/'verificacion_http.json'))
        result['http'] = json.loads((run/'verificacion_http.json').read_text())
        result['estado'] = 'flujo_completo_verificado'
        result['revision_visual'] = 'No incluida en la comprobación automática HTTP; registrar por separado.'
    except Exception:
        result['estado'] = 'error'
        result['detalle'] = traceback.format_exc()
        print(result['detalle'], flush=True)
    finally:
        # Si el destino ya existía, main lo rechaza antes de llegar aquí.
        if run.exists():
            before_path = run/'integridad_oficial_antes.json'
            if before_path.exists():
                before = json.loads(before_path.read_text())
                after = chain.protected_snapshot()
                changed = [p for p, h in before.items() if after.get(p) != h]
                added = sorted(set(after)-set(before))
                result.update(oficiales_intactos=not changed and not added,
                              archivos_oficiales_comprobados=len(before),
                              archivos_oficiales_modificados=changed, archivos_oficiales_creados=added)
                if changed or added:
                    result['estado'] = 'error_integridad_oficial'
            result['ejecuciones'] = stages
            chain.write_json(run/'resultado.json', result)
            chain.announce(run, result['estado'])
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-name', default=datetime.now().strftime('flujo_completo_%Y%m%d_%H%M%S'))
    args = parser.parse_args()
    run = destination(args.run_name)
    result = execute(run)
    print('CARPETA_RESULTADOS=' + str(run), flush=True)
    raise SystemExit(0 if result['estado'] == 'flujo_completo_verificado' else 1)
