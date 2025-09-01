import pandas as pd
import requests
import json
import datetime as dt
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf

def fetch_interbank_liquidity():
    url = 'https://api.hkma.gov.hk/public/market-data-and-statistics/daily-monetary-statistics/daily-figures-interbank-liquidity?offset=0&pagesize=999&sortby=end_of_date&sortorder=desc'
    response = requests.get(url).text
    response = json.loads(response)
    df = pd.DataFrame(response['result']['records'])
    df['end_of_date'] = pd.to_datetime(df['end_of_date'])
    return df

def get_hibor(startDate, endDate) -> pd.DataFrame:
    selected_keys = ['Overnight', '1 Week', '2 Weeks', '1 Month', '2 Months', '3 Months', '6 Months', '12 Months']
    hibor_df = pd.DataFrame(columns=selected_keys)
    for date in pd.date_range(startDate, endDate):
        if date.dayofweek < 5:
            year, month, day = date.year, date.month, date.day
            hibor_url = f"https://www.hkab.org.hk/api/hibor?year={year}&month={month}&day={day}"
            hibor_response = requests.get(hibor_url).json()
            if hibor_response['isHoliday'] == False:
                temp_df = pd.DataFrame(hibor_response, index=[date], columns=selected_keys)
                hibor_df = pd.concat([hibor_df, temp_df], ignore_index=False)
    hibor_df = hibor_df.dropna().sort_index(ascending=False).reset_index(drop=False).rename(columns={'index': 'date'})
    return hibor_df

def plot_hibor(hibor_df):
    hibor_fig = px.line(
        hibor_df,
        x='date', y=['Overnight', '1 Week', '1 Month', '3 Months', '6 Months', '12 Months'],
        title='HIBOR Rates',
        labels={'end_of_date': 'Date', 'value': 'HIBOR Rate (%)'},
    )
    last = hibor_df.iloc[0]
    hibor_fig.add_annotation(
        text=f"Date: {last['date'].strftime('%Y-%m-%d')}<br>Overnight: {round(last['Overnight'],2)}%<br>1M: {round(last['1 Month'],2)}%<br>3M: {round(last['3 Months'],2)}%<br>6M: {round(last['6 Months'],2)}%<br>12M: {round(last['12 Months'],2)}%",
        xref="paper", yref="paper", x=1, y=1.2, showarrow=False,
        bgcolor="rgba(1, 108, 2, 1)", borderwidth=2,
        font=dict(size=12, color="white"), align='right',
    )
    hibor_fig.update_xaxes(
        rangeslider_visible=False,
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(step="all")
            ])
        )
    )    
    return hibor_fig

def plot_aggreBal(df):
    aggreBal_df = df[['end_of_date', 'opening_balance', 'closing_balance']].head(251)
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
    last = aggreBal_df.iloc[0]
    aggreBal_fig.add_annotation(
        text=f"Date: {last['end_of_date'].strftime('%Y-%m-%d')}<br>Open: {last['opening_balance']}<br>Close: {last['closing_balance']}<br>Change: {last['day_change']}",
        xref="paper", yref="paper", x=1, y=1.2, showarrow=False,
        bgcolor="rgba(0, 78, 123, 1)", borderwidth=2,
        font=dict(size=12, color="white")
    )
    aggreBal_fig.update_layout(
        title="Hong Kong Aggregate Balance (Candlestick)",
        xaxis_title="Date",
        yaxis_title="Balance (HKD Million)",
    )
    aggreBal_fig.update_xaxes(
        rangeslider_visible=False,
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(step="all")
            ])
        )
    )    
    return aggreBal_fig

