"""Perfilado inicial sin necesitar cargar Excel en las pruebas unitarias."""
import ast
import json
import unittest
from unittest.mock import Mock

import pandas as pd
from src.rutas import ROOT


class ComprensionDatosTest(unittest.TestCase):
    def setUp(self):
        nb=json.loads((ROOT/'notebooks/02_Comprension_de_los_Datos.ipynb').read_text())
        self.sources=[''.join(c['source']) for c in nb['cells'] if c['cell_type']=='code']

    def test_info_invocado_en_las_cuatro_hojas(self):
        called=set()
        for i,source in enumerate(self.sources):
            tree=ast.parse(source)
            compile(tree,f'02:{i}','exec')
            for node in ast.walk(tree):
                if isinstance(node,ast.Expr) and isinstance(node.value,ast.Attribute):
                    self.assertNotEqual(node.value.attr,'info','Referencia al método sin invocarlo')
                if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=='info':
                    called.add(node.func.value.id)
                    options={k.arg:ast.literal_eval(k.value) for k in node.keywords}
                    self.assertTrue(options['show_counts'])
                    self.assertTrue(options['verbose'])
        self.assertEqual(called,{'siniestros','vehiculos','Actor_vial','Diccionario'})

    def test_resumen_y_tipos_muestran_cada_hoja(self):
        sheets={name:pd.DataFrame({'Codigo':[1], 'Texto':['ejemplo']})
                for name in ['Siniestros','Vehiculos','Actor_vial','Diccionario']}
        show=Mock();printer=Mock()
        scope={'pd':pd,'hojas':sheets,'display':show,'print':printer}
        source=next(s for s in self.sources if 'resumen_hojas =' in s)
        exec(compile(source,'resumen','exec'),scope)
        self.assertEqual(show.call_args.args[0].Hoja.tolist(),list(sheets))
        show.reset_mock()
        source=next(s for s in self.sources if 'tabla.dtypes' in s)
        exec(compile(source,'tipos','exec'),scope)
        self.assertEqual(show.call_count,4)
        for name,call in zip(sheets,printer.call_args_list):
            self.assertIn(name,call.args[0])
        for call in show.call_args_list:
            self.assertEqual(call.args[0].index.tolist(),['Codigo','Texto'])
            self.assertEqual(list(call.args[0].columns),['Tipo de dato pandas'])


if __name__=='__main__':
    unittest.main()
