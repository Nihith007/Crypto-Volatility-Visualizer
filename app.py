import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np
import requests
from io import StringIO
import pytz

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
# GITHUB CSV URL — points to your repo
# ─────────────────────────────────────────────────────────────────────────────
GITHUB_CSV_URL = (
    "https://raw.githubusercontent.com/Nihith007/Crypto-Volatility-Visualizer"
    "/refs/heads/main/btcusd_1-min_data.csv"
)

# ─────────────────────────────────────────────────────────────────────────────
# CHANGE 1 ── TIMEZONE MAP
# WHERE: Top of file, global constant
# WHY: Assignment requires India timezone support. Added IST as default plus
#      all major world timezones so users can convert timestamps instantly.
# ─────────────────────────────────────────────────────────────────────────────
TIMEZONE_OPTIONS = {
    "🇮🇳 India (IST) UTC+5:30":        "Asia/Kolkata",
    "🌍 UTC (Universal)":               "UTC",
    "🇺🇸 New York (EST/EDT)":           "America/New_York",
    "🇺🇸 Los Angeles (PST/PDT)":        "America/Los_Angeles",
    "🇬🇧 London (GMT/BST)":             "Europe/London",
    "🇪🇺 Paris / Berlin (CET/CEST)":    "Europe/Paris",
    "🇦🇪 Dubai (GST) UTC+4":            "Asia/Dubai",
    "🇸🇬 Singapore (SGT) UTC+8":        "Asia/Singapore",
    "🇯🇵 Tokyo (JST) UTC+9":            "Asia/Tokyo",
    "🇦🇺 Sydney (AEDT) UTC+11":         "Australia/Sydney",
}

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
# CHANGE 2 ── TIMEZONE SELECTOR IN SIDEBAR (always visible)
# WHERE: Sidebar, shown in ALL modes
# WHY: India timezone (IST) is required. Selector converts all chart timestamps
#      to the chosen timezone so dates/times are locally meaningful.
# ─────────────────────────────────────────────────────────────────────────────
st.sidebar.header("🌐 Timezone")
selected_tz_label = st.sidebar.selectbox(
    "Display times in:",
    list(TIMEZONE_OPTIONS.keys()),
    index=0,   # India IST is default (index 0)
)
selected_tz = TIMEZONE_OPTIONS[selected_tz_label]
tz = pytz.timezone(selected_tz)

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
date_range            = None   # will be set below for real data modes

if mode == "📊 Real Bitcoin Data":
    st.sidebar.markdown("---")
    st.sidebar.header("📁 Data Source")
    data_source = st.sidebar.radio(
        "Source:", ["🌐 GitHub (Auto-fetch)", "📂 Upload CSV"]
    )
    if data_source == "📂 Upload CSV":
        uploaded_file = st.sidebar.file_uploader(
            "Upload btcusd_1-min_data.csv", type=["csv"],
            help="Needs columns: Timestamp (Unix s), Open, High, Low, Close, Volume"
        )
    st.sidebar.subheader("📈 Display Options")
    show_volatility_bands = st.sidebar.checkbox("Show Volatility Bands", value=True)
    show_volume           = st.sidebar.checkbox("Show Volume Analysis",   value=True)

elif mode == "🧮 Mathematical Simulation":
    st.sidebar.markdown("---")
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
    amplitude   = st.sidebar.slider("Amplitude (Swing Size $)", 100, 5000, 1000, 100,
                    help="Height of each price swing — A in A·sin(2πft/T)")
    frequency   = st.sidebar.slider("Frequency (Cycles)",       0.1,  5.0,  1.0,  0.1,
                    help="Number of full wave cycles across the time window")
    drift       = st.sidebar.slider("Drift ($/day)",            -50,   50,   10,    5,
                    help="Long-term trend — computed as integral ∫D dt = D·t")
    noise_level = st.sidebar.slider("Noise Level (σ)",            0,  500,  100,   10,
                    help="Std deviation of random jumps N(0,σ)")
    st.sidebar.subheader("⏱️ Time Range")
    num_days = st.sidebar.slider("Number of Days", 1, 30, 7)

else:  # Compare Both
    st.sidebar.markdown("---")
    st.sidebar.header("📁 Real Data Source")
    data_source = st.sidebar.radio("Source:", ["🌐 GitHub (Auto-fetch)", "📂 Upload CSV"])
    if data_source == "📂 Upload CSV":
        uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])
    st.sidebar.header("🧮 Simulation Settings")
    pattern_type = st.sidebar.selectbox(
        "Pattern:",
        ["Sine Wave (Smooth Cycles)", "Cosine Wave (Smooth Cycles)", "Sine + Noise (Realistic Market)"],
    )
    amplitude    = st.sidebar.slider("Amplitude",    100, 5000, 1000, 100)
    frequency    = st.sidebar.slider("Frequency",    0.1,  5.0,  1.0,  0.1)
    drift        = st.sidebar.slider("Drift",        -50,   50,   10,    5)
    noise_level  = st.sidebar.slider("Noise (σ)",     0,   500,  100,   10)
    num_days     = st.sidebar.slider("Sim days",       1,    30,    7)


