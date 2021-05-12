import datetime
from pymongoose import methods
from pymongoose.mongo_types import Types, Schema, MongoException, MongoError
from bson import json_util
from bson.objectid import ObjectId

users = None

def user_model_init (db):
   global users
   users = db["users"]

class User(Schema):
    id = None
    name = None
    password = None
    role = None

    def __init__(self, **kwargs):
        self.schema = {
            "name": {
                "type": Types.String,
                "required": True
            },
            "password": {
                "type": Types.String,
                "required": True
            },
            "role" : {
                "type": Types.ObjectId,
                "ref": "roles"
            }
        }

        if not "empty" in kwargs:
            self.id = ObjectId()
            self.name = super().get_default_value("name", kwargs)
            self.password = super().get_default_value("password", kwargs)
            self.role = super().get_default_value("role", kwargs)

        self.iat = 0
        self.items_count = 0

    def __str__(self):
        return f"User: {self.name}, Password: {self.password}"

    def fromJson(self, json_obj):
        self.id = super().extract("_id", json_obj)
        self.name = super().extract("name", json_obj)
        self.password = super().extract("password", json_obj)
        self.role = super().extract("role", json_obj)
        

    def toJson(self, full = True):
        json_obj =  {
            "name": self.name,
            "password": self.password,
            "role": self.role
        }
        if full:
            json_obj["id"] = self.id
        return super().convert_json(json_obj) if full else json_obj


    def save(self, id = None):
        if not super().validate_required(self.toJson(False), super().schema):
            raise MongoException(message="Required fields missing", mongoError=MongoError.Required_field)
        else:
            json_obj = self.toJson(False)
            if id is not None:
                json_obj["_id"] = id

            self.id = users.insert(json_obj)
        return self.id

    @staticmethod
    def exists(query):
        global users
        retval = methods.exists(users, query)
        return retval
    @staticmethod
    def find(query, select = None, populate=None, one=False):
        global users
        retval = methods.find(users, "users", query, select, populate, one)
        if one:
            if retval is not None:
                retval = User.parse(retval)

        return retval

    @staticmethod
    def find_by_id(id, select = None, populate=None):
        global users
        retval = methods.find_by_id(users, "users", id, select, populate)
        if retval is not None:
            retval = User.parse(retval)
        return retval

    @staticmethod
    def update(query, update, many = False):
        global users
        retval = methods.update(users, query, update, many)
        return retval

    @staticmethod
    def delete(query, many = False):
        global users
        retval = methods.delete(users, query, many)
        return retval

    @staticmethod
    def parse(dictionary):
        user = User()
        user.fromJson(dictionary)
        return user