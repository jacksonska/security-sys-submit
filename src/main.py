import json
import requests
import threading
import time
from pprint import pprint

import paho.mqtt.client as mqtt

from dataLoader import serverData, DANGER_THRESHOLD
from detector import Detector
from buzzer import Buzzer
buzzer = Buzzer()
detector = Detector()


lock = threading.Lock()
readings = []


def detector_callback(client, userdata, message):
    print("detector_callback: " + message.topic + " " + "\"" + 
        str(message.payload, "utf-8") + "\"")
    
    with lock:
        if str(message.payload, "utf-8") == "ON":
            # Set the internal flag to start the detector
            print("starting the sensor")
            detector.stop_sensing = False
        elif str(message.payload, "utf-8") == "OFF":
            
            # Set the detector's internal flag to stop sensing
            detector.stop_sensing = True
            print("stopping the sensing & sending data to server")
            # Turn off the buzzer, because OFF message is only sent when the user on the site
            # Tells the server to turn of the system
            buzzer.off()
            # Send an HTTP post to the HTTP server for storage
            send_readings(server_data.http["address"], "ultrasonic", readings)
            # Reset the readings for the next batch
            readings.clear()

def buzzer_callback(client, userdata, message):
    print("detector_callback: " + message.topic + " " + "\"" + 
        str(message.payload, "utf-8") + "\"")
    pl = str(message.payload, "utf-8")
    if pl == "ON":
        # Activate the buzzer
        buzzer.on()
        # When the buzzer is on the sensor should be off, tell the internal flag
        detector.stop_sensing = True
    if pl == "OFF":
        # Activate the buzzer
        buzzer.off()

def on_connect(client, userdata, flags, rc):
    print("Connected to mqtt broker with status " + str(rc))

    # Subscribe to the status of the deteector: Whether or not the sensor should be publishing.. 
    client.subscribe(server_data.mqtt["topics"]["detector_status"], qos=2)
    client.message_callback_add(sub=server_data.mqtt["topics"]["detector_status"], callback=detector_callback)
    
    # Subscribe to the buzzer's state: ON or OFF
    client.subscribe(server_data.mqtt["topics"]["buzzer"], qos=2)
    client.message_callback_add(sub=server_data.mqtt["topics"]["buzzer"], callback=buzzer_callback)

#Default message callback. Please use custom callbacks.
def on_message(client, userdata, message):
    print("default callback function " + message.topic + " \"" 
    + str(message.payload, "utf-8") + "\"")
    print("Please, create a custom callback for this topic: " + message.topic)


def send_readings(address, sensor_name, avgs):
    # HTTP POST request, Content-Type tells how the data will be formatted
    headers = {
        "Content-Type" : "application/json",
        "Authorization" : "Basic admin:password"
    }

    payload = {
        "sensor_name" : sensor_name,
        "avgs" : avgs
    }

    # Send a POST with the content to the HTTP server
    response = requests.post(f"http://{address}/sendReadings",
        headers=headers,
        data=json.dumps(payload))

    pprint(f"http server response: {response}" )

if __name__ == "__main__":
    
    # Usage : serverData(username, password) for the username and password used to login to the MQTT Broker
    server_data = serverData("jskaaden", "9H$1FcVAmycwtZw1") 
    
    try:
        client = mqtt.Client()
        client.on_message = on_message
        client.on_connect = on_connect
        client.username_pw_set(username="jskaaden", password=server_data.mqtt["pass"])
        client.connect(host=server_data.mqtt["ip"], port=server_data.mqtt["port"], keepalive=server_data.mqtt["keepalive"])
        client.loop_start()
    
        while(True):
            # Do the RPI sensing contiuously
            time.sleep(0.83) # Needs to be longer than it takes to read the values with filtering (8ms)

            with lock:
                # simple logic for whether or not to publish a value
                if detector.stop_sensing == True:
                    print("not sensing")
                    time.sleep(0.1)
                    continue
                else:
                    print("Im sensing!")
                    # Get the filtered sensor input
                    out = detector.readVal_with_filter()
                    if out != -1:
                        # If the result code indicates success
                        print(out)
                        if out > DANGER_THRESHOLD:
                            # The alarm is triggered
                            print("danger")
                            buzzer.on()
                        # Verify one more time that the flag wasn't tripped while doing this computation and publish the raw value
                        if detector.stop_sensing != True:
                            readings.append(out) # add reading to list of readings

    except KeyboardInterrupt:
        # Catch and make sure the program exits nicely
        print("\n")
        print("Disconnecting...")
        buzzer.off() # Just make sure not to leave the buzzer on ;)
        client.disconnect()


    
        