import threading
lock = threading.Lock()
import time
import sys

# need to import the grovepi source code manually and custom module
from dataLoader import groveData
sys.path.append(groveData.init_settings["grove_path"]) 
import grovepi



class Buzzer:
    grove_d = groveData()
    buzzer_settings = grove_d.buzzer_settings

    def __init__(self):
        self.pin = self.buzzer_settings["pin"]
        self.pinMode = self.buzzer_settings["pinMode"]

        
        with lock:
            grovepi.pinMode(self.pin, self.pinMode)

    # Activate the buzzer
    def on(self):
        try:
            with lock:
                grovepi.digitalWrite(self.pin, 1)
        except IOError:
            print ("Buzzer IOError")
            # grovepi.digitalWrite(self.pin, 0)
        except TypeError:
            print ("Buzzer TypeError")
            # grovepi.digitalWrite(self.pin, 0)


    # Deactivate the buzzer
    def off(self):
        try:
            with lock:
                grovepi.digitalWrite(self.pin, 0)
        except IOError:
            print ("Error")
            # grovepi.digitalWrite(self.pin, 0)
        except TypeError:
            print ("Error")
            # grovepi.digitalWrite(self.pin, 0)

    """
    Runs a buzzer tone a certain number of times
    """
    def buzzer_alert(self, runs):
        while runs >= 0:
            # Just some simple buzzer tone
            self.on()
            time.sleep(1)
            self.off()
            
            time.sleep(1)
            
            self.on()
            time.sleep(2)
            self.off()

            time.sleep(1)
            
            runs-=1

if __name__ == "__main__":
    buzzer = Buzzer()
    
    # Just do some basic morse code-esque testing of the basic functions
    while(True):
        try:
            buzzer.on()
            time.sleep(1)
            buzzer.off()
            
            time.sleep(1)
            
            buzzer.on()
            time.sleep(2)
            buzzer.off()

            time.sleep(1)
        except KeyboardInterrupt:
            print("program quit")
            buzzer.off()
            break