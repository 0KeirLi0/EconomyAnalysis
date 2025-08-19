import pandas as pd
import requests
import json
import datetime as dt
import plotly.express as px
import plotly.graph_objects as go
import os
import yfinance as yf

url = 'https://api.hkma.gov.hk/public/market-data-and-statistics/daily-monetary-statistics/daily-figures-interbank-liquidity?offset=0&pagesize=999&sortby=end_of_date&sortorder=desc'
response = requests.get(url).text
response = json.loads(response)
df = pd.DataFrame(response['result']['records'])
df['end_of_date'] = pd.to_datetime(df['end_of_date'])

hibor_df = df[['end_of_date', 'hibor_overnight', 'hibor_fixing_1m']]

hibor_fig = px.line(hibor_df,
             x='end_of_date', y=['hibor_overnight', 'hibor_fixing_1m'],
             title='HIBOR Rates (Overnight & 1-Month)',
             labels={'end_of_date': 'Date', 'value': 'HIBOR Rate (%)'},
             )

last_date = hibor_df['end_of_date'].iloc[0]
last_overnight = hibor_df['hibor_overnight'].iloc[0]
last_1m = hibor_df['hibor_fixing_1m'].iloc[0]

hibor_fig.add_annotation(
    text=f"Date: {last_date.strftime('%Y-%m-%d')}<br>Overnight: {last_overnight}%<br>1M: {last_1m}%",
    xref="paper", yref="paper",
    x=1, y=1.2,  
    showarrow=False,
    bgcolor="rgba(1, 108, 2, 1)",
    borderwidth=2,
    font=dict(size=12, color="white")
)

hibor_fig.update_layout(
    xaxis_rangeslider_visible=True,
)

aggreBal_df = df[['end_of_date', 'opening_balance', 'closing_balance']].head(200)
aggreBal_df['day_change'] = aggreBal_df['closing_balance'] - aggreBal_df['opening_balance']
aggreBal_df['high'] = aggreBal_df[['opening_balance', 'closing_balance']].max(axis=1)
aggreBal_df['low'] = aggreBal_df[['opening_balance', 'closing_balance']].min(axis=1)

aggreBal_fig = go.Figure(data=[go.Candlestick(
    x=aggreBal_df['end_of_date'],
    open=aggreBal_df['opening_balance'],
    high=aggreBal_df['high'],
    low=aggreBal_df['low'],
    close=aggreBal_df['closing_balance'],
    name='Aggregate Balance',
    showlegend=True,
)])

last_date = aggreBal_df['end_of_date'].iloc[0]
last_open = aggreBal_df['opening_balance'].iloc[0]
last_close = aggreBal_df['closing_balance'].iloc[0]
last_day_change = aggreBal_df['day_change'].iloc[0]

aggreBal_fig.add_annotation(
    text=f"Date: {last_date.strftime('%Y-%m-%d')}<br>Open: {last_open}<br>Close: {last_close}<br>Change: {last_day_change}",
    xref="paper", yref="paper",
    x=1, y=1.2,
    showarrow=False,
    bgcolor="rgba(0, 78, 123, 1)",
    borderwidth=2,
    font=dict(size=12, color="white")
)

aggreBal_fig.update_layout(
    xaxis_rangeslider_visible=True,
    title="Hong Kong Aggregate Balance (Candlestick)",
    xaxis_title="Date",
    yaxis_title="Balance (HKD Million)",
)

usdhkd = yf.Ticker("HKD=X")
usdhkd_df = usdhkd.history(period ='max').reset_index()
usdhkd_df['Date'] = pd.to_datetime(usdhkd_df['Date'], format='%Y-%m-%d')
usdhkd_df = usdhkd_df[['Date', 'Close']]
usdhkd_df = usdhkd_df.rename(columns={'Date': 'end_of_date', 'Close': 'usdhkd_close'})
usdhkd_df['end_of_date'] = pd.to_datetime(usdhkd_df['end_of_date'])
usdhkd_df.set_index('end_of_date', inplace=True)
usdhkd_df.index = usdhkd_df.index.tz_localize(None)

