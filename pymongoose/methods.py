from dataclasses import replace
import sys
from pymongo import DESCENDING, ASCENDING
from pymongo.database import Database
from pymongo.collection import Collection
from bson.objectid import ObjectId
from .mongo_types import *
from pprint import pprint
from pymongoose.logger import Logger
import math

schemas = {}
debug_log = True
database = None

def set_schemas(db: Database, schemas_re: dict, _debug_log_=True):
    """
    ## Description:
    Function to be called were you control your models registration
    # Parameters
    ------------
    - db: Database
    MongoDB connection database
    - schemas_re: dict
    A dictionary with all your registered schemas.
    f.e: {"users": User.schema}
    - _debug_log_: bool
    A variable to set logs on or off
    Default True
    """
    global database
    global schemas
    global debug_log
    database = db
    schemas = schemas_re
    debug_log = _debug_log_
    if debug_log:
        Logger.set_terminal_color("blue")
        print("MongoDB Schemas: ")
        pprint(schemas)
        Logger.set_terminal_color("reset")

def set_schemas_from_list (db: Database, schemas_list: list, _debug_log_=True):
    """
    ## Description:
    Function to be called were you control your models registration as list
    # Parameters
    ------------
    - db: Database
    MongoDB connection database
    - schemas_re: list
    A list with your schemas.
    f.e: [User (empty=True)]
        (User must be Schema subclass)
    - _debug_log_: bool
    A variable to set logs on or off
    Default True
    """
    global database
    global schemas
    global debug_log
    database = db
    schemas = {}
    debug_log = _debug_log_
    for schema in schemas_list:
        schema: Schema
        schemas[schema.schema_name] = schema.schema

    if debug_log:
        Logger.set_terminal_color("blue")
        print("MongoDB Schemas: ")
        pprint(schemas)
        Logger.set_terminal_color("reset")

def get_schema_by_name(name:str) -> dict:
    if name in schemas:
        return schemas[name]
    else: return None

def exists(schema, query):
    """
	Check if document exists in collection
	# Parameters
	------------
	### schema: Mongo collection name
		Mongo collection name where query will be executed
    ### query: dict
        Dictionary containing query
    # Returns
    ------------
    - boolean
	"""
    return database[schema].count_documents(query, limit = 1) > 0

def _get_clean_schema(schema, pop):
    isList = False
    aux_schema = schema.copy()
    pop_list = None
    if pop.find(".") > 0: # If the populate path is a child of another object
        populate_list = pop.replace(" ", "").split(".") ## Split The populate items from pop. g.e user.permissions -> user, permissions
        for pop1 in populate_list:
            if type(aux_schema) is list: # If current schema is list. g.e presets: [{type: Types.ObjectId, default: None}]
                isList = True
                aux_schema = aux_schema[0]

                if (not pop_list):
                    pop_list = pop1 # Save that this current schema is a list

            aux_schema = aux_schema[pop1]
    else:
        aux_schema = aux_schema[pop]
        if type(aux_schema) is list:
            isList = True
            aux_schema = aux_schema [0]
            
            if (not pop_list):
                pop_list = pop

    return aux_schema, isList, pop_list

def _merge_objects(parentRoot, parentAux, acum, popAux):
    if(len(parentAux) > 0):
        p = parentAux.pop(-1)
        return {
            parentRoot: {
                "$mergeObjects": [
                    f"$doc.{acum}", _merge_objects(p, parentAux, acum + "." + p, popAux)
                ]
            }
        }
    else:
        return {popAux: f"${popAux}"}

