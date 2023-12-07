#!/usr/bin/python3

from flask import Flask
from flask import request
import json
import sqlite3
import pickle
import numpy as np
from keirudb import Keiru, IncNonce
from threading import Thread


############################################
# Configurations
database_file = "database.pickle"
queries_db = "queries.db"
PORT = 5000
############################################

############################################
# Global variables
queries_conn = None
queries_c = None
database = None
memdb = Keiru()
nonceGen = IncNonce()

app = Flask(__name__)
############################################


def init():
    '''Sets up the database and loads the database from disk'''
    global database
    global queries_conn
    global queries_c
    queries_conn = sqlite3.connect(queries_db, check_same_thread=False)
    queries_c = queries_conn.cursor()

    queries_c.execute('''CREATE TABLE IF NOT EXISTS queries
                (queryid text PRIMARY KEY, Mt text)''')
    queries_conn.commit()
    
    try:
        with open(database_file, 'rb') as f:
            database = pickle.load(f)
    except:
        pass


def prepare_db(queryid, Mt, nonce: int):
    '''Prepares the database for a query by multiplying it with Mt and pushing it to the in memory database'''
    global database
    if len(database) == 0:
        return False
    Mtinv = np.linalg.inv(Mt)
    newdb = np.array([np.matmul(x, Mtinv) for x in database])
    memdb.finishpush(queryid, newdb, nonce)
    return True

def check_query_id_data(queryid) -> bool :
    '''Checks if the queryid is present in the database and if it is, starts the process of preparing the database for the query'''
    global memdb
    if memdb.getdata(queryid) is not None:
        return True
    queries_c.execute("SELECT * FROM queries WHERE queryid=?", (queryid,))
    row = queries_c.fetchone()
    if row is None:
        return False
    Mt = np.array(json.loads(row[1]), dtype=np.int64)
    memdb.startpush(queryid)
    prepare_db(queryid, Mt)
    return True


@app.route('/cleardb', methods=['POST'])
def cleardb():
    '''Clears the database and the in memory database'''
    global database
    global memdb
    global queries_c
    global queries_conn
    database = None
    with open(database_file, 'wb') as f:
        pickle.dump(database, f)
    memdb.cleardb()
    queries_c.execute("DELETE FROM queries")
    queries_conn.commit()
    return "OK"

@app.route('/upload', methods=['POST'])
def uploaddb():
    '''Uploads the database to the server'''
    global database
    global memdb
    global queries_c
    global queries_conn

    data = request.get_json()
    datapoints = np.array(data['datapoints'], dtype=np.float64)

    if database is None:
        database = datapoints
    elif len(database[0]) != len(datapoints[0]):
        return "ERROR: Dimension mismatch", 400
    else:
        # Add the datapoints to the database    
        database = np.vstack((database, datapoints))
    with open(database_file, 'wb') as f:
        pickle.dump(database, f)

    # clear the saved query matrices as Max_Norm may have changed
    memdb.cleardb()
    queries_c.execute("DELETE FROM queries")
    queries_conn.commit()
    return "OK"

@app.route('/getdata', methods=['GET'])
def getdata():
    '''Returns the database as a json object'''
    global database
    return json.dumps(database.tolist())


@app.route('/pushquery', methods=['POST'])
def pushquery():
    '''Pushes the query matrix to the server'''
    global queries_c
    global queries_conn
    data = request.get_json()
    queryid = data['queryid'] # the query id
    mt = np.array(data['Mt'], dtype=np.float64)
    # check if the queryid is already present in the database
    queries_c.execute("SELECT * FROM queries WHERE queryid=?", (queryid,))
    row = queries_c.fetchone()
    if row is None or row[1] != str(mt.tolist()):
        # if not, add it to the database
        queries_c.execute("INSERT OR REPLACE INTO queries VALUES (?, ?)", (queryid, str(mt.tolist())))
        queries_conn.commit()
        nonce = nonceGen.get()
        # start the process of preparing the database for the query in a separate thread
        # this is done so that the client does not have to wait for the database to be prepared
        memdb.startpush(queryid, nonce)
        th = Thread(target=prepare_db, args=(queryid, mt, nonce))
        th.start()
    return "OK"

@app.route('/getmt', methods=['GET'])
def getmt():
    '''Returns the query matrix as a json object'''
    global queries_c
    global queries_conn
    queryid = request.args.get('queryid')
    queries_c.execute("SELECT * FROM queries WHERE queryid=?", (queryid,))
    row = queries_c.fetchone()
    if row is None:
        return "ERROR: queryid not found", 400
    return json.dumps({"Mt": json.loads(row[1])})

@app.route('/computeknn', methods=['POST'])
def computeknn():
    '''Computes the k nearest neighbours of the query'''
    data = request.get_json()
    queryid = data['queryid'] # the query id
    query = np.array(data['query'], dtype=np.float64) # the query
    k = data['k']


    if k > len(database):
        return "ERROR: k is greater than database size", 400
    if check_query_id_data(queryid) is False:
        return "ERROR: queryid not found", 400
    db = memdb.getdata(queryid)
    if db is None:
        return "ERROR: queryid not found", 400
    if len(db) == 0:
        return "ERROR: Database is empty", 400
    if len(db[0]) != len(query):
        return "ERROR: Dimension mismatch", 400
    
    # compute the distance between the query and all the datapoints in the database
    dist = np.dot(db, query)
    # get the indices of the k smallest distances
    idx = np.argpartition(dist, k)[:k]
    # return normal encrypted datapoints
    return json.dumps({"datapoints":  database[idx].tolist()})


if __name__ == '__main__':
    init()
    app.run(host="0.0.0.0", port=PORT)



