import os, traceback
from pymongo import MongoClient
from pymongoose.methods import set_schemas, get_cursor_length
from pymongoose.methods import AS_DICT, AS_STRING
from models.user import User
from models.complex_model import Complex
from models.role import Role
from pymongo.cursor import Cursor


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
            "roles": Role(empty=True).schema,
            "complexs": Complex(empty=True).schema
        }

        set_schemas(db, schemas)
        print("MongoDB Connected!")
    except:
        traceback.print_exc()
        print("Error initializing database")
        raise Exception("Error initializing database")

    return 0

def cursor_size (cursor: Cursor) -> int:
    if (cursor is None):
        return 0
    else:
        return len (list (cursor))


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
    except:
        traceback.print_exc()
        raise Exception("Users insertion failed")

    try:
        complex = Complex(
            name="Test",
            elements=[
                {
                    "id": 0,
                    "values": [{
                        "desc": "hola12",
                        "colors": [
                            {
                                "name": "Red",
                                "code": 1
                            },
                            {
                                "name": "Green",
                                "code": 2
                            }
                        ]
                    }]
                },
                {
                    "id": 1,
                    "values": [{
                        "desc": "adios12",
                        "colors": [
                            {
                                "name": "Blue",
                                "code": 2
                            }
                        ]
                    }]
                }
            ]
        )

        complex.save()
        print("Insert exit with code 0")
        return 0
    except:
        traceback.print_exc()
        raise Exception ("Complexs insertion failed")

def test_find():
    mongo_init()
    try:
        users = User.find({})
        if users is None or len(list(users)) == 0:
            return 1

        print("Find exit with code 0")
        return 0

    except:
        traceback.print_exc()
        raise Exception("Error initializing database")
        return 1

# def test_find_no_timeout ():
#     mongo_init()
#     try:
#         users = User.find({}, no_cursor_timeout=True)
#         users_len = 0

#         users: Cursor

#         for user in users:
#             users_len += 1

#         users.close ()

#         print ("Closed??")
        
#         if users is None or users_len == 0:
#             return 1

#         print("Find exit with code 0")
#         return 0

#     except:
#         traceback.print_exc()
#         raise Exception("Error initializing database")
#         return 1

def test_find_dict():
    mongo_init()
    try:
        users = User.find({}, cursor=AS_DICT)
        if users is None or type(users) is not list:
            return 1

        print("Error finding as dict")
        return 0

    except:
        traceback.print_exc()
        raise Exception("Error initializing database")
        return 1

def test_find_string():
    mongo_init()
    try:
        users = User.find({}, cursor=AS_STRING)
        if users is None or type(users) is not str:
            print("Error finding as string")
            return 1

        print("Find exit with code 0")
        return 0

    except:
        traceback.print_exc()
        raise Exception("Error initializing database")
        return 1

def test_find_check_none():
    mongo_init()
    try:
        user = User.find({"name": "This_user_doesnt_exists"}, one=True)
        if user is not None:
            return 1

        print("Find check none exit with code 0")
        return 0
    except:
        traceback.print_exc()
        raise Exception("Error initializing database")
        return 1

def test_find_skip():
    mongo_init()
    try:
        users = User.find({}, skip=1)
        if users is None or (cursor_size (users) > 1 and cursor_size (users) == 0):
            return 1

        print("Find skip exit with code 0")
        return 0

    except:
        traceback.print_exc()
        raise Exception("Error initializing database")
        return 1

def test_find_limit():
    mongo_init()
    try:
        users = User.find({}, limit=1)
        if users is None or (cursor_size (users) > 1 and cursor_size (users) == 0):
            return 1

        print("Find limit exit with code 0")
        return 0

    except:
        traceback.print_exc()
        raise Exception("Error initializing database")
        return 1

def test_find_sort():
    mongo_init()
    try:
        users = User.find({}, sort={"name": -1})
        if users is None or cursor_size (users) == 0:
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

def test_find_by_id_dict():
    mongo_init()
    try:
        user = User.find_by_id(users[0].id, cursor=AS_DICT, parse=False)
        if user is None or type(user) is not dict:
            raise Exception("No user was found!")
            return 1

        print("Find by id exit with code 0")
        return 0
    except:
        raise Exception("Error finding as dict")
        return 1

def test_find_by_id_string():
    mongo_init()
    try:
        user = User.find_by_id(users[0].id, cursor=AS_STRING, parse=False)
        if user is None or type(user) is not str:
            raise Exception("No user was found!")
            return 1

        print("Find by id exit with code 0")
        return 0
    except:
        raise Exception("Error finding as string")
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

def test_find_one_dict():
    mongo_init()
    try:
        user = User.find({"name": "TestA"}, one=True, parse=False, cursor=AS_DICT)
        
        if user is None or type(user) is not dict:
            raise Exception("No one user found")
            return 1
        print("Find one exit with code 0")
        return 0
    except:
        raise Exception("Error finding")
        return 1

def test_find_one_string():
    mongo_init()
    try:
        user = User.find({"name": "TestA"}, one=True, parse=False, cursor=AS_STRING)
        
        if user is None or type(user) is not str:
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

def test_populate_dict():
    mongo_init()
    try:
        user = User.find({}, populate=["role"], cursor=AS_DICT)

        if user is None or type(user) is not list:
            raise Exception("No users where returned after populate")
            return 1
        print("find populated exit with code 0")
        return 0
    except:
        raise Exception("Error populating dict")
        traceback.print_exc()
        return 1

def test_populate_string():
    mongo_init()
    try:
        user = User.find({}, populate=["role"], cursor=AS_STRING)

        if user is None or type(user) is not str:
            raise Exception("No users where returned after populate")
            return 1
        print("find populated exit with code 0")
        return 0
    except:
        raise Exception("Error populating string")
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

def test_populate_with_match():
    mongo_init()
    try:
        user = User.find_by_id(users[0].id, populate=[{
            "path": "role",
            "match": {"name": "common"}
        }])

        if user is None:
            raise Exception("No user was populated")
            return 1
        print("Find one populated exit with code 0")
        return 0
    except:
        raise Exception("Error populating one with match")
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
# test_find_no_timeout ()
# test_find_dict()
# test_find_string()
# test_find_sort()
# test_find_by_id()
# test_find_by_id_dict()
# test_find_by_id_string()
# test_find_one()
# test_find_one_dict()
# test_find_one_string()
# test_find_check_none()
# test_find_skip()
# test_find_limit()
# test_populate_with_match()
# test_update()
# test_update_one()
# test_populate()
# test_populate_dict()
# test_populate_string()
# test_populate_one()
# test_delete_one()
# test_delete_many()