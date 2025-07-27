import pandas as pd
import streamlit as st
import plotly.express as px
import numpy as np

def load_data(file):
    """Load and process the CSV data with proper handling of your specific format"""
    if file is None:
        return None
    
    try:
        # Read the CSV file
        df = pd.read_csv(file)
        
        # Convert duration minutes to hours
        df['Hours'] = df['Duration (mins)'] / 60.0
        
        # Convert Payroll Date to datetime
        df['Payroll Date'] = pd.to_datetime(df['Payroll Date'])
        
        # Filter out RDOs, Personal Leave, and Sick Leave
        df = df[~df['Task Name'].str.contains(
            'RDO|Rostered Day Off|Personal Leave|Sick Leave|Annual Leave', 
            case=False, 
            na=False
        )]
        
        return df
    except Exception as e:
        st.error(f"Error loading  {str(e)}")
        st.error("Please ensure you're uploading the correct CSV format exported from your system.")
        return None

def apply_rounding(hours, method='15min'):
    """Apply rounding to hours"""
    if pd.isna(hours):
        return hours
        
    if method == '15min':  # 15 minutes = 0.25 hours
        return np.round(hours * 4) / 4
    elif method == '30min':  # 30 minutes = 0.5 hours
        return np.round(hours * 2) / 2
    elif method == 'hour':
        return np.round(hours)
    return hours

def calculate_daily_totals(df, rounding_method='None'):
    """Calculate total hours per technician per day with optional rounding"""
    # Group by technician and date to get daily totals
    daily_totals = df.groupby(['Technician Name', 'Payroll Date'])['Hours'].sum().reset_index(name='Raw Hours')
    
    # Apply rounding if selected
    if rounding_method != "None":
        method = rounding_method.lower().replace(" ", "")
        daily_totals['Rounded Hours'] = daily_totals['Raw Hours'].apply(lambda x: apply_rounding(x, method))
    else:
        daily_totals['Rounded Hours'] = daily_totals['Raw Hours']
    
    # Add day of week information
    daily_totals['Day of Week'] = daily_totals['Payroll Date'].dt.day_name()
    daily_totals['Is Weekday'] = daily_totals['Payroll Date'].dt.weekday < 5  # Monday=0, Sunday=6
    
    return daily_totals

