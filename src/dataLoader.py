import json
import sys
# If avg sensor value is greater than 6, alarm should be tripped
DANGER_THRESHOLD = 6.0
"""
The ultrasonic ranger is plugged into grove shield port D6 
    - TO UPDATE CHANGE VALUE IN `groveData.detector_settings["pin"]`

The buzzer is plugged into the grove shield port D2
    - TO UPDATE CHANGE VALUE IN `groveData.buzzer_settings["pin"]`
"""


"""
NOTE: Please change the absolute path below grove_data.init_settings["grove_path"] to the path where your grovepi
python code lives
"""
class groveData:
    #General information for any RPI app that uses grove
    init_settings = { "grove_path" : "~/dev/GrovePi-EE250/Software/Python/" }
    
    # Different things the ultrasonic ranger (detector) need to initialize
    detector_settings = { 
        "pinMode" : "INPUT",
        "pin" : 6 # In GROVE PORT D6 - CHANGE IF NEEDED
        }
    
    # The initalization settings the buzzer class needs to initialize 
    buzzer_settings = {
        "pinMode" : "OUTPUT",
        "pin" : 2 # In GROVE PORT D2 - CHANGE IF NEEDED
    }


"""
Usage : server = serverData("admin", "password") where username & password are the
username and password used to login to the respective MQTT broker
"""
class serverData:    
    def __init__(self, user, password):
        self.mqtt = {
            "ip" : "34.228.115.73", # NOTE: NEED TO UPDATE THE MQTT IP EVERYTIME THE AWS instance IS STARTED
            "port" : 1883,
            "user" : user,
            "pass" : password,
            "keepalive" : 60,
            "topics" : {
                "detector_status" : "system/detector/status",
                "buzzer" : "system/sensors/buzzer"
                }
        } 
        self.http = {
            "address" : "54.152.17.53:5000" # NOTE: NEED TO UPDATE THIS IP AND PORT WITH THE IP AND PORT OF YOUR CONTROL NODE
        }