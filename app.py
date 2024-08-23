import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from datetime import datetime

# Load the dataset
@st.cache_data
def load_data():
    return pd.read_excel("Basic_Data.xlsx")

df = load_data()

# Ensure the 'Date' column is of datetime type
df['Date'] = pd.to_datetime(df['Date'])

# Map of troubleshooting codes to their descriptions
troubleshooting_descriptions = {
    "WA009": "Drivers: steeringTrackingLost\nSTARTUP_CHECKS_FAILED\nmay also work for other LLC errors",
    "WA041": "Cameras 19-22: camera_internal_state_error\nvision orchestration process aborted\nmay also work for other Camera errors",
    "WA042": "Cameras 1-18: camera_internal_state_error\nvision orchestration process aborted\nmay also work for other Camera errors",
    "WA043": "Logger Status: Chum Recorder is not recording to external drives.\nDisk is not connected at USB 3.0 speed.\nDisk is not mounted.",
    "WA047": "Radar Communication Failure: Data_Invalid",
    "WA066": "Lidar: PTPTimeSyncFault",
    "WA070": "Drivers: LinkStabilityLow",
    "WA065": "Radar: RadarOutputSilent\nRadarDataMissing\nInvalidPtl",
    "WA050.a": "SideKick: DataDependency",
    "WA050.b": "SideKick: Unable to complete mic check with 'Say Hello Hero'",
    "WA050.c": "SideKick: Unable to start mic check with ADR button not responsive"
}

# Function to wrap text
def wrap_text(text, width=40):
    wrapped_text = []
    for line in text.splitlines():
        while len(line) > width:
            wrapped_text.append(line[:width])
            line = line[width:]
        wrapped_text.append(line)
    return "<br>".join(wrapped_text)

# Apply wrapping to descriptions
for code, description in troubleshooting_descriptions.items():
    troubleshooting_descriptions[code] = wrap_text(description)

# Sidebar for filters
st.sidebar.header("Filter Options")

# "Select All" option for car numbers
car_list = df["Car Number"].unique().tolist()
car_filter = st.sidebar.multiselect(
    "Select Car(s)",
    options=car_list,
    default=[]  # No selection by default
)
if st.sidebar.checkbox("Select All Cars"):
    car_filter = car_list

# "Select All" option for error codes
error_list = df["Troubleshooting Code"].unique().tolist()
error_filter = st.sidebar.multiselect(
    "Select Error Code(s)",
    options=error_list,
    default=[]  # No selection by default
)
if st.sidebar.checkbox("Select All Error Codes"):
    error_filter = error_list

# Filter by date range
date_filter = st.sidebar.date_input(
    "Select Date Range",
    [df["Date"].min().date(), df["Date"].max().date()]
)

# Ensure the date inputs are also converted to datetime for comparison
start_date = pd.to_datetime(date_filter[0])
end_date = pd.to_datetime(date_filter[1])

# Filter by period (daily, weekly, monthly, yearly)
period_filter = st.sidebar.selectbox(
    "Select Period",
    options=["Yearly", "Monthly", "Weekly", "Daily"]  # Default to Yearly
)

# Apply filters only if the user has made a selection
filtered_df = df[
    (df["Car Number"].isin(car_filter) if car_filter else True) &
    (df["Troubleshooting Code"].isin(error_filter) if error_filter else True) &
    (df["Date"].between(start_date, end_date))
]

# Group data based on selected period and ensure the necessary columns exist
if period_filter == "Daily":
    filtered_df["Day"] = filtered_df["Date"].dt.date
    grouped_df = filtered_df.groupby(["Day", "Troubleshooting Code", "Car Number"]).size().reset_index(name="Count")
    time_unit = "Day"

elif period_filter == "Weekly":
    filtered_df["Week"] = filtered_df["Date"].dt.strftime('%Y-W%U')
    grouped_df = filtered_df.groupby(["Week", "Troubleshooting Code", "Car Number"]).size().reset_index(name="Count")
    time_unit = "Week"

elif period_filter == "Monthly":
    filtered_df["Month"] = filtered_df["Date"].dt.strftime('%B')
    grouped_df = filtered_df.groupby(["Month", "Troubleshooting Code", "Car Number"]).size().reset_index(name="Count")
    time_unit = "Month"

elif period_filter == "Yearly":
    filtered_df["Year"] = filtered_df["Date"].dt.year
    grouped_df = filtered_df.groupby(["Year", "Troubleshooting Code", "Car Number"]).size().reset_index(name="Count")
    time_unit = "Year"

# Calculate the total time spent for each troubleshooting code
time_spent = df.groupby('Troubleshooting Code')['Time (min)'].sum().reset_index()
time_spent.columns = ['Troubleshooting Code', 'Total Time Spent (min)']

# Merge the time spent information with the grouped data
grouped_df = pd.merge(grouped_df, time_spent, on='Troubleshooting Code')

# Add descriptions for the hover tooltip and keep code for labels
grouped_df['Description'] = grouped_df['Troubleshooting Code'].map(troubleshooting_descriptions)
grouped_df['Code'] = grouped_df['Troubleshooting Code']

