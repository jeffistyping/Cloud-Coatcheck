# check.py
import os
from appconfig import TwilioConfig, PayloadConfig, DBConfig
import json
import requests
import pymongo
from pymongo import MongoClient
from twilio.rest import Client


acc_sid, auth_t, twil_num = TwilioConfig()
user, pwrd, location = DBConfig()
payload, entry = PayloadConfig()


tw_client = Client(acc_sid,auth_t)
uri = 'mongodb://' + user + ':' + pwrd + location
client = MongoClient(uri, connectTimeoutMS=30000)
db = client.get_database("coatcheck")
jacket = db.jacket

def sendMessage(twilioclient,msg_body,msg_from,msg_to):
    message = twilioclient.messages.create(body=msg_body,from_=msg_from,to=msg_to)

def notify(size):
	luckyOnes = jacket.find({'size': size})
	for person in luckyOnes:
		if not person['notified']:
			message = "Quick! Your jacket is in stock NOW in size: " + person['size'].upper()
			sendMessage(tw_client,message,twil_num,person['name'])
			jacket.update(	{
							'name': person['name']
							}, 
							{
								'name': person['name'],
	    						'size': person['size'],
								'notified': True
							})

def runner():
	res = requests.get(payload).json()
	msg = ""
	for sizes in res["Black"]:
		msg += "Size: " + sizes["size"] + "\n" + "Stock: " + ("yes" if sizes["purchasable"] else "no") + "\n"
		if sizes["purchasable"]:
			notify(sizes["purchasable"])
	print(msg)

if __name__=="__main__":
	runner()	