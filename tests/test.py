import os, traceback
import signal 
from pymongo import MongoClient
from pymongoose.methods import set_schemas, get_cursor_length
from models.user import User
from models.role import Role


MONGO_URI = os.environ.get("MONGO_URI")

mongo_db = None
users = []
role = None

def mongo_init ():
    global mongo_db

    client = MongoClient(MONGO_URI)
    db = client.test
    try:

        schemas = {
            "users": User(empty=True).schema,
            "roles": Role(empty=True).schema
        }

        set_schemas(db, schemas)
        print("MongoDB Connected!")
    except:
        traceback.print_exc()
        print("Error initializing database")
        raise Exception("Error initializing database")

    return 0

def test_insert():
    global users
    global role

    mongo_init()
    try:
        role = Role(
            name="common",
            actions=["Insert", "Delete", "Update"]
        )
        role_id = role.save()
    except:
        traceback.print_exc()
        raise Exception("Role insertion failed")


    try:
        userA = User(
            name="TestA",
            username="test",
            role=role_id
        )


        userB = User(
            name="TestB",
            username="test",
            role=role_id
        )

        userA.save()
        userB.save()

        users.append(userA)
        users.append(userB)
        print("Insert exit with code 0")
        return 0
    except:
        traceback.print_exc()
        raise Exception("Users insertion failed")

def test_find():
    mongo_init()
    try:
        users = User.find({})
        if users is None or users.count() == 0:
            return 1

        print("Find exit with code 0")
        return 0

    except:
        traceback.print_exc()
        raise Exception("Error initializing database")
        return 1

def test_find_sort():
    mongo_init()
    try:
        users = User.find({}, sort={"name": -1})
        print(users.count())
        if users is None or users.count() == 0:
            return 1

        print("Find sorted exit with code 0")
        return 0

    except:
        traceback.print_exc()
        raise Exception("Error initializing database")
        return 1

def test_count():
    mongo_init()
    try:
        user_count = User.count({})
        if user_count != -1:
            return 0
        else: 
            raise Exception("No users were count")
    except:
        raise Exception("Error counting")

def test_find_by_id():
    mongo_init()
    try:
        user = User.find_by_id(users[0].id)

        if user is None:
            raise Exception("No user was found!")
            return 1

        print("Find by id exit with code 0")
        return 0
    except:
        raise Exception("Error finding")
        return 1

def test_find_one():
    mongo_init()
    try:
        user = User.find({"name": "TestA"}, one=True)
        
        if user is None:
            raise Exception("No one user found")
            return 1
        print("Find one exit with code 0")
        return 0
    except:
        raise Exception("Error finding")
        return 1

def test_update():
    mongo_init()
    try:
        count = User.update({}, {
            "$set": {
                "username": "-test-"
            }
        }, many=True)

        if count == 0:
            raise Exception("No Updates were applied")
            return 1
        print("Update exit with code 0")
        return 0
    except:
        raise Exception("Error updating")
        return 1

def test_update_one():
    mongo_init()
    try:
        count = User.update({"name": "TestA"}, {
            "$set": {
                "name": "Test0"
            }
        })

        if not count == 1:
            raise Exception("No Updates were applied")
            return 1

        print("Update one exit with code 0")
        return 0

    except:
        raise Exception("Error updating one")
        return 1

def test_populate():
    mongo_init()
    try:
        user = User.find({}, populate=["role"])

        if user is None or get_cursor_length(user) == 0:
            raise Exception("No users where returned after populate")
            return 1
        print("find populated exit with code 0")
        return 0
    except:
        raise Exception("Error populating")
        traceback.print_exc()
        return 1

def test_populate_one():
    mongo_init()
    try:
        user = User.find_by_id(users[0].id, populate=["role"])

        if user is None:
            raise Exception("No user was populated")
            return 1
        print("Find one populated exit with code 0")
        return 0
    except:
        raise Exception("Error populating one")
        return 1

def test_delete_one():
    mongo_init()
    try:
        count = Role.delete({"_id": role.id})

        if count == 0:
            raise Exception("No role was deleted")
            return 1
        print("Delete one exit with code 0")
        return 0
    except:
        raise Exception("Error deleting one")
        return 1

def test_delete_many():
    mongo_init()
    try:
        count = User.delete({}, many=True)

        if count == 0:
            raise Exception("No users where deleted")
            return 1
        print("Delete many with code 0")
        return 0
    except:
        raise Exception("Error deleting many")
        traceback.print_exc()
        return 1

# test_insert()
# test_find()
# test_find_sort()
# test_find_by_id()
# test_find_one()
# test_update()
# test_update_one()
# test_populate()
# test_populate_one()
# test_delete_one()
# test_delete_many()