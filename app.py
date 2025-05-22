from flask import Flask, render_template, request, redirect, url_for, send_file, flash
import pandas as pd
from fpdf import FPDF
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  

BILL_CSV = 'bill.csv'  


def get_items():
    df = pd.read_csv(BILL_CSV)
    return df['Item'].tolist()


def generate_pdf(dataframe, filename='bill_invoice.pdf'):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Smart Grocery Billing Invoice", ln=True, align='C')

    
    pdf.cell(60, 10, "Item", 1)
    pdf.cell(40, 10, "Price", 1)
    pdf.cell(40, 10, "Quantity", 1)
    pdf.cell(40, 10, "Total", 1)
    pdf.ln()

    
    for _, row in dataframe.iterrows():
        pdf.cell(60, 10, str(row['Item']), 1)
        pdf.cell(40, 10, str(row['Price']), 1)
        pdf.cell(40, 10, str(row['Quantity']), 1)
        pdf.cell(40, 10, str(row['Total']), 1)
        pdf.ln()

    
    total_amount = dataframe['Total'].sum()
    pdf.cell(140, 10, "Grand Total", 1)
    pdf.cell(40, 10, str(total_amount), 1)

    pdf.output(filename)
    return filename


@app.route('/', methods=['GET', 'POST'])
def index():
    df = pd.read_csv(BILL_CSV)

    if request.method == 'POST':
        item = request.form.get('item')
        quantity = int(request.form.get('quantity', 1))

        
        item_row = df[df['Item'] == item]
        if item_row.empty:
            flash('Selected item not found!', 'error')
            return redirect(url_for('index'))

        price = float(item_row['Price'].values[0])
        total = price * quantity

        
        if 'Quantity' not in df.columns:
            df['Quantity'] = 0
            df['Total'] = 0

        
        df.loc[df['Item'] == item, 'Quantity'] += quantity
        df.loc[df['Item'] == item, 'Total'] = df.loc[df['Item'] == item, 'Price'] * df.loc[df['Item'] == item, 'Quantity']

        df.to_csv(BILL_CSV, index=False)

        flash(f'Added {quantity} x {item} to the bill.', 'success')
        return redirect(url_for('index'))

    
    bill = df[df['Quantity'] > 0]

    total_bill = bill['Total'].sum() if not bill.empty else 0

    return render_template('index.html', items=get_items(), bill=bill.to_dict(orient='records'), total_bill=total_bill)


@app.route('/reset')
def reset_bill():
    df = pd.read_csv(BILL_CSV)
    if 'Quantity' in df.columns:
        df['Quantity'] = 0
        df['Total'] = 0
        df.to_csv(BILL_CSV, index=False)
    flash('Bill has been reset.', 'info')
    return redirect(url_for('index'))


@app.route('/download_csv')
def download_csv():
    df = pd.read_csv(BILL_CSV)
    bill = df[df['Quantity'] > 0]
    temp_file = 'bill_current.csv'
    bill.to_csv(temp_file, index=False)
    return send_file(temp_file, as_attachment=True)


@app.route('/download_pdf')
def download_pdf():
    df = pd.read_csv(BILL_CSV)
    bill = df[df['Quantity'] > 0]
    if bill.empty:
        flash('No items in bill to generate PDF.', 'error')
        return redirect(url_for('index'))
    pdf_file = generate_pdf(bill)
    return send_file(pdf_file, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)