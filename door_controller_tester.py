from __future__ import annotations

import requests
import time
import datetime
import xmltodict

import enum

import requests
import yaml
from typing import Optional

from awscrt import io, mqtt, auth, http
from awsiot import mqtt_connection_builder
import json
import sys

success_response = 0
fail_response = 0

with open("config.yaml", 'r') as stream:
    try:
        config = yaml.safe_load(stream)
        print(config)
    except yaml.YAMLError as exc:
        print(exc)

# Spin up resources
event_loop_group = io.EventLoopGroup(1)
host_resolver = io.DefaultHostResolver(event_loop_group)
client_bootstrap = io.ClientBootstrap(
    event_loop_group, host_resolver
)
mqtt_connection = mqtt_connection_builder.mtls_from_path(
    endpoint=config["mqtt"]["api_endpoint"],
    cert_filepath=config["mqtt"]["cert"],
    pri_key_filepath=config["mqtt"]["key"],
    client_bootstrap=client_bootstrap,
    ca_filepath=config["mqtt"]["root_cert"],
    client_id=config["mqtt"]["name"],
    clean_session=False,
    keep_alive_secs=6,
)
print(
    "Connecting to {} with client ID '{}'...".format(
        config["mqtt"]["api_endpoint"], config["mqtt"]["name"]
    )
)
# Make the connect() call
# Future.result() waits until a result is available
try:
    connect_future = mqtt_connection.connect()
    connect_future.result()
except:
    print("Problem with connecting")
    sys.exit(1)

print("Connected!")

print("Please enter the duration for the run (in seconds): ")
x = input()
DIPinOne = ""
DIPinTwo = ""
successOne = True
successTwo = True

formerTime = time.time()

for i in range(int(x)):
    time.sleep(1)

    try:
        session = requests.Session()
        session.auth = ("root", "00000000")
        response = session.get(
            "http://169.254.170.22/digitalinput/0/value", timeout=10)
        successOne = True
        responseJSON = xmltodict.parse(response.content)
        DIPinOne = responseJSON["ADAM-6052"]["DI"]["ID"]
    except:
        successOne = False

    try:
        session = requests.Session()
        session.auth = ("root", "00000000")
        response = session.get(
            "http://169.254.170.22/digitalinput/1/value", timeout=10)
        successTwo = True
        responseJSON = xmltodict.parse(response.content)
        DIPinTwo = responseJSON["ADAM-6052"]["DI"]["ID"]
    except:
        successTwo = False

    data = {
        "door_name": "service_lobby_L3_door",
        "door_state": DIPinOne,
        "door_state_two": DIPinTwo
    }
    try:
        publish_future, packet_id = mqtt_connection.publish(
            topic=config["mqtt"]["get-topic"],
            payload=json.dumps(data),
            qos=mqtt.QoS.AT_LEAST_ONCE,
        )
        if (successTwo and successOne):
            print(str(i) + " Successful")
            success_response = success_response + 1
        else:
            print(str(i) + " Fail")
            fail_response = fail_response + 1
    except Exception as err:
        print(f"{err}")

f = open("results.txt", "a")
f.write("\n")
f.write("\n")
f.write("time started: " + str(datetime.datetime.now()))
f.write("\n")
f.write("successful responses = " + str(success_response) + "\n")
f.write("failed responses = " + str(fail_response))
f.close()