cu_df = df[['end_of_date', 'cu_weakside', "cu_strongside"]]
cu_df['end_of_date'] = pd.to_datetime(cu_df['end_of_date'])
cu_df = cu_df.set_index('end_of_date').join(usdhkd_df, on='end_of_date', how='left')
cu_df = cu_df.reset_index()
cu_df.sort_values(by='end_of_date', ascending=False, inplace=True)

cu_fig = px.line(cu_df,
             x='end_of_date', y=['usdhkd_close', 'cu_weakside', 'cu_strongside'],
             title='USD/HKD and Currency Pegs',
             labels={'end_of_date': 'Date', 'value': 'Value (HKD)'},
             )


last_date = cu_df['end_of_date'].iloc[0]
last_usdhkd_close = round(cu_df['usdhkd_close'].iloc[0],4)

cu_fig.add_annotation(
    text=f"Date: {last_date.strftime('%Y-%m-%d')}<br>usdhkd: {last_usdhkd_close}",
    xref="paper", yref="paper",
    x=1, y=1.2, 
    showarrow=False,
    bgcolor="rgba(108, 1, 2, 1)",
    borderwidth=2,
    font=dict(size=12, color="white")
)

cu_fig.update_layout(
    xaxis_rangeslider_visible=True,
)

hkdtwi_df = df[['end_of_date', 'twi']]
hkdtwi_fig = px.line(hkdtwi_df,
             x='end_of_date', y='twi',
             title='HKD Trade-Weighted Index (TWI)',
             labels={'end_of_date': 'Date', 'value': 'Value'},
             )


last_date = hkdtwi_df['end_of_date'].iloc[0]
last_twi = hkdtwi_df['twi'].iloc[0]

hkdtwi_fig.add_annotation(
    text=f"Date: {last_date.strftime('%Y-%m-%d')}<br>TWI(HKD): {last_twi}",
    xref="paper", yref="paper",
    x=1, y=1.2,
    showarrow=False,
    bgcolor="rgba(156, 33, 315, 1)",
    borderwidth=2,
    font=dict(size=12, color="white")
)

hkdtwi_fig.update_layout(
    xaxis_rangeslider_visible=True,
)

hsi = yf.Ticker("^HSI")
hsi_df = hsi.history(period ='10y').reset_index()
hsi_df.set_index('Date', inplace=True)
hsi_df.index = hsi_df.index.tz_localize(None)
hsi_df.sort_values(by='Date', ascending=False, inplace=True)
hsi_df['day_change'] = hsi_df['Close'] - hsi_df['Open']
hsi_df = hsi_df.reset_index()

hsi_fig = px.line(hsi_df,
             x='Date', y='Close',
             title='HSI',
             labels={'Date': 'Date', 'value': 'Value'},
             )


last_date = hsi_df['Date'].iloc[0]
last_hsi = round(hsi_df['Close'].iloc[0],2)

hsi_fig.add_annotation(
    text=f"Date: {last_date.strftime('%Y-%m-%d')}<br>Index(HKD): {last_hsi}",
    xref="paper", yref="paper",
    x=1, y=1.2, 
    showarrow=False,
    bgcolor="rgba(156, 33, 315, 1)",
    borderwidth=2,
    font=dict(size=12, color="white")
)

hsi_fig.update_layout(
    xaxis_rangeslider_visible=True,
)

figs = [
    (hibor_fig, "HIBOR"),
    (aggreBal_fig, "AggreBal"),
    (hsi_fig, "HSI"),
    (cu_fig, "Currency"),
    (hkdtwi_fig, "HKDTWI"),
]

html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Charts</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body { margin: 20px; text-align: center; }
        div { margin: 30px auto; width: 80%; }
    </style>
</head>
<body>
    <h1>Charts</h1>
"""
for i, (fig, title) in enumerate(figs, 1):
    html += "<hr>\n"
    html += f"<h2>{title}</h2>\n"
    html += fig.to_html(full_html=False, div_id=f"chart{i}", include_plotlyjs=True)

html += "</body>\n</html>"

output_path = os.path.abspath(os.path.join(os.path.abspath(os.path.join(os.getcwd(), "..")), ".."))+ "/docs/charts.html"
with open(output_path, "w", encoding="utf-8") as f:
    f.write(html)
    