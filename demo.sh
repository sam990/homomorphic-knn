#!/bin/bash

# This script is used to run the knn encrypter program

cd cloud_service_provider
# Run the cloud service provider
python3 csp_server.py > /dev/null 2>&1 &
CSP_PID=$!
if [ $? -eq 0 ]; then
    echo "CSP server started successfully"
else
    echo "CSP server failed to start"
    exit 1
fi

cd ../data_owner

# Run the data owner
python3 owner.py > /dev/null 2>&1 &
OWNER_PID=$!

if [ $? -eq 0 ]; then
    echo "Data owner started successfully"
else
    echo "Data owner failed to start"
    exit 1
fi

cd ..

sleep 2 # Wait for the data owner and CSP to start

# upload the data from owner to csp
echo "Uploading data from owner to CSP"
curl -X POST http://localhost:5001/uploaddatabase
echo ""
echo ""

# Run the client
python3 demo.py

# Kill the data owner and CSP
kill $OWNER_PID
kill $CSP_PID