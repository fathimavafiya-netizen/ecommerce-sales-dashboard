from flask import Flask, jsonify, render_template, Response
from flask_cors import CORS
from datetime import datetime
import pandas as pd

app = Flask(__name__)
CORS(app)

# Load dataset safely
try:
    df = pd.read_csv("ecommerce_data.csv")
except FileNotFoundError:
    df = pd.DataFrame()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/kpis')
def kpis():
    if df.empty:
        return jsonify({"error": "No data available"})

    total_sales = df['total_price'].sum()
    total_orders = df.shape[0]
    avg_order_value = total_sales / total_orders

    return jsonify({
        "total_sales": float(total_sales),
        "total_orders": int(total_orders),
        "avg_order_value": float(avg_order_value)
    })

@app.route('/api/sales_by_category')
def sales_by_category():
    data = df.groupby('product_category')['total_price'].sum().reset_index()
    return jsonify(data.to_dict(orient='records'))

@app.route('/api/download_csv')
def download_csv():
    csv = df.to_csv(index=False)
    filename = f"report_{datetime.now().strftime('%Y%m%d')}.csv"

    return Response(
        csv,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )

@app.route('/api/sales_by_month')
def sales_by_month():
    df_copy = df.copy()
    df_copy['order_date'] = pd.to_datetime(df_copy['order_date'])
    df_copy['month'] = df_copy['order_date'].dt.to_period('M').astype(str)

    data = df_copy.groupby('month')['total_price'].sum().reset_index()
    return jsonify(data.to_dict(orient='records'))

if __name__ == '__main__':
    app.run(debug=True)