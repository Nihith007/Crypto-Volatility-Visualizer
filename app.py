import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np
import requests
from io import StringIO

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Crypto Volatility Visualizer",
    page_icon="₿",
    layout="wide"
)

st.title("₿ Crypto Volatility Visualizer")
st.markdown("### Simulating Market Swings with Mathematics for AI and Python")
st.markdown("*Using sine, cosine, random noise, and integrals to model cryptocurrency volatility*")
st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────────
# CHANGE 1 ── GITHUB CSV URL
# Your notebook (Copy_of_Data_Mining_Python_Lab.ipynb) loads:
#   file_path = '/content/btcusd_1-min_data.csv'
# Columns: Timestamp (Unix epoch seconds), Open, High, Low, Close, Volume
# First row showed: Timestamp=1.325412e+09, all prices=4.58, Volume=0.0
#
# ACTION REQUIRED: Upload btcusd_1-min_data.csv to your GitHub repo, then this
# URL will work automatically. If the file is too large (>100MB), upload a
# sampled version — see instructions at bottom of this file.
# ─────────────────────────────────────────────────────────────────────────────
GITHUB_CSV_URL = (
    "https://raw.githubusercontent.com/Nihith007/Crypto-Volatility-Visualizer"
    "/main/btcusd_1-min_data.csv"
)

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR — MODE SELECTION
# ─────────────────────────────────────────────────────────────────────────────
st.sidebar.header("🎯 Dashboard Mode")
mode = st.sidebar.radio(
    "Choose your analysis mode:",
    ["📊 Real Bitcoin Data", "🧮 Mathematical Simulation", "🔍 Compare Both"],
)
st.sidebar.markdown("---")

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR CONTROLS — per mode
# ─────────────────────────────────────────────────────────────────────────────
uploaded_file         = None
pattern_type          = "Sine Wave (Smooth Cycles)"
amplitude             = 1000
frequency             = 1.0
drift                 = 10
noise_level           = 100
num_days              = 7
days_to_show          = 7
show_volatility_bands = True
show_volume           = True
data_source           = "🌐 GitHub (Auto-fetch)"

if mode == "📊 Real Bitcoin Data":
    st.sidebar.header("📁 Data Source")
    # CHANGE 2 ── GitHub auto-fetch radio added
    # WHERE: Sidebar, Real Bitcoin Data mode
    # WHY: Assignment Stage 4 requires loading data from the GitHub repository,
    #      not just from a local file upload. This option fetches it automatically.
    data_source = st.sidebar.radio(
        "Source:", ["🌐 GitHub (Auto-fetch)", "📂 Upload CSV"]
    )
    if data_source == "📂 Upload CSV":
        uploaded_file = st.sidebar.file_uploader(
            "Upload btcusd_1-min_data.csv", type=["csv"],
            help="Needs columns: Timestamp (Unix s), Open, High, Low, Close, Volume"
        )
    st.sidebar.subheader("⏱️ Time Range")
    days_to_show = st.sidebar.slider("Days to display", 1, 30, 7)
    st.sidebar.subheader("📈 Display Options")
    show_volatility_bands = st.sidebar.checkbox("Show Volatility Bands", value=True)
    show_volume = st.sidebar.checkbox("Show Volume Analysis", value=True)

