# check.py
import os
from appconfig import TwilioConfig, PayloadConfig, DBConfig
import json
import requests
import pymongo
from pymongo import MongoClient
from twilio.rest import Client
import datetime as dt

acc_sid, auth_t, twil_num = TwilioConfig()
user, pwrd, location = DBConfig()
m_corps, w_corps, entry = PayloadConfig()


tw_client = Client(acc_sid,auth_t)
uri = 'mongodb://' + user + ':' + pwrd + location
client = MongoClient(uri, connectTimeoutMS=30000)
db = client.get_database("coatcheck")
jacket = db.jacket

def sendMessage(twilioclient,msg_body,msg_from,msg_to):
    message = twilioclient.messages.create(body=msg_body,from_=msg_from,to=msg_to)

def updateLastStock(size,item):
	'''
	Params: Size, Item
	Function: Updates the stock of a specified item and size in the database
	Returns: None
	'''
	a = dt.datetime.now()
	record = jacket.find_one({'name':'stock'})
	record[item + '_stock'][size] = str(a)
	jacket.update({'name':'stock'},record)

def notify(size, item):
	luckyOnes = jacket.find({'size': size,'item': item })
	for person in luckyOnes:
		if not person['notified']:
			message = f"Quick! Your jacket is in stock NOW in size: {person['size'].upper()} \
			 \nIf you wish you to be placed back onto the notification list, please reply 'reset'"
			sendMessage(tw_client,message,twil_num,person['name'])
			person['notified'] = True
			jacket.update(	{
							'name': person['name'],
							'size': person['size'],
							'item': item},
							person)

def runner(payload, item):
	'''
	Params: payload API, item of interest
	Function: Interfaces with shop API
	Returns: None
	'''
	res = requests.get(payload).json()
	msg = ""
	print("Item: " + item)
	for sizes in res["Black"]:
		msg += "Size: " + sizes["size"] + "\n" + "Stock: " + ("yes" if sizes["purchasable"] else "no") + "\n"
		if sizes["purchasable"]:
			inStock = sizes["size"].lower()
			notify(inStock,item)
			updateLastStock(inStock,item)

if __name__=="__main__":
	runner(m_corps,'mens_corps')
	runner(w_corps,'womens_corps')

