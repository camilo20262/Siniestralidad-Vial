"""Arranca un servidor local temporal y verifica el protocolo HTTP real de Dash.

No sustituye la revisión visual en navegador ni una prueba de aceptación humana.
El puerto lo asigna el sistema; no ocupa ni detiene el dashboard del usuario.
"""
import argparse
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def serve(ready):
    from dashboard.app import create_app
    from werkzeug.serving import make_server
    app = create_app()
    with make_server('127.0.0.1', 0, app.server, threaded=True) as server:
        callbacks = {}
        for key, value in app.callback_map.items():
            outputs = value['output']
            def spec(o):
                return {'id': o.component_id, 'property': o.component_property}
            callbacks[key] = {
                'outputs': [spec(o) for o in outputs] if isinstance(outputs, list) else spec(outputs),
                'inputs': value['inputs'], 'state': value['state']}
        payload = json.dumps({'port': server.server_port, 'callbacks': callbacks})
        pending = ready.with_suffix('.tmp')
        pending.write_text(payload, encoding='utf-8')
        pending.replace(ready)
        server.serve_forever()


def callback_payload(key, spec, inputs, states=()):
    if len(inputs) != len(spec['inputs']) or len(states) != len(spec['state']):
        raise ValueError(f'Contrato de callback distinto al esperado: {key}')
    return {'output': key, 'outputs': spec['outputs'],
            'inputs': [dict(s, value=v) for s, v in zip(spec['inputs'], inputs)],
            'state': [dict(s, value=v) for s, v in zip(spec['state'], states)],
            'changedPropIds': [f"{spec['inputs'][0]['id']}.{spec['inputs'][0]['property']}"]}