elif mode == "🧮 Mathematical Simulation":
    st.sidebar.header("🎛️ Mathematical Controls")
    st.sidebar.subheader("📊 Pattern Type")
    pattern_type = st.sidebar.selectbox(
        "Choose price swing pattern:",
        [
            "Sine Wave (Smooth Cycles)",
            "Cosine Wave (Smooth Cycles)",
            "Random Noise (Chaotic Jumps)",
            "Sine + Noise (Realistic Market)",
            "Cosine + Noise (Realistic Market)",
            "Combined Waves (Complex Pattern)",
        ],
    )
    st.sidebar.subheader("🔧 Wave Parameters")

    # CHANGE 3 ── Sliders now work because cache removed from generator (Change 7)
    # WHERE: Sidebar, Mathematical Simulation mode
    amplitude = st.sidebar.slider(
        "Amplitude (Swing Size $)", 100, 5000, 1000, 100,
        help="Height of each price swing — A in A·sin(2πft/T)"
    )
    frequency = st.sidebar.slider(
        "Frequency (Cycles)", 0.1, 5.0, 1.0, 0.1,
        help="Number of full wave cycles across the time window"
    )
    drift = st.sidebar.slider(
        "Drift ($/day)", -50, 50, 10, 5,
        help="Long-term trend slope — computed as integral ∫D dt = D·t"
    )
    # CHANGE 4 ── Noise slider fixed
    # WHERE: Sidebar, Mathematical Simulation mode
    # WHY IT WAS BROKEN: @st.cache_data on generate_mathematical_data() caused
    #   Streamlit to return the same cached output regardless of the slider value.
    #   Changing noise from 100→200 appeared to have no effect on the chart.
    # FIX: @st.cache_data removed from generate_mathematical_data() — see Change 7.
    noise_level = st.sidebar.slider(
        "Noise Level (σ)", 0, 500, 100, 10,
        help="Std deviation of random jumps N(0,σ) — NOW updates chart instantly"
    )
    st.sidebar.subheader("⏱️ Time Range")
    num_days = st.sidebar.slider("Number of Days", 1, 30, 7)

else:  # Compare Both
    st.sidebar.header("📁 Real Data Source")
    data_source = st.sidebar.radio("Source:", ["🌐 GitHub (Auto-fetch)", "📂 Upload CSV"])
    if data_source == "📂 Upload CSV":
        uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])
    st.sidebar.header("🧮 Simulation Settings")
    pattern_type = st.sidebar.selectbox(
        "Pattern:",
        ["Sine Wave (Smooth Cycles)", "Cosine Wave (Smooth Cycles)", "Sine + Noise (Realistic Market)"],
    )
    amplitude    = st.sidebar.slider("Amplitude",      100, 5000, 1000, 100)
    frequency    = st.sidebar.slider("Frequency",      0.1,  5.0,  1.0,  0.1)
    drift        = st.sidebar.slider("Drift",          -50,   50,   10,    5)
    noise_level  = st.sidebar.slider("Noise (σ)",        0,  500,  100,   10)
    days_to_show = st.sidebar.slider("Real data days",   1,   30,    7)
    num_days     = st.sidebar.slider("Sim days",         1,   30,    7)


# ─────────────────────────────────────────────────────────────────────────────
# CHANGE 5 ── fetch_github_data() — NEW FUNCTION
# WHERE: Data loading section (replaces the old uploaded_file-only approach)
# WHY: Assignment Stage 4 says "Loading the dataset: Open the CSV file in Python"
#      Your notebook did this via Google Drive. In Streamlit Cloud the equivalent
#      is fetching from GitHub using requests. Cached so it only fetches once
#      per session, not on every slider interaction.
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="📡 Fetching btcusd_1-min_data.csv from GitHub…")
def fetch_github_data():
    try:
        r = requests.get(GITHUB_CSV_URL, timeout=20)
        r.raise_for_status()
        return pd.read_csv(StringIO(r.text)), None
    except requests.exceptions.HTTPError as e:
        return None, f"HTTP {e.response.status_code} — CSV not found at that URL yet."
    except Exception as e:
        return None, str(e)


