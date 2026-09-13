"""Reproduce 03B → 04B → 04C → 05B sin escribir en los artefactos oficiales.

Cada ejecución crea una carpeta nueva y un venv sin system-site-packages. Copia
únicamente el Excel y código; todos los datasets, modelos y reportes se generan.
El registro de 05B se adapta a los artefactos reconstruidos, no a los oficiales.
Las comparaciones contra los oficiales se realizan después y por separado.
"""

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback
import venv

import joblib
from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpecManager
import nbformat
from nbclient import NotebookClient
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
NAMES = ['03B_Preparacion_Datos_Con_Victimas.ipynb',
         '04B_Modelado_Con_Victimas.ipynb',
         '04C_Ajuste_Hiperparametros_Con_Victimas.ipynb',
         '05B_Evaluacion_Con_Victimas.ipynb']
SCORE_ATOL = 1e-10


def digest(path):
    h = sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def same_parameters(a, b):
    # XGBoost declara missing=NaN: NaN != NaN no implica un cambio de modelo.
    return json.dumps(a, sort_keys=True, default=str) == json.dumps(b, sort_keys=True, default=str)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str), encoding='utf-8')


def protected_snapshot():
    files = []
    for folder in ['data', 'models', 'notebooks', 'src', 'reports']:
        files += [p for p in (ROOT / folder).rglob('*') if p.is_file()
                  and '__pycache__' not in p.parts
                  and not p.is_relative_to(ROOT / 'reports/reproducibilidad')]
    files += [ROOT / 'requirements.txt', ROOT / 'scripts/verificar_modelo_principal.py']
    return {str(p.relative_to(ROOT)): digest(p) for p in sorted(set(files))}


def announce(run, message, **extra):
    now = datetime.now(timezone.utc).isoformat()
    print(f'[{now}] {message}', flush=True)
    write_json(run / 'estado.json', {'momento_utc': now, 'etapa': message, **extra})


def setup(run):
    run.mkdir(parents=True, exist_ok=False)
    write_json(run / 'integridad_oficial_antes.json', protected_snapshot())
    for name in ['notebooks', 'data/raw', 'models/victimas', 'reports', 'scripts', 'src', 'runtime/kernels/repro']:
        (run / name).mkdir(parents=True, exist_ok=True)
    raw = Path('data/raw/base-anuario-de-siniestralidad-2024.xlsx')
    shutil.copy2(ROOT / raw, run / raw)
    # Una copia real, no enlaces hacia archivos oficiales que pudieran alterarse.
    (run / raw).chmod(0o444)
    for folder in ['src', 'scripts']:
        names = list((ROOT / folder).glob('*.py')) if folder == 'src' else [ROOT / 'scripts/verificar_modelo_principal.py']
        for p in names:
            shutil.copy2(p, run / folder / p.name)
    shutil.copy2(ROOT / 'requirements.txt', run / 'requirements.txt')
    provenance = []
    for name in NAMES:
        original = ROOT / 'notebooks' / name
        nb = nbformat.read(original, as_version=4)
        for c in nb.cells:
            if c.cell_type == 'code':
                c.outputs = []
                c.execution_count = None
        nb.metadata['reproduccion_aislada'] = {'origen': str(original), 'sha256_origen': digest(original),
            'nota': 'Código original sin cambios. Salidas generadas en esta carpeta. Registro local no oficial.'}
        nbformat.write(nb, run / 'notebooks' / name)
        provenance.append({'notebook': name, 'sha256_original': digest(original), 'codigo_sin_cambios': True})
    write_json(run / 'procedencia.json', {'git_commit': subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(), 'notebooks': provenance,
        'excel_sha256': digest(run / raw), 'tolerancia_absoluta_scores_metricas': SCORE_ATOL,
        'entorno': 'venv nuevo sin system-site-packages; requirements.txt instalado independientemente',
        'originales_modificados': False})
    announce(run, 'Creando entorno virtual independiente')
    venv.EnvBuilder(with_pip=True, system_site_packages=False).create(run / '.venv')
    python = run / '.venv/bin/python'
    announce(run, 'Instalando las dependencias declaradas')
    with (run / 'instalacion.log').open('w') as log:
        subprocess.run([str(python), '-m', 'pip', 'install', '-r', str(run / 'requirements.txt')],
                       cwd=run, stdout=log, stderr=subprocess.STDOUT, check=True)
    with (run / 'dependencias_congeladas.txt').open('w') as log:
        subprocess.run([str(python), '-m', 'pip', 'freeze'], stdout=log, check=True)
    check = subprocess.check_output([str(python), '-m', 'pip', 'check'], text=True)
    env = subprocess.check_output([str(python), '-c',
        'import sys,json,platform,importlib.metadata as m; print(json.dumps({"python":sys.version,"executable":sys.executable,"platform":platform.platform(),"packages":{d.metadata["Name"]:d.version for d in m.distributions()}}))'], text=True)
    write_json(run / 'entorno.json', {**json.loads(env), 'pip_check': check.strip()})
    write_json(run / 'runtime/kernels/repro/kernel.json', {'argv': [str(python), '-m', 'ipykernel_launcher', '-f', '{connection_file}'],
        'display_name': 'Reproducción aislada', 'language': 'python'})