def _populate(schema, populate, aggregate: list, parent=""):
    wasList = False
    for pop in populate: #Iterate in each populate object or str
        if type(pop) is not dict: #If is a str is a simple lookup and unwind
            aux_schema, isList, pop_list = _get_clean_schema(schema, pop)
            if ("." in pop):
                unwind = {
                    "path": f"${parent + pop_list}",
                    "preserveNullAndEmptyArrays": True
                }
                aggregate.append({"$unwind": unwind})

            e = {
                "$lookup": {
                    "from": aux_schema["ref"],
                    "localField": parent + pop,
                    "foreignField": "_id",
                    "as": parent + pop
                }
            }
            aggregate.append(e)

            if not isList:
                unwind = {
                    "path": f"${parent + pop}",
                    "preserveNullAndEmptyArrays": True
                }
                aggregate.append({"$unwind": unwind})

        else: 
            aux_schema, isList, pop_list = _get_clean_schema(schema, pop["path"])
            
            if isList:  #If is list first unwind path dessired
                aggregate.append(
                    {
                        "$unwind": {
                            "path": f"${parent}{pop['path'] if not pop['path'].find('.') else pop['path'].split('.')[0]}",
                            "preserveNullAndEmptyArrays": True
                        }
                    }
                )
                wasList = True
            ## Add respective pipeline with select and match
            pipeline = [
                {
                    "$match": {
                        "$expr":{
                            "$eq": ["$_id", "$$var"]
                        }
                    }
                },
            ]
            if "select" in pop:
                project = {}
                for s in pop["select"]:
                    project[s]= 1
                
                pipeline.append({"$project": project})

            ## This means two things, The first is that the current path is a dict and contains values to be populated
            ## Or, the schema is not correct
            if ("ref" not in aux_schema):
                if ("options" in pop):
                    _populate (aux_schema, pop["options"], aggregate, pop["path"] + ".")
                else:
                    raise MongoException(
                        message=f"Schema {pop['path']} is not correct, Missing 'ref'"
                    )
            else:
                e = {
                    "$lookup": {
                        "from": aux_schema["ref"],
                        "let": {f"var": f"${parent + pop['path']}"},
                        "pipeline": pipeline,
                        "as": parent + pop["path"]
                    }
                }

                aggregate.append(e)
                #Unwind result
                unwind = {
                    "path": f"${parent + pop['path']}",
                    "preserveNullAndEmptyArrays": True
                }
                aggregate.append({"$unwind": unwind})

                if "match" in pop:
                    aggregate.append({"$match": {f"{parent}{pop['path']}.{k}": v for k, v in pop["match"].items()}})

                wL = False

                if "options" in pop: #If has attached populates
                    
                    ##Recursively call to function with respective schema 

                    wL = _populate(schemas[aux_schema["ref"]], pop["options"], aggregate, parent + pop["path"] + ".") 

                """
                If current isList is true:
                    If parent exists:
                        Current parent should be added in _id 
                    else:
                        _id = "$_id"
                        path: {"$push": "$parent.path"}
                        doc: {"$first": "$$ROOT"}

                    add $replaceRoot with 
                        $_id, 
                        parent: {
                            "$mergeObjects": [
                                "$doc", {"_id": "$_id._id"}, to obtain real _id 
                                {
                                    "$parent": {
                                        "$mergeObjects": ["$parent", {"path": "$path"}]
                                    }
                                }
                            ]
                        }
                """

                # Group and replace to have a correct object
                if isList: 
                    group = {}
                    _id = {}
                    
                    parentAux = parent
                    parentRoot = parentAux

                    # If parent has a dot, remove it and get the parentRoot (The first position)
                    if(parent.find(".") > 0): 
                        parentRoot = parent.split(".")[0]

                    # If parent is not empty it means is required to add in _id each parent participant
                    if len(parent) > 0:
                        parentAux = parent[:-1]

                        _id = {
                            "_id": f"$_id",
                        }

                        # Generate a list of parents splitted by .
                        parents_list = parentAux.split (".")

                        # Lambda to generate the correct format
                        # For key its required to be with _ and for _id value is required a .
                        #e.g
                        # 'components': "$components._id",
                        # 'components_children': '$components.children._id'
                        formatted_parent = lambda c, limit: f"{c}".join (parents_list [0:limit + 1])

                        for i, _ in enumerate(parents_list):
                            idd = "$" + formatted_parent ('.', i) + "._id"
                            _id [formatted_parent ('_', i)] = idd

                    else: 

                        _id = f"$_id"

                    # Group the path (The current populated item) in an array, if path has a dot, it means the populated item is inside an object
                    # Which doesn't care, so its required to take only the first name of the path.
                    """
                        E.g.
                        for the schema: 
                            users: [
                                {
                                    user_id: {
                                        type: Types.ObjectId,
                                        required: True,
                                        ref: "users"
                                    },
                                    count: {
                                        type: Types.Number,
                                        required: True
                                    }
                                }
                            ]

                        The path for populate would be /users.user_id/
                    """

                    popAux = pop["path"]
                    if popAux.find(".") > 0:
                        popAux = popAux.split(".")[0]

                    group["_id"] = _id
                    group[popAux] = {"$push": f"${parent}{popAux}"}
                    group["doc"] = {"$first": "$$ROOT"}

                    # print (group)

                    # print (f"path: {pop['path']}")
                    # print (f"N_parents {n_parents}")
                    # print (f"Parent: {parentAux}")
                    # print (f"Was List: {wL}")
                    
                    aggregate.append({
                        "$group": group
                    })

                    replaceRoot = {}
                    
                    if len(parent) > 0:
                        replaceRoot = {
                            "$mergeObjects": [
                                "$doc",
                                {"_id": f"$_id._id"},
                                _merge_objects(parentRoot, parentAux.split("."), parentRoot, popAux)
                            ]
                        }
                    else:
                        replaceRoot = {
                            "$mergeObjects": [
                                "$doc",
                                {"_id": "$_id._id"},
                                
                                {popAux: f"${popAux}"}
                                
                            ]
                        }
                    
                    aggregate.append({
                        "$replaceRoot": {"newRoot": replaceRoot}
                    })
                    

    return wasList