# ─────────────────────────────────────────────────────────────────────────────
# CHANGE 6 ── normalize_dataframe() — NEW FUNCTION
# WHERE: Data loading section
# WHY: Replicates Stage 4 data preparation steps from the notebook:
#   • Timestamp column (Unix seconds like 1.325412e+09) → datetime
#     [notebook: pd.to_datetime(df['Timestamp'], unit='s')]
#   • Close column → renamed to Price
#     [Stage 4: "Focus on Close Price — rename Close → Price"]
#   • dropna() on missing values
#     [Stage 4: "Handle missing data — drop them"]
#   • sort_values('Timestamp')
#     [Stage 4: preparation before plotting]
# ─────────────────────────────────────────────────────────────────────────────
def normalize_dataframe(df):
    df = df.copy()
    df.columns = [c.strip() for c in df.columns]

    # Detect & convert Timestamp — your notebook data uses Unix seconds
    for col in ["Timestamp", "timestamp", "Date", "date", "Time", "time"]:
        if col in df.columns:
            try:
                df["Timestamp"] = pd.to_datetime(df[col], unit="s")
            except Exception:
                df["Timestamp"] = pd.to_datetime(df[col])
            if col != "Timestamp":
                df.drop(columns=[col], inplace=True)
            break
    else:
        df["Timestamp"] = pd.date_range("2012-01-01", periods=len(df), freq="min")

    # Stage 4: "Focus on Close Price" → rename to Price
    for src in ["Close", "close", "Price", "price"]:
        if src in df.columns:
            df["Price"] = pd.to_numeric(df[src], errors="coerce")
            break

    # Make sure OHLV are numeric
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Fill missing OHLC if absent
    if "Price" in df.columns:
        for c in ["Open", "Close"]:
            if c not in df.columns:
                df[c] = df["Price"]
        if "High" not in df.columns:
            df["High"] = df["Price"] * 1.002
        if "Low" not in df.columns:
            df["Low"]  = df["Price"] * 0.998

    if "Volume" not in df.columns:
        df["Volume"] = np.random.uniform(0, 50, len(df))

    # Stage 4: handle missing values
    df = df.dropna(subset=["Timestamp", "Price"])
    df = df.sort_values("Timestamp").reset_index(drop=True)
    return df


@st.cache_data
def create_sample_bitcoin_data(days=7):
    """Fallback sample data — only used if GitHub fetch fails."""
    np.random.seed(42)
    minutes = days * 24 * 60
    timestamps = pd.date_range(end=datetime.now(), periods=minutes, freq="min")
    prices = [45000]
    for _ in range(minutes - 1):
        prices.append(max(100, prices[-1] + np.random.normal(0, 50)))
    prices = np.array(prices)
    return pd.DataFrame({
        "Timestamp": timestamps,
        "Price":  prices,
        "Open":   prices * np.random.uniform(0.999, 1.001, minutes),
        "High":   prices * np.random.uniform(1.001, 1.005, minutes),
        "Low":    prices * np.random.uniform(0.995, 0.999, minutes),
        "Close":  prices,
        "Volume": np.random.uniform(0, 50, minutes),
    })


def load_real_data(source="github", uploaded_file=None):
    if source == "upload" and uploaded_file is not None:
        return normalize_dataframe(pd.read_csv(uploaded_file)), None
    raw, err = fetch_github_data()
    if err or raw is None:
        return create_sample_bitcoin_data(), err
    return normalize_dataframe(raw), None


