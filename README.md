# Pymongoose

This is a pymongo helper package, that let you make more complicated actions with your collections.
It gives you the possibility to populate between packages without needs of creating an aggregation by yourself.
Gives you the basic actions such as find, update and delete, with more simplicity.

Pymongoose came with a Schema class that let you work with more efficiency and organization

# First Steps

```bash
pip install pymongoose pymongo
```

## Create a model:

models/role.py

```python
import datetime
from pymongoose import methods
from pymongoose.mongo_types import Types, Schema, MongoException, MongoError
from bson import json_util
from bson.objectid import ObjectId

roles = None

#Required function
def role_model_init (db):
   global roles
   roles = db["roles"]

class Role(Schema):
    #Global variables of the model
    id = None
    name = None
    action = None

    def __init__(self, **kwargs):
        #Schema of the model
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

        #Declaration of fields when a Model Object is created
        if not "empty" in kwargs:
            self.id = ObjectId()
            self.name = super().get_default_value("name", kwargs)
            self.action = super().get_default_value("action", kwargs)

        self.iat = 0
        self.items_count = 0

    def __str__(self):
        return f"Role: {self.name}, Password: {self.action}"

    ## Required function
    def fromJson(self, json_obj):
        self.id = super().extract("_id", json_obj)
        self.name = super().extract("name", json_obj)
        self.action = super().extract("action", json_obj)
        
    ## Required function
    def toJson(self, full = True):
        json_obj =  {
            "name": self.name,
            "action": self.action
        }
        if full:
            json_obj["id"] = self.id
        return super().convert_json(json_obj) if full else json_obj

    ## Required function
    def save(self, id = None):
        if not super().validate_required(self.toJson(False), super().schema):
            raise MongoException(message="Required fields missing", mongoError=MongoError.Required_field)
        else:
            json_obj = self.toJson(False)
            if id is not None:
                json_obj["_id"] = id

            self.id = roles.insert(json_obj)
        return self.id

    ## Required function
    @staticmethod
    def exists(query):
        global roles
        retval = methods.exists(roles, query)
        return retval
    
    ## Required function
    @staticmethod
    def find(query, select = None, populate=None, one=False):
        global roles
        retval = methods.find(roles, Role.schema, query, select, populate, one)
        if one:
            retval = Role.parse(retval)
        return retval

    ## Required function
    @staticmethod
    def find_by_id(id, select = None, populate=None, one=False):
        global roles
        retval = methods.find_by_id(roles, Role.schema, id, select, populate)
        return Role.parse(retval)

    ## Required function
    @staticmethod
    def update(query, update, many = False):
        global roles
        retval = methods.update(roles, query, update, many)
        return retval

    ## Required function
    @staticmethod
    def delete(query, many = False):
        global roles
        retval = methods.delete(roles, query, many)
        return retval

    ## Required function
    @staticmethod
    def parse(dictionary):
        role = Role()
        role.fromJson(dictionary)
        return role
```

**Is higly recommended to follow this model for any schema**

## Mongo Configuration
This mongo configuration is required for pymongoose to work correctly

db.py:
```python
    import os, traceback
    import signal 
    from pymongo import MongoClient
    from pymongoose.methods import set_schemas, get_cursor_length
    from models.role import role_model_init, Role

    MONGO_URI = os.environ.get("MONGO_URI")

    mongo_db = None

    def mongo_init ():
        global mongo_db

        client = MongoClient(MONGO_URI)
        db = client.test
        try:
            role_model_init(db)

            schemas = {
                "roles": Role(empty=True).schema
            }

            set_schemas(schemas)
            print("MongoDB Connected!")
        except:
            traceback.print_exc()
            print("Error initializing database")
            exit(1)

    if __name__ == "__main__":
        mongo_init()
```

## Examples:
- For more model examples check examples/

### Insert function: 

```python
user = User(
    name="TestA",
    password="test",
    role=role.id
)
id = user.save()
```
user.save() will throw an exception if a field marked as required in schema is **None**

### Find function:
```python
users = User.find({})
for user in users:
    user = User.parse(user)
```
This will return a cursor of elements, which can be parsed into User model for a better management

### Find one function:
```python
user = User.find({}, one=True)
```
This will return a User element with fields obtained by database
### Find by id function:
```python
# this Function will search for "_id" field 
# so id must be a hex24 string or ObjectId
user = User.find_by_id(id)
# for a complete user
user = User.find_by_id(id, select={"name": 1, "username": 1})
# For a custom user
```
This will return a User element with fields obtained by database

### Populate a search:
```python
user = User.find_by_id(id, populate=[
    {
        "path": "role",
        "select": ["name", "actions"],
        "options": ["actions"]
    }
])
# For an extensive populate
# or
user = User.find_by_id(id, populate=["role"])
# For a simple populate
```
This will return a User element with fields obtained by database


Populate is a really useful tool when we work with difficult or complex models, with pymongoose you wont need to create an extensive aggregation to lookup for elements.

Populate works with simple ids like:
```python
schema = {
    "name": {
        "type": Types.String,
        "required": True
    },
    "role": { # <- Simple field
        "type": Types.ObjectId,
        "ref": "roles"
    }
}
```
lists: 
```python
schema = {
    "name": {
        "type": Types.String,
        "required": True
    },
    "logs": [{ # <- List field
        "type": Types.ObjectId,
        "ref": "logs"
    }]
}
```
and complex models

```python
schema = {
    "name": {
        "type": Types.String,
        "required": True
    },
    "friends": [{ 
        "friend": {
            "type": Types.ObjectId, # <- Complex list field
            "ref": "friends"
        },
        "frequent": {
            "type": Types.Boolean,
            "default": False
        }
    }]
}
```

Pymongoose can recursively populate fields like this:
```python
    #menu schema:
    menu_schema = {
        # ...
        "items":[
            {
                "type":Types.ObjectId,
                "ref":"items"
            }
        ],
        # ...
    }

    #item schema:
    item_schema: {
        # ...
        "drink":{
            "type":Types.ObjectId,
            "ref":"drinks"
        },
        "dish":{
            "type":Types.ObjectId,
            "ref":"dishes"
        }
        # ...
    }

    #Populate

    menus = Menu.find({}, populate=[{
        "path": "items",
        "options": ["dish", "drink"]
    }])

    for menu in menus:
        print(menu)
```
This will return a CursorCommand element

In this example all menus populate each item of their array, at same time element dish and drink are populated, returning a complete array of populated menus with populated items.

## Update item:
```python
count = User.update({},
            {
                "$set": {
                    "password": "0"
                }
            }, many=True
        ) #many is set to False by default
```

## Delete item:
```python
count = User.delete({}, many=True) #many is set to False by default
```

# Note:
If you are working with vscode I have already created a model snippet to save you a lots of time:
https://github.com/Djcharles26/pymongoose/blob/master/pymongoose-snippets.json

For using this you must copy them to your python snippets:

1. CTRL + SHIFT + P
2. Configure User snippets
3. python.json
4. Copy snippets in blob
5. Paste them in your user python.json
