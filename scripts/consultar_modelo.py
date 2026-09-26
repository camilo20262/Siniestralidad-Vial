"""Consulta retrospectiva desde cualquier directorio; no escribe archivos."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.consulta_retrospectiva import cargar_consulta


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fecha', required=True)
    parser.add_argument('--localidad', required=True)
    parser.add_argument('--franja', required=True)
    args = parser.parse_args()
    try:
        resultado = cargar_consulta().consultar(args.fecha, args.localidad, args.franja)
    except (ValueError, RuntimeError) as exc:
        parser.exit(2, f'Consulta rechazada: {exc}\n')
    print(resultado.to_json(orient='records', force_ascii=False, indent=2))