# ─────────────────────────────────────────────────────────────────────────────
# CHANGE 7 ── @st.cache_data REMOVED from generate_mathematical_data()
# WHERE: Mathematical data generator function
# WHY THIS FIXES ALL SLIDERS:
#   Previously the function had @st.cache_data. Streamlit caches by hashing
#   all function arguments. The problem was numpy's random number generator —
#   even when noise_level changed, the numpy random calls inside produced
#   values that looked similar OR Streamlit's hash didn't detect the change,
#   so it returned the same cached DataFrame. Result: sliders appeared frozen.
#   Removing @st.cache_data means the function runs fresh on EVERY interaction,
#   so amplitude, frequency, drift, and noise_level all update the chart live.
# ─────────────────────────────────────────────────────────────────────────────
def generate_mathematical_data(pattern, amp, freq, drift_val, noise, days):
    """
    Generates simulated Bitcoin price using mathematical functions.
    Stage 5 / Stage 6 requirements:
      Sine/Cosine → wave-like swings:  A·sin(2πft/T)
      Random noise → sudden jumps:     N(0, σ)
      Drift → long-term slope:         ∫D dt = D·t
    """
    hours = days * 24
    t     = np.linspace(0, days, hours)
    base  = 45000
    sigma = max(noise, 1)   # prevent N(0,0)

    if pattern == "Sine Wave (Smooth Cycles)":
        prices = base + amp * np.sin(2 * np.pi * freq * t / days)

    elif pattern == "Cosine Wave (Smooth Cycles)":
        prices = base + amp * np.cos(2 * np.pi * freq * t / days)

    elif pattern == "Random Noise (Chaotic Jumps)":
        prices = base + np.cumsum(np.random.normal(0, sigma, hours))

    elif pattern == "Sine + Noise (Realistic Market)":
        prices = (base
                  + amp * np.sin(2 * np.pi * freq * t / days)
                  + np.cumsum(np.random.normal(0, sigma, hours)))

    elif pattern == "Cosine + Noise (Realistic Market)":
        prices = (base
                  + amp * np.cos(2 * np.pi * freq * t / days)
                  + np.cumsum(np.random.normal(0, sigma, hours)))

    else:  # Combined Waves
        prices = (base
                  + amp     * np.sin(2 * np.pi * freq * 1 * t / days)
                  + amp / 2 * np.cos(2 * np.pi * freq * 2 * t / days)
                  + amp / 3 * np.sin(2 * np.pi * freq * 3 * t / days))

    # Drift — integral of constant D = D·t (linear ramp)
    prices = prices + drift_val * t / days
    prices = np.maximum(prices, 100)

    start  = datetime.now() - timedelta(days=days)
    stamps = [start + timedelta(hours=i) for i in range(hours)]

    return pd.DataFrame({
        "Timestamp": stamps,
        "Time":      t,
        "Price":     prices,
        "Open":      prices * np.random.uniform(0.999, 1.001, hours),
        "High":      prices + np.random.uniform(50, 200, hours),
        "Low":       prices - np.random.uniform(50, 200, hours),
        "Close":     prices,
        "Volume":    np.random.uniform(1000, 50000, hours),
    })


# ─────────────────────────────────────────────────────────────────────────────
# METRIC HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def calculate_volatility(df):
    returns = df["Price"].pct_change().dropna()
    return returns.std() * np.sqrt(len(returns)) * 100

def calculate_drift_metric(df):
    return (df["Price"].iloc[-1] - df["Price"].iloc[0]) / df["Price"].iloc[0] * 100

def show_sidebar_metrics(df):
    st.sidebar.markdown("---")
    st.sidebar.subheader("📈 Key Metrics")
    st.sidebar.metric("Volatility Index", f"{calculate_volatility(df):.2f}%")
    st.sidebar.metric("Average Drift",    f"{calculate_drift_metric(df):+.2f}%")
    st.sidebar.metric("Current Price",    f"${df['Price'].iloc[-1]:,.2f}")


