import numpy as np
import requests


UNIFORM_SAMPLE_SPACE = 10
RANDOM_SEED = 46
DO_URL = "http://localhost:5001"
CSP_URL = "http://localhost:5000"
B1 = 10

np.random.seed(RANDOM_SEED)

def generate_N(D: int) -> np.array:
    '''Generates a diagonal matrix of size D with random values from 1 to UNIFORM_SAMPLE_SPACE'''
    vec = np.random.randint(1, UNIFORM_SAMPLE_SPACE, size=D)
    return np.diag(vec)



def encrypt_query(query: np.array, queryid: str) -> np.array:
    '''Encrypts the query and returns the encrypted query'''
    D = query.shape[0]
    N = generate_N(D)
    qdot = B1 * np.matmul(query, N)
    response = requests.post(DO_URL + "/encryptquery", json={"datapoints": qdot.tolist(), "queryid": queryid})
    if response.status_code != 200:
        print("Error encrypting query")
        return None
    qcap = np.array(response.json().get("datapoints"))
    eita = qcap.shape[0]
    Ncap = np.diag(np.concatenate((np.diag(N), np.ones(eita-D, dtype=np.int64))))
    Ncapinv = np.linalg.inv(Ncap)
    qtildemat = np.matmul(qcap, Ncapinv)
    qtildecev = np.sum(qtildemat, axis=1)
    return qtildecev


def getKnn(query: np.array, k: int, queryid: str) -> np.array:
    '''Returns the k nearest neighbors of query in the encrypted database'''
    response = requests.post(CSP_URL + "/computeknn", json={"query": query.tolist(), "k": k, "queryid": queryid})
    if response.status_code != 200:
        print("Error getting knn")
        return None
    return np.array(response.json().get("datapoints"))

def decrypt_datapoints(datapoints: np.array) -> np.array:
    '''Decrypts the datapoints and returns the decrypted datapoints'''
    response = requests.post(DO_URL + "/decrypt", json={"datapoints": datapoints.tolist()})
    if response.status_code != 200:
        print("Error decrypting datapoints")
        return None
    return np.array(response.json().get("datapoints"))

def getKnnEnc(query: np.array, k: int, queryid: str) -> np.array:
    '''Returns the k nearest neighbors of query in the encrypted database'''

    qtildecev = encrypt_query(query, queryid)
    if qtildecev is None:
        return None
    datapoints = getKnn(qtildecev, k, queryid)
    if datapoints is None:
        return None
    return decrypt_datapoints(datapoints)
