import csv
import numpy as np
import pickle
import requests
from flask import Flask, request
import json


############################################
# Configurations

UNIFORM_SAMPLE_SPACE = 10 # Size of uniform distribution
C = 10
EPSILON = 5
RANDOM_SEED = 42
B2 = 2

PORT = 5001

datacenter_url = "http://localhost:5000"

state_file = "state.pickle"
#############################################

############################################
# Global variables
state = {}

app = Flask(__name__)
############################################

def init():
    '''Loads state from disk'''
    global state
    try:
        with open(state_file, 'rb') as f:
            state = pickle.load(f)
    except:
        pass

def load_data(filename: str) -> np.array:
    '''Loads data from a csv file'''
    data = []
    with open(filename, 'r') as f:
        reader = csv.reader(f)
        data = list(reader)
        data = np.array(data, dtype=np.int64)
    return data

def generate_M_base(eita: int) -> np.array:
    '''Mbase should be invertible'''
    while True:
        m =  np.random.randint(-UNIFORM_SAMPLE_SPACE/2, UNIFORM_SAMPLE_SPACE/2, size=(eita, eita))
        if np.linalg.det(m) != 0:
            return m

def generate_M_t(eita: int, qmax: int, max_norm: float) -> np.array:
    '''M_t should be invertible'''
    while True:
        m = np.random.randint(qmax + 1, qmax + 1 + UNIFORM_SAMPLE_SPACE, size=(eita, eita))
        mx = np.random.randint(int(max_norm + 1), int(max_norm + 1) + UNIFORM_SAMPLE_SPACE, size=eita)
        np.fill_diagonal(m, mx)
        if np.linalg.det(m) != 0:
            return m


def save_keys(Mbase, s, w, max_norm ) -> None:
    '''Saves the keys to disk'''
    global state
    state["Mbase"] = Mbase
    state["s"] = s
    state["w"] = w
    state["max_norm"] = max_norm
    with open(state_file, 'wb') as f:
        pickle.dump(state, f)

    

def encrypt_database(data : np.array) -> np.array:
    '''Encrypts the database'''
    D = data.shape[1] # D = dimension of data
    eita = D + 1 + C + EPSILON # eita = dimension of encrypted data
    Mbase = generate_M_base(eita) 
    invMbase = np.linalg.inv(Mbase) # invMbase = inverse of Mbase
    w = np.random.randint(-UNIFORM_SAMPLE_SPACE//2, UNIFORM_SAMPLE_SPACE//2, size=C) # w = random vector of size C
    s = np.random.randint(-UNIFORM_SAMPLE_SPACE//2, UNIFORM_SAMPLE_SPACE//2, size=D+1) # s = random vector of size D+1

    enc_data = []

    max_norm = np.max(np.linalg.norm(data, axis=1)) # max_norm = maximum norm of a datapoint

    # Encryption
    for p in data:
        pd = np.array([ a - 2*b for a, b in zip(s, p)])
        z = np.random.randint(-UNIFORM_SAMPLE_SPACE//2, UNIFORM_SAMPLE_SPACE//2, size=EPSILON) # z = random vector of size EPSILON
        pd = np.append(pd, s[D] + np.dot(p, p))
        pd = np.concatenate((pd, w))
        pd = np.concatenate((pd, z))
        pe = np.dot(pd, invMbase)
        enc_data.append(pe)
    
    enc_data = np.array(enc_data)
    # saving secret keys
    save_keys(Mbase, s, w, max_norm)
    return enc_data


def clear_csp_data() -> bool:
    '''Clears the cloud service provider database'''
    response = requests.post(datacenter_url + "/cleardb")
    if response.status_code != 200:
        print("Error clearing datacenter database")
        return False
    return True

def upload_csp_data(enc_datapoints: np.array) -> bool:
    '''Uploads the encrypted database to the cloud service provider'''
    response = requests.post(datacenter_url + "/upload", json={ "datapoints": enc_datapoints.tolist() })
    if response.status_code != 200:
        print("Error uploading datacenter database")
        return False
    return True


def encq(query: np.array) -> np.array:
    '''Encrypts the query'''
    global state
    Mbase = state["Mbase"]
    max_norm = state["max_norm"]

    qmax = np.max(query)
    x = np.random.randint(1, UNIFORM_SAMPLE_SPACE, size=C) # x = random vector of size C
    zerovec = np.zeros(EPSILON, dtype=np.int64) # zerovec = vector of size EPSILON with all zeros
    qdash = np.append(query, 1) # qdash = query with 1 appended to it
    qdash = np.concatenate((qdash, x)) # qdash = qdash with x appended to it
    qdash = np.concatenate((qdash, zerovec)) # qdash = qdash with zerovec appended to it
    qmat = np.diag(qdash) # qmat = diagonal matrix with qdash as diagonal
    M_t = generate_M_t(qmat.shape[0], qmax, max_norm) # M_t = random matrix of size qmat.shape[0] x qmat.shape[0]
    M_sec = np.matmul(M_t, Mbase) # M_sec = M_t * Mbase
    E = np.random.randint(int(qmax + 1), int(qmax + 1) + UNIFORM_SAMPLE_SPACE, size=M_t.shape) # E = random matrix of size M_t.shape
    # E = np.full(M_t.shape, 0)
    qcap = B2 * (np.matmul(M_sec, qmat) + E) # qcap = B2 * (M_sec * qmat + E)
    return (qcap, M_t)


@app.route('/uploaddatabase', methods=['POST'])
def uploaddatabase() -> str | tuple :
    '''Uploads the database to the cloud service provider'''

    data = load_data("data.csv")
    enc_data = encrypt_database(data)
    if not clear_csp_data():
        return "Error clearing csp database", 400
    if not upload_csp_data(enc_data):
        return "Error uploading csp database", 400
    return "OK"

@app.route('/encryptquery', methods=['POST'])
def encrypt_query() -> str | tuple :
    '''Encrypts the query and pushes it to the cloud service provider'''

    data = request.get_json()
    query = np.array(data['datapoints'], dtype=np.int64)
    query_id = data['queryid']
    qcap, M_t = encq(query)
    response = requests.post(datacenter_url + "/pushquery", json={"queryid": query_id, "Mt": M_t.tolist()})

    if response.status_code != 200:
        print("Error pushing query to datacenter")
        return "Error pushing query to datacenter", 400
    
    return json.dumps({"datapoints": qcap.tolist()})

@app.route('/decrypt', methods=['POST'])
def decrypt() -> str | tuple :
    '''Decrypts the data'''
    global state
    data = request.get_json()
    datapoints = np.array(data['datapoints'], dtype=np.float64)
    Mbase = state["Mbase"]
    s = state["s"]
    dec_data = []
    D = datapoints.shape[1] - 1 - C - EPSILON # D = dimension of data
    for pdash in datapoints:
        pd = np.matmul(pdash, Mbase)
        p = [ round((a - b)/2) for a, b in zip(s[:D], pd[:D])] 
        dec_data.append(p)
    return json.dumps({"datapoints": dec_data})


if __name__ == "__main__":
    np.random.seed(RANDOM_SEED)
    init()
    app.run(host="0.0.0.0", port=PORT)