def execute_notebook(run, name):
    path = run / 'notebooks' / name
    nb = nbformat.read(path, as_version=4)
    original = nbformat.read(ROOT / 'notebooks' / name, as_version=4)
    assert [c.source for c in nb.cells] == [c.source for c in original.cells]
    announce(run, f'Ejecutando {name}')
    start = time.monotonic()
    def progress(cell, cell_index, **kwargs):
        announce(run, f'{name}: celda {cell_index + 1} ejecutada')
    manager = KernelManager(kernel_name='repro', kernel_spec_manager=KernelSpecManager(
        kernel_dirs=[str(run / 'runtime/kernels')]))
    client = NotebookClient(nb, km=manager, timeout=3600,
        resources={'metadata': {'path': str(run / 'notebooks')}}, on_cell_executed=progress)
    try:
        client.execute(cwd=str(run / 'notebooks'))
    finally:
        # También se conserva la evidencia y el error si falla una celda.
        nbformat.write(nb, path)
        if manager.has_kernel:
            manager.shutdown_kernel(now=True)
    code = [c for c in nb.cells if c.cell_type == 'code']
    errors = [o for c in code for o in c.outputs if o.output_type == 'error']
    assert all(c.execution_count is not None for c in code) and not errors
    return {'notebook': name, 'celdas_codigo': len(code), 'celdas_ejecutadas': len(code),
            'errores': len(errors), 'segundos': round(time.monotonic() - start, 2),
            'sha256_ejecutado': digest(path)}


def local_registry(run):
    """Contrato local de evaluación construido con resultados nuevos de 04C.

    No se copian modelos, datasets procesados ni reportes oficiales al ensayo.
    Se usa la estructura del registro como contrato; sus hashes y resultados son
    los del ensayo. La comparación con el oficial no depende de este registro.
    """
    registry = json.loads((ROOT / 'models/victimas/modelo_principal.json').read_text())
    tuned = json.loads((run / 'models/victimas/metadata_random_forest_ajustado.json').read_text())
    model = joblib.load(run / registry['artefacto']['ruta'])
    data = pd.read_parquet(run / registry['datos']['ruta'])
    thresholds = data[data.Periodo.eq('train')].groupby(['Localidad', 'Franja_Horaria']).Num_Accidentes.quantile(2 / 3)
    thresholds.rename('Umbral_Etiqueta').reset_index().to_csv(run / registry['etiqueta']['archivo_umbrales'], index=False)
    registry['id_modelo'] = 'reproduccion_aislada_' + run.name
    registry['estado'] = 'ensayo_no_oficial'
    registry['alcance_cierre'] = 'Contrato del ensayo reconstruido. No reemplaza ni declara un modelo principal nuevo.'
    registry['artefacto']['sha256'] = digest(run / registry['artefacto']['ruta'])
    registry['datos']['sha256'] = digest(run / registry['datos']['ruta'])
    registry['hiperparametros'] = model.named_steps['modelo'].get_params(deep=False)
    registry['decision']['umbral_score'] = float(tuned['umbral_temporal'])
    registry['decision']['umbral_original_metadata'] = float(tuned['umbral_temporal'])
    registry['versiones']['entrenamiento_declarado'] = {'python': tuned['version_python'], 'scikit_learn': tuned['version_sklearn']}
    registry['evaluacion']['metricas'] = tuned['metricas_test_retro']
    registry['seleccion']['candidato'] = tuned['mejor_candidato']
    registry['seleccion']['ap_media'] = float(pd.read_csv(run / 'reports/tuning_victimas/busqueda_temporal_resumen.csv').iloc[0].AP_Media)
    # 05B aún no produjo sus reportes: no se precargan salidas esperadas como si
    # hubieran sido generadas. Sí se protegen sus entradas recién reconstruidas.
    registry['evidencias'] = [{'ruta': e['ruta'], 'sha256': digest(run / e['ruta'])}
                              for e in registry['evidencias'] if (run / e['ruta']).exists()]
    registry['referencia_base']['sha256'] = digest(run / registry['referencia_base']['artefacto'])
    write_json(run / 'models/victimas/modelo_principal.json', registry)
    write_json(run / 'adaptacion_registro_local.json', {'motivo': registry['alcance_cierre'],
        'campos_de_control': 'Hashes, parámetros y métricas provienen del ensayo; esquema de la versión oficial.',
        'reportes_oficiales_precargados': 0, 'modelos_oficiales_copiados': 0,
        'notebook_05B_codigo_modificado': False,
        'advertencia_textos': 'Las referencias a rf_victimas_bogota_v1.0 en las conclusiones originales son contexto de comparación, no promoción del modelo reconstruido.'})