def _convert_id_to_object_id(id) -> ObjectId:#
    if type(id) is not ObjectId:
        id = ObjectId(id)
    return id

def count_documents(schema: str, query: dict) -> int:
    global schemas
    retval = -1
    try:
        schema_name = schema
        retval = database[schema_name].count_documents(query)
    except:
        raise MongoException(message="Error counting document(s)", mongoError=MongoError.Bad_action, bt=sys.exc_info())

    return retval

def find(schema: str, query: dict, select = {}, populate=None, one=False, skip = 0, limit=None, sort=None, no_cursor_timeout=False):
    global schemas
    schema_name = schema
    """
	Find a document inside a collection
	# Parameters
	------------
    ### schema: str
        Schema Name created in order to manage mongo documents
    ### query: dict
        Dictionary containing query
    ### select: dict
        Dictionary containing requested fields
        defaults to: {}
    ### populate: dict
        Dictionary containing lookup structure of the fields required to populate
        defaults to: None
    ### one: bool
        Variable to select if return one ore many
        defaults to: False
    ### skip: int
        Integer to skip to 'n' values to the left in the collection
        defaults to: 0
    ### limit: int
        Integer to limit number of documents returned from the collection
        defaults to: infinite
    ### sort: dict
        Dictionary to set an order of documents based on a field
        defaults to: None
    ### no_cursor_timeout: bool
    # Returns
    ------------
    - cursor if one is False else dict
	"""
    try:
        if "_id" in query and type(query["_id"]) is not dict:
            query["_id"] = _convert_id_to_object_id(query["_id"])
        
        
        sort_key, sort_value = "_id", ASCENDING
        if sort is not None:
                    sort_key = list(sort.keys())[0]
                    sort_value = ASCENDING if sort[sort_key] == 1 else DESCENDING

        schema = schemas[schema]
        retval = {}
        if populate is None:
            if one:
                retval = database[schema_name].find_one(query, select, no_cursor_timeout=no_cursor_timeout)
            else:
                if sort is not None:
                    if limit is None:
                        retval = database[schema_name].find(query, select, no_cursor_timeout=no_cursor_timeout).skip(skip).sort(sort_key, sort_value)
                    else:
                        retval = database[schema_name].find(query, select, no_cursor_timeout=no_cursor_timeout).skip(skip).limit(limit).sort(sort_key, sort_value)
                else:
                    if limit is None:
                        retval = database[schema_name].find(query, select, no_cursor_timeout=no_cursor_timeout).skip(skip)
                    else:
                        retval = database[schema_name].find(query, select, no_cursor_timeout=no_cursor_timeout).skip(skip).limit(limit)
        else:
            aggregate = [
                {"$match" : query}
            ]
        
            _populate(schema, populate, aggregate, "")
            
            if select is not None:
                aggregate.append({
                    "$project": select
                })

            if(sort is not None):
                aggregate.append({
                    "$sort": {
                        f"{sort_key}": sort_value
                    }
                })

            if(skip > 0):
                aggregate.append({
                    "$skip": skip
                })
            
            if(limit is not None):
                aggregate.append({
                    "$limit": limit
                })

            if debug_log:
                Logger.printLog (aggregate)

            retval = database[schema_name].aggregate(aggregate)

            
        if populate is not None and one:
            retval = list(retval)
            if len(retval) > 0:
                return retval[0]
            else:
                return None
        else:
            return retval
        
        
    except:
        raise MongoException(message="Error finding document(s)", mongoError=MongoError.Bad_action, bt=sys.exc_info())

