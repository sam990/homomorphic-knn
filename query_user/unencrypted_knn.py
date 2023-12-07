import numpy as np
import csv


def load_data(filename: str) -> np.array:
    data = []
    with open(filename, 'r') as f:
        reader = csv.reader(f)
        data = list(reader)
        data = np.array(data, dtype=np.int64)
    return data

def knn(data: np.array, query: np.array, k: int) -> np.array:
    '''Returns the k nearest neighbors of query in data'''
    dist = np.linalg.norm(data - query, axis=1)
    indices = np.argpartition(dist, k)[:k]
    return data[indices]


