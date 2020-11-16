import json
import sys
sys.path.append("../src/")


from flask import Flask, redirect, url_for, render_template, request, session, flash, jsonify

import paho.mqtt.client as mqtt

# #ignore the error here
from dataLoader import DANGER_THRESHOLD
import serverManager

# I want the server to deal with the username password mishaps, so move user_data here, and 


app = Flask("Controller Server")

# Secret key created for server sessions. Not very secure passphrase,
#  but currently this is only run localhost so not to worry
app.secret_key = "hello world" 

"""
home
    - Displays basic homepage that will redirect to login page
Arguments
    - None
Return
    - renders index.html
"""
@app.route("/")
def home():
    return render_template("index.html")


"""
login
    - displays login prompt and redirects to user page or re-prompts
        if user or password are incorrect
Arguments
    - None
Return
    - Renders login page or redirects to /<usr> page
"""
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Check if the user exists
        user = request.form["nm"] # dictionary key
        password = request.form["pass"]
        user_exist = server_manager.read_password(user, "mqtt")
        
        if user_exist == "NO USER" or password != user_exist:
            # Redirect to the no_user page
            return render_template("no_user.html")
        else:
            # Username and password are correct
            session["user"] = user
            session["password"] = password
            return redirect(url_for("user", usr=session["user"]))
    else:
        # If the user has already logged in, don't send them to login page
        if "user" in session:
            return redirect(url_for("user", usr=session["user"]))
        # Haven't submitted the username yet; display the login request
        return render_template("login.html")
"""
user
    - Displays the main page: the system control page. Handles redirects to some other pages
Arguments
    - usr: Username of the logged in user
    - status: status of sensor nodes. ON or OFF
Return
    - Various possible redirects and webpage templates
"""
@app.route("/<usr>", methods=["GET", "POST"])
def user(usr, status="OFF"):
    # Verify login
    if "user" in session:
        # User is logged in and wants the default page
        user = session["user"]
        
        if request.method == "POST":
            form = request.form
            #status)
            if "ctl_btn" in form:
                if form["ctl_btn"] == "ON":
                    # The button to turn system on was pressed
                    # Publish to the broker to turn on the sensor
                    server_manager.mqtt_publish("ON")
                    return render_template("control.html", username=user, status="ON")
                elif form["ctl_btn"] == "OFF":
                    # The button to turn the system off was pressed
                    return redirect(url_for("userPass", usr=session["user"]))
                    #  return render_template("control.html", username=user, status="OFF")
            elif "idx" in form:
                # Requesting to view a specific data reading
                index = form["idx"]
                if index == "":
                    # Make sure an index was actually input
                    return render_template("control.html", username=user, status=status)
                else:
                    return redirect(url_for("displayReadings", idx=int(index)))
            else:
                return render_template("control.html", username=user, status=status)
        else:
            # GET request was submitted
            return render_template("control.html", username=user, status=status)
    else:
        return redirect(url_for("login"))
"""
userPass
    - Displays a prompt for password re-entry to deactivate the sensor node. 
        Upon correct password entry, the server will publish a message to 
        the sensor node to deactivate
Arguments
    - current_status: current status of the sensor node, defaults to on
Return
    - Either another password prompt, or a redirect to control page
"""
@app.route("/<usr>Pass", methods=["GET", "POST"])
def userPass(usr, current_status="ON"):
    if "user" in session:
        
        if request.method == "GET":
            # They have logged in already, and clicked the off button on the /<usr> page, so just need a password Re-Enter
            return render_template("user_pass.html", username=session["user"], current_status="OFF")

        else:
            # They have re-entered their password and posted a form with their info
            # copied logic from login() to check password
            password = request.form["pass"]
            user_exist = server_manager.read_password(session["user"], "mqtt")
            
            if user_exist == "NO USER" or password != user_exist:
                # Bad password, request for the password again
                return render_template("user_pass.html", username=session["user"])
            else:
                # Username and password are correct, PUBLISH OFF, and redirect to the control page (with option to review most recent results)
                # session["user"] = user
                # session["password"] = password
                # *************PUBLISH TO TURN OFF BUZZER AND SYSTEM
                # Add new page to display the results, or ?
                server_manager.mqtt_publish("OFF")
                return redirect(url_for("user", usr=session["user"], status="OFF"))
    else:
        # User has not logged in already, so they need to in order to access the page
        return redirect(url_for("login"))
