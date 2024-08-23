import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="Vehicle Error Analysis Dashboard", page_icon="🚗", layout="wide")

st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 50px 0 20px 0;
        font-size: 36px;
        font-weight: bold;
        color: #333333;
    }
    .subheader {
        text-align: center;
        font-size: 18px;
        color: #555555;
        margin-bottom: 40px;
    }
    .stMultiSelect [role="listbox"] ul {
        max-height: 0px;
    }
    .stMultiSelect [role="listbox"]:hover ul {
        max-height: 150px;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="main-header">🚗 Vehicle Error Analysis Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="subheader">An interactive dashboard to monitor and analyze vehicle errors over time.</div>', unsafe_allow_html=True)

@st.cache_data
def load_data():
    return pd.read_excel("Basic_Data.xlsx")

df = load_data()
df['Date'] = pd.to_datetime(df['Date'])

troubleshooting_descriptions = {
    "WA009": "Drivers: steeringTrackingLost\nSTARTUP_CHECKS_FAILED\nMay also work for other LLC errors.",
    "WA041": "Cameras 19-22: camera_internal_state_error\nVision orchestration process aborted.\nMay also work for other camera errors.",
    "WA042": "Cameras 1-18: camera_internal_state_error\nVision orchestration process aborted.\nMay also work for other camera errors.",
    "WA043": "Logger Status: Chum Recorder is not recording to external drives.\nDisk is not connected at USB 3.0 speed.\nDisk is not mounted.",
    "WA047": "Radar Communication Failure: Data_Invalid.",
    "WA066": "Lidar: PTPTimeSyncFault.",
    "WA070": "Drivers: LinkStabilityLow.",
    "WA065": "Radar: RadarOutputSilent\nRadarDataMissing\nInvalidPtl.",
    "WA050.a": "SideKick: DataDependency.",
    "WA050.b": "SideKick: Unable to complete mic check with 'Say Hello Hero'.",
    "WA050.c": "SideKick: Unable to start mic check with ADR button not responsive."
}

st.sidebar.header("🔎 Filter Options")

car_list = sorted(df["Car Number"].unique())
select_all_cars = st.sidebar.checkbox("Select All Cars", value=True)
selected_cars = car_list if select_all_cars else st.sidebar.multiselect("Select Car Number(s):", options=car_list)
st.sidebar.multiselect("Select Car Number(s):", options=car_list, default=selected_cars if not select_all_cars else [])

error_list = sorted(df["Troubleshooting Code"].unique())
select_all_errors = st.sidebar.checkbox("Select All Error Codes", value=True)
selected_errors = error_list if select_all_errors else st.sidebar.multiselect("Select Troubleshooting Code(s):", options=error_list)
st.sidebar.multiselect("Select Troubleshooting Code(s):", options=error_list, default=selected_errors if not select_all_errors else [])

min_date = df["Date"].min()
max_date = df["Date"].max()
selected_dates = st.sidebar.date_input("Select Date Range:", value=(min_date, max_date), min_value=min_date, max_value=max_date)

period_options = ["Daily", "Weekly", "Monthly", "Yearly"]
selected_period = st.sidebar.selectbox("Select Time Period:", options=period_options, index=2)

filtered_df = df[
    (df["Car Number"].isin(selected_cars)) &
    (df["Troubleshooting Code"].isin(selected_errors)) &
    (df["Date"] >= pd.to_datetime(selected_dates[0])) &
    (df["Date"] <= pd.to_datetime(selected_dates[1]))
]

if selected_period == "Daily":
    filtered_df["Period"] = filtered_df["Date"].dt.date
elif selected_period == "Weekly":
    filtered_df["Period"] = filtered_df["Date"].dt.to_period('W').apply(lambda r: r.start_time)
elif selected_period == "Monthly":
    filtered_df["Period"] = filtered_df["Date"].dt.to_period('M').apply(lambda r: r.start_time)
elif selected_period == "Yearly":
    filtered_df["Period"] = filtered_df["Date"].dt.to_period('Y').apply(lambda r: r.start_time)

agg_counts = filtered_df.groupby(["Period", "Troubleshooting Code"]).size().reset_index(name='Count')
agg_time = filtered_df.groupby(["Period", "Troubleshooting Code"])["Time (min)"].sum().reset_index()
agg_data = pd.merge(agg_counts, agg_time, on=["Period", "Troubleshooting Code"])
agg_data["Description"] = agg_data["Troubleshooting Code"].map(troubleshooting_descriptions)

st.markdown("## 📊 Overview")

total_errors = filtered_df.shape[0]
total_time = filtered_df["Time (min)"].sum()

col1, col2, col3 = st.columns(3)
col1.metric("Total Errors", f"{total_errors}")
col2.metric("Total Time Spent (min)", f"{total_time:.2f}")
col3.metric("Unique Cars Affected", f"{filtered_df['Car Number'].nunique()}")

st.markdown("---")

st.markdown(f"### 📈 Error Trend Over Time ({selected_period})")
fig_trend = px.line(agg_data, x="Period", y="Count", color="Troubleshooting Code", hover_data=["Description", "Time (min)"], labels={"Period": selected_period, "Count": "Number of Errors", "Troubleshooting Code": "Error Code"}, template="plotly_white")
fig_trend.update_layout(hovermode="x unified")
st.plotly_chart(fig_trend, use_container_width=True)

st.markdown(f"### 🏆 Top Errors ({selected_period})")
top_errors = agg_data.groupby(["Troubleshooting Code", "Period"])["Count"].sum().reset_index().sort_values(by="Count", ascending=False).head(10)
top_errors["Description"] = top_errors["Troubleshooting Code"].map(troubleshooting_descriptions)

fig_top_errors = px.bar(top_errors, x="Count", y="Troubleshooting Code", orientation="h", hover_data=["Description"], labels={"Count": "Number of Errors", "Troubleshooting Code": "Error Code"}, template="plotly_white")
fig_top_errors.update_layout(yaxis={'categoryorder':'total ascending'})
st.plotly_chart(fig_top_errors, use_container_width=True)

st.markdown(f"### 🔥 Heatmap of Errors by Car and {selected_period}")
heatmap_data = filtered_df.groupby(["Car Number", "Period"]).size().reset_index(name="Count")
heatmap_pivot = heatmap_data.pivot(index="Car Number", columns="Period", values="Count").fillna(0)

fig_heatmap = px.imshow(heatmap_pivot, aspect="auto", labels={"x": selected_period, "y": "Car Number", "color": "Number of Errors"}, color_continuous_scale="Reds", template="plotly_white")
st.plotly_chart(fig_heatmap, use_container_width=True)

st.markdown(f"### 🌳 Error Distribution Treemap ({selected_period})")
treemap_data = filtered_df.groupby(["Troubleshooting Code", "Car Number", "Period"]).size().reset_index(name="Count")
treemap_data["Description"] = treemap_data["Troubleshooting Code"].map(troubleshooting_descriptions)

fig_treemap = px.treemap(treemap_data, path=["Troubleshooting Code", "Car Number"], values="Count", hover_name="Car Number", hover_data={"Count": True, "Troubleshooting Code": False, "Description": False}, labels={"parent": "Error Code", "label": "Car Number", "Count": "Number of Errors"}, template="plotly_white")
st.plotly_chart(fig_treemap, use_container_width=True)

st.markdown("### 📄 Detailed Data")
st.dataframe(filtered_df.sort_values(by="Date", ascending=False), height=400)

@st.cache_data
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')

csv = convert_df(filtered_df)
st.download_button(label="📥 Download Filtered Data as CSV", data=csv, file_name='filtered_vehicle_errors.csv', mime='text/csv')

st.markdown("---")
st.markdown("Developed by [Irfan Senyurt](https://irfansenyurt.com) | © 2024 All Rights Reserved")
