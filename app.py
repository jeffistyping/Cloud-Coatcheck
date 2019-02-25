from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from pymongo import MongoClient
import os
import logging
import requests
import pymongo
import json
from appconfig import TwilioConfig, PayloadConfig, DBConfig

'''
Environment Setup
'''
user, pwrd, location = DBConfig()
payload, entry = PayloadConfig()

#tw_client = Client(acc_sid,auth_t)
uri = 'mongodb://' + user + ':' + pwrd + location
client = MongoClient(uri, connectTimeoutMS=30000)
db = client.get_database("coatcheck")
jacket = db.jacket

app = Flask(__name__)
CORS(app)

'''
Database Access Utilities
'''
def getUser(name):
	record = jacket.find_one({'name': name})
	return record

def addUser(username, size):
	if getUser(username) is None:
	    record = {
	    	'name': username,
	    	'size': size,
	    	'notified': False
	    }
	    jacket.insert_one(record)
	    return True
	return False

def remUser(username):
    record = getUser(username)
    if record is not None:
    	jacket.delete_one(record)
    	return True
    return False

'''
Routing
'''
@app.route('/')
def index():
	return render_template("index.html")

@app.route('/corp')
def corpsjacket():
	return render_template("corps.html")

@app.route('/register', methods=['POST'])
def register():
	if request.form['Password'] == entry:
		addUser(request.form['Phone'],request.form['Size'])
		return "Hold Tight, we'll let you know when it comes in stock!"
	return "Check the form and try again"

# @app.route('/addMe',methods=['POST'])
# def sms():
# 	number = request.form['From']
# 	message_body = request.form['Body']
# 	resp = MessagingResponse()
# 	if entry in message_body.lower():
# 		size = message_body.split(' ')[1].lower() in ['s','m','l','xl','xxl']
# 		if size and addUser(number,message_body.split(' ')[1].lower()):
# 			resp.message("Alright, I gotchu. You're in")
# 		else: 
# 			resp.message("Looks like you're already on the list")
# 	elif "serverstatus" in message_body.lower():
#             resp.message("Server Health: Good")

# 	else:
# 		resp.message("Invalid")
# 	return str(resp)






@app.route('/sms',methods=['POST'])
def sms():
	number = request.form['From']
	message_body = request.form['Body']
	resp = MessagingResponse()
	if entry in message_body.lower():
		size = message_body.split(' ')[1].lower() in ['s','m','l','xl','xxl']
		if size and addUser(number,message_body.split(' ')[1].lower()):
			resp.message("Alright, I gotchu. You're in")
		else: 
			resp.message("Looks like you're already on the list")
	elif "serverstatus" in message_body.lower():
            resp.message("Server Health: Good")

	else:
		resp.message("Invalid")
	return str(resp)

@app.errorhandler(500)
def server_error(e):
    logging.exception('An error occurred during a request.')
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0')
