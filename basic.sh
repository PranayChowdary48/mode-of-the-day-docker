#!/bin/bash

# Display docker version
docker --version
# run a special container to check docker
docker run hello-world
# pull image from docker hub
docker pull alpine
# pull and run a container
docker container run centos:7 echo 'Hello World!'
# run a container in background and keep it alive
docker container run -di alpine
# stop running containers
docker stop $(docker ps -q) 
# remove exited containers
docker rm $(docker ps -a -q -f status=exited)
# remove images
docker rmi $(docker images -q)