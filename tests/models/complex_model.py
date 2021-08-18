import datetime
from pymongoose import methods
from pymongoose.mongo_types import Types, Schema, MongoException, MongoError
from bson import json_util
from bson.objectid import ObjectId

class Complex(Schema):
    schema_name = "complexs"
    name= None
    elements = None

    def __init__(self, **kwargs):
        self.schema = {
            "name": {
                "type": Types.String,
                "required": True
            },
            "elements": [
                {
                    "id": {
                        "type": Types.Number
                    },
                    "values": [
                        {
                            "desc": {
                                "type": Types.String,
                                "required": True
                            },
                            "colors": [
                                {
                                    "name": {"type": Types.String},
                                    "code": {
                                        "type": Types.Number,
                                        "required": True
                                    }
                                }
                            ]
                        }
                    ]
                }
            ]
        }

        super().__init__(self.schema_name, self.schema, kwargs)

    def __str__(self):
        return f""