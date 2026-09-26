"""Impide que el catálogo vigente pierda rutas o apunte al modelo base."""
import json
import unittest
from src.rutas import ROOT


class CatalogoTest(unittest.TestCase):
    def setUp(self):
        self.catalogo = json.loads((ROOT/'config/artefactos.json').read_text())

    def test_rutas_catalogadas_existen(self):
        def rutas(value):
            if isinstance(value, dict):
                for key, child in value.items():
                    if key != 'politica':
                        yield from rutas(child)
            elif isinstance(value, list):
                for child in value:
                    yield from rutas(child)
            elif isinstance(value, str) and value.startswith(('models/', 'data/', 'reports/', 'notebooks/')):
                yield value
        for path in rutas(self.catalogo):
            with self.subTest(path=path):
                self.assertTrue((ROOT/path).exists(), path)

    def test_principal_coincide_con_registro_y_no_con_alias_base(self):
        registro = json.loads((ROOT/self.catalogo['autoridad_modelo']).read_text())
        principal = self.catalogo['principal']
        self.assertEqual(principal['pipeline'], registro['artefacto']['ruta'])
        self.assertEqual(principal['dataset'], registro['datos']['ruta'])
        self.assertNotIn(principal['pipeline'], self.catalogo['referencia_base_no_principal'])
        self.assertFalse(set(principal['notebooks']) & set(self.catalogo['legacy_todos_los_siniestros']['notebooks']))
