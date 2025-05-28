import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd

st.title('Dynamic Tension Zones (DTZ) Strategy')

# Select asset pair and timeframe
asset_pair = st.selectbox('Asset Pair', ['BTC/USD', 'XAU/USD'])
timeframe = st.selectbox('Timeframe', ['5m', '15m'])

# Load historical data
try:
    data = yf.download(asset_pair, period='1d')
    st.write(f'Loaded {len(data)} data points')
except Exception as e:
    st.error(f'Failed to load data: {e}')
    data = pd.DataFrame()

# Calculate DTZ zones
if not data.empty:
    pdl = data['Low'].iloc[-1]
    pdh = data['High'].iloc[-1]
    if pdh <= pdl:
        st.error('Failed to calculate DTZ zones: High is less than or equal to Low')
        mtz_zones = []
    else:
        tension_span = pdh - pdl
        mtz_zones = (pdl + (tension_span * 0.2),
                    pdl + (tension_span * 0.4),
                    pdl + (tension_span * 0.6),
                    pdl + (tension_span * 0.8),
                    pdh)

# Plot candlestick chart with DTZ zones
if not data.empty and mtz_zones:
    fig = go.Figure(data=[go.Candlestick(x=data.index,
                                            open=data['Open'],
                                            high=data['High'],
                                            low=data['Low'],
                                            close=data['Close'])])
    for i, mtz in enumerate(mtz_zones):
        fig.add_annotation(x=data.index[-1],
                            y=mtz,
                            text=f'MTZ {i+1}',
                            showarrow=False)
    fig.update_layout(xaxis_title='Date',
                       yaxis_title='Price')
    st.plotly_chart(fig, use_container_width=True)

# Display AoE and KP values
if not data.empty and mtz_zones:
    aoe = (data['Close'].iloc[-1] - data['Close'].iloc[-4]) / 4
    kp = 1 if data['Close'].iloc[-1] == data['Close'].iloc[-2] else 0
    st.write(f'AoE: {aoe:.2f}')
    st.write(f'KP: {kp}')

# Display trade signals
if asset_pair == 'BTC/USD' and timeframe == '5m':
    st.write('Recoil Entry: Mean Reversion/Fade')
    st.write('Absorption Entry: Momentum Continuation')
elif asset_pair == 'XAU/USD' and timeframe == '15m':
    st.write('Recoil Entry: Mean Reversion/Fade')
    st.write('Absorption Entry: Momentum Continuation')
else:
    st.write('No trade signals available')
