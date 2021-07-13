import sys
from pymongo import DESCENDING, ASCENDING
from bson.objectid import ObjectId
from .mongo_types import *
from pprint import pprint
import math

schemas = {}

def set_schemas(schemas_re):
    """
    ## Description:
    Function to be called were you control your models registration
    # Parameters
    ------------
    - schemas_re: dict
    A dictionary with all your registerd schemas.
    f.e: {"users": User.schema}
    """
    global schemas
    schemas = schemas_re
    print("MongoDB Schemas: ")
    pprint(schemas)

def exists(collection, query):
    """
	Check if document exists in collection
	# Parameters
	------------
	### collection: Mongo collection
		Mongo collection where query will be executed
    ### query: dict
        Dictionary containing query
    # Returns
    ------------
    - boolean
	"""
    return collection.count_documents(query, limit = 1) > 0

def _get_clean_schema(schema, pop):
    isList = False
    aux_schema = schema.copy()
    if pop.find(".") > 0:
        populate_list = pop.replace(" ", "").split(".")
        for pop1 in populate_list:
            if type(aux_schema) is list: 
                isList = True
                aux_schema = aux_schema[0]

            aux_schema = aux_schema[pop1]
    else:
        aux_schema = aux_schema[pop]

    if type(aux_schema) is list:
        isList = True
        aux_schema = aux_schema[0]

    return aux_schema, isList

def _populate(schema, populate, aggregate, parent=""):
    wasList = False
    for pop in populate: #Iterate in each populate object or str
        if type(pop) is not dict: #If is a str is a simple lookup and unwind
            aux_schema, isList = _get_clean_schema(schema, pop)
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
            aux_schema, isList = _get_clean_schema(schema, pop["path"])
            
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
            ##Add respective pipeline with select and match
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
                    print(s)
                    project[s]= 1
                
                pipeline.append({"$project": project})

            if "match" in pop:
                pipeline.append({"$match": pop["match"]})
            

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

            wL = False

            if "options" in pop: #If has attached populates
                
                ##Recursively call to function with respectie schema 

                wL = _populate(schemas[aux_schema["ref"]], pop["options"], aggregate, parent + pop["path"] + ".") 

            ## If current isList is true
            ## If len(parent) > 0 then current parent should be added in _id else _id = "$_id._id"
                ## path: {"$push": "$parent.path"}
                ## doc: {"$first": "$$ROOT"}
                ## add $replaceRoot with $_id, parent: {"$mergeObjects": ["$doc", {"_id": "$_id"}, {"$parent": {"$mergeObjects": ["$parent", {"path": "$path"}]}}]}

            if isList: #Group and replace to have a correct object
                group = {}
                _id = {}

                parentAux = parent
                if len(parent) > 0:
                    parentAux = parent[:-1]
                    _id = {
                        "_id": "$_id",
                        parentAux: f"${parentAux}._id"
                    }
                else: 
                    _id = "$_id._id" if wL else "$_id"

                popAux = pop["path"]
                if popAux.find(".") > 0:
                    popAux = popAux.split(".")[0]

                group["_id"] = _id
                group[popAux] = {"$push": f"${parent}{popAux}"}
                group["doc"] = {"$first": "$$ROOT"}

                aggregate.append({
                    "$group": group
                })

                replaceRoot = {}
                if len(parent) > 0:
                    replaceRoot = {
                        "$mergeObjects": [
                            "$doc",
                            {"_id": "$_id"},
                            {
                                parentAux: {
                                    "$mergeObjects": [f"$doc.{parentAux}", {popAux: f"${popAux}"}]
                                }
                            }
                        ]
                    }
                else:
                    replaceRoot = {
                        "$mergeObjects": [
                            "$doc",
                            {"_id": "$_id"},
                            
                            {popAux: f"${popAux}"}
                            
                        ]
                    }
                
                aggregate.append({
                    "$replaceRoot": {"newRoot": replaceRoot}
                })
                

    return wasList

def _convert_id_to_object_id(id) -> ObjectId:
    if type(id) is not ObjectId:
        id = ObjectId(id)
    return id

def find(collection, schema, query, select = {}, populate=None, one=False, skip = 0, limit=None, sort = None):
    global schemas
    """
	Find a document inside a collection
	# Parameters
	------------
	### collection: Mongo collection
		Mongo collection where query will be executed
    ### schema: dict
        Schema created in order to manage mongo documents
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
                retval = collection.find_one(query, select)
            else:
                if limit is None:
                    retval = collection.find(query, select).skip(skip).sort(sort_key, sort_value)
                else:
                    retval = collection.find(query, select).skip(skip).limit(limit).sort(sort_key, sort_value)
        else:
            aggregate = [
                {"$match" : query}
            ]
        
            _populate(schema, populate, aggregate, "")
            
            if select is not None:
                aggregate.append({
                    "$project": select
                })

            aggregate.append({
                "$skip": skip
            })
            
            if(limit is not None):
                aggregate.append({
                    "$limit": limit
                })

            aggregate.append({
                "$sort": {
                    f"{sort_key}": sort_value
                }
            })
            

            retval = collection.aggregate(aggregate)

            
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

def find_by_id(collection, schema, id, select = {}, populate=None):
    """
	Find a document inside a collection by _id
    (Same as find({_id:id}))
	# Parameters
	------------
	### collection: Mongo collection
		Mongo collection where query will be executed
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
    # Returns
    ------------
    - dict
	"""
    if type(id) is not dict:
        id = _convert_id_to_object_id(id)
    
    retval = find(collection, schema, {"_id": id}, select, populate, one=True)
    return retval

def aggregate(collection, aggregate):
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
    return collection.aggregate(aggregate)

def update(collection, query, update, many = False):
    """
	Update a document inside collection
	# Parameters
	------------
	### collection: Mongo collection
		Mongo collection where query will be executed
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
        if "_id" in query:
            query["_id"] = _convert_id_to_object_id(query["_id"])

        if not many:
            retval = collection.update_one(query, update)
            return retval.modified_count
        else:
            retval = collection.update_many(query, update)
            return retval.modified_count
    except:
        raise MongoException(sys.exc_info()[0],  message="Error updating document(s)", mongoError=MongoError.Bad_actio)

def delete(collection, query, many = False):
    """
	Delete documents inside collection
	# Parameters
	------------
	### collection: Mongo collection
		Mongo collection where query will be executed
    ### query: dict
        Dictionary containing query
    ### many: bool
        Variable to select if delete one ore many
        defaults to: False
    # Returns
    ------------
    - number of documents deleted
	"""
    try:
        if "_id" in query:
            query["_id"] = _convert_id_to_object_id(query["_id"])

        if many:
            retval = collection.delete_many(query)
            return retval.deleted_count
        else:
            collection.delete_one(query)
            return 1
    except:
        raise MongoException(message="Error deleting document(s)", mongoError=MongoError.Bad_action, bt=sys.exc_info()[0])

def get_cursor_length(cursor):
    return len(list(cursor))