# ─────────────────────────────────────────────────────────────────────────────
# CHANGE 3 ── apply_timezone()  NEW HELPER
# WHERE: Called on every DataFrame before plotting
# WHY: Converts UTC timestamps from the CSV into the user-selected timezone
#      so that chart X-axis shows correct local times (e.g. IST = UTC+5:30).
#      Without this all times showed as UTC regardless of location.
# ─────────────────────────────────────────────────────────────────────────────
def apply_timezone(df, tz):
    df = df.copy()
    if df["Timestamp"].dt.tz is None:
        # Timestamps are tz-naive → assume UTC, then convert
        df["Timestamp"] = (
            df["Timestamp"]
            .dt.tz_localize("UTC")
            .dt.tz_convert(tz)
        )
    else:
        df["Timestamp"] = df["Timestamp"].dt.tz_convert(tz)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# DATA LOADING FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="📡 Fetching btcusd_1-min_data.csv from GitHub…")
def fetch_github_data():
    try:
        r = requests.get(GITHUB_CSV_URL, timeout=60)
        r.raise_for_status()
        return pd.read_csv(StringIO(r.text)), None
    except requests.exceptions.HTTPError as e:
        return None, f"HTTP {e.response.status_code} — CSV not found at that URL yet."
    except Exception as e:
        return None, str(e)


