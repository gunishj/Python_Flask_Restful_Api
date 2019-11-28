from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from pymongo import MongoClient
import bcrypt
import spacy

app = Flask(__name__)
api = Api(app)

client = MongoClient("mongodb://db:27017")
db = client.SimilarityDB
users = db["Users"]

def UserExist(username):
    if users.find({"Username":username}).count() == 0:
        return False
    else:
        return True

def VerifyPw(username,password):
    if not UserExist(username):
        return False

    hashed_pw = users.find({
        "Username":username
    })[0]["Password"]

    if bcrypt.hashpw(password.encode('utf-8'),hashed_pw) == hashed_pw:
        return True
    else:
        return False


def CountTokens(username):
    tokens = users.find({
        "Username":username
    })[0]["Tokens"]
    return tokens



class Register(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]

        if UserExist(username):
            retJson = {
            "status": 301,
            "message": "Invalid Username"
            }
            return jsonify(retJson)

        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        users.insert({
            "Username": username,
            "Password": hashed_pw,
            "Tokens": 6
        })
        retJson = {
        "status": 200,
        "msg": "You've successfully signed up to the API"
        }
        return jsonify(retJson)

class Detect(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]
        text1 = postedData["text1"]
        text2 = postedData["text2"]

        if not UserExist(username):
            retJson = {
                "status":"301",
                "msg":"Invalid Username"
            }
            return jsonify(retJson)

        correct_pw = VerifyPw(username, password)

        if not correct_pw:
            retJson = {
                "status": 302,
                "msg":"Invalid Password"
            }
            return jsonify(retJson)

        num_tokens = CountTokens(username)

        if num_tokens <= 0:
            retJson = {
                "status": 303,
                "msg": "You're out of tokens, please refill"
            }
            return jsonify(retJson)

        #Calculate the edit distance
        nlp = spacy.load('en_core_web_md')

        text1 = nlp(text1)
        text2 = nlp(text2)

        #ration is a number between 0 and 1 the closer to 1, The more similar text1 and text2 are
        ratio = text1.similarity(text2)
        retJson = {
            "status": 200,
            "similarity":ratio,
            "msg":"similarity score Calculated successfully"
        }

        current_tokens = CountTokens(username)

        users.update({
            "Username":username
        },{
            "$set":{
                    "Tokens":current_tokens-1
            }
        })

        return jsonify(retJson)

class Refill(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["admin_pw"]
        refill_amount = postedData["refill"]

        if not UserExist(username):
            retJson = {
                "status": 301,
                "msg": "Invalid Username"
            }
            return jsonify(retJson)

        correct_pw = "abc123"
        if not password == correct_pw:
            retJson = {
                "status": 304,
                "msg": "Invalid Admin Password"
            }
            return jsonify(retJson)



        users.update({
            "Username": username
        },{
            "$set":{
                "Tokens": refill_amount
            }
        })

        retJson = {
            "status": 200,
            "msg": "Refilled successfully"
        }
        return jsonify(retJson)

api.add_resource(Register,'/register')
api.add_resource(Detect,'/detect')
api.add_resource(Refill,'/refill')

if __name__ == "__main__":
    app.run(host = '0.0.0.0')
