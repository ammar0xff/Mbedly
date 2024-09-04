#!/bin/bash



if [ $(id -u) -ne 0 ]
  then echo "Please run as root."
  exit
fi


apt update 
apt install curl -y