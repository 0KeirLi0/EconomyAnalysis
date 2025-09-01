import sys
import os
from datetime import datetime


import dash
from dash import dcc, html
import plotly.graph_objects as go
from dash_bootstrap_components.themes import BOOTSTRAP

from src.hk_chart.hk_daily_interbank_liquidity import hkfigs_generation

def get_layout():
    # figs= hkfigs_generation()
    layout = html.Div([
    ###### HK Chart ######
        html.H1("HK Chart", style={'textAlign': 'center'}),  
        html.Div(f"Last update time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", style={'textAlign': 'left', 'margin': '10px'}),
        html.Div([
            html.Div([
                html.H2(title, style={'textAlign': 'center'}),
                dcc.Graph( figure=fig)
            ])
            for fig, title in hkfigs_generation()
        ])
    #####################
    ])
    return layout

