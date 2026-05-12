from flask import Flask, render_template
import sqlite3
import pandas as pd
import plotly.graph_objs as go
import plotly
import json
import os

app = Flask(__name__)

DATA_FOLDER = "data"

# -----------------------------------
# HOME PAGE
# -----------------------------------

@app.route("/")
def home():

    conn = sqlite3.connect("data/monitoring.db")

    history_df = pd.read_sql("""
    SELECT *
    FROM insertion_history
    ORDER BY insertion_date DESC
    """, conn)

    conn.close()

    history = history_df.to_dict(orient="records")

    return render_template(
        "index.html",
        history=history,
        graphJSON=None,
        selected_date=None
    )

# -----------------------------------
# DASHBOARD PAGE
# -----------------------------------

@app.route("/dashboard/<path:selected_date>")
def dashboard(selected_date):

    monitor_conn = sqlite3.connect("data/monitoring.db")

    history_df = pd.read_sql("""
    SELECT *
    FROM insertion_history
    ORDER BY insertion_date DESC
    """, monitor_conn)

    # Get selected row
    selected_row = history_df[
        history_df["insertion_date"] == selected_date
    ].iloc[0]

    # DB names from monitoring table
    bitcoin_db = selected_row["bitcoin_db"]

    prediction_db = selected_row["prediction_db"]

    # Add data folder path
    bitcoin_db_path = os.path.join(
        DATA_FOLDER,
        bitcoin_db
    )

    prediction_db_path = os.path.join(
        DATA_FOLDER,
        prediction_db
    )

    # -----------------------------------
    # Load Historical Data
    # -----------------------------------

    bitcoin_conn = sqlite3.connect(
        bitcoin_db_path
    )

    bitcoin_df = pd.read_sql("""
    SELECT *
    FROM bitcoin_prices
    """, bitcoin_conn)

    bitcoin_conn.close()

    bitcoin_df["timestamp"] = pd.to_datetime(
        bitcoin_df["timestamp"]
    )

    # -----------------------------------
    # Load Prediction Data
    # -----------------------------------

    prediction_conn = sqlite3.connect(
        prediction_db_path
    )

    prediction_df = pd.read_sql("""
    SELECT *
    FROM bitcoin_predictions
    """, prediction_conn)

    prediction_conn.close()

    prediction_df["date"] = pd.to_datetime(
        prediction_df["date"]
    )

    # -----------------------------------
    # Create Graph
    # -----------------------------------

    historical_trace = go.Scatter(
        x=bitcoin_df["timestamp"],
        y=bitcoin_df["price"],
        mode="lines",
        name="Historical Bitcoin Price"
    )

    prediction_trace = go.Scatter(
        x=prediction_df["date"],
        y=prediction_df["predicted_price"],
        mode="lines+markers",
        name="10-Day Prediction"
    )

    layout = go.Layout(
        title="Bitcoin Price Forecast Dashboard",
        xaxis=dict(title="Date"),
        yaxis=dict(title="Bitcoin Price"),
        template="plotly_dark"
    )

    figure = go.Figure(
        data=[historical_trace, prediction_trace],
        layout=layout
    )

    graphJSON = json.dumps(
        figure,
        cls=plotly.utils.PlotlyJSONEncoder
    )

    history = history_df.to_dict(
        orient="records"
    )

    monitor_conn.close()

    return render_template(
        "index.html",
        history=history,
        graphJSON=graphJSON,
        selected_date=selected_date
    )

# -----------------------------------
# RUN APP
# -----------------------------------

if __name__ == "__main__":

    app.run(debug=True)