# Display dashboards only if data is filtered
if not filtered_df.empty:
    col1, col2 = st.columns(2)

    with col1:
        st.header(f"Errors ({period_filter})")
        top_errors = grouped_df.groupby(['Code', 'Description', 'Total Time Spent (min)'])['Count'].sum().sort_values(ascending=False).reset_index().head(5)
        
        fig = px.bar(
            top_errors,
            x='Code',
            y='Count',
            hover_data={'Total Time Spent (min)': True},
            labels={'Code': 'Troubleshooting Code', 'Count': 'Count'},
            text='Code',
            hover_name='Description'  # This shows only the description text
        )
        fig.update_traces(marker_color='rgb(199, 121, 93)', textposition='outside')
        fig.update_layout(
            uniformtext_minsize=8,
            uniformtext_mode='hide',
            hoverlabel=dict(
                font_size=14,
                font_family="Arial, sans-serif",
                align="left",
            ),
            font=dict(
                family="Arial, sans-serif",
                size=16,
                color="Black"
            )
        )
        st.plotly_chart(fig)

    with col2:
        st.header("Top Errors by Car")
        top_cars = filtered_df["Car Number"].value_counts().head(10)
        st.bar_chart(top_cars, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        st.header("Error Trend Over Time")
        if time_unit in grouped_df.columns:
            error_trend_summary = grouped_df.groupby(time_unit)['Count'].sum().reset_index()
            fig = px.line(
                error_trend_summary,
                x=time_unit,
                y='Count',
                markers=True,
                labels={time_unit: time_unit, 'Count': 'Total Errors'},
                title=f"Total Errors Over {period_filter}"
            )
            fig.update_traces(line=dict(color='rgb(199, 121, 93)', width=2))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write(f"No '{time_unit}' data available for the selected filters.")

    with col4:
        st.header("Car-Specific Error Analysis")
        car_error_summary = grouped_df.groupby('Code')['Count'].sum().reset_index()
        fig = px.bar(
            car_error_summary,
            x='Code',
            y='Count',
            labels={'Code': 'Troubleshooting Code', 'Count': 'Count'},
            title="Top Errors Across Selected Cars"
        )
        fig.update_traces(marker_color='rgb(93, 121, 199)')
        st.plotly_chart(fig, use_container_width=True)

    # Additional visualization: Time spent on errors per car
    st.header("Time Spent on Errors by Car")
    time_spent_per_car = df.groupby(['Car Number'])['Time (min)'].sum().reset_index()
    fig = px.bar(time_spent_per_car, x='Car Number', y='Time (min)', 
                 title="Total Time Spent on Errors by Car",
                 labels={'Time (min)': 'Total Time (min)'})
    fig.update_traces(marker_color='rgb(121, 199, 93)')
    st.plotly_chart(fig, use_container_width=True)

# Grouping filtered_df for the Treemap
grouped_for_treemap = filtered_df.groupby(['Car Number', 'Troubleshooting Code'])['Time (min)'].sum().reset_index()

# Additional visualization with Treemap focusing on time spent
st.header("Error Resolution Time Treemap by Car and Error Type")
fig = px.treemap(grouped_for_treemap, path=['Car Number', 'Troubleshooting Code'], values='Time (min)', 
                 title='Treemap of Error Resolution Time by Car and Error Type',
                 color='Time (min)', color_continuous_scale='Viridis')
fig.update_traces(
    hovertemplate="<b>Car Number:</b> %{label}<br><b>Total Time Spent (min):</b> %{value}<extra></extra>",
    textinfo="label+value"
)
st.plotly_chart(fig)

# Additional heatmap for visualization, focusing on time spent
if time_unit in filtered_df.columns:
    st.header("Heatmap of Time Spent on Errors by Car and Time Unit")
    heatmap_data = pd.pivot_table(
        filtered_df.groupby(['Car Number', time_unit])['Time (min)'].sum().reset_index(),
        values='Time (min)',
        index='Car Number',
        columns=time_unit,
        fill_value=0
    )
    # Correct tooltip label from 'color' to 'Total Time Spent (min)'
    fig = px.imshow(
        heatmap_data,
        color_continuous_scale="Viridis",
        aspect="auto",
        title="Heatmap of Time Spent on Errors",
        labels={'color': 'Total Time Spent (min)'}
    )
    fig.update_traces(hovertemplate=f"{time_unit}: %{{x}}<br>Car Number: %{{y}}<br>Total Time Spent (min): %{{z}}<extra></extra>")
    st.plotly_chart(fig)
else:
    st.write(f"Heatmap cannot be generated as '{time_unit}' data is missing.")

# Sidebar Information
st.sidebar.header("About")
st.sidebar.write("""
This app allows users to analyze error data from vehicles over time. 
You can filter by car, error code, and date to see trends and patterns in the errors. 
The dashboard also provides insights into the time spent resolving each error, 
helping to identify areas for improving vehicle efficiency and reducing downtime.
""")

