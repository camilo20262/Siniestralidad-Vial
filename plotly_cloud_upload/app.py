"""Entrada aislada para publicar el dashboard en Plotly Cloud."""

from cloud_service import load_cloud_data
from dashboard.app import create_app


# Plotly Cloud detecta este objeto Dash como punto de entrada.
app = create_app(load_cloud_data())

