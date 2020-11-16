from datetime import datetime
import pickle
import json
import time
import os
import sys
sys.path.append("../src/")

import paho.mqtt.client as mqtt


#ignore the error here
import dataLoader

"""
NOTE: the functions update_DB, verify_valid_reading, and add_reading are adapted 
from the mailboxManager.py file in lab04 and were not FULLY created by me.
"""

DB_FILE = "readings.pickle"
REQ_FIELDS = ["sensor_name", "avgs"] # gonna be dict like = {"sensor_name" : "ultrasonic", "avgs" : [a,b,c,d]}
class serverManager:

    def __init__(self):
        self.server_info = dataLoader.serverData("jskaaden", "9H$1FcVAmycwtZw1")
        
        self.readings = []

        try:
            with open(DB_FILE, 'rb') as f:
                self.readings = pickle.load(f)
                f.close()
        except FileNotFoundError:
            pass
    
    
    """
    Copied from Lab04 : updates the pickle file which contains the server data
    """
    def _update_DB(self):
        with open(DB_FILE, 'wb') as f:
            pickle.dump(self.readings, f)
            f.close()
    
    """
    get_recent_reading
        - Return the most recent reading values sent from the rpi
    Arguments
        - None
    Return
        - Either "bad index" if user provided index out of range
            OR it will return a list containing the one element 
            of the readings the user wanted
    """
    def get_recent_readings(self, idx):
        if abs(idx) >= len(self.readings):
            return "Bad index"
        else:
            return self.readings[idx]


    """
    get_recent_reading
        - Return the all reading values sent from the rpi
    Arguments
        - None
    Return
        - The list of readings saved by the server
    """
    def get_readings(self):
        return self.readings
    
    
    """
    _clear_DB
        - Delete all readings from the DB file
    Arguments
        - None
    Return
        - None
    """
    def _clear_DB(self):
        try:
            with open(DB_FILE, "wb") as f:
                print("removing file")
                os.remove(DB_FILE)
        except FileNotFoundError:
            pass


    """
    Similar to _mail_format_valid in mailboxManager.py from lab04 : Verifies the formating of a new entry
    """
    def verify_valid_reading(self, entry):
        if isinstance(entry, dict):
            fields = entry.keys()
            if len(fields) == len(REQ_FIELDS):
                for field in REQ_FIELDS:
                    if not field in fields:
                        # The field is not in the required list
                        return False
                # if reached here, everything was valid return true
                return True
            else:
                # Dict does not have enough fields
                return False
        else:
            # Entry is not a dict
            return False

    """
    Similar to add_mail in mailboxManager.py from lab04 : Add a new ultrasonic ranger reading to the server db
    """
    def add_reading(self, new_entry):  
        if self.verify_valid_reading(new_entry):

            if len(self.readings) == 0:
                # Currently no readings, its first set of readings
                pid = 0
            else:
                # Make the new reading's id 1 greater than the most recent
                pid = self.readings[-1]["id"] + 1

            # Assign the id and timestamp for the ultrasonic reading
            new_entry["id"] = pid
            new_entry["time"] = str(datetime.now())
            self.readings.append(new_entry)
            self._update_DB()

    """
    read_password 
        - Function to read in the password of the specified user, and server
    Arguments
        - user: username of the user whose password to fetch
        - password: the user entered "guess" for the respective password
    Returns
        - "NO USER": if the password argument does not match and saved passwords 
            for that user.
        - string of the password of the user that was read in
    """
    def read_password(self, user, server):
        # Open the json file storing the user info for the server
        
        with open("user_data.json", "r") as f:
            user_info = json.loads(f.read())
            
        # Return the specified users password
        if user in user_info[server]:
            return user_info[server][user]
        else:
            return "NO USER"

    """
    Default on connect function that is called when conncting to the mqtt server
    """
    def on_connect(self, client, userdata, flags, rc):
        print("Connected to mqtt broker with status " + str(rc))

    """
    Default on message function that is called when receiving from the mqtt server.
    NOTE: this is never expected to be run
    """
    def on_message(self, client, userdata, message):
        print("default callback function " + message.topic + " \"" 
        + str(message.payload, "utf-8") + "\"")
        print("Please, create a custom callback for this topic: " + message.topic)

    """
    mqtt_publish 
        - Function to quickly connect, publish a message to the ranger's topic and then disconnect
    Arguments
        - payload: The message to send to the MQTT Broker. Should be "ON" or "OFF"
    Return
        - None
    """
    def mqtt_publish(self, payload):
        print(f"publishing {payload} to the mqtt broker")
        
        client = mqtt.Client()
        client.on_message = self.on_message
        client.on_connect = self.on_connect
        client.username_pw_set(username="jskaaden", password=self.server_info.mqtt["pass"])
        client.connect(host=self.server_info.mqtt["ip"], port=self.server_info.mqtt["port"], keepalive=self.server_info.mqtt["keepalive"])
        client.loop_start()

        client.publish(topic=self.server_info.mqtt["topics"]["detector_status"], payload=payload, qos=2)

        client.loop_stop()
        client.disconnect()
"""
Just some code testing the functions defined above
"""
if __name__ == "__main__":
    # server_data = dataLoader.serverData("jskaaden", "9H$1FcVAmycwtZw1")
    tool = serverManager()

    fake = {"sensor_name" : "ultrasonic", "avgs" : [0,1,2,3]}

    tool.add_reading(fake)

    print(tool.readings)

    tool.mqtt_publish("ON")
    time.sleep(1)
    tool.mqtt_publish("OFF")
    