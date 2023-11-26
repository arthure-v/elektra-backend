from flask_cors import CORS, cross_origin
from flask import Flask,request,abort,send_from_directory
import uuid as uid
import pandas as pd
import datetime as dt
from loguru import logger   
import requests as rq
import os
import json
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi



################## DB #######################

secret = json.load(open("/etc/secrets/secret.json","r"))
client = MongoClient(secret['uri'], server_api=ServerApi('1'))
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
    logger.info('Connected DB\n')
except Exception as e:
    logger.error(e)

def insertData(data):
    try:
        col = client['elektra']['registration']
        col.insert_one(data)
        return True
    except Exception as e:
        return False

def getData():
    col = client['elektra']['registration']
    cur = col.find({},{'_id' : 0})
    return cur


################## Flask #######################

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['DEBUG'] = True

def handleForm(request):
    try:
        logger.info('Handling Input\n')
        data = dict(request.form)
        json_data = {
            'Name' : data['name'],
            "Email" : data['email'],
            "Phone" : data['phone'],
            "Institute" : data['inst'],
            "Department" : data['dept'],
            "Year" : data['year'],
            "Workshop" : data['wrk'],
            "Food" : data['food'],
            "IEEE Member" : data['ieee'],
            "IEEE ID" : data['ieee_id'],
            "Referral ID" : data['ref']
        }
        data = {'content' : '**Name** : ' + data['name'] + '\n**Email** : ' +data['email'] +
        '\n**Phone** : ' + data['phone'] + '\n**Institute** : ' + data['inst'] +
        '\n**Department** : ' + data['dept'] + '\n**Year** : ' + data['year'] +
        '\n**WorkShop** : ' + data['wrk'] + '\n**Food** : ' + data['food'] +
        '\n**IEEE Member** : ' + data['ieee'] + '\n**IEEE ID** : ' + data['ieee_id'] + 
        '\n**Referral ID** : ' + data['ref']}
       
        with rq.session() as session:
            d = session.post(secret['reg_hook'], data=data,files={request.files['file-upload'].filename : request.files['file-upload'].read()})
            json_data['url'] = d.json()['attachments'][0]['url']
            if insertData(json_data):
                logger.info('Handling Input\n')
            else:
                logger.error('Error in Inserting : ' + str(e) + '\n')
            session.close()
            
        return True
    except Exception as e:
        logger.error('Error : ' + str(e) + '\n')
        return False

@app.route('/')
@cross_origin()
def home():
    logger.info('Pinging\n')
    return {'message' : 'success'}

@app.route('/api/register', methods=['POST'])
@cross_origin()
def saveData():
    logger.info('pinged register\n')
    if request.method == 'POST':
        if handleForm(request):
            return {'message' : 'success'}
        return {'message' : 'failure'}
    abort(405)

@app.route('/api/fetch/table/for/every/10/minute/please', methods=['GET'])
@cross_origin()
def getDiscordData():
    logger.info('pinged Discord data\n')
    if request.method == 'GET':
        name = "ELEKTRA REG " + str(dt.datetime.now().strftime("%d-%m-%Y-%H-%M-%S")) + '.xlsx'
        df = pd.DataFrame(list(getData()))
        df.to_excel('./data/' + name, index=False)
        logger.info('Sending Sheet\n')
        with rq.session() as session:
            session.post(secret['ten_hook'], files={name : open('./data/' + name, 'rb')})
            os.remove('./data/' + name)
            session.close()
        return {'message' : 'success'}
    abort(405)


@app.route('/api/file/<filename>', methods=['GET'])
@cross_origin()
def getFile(filename):
    if request.method == 'GET':
        return send_from_directory('./uploads', filename)
    abort(405)

if __name__ == "__main__":
    app.run()