def find_by_id(schema, id, select = {}, populate=None, no_cursor_timeout=False):
    """
	Find a document inside a collection by _id
    (Same as find({_id:id}))
	# Parameters
	------------
    ### schema: dict
        Schema created in order to manage mongo documents
    ### id: str
        ObjectId of the document
    ### select: dict
        Dictionary containing requested fields
        defaults to: {}
    ### populate: dict
        Dictionary containing lookup structure of the fields required to populate
        defaults to: None
    ### no_cursor_timeout: bool
    # Returns
    ------------
    - dict
	"""
    if type(id) is not dict:
        id = _convert_id_to_object_id(id)
    
    retval = find(schema, {"_id": id}, select, populate, one=True)
    return retval

def insert_one(schema, object: dict) -> ObjectId:
    try:
        retval = database[schema].insert_one(object)

        return retval.inserted_id
    except:
        raise MongoException(message=f"Error saving object in {schema}", mongoError=MongoError.Bad_action)

def aggregate(schema, aggregate):
    """
	Find a document inside a collection
	# Parameters
	------------
	### collection: Mongo collection
		Mongo collection where query will be executed
    ### aggregate: list
        Aggregation pipeline that is required
    # Returns
    ------------
    - coursor if one is False else dict
	"""
    return database[schema].aggregate(aggregate)

def update(schema, query, update, many = False, complete_response = False):
    """
	Update a document inside collection
	# Parameters
	------------
    ### schema: dict
        Schema created in order to manage mongo documents
    ### query: dict
        Dictionary containing query
    ### update: dict
        Dictionary containing mongodb update structure
    ### many: bool
        Variable to select if update one ore many
        defaults to: False
    # Returns
    ------------
    - Number of documents updated
	"""
    try:
        if type(query.get ("_id")) is str:
            query["_id"] = _convert_id_to_object_id(query["_id"])

        if not many:
            retval = database[schema].update_one(query, update)
            if (complete_response):
                return retval
            else:
                return retval.modified_count
        else:
            retval = database[schema].update_many(query, update)
            if (complete_response):
                return retval
            else:
                return retval.modified_count
    except:
        raise MongoException(sys.exc_info()[0],  message="Error updating document(s)", mongoError=MongoError.Bad_action)

def delete(schema, query, many = False, cascade=False):
    """
	Delete documents inside collection
	# Parameters
	------------
	### schema: dict
        Schema created in order to manage mongo documents
    ### query: dict
        Dictionary containing query
    ### many: bool
        Variable to select if delete one ore many
        defaults to: False
    ### cascade: bool
        Variable to delete all items related with this object id
        defaults to False
    # Returns
    ------------
    - number of documents deleted
	"""
    try:
        if "_id" in query:
            query["_id"] = _convert_id_to_object_id(query["_id"])

        if many:
            retval = database[schema].delete_many(query)
            return retval.deleted_count
        else:
            if(cascade):
                id = database[schema].find_one(query, {"_id": 1})
            database[schema].delete_one(query)
            return 1
    except:
        raise MongoException(message="Error deleting document(s)", mongoError=MongoError.Bad_action, bt=sys.exc_info()[0])

def get_cursor_length(cursor):
    return len(list(cursor))