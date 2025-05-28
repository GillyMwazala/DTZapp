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

# Display signals
if data.empty:
    st.write('No data loaded. Please select a valid asset pair and timeframe.')
else:
    # Calculate DTZ zones
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

    if mtz_zones:
        # Plot candlestick chart with DTZ zones
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
                           yaxis_title='Price',
                           xaxis_rangeslider_visible=True)
        fig.update_layout(title='Candlestick Chart')

        # Recoil Entry (Mean Reversion/Fade)
        if (data['Close'].iloc[-1] >= mtz_zones[0] and data['Close'].iloc[-1] <= mtz_zones[-1] and
            (data['Close'].iloc[-1] - data['Close'].iloc[-4]) / 4 > 0.8 and
            (data['Close'].iloc[-1] == data['Close'].iloc[-2] or data['Close'].iloc[-2] == data['Close'].iloc[-3])):
            fig.add_annotation(x=data.index[-1],
                                y=data['Close'].iloc[-1],
                                text='Recoil Entry: Mean Reversion/Fade',
                                showarrow=False,
                                textfont=dict(color='green'))
            st.write('Recoil Entry: Mean Reversion/Fade')
            st.write(f'Entry Zone: {mtz_zones[0]} to {mtz_zones[-1]}')
        elif (data['Close'].iloc[-1] >= mtz_zones[0] and data['Close'].iloc[-1] <= mtz_zones[-1] and
              (data['Close'].iloc[-1] - data['Close'].iloc[-4]) / 4 < 0.8 and
              (data['Close'].iloc[-1] == data['Close'].iloc[-2] or data['Close'].iloc[-2] == data['Close'].iloc[-3])):
            st.write('No Recoil Entry signal')

        # Absorption Entry (Momentum Continuation)
        if (data['Close'].iloc[-1] >= mtz_zones[1] and data['Close'].iloc[-1] <= mtz_zones[2] and
            (data['Close'].iloc[-1] - data['Close'].iloc[-4]) / 4 < 0.4 and
            (data['Close'].iloc[-1] == data['Close'].iloc[-2] or data['Close'].iloc[-2] == data['Close'].iloc[-3]) and
            (data['Close'].iloc[-1] - data['Close'].iloc[-6]) / 6 >= 0.4):
            fig.add_annotation(x=data.index[-1],
                                y=data['Close'].iloc[-1],
                                text='Absorption Entry: Momentum Continuation',
                                showarrow=False,
                                textfont=dict(color='green'))
            st.write('Absorption Entry: Momentum Continuation')
            st.write(f'Entry Zone: {mtz_zones[1]} to {mtz_zones[2]}')
        elif (data['Close'].iloc[-1] >= mtz_zones[1] and data['Close'].iloc[-1] <= mtz_zones[2] and
              (data['Close'].iloc[-1] - data['Close'].iloc[-4]) / 4 < 0.4 and
              (data['Close'].iloc[-1] == data['Close'].iloc[-2] or data['Close'].iloc[-2] == data['Close'].iloc[-3]) and
              (data['Close'].iloc[-1] - data['Close'].iloc[-6]) / 6 < 0.4):
            st.write('No Absorption Entry signal')

        st.plotly_chart(fig, use_container_width=True)

    else:
        st.write('No valid DTZ zones.')