def compare_table(run, relative, keys=None):
    def read(path):
        return pd.read_parquet(path) if path.suffix == '.parquet' else pd.read_csv(path, float_precision='round_trip')
    a, b = read(run / relative), read(ROOT / relative)
    result = {'archivo': relative, 'filas_reconstruidas': len(a), 'filas_oficiales': len(b)}
    if keys:
        if 'Fecha_Acc' in keys:
            a['Fecha_Acc'], b['Fecha_Acc'] = pd.to_datetime(a.Fecha_Acc), pd.to_datetime(b.Fecha_Acc)
        assert not a.duplicated(keys).any() and not b.duplicated(keys).any()
        a, b = a.sort_values(keys).reset_index(drop=True), b.sort_values(keys).reset_index(drop=True)
    try:
        pd.testing.assert_frame_equal(a, b, check_dtype=False, check_exact=False, rtol=0, atol=SCORE_ATOL)
        result['equivalente'] = True
    except AssertionError as error:
        result['equivalente'] = False
        result['detalle'] = str(error)[:2000]
    result['max_diferencias_numericas'] = {}
    if a.shape == b.shape and list(a.columns) == list(b.columns):
        for col in a.select_dtypes(include='number').columns:
            if pd.api.types.is_numeric_dtype(b[col]):
                value = (a[col] - b[col]).abs().max()
                result['max_diferencias_numericas'][col] = float(value) if pd.notna(value) else None
    return result


