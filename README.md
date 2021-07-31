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


class Role(Schema):
    schema_name = "roles" # Name of the schema that mongo uses
    
    # Attributes
    id = None
    name = None
    action = None

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
    from models.role import Role

    MONGO_URI = os.environ.get("MONGO_URI")

    mongo_db = None

    def mongo_init ():
        global mongo_db

        client = MongoClient(MONGO_URI)
        db = client.test
        try:
            schemas = {
                "roles": Role(empty=True).schema
            }

            set_schemas(db, schemas)
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
