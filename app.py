from flask import Flask, jsonify, render_template, Response, request
from flask_cors import CORS
from datetime import datetime
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.units import inch

app = Flask(__name__)
CORS(app)

# Load dataset safely
try:
    df = pd.read_csv("ecommerce_data.csv")
    df['order_date'] = pd.to_datetime(df['order_date'])
except FileNotFoundError:
    df = pd.DataFrame()
    print("⚠️ Warning: ecommerce_data.csv not found. Please run generate_data.py")

@app.route('/')
def home():
    return render_template('index.html')

# ============================================
# EXISTING ENDPOINTS (WITH ERROR HANDLING)
# ============================================

@app.route('/api/kpis')
def kpis():
    if df.empty:
        return jsonify({"error": "No data available"}), 404
    
    try:
        total_sales = df['total_price'].sum()
        total_orders = df.shape[0]
        avg_order_value = total_sales / total_orders
        
        return jsonify({
            "total_sales": float(total_sales),
            "total_orders": int(total_orders),
            "avg_order_value": float(avg_order_value)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sales_by_category')
def sales_by_category():
    if df.empty:
        return jsonify({"error": "No data available"}), 404
    
    try:
        data = df.groupby('product_category')['total_price'].sum().reset_index()
        data = data.sort_values('total_price', ascending=False)
        return jsonify(data.to_dict(orient='records'))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sales_by_month')
def sales_by_month():
    if df.empty:
        return jsonify({"error": "No data available"}), 404
    
    try:
        df_copy = df.copy()
        df_copy['month'] = df_copy['order_date'].dt.to_period('M').astype(str)
        data = df_copy.groupby('month')['total_price'].sum().reset_index()
        return jsonify(data.to_dict(orient='records'))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================
# NEW ENDPOINTS
# ============================================

@app.route('/api/sales_by_date_range')
def sales_by_date_range():
    """Filter sales data by date range"""
    if df.empty:
        return jsonify({"error": "No data available"}), 404
    
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date or not end_date:
            return jsonify({"error": "Please provide start_date and end_date"}), 400
        
        # Convert to datetime
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        
        # Filter data
        filtered_df = df[(df['order_date'] >= start) & (df['order_date'] <= end)]
        
        if filtered_df.empty:
            return jsonify({"message": "No data found for the selected date range", "count": 0})
        
        # Calculate metrics
        total_sales = filtered_df['total_price'].sum()
        total_orders = filtered_df.shape[0]
        avg_order_value = total_sales / total_orders if total_orders > 0 else 0
        
        # Category breakdown
        category_sales = filtered_df.groupby('product_category')['total_price'].sum().to_dict()
        
        return jsonify({
            "total_sales": float(total_sales),
            "total_orders": int(total_orders),
            "avg_order_value": float(avg_order_value),
            "category_sales": category_sales,
            "date_range": {
                "start": start_date,
                "end": end_date
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/top_products')
def top_products():
    """Get top selling products"""
    if df.empty:
        return jsonify({"error": "No data available"}), 404
    
    try:
        limit = request.args.get('limit', 10, type=int)
        
        # Aggregate by product
        product_sales = df.groupby('product_name').agg({
            'total_price': 'sum',
            'quantity': 'sum',
            'order_id': 'count'
        }).reset_index()
        
        product_sales.columns = ['product_name', 'total_sales', 'total_quantity', 'order_count']
        product_sales = product_sales.sort_values('total_sales', ascending=False).head(limit)
        
        return jsonify(product_sales.to_dict(orient='records'))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/customer_insights')
def customer_insights():
    """Get customer behavior insights"""
    if df.empty:
        return jsonify({"error": "No data available"}), 404
    
    try:
        # Unique customers
        unique_customers = df['customer_id'].nunique()
        
        # Orders per customer
        orders_per_customer = df.groupby('customer_id')['order_id'].count()
        avg_orders_per_customer = orders_per_customer.mean()
        
        # Repeat customers (more than 1 order)
        repeat_customers = (orders_per_customer > 1).sum()
        repeat_rate = (repeat_customers / unique_customers * 100) if unique_customers > 0 else 0
        
        # Customer lifetime value
        customer_ltv = df.groupby('customer_id')['total_price'].sum()
        avg_customer_ltv = customer_ltv.mean()
        
        # Top customers
        top_customers = customer_ltv.sort_values(ascending=False).head(5)
        
        return jsonify({
            "unique_customers": int(unique_customers),
            "avg_orders_per_customer": float(avg_orders_per_customer),
            "repeat_customers": int(repeat_customers),
            "repeat_rate_percent": float(repeat_rate),
            "avg_customer_ltv": float(avg_customer_ltv),
            "top_customers": [
                {"customer_id": int(cid), "total_spent": float(val)} 
                for cid, val in top_customers.items()
            ]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/download_csv')
def download_csv():
    """Download CSV with optional date filtering"""
    if df.empty:
        return jsonify({"error": "No data available"}), 404
    
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Filter if dates provided
        if start_date and end_date:
            start = pd.to_datetime(start_date)
            end = pd.to_datetime(end_date)
            filtered_df = df[(df['order_date'] >= start) & (df['order_date'] <= end)]
        else:
            filtered_df = df
        
        csv = filtered_df.to_csv(index=False)
        filename = f"sales_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return Response(
            csv,
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment;filename={filename}"}
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate_pdf_report')
def generate_pdf_report():
    """Generate PDF report with optional date filtering"""
    if df.empty:
        return jsonify({"error": "No data available"}), 404
    
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Filter if dates provided
        if start_date and end_date:
            start = pd.to_datetime(start_date)
            end = pd.to_datetime(end_date)
            filtered_df = df[(df['order_date'] >= start) & (df['order_date'] <= end)]
            date_range_text = f"{start_date} to {end_date}"
        else:
            filtered_df = df
            date_range_text = "All Time"
        
        if filtered_df.empty:
            return jsonify({"error": "No data for selected date range"}), 404
        
        # Create PDF in memory
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=30,
            alignment=1  # Center
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=12,
        )
        
        # Title
        title = Paragraph("E-Commerce Sales Report", title_style)
        elements.append(title)
        
        # Date range
        date_info = Paragraph(f"<b>Report Period:</b> {date_range_text}", styles['Normal'])
        elements.append(date_info)
        elements.append(Spacer(1, 0.3*inch))
        
        # KPIs Summary
        total_sales = filtered_df['total_price'].sum()
        total_orders = filtered_df.shape[0]
        avg_order = total_sales / total_orders if total_orders > 0 else 0
        
        elements.append(Paragraph("Executive Summary", heading_style))
        
        kpi_data = [
            ['Metric', 'Value'],
            ['Total Sales', f'₹{total_sales:,.2f}'],
            ['Total Orders', f'{total_orders:,}'],
            ['Average Order Value', f'₹{avg_order:,.2f}'],
        ]
        
        kpi_table = Table(kpi_data, colWidths=[3*inch, 3*inch])
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(kpi_table)
        elements.append(Spacer(1, 0.4*inch))
        
        # Sales by Category
        elements.append(Paragraph("Sales by Category", heading_style))
        
        category_sales = filtered_df.groupby('product_category')['total_price'].sum().reset_index()
        category_sales = category_sales.sort_values('total_price', ascending=False)
        
        cat_data = [['Category', 'Sales (₹)']]
        for _, row in category_sales.iterrows():
            cat_data.append([row['product_category'], f"₹{row['total_price']:,.2f}"])
        
        cat_table = Table(cat_data, colWidths=[3*inch, 3*inch])
        cat_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ecc71')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(cat_table)
        elements.append(Spacer(1, 0.4*inch))
        
        # Top Products
        elements.append(Paragraph("Top 10 Products", heading_style))
        
        top_products = filtered_df.groupby('product_name').agg({
            'total_price': 'sum',
            'quantity': 'sum'
        }).reset_index()
        top_products = top_products.sort_values('total_price', ascending=False).head(10)
        
        prod_data = [['Product', 'Units Sold', 'Revenue (₹)']]
        for _, row in top_products.iterrows():
            prod_data.append([
                row['product_name'],
                f"{int(row['quantity']):,}",
                f"₹{row['total_price']:,.2f}"
            ])
        
        prod_table = Table(prod_data, colWidths=[2.5*inch, 1.5*inch, 2*inch])
        prod_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(prod_table)
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        
        filename = f"sales_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return Response(
            buffer.getvalue(),
            mimetype="application/pdf",
            headers={"Content-Disposition": f"attachment;filename={filename}"}
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)