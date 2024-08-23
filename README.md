# Vehicle Error Analysis Dashboard

https://zooxvehicle.streamlit.app/

This project is an interactive Streamlit dashboard for analyzing vehicle errors over time. The dashboard allows users to filter data based on vehicle numbers, error codes, date ranges, and time periods (daily, weekly, monthly, yearly) and visualize the error data through various charts and visualizations.

## Features

- **Data Filters**: Filter the data by selecting specific vehicles, error codes, and date ranges.
- **Interactive Visualizations**: 
  - **Error Trend Over Time**: A line chart showing the trend of errors over the selected time period.
  - **Top Errors**: A bar chart displaying the top errors based on the selected time period.
  - **Heatmap**: A heatmap showing the distribution of errors by vehicle and time period.
  - **Treemap**: A treemap visualizing the distribution of errors across different vehicles and error codes.
- **Downloadable Data**: Download the filtered data as a CSV file.

## Requirements

- **Python 3.7+**
- **Streamlit**
- **Pandas**
- **Plotly**

## Installation

1. Clone the repository to your local machine.
   
2. Install the required Python packages.

3. Ensure the `kitt-pic.jpg` image file and `Basic_Data.xlsx` data file are in the project directory.

## Usage

1. Run the Streamlit application.

2. Access the dashboard in your web browser.

3. Use the filter options in the sidebar to narrow down the data.

4. The following visualizations are available:
   - **Error Trend Over Time**: Displays the trend of errors over the selected period.
   - **Top Errors**: Shows the top errors in a bar chart.
   - **Heatmap**: Visualizes errors by vehicle and time period.
   - **Treemap**: Provides a treemap visualization of errors by vehicle and error code.

5. Download the filtered data as a CSV file by clicking the download button at the bottom of the dashboard.


