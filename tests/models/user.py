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
    schema_name = "users"
    
    id = None
    name = None
    username = None
    role = None

    def __init__(self, **kwargs):
        self.schema = {
            "name": {
                "type": Types.String,
                "required": True
            },
            "username": {
                "type": Types.String,
                "required": True
            },
            "role" : {
                "type": Types.ObjectId,
                "ref": "roles"
            }
        }

        super().__init__(self.schema_name, self.schema, kwargs)

    def __str__(self):
        return f"User: {self.name}, Password: {self.username}"