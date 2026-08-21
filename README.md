# Uptick Hours

A Streamlit dashboard for reviewing exported pay-week hours from Uptick.

## How to Use

1. Run the app: `streamlit run hours_app.py`
2. Upload your exported time-tracking CSV using the sidebar.
3. Use the sidebar options to configure the minimum hours threshold, overtime
   threshold, rounding method, and whether travel time is included.

The app shows daily totals per technician, flags days below the minimum
threshold or above the overtime threshold, breaks down weekday/weekend
overtime, and lets you filter/download the detailed data as CSV.

## Requirements

- Python 3 (see `requirements.txt`: pandas, streamlit, plotly, numpy)

Install dependencies:

```bash
pip install -r requirements.txt
```

## Notes

- Rows whose Task Name contains RDO, Rostered Day Off, Personal Leave,
  Sick Leave, or Annual Leave are excluded from totals.
- The CSV is expected to include at least these columns: `Duration (mins)`,
  `Payroll Date`, `Task Name`, `Technician Name`, and `Type`.
- A dev container configuration is included (port 8501 forwarded).
