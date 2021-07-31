import datetime
from pymongoose import methods
from pymongoose.mongo_types import Types, Schema, MongoException, MongoError
from bson import json_util
from bson.objectid import ObjectId


class Role(Schema):
    id = None
    name = None
    action = None
    schema_name = "roles"

    def __init__(self, **kwargs):
        self.schema = {
            "name": {
                "type": Types.String,
                "required": True
            },
            "actions": [{
                "type": Types.String,
                "required": True
            }]
        }

        super().__init__(self.schema_name, self.schema, kwargs)


    def __str__(self):
        return f"Role: {self.name}, Actions: {self.action}"