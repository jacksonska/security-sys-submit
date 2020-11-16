import sys
import threading
lock = threading.Lock()
import time

# need to import the grovepi source code manually and custom module
from dataLoader import groveData
sys.path.append(groveData.init_settings["grove_path"]) 
import grovepi


class Detector:
    grove_d = groveData()
    detector_settings = grove_d.detector_settings

    
    # Constructor to just set some variables
    def __init__ (self):
        self.pinMode = self.detector_settings["pinMode"]
        self.pin = self.detector_settings["pin"]
        # Variable to stop the sensing thread, defaults to off
        self.stop_sensing = True
        # Set the necessary grove pinmode
        with lock:
            grovepi.pinMode(self.pin, self.pinMode)

    """
    Function to read the raw value from the grove ultrasonic ranger
    """
    def readVal(self):
        try:
            with lock:
                # Obtain the raw value
                distance = grovepi.ultrasonicRead(self.pin)
                # print ("raw value {}".format(distance))
        except IOError:
            print ("Detector IOError")
            distance = -1
        except TypeError:
            print ("Detector TypeError")
            distance = -1
        return distance
    
    """
    Reads 4 values, and takes their average

    Returns
    avgval - average of the last 4 distance values 
        -> (-1) if 4 values were not read correctly
    """
    def readVal_with_filter(self):
        recents = []
        i = 0 
        while i < 4:
            time.sleep(0.2) 
            recents.append(self.readVal())
            # print(ranger.readVal())
            i+=1
        if len(recents) == 4:
            avgval = sum(recents) / len(recents)
        else:
            avgval = -1
        return avgval

# This was just used for some testing
if __name__ == "__main__":
    ranger = Detector()

    try:
        output = ranger.readVal_with_filter()
        print(output)
        input("press enter to quit")
    except KeyboardInterrupt:
        print("Program Quit")
    