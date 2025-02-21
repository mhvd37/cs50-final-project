
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
import sqlite3
import os
import csv

app = Flask(__name__)
app.secret_key = 'your_secret_key'
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the uploads folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize the database
def init_db():
    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS sales (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT NOT NULL,
                        product TEXT NOT NULL,
                        amount REAL NOT NULL
                    )''')
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database initialization error: {e}")
    finally:
        conn.close()

# Home route to display sales data
@app.route('/')
def index():
    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('SELECT date, product, amount FROM sales ORDER BY date DESC')
        data = c.fetchall()
    except sqlite3.Error as e:
        flash(f"Error fetching data: {e}")
        data = []
    finally:
        conn.close()
    return render_template('index.html', data=data)

# Upload route to handle CSV file uploads
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files.get('file')

        if not file or file.filename == '':
            flash('No file selected.')
            return redirect(request.url)

        if not file.filename.lower().endswith('.csv'):
            flash('Only CSV files are allowed.')
            return redirect(request.url)

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        try:
            file.save(filepath)
            with open(filepath, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)

                required_fields = {'date', 'product', 'amount'}
                if not required_fields.issubset(reader.fieldnames):
                    flash('CSV file must contain date, product, and amount columns.')
                    return redirect(request.url)

                conn = sqlite3.connect('database.db')
                c = conn.cursor()

                for row in reader:
                    try:
                        c.execute('INSERT INTO sales (date, product, amount) VALUES (?, ?, ?)',
                                  (row['date'], row['product'], float(row['amount'])))
                    except (ValueError, KeyError) as e:
                        flash(f"Error in CSV row: {e}")
                        continue

                conn.commit()
                flash('File uploaded and data added successfully!')

        except Exception as e:
            flash(f"An error occurred: {e}")
        finally:
            conn.close()

        return redirect(url_for('index'))

    return render_template('upload.html')

if __name__ == '__main__':
    init_db()
    app.run(debug=False, host='0.0.0.0', port=5000)