"""
sendReadings
    - Acts as a callback, only expected to receieve posts from the RPI. 
        POTNETIAL RISK of program failure if this receives non formatted data
Arguments
    - None
Return
    - The server response code
"""
@app.route("/sendReadings", methods=["POST"])
def sendReading():
    # Extract the sensor reading data
    payload = request.get_json()
    # stor the sensor reading data
    server_manager.add_reading(payload)
    # Send confirmation response to the sender
    response = jsonify({"Response" : "Readings Received"})
    return response
"""
displayReadings
    - Displays the sensors most recent data readings
Arguments
    - None
Return
    - redirect to login page with flashed message notifying successful logout
"""
@app.route("/displayReadings", methods=["GET","POST"])
def displayReadings(idx=None):
    # make sure user has valid login
    if "user" in session:
        if request.method == "GET":
            # No index is input, so show all readings
            recent = server_manager.get_readings()
            # Iterate through the recent data and determine if the alarm was tripped based on sensor values
            for readings in recent:
                for val in readings["avgs"]:
                    if float(val) > DANGER_THRESHOLD:
                        flash("The alarm was tripped during reading {}'s sensing period".format(readings["id"]))
                        break 
                flash(readings)        
            reformat = {"Requested all Readings" : "Shown above"}
            # Display the results
            return render_template("display.html", username=session["user"], jsonfile=json.dumps(reformat))
        else:
            if "idx" in request.form:
                if request.form["idx"] != "":
                    # Proper index was sent to the page
                    index = int(request.form["idx"])
                    recent = server_manager.get_recent_readings(index)
                    if recent == "Bad index":
                        # check if the index was ok
                        flash("Bad index provided")
                        recent = {}
                        # Display the results, saying index was bad
                        return render_template("display.html", username=session["user"], jsonfile=json.dumps(recent))
                    else:
                        for readings in recent["avgs"]:
                            # Iterate through the readings and check values
                            if float(readings) > DANGER_THRESHOLD:
                                flash("The alarm was tripped during reading {}'s sensing period".format(recent["id"]))
                                break 
                        return render_template("display.html", username=session["user"], jsonfile=json.dumps(recent))
                else:
                    flash("Please enter a valid index")
                    dummy = {}
                    return render_template("display.html", username=session["user"], jsonfile=json.dumps(dummy))
            else:
                # Method was POST, and no index was provided to redirect to control page
                return redirect(url_for("user", usr=session["user"]))
    else:
        # The user is not logged into the session
        return redirect(url_for("login"))
"""
removeReadings
    - Webpage for deleting all sensing data stored on the server
        NOTE: Accepts GET and POST http methods
Arguments
    - None
Return
    - Webpage for removing readings or a redirect to another page
"""
@app.route("/removeReadings", methods=["GET", "POST"])
def removeReadings():
    if "user" in session:
        # Logged in user wants to delete all of the user data
        if request.method == "GET":
            # Display initial page
            return render_template("remove_readings.html", username=session["user"])
        else:
            # method == POST
            # Determine which button they pushed
            if request.form["bttn"] == "Return to User Page":
                return redirect(url_for("user", usr=session["user"]))
            else:
                if len(server_manager.readings) == 0:
                    # the db was already cleared
                    flash("The Readings data is already cleared!","info")
                else:
                    # The DB has yet to be cleared so do it
                    flash("Successfully cleared server data.", "info")
                    server_manager.readings = []
                    server_manager._clear_DB()
                
                return render_template("remove_readings.html", username=session["user"])
    else:
        # Not logged in so make them login
        return redirect(url_for("login"))
"""
logout
    - Logs out the user of the current session. Just pop their session data.
Arguments
    - None
Return
    - redirect to login page with flashed message notifying successful logout
"""
@app.route("/logout")
def logout():
    name = session["user"]
    session.pop("user", None)
    session.pop("pass", None)

    flash(f"{name} has been succcessfully logged out")
    return redirect(url_for("login"))



if __name__ == "__main__":
    server_manager = serverManager.serverManager()
    
    app.run(debug=False, host="0.0.0.0", port=5000)