def plot_currency(df):
    usdhkd = yf.Ticker("HKD=X")
    usdhkd_df = usdhkd.history(period='max').reset_index()
    usdhkd_df['Date'] = pd.to_datetime(usdhkd_df['Date'], format='%Y-%m-%d')
    usdhkd_df = usdhkd_df[['Date', 'Close']].rename(columns={'Date': 'end_of_date', 'Close': 'usdhkd_close'})
    usdhkd_df['end_of_date'] = pd.to_datetime(usdhkd_df['end_of_date'])
    usdhkd_df.set_index('end_of_date', inplace=True)
    usdhkd_df.index = usdhkd_df.index.tz_localize(None)
    cu_df = df[['end_of_date', 'cu_weakside', "cu_strongside"]].head(251)
    cu_df['end_of_date'] = pd.to_datetime(cu_df['end_of_date'])
    cu_df = cu_df.set_index('end_of_date').join(usdhkd_df, on='end_of_date', how='left').reset_index()
    cu_df.sort_values(by='end_of_date', ascending=False, inplace=True)
    cu_fig = px.line(
        cu_df,
        x='end_of_date', y=['usdhkd_close', 'cu_weakside', 'cu_strongside'],
        title='USD/HKD and Currency Pegs',
        labels={'end_of_date': 'Date', 'value': 'Value (HKD)'},
    )
    last = cu_df.iloc[0]
    cu_fig.add_annotation(
        text=f"Date: {last['end_of_date'].strftime('%Y-%m-%d')}<br>usdhkd: {round(last['usdhkd_close'],4)}",
        xref="paper", yref="paper", x=1, y=1.2, showarrow=False,
        bgcolor="rgba(108, 1, 2, 1)", borderwidth=2,
        font=dict(size=12, color="white")
    )
    cu_fig.update_xaxes(
        rangeslider_visible=False,
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(step="all")
            ])
        )
    )   
    return cu_fig

def plot_hkdtwi(df):
    hkdtwi_df = df[['end_of_date', 'twi']].head(251)
    hkdtwi_fig = px.line(
        hkdtwi_df,
        x='end_of_date', y='twi',
        title='HKD Trade-Weighted Index (TWI)',
        labels={'end_of_date': 'Date', 'value': 'Value'},
    )
    last = hkdtwi_df.iloc[0]
    hkdtwi_fig.add_annotation(
        text=f"Date: {last['end_of_date'].strftime('%Y-%m-%d')}<br>TWI(HKD): {last['twi']}",
        xref="paper", yref="paper", x=1, y=1.2, showarrow=False,
        bgcolor="rgba(156, 33, 315, 1)", borderwidth=2,
        font=dict(size=12, color="white")
    )
    hkdtwi_fig.update_xaxes(
        rangeslider_visible=False,
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(step="all")
            ])
        )
    ) 
    return hkdtwi_fig

def plot_hsi():
    hsi = yf.Ticker("^HSI")
    hsi_df = hsi.history(period='251d').reset_index()
    hsi_df.set_index('Date', inplace=True)
    hsi_df.index = hsi_df.index.tz_localize(None)
    hsi_df.sort_values(by='Date', ascending=False, inplace=True)
    hsi_df['day_change'] = hsi_df['Close'] - hsi_df['Open']
    hsi_df = hsi_df.reset_index()
    hsi_fig = px.line(
        hsi_df,
        x='Date', y='Close',
        title='HSI',
        labels={'Date': 'Date', 'value': 'Value'},
    )
    last = hsi_df.iloc[0]
    hsi_fig.add_annotation(
        text=f"Date: {last['Date'].strftime('%Y-%m-%d')}<br>Index(HKD): {round(last['Close'],2)}",
        xref="paper", yref="paper", x=1, y=1.2, showarrow=False,
        bgcolor="rgba(156, 33, 315, 1)", borderwidth=2,
        font=dict(size=12, color="white")
    )
    hsi_fig.update_xaxes(
        rangeslider_visible=False,
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(step="all")
            ])
        )
    ) 
    return hsi_fig

