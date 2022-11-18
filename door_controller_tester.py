from __future__ import annotations

import datetime
import enum
import json
import sys
import threading
import time
from typing import Optional

import requests
import xmltodict
import yaml
from awscrt import auth, http, io, mqtt
from awsiot import mqtt_connection_builder

#sudo apt install libcairo2-dev pkg-config python3-dev

def status_publisher(mqtt_connect, rest_session, config_file):
    DIPinOne = ""
    DIPinTwo = ""
    successOne = True
    successTwo = True

    i = 0
    start = time.time()
    interval = 1.0
    while (i < 3600):
        #    time.sleep(1
        # print(str(time.time() - start))
        if (time.time() - start > interval):
            print(time.time() - start)
            for door in config_file["doors"]:
                try:
                    response = rest_session.get(
                        config_file["doors"][door]+"/digitalinput/1/value", timeout=(5, 10)) #read if door is fully open
                    successOne = True
                    # print(response.status_code)
                    responseJSON = xmltodict.parse(response.content)
                    print(responseJSON)
                    DIPinOne = responseJSON["ADAM-6052"]["DI"]["VALUE"]
                except Exception as err:
                    print(f"{err}")
                    successOne = False
                    print("error for restful call 1")

                try:
                    response = rest_session.get(
                        config_file["doors"][door]+"/digitalinput/2/value", timeout=(5, 10)) #read if door is fully closed
                    successTwo = True
                    # print(response.status_code)
                    responseJSON = xmltodict.parse(response.content)
                    print(responseJSON)
                    DIPinTwo = responseJSON["ADAM-6052"]["DI"]["VALUE"]
                except Exception as err:
                    print(f"{err}")
                    print("error for restful call 2")

                door_mode = 0

                if (successOne and successTwo):
                    print("DPInOne = " + DIPinOne)
                    print("DPInTwo = " + DIPinTwo)
                    if (DIPinOne == "1"):
                        door_mode = 2  # door is fully open
                    elif (DIPinTwo == "1"):
                        door_mode = 0  # door is fully closed
                    else:
                        door_mode = 1  # door is moving
                else:
                    door_mode = 3

                data = {
                    "door_name": door,
                    "current_mode": door_mode
                }
                print(data)
            start = time.time()
            i += 1
            # print(i)

            try:
                publish_future, packet_id = mqtt_connect.publish(
                    topic=(config_file["mqtt"]["topic"] +
                           door + "/data"),
                    payload=json.dumps(data),
                    qos=mqtt.QoS.AT_LEAST_ONCE,
                )
                print("published to topic " + config_file["mqtt"]["topic"] +
                      door + "/data")
            except (KeyboardInterrupt, SystemExit):
                print("\nkeyboardinterrupt caught (again)")
                print("\n...Program Stopped Manually!")
                raise
            except Exception as err:
                print(f"{err}")
                print("error for mqtt publish")


def command_subscriber(mqtt_connect, rest_session, config_file):
    global mqtt_response
    mqtt_response = {}

    def on_message_received(topic, payload, dup, qos, retain, **kwargs):
        global mqtt_response
        mqtt_response = json.loads(payload)
        return mqtt_response

    while (True):
        for door in config_file["doors"]:
            time.sleep(1)
            try:
                subscribe_future, packet_id = mqtt_connect.subscribe(
                    topic=config_file["mqtt"]["topic"] + door + "/command",
                    qos=mqtt.QoS.AT_LEAST_ONCE,
                    callback=on_message_received,
                )
                print(mqtt_response)
                # res = json.loads(mqtt_response)
                if (mqtt_response == {}):
                    print("empty")
                    rest_session.post(
                        config_file["doors"][door]+"/digitaloutput/all/value", timeout=10, data="DO1=0")
                elif (mqtt_response["requested_mode"] == "2"):
                    rest_resp = rest_session.post(
                        config_file["doors"][door]+"/digitaloutput/all/value", timeout=10, data="DO1=0")
                    print(rest_resp)
                    time.sleep(2.5)
                    rest_resp = rest_session.post(
                        config_file["doors"][door]+"/digitaloutput/all/value", timeout=10, data="DO1=1")
                    print(rest_resp)
                    time.sleep(2.5)
                    rest_resp = rest_session.post(
                        config_file["doors"][door]+"/digitaloutput/all/value", timeout=10, data="DO1=0")
                    print(rest_resp)
                    print("door opened")
                else:
                    rest_resp = rest_session.post(
                        config_file["doors"][door]+"/digitaloutput/all/value", timeout=10, data="DO1=0")
                    print("door closed")
                    print(rest_resp)
                    mqtt_response = {}

            except (KeyboardInterrupt, SystemExit):
                print("\nkeyboardinterrupt caught (again)")
                print("\n...Program Stopped Manually!")
                raise

            except Exception as err:
                print(f"{err}")
                print("error for mqtt subscribe")


if __name__ == "__main__":

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

    session = requests.Session()
    session.auth = ("root", "00000000")
    # creating thread
    t1 = threading.Thread(target=status_publisher, args=(mqtt_connection, session, config))
    t2 = threading.Thread(target=command_subscriber, args=(mqtt_connection, session, config))

    # starting thread 1
    t1.start()
    # starting thread 2
    t2.start()

    # wait until thread 1 is completely executed
    t1.join()
    # wait until thread 2 is completely executed
    t2.join()

    # both threads completely executed
    print("Done!")
