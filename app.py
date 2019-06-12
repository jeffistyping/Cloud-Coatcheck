# -*- coding: utf-8 -*-
"""Flask Web Server for CoatCheck

This module is the main server for operating the Coatcheck service. 
It hands user requests via a RESTful service and is connected to the main
persistent database for stock and user data

"""


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
from appconfig import TwilioConfig, PayloadConfig, DBConfig, SessionConfig
from datetime import datetime as dt
import math

'''
Environment Setup
'''

user, pwrd, location = DBConfig()
_,_, entry = PayloadConfig()

uri = 'mongodb://' + user + ':' + pwrd + location
client = MongoClient(uri, connectTimeoutMS=30000)
db = client.get_database("coatcheck")
jacket = db.jacket

app = Flask(__name__)
app.secret_key = SessionConfig()
CORS(app)

'''
Database Access Utilities
'''
def getUser(name):
	record = jacket.find_one({'name': name})
	return record

def addUser(username, size,item):
	'''
	Params: Username, size, item
	Function: Adds new user to database if not exist
	Returns: Boolean if user is added
	'''
	if getUser(username) is None:
	    record = {
	    	'name': username,
	    	'size': size,
	    	'notified': False,
			'item': item
	    }
	    jacket.insert_one(record)
	    return True
	return False

def humanTime(sizes,lastStockDict):
	'''
	Params: Last Stock Time, Sizes
	Function: Output relative time in natural language
	Returns: Dictionary of relative time mapped to product
	'''
	now = dt.now()
	humanOutput = {}
	for size in sizes:
		if lastStockDict[size] != "No Data":
			delta = now - dt.strptime(lastStockDict[size],"%Y-%m-%d %H:%M:%S.%f")
			totalTime = delta.total_seconds()
			if totalTime/ 31622400 > 1:
				humanOutput[size] = str(int(math.floor(totalTime/31622400))) + " year(s) ago"
			elif totalTime/31622400 == 1:
				humanOutput[size] = "1 year ago"
			elif totalTime/604800 > 1:
				humanOutput[size] = str(int(math.floor(totalTime/604800))) + " weeks ago"
			elif totalTime/604800 == 1:
				humanOutput[size] = "1 week ago"
			elif totalTime/86400 > 1:
				humanOutput[size] = str(int(math.floor(totalTime/86400))) + " days ago"
			elif totalTime/86400 == 1:
				humanOutput[size] = "1 day ago"
			elif totalTime/3600 > 1:
				humanOutput[size] = str(int(math.floor(totalTime/3600))) + " hours ago"
			elif totalTime/3600 == 1:
				humanOutput[size] = "1 hour ago"
			elif totalTime/60 > 1:
				humanOutput[size] = str(int(math.floor(totalTime/3600))) + " minutes ago"
			elif totalTime/60 == 1:
				humanOutput[size] = "1 minute ago"
			else:
				humanOutput[size] = "In Stock Now"
		else:
			humanOutput[size] = "No Data"	
	return humanOutput


'''
Routing
'''

@app.route('/')
def index():
	'''
	get: renders home page
	'''
	return render_template("index.html")

@app.route('/mens_corp', methods=['GET','POST'])
def mens_corp():
	'''
	get: renders live tracking page for men's corps jacket
	post: submit name for men's corps jacket notification list 
	'''
	record = jacket.find_one({'name':"stock"})
	output = record["mens_corps_stock"]
	sizes = ['s','m','l','xl','xxl','3xl']
	options = humanTime(sizes,output)
	if request.method == "POST":
		if request.form['password'] == entry:
			if getUser("+1"+ request.form["name"]) == None:
				addUser("+1" + request.form['name'],request.form['size'],"mens_corps")
				flash("You're on the list. We'll let you know!", "success")
			else:
				flash("Wow! We like you too, but it looks like you've already signed up. We'll keep you posted!", "success")
		else:
			flash("Yikes! Check your contact information or secret password", "danger")
	return render_template("corps.html", options=options, postname="mens_corp", itemname="Men's Corps Jacket", sizes=sizes)

@app.route('/womens_corp', methods=['GET','POST'])
def womens_corp():
	'''
	get: renders live tracking page for women's corps jacket
	post: submit name for women's corps jacket notification list 
	'''
	record = jacket.find_one({'name':"stock"})
	output = record["womens_corps_stock"]
	sizes = ['xs','s','m','l','xl','xxl']
	options = humanTime(sizes,output)
	if request.method == "POST":
		if request.form['password'] == entry:
			if getUser("+1"+ request.form["name"]) == None:
				addUser("+1" + request.form['name'],request.form['size'],"womens_corps")
				flash("You're on the list. We'll let you know!", "success")
			else:
				flash("Wow! We like you too, but it looks like you've already signed up. We'll keep you posted!", "success")
		else:
			flash("Yikes! Check your contact information or secret password", "danger")
	return render_template("corps.html", options=options, postname="womens_corp", itemname="Women's Corps Jacket", sizes=sizes)


@app.route('/sms',methods=['POST'])
def sms():
	'''
	post: Adds users to the appropriate notification lists from mobile text through Twilio API
	'''
	number = request.form['From']
	message_body = request.form['Body']
	resp = MessagingResponse()

	if "serverstatus" in message_body.lower():
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

@app.errorhandler(500)
def server_error(e):
    logging.exception('An error occurred during a request.')
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0')