def main():
    st.set_page_config(page_title="Team Hours Analysis", layout="wide")
    st.title("Team Hours Analysis Dashboard | Made with ❤️ by Juan Mackie")
    
    st.info("""
    ### How to Use This App
    
    1. Make sure Streamlit is installed: `python -m pip install streamlit pandas plotly numpy`
    2. Run this app using: `python -m streamlit run your_file.py`
    3. A browser window will automatically open
    4. Use the file uploader in the sidebar to select your CSV file
    
    This app analyzes your team's work hours and highlights days where technicians worked less than the threshold or more than the overtime threshold.
    """)
    
    # Upload section
    st.sidebar.header("Upload & Configuration")
    uploaded_file = st.sidebar.file_uploader("Upload time tracking CSV", type="csv")
    
    if not uploaded_file:
        st.warning("Please upload a CSV file using the sidebar to begin analysis.")
        st.stop()
    
    # Configuration options
    threshold = st.sidebar.number_input("Minimum Hours Threshold", value=8.0, min_value=0.0, step=0.5)
    overtime_threshold = st.sidebar.number_input("Overtime Hours Threshold", value=8.0, min_value=0.0, step=0.5)
    rounding = st.sidebar.selectbox("Rounding Method", ["None", "15 minutes", "30 minutes", "Hour"])
    show_travel = st.sidebar.checkbox("Include Travel Time", value=True)
    
    # Load and process data
    df = load_data(uploaded_file)
    if df is None:
        st.stop()
    
    # Filter out travel time if needed
    if not show_travel:
        df = df[df['Type'] != 'Travel Time']
    
    # Calculate daily totals with rounding
    daily_totals = calculate_daily_totals(df, rounding)
    
    # Calculate key metrics
    total_days = len(daily_totals)
    low_hours_days = len(daily_totals[daily_totals['Rounded Hours'] < threshold])
    overtime_days = len(daily_totals[daily_totals['Rounded Hours'] > overtime_threshold])
    avg_hours = daily_totals['Rounded Hours'].mean() if not daily_totals.empty else 0
    
    # Display key metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Worked Days", total_days)
    col2.metric(f"Days Below {threshold} Hours", low_hours_days)
    col3.metric(f"Days Over {overtime_threshold} Hours", overtime_days)
    col4.metric("Average Hours/Day", f"{avg_hours:.2f}")
    
    # Visualizations
    st.subheader("Daily Hours Overview")
    
    # Create a copy for visualization to avoid modifying original data
    viz_data = daily_totals.copy()
    
    # Add a column to identify hours status
    viz_data['Status'] = viz_data['Rounded Hours'].apply(
        lambda x: 'Below Threshold' if x < threshold 
        else ('Overtime' if x > overtime_threshold else 'Meets Threshold')
    )
    
    # Create a combined column for technician and status for color coding
    viz_data['Tech-Status'] = viz_data['Technician Name'] + ' - ' + viz_data['Status']
    
    # Create color mapping for technician-status combinations
    technicians = viz_data['Technician Name'].unique()
    
    # Define base colors for each technician
    base_colors = px.colors.qualitative.Plotly[:len(technicians)] if len(technicians) <= 10 else px.colors.qualitative.Alphabet[:len(technicians)]
    
    # Create color mapping dictionary
    color_mapping = {}
    for i, tech in enumerate(technicians):
        base_color = base_colors[i % len(base_colors)]
        # For "Meets Threshold" - use base color
        color_mapping[f"{tech} - Meets Threshold"] = base_color
        # For "Below Threshold" - use a lighter version of the base color
        # We'll use a simple approach to lighten the color by blending with white
        if base_color.startswith('#'):
            # Convert hex to RGB
            r, g, b = int(base_color[1:3], 16), int(base_color[3:5], 16), int(base_color[5:7], 16)
            # Lighten by blending with white (70% base color, 30% white)
            r = int(r * 0.7 + 255 * 0.3)
            g = int(g * 0.7 + 255 * 0.3)
            b = int(b * 0.7 + 255 * 0.3)
            light_color = f"#{r:02x}{g:02x}{b:02x}"
            color_mapping[f"{tech} - Below Threshold"] = light_color
        # For "Overtime" - use a darker version of the base color
        if base_color.startswith('#'):
            # Convert hex to RGB
            r, g, b = int(base_color[1:3], 16), int(base_color[3:5], 16), int(base_color[5:7], 16)
            # Darken by blending with black (70% base color, 30% black)
            r = int(r * 0.7)
            g = int(g * 0.7)
            b = int(b * 0.7)
            dark_color = f"#{r:02x}{g:02x}{b:02x}"
            color_mapping[f"{tech} - Overtime"] = dark_color
    
    # Create the bar chart with enhanced color coding
    fig = px.bar(viz_data,
                 x='Payroll Date',
                 y='Rounded Hours',
                 color='Tech-Status',
                 hover_data=['Rounded Hours', 'Status', 'Technician Name', 'Day of Week'],
                 color_discrete_map=color_mapping)
    
    # Add threshold lines
    fig.add_hline(y=threshold, line_dash="dash", line_color="red",
                  annotation_text=f"Min Threshold: {threshold} hours")
    fig.add_hline(y=overtime_threshold, line_dash="dash", line_color="orange",
                  annotation_text=f"Overtime Threshold: {overtime_threshold} hours")
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Low hours analysis
    low_hours = daily_totals[daily_totals['Rounded Hours'] < threshold]
    if not low_hours.empty:
        st.subheader(f"Days Below {threshold} Hours ({len(low_hours)})")
        
        # Show both raw and rounded values if rounding is applied
        if rounding != "None":
            display_data = low_hours[['Technician Name', 'Payroll Date', 'Raw Hours', 'Rounded Hours', 'Day of Week']].copy()
            sort_column = 'Raw Hours'
        else:
            display_data = low_hours[['Technician Name', 'Payroll Date', 'Raw Hours', 'Day of Week']].copy()
            display_data.rename(columns={'Raw Hours': 'Hours'}, inplace=True)
            sort_column = 'Hours'  # Changed from 'Raw Hours' to 'Hours' after rename
        
        # Sort by hours (ascending to show lowest first)
        display_data = display_data.sort_values(sort_column)
        
        # Format the display
        if rounding != "None":
            st.dataframe(
                display_data.style.format({
                    'Raw Hours': '{:.2f}', 
                    'Rounded Hours': '{:.2f}'
                })
            )
        else:
            st.dataframe(
                display_data.style.format({sort_column: '{:.2f}'})  # Updated to use the correct column name
            )
        
        # Technician-specific analysis
        st.subheader("Technician Analysis")
        tech_analysis = low_hours.groupby('Technician Name').agg(
            Days_Below=('Rounded Hours', 'count'),
            Avg_Hours=('Rounded Hours', 'mean'),
            Total_Hours=('Rounded Hours', 'sum')
        ).reset_index()
        
        st.dataframe(tech_analysis.style.format({
            "Avg_Hours": "{:.2f}", 
            "Total_Hours": "{:.2f}"
        }))
    
    # Overtime analysis
    overtime_data = daily_totals[daily_totals['Rounded Hours'] > overtime_threshold]
    if not overtime_data.empty:
        st.subheader(f"Overtime Days Over {overtime_threshold} Hours ({len(overtime_data)})")
        
        # Add weekday/weekend categorization
        overtime_data['Day Type'] = overtime_data['Is Weekday'].apply(lambda x: 'Weekday' if x else 'Weekend')
        
        # Show both raw and rounded values if rounding is applied
        if rounding != "None":
            display_data = overtime_data[['Technician Name', 'Payroll Date', 'Raw Hours', 'Rounded Hours', 'Day of Week', 'Day Type']].copy()
            sort_column = 'Raw Hours'
        else:
            display_data = overtime_data[['Technician Name', 'Payroll Date', 'Raw Hours', 'Day of Week', 'Day Type']].copy()
            display_data.rename(columns={'Raw Hours': 'Hours'}, inplace=True)
            sort_column = 'Hours'
        
        # Sort by hours (descending to show highest overtime first)
        display_data = display_data.sort_values(sort_column, ascending=False)
        
        # Format the display
        if rounding != "None":
            st.dataframe(
                display_data.style.format({
                    'Raw Hours': '{:.2f}', 
                    'Rounded Hours': '{:.2f}'
                })
            )
        else:
            st.dataframe(
                display_data.style.format({sort_column: '{:.2f}'})
            )
        
        # Separate weekday and weekend overtime
        weekday_overtime = overtime_data[overtime_data['Is Weekday']]
        weekend_overtime = overtime_data[~overtime_data['Is Weekday']]
        
        col1, col2 = st.columns(2)
        
        with col1:
            if not weekday_overtime.empty:
                st.subheader(f"Weekday Overtime ({len(weekday_overtime)})")
                weekday_display = weekday_overtime[['Technician Name', 'Payroll Date', 'Rounded Hours' if rounding != "None" else 'Raw Hours', 'Day of Week']].copy()
                weekday_display = weekday_display.sort_values('Rounded Hours' if rounding != "None" else 'Raw Hours', ascending=False)
                st.dataframe(weekday_display.style.format({
                    'Rounded Hours': '{:.2f}', 
                    'Raw Hours': '{:.2f}'
                }))
        
        with col2:
            if not weekend_overtime.empty:
                st.subheader(f"Weekend Overtime ({len(weekend_overtime)})")
                weekend_display = weekend_overtime[['Technician Name', 'Payroll Date', 'Rounded Hours' if rounding != "None" else 'Raw Hours', 'Day of Week']].copy()
                weekend_display = weekend_display.sort_values('Rounded Hours' if rounding != "None" else 'Raw Hours', ascending=False)
                st.dataframe(weekend_display.style.format({
                    'Rounded Hours': '{:.2f}', 
                    'Raw Hours': '{:.2f}'
                }))
        
        # Technician-specific overtime analysis
        st.subheader("Overtime Analysis by Technician")
        tech_overtime_analysis = overtime_data.groupby('Technician Name').agg(
            Overtime_Days=('Rounded Hours', 'count'),
            Avg_Overtime_Hours=('Rounded Hours', 'mean'),
            Total_Overtime_Hours=('Rounded Hours', 'sum')
        ).reset_index()
        
        # Adjust mean calculation to show average overtime (not average of all hours)
        overtime_columns = ['Rounded Hours' if rounding != "None" else 'Raw Hours'][0]
        tech_overtime_analysis['Avg_Overtime_Hours'] = overtime_data.groupby('Technician Name')[overtime_columns].mean().values
        
        st.dataframe(tech_overtime_analysis.style.format({
            "Avg_Overtime_Hours": "{:.2f}", 
            "Total_Overtime_Hours": "{:.2f}"
        }))
    
    # Detailed view of all data
    st.subheader("Detailed Data Analysis")
    
    # Add a filter for technician
    if 'Technician Name' in df.columns:
        technicians = df['Technician Name'].dropna().unique()
        selected_tech = st.multiselect("Filter by Technician", options=technicians, default=technicians)
        
        # Filter the data
        filtered_df = df[df['Technician Name'].isin(selected_tech)]
    else:
        filtered_df = df
    
    # Show filtered data
    st.dataframe(filtered_df)
    
    # Add download button for filtered data
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        label="Download filtered data as CSV",
        data=csv,
        file_name="filtered_hours.csv",
        mime="text/csv"
    )

if __name__ == "__main__":
    main()