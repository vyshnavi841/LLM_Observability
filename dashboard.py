import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
import os

# Set page config
st.set_page_config(page_title="LLM Observability Dashboard", layout="wide", page_icon="📊")

st.title("📊 LLMOps Observability Dashboard")
st.markdown("Monitoring Latency, Cost, Quality, and Error Rates for the LLM Application.")

# --- Load Data ---
@st.cache_data(ttl=5) # refresh every 5s if active
def load_logs(file_path="logs.jsonl"):
    if not os.path.exists(file_path):
        return pd.DataFrame()
        
    data = []
    with open(file_path, "r") as f:
        for line in f:
            if line.strip():
                try:
                    data.append(json.loads(line))
                except Exception as e:
                    pass
    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df.set_index("timestamp", inplace=True)
    df.sort_index(inplace=True)
    return df

df = load_logs()

if df.empty:
    st.warning("No data found in logs.jsonl. Please run simulate_load.py first.")
    st.stop()

# --- Top Level Metrics ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Requests", len(df))
col2.metric("Total Tokens", int(df["total_tokens"].sum()))
col3.metric("Total Cost (USD)", f"${df['estimated_cost_usd'].sum():.5f}")
error_rate_overall = (df["error"].notna().sum() / len(df)) * 100
col4.metric("Overall Error Rate", f"{error_rate_overall:.1f}%")

st.divider()

# --- Chart 1: Request Volume ---
st.subheader("1. Request Volume")
st.markdown("Number of requests over time.")
# Resample by hour usually, but dataset is small/fast (generated in seconds). 
# We'll resample by 'S' or 'Min' relative to range, but the spec says "number of requests per hour".
# If data is generated in seconds, 'H' will just have 1 bar. Let's do 'H' to fulfill req strictly.
volume_df = df.resample('H').size().reset_index(name='requests')
fig_vol = px.bar(volume_df, x='timestamp', y='requests', title="Requests per Hour", labels={'timestamp': 'Time', 'requests': 'Count'})
fig_vol.update_layout(xaxis_type='category')
st.plotly_chart(fig_vol, use_container_width=True)

# --- Chart 2: Latency Percentiles ---
st.subheader("2. Latency Percentiles")
st.markdown("Daily latency (p50, p95, p99)")
# Group by day
latency_daily = df.groupby(df.index.date)['latency_ms'].agg(
    p50=lambda x: x.quantile(0.50),
    p95=lambda x: x.quantile(0.95),
    p99=lambda x: x.quantile(0.99)
).reset_index()
latency_daily = latency_daily.rename(columns={'index':'date'})

fig_lat = go.Figure()
if not latency_daily.empty:
    fig_lat.add_trace(go.Bar(x=latency_daily['date'], y=latency_daily['p50'], name='p50'))
    fig_lat.add_trace(go.Bar(x=latency_daily['date'], y=latency_daily['p95'], name='p95'))
    fig_lat.add_trace(go.Bar(x=latency_daily['date'], y=latency_daily['p99'], name='p99'))
    fig_lat.update_layout(barmode='group', title="Latency Percentiles (ms)", xaxis_title="Date", yaxis_title="Latency (ms)")
    fig_lat.update_layout(xaxis_type='category')
st.plotly_chart(fig_lat, use_container_width=True)


# --- Chart 3: Daily Cost ---
st.subheader("3. Daily Cost")
cost_daily = df.groupby(df.index.date)['estimated_cost_usd'].sum().reset_index()
cost_daily = cost_daily.rename(columns={'index':'date'})
fig_cost = px.bar(cost_daily, x='date', y='estimated_cost_usd', title="Estimated Daily Cost (USD)", labels={'date': 'Date', 'estimated_cost_usd': 'Cost ($)'})
fig_cost.update_layout(xaxis_type='category')
st.plotly_chart(fig_cost, use_container_width=True)


# --- Chart 4: Error Rate Trend ---
st.subheader("4. Error Rate Trend (1H Rolling)")
# For demo data which is generated instantly, 1-hour window might look flat. We'll use pandas rolling
df_error = df.copy()
df_error['is_error'] = df_error['error'].notna().astype(int)
# Calculate rolling mean over 1-hour window
rolling_error = df_error['is_error'].rolling('1H').mean().reset_index()
fig_err = px.line(rolling_error, x='timestamp', y='is_error', title="Error Rate Trend (1H Rolling Window)", labels={'timestamp': 'Time', 'is_error': 'Error Rate'})
fig_err.update_layout(yaxis_tickformat='.1%')
st.plotly_chart(fig_err, use_container_width=True)


# --- Chart 5: Quality Flag Distribution ---
st.subheader("5. Quality Flag Distribution")
# Explode the lists of flags
all_flags = df['quality_flags'].explode().dropna()
# Count occurrences
if not all_flags.empty:
    # Filter out empty lists that exploded to NaN
    all_flags = all_flags[all_flags != ""]
    
if not all_flags.empty:
    flag_counts = all_flags.value_counts().reset_index()
    flag_counts.columns = ['quality_flag', 'count']
    fig_flags = px.pie(flag_counts, values='count', names='quality_flag', title="Proportion of Detected Quality Issues")
    st.plotly_chart(fig_flags, use_container_width=True)
else:
    st.info("No quality flags detected in the dataset.")

# Additional view: recent logs table
st.subheader("Recent Requests")
st.dataframe(df[['request_id', 'model', 'latency_ms', 'total_tokens', 'estimated_cost_usd', 'error', 'quality_flags']].tail(10))
