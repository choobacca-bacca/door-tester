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

DIPinOne = ""
DIPinTwo = ""
successOne = True
successTwo = True

session = requests.Session()
session.auth = ("root", "00000000")

for i in range(3600):
    for door in config["doors"]:
        try:
            response = session.get(
                config["doors"][door]+"/digitalinput/0/value", timeout=10)
            successOne = True
            responseJSON = xmltodict.parse(response.content)
            DIPinOne = responseJSON["ADAM-6052"]["DI"]["ID"]
        except:
            successOne = False
            print("error for restful call 1")

        try:
            response = session.get(
                config["doors"][door]+"/digitalinput/1/value", timeout=10)
            successTwo = True
            responseJSON = xmltodict.parse(response.content)
            DIPinTwo = responseJSON["ADAM-6052"]["DI"]["ID"]
        except:
            successTwo = False
            print("error for restful call 2")

        door_mode = 0

        if (successOne and successTwo):
            if (DIPinOne == 1):
                door_mode = 0  # door is closed
            elif (DIPinTwo == 1):
                door_mode = 2  # door is open
            else:
                door_mode = 1  # door is moving
        else:
            door_mode = 3

        data = {
            "door_name": door,
            "current_mode": door_mode
        }

        try:
            publish_future, packet_id = mqtt_connection.publish(
                topic=(config["mqtt"]["get-topic"] +
                       config["doors"][door] + "/data"),
                payload=json.dumps(data),
                qos=mqtt.QoS.AT_LEAST_ONCE,
            )
            print("published to topic " + config["mqtt"]["get-topic"] +
                  config["doors"][door] + "/data")
        except (KeyboardInterrupt, SystemExit):
            print ("\nkeyboardinterrupt caught (again)")
            print ("\n...Program Stopped Manually!")
            raise
        except Exception as err:
            print(f"{err}")
            print("error for mqtt publish")
            print("published to topic " + config["mqtt"]["get-topic"] +
                  config["doors"][door] + "/data")
        

    print(i)