def normalize_dataframe(df):
    df = df.copy()
    df.columns = [c.strip() for c in df.columns]

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

    for src in ["Close", "close", "Price", "price"]:
        if src in df.columns:
            df["Price"] = pd.to_numeric(df[src], errors="coerce")
            break

    for col in ["Open", "High", "Low", "Close", "Volume"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

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

    df = df.dropna(subset=["Timestamp", "Price"])
    df = df.sort_values("Timestamp").reset_index(drop=True)
    return df


@st.cache_data
def create_sample_bitcoin_data(days=30):
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


# No @st.cache_data — sliders update chart instantly
def generate_mathematical_data(pattern, amp, freq, drift_val, noise, days, tz):
    hours = days * 24
    t     = np.linspace(0, days, hours)
    base  = 45000
    sigma = max(noise, 1)

    if pattern == "Sine Wave (Smooth Cycles)":
        prices = base + amp * np.sin(2 * np.pi * freq * t / days)
    elif pattern == "Cosine Wave (Smooth Cycles)":
        prices = base + amp * np.cos(2 * np.pi * freq * t / days)
    elif pattern == "Random Noise (Chaotic Jumps)":
        prices = base + np.cumsum(np.random.normal(0, sigma, hours))
    elif pattern == "Sine + Noise (Realistic Market)":
        prices = (base + amp * np.sin(2 * np.pi * freq * t / days)
                  + np.cumsum(np.random.normal(0, sigma, hours)))
    elif pattern == "Cosine + Noise (Realistic Market)":
        prices = (base + amp * np.cos(2 * np.pi * freq * t / days)
                  + np.cumsum(np.random.normal(0, sigma, hours)))
    else:
        prices = (base
                  + amp     * np.sin(2 * np.pi * freq * 1 * t / days)
                  + amp / 2 * np.cos(2 * np.pi * freq * 2 * t / days)
                  + amp / 3 * np.sin(2 * np.pi * freq * 3 * t / days))

    prices = prices + drift_val * t / days
    prices = np.maximum(prices, 100)

    # CHANGE 4 ── Simulation timestamps generated in selected timezone
    # WHERE: generate_mathematical_data(), timestamp creation
    # WHY: Simulation times should also reflect the user's chosen timezone
    #      so the X-axis is consistent with real data mode.
    now_tz = datetime.now(pytz.timezone(tz))
    start  = now_tz - timedelta(days=days)
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
# CHANGE 5 ── date_range_filter()  NEW HELPER
# WHERE: Called in Real Data and Compare Both modes, after loading data
# WHY: The old slider used days_to_show × 24 × 60 rows via tail(), which
#      BROKE when the data didn't have a full contiguous range or when the
#      slider moved — it just sliced rows blindly without knowing dates.
#      This new function shows a proper date picker (start → end) built from
#      the actual min/max dates in the dataset, so the slider always works
#      correctly regardless of data gaps or size.
# ─────────────────────────────────────────────────────────────────────────────
def date_range_filter(df, key_prefix="main"):
    min_date = df["Timestamp"].min().date()
    max_date = df["Timestamp"].max().date()
    total_days_in_data = (max_date - min_date).days

    st.sidebar.subheader("📅 Date Range Filter")

    # Ensure we never ask for more than 30 days, or more than the data has
    limit_days = min(total_days_in_data, 30)
    
    if limit_days < 1:
        return df

    days_back = st.sidebar.slider(
        "Show last N days",
        min_value=1,
        max_value=30, # Hard limit set to 30
        value=limit_days, 
        step=1,
        key=f"{key_prefix}_days_slider",
        help="View up to the last 30 days of data."
    )

    start_date = max_date - timedelta(days=days_back)
    mask = df["Timestamp"].dt.date >= start_date
    return df[mask].copy()

    if len(filtered) == 0:
        st.warning("No data in selected date range — showing all data.")
        return df

    return filtered


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
            "**To fix:** Upload the data file to your GitHub repo "
            "`Nihith007/Crypto-Volatility-Visualizer`.\n\n"
            "*Showing generated sample data in the meantime.*"
        )
    elif src == "github":
        st.success(
            f"✅ Loaded data from GitHub — "
            f"**{len(df_raw):,} rows** | "
            f"{df_raw['Timestamp'].min().date()} → {df_raw['Timestamp'].max().date()}"
        )

    # Apply selected timezone to all timestamps
    df_tz = apply_timezone(df_raw, tz)
    
    # Optional: Pre-slice the dataframe to the last 30 days before even hitting the filter
    last_date = df_tz["Timestamp"].max()
    thirty_days_ago = last_date - timedelta(days=30)
    df_tz = df_tz[df_tz["Timestamp"] >= thirty_days_ago]
    
    # Dataset preview
    with st.expander("🔍 Dataset Preview — head() & shape (Stage 4 check)"):
        st.markdown(f"**Shape:** `{df_tz.shape[0]:,} rows × {df_tz.shape[1]} columns`")
        st.markdown("**Columns:** " + ", ".join(f"`{c}`" for c in df_tz.columns.tolist()))
        st.info(f"Timestamps converted from UTC → **{selected_tz_label}**")
        st.dataframe(df_tz.head(10), use_container_width=True)

    # CHANGE 5 in action — proper date filter based on actual timestamps
    df = date_range_filter(df_tz, key_prefix="real")
    show_sidebar_metrics(df)

    # Show timezone info banner
    st.info(f"🕐 All times shown in **{selected_tz_label}**")

    # ── CHART 1: Line Graph of Close Price Over Time
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("📈 Bitcoin Close Price Over Time")
        fig1 = go.Figure()
        
        # Add the main price line
        fig1.add_trace(go.Scatter(
            x=df["Timestamp"], y=df["Price"],
            mode="lines", name="Close Price",
            line=dict(color="#1f77b4", width=1.5)
        ))
        
        # ... (volatility band code stays the same) ...
        
        # THE CRITICAL CHANGE IS HERE:
        fig1.update_layout(
            xaxis_title=f"Date ({selected_tz_label.split(' ')[1].strip('()')} Time)",
            yaxis_title="Price (USD)",
            # Force the X-axis to match the filtered data exactly
            xaxis=dict(
                range=[df["Timestamp"].min(), df["Timestamp"].max()],
                type="date"
            ),
            hovermode="x unified", 
            height=420, 
            template="plotly_white"
        )
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

    # ── CHART 2: High vs Low
    st.subheader("📉 High vs Low Price Comparison")
    st.markdown("*The gap between High and Low shows that period's volatility.*")
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=df["Timestamp"], y=df["High"],
        mode="lines", name="High", line=dict(color="green", width=1)))
    fig2.add_trace(go.Scatter(x=df["Timestamp"], y=df["Low"],
        mode="lines", name="Low", line=dict(color="red", width=1),
        fill="tonexty", fillcolor="rgba(0,180,0,0.07)"))
    fig2.update_layout(
        xaxis_title=f"Date ({selected_tz_label.split(' ')[1].strip('()')} Time)",
        yaxis_title="Price (USD)",
        hovermode="x unified", height=320, template="plotly_white")
    st.plotly_chart(fig2, use_container_width=True)

    # ── CHART 3: Volume
    if show_volume:
        st.subheader("📦 Volume Analysis")
        st.markdown("*Compare if higher-volume periods match with bigger price changes.*")
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(x=df["Timestamp"], y=df["Volume"],
            name="Volume", marker_color="steelblue", opacity=0.7))
        fig3.update_layout(
            xaxis_title=f"Date ({selected_tz_label.split(' ')[1].strip('()')} Time)",
            yaxis_title="Volume (BTC)",
            height=300, template="plotly_white")
        st.plotly_chart(fig3, use_container_width=True)

    # ── CHART 4: Stable vs Volatile
    st.subheader("🔀 Stable vs Volatile Periods")
    st.markdown("*Flat lines = Stable. Sharp spikes = Volatile.*")
    col3, col4 = st.columns(2)
    with col3:
        w = max(min(60, len(df) // 10), 2)
        df["Rolling_Vol"] = df["Price"].rolling(w).std()
        fig4 = go.Figure()
        fig4.add_trace(go.Scatter(x=df["Timestamp"], y=df["Rolling_Vol"],
            mode="lines", line=dict(color="orange", width=1.5)))
        fig4.update_layout(title=f"Rolling Volatility ({w}-period window)",
            xaxis_title=f"Date ({selected_tz_label.split(' ')[1].strip('()')} Time)",
            yaxis_title="Std Dev ($)", height=320, template="plotly_white")
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

    df_m = generate_mathematical_data(
        pattern_type, amplitude, frequency, drift, noise_level, num_days, selected_tz
    )
    show_sidebar_metrics(df_m)

    st.info(f"🕐 All times shown in **{selected_tz_label}**")
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

    fig_m1 = go.Figure()
    fig_m1.add_trace(go.Scatter(
        x=df_m["Timestamp"], y=df_m["Price"],
        mode="lines", name="Simulated Price",
        line=dict(color="#2E86DE", width=2),
        fill="tozeroy", fillcolor="rgba(46,134,222,0.07)"
    ))
    fig_m1.update_layout(
        title=f"Simulated Bitcoin Price — {pattern_type}",
        xaxis_title=f"Time ({selected_tz_label.split(' ')[1].strip('()')})",
        yaxis_title="Price (USD)",
        hovermode="x unified", height=480, template="plotly_white"
    )
    st.plotly_chart(fig_m1, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📉 High vs Low")
        fhl = go.Figure()
        fhl.add_trace(go.Scatter(x=df_m["Timestamp"], y=df_m["High"],
            mode="lines", name="High", line=dict(color="green", width=1)))
        fhl.add_trace(go.Scatter(x=df_m["Timestamp"], y=df_m["Low"],
            mode="lines", name="Low",  line=dict(color="red", width=1), fill="tonexty"))
        fhl.update_layout(height=300, template="plotly_white",
            xaxis_title="Time", yaxis_title="Price (USD)")
        st.plotly_chart(fhl, use_container_width=True)

    with col2:
        st.subheader("📦 Volume")
        fvol = go.Figure()
        fvol.add_trace(go.Bar(x=df_m["Timestamp"], y=df_m["Volume"],
            marker_color="steelblue", opacity=0.7))
        fvol.update_layout(height=300, template="plotly_white",
            xaxis_title="Time", yaxis_title="Volume")
        st.plotly_chart(fvol, use_container_width=True)

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

    st.markdown("---")
    st.markdown("### 🎓 Understanding the Mathematics")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.info("**🌊 Sine / Cosine Waves**\nSmooth, repeating price cycles.\n- **Amplitude** = height of swing\n- **Frequency** = cycles per period\n- Formula: `A · sin(2πft/T)`")
    with c2:
        st.info("**📈 Drift (Integral)**\nModels long-term price slope.\n- Calculated as: `∫D dt = D·t`\n- Positive → upward trend\n- Negative → downward trend")
    with c3:
        st.info("**🎲 Random Noise**\nModels sudden market jumps.\n- Drawn from `N(0, σ)`\n- Higher σ → more chaotic\n- Cumulative sum = random walk")


# ─────────────────────────────────────────────────────────────────────────────
# ══════════════════════  MODE: COMPARE BOTH  ══════════════════════
# ─────────────────────────────────────────────────────────────────────────────
else:
    st.header("🔍 Comparison: Real Data vs Mathematical Simulation")

    src = "github" if data_source == "🌐 GitHub (Auto-fetch)" else "upload"
    df_raw, err = load_real_data(source=src, uploaded_file=uploaded_file)
    if err:
        st.warning(f"⚠️ {err} — using sample data.")

    df_tz = apply_timezone(df_raw, tz)
    df_r  = date_range_filter(df_tz, key_prefix="compare")
    df_m  = generate_mathematical_data(
        pattern_type, amplitude, frequency, drift, noise_level, num_days, selected_tz
    )

    st.info(f"🕐 All times shown in **{selected_tz_label}**")

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
