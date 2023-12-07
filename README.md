# Secure KNN computation on cloud

Implemenation of KNN computation between 3 parties: user, data owner and cloud service provider. None of the parties share unencrypted data with each other. 

### Instructions to run
- Install [python3](https://www.python.org/downloads/)
- Create a virtual environment using venv
```python3 -m venv {{venv_name}}```
- Activate the virtual environment
```source {{venv_name}}/bin/activate```
- Install dependencies
```pip install -r requirements.txt```
- Run the demo script to see the working
```bash demo.sh```

## Implementation Details
All the parties are assumed to be connected to network. The data owner and cloud service provider expose REST APIs for the user to interact with. The user can query the data owner for encryption of the query and then send the encrypted query to the cloud service provider. The cloud service provider then computes the KNN on the encrypted data and returns the encrypted results to the user. The user can then decrypt the results using api exposed by data owner. All the REST APIs are implemented using [Flask](https://flask.palletsprojects.com/en/1.1.x/).

- Data owner exposes REST API for following operations:
    - Encrypt data and upload to cloud service provider
    - Query encryption
    - Data decryption

- Cloud service provider exposes REST API for following operations:
    - Store encrypted data
    - Storage of temporary data for encrypted queries
    - Compute KNN on encrypted data
    - Return encrypted KNN results

- User provides following operations:
    - Query encryption
    - Decrypt KNN results
 
## Features
- Secure KNN computation on encrypted data
- Computation of temporary data on cloud is done using off path threads to reduce latency
- Reduction in memory usage as temporary data is deleted after some time
 

## Results
- Verified correctness of the implementation by comparing the results with unencrypted KNN computation on the same data for different values of K