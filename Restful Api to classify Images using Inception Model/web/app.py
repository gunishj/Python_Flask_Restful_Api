from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from pymongo import MongoClient
import bcrypt
import requests
import subprocess #from classify.py
import json
import numpy as np
#from tensorflow.python import *
import tensorflow as tf

app = Flask(__name__)
api = Api(app)

client = MongoClient("mongodb://db:27017")
db = client.ImageClassification
users = db["Users"]


#check if user exist
def UserExist(username):
    #return false if user doesnt exist
    if users.find({"Username":username}).count() == 0:
        return False
    #return true if it does
    else:
        return True

#func for json status code and msg
def getStatusMsg(status, message):
    retJson = {
        "status": status,
        "message": message
    }
    return retJson

#function to verify pwd match with user
def verifyPw(username, password):
    #gets the pwd of the corresponding username and save it as hashed_pw
    hashed_pw = users.find({
        "Username": username
    })[0]["Password"]
    #hashes the given pwd by the user and compares it with the saved hashed pwd. ret true if equal
    if bcrypt.hashpw(password.encode('utf8'), hashed_pw) == hashed_pw:
        return True
    else:
        return False




def verifyLoginDetails(username, password):
    if not UserExist(username):
        return genStatusMsgDict(301, "Username doesnt exist"), True
    correct_pw = verifyPw(username, password)
    if not correct_pw:
        return genStatusMsg(302, "Incorrect password" ), True

    return None, False



#Resources
class Register(Resource):
    def post(self):
        #get data from user
        postedData = request.get_json()
        username = postedData["username"]
        password = postedData["password"]
        #check if user exist
        if UserExist(username):
            return jsonify(getStatusMsg(301, "username already taken"))
            #if user doesnt exist, hash password
        hashedpw = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())
        #insert user in db
        users.insert({
            "Username": username,
            "Password": hashedpw,
            "Tokens": 6
        })
        return jsonify(getStatusMsg(200, "account succesfully created"))

class Classify(Resource):
    def post(self):
        #get data from user
        postedData = request.get_json()
        username = postedData["username"]
        password = postedData["password"]
        #url = image url
        url = postedData["url"]
        #verify logindetails
        retJson, error = verifyLoginDetails(username, password)
        #if true, returns corresponding error message
        if error:
            return jsonify(retJson)
        #get the num of tokens for user
        tokens = users.find({ "Username": username})[0]["Tokens"]
        #check if user has enough tokens
        if tokens<=0:
            return jsonify(getStatusMsg(303, "Insufficient Tokens!"))

        """r = requests.get(url)
        retJson = {}
        with open('temp.jpg', 'wb') as f:
            f.write(r.content)
            proc = subprocess.Popen('python classify_image.py --model_dir=. --image_file=./temp.jpg', stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            ret = proc.communicate()[0]
            proc.wait()
            with open("text.txt") as f:
                retJson = json.load(f)"""
        #if theres enough token get the image from the url given by the user and save it as r
        r = requests.get(url)
        retJson = {}
        #creates and open an empty file temp.jpg and rep it as f (f = temp.jpg)
        with open("temp.jpg", "wb") as f:
            #copy the content of the image gotten from the url into f
            f.write(r.content)
            #create a subprocess with a Popen method that imports the python file 'classify.py',
            #takes the arguments variable(model_dir and image_file) needed to run the process

            proc = subprocess.Popen("python classify_image.py --model_dir=. --image_file=./temp.jpg", stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True )
            # send the communication subprocess request to the image classifier api
            proc.communicate()[0]
            #wait for the process to runs and saves the result of analysing the image in a text.txt(dict) file
            proc.wait()
            #get and assign the text.txt file to g
            with open("text.txt") as g:
                #copy and saves the content of g into retJson
                retJson = json.load(g)

        #subtract one token from users
        users.update({
            "Username": username
        }, {
            "$set": {
                "Tokens": tokens - 1
            }
        })
        return retJson

class Refill(Resource):
    def post(self):
        postedData = request.get_json()
        username = postedData["username"]
        admin_pwd = postedData["admin_pwd"]
        refill_amount = postedData["refill"]


        if not UserExist(username):
            retJson = {
                "status": 301,
                "msg": "Username does not exist"
            }
            return jsonify(retJson)

        correct_pw = "abc123"
        if not admin_pwd == correct_pw:
            return jsonify(getStatusMsg(304, "Invalid Admin Password" ))
        users.update({
                "Username": username },
            {
                    "$set":{
                        "Tokens": refill_amount
                }
            })

        return jsonify(getStatusMsg(200, "Refilled Succesfully"))



api.add_resource(Register, '/register')
api.add_resource(Classify, '/classify')
api.add_resource(Refill, '/refill')


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")

#class Classify(Resource):
    #def post(self):
    #    user
