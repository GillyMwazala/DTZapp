import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd

st.title('Dynamic Tension Zones (DTZ) Strategy')

# Asset selection
asset_map = {'BTC/USD': 'BTC-USD', 'XAU/USD': 'XAUUSD=X'}
asset_label = st.selectbox('Asset Pair', list(asset_map.keys()))
symbol = asset_map[asset_label]

# Timeframe selection
timeframe = st.selectbox('Timeframe', ['5m', '15m'])
interval = '5m' if timeframe == '5m' else '15m'

# Download past 2 days of data
try:
    data = yf.download(tickers=symbol, period='2d', interval=interval)
    data.dropna(inplace=True)
    st.success(f"Loaded {len(data)} bars of {interval} data for {asset_label}")
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

if len(data) < 20:
    st.warning("Insufficient data to determine signals.")
    st.stop()

# Separate previous day and today's candles
prev_day = data.iloc[:-100]
recent = data.iloc[-100:]

# Calculate PDH/PDL from previous day
pdh = prev_day['High'].max()
pdl = prev_day['Low'].min()
ts = pdh - pdl

# Define 5 MTZ zones
mtz_zones = [pdl + ts * i * 0.2 for i in range(6)]
zone_labels = [f'MTZ {i+1}' for i in range(5)]

# Label each candle with its current zone
recent['zone'] = pd.cut(recent['Close'], bins=mtz_zones, labels=zone_labels, include_lowest=True)

# Calculate AoE (slope of price move over 4 candles)
recent['AoE'] = (recent['Close'] - recent['Close'].shift(4)) / 4

# Calculate KP (consecutive bars in same zone)
recent['KP'] = recent['zone'].eq(recent['zone'].shift()).astype(int)
recent['KP'] = recent['KP'].rolling(window=5).sum().fillna(0)

# Last row for analysis
last = recent.iloc[-1]
zone = last['zone']
aoe = last['AoE']
kp = last['KP']
close_price = last['Close']

# Setup chart
fig = go.Figure(data=[go.Candlestick(
    x=recent.index,
    open=recent['Open'],
    high=recent['High'],
    low=recent['Low'],
    close=recent['Close']
)])

# Add MTZ zone lines
for i in range(1, 5):
    fig.add_hline(y=mtz_zones[i], line_dash='dot',
                  annotation_text=zone_labels[i-1], annotation_position='top left')

# Signal detection logic
if zone in ['MTZ 1', 'MTZ 5'] and aoe > 0.8 and kp <= 2:
    fig.add_annotation(x=recent.index[-1], y=close_price,
                       text='Recoil Entry', arrowhead=2, arrowcolor='green')
    st.success("📈 Recoil Entry Signal Detected")

elif zone in ['MTZ 2', 'MTZ 3'] and aoe < 0.4 and kp >= 3:
    fig.add_annotation(x=recent.index[-1], y=close_price,
                       text='Absorption Entry', arrowhead=2, arrowcolor='blue')
    st.success("⚡ Absorption Entry Signal Detected")

else:
    st.info("No clear entry signal at the moment.")

fig.update_layout(title=f'DTZ Zones for {asset_label}',
                  xaxis_title='Time', yaxis_title='Price',
                  xaxis_rangeslider_visible=False)

st.plotly_chart(fig, use_container_width=True)
