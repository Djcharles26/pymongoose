#!/bin/bash

#ensure a clean build

sudo docker build -t djcharles26/pymongoose:test -f Dockerfile.test . || { exit 1; }

sudo docker run \
    -d \
    --name test --rm \
    -e MONGO_URI=mongodb+srv://backdoor:f15SCUdzFcFFUotI@cluster0.boyri.mongodb.net/test \
    djcharles26/pymongoose:test /bin/bash test.sh

sleep 2

sudo docker inspect test --format='{{.State.ExitCode}}' || { exit 1;}