import mysql.connector
from flask import Flask, render_template

conn = mysql.connector.connect(
    host="82.66.24.184",
    port=3305,
    user="cinemacousas",
    password="password",
    database="Cinemacousas"
)

cursor = conn.cursor()
cursor.execute("SHOW TABLES")

tables = cursor.fetchall()
for table in tables:
    print(table[0])

cursor.close()
conn.close()

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html', storeUrl=True)

@app.route('/movies')
def movies():
    return render_template('movies.html', storeUrl=True)

@app.route('/login')
def login():
    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5500)

