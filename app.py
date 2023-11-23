from flask_cors import CORS, cross_origin
from flask import Flask,request,render_template,abort,send_from_directory
import sqlite3 as sql
import uuid as uid
import pandas as pd
import datetime as dt

con = sql.connect('database.db')
api = 'https://api-elektra.ieeesbcemunnar.org/api/file/'
cur = con.cursor()
cur.execute('''
    CREATE TABLE IF NOT EXISTS elektra_reg (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT NOT NULL,
    inst TEXT,
    dept TEXT,
    year TEXT,
    wrk TEXT,
    food TEXT,
    ieee TEXT,
    ieee_id TEXT,
    payment TEXT)'''
)
con.commit()


app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

def handleForm(data):
    try:
        con = sql.connect('database.db')
        data = request.files['file-upload']
        ext = data.filename.split('.')[-1]
        name = str(uid.uuid1()) + "." + ext
        data.save(f'./uploads/{str(name)}')
        data = dict(request.form)
        cur = con.cursor()
        cur.execute('''
        INSERT OR IGNORE INTO elektra_reg (name, email, phone, inst, dept, year, wrk, food, ieee, ieee_id, payment) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (data['name'], data['email'], data['phone'],data['inst'], data['dept'], data['year'], data['wrk'] , data['food'],data['ieee'], data['ieee_id'], api+name))
        con.commit()
        con.close()
        return True
    except Exception as e:
        return False
    
@app.route('/api/register', methods=['POST'])
@cross_origin()
def saveData():
    if request.method == 'POST':
        if handleForm(request):
            return {'message' : 'success'}
        return {'message' : 'failure'}
    abort(405)

@app.route('/api/getdata/table', methods=['GET'])
@cross_origin()
def getData():
    if request.method == 'GET':
        name = "ELEKTRA REG " + str(dt.datetime.now().strftime("%d-%m-%Y-%H-%M-%S")) + '.xlsx'
        con = sql.connect('database.db')
        df = pd.read_sql_query('SELECT * FROM elektra_reg',con)
        df.to_excel('./data/' + name, index=False)
        return send_from_directory('./data', name)
    abort(405)

@app.route('/api/file/<filename>', methods=['GET'])
@cross_origin()
def getFile(filename):
    if request.method == 'GET':
        return send_from_directory('./uploads', filename)
    abort(405)


if __name__ == "__main__":
    app.run()