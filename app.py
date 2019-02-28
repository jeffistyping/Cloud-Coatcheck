from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from flask import Flask, request, jsonify, render_template, flash
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
app.secret_key = 'some_secret'
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

@app.route('/corp', methods=['GET','POST'])
def corp():
	record = jacket.find_one({'name':"history"})
	output = record["stock"]
	if request.method == "POST":
		if request.form['password'] == entry and len(request.form['name']) == 10 and request.form['name'].isdigit():
			if getUser("+1"+ request.form["name"]) == None:
				addUser("+1" + request.form['name'],request.form['size'])
				flash("You're on the list. We'll let you know!", "success")
			else:
				flash("Wow! We like you too, but it looks like you've already signed up. We'll keep you posted!", "success")
		else:
			flash("Yikes! Check your contact information or secret password", "danger")
	return render_template("corps.html", small=output["s"],med=output["m"],large=output['l'],xl=output['xl'],xxl=output['xxl'],threexl=output['3xl'])



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

        elif "reset" in message_body.lower():
            found = getUser(number)
            if found != None:
                found['notified'] = False
                jacket.update({"name":number},found)
                resp.message("Okay! You're back on the list")
            else:
                resp.message("Can't find you")
        else:
		resp.message("Invalid")
	return str(resp)

@app.route('/justfortest')
def test():
    test_str = '{"Black":[{"color":"Black","name":"Mens Corp Jacket","price":"$120","purchasable":false,"size":"S","sku":"100036703","priority":0},{"color":"Black","name":"Mens Corp Jacket","price":"$120","purchasable":false,"size":"M","sku":"100036702","priority":0},{"color":"Black","name":"Mens Corp Jacket","price":"$120","purchasable":false,"size":"L","sku":"100036701","priority":0},{"color":"Black","name":"Mens Corp Jacket","price":"$120","purchasable":false,"size":"XL","sku":"100036704","priority":0},{"color":"Black","name":"Mens Corp Jacket","price":"$120","purchasable":false,"size":"XXL","sku":"100036705","priority":0},{"color":"Black","name":"Mens Corp Jacket","price":"$120","purchasable":true,"size":"3XL","sku":"100036706","priority":0}]}'
    output = json.loads(test_str)
    return jsonify(output)

@app.errorhandler(500)
def server_error(e):
    logging.exception('An error occurred during a request.')
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0')
