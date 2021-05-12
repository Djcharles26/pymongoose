import datetime
from pymongoose import methods
from pymongoose.mongo_types import Types, Schema, MongoException, MongoError
from bson import json_util
from bson.objectid import ObjectId

roles = None

def role_model_init (db):
   global roles
   roles = db["roles"]

class Role(Schema):
    id = None
    name = None
    action = None

    def __init__(self, **kwargs):
        self.schema = {
            "name": {
                "type": Types.String,
                "required": True
            },
            "action": {
                "type": Types.String,
                "required": True
            }
        }

        if not "empty" in kwargs:
            self.id = ObjectId()
            self.name = super().get_default_value("name", kwargs)
            self.action = super().get_default_value("action", kwargs)

        self.iat = 0
        self.items_count = 0

    def __str__(self):
        return f"Role: {self.name}, Password: {self.action}"

    def fromJson(self, json_obj):
        self.id = super().extract("_id", json_obj)
        self.name = super().extract("name", json_obj)
        self.action = super().extract("action", json_obj)
        

    def toJson(self, full = True):
        json_obj =  {
            "name": self.name,
            "action": self.action
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

            self.id = roles.insert(json_obj)
        return self.id

    @staticmethod
    def exists(query):
        global roles
        retval = methods.exists(roles, query)
        return retval
    @staticmethod
    def find(query, select = None, populate=None, one=False):
        global roles
        retval = methods.find(roles, Role.schema, query, select, populate, one)
        if one:
            retval = Role.parse(retval)
        return retval

    @staticmethod
    def find_by_id(id, select = None, populate=None, one=False):
        global roles
        retval = methods.find_by_id(roles, Role.schema, id, select, populate)
        return Role.parse(retval)

    @staticmethod
    def update(query, update, many = False):
        global roles
        retval = methods.update(roles, query, update, many)
        return retval

    @staticmethod
    def delete(query, many = False):
        global roles
        retval = methods.delete(roles, query, many)
        return retval

    @staticmethod
    def parse(dictionary):
        role = Role()
        role.fromJson(dictionary)
        return role