def verificar():
    import pandas as pd
    from src.rutas import sha256_archivo
    registry = json.loads((ROOT/'models/victimas/modelo_principal.json').read_text())
    protected = {e['ruta']: sha256_archivo(ROOT/e['ruta']) for e in registry['evidencias']}
    with tempfile.TemporaryDirectory(prefix='siniestralidad-http-') as temporary:
        ready = Path(temporary)/'ready.json'
        with tempfile.TemporaryFile(mode='w+') as log:
            process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()),
                                        '--servidor', str(ready)], cwd=ROOT,
                                       env={**os.environ, 'SINIESTRALIDAD_ROOT': str(ROOT)},
                                       stdout=log, stderr=subprocess.STDOUT)
            try:
                deadline = time.monotonic() + 90
                while not ready.exists():
                    if process.poll() is not None or time.monotonic() > deadline:
                        log.seek(0)
                        raise RuntimeError('No inició el servidor temporal: ' + log.read()[-4000:])
                    time.sleep(.1)
                info = json.loads(ready.read_text())
                base = f"http://127.0.0.1:{info['port']}"
                calls = []
                def request(path, payload=None):
                    start = time.monotonic()
                    req = Request(base+path, data=None if payload is None else json.dumps(payload).encode(),
                                  headers={'Content-Type': 'application/json'})
                    with urlopen(req, timeout=30) as response:
                        body = response.read()
                        if response.status != 200:
                            raise ValueError(f'HTTP {response.status}: {path}')
                    calls.append({'ruta': path, 'estado_http': 200,
                                  'segundos': round(time.monotonic()-start, 4)})
                    return body
                def call(key, values, states=()):
                    payload = callback_payload(key, info['callbacks'][key], values, states)
                    return json.loads(request('/_dash-update-component', payload))['response']
                request('/')
                layout = json.loads(request('/_dash-layout'))
                request('/_dash-dependencies')
                request('/assets/dashboard.css')
                health = json.loads(request('/healthz'))
                if health['modelo'] != registry['id_modelo']:
                    raise ValueError('El servidor no consume el registro de este ensayo.')
                pages = ['overview', 'query', 'history', 'evaluation', 'about']
                layout_text = json.dumps(layout, ensure_ascii=False)
                if any(f'page-{page}' not in layout_text for page in pages):
                    raise ValueError('El layout no contiene las cinco vistas montadas.')
                key = next(k for k in info['callbacks'] if k.startswith('..query-map'))
                queries = [('2023-01-01', 'Mañana', 'KENNEDY'),
                           ('2024-02-29', 'Noche', 'CANDELARIA'),
                           ('2024-12-31', 'Madrugada', 'SUMAPAZ')]
                for date, slot, locality in queries:
                    result = call(key, [date, slot, locality, 'distrito', 'dark'], [None])
                    if result['query-error']['children']:
                        raise ValueError(result['query-error']['children'])
                    traces=result['query-map']['figure']['data']
                    if len([trace for trace in traces
                            if trace.get('name') in registry['categorias']['Localidad']]) != 20:
                        raise ValueError('Mapa sin las 20 localidades.')
                invalid = call(key, ['2025-01-01', 'Noche', 'KENNEDY', 'distrito', 'dark'], [None])
                if not invalid['query-error']['children'] or invalid['query-detail']['children'] != []:
                    raise ValueError('La consulta futura no se rechazó limpiamente.')
                figure = result['query-map']['figure']
                index = next(index for index,trace in enumerate(figure['data'])
                             if trace.get('name')=='KENNEDY')
                point = {'curveNumber': index, 'pointNumber': 0,
                         'customdata': figure['data'][index]['customdata'][0]}
                selected = call('query-locality.value', [{'points': [point]}])
                if selected['query-locality']['value'] != 'KENNEDY':
                    raise ValueError('La selección del mapa no se propaga.')
                for prefix, values, error in [
                    ('..history-kpis', ['Todos', 'Todas', 'Todas', 'Todos', 'dark'], 'history-error'),
                    ('..history-kpis', [2024, 'KENNEDY', 'Noche', 'Peatón', 'dark'], 'history-error'),
                    ('..eval-kpis', ['Todos', 'Todas', 'Todas', 'dark'], 'eval-error'),
                    ('..eval-kpis', [2023, 'SUMAPAZ', 'Madrugada', 'dark'], 'eval-error')]:
                    callback = next(k for k in info['callbacks'] if k.startswith(prefix))
                    if call(callback, values)[error]['children']:
                        raise ValueError(f'Error al filtrar {prefix}')
                downloads = []
                for key, states in [
                    ('download-query.data', ['2023-01-01', 'KENNEDY', 'Mañana']),
                    ('download-map.data', ['2023-01-01', 'Mañana']),
                    ('download-history.data', [2024, 'KENNEDY', 'Noche', 'Peatón']),
                    ('download-eval.data', ['Todos', 'Todas', 'Todas'])]:
                    data = call(key, [1], states)[key.split('.')[0]]['data']
                    content = data['content']
                    if key.startswith('download-query'):
                        rows = json.loads(content)
                        if len(rows) != 1 or rows[0]['Id_Modelo'] != registry['id_modelo']:
                            raise ValueError('Descarga de consulta sin trazabilidad local.')
                    else:
                        frame = pd.read_csv(io.StringIO(content))
                        if frame.empty:
                            raise ValueError('Descarga vacía.')
                        if not key.startswith('download-history') and not frame.Id_Modelo.eq(registry['id_modelo']).all():
                            raise ValueError('Descarga con modelo ajeno al ensayo.')
                        if key.startswith('download-map') and len(frame) != 20:
                            raise ValueError('Descarga del mapa incompleta.')
                    downloads.append(data['filename'])
            finally:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=10)
            if any(sha256_archivo(ROOT/p) != h for p, h in protected.items()):
                raise ValueError('La prueba HTTP modificó artefactos del ensayo.')
    return {'resultado': 'correcto', 'modelo': registry['id_modelo'],
            'servidor': '127.0.0.1, puerto temporal asignado por el sistema',
            'servidor_detenido': process.poll() is not None, 'paginas': pages,
            'consultas_validas': len(queries), 'consulta_futura_rechazada': True,
            'descargas': downloads, 'peticiones': calls,
            'revision_visual_automatizada': False,
            'limite': 'HTTP y callbacks reales; no ejecuta JavaScript ni evalúa diseño o usabilidad.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--servidor', type=Path, help=argparse.SUPPRESS)
    parser.add_argument('--salida', type=Path)
    args = parser.parse_args()
    if args.servidor:
        serve(args.servidor)
    else:
        if args.salida and args.salida.exists():
            parser.error('El informe ya existe; use una ruta nueva.')
        result = verificar()
        if args.salida:
            args.salida.parent.mkdir(parents=True, exist_ok=True)
            with args.salida.open('x', encoding='utf-8') as stream:
                json.dump(result, stream, ensure_ascii=False, indent=2)
        print(json.dumps(result, ensure_ascii=False, indent=2))
