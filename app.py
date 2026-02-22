import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- CONFIGURATION & DATA LOADING ---
# Replace this with your actual raw GitHub URL for the dataset
GITHUB_CSV_URL = "https://raw.githubusercontent.com/your-username/your-repo/main/your-file.csv"

st.set_page_config(page_title="Crypto Volatility Visualizer", layout="wide")
st.title("📈 Crypto Volatility Visualizer")
st.markdown("Simulating Market Swings with Mathematics for AI (FA-2)")

@st.cache_data
def load_data(url):
    # Stage 4: Data Preparation & Exploration 
    df = pd.read_csv(url)
    # Convert Timestamp to proper date-time format 
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    # Handle missing data 
    df = df.dropna()
    # Rename columns for simplicity if needed 
    df = df.rename(columns={'Close': 'Price'})
    return df

try:
    data = load_data(GITHUB_CSV_URL)
    st.sidebar.success("Dataset Loaded Successfully")
except Exception as e:
    st.sidebar.error(f"Error loading data: {e}")
    # Placeholder data if GitHub link is not yet updated
    data = pd.DataFrame({
        'Timestamp': pd.date_range(start='2023-01-01', periods=100, freq='D'),
        'Price': np.random.randint(20000, 30000, 100),
        'High': np.random.randint(30000, 35000, 100),
        'Low': np.random.randint(15000, 20000, 100),
        'Volume': np.random.randint(1000, 5000, 100)
    })

# --- STAGE 2 & 5: SIDEBAR CONTROLS ---
# Controls based on FA1 Slides and FA2 Requirements [cite: 20, 11]
st.sidebar.header("Simulation Parameters")

pattern = st.sidebar.selectbox("Pattern Selector", 
                               ["Sine Wave", "Cosine Wave", "Random Noise"], 
                               help="Choose how the price moves ")

amplitude = st.sidebar.slider("Amplitude (Volatility)", 0, 100, 40, 
                              help="Small (0-20): Stable | Large (60-100): High Risk [cite: 21]")

frequency = st.sidebar.slider("Frequency (Swing Speed)", 0.1, 5.0, 1.0, 
                              help="Changes how fast the price oscillates [cite: 21]")

drift = st.sidebar.slider("Drift (Trend)", -10.0, 10.0, 0.0, 
                          help="Adds a long-term upward or downward slope [cite: 21]")

noise_level = st.sidebar.slider("Noise Control", 0, 50, 10, 
                                help="Simulate random market shocks ")

comparison_mode = st.sidebar.checkbox("Comparison Mode (Stable vs Volatile)", 
                                     help="Shows two graphs side-by-side [cite: 22]")

# --- MATHEMATICAL SIMULATION FUNCTIONS ---
# Functions to create wave-like swings and drift 
def generate_simulation(base_data, amp, freq, drft, pattern_type, noise):
    t = np.linspace(0, 10, len(base_data))
    
    # Pattern selection logic 
    if pattern_type == "Sine Wave":
        wave = amp * np.sin(freq * t)
    elif pattern_type == "Cosine Wave":
        wave = amp * np.cos(freq * t)
    else: # Random Noise only
        wave = np.zeros(len(t))
    
    # Adding Drift (Integral/Slope) and Noise (Shocks) 
    drift_line = drft * t
    random_shocks = np.random.normal(0, noise, len(t))
    
    # Combining math functions to simulate price 
    simulated_price = base_data['Price'].iloc[0] + wave + drift_line + random_shocks
    return simulated_price

# --- STAGE 5: BUILD VISUALIZATIONS ---
# Interactive graphs using Plotly 

if comparison_mode:
    # Comparison Mode: Side-by-side graphs [cite: 22]
    col1, col2 = st.columns(2)
    
    # Stable simulation (Low amplitude)
    stable_sim = generate_simulation(data, 10, 0.5, 0, "Sine Wave", 2)
    with col1:
        st.subheader("Stable Asset Simulation")
        fig_stable = go.Figure()
        fig_stable.add_trace(go.Scatter(x=data['Timestamp'], y=stable_sim, name="Stable"))
        st.plotly_chart(fig_stable, use_container_width=True)
        
    # Volatile simulation (User controlled)
    volatile_sim = generate_simulation(data, amplitude, frequency, drift, pattern, noise_level)
    with col2:
        st.subheader("Volatile Asset Simulation")
        fig_vol = go.Figure()
        fig_vol.add_trace(go.Scatter(x=data['Timestamp'], y=volatile_sim, name="Volatile", line=dict(color='red')))
        st.plotly_chart(fig_vol, use_container_width=True)

else:
    # Main Dashboard Visualization 
    st.subheader("Simulated Price vs Real Market Data")
    sim_price = generate_simulation(data, amplitude, frequency, drift, pattern, noise_level)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data['Timestamp'], y=data['Price'], name="Real Price (Close)"))
    fig.add_trace(go.Scatter(x=data['Timestamp'], y=sim_price, name="Simulated Price", line=dict(dash='dash')))
    st.plotly_chart(fig, use_container_width=True)

    # High vs Low Comparison & Volume Analysis 
    st.subheader("Market Indicators")
    tab1, tab2 = st.tabs(["High vs Low", "Trading Volume"])
    
    with tab1:
        fig_hl = go.Figure()
        fig_hl.add_trace(go.Scatter(x=data['Timestamp'], y=data['High'], name="High Price"))
        fig_hl.add_trace(go.Scatter(x=data['Timestamp'], y=data['Low'], name="Low Price"))
        st.plotly_chart(fig_hl, use_container_width=True)
        
    with tab2:
        fig_vol = go.Bar(x=data['Timestamp'], y=data['Volume'], name="Volume")
        st.plotly_chart(go.Figure(data=[fig_vol]), use_container_width=True)

st.markdown("---")
st.info("This app uses Sine/Cosine for cycles, Integrals for drift, and Random Noise for market shocks. [cite: 5, 11]")
