import sys
import os

from dash import Dash
from dash_bootstrap_components.themes import BOOTSTRAP
from src.app.layout import get_layout


def main():
    plotly_could = True
    app = Dash(__name__, external_stylesheets=[BOOTSTRAP])
    app.title = "Keir's Charts Collection"
    app.layout = get_layout()
    if plotly_could:
        server = app.server
        app.run()
    else:
        app.run(debug=True, host='127.0.0.1', port=8050)
    
    

if __name__ == "__main__":
    main()