def get_sofr(startDate, endDate) -> pd.DataFrame:
    sofr_url = f"https://markets.newyorkfed.org/read?productCode=50&eventCodes=525&startDt={startDate}&endDt={endDate}&fields=averageIndex30days&sort=postDt:1"
    sofr_response = requests.get(sofr_url).json()
    sofr_df = pd.DataFrame([
    {'postDt': i['postDt'], 'averageIndex30days': json.loads(i['data'])['averageIndex30days']}
    for i in sofr_response['data']
    ])
    sofr_df['postDt'] = pd.to_datetime(sofr_df['postDt'])
    sofr_df.columns = ['date', 'SOFR_1M']
    return sofr_df

def combine_hibor_sofr(hibor_df, sofr_df):
    hibor_df = hibor_df[['date', '1 Month']]
    hibor_df.columns = ['date', 'HIBOR_1M']

    hibor_sofr_df = pd.concat([sofr_df.set_index('date'), hibor_df.set_index('date')], axis=1).dropna().reset_index()
    hibor_sofr_df['SOFR minus HIBOR'] = hibor_sofr_df['SOFR_1M'] - hibor_sofr_df['HIBOR_1M']
    return hibor_sofr_df

def plot_sofr_vs_hibor(hibor_sofr_df):
    hibor_sofr_fig = px.line(
        hibor_sofr_df,
        x='date',
        y=['SOFR_1M', 'HIBOR_1M'],
        title='SOFR 1M vs HIBOR 1M',
        labels={'value': 'Rate (%)', 'date': 'Date'}
    )
    hibor_sofr_fig.update_xaxes(
        rangeslider_visible=False,
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(step="all")
            ])
        )
    )

    fig_diff = px.area(
        hibor_sofr_df,
        x='date',
        y='SOFR minus HIBOR',
        title='SOFR 1M minus HIBOR 1M',
        labels={'date': 'Date', 'SOFR minus HIBOR': 'SOFR 1M - HIBOR 1M (%)'}
    )
    fig_diff.update_xaxes(
        rangeslider_visible=False,
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(step="all")
            ])
        )
    )
    return hibor_sofr_fig, fig_diff


def generate_html(figs, output_path):
    html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Charts</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
</head>
<body>
    <h1>Charts</h1>
"""
    for i, (fig, title) in enumerate(figs, 1):
        html += "<hr>\n"
        html += f"<h2>{title}</h2>\n"
        html += fig.to_html(full_html=False, div_id=f"chart{i}", include_plotlyjs=True)
    html += "</body>\n</html>"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

def hkfigs_generation():
    df = fetch_interbank_liquidity()
    endDate = pd.Timestamp.now(tz='Asia/Hong_Kong').strftime('%Y-%m-%d')
    startDate = (pd.Timestamp.now(tz='Asia/Hong_Kong') - pd.Timedelta(days=365)).strftime('%Y-%m-%d')
    hibor_df = get_hibor(startDate, endDate).head(251)
    hibor_fig = plot_hibor(hibor_df)
    aggreBal_fig = plot_aggreBal(df)
    cu_fig = plot_currency(df)
    hkdtwi_fig = plot_hkdtwi(df)
    hsi_fig = plot_hsi()
    sofr_df = get_sofr(startDate, endDate)
    hibor_sofr_df = combine_hibor_sofr(hibor_df, sofr_df)
    hibor_sofr_fig, hibor_sofr_diff = plot_sofr_vs_hibor(hibor_sofr_df)
    figs = [
        (hibor_fig, "HIBOR"),
        (aggreBal_fig, "AggreBal"),
        (hsi_fig, "HSI"),
        (cu_fig, "Currency"),
        (hkdtwi_fig, "HKD--TWI"),
        (hibor_sofr_fig, "SOFR vs HIBOR"),
        (hibor_sofr_diff, "SOFR - HIBOR"),
    ]
    return figs


def main():
    figs = hkfigs_generation()
    output_path = '/home/runner/work/EconomyAnalysis/EconomyAnalysis/docs/hkcharts.html'
    generate_html(figs, output_path)

if __name__ == "__main__":
    main()