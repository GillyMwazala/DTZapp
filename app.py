import pandas as pd
import numpy as np
import yfinance as yf
import streamlit as st
import matplotlib.pyplot as plt

# Input parameters
asset_pair = st.selectbox("Select Asset Pair", ["BTC/USD", "XAU/USD"])
timeframe = st.selectbox("Select Timeframe", ["5m", "15m"])
data_source = st.selectbox("Select Data Source", ["CSV", "yfinance"])

# Load historical data
if data_source == "CSV":
    data = pd.read_csv(st.file_uploader("Upload CSV", type=["csv"]))
else:
    data = yf.download(asset_pair.replace("/", ""), interval=timeframe, period="7d")

# Calculate Previous Day's High and Low
data['Date'] = pd.to_datetime(data.index)
previous_day = data[data['Date'].dt.date == (data['Date'].dt.date.max() - pd.Timedelta(days=1))]
PDH = previous_day['High'].max()
PDL = previous_day['Low'].min()

# Calculate Tension Span
TS = PDH - PDL

# Define Micro-Tension Zones
MTZ1 = (PDL, PDL + 0.2 * TS)
MTZ2 = (PDL + 0.2 * TS, PDL + 0.4 * TS)
MTZ3 = (PDL + 0.4 * TS, PDL + 0.6 * TS)
MTZ4 = (PDL + 0.6 * TS, PDL + 0.8 * TS)
MTZ5 = (PDL + 0.8 * TS, PDH)

# Monitor Price Movement Across Zones
data['MTZ'] = np.where(data['Close'] <= MTZ1[1], 'MTZ1',
                np.where(data['Close'] <= MTZ2[1], 'MTZ2',
                np.where(data['Close'] <= MTZ3[1], 'MTZ3',
                np.where(data['Close'] <= MTZ4[1], 'MTZ4', 'MTZ5'))))

# Calculate Angle of Entry and Kinetic Pause
data['AoE'] = (data['Close'].diff(3) / 3).fillna(0)
data['KP'] = (data['MTZ'] == data['MTZ'].shift()).astype(int).groupby((data['MTZ'] != data['MTZ'].shift()).cumsum()).cumsum()

# Generate Trade Signals
def generate_signals(row):
    if row['MTZ'] == 'MTZ5' and row['AoE'] > 0.8 and row['KP'] < 2:
        return 'Recoil Entry'
    elif row['MTZ'] == 'MTZ2' and row['AoE'] < 0.4 and row['KP'] >= 5:
        return 'Absorption Entry'
    return None

data['Trade Signal'] = data.apply(generate_signals, axis=1)

# Plotting
plt.figure(figsize=(14, 7))
plt.plot(data['Close'], label='Close Price')
plt.axhline(PDH, color='red', linestyle='--', label='PDH')
plt.axhline(PDL, color='green', linestyle='--', label='PDL')
plt.title(f'{asset_pair} Price with Tension Zones')
plt.legend()
plt.show()

# Streamlit Dashboard
st.title("Dynamic Tension Zones Trading Strategy")
st.line_chart(data['Close'])
st.write(data[['Date', 'Close', 'Trade Signal']])
