"""Comando único de pruebas. --integracion comprueba artefactos sin reentrenar."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--integracion', action='store_true', help='Requiere Excel real (Git LFS), dataset y modelos.')
    parser.add_argument('--salida', type=Path, help='JSON nuevo; nunca reemplaza un informe existente.')
    args = parser.parse_args()
    if args.salida and args.salida.exists():
        parser.error('El informe ya existe; elija un nombre nuevo.')
    suite = unittest.defaultTestLoader.discover(str(ROOT/'tests'))
    test = unittest.TextTestRunner(verbosity=2).run(suite)
    if not test.wasSuccessful():
        raise SystemExit(1)
    report = {'fecha_utc': datetime.now(timezone.utc).isoformat(), 'resultado': 'correcto',
              'pruebas_unitarias': test.testsRun, 'fallos': len(test.failures), 'errores': len(test.errors),
              'integracion_ejecutada': args.integracion, 'modelos_reentrenados': 0}
    if args.integracion:
        import numpy as np
        import pandas as pd
        from scripts.verificar_preparacion import verificar as verificar_preparacion
        from scripts.verificar_modelo_principal import verificar as verificar_modelo
        from scripts.verificar_fuente import verificar as verificar_fuente
        from src.consulta_retrospectiva import cargar_consulta
        report['fuente'] = verificar_fuente()
        report['preparacion'] = verificar_preparacion()
        report['modelo'] = verificar_modelo()
        consulta = cargar_consulta()
        previas = pd.read_parquet(ROOT/'reports/evaluation_victimas/predicciones_random_forest_ajustado_2023_2024.parquet')
        muestras = previas.iloc[[0, 100, len(previas)//2, len(previas)-1]]
        for _, fila in muestras.iterrows():
            actual = consulta.consultar(fila.Fecha_Acc, fila.Localidad, fila.Franja_Horaria).iloc[0]
            np.testing.assert_allclose(actual.Score_Priorizacion, fila.Score, atol=1e-12, rtol=0)
            assert actual.Alerta_Modelo == fila.Prediccion
        report['consulta'] = {'casos_reales': len(muestras), 'coincide_con_05B': True,
                              'alcance': 'consulta retrospectiva de variables preparadas, no predicción futura'}
    if args.salida:
        args.salida.parent.mkdir(parents=True, exist_ok=True)
        with args.salida.open('x', encoding='utf-8') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