def compare_results(run):
    results = []
    keys = ['Fecha_Acc', 'Localidad', 'Franja_Horaria']
    tables = [
        ('reports/modeling_victimas/validacion_temporal_detalle.csv', ['Corte', 'Modelo']),
        ('reports/modeling_victimas/seleccion_umbral_2020_2022.csv', ['Umbral']),
        ('reports/modeling_victimas/predicciones_oof_2020_2022.parquet', ['Modelo', *keys]),
        ('reports/modeling_victimas/predicciones_2023_2024.parquet', ['Modelo', *keys]),
        ('reports/tuning_victimas/busqueda_temporal_detalle.csv', ['Candidato', 'Validacion']),
        ('reports/tuning_victimas/busqueda_temporal_resumen.csv', ['Candidato']),
        ('reports/tuning_victimas/seleccion_umbral.csv', ['Umbral']),
        ('reports/tuning_victimas/predicciones_oof_mejor_configuracion.parquet', keys),
        ('reports/evaluation_victimas/predicciones_random_forest_ajustado_2023_2024.parquet', keys),
        ('reports/evaluation_victimas/metricas_globales.csv', ['Modelo']),
        ('reports/evaluation_victimas/metricas_random_forest_ajustado_por_localidad.csv', ['Localidad']),
        ('reports/evaluation_victimas/metricas_random_forest_ajustado_por_franja.csv', ['Franja_Horaria']),
        ('reports/evaluation_victimas/comparacion_referencias_historicas.csv', ['Metodo']),
        ('reports/evaluation_victimas/bootstrap_rf_vs_referencia_resumen.csv', ['Metrica']),
    ]
    for path, key in tables:
        results.append(compare_table(run, path, key))
    metadata = []
    for filename, fields in [('metadata_modelo.json', ['modelo_seleccionado', 'umbral_candidato', 'variables', 'random_state']),
                             ('metadata_random_forest_ajustado.json', ['mejor_candidato', 'hiperparametros', 'umbral_temporal'])]:
        a = json.loads((run / 'models/victimas' / filename).read_text())
        b = json.loads((ROOT / 'models/victimas' / filename).read_text())
        metadata.append({'archivo': filename, 'coincidencias': {k: a[k] == b[k] for k in fields},
                         'python_oficial': b['version_python'], 'python_reproduccion': a['version_python']})
    models = []
    for name in ['pipeline_logistica_victimas.pkl', 'pipeline_random_forest_victimas.pkl',
                 'pipeline_xgboost_victimas.pkl', 'pipeline_random_forest_ajustado_victimas.pkl']:
        a, b = joblib.load(run / 'models/victimas' / name), joblib.load(ROOT / 'models/victimas' / name)
        models.append({'modelo': name, 'mismo_esquema': a.feature_names_in_.tolist() == b.feature_names_in_.tolist(),
            'mismos_hiperparametros': same_parameters(a.named_steps['modelo'].get_params(), b.named_steps['modelo'].get_params()),
            'mismos_bytes': digest(run / 'models/victimas' / name) == digest(ROOT / 'models/victimas' / name)})
    return {'tablas': results, 'seleccion': metadata, 'modelos': models,
            'nota_bytes': 'No se exige identidad binaria de pickle; se comparan esquema, parámetros, decisiones y scores con tolerancia prefijada.'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-name', default=datetime.now().strftime('ejecucion_%Y%m%d_%H%M%S'))
    parser.add_argument('--compare-only', action='store_true',
                        help='Repite únicamente la auditoría de una ejecución completa; no entrena ni ejecuta notebooks.')
    args = parser.parse_args()
    if not args.run_name or args.run_name in {'.', '..'} or Path(args.run_name).name != args.run_name:
        raise ValueError('El nombre no puede contener rutas.')
    run = ROOT / 'reports/reproducibilidad' / args.run_name
    if not args.compare_only and run.exists():
        raise FileExistsError(f'La carpeta ya existe; elige otro --run-name: {run}')
    if args.compare_only:
        stages = json.loads((run / 'ejecuciones_notebooks.json').read_text())
        assert [s['notebook'] for s in stages] == NAMES, 'La cadena no está completa.'
        for stage in stages:
            path = run / 'notebooks' / stage['notebook']
            assert stage['sha256_ejecutado'] == digest(path), 'Notebook alterado después de ejecutarlo.'
            assert stage['errores'] == 0 and stage['celdas_ejecutadas'] == stage['celdas_codigo']
        shutil.copy2(run / 'resultado.json', run / ('resultado_previo_' + datetime.now().strftime('%Y%m%d_%H%M%S') + '.json'))
    else:
        stages = []
    result = {'estado': 'en_progreso'}
    try:
        if not args.compare_only:
            setup(run)
        for name in ([] if args.compare_only else NAMES):
            if name.startswith('05B'):
                local_registry(run)
            stages.append(execute_notebook(run, name))
            write_json(run / 'ejecuciones_notebooks.json', stages)
            if name.startswith('03B'):
                path = Path('data/processed/dataset_victimas_localidad_franja_fecha.parquet')
                pd.testing.assert_frame_equal(pd.read_parquet(run / path), pd.read_parquet(ROOT / path), check_exact=True)
                write_json(run / 'comparacion_dataset.json', {'coincidencia_exacta': True, 'filas': 204560, 'columnas': 16,
                    'incluye': 'Valores, tipos, orden de filas y columnas, variables y etiquetas.'})
        announce(run, 'Comparando resultados reconstruidos contra la versión oficial')
        result = compare_results(run)
        passed = all(x['equivalente'] for x in result['tablas']) and all(all(x['coincidencias'].values()) for x in result['seleccion'])
        passed &= all(x['mismo_esquema'] and x['mismos_hiperparametros'] for x in result['modelos'])
        result['estado'] = 'reproduccion_equivalente' if passed else 'ejecutado_con_diferencias'
    except Exception:
        result = {'estado': 'error', 'detalle': traceback.format_exc()}
        print(result['detalle'], flush=True)
    finally:
        if run.exists():
            before_path = run / 'integridad_oficial_antes.json'
            if before_path.exists():
                before = json.loads(before_path.read_text())
                changed = [p for p, h in before.items() if not (ROOT / p).exists() or digest(ROOT / p) != h]
                result['oficiales_intactos'] = not changed
                result['archivos_oficiales_comprobados'] = len(before)
                result['archivos_oficiales_modificados'] = changed
                if changed:
                    result['estado'] = 'error_integridad_oficial'
            result['ejecuciones'] = stages
            write_json(run / 'resultado.json', result)
            announce(run, result['estado'], oficiales_intactos=result.get('oficiales_intactos'))
            print('CARPETA_RESULTADOS=' + str(run), flush=True)
    if result['estado'] not in ['reproduccion_equivalente', 'ejecutado_con_diferencias']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
