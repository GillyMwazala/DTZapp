import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="Dynamic Tension Zones (DTZ)", layout="wide")
st.title("Dynamic Tension Zones (DTZ) - Gold & Bitcoin Short-Term Trade Framework")

# --- User Inputs ---
symbol = st.selectbox("Select Instrument", ["XAUUSD=X", "BTC-USD"], index=0)

interval = st.selectbox("Select Timeframe", ["5m", "15m"], index=0)
days_back = st.slider("Select Number of Past Days to Load", 2, 10, 3)

# --- Load Data ---
end_date = datetime.utcnow()
start_date = end_date - timedelta(days=days_back)

@st.cache_data(ttl=300)
def load_data(ticker, start, end, interval):
    data = yf.download(ticker, start=start, end=end, interval=interval)
    data.dropna(inplace=True)
    return data

data = load_data(symbol, start_date, end_date, interval)
data.index = pd.to_datetime(data.index)
data['Date'] = data.index.date

# --- Identify Previous Day's High/Low ---
yesterday = (datetime.utcnow() - timedelta(days=1)).date()
pd_data = data[data['Date'] == yesterday]

if pd_data.empty:
    st.warning("Not enough historical data to compute previous day's high/low.")
    st.stop()

PDH = pd_data['High'].max()
PDL = pd_data['Low'].min()
TS = PDH - PDL

# --- Define MTZs ---
MTZ = {
    'MTZ1': (PDL, PDL + 0.2 * TS),
    'MTZ2': (PDL + 0.2 * TS, PDL + 0.4 * TS),
    'MTZ3': (PDL + 0.4 * TS, PDL + 0.6 * TS),
    'MTZ4': (PDL + 0.6 * TS, PDL + 0.8 * TS),
    'MTZ5': (PDL + 0.8 * TS, PDH)
}

def get_mtz(price):  # price is a float
    for zone, (low, high) in MTZ.items():
        if low <= price <= high:
            return zone
    return None

# Apply to Close prices (scalar values)
data['MTZ'] = data['Close'].apply(lambda x: get_mtz(float(x)))

# --- Detect AoE and KP ---
data['Zone_Change'] = data['MTZ'] != data['MTZ'].shift(1)
data['KP_Counter'] = (~data['Zone_Change']).groupby((data['Zone_Change']).cumsum()).cumcount() + 1

# Angle of Entry (AoE)
def calculate_aoe(df, window=3):
    aoe_list = [None]*window
    for i in range(window, len(df)):
        delta_price = df['Close'].iloc[i] - df['Close'].iloc[i-window]
        delta_time = window * int(interval.replace("m", ""))
        aoe = delta_price / delta_time
        aoe_list.append(aoe)
    return aoe_list

data['AoE'] = calculate_aoe(data)

# --- Plotting ---
st.subheader(f"{symbol} | Previous Day High: {PDH:.2f} | Low: {PDL:.2f}")

fig = go.Figure()
fig.add_trace(go.Candlestick(
    x=data.index,
    open=data['Open'],
    high=data['High'],
    low=data['Low'],
    close=data['Close'],
    name='Price'
))

# Add MTZ bands
colors = {
    'MTZ1': 'rgba(255, 100, 100, 0.2)',
    'MTZ2': 'rgba(255, 165, 0, 0.2)',
    'MTZ3': 'rgba(255, 255, 0, 0.2)',
    'MTZ4': 'rgba(144, 238, 144, 0.2)',
    'MTZ5': 'rgba(173, 216, 230, 0.2)',
}
for zone, (low, high) in MTZ.items():
    fig.add_hrect(y0=low, y1=high, fillcolor=colors[zone], opacity=0.4, line_width=0)

fig.update_layout(height=600, xaxis_rangeslider_visible=False)
st.plotly_chart(fig, use_container_width=True)

# --- Display Insights ---
st.subheader("Recent Tension Zone Dynamics")
st.dataframe(data[['Close', 'MTZ', 'KP_Counter', 'AoE']].tail(30), use_container_width=True)

st.caption("This prototype uses the Dynamic Tension Zones model to track psychological price behavior across time.")