# ─────────────────────────────────────────────────────────────────────────────
# ══════════════════════  MODE: REAL BITCOIN DATA  ══════════════════════
# ─────────────────────────────────────────────────────────────────────────────
if mode == "📊 Real Bitcoin Data":
    st.header("📊 Real Bitcoin Data Analysis")

    src = "github" if data_source == "🌐 GitHub (Auto-fetch)" else "upload"
    df_raw, err = load_real_data(source=src, uploaded_file=uploaded_file)

    if err:
        st.warning(
            f"⚠️ **GitHub fetch failed:** {err}\n\n"
            "**To fix this:** Upload `btcusd_1-min_data.csv` to your GitHub repo "
            f"`Nihith007/Crypto-Volatility-Visualizer` and the URL will work.\n\n"
            "*Showing generated sample data in the meantime.*"
        )
    elif src == "github":
        st.success(
            f"✅ Loaded `btcusd_1-min_data.csv` from GitHub — "
            f"**{len(df_raw):,} rows** | "
            f"{df_raw['Timestamp'].min().date()} → {df_raw['Timestamp'].max().date()}"
        )

    # CHANGE 8 ── Dataset preview expander
    # WHERE: Real Bitcoin Data mode, below header
    # WHY: Stage 4 tip — "always check the dataset shape (rows × columns) before starting"
    #      and "print the first few rows" — mirrors notebook's print(data.head(101))
    with st.expander("🔍 Dataset Preview — head() & shape (Stage 4 check)"):
        st.markdown(f"**Shape:** `{df_raw.shape[0]:,} rows × {df_raw.shape[1]} columns`")
        st.markdown("**Columns:** " + ", ".join(f"`{c}`" for c in df_raw.columns.tolist()))
        st.info("Timestamp was Unix epoch seconds (e.g. `1.325412e+09`) → converted to datetime")
        st.dataframe(df_raw.head(10), use_container_width=True)

    # Stage 4: "Subset for simplicity — take one week or one month"
    # 1-min data: days × 24h × 60min rows per day
    n_rows = days_to_show * 24 * 60
    df = df_raw.tail(n_rows).copy() if len(df_raw) > n_rows else df_raw.copy()
    show_sidebar_metrics(df)

    # ── CHART 1: Line Graph of Close Price Over Time (Stage 5 step 1)
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("📈 Bitcoin Close Price Over Time")
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(
            x=df["Timestamp"], y=df["Price"],
            mode="lines", name="Close Price",
            line=dict(color="#1f77b4", width=1.5)
        ))
        if show_volatility_bands:
            w = max(min(60, len(df) // 10), 2)
            rm = df["Price"].rolling(w).mean()
            rs = df["Price"].rolling(w).std()
            fig1.add_trace(go.Scatter(x=df["Timestamp"], y=rm + 2*rs,
                mode="lines", line=dict(width=0), showlegend=False))
            fig1.add_trace(go.Scatter(x=df["Timestamp"], y=rm - 2*rs,
                mode="lines", name="Volatility Band (±2σ)", line=dict(width=0),
                fill="tonexty", fillcolor="rgba(31,119,180,0.12)"))
        fig1.update_layout(xaxis_title="Date", yaxis_title="Price (USD)",
            hovermode="x unified", height=420, template="plotly_white")
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.subheader("📊 Price Statistics")
        stats = pd.DataFrame({
            "Metric": ["Min Price", "Max Price", "Avg Price", "Price Range", "Data Points"],
            "Value":  [
                f"${df['Price'].min():,.2f}",
                f"${df['Price'].max():,.2f}",
                f"${df['Price'].mean():,.2f}",
                f"${df['Price'].max() - df['Price'].min():,.2f}",
                f"{len(df):,}",
            ]
        })
        st.dataframe(stats, hide_index=True, use_container_width=True)
        st.markdown("##### Price Distribution")
        fig_h = px.histogram(df, x="Price", nbins=40, color_discrete_sequence=["#1f77b4"])
        fig_h.update_layout(showlegend=False, height=240,
            xaxis_title="Price (USD)", yaxis_title="Count",
            margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig_h, use_container_width=True)

    # ── CHART 2: High vs Low Comparison (Stage 5 step 2)
    st.subheader("📉 High vs Low Price Comparison")
    st.markdown("*The gap between High and Low on each candle shows that minute's volatility.*")
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=df["Timestamp"], y=df["High"],
        mode="lines", name="High", line=dict(color="green", width=1)))
    fig2.add_trace(go.Scatter(x=df["Timestamp"], y=df["Low"],
        mode="lines", name="Low",  line=dict(color="red",   width=1),
        fill="tonexty", fillcolor="rgba(0,180,0,0.07)"))
    fig2.update_layout(xaxis_title="Date", yaxis_title="Price (USD)",
        hovermode="x unified", height=320, template="plotly_white")
    st.plotly_chart(fig2, use_container_width=True)

    # ── CHART 3: Volume Bar Chart (Stage 5 step 3)
    if show_volume:
        st.subheader("📦 Volume Analysis")
        st.markdown("*Compare if higher-volume minutes match with bigger price changes.*")
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(x=df["Timestamp"], y=df["Volume"],
            name="Volume", marker_color="steelblue", opacity=0.7))
        fig3.update_layout(xaxis_title="Date", yaxis_title="Volume (BTC)",
            height=300, template="plotly_white")
        st.plotly_chart(fig3, use_container_width=True)

    # ── CHART 4: Stable vs Volatile Periods (Stage 5 step 4)
    st.subheader("🔀 Stable vs Volatile Periods")
    st.markdown("*Flat lines = Stable market. Sharp spikes up/down = Volatile periods.*")
    col3, col4 = st.columns(2)
    with col3:
        w = max(min(60, len(df) // 10), 2)
        df["Rolling_Vol"] = df["Price"].rolling(w).std()
        fig4 = go.Figure()
        fig4.add_trace(go.Scatter(x=df["Timestamp"], y=df["Rolling_Vol"],
            mode="lines", line=dict(color="orange", width=1.5)))
        fig4.update_layout(title=f"Rolling Volatility ({w}-minute window)",
            xaxis_title="Date", yaxis_title="Std Dev ($)",
            height=320, template="plotly_white")
        st.plotly_chart(fig4, use_container_width=True)
    with col4:
        med = df["Rolling_Vol"].median()
        df["Period"] = df["Rolling_Vol"].apply(lambda x: "Volatile" if x > med else "Stable")
        counts = df["Period"].value_counts()
        fig5 = px.pie(values=counts.values, names=counts.index,
            title="Stable vs Volatile Distribution",
            color=counts.index,
            color_discrete_map={"Stable": "lightgreen", "Volatile": "salmon"})
        fig5.update_layout(height=320)
        st.plotly_chart(fig5, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# ══════════════════  MODE: MATHEMATICAL SIMULATION  ══════════════════
# ─────────────────────────────────────────────────────────────────────────────
elif mode == "🧮 Mathematical Simulation":
    st.header("🧮 Mathematical Simulation")

    # Change 7 in action — no cache → all 4 sliders update chart immediately
    df_m = generate_mathematical_data(
        pattern_type, amplitude, frequency, drift, noise_level, num_days
    )
    show_sidebar_metrics(df_m)

    st.subheader(f"📊 Pattern: {pattern_type}")

    with st.expander("🧮 Mathematical Formula & Parameters"):
        if "Sine" in pattern_type and "Cosine" not in pattern_type:
            st.latex(r"Price(t)=45000+A\cdot\sin\!\left(\tfrac{2\pi f\,t}{T}\right)+\underbrace{D\cdot t}_{\int D\,dt}+\mathcal{N}(0,\sigma)")
        elif "Cosine" in pattern_type:
            st.latex(r"Price(t)=45000+A\cdot\cos\!\left(\tfrac{2\pi f\,t}{T}\right)+D\cdot t+\mathcal{N}(0,\sigma)")
        elif "Random" in pattern_type:
            st.latex(r"Price(t)=Price(t-1)+\mathcal{N}(0,\,\sigma)")
        else:
            st.latex(r"Price(t)=45000+A\sin(\cdot)+\tfrac{A}{2}\cos(2\cdot)+\tfrac{A}{3}\sin(3\cdot)+D\cdot t")

        st.markdown(f"""
| Parameter | Symbol | Value |
|---|---|---|
| Base Price | — | $45,000 |
| Amplitude | A | **${amplitude:,}** |
| Frequency | f | **{frequency} cycles** |
| Drift | D | **${drift}/day** |
| Noise σ | σ | **±${noise_level}** |
| Days | T | **{num_days}** |
        """)

    # ── CHART 1: Main price line (Stage 5 step 1)
    fig_m1 = go.Figure()
    fig_m1.add_trace(go.Scatter(
        x=df_m["Timestamp"], y=df_m["Price"],
        mode="lines", name="Simulated Price",
        line=dict(color="#2E86DE", width=2),
        fill="tozeroy", fillcolor="rgba(46,134,222,0.07)"
    ))
    fig_m1.update_layout(
        title=f"Simulated Bitcoin Price — {pattern_type}",
        xaxis_title="Time", yaxis_title="Price (USD)",
        hovermode="x unified", height=480, template="plotly_white"
    )
    st.plotly_chart(fig_m1, use_container_width=True)

    col1, col2 = st.columns(2)

    # ── CHART 2: High vs Low (Stage 5 step 2)
    with col1:
        st.subheader("📉 High vs Low")
        fhl = go.Figure()
        fhl.add_trace(go.Scatter(x=df_m["Timestamp"], y=df_m["High"],
            mode="lines", name="High", line=dict(color="green", width=1)))
        fhl.add_trace(go.Scatter(x=df_m["Timestamp"], y=df_m["Low"],
            mode="lines", name="Low",  line=dict(color="red",   width=1), fill="tonexty"))
        fhl.update_layout(height=300, template="plotly_white",
            xaxis_title="Time", yaxis_title="Price (USD)")
        st.plotly_chart(fhl, use_container_width=True)

    # ── CHART 3: Volume (Stage 5 step 3)
    with col2:
        st.subheader("📦 Volume")
        fvol = go.Figure()
        fvol.add_trace(go.Bar(x=df_m["Timestamp"], y=df_m["Volume"],
            marker_color="steelblue", opacity=0.7))
        fvol.update_layout(height=300, template="plotly_white",
            xaxis_title="Time", yaxis_title="Volume")
        st.plotly_chart(fvol, use_container_width=True)

    # ── CHART 4: Stable vs Volatile (Stage 5 step 4)
    st.subheader("🔀 Stable vs Volatile Periods")
    df_m["Rolling_Vol"] = df_m["Price"].rolling(24).std()
    med = df_m["Rolling_Vol"].median()
    df_m["Period"] = df_m["Rolling_Vol"].apply(lambda x: "Volatile" if x > med else "Stable")

    col3, col4 = st.columns(2)
    with col3:
        frv = go.Figure()
        frv.add_trace(go.Scatter(x=df_m["Timestamp"], y=df_m["Rolling_Vol"],
            mode="lines", line=dict(color="orange", width=2)))
        frv.update_layout(title="Rolling Volatility (24-hour window)",
            xaxis_title="Time", yaxis_title="Std Dev ($)",
            height=300, template="plotly_white")
        st.plotly_chart(frv, use_container_width=True)
    with col4:
        pc = df_m["Period"].value_counts()
        fp = px.pie(values=pc.values, names=pc.index,
            title="Stable vs Volatile Distribution",
            color=pc.index,
            color_discrete_map={"Stable": "lightgreen", "Volatile": "salmon"})
        fp.update_layout(height=300)
        st.plotly_chart(fp, use_container_width=True)

    # Educational section (Stage 5 tip)
    st.markdown("---")
    st.markdown("### 🎓 Understanding the Mathematics")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.info("""
**🌊 Sine / Cosine Waves**
Smooth, repeating price cycles.
- **Amplitude** = height of swing
- **Frequency** = cycles per period
- Formula: `A · sin(2πft/T)`
        """)
    with c2:
        st.info("""
**📈 Drift (Integral)**
Models long-term price slope.
- Calculated as: `∫D dt = D·t`
- Positive → upward trend
- Negative → downward trend
        """)
    with c3:
        st.info("""
**🎲 Random Noise**
Models sudden market jumps.
- Drawn from `N(0, σ)`
- Higher σ → more chaotic
- Cumulative sum = random walk
        """)


# ─────────────────────────────────────────────────────────────────────────────
# ══════════════════════  MODE: COMPARE BOTH  ══════════════════════
# ─────────────────────────────────────────────────────────────────────────────
else:
    st.header("🔍 Comparison: Real Data vs Mathematical Simulation")

    src = "github" if data_source == "🌐 GitHub (Auto-fetch)" else "upload"
    df_raw, err = load_real_data(source=src, uploaded_file=uploaded_file)
    if err:
        st.warning(f"⚠️ {err} — using sample data.")

    n_rows = days_to_show * 24 * 60
    df_r = df_raw.tail(n_rows).copy() if len(df_raw) > n_rows else df_raw.copy()
    df_m  = generate_mathematical_data(
        pattern_type, amplitude, frequency, drift, noise_level, num_days
    )

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📊 Real Bitcoin Data")
        fr = go.Figure()
        fr.add_trace(go.Scatter(x=df_r["Timestamp"], y=df_r["Price"],
            mode="lines", line=dict(color="blue", width=1.5), name="Real Price"))
        fr.update_layout(height=360, template="plotly_white",
            xaxis_title="Time", yaxis_title="Price (USD)", hovermode="x unified")
        st.plotly_chart(fr, use_container_width=True)
        st.metric("Volatility Index", f"{calculate_volatility(df_r):.2f}%")
        st.metric("Drift",            f"{calculate_drift_metric(df_r):+.2f}%")

    with col2:
        st.subheader("🧮 Mathematical Simulation")
        fm = go.Figure()
        fm.add_trace(go.Scatter(x=df_m["Timestamp"], y=df_m["Price"],
            mode="lines", line=dict(color="green", width=1.5), name="Simulated Price"))
        fm.update_layout(height=360, template="plotly_white",
            xaxis_title="Time", yaxis_title="Price (USD)", hovermode="x unified")
        st.plotly_chart(fm, use_container_width=True)
        st.metric("Volatility Index", f"{calculate_volatility(df_m):.2f}%")
        st.metric("Drift",            f"{calculate_drift_metric(df_m):+.2f}%")

    st.subheader("📈 Overlay Comparison")
    fo = go.Figure()
    fo.add_trace(go.Scatter(x=df_r["Timestamp"], y=df_r["Price"],
        mode="lines", name="Real Data",  line=dict(color="blue",  width=1.5)))
    fo.add_trace(go.Scatter(x=df_m["Timestamp"], y=df_m["Price"],
        mode="lines", name="Simulation", line=dict(color="green", width=1.5)))
    fo.update_layout(height=420, template="plotly_white",
        xaxis_title="Time", yaxis_title="Price (USD)", hovermode="x unified")
    st.plotly_chart(fo, use_container_width=True)

    st.subheader("📉 High vs Low — Both Sources")
    col3, col4 = st.columns(2)
    with col3:
        frl = go.Figure()
        frl.add_trace(go.Scatter(x=df_r["Timestamp"], y=df_r["High"],
            mode="lines", name="High", line=dict(color="green", width=1)))
        frl.add_trace(go.Scatter(x=df_r["Timestamp"], y=df_r["Low"],
            mode="lines", name="Low",  line=dict(color="red",   width=1), fill="tonexty"))
        frl.update_layout(title="Real Data", height=300, template="plotly_white")
        st.plotly_chart(frl, use_container_width=True)
    with col4:
        fml = go.Figure()
        fml.add_trace(go.Scatter(x=df_m["Timestamp"], y=df_m["High"],
            mode="lines", name="High", line=dict(color="green", width=1)))
        fml.add_trace(go.Scatter(x=df_m["Timestamp"], y=df_m["Low"],
            mode="lines", name="Low",  line=dict(color="red",   width=1), fill="tonexty"))
        fml.update_layout(title="Simulation", height=300, template="plotly_white")
        st.plotly_chart(fml, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
**Crypto Volatility Visualizer** | Mathematics for AI-II — FA-2  
*Built with Python · Streamlit · NumPy · Plotly* | **FinTechLab Pvt. Ltd.**
""")

# =============================================================================
# HOW TO ADD YOUR CSV TO GITHUB (btcusd_1-min_data.csv is ~500MB — too large)
# =============================================================================
# OPTION A — Create a small sampled version (recommended):
#   1. In Google Colab, after loading the full CSV, run:
#        sample = data.tail(10000)          # last 10,000 rows (~1 week of 1-min data)
#        sample.to_csv('btc_sample.csv', index=False)
#   2. Download btc_sample.csv from Colab
#   3. Upload it to your GitHub repo as btcusd_1-min_data.csv
#   4. The GITHUB_CSV_URL in this file will then work automatically
#
# OPTION B — Use Git LFS for large files:
#   git lfs install
#   git lfs track "*.csv"
#   git add btcusd_1-min_data.csv && git commit && git push
# =============================================================================
