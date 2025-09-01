import sys
import os

from dash import Dash
from dash_bootstrap_components.themes import BOOTSTRAP
from src.app.layout import get_layout

app = Dash(__name__, external_stylesheets=[BOOTSTRAP])
server = app.server

def main():
    app.title = "Keir's Charts Collection"
    app.layout = get_layout()
    app.run()
    # app.run(debug=True, host='127.0.0.1', port=8050)
    
    

if __name__ == "__main__":
    main()
