import os, traceback
import signal 
from pymongo import MongoClient
from pymongoose.methods import set_schemas, get_cursor_length
from models.user import user_model_init, User
from models.role import role_model_init, Role

MONGO_URI = os.environ.get("MONGO_URI")

mongo_db = None
users = []
role = None

def mongo_init ():
    global mongo_db

    client = MongoClient(MONGO_URI)
    db = client.test
    try:
        user_model_init(db)
        role_model_init(db)

        schemas = {
            "users": User(empty=True).schema,
            "roles": Role(empty=True).schema
        }

        set_schemas(schemas)
        print("MongoDB Connected!")
    except:
        traceback.print_exc()
        print("Error initializing database")
        exit(1)


def test_insert():
    global users
    global role
    try:
        role = Role(
            name="common",
            action=["Insert", "Delete", "Update"]
        )

        role.save()
    except:
        traceback.print_exc()
        return 1


    try:
        userA = User(
            name="TestA",
            password="test",
            role=role.id
        )


        userB = User(
            name="TestB",
            password="test",
            role=role.id
        )

        userA.save()
        userB.save()

        users.append(userA)
        users.append(userB)

        return 0
    except:
        traceback.print_exc()
        return 1

def test_find():
    try:
        users = User.find({})
        if users is None or users.count() == 0:
            return 1
        
        return 0

    except:
        traceback.print_exc()
        return 1

def test_find_by_id():
    try:
        user = User.find_by_id(users[0].id)

        if user is None:
            return 1

        return 0
    except:
        return 1

def test_find_one():
    try:
        user = User.find({"name": "TestA"}, one=True)
        
        if user is None:
            return 1

        return 0
    except:
        return 1

def test_update():
    try:
        count = User.update({}, {
            "$set": {
                "password": "-test-"
            }
        }, many=True)

        if count == 0:
            return 1
        
        return 0
    except:
        return 1

def test_update_one():
    try:
        count = User.update({"name": "TestA"}, {
            "$set": {
                "name": "Test0"
            }
        })

        if not count == 1:
            return 1

        return 0

    except:
        return 1

def test_populate():
    try:
        user = User.find({}, populate=["role"])

        if user is None or get_cursor_length(user) == 0:
            return 1

        return 0
    except:
        traceback.print_exc()
        return 1

def test_populate_one():
    try:
        user = User.find_by_id(users[0].id, populate=["role"])

        if user is None:
            return 1

        return 0
    except:
        return 1

def test_delete_one():
    try:
        count = Role.delete({"_id": role.id})

        if count == 0:
            return 1

        return 0
    except:
        return 1

def test_delete_many():
    try:
        count = User.delete({}, many=True)

        if count == 0:
            return 1

        return 0
    except:
        traceback.print_exc()
        return 1

def test_answer():
    assert test_insert() == 0

if __name__ == "__main__":
    mongo_init()
    
    print("Testing insertion")
    retval = test_insert()
    if retval == 1: exit(retval)    
    print("Testing Find")
    retval = test_find()    
    if retval == 1: exit(retval)    
    print("Testing Find by id")
    retval = test_find_by_id()    
    if retval == 1: exit(retval)    
    print("Testing Find one")
    retval = test_find_one()    
    if retval == 1: exit(retval)    
    print("Testing Update")
    retval = test_update()    
    if retval == 1: exit(retval)    
    print("Testing Update one")
    retval = test_update_one()    
    if retval == 1: exit(retval)    
    print("Testing Populate")
    retval = test_populate()    
    if retval == 1: exit(retval)    
    print("Testing Populate one")
    retval = test_populate_one()    
    if retval == 1: exit(retval)    
    print("Testing Delete one")
    retval = test_delete_one()    
    if retval == 1: exit(retval)    
    print("Testing Delete many")
    retval = test_delete_many()
    if retval == 1: exit(retval)    