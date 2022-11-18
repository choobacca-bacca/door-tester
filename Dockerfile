# syntax=docker/dockerfile:1

FROM ubuntu:20.04

RUN apt-get update -y
RUN apt-get install -y python3 python3-pip
RUN python3 -m pip install --upgrade pip

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY . .


CMD [ "python3", "door_controller_tester.py", "--host=0.0.0.0"]