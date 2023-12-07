import numpy as np
from query_user.unencrypted_knn import knn, load_data
from query_user.user import getKnnEnc


DATA_SAMPLE_SPACE = 100
RANDOM_SEED = 46

unencrypted_data = load_data("data_owner/data.csv")
data_dimnesion = unencrypted_data.shape[1]


def get_knn_and_compare(query: np.array, k: int, querid: str) -> np.array:
    enc_knn = getKnnEnc(query, k, querid)
    unenc_knn = knn(unencrypted_data, query, k)

    sorted_enc_knn = sorted(enc_knn.tolist())
    sorted_unenc_knn = sorted(unenc_knn.tolist())

    print("Query: ", query.tolist())
    print("K: ", k)
    print()
    print("Encrypted knn")
    for i in sorted_enc_knn:
        print(i)
    print()
    print("Unencrypted knn: ")
    for i in sorted_unenc_knn:
        print(i)
    print()
    print("Encrypted knn == Unencrypted knn: ", sorted_enc_knn == sorted_unenc_knn)
    print('\n')

def main():
    '''Runs knn for 10 random queries with different k and compares the results with the unencrypted knn'''
    np.random.seed(RANDOM_SEED)
    for k in range(1, 6):
        query = np.array([-59, -65, -28, 66, 60, 25, 29, -35, -19, 20, 37, -73, 9, -39, 30, 60, 0, -27, -87, 72])
        get_knn_and_compare(query, k, str(k+1))


if __name__ == "__main__":
    main()