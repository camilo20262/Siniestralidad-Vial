from dashboard.app import create_app

dash_app = create_app()
app = dash_app.server
