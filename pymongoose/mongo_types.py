import sys, traceback
from enum import Enum
import datetime
import bson.json_util as json_util
from pymongoose.logger import Logger
from pymongoose import methods
from bson import ObjectId
import json

AS_DEFAULT = 0
AS_DICT = 1
AS_STRING = 2

class Types(Enum):
	"""
	Enum to be used on your schemas creation
	"""
	String      = 1
	Number      = 2
	Date        = 3
	ObjectId    = 4
	Boolean     = 5

class MongoError(Enum):
	"""
	Mongo error Enum used in mongo exception
	"""
	Empty_dataset	= 1
	Required_field 	= 2
	Bad_type 		= 3
	Bad_action		= 4

class MongoException(Exception):
	"""
	Mongo exception class to be used in mongo methods
	"""
	message = ""
	mongoError = None
	bt = ""

	def __init__(self, *args, **kwargs):
		self.message = kwargs["message"]
		self.mongoError = kwargs["mongoError"]
		exc_type, exc_obj, exc_tb = sys.exc_info()
		super().__init__(
			# f"Exception ocurred in line = {exc_tb.tb_lineno}\n",
			f"Offense ocurred = {MongoError(self.mongoError).name}\n" +
			f"Thrown message = {self.message}"
		)
		traceback.print_exc()
		if methods.debug_log:
			Logger.printError(
				# f"Exception ocurred in line = {exc_tb.tb_lineno}\n",
				f"Offense ocurred = {MongoError(self.mongoError).name}\n" +
				f"Thrown message = {self.message}"
			)	

class Schema(object):
	"""
	Parent class of any schema that is created
	"""
	id = None
	schema = {}
	schema_name = None

	def __init__(self, schema_name, schema, initial_values = {}):
		"""
		### schema_name: str
			Name set to the schema (must be plural)
		### schema: dict
			Schema generated with types, defaults and/or required fields
		### initial_values: dict
			Dictionary containing initial values of this schema, must contain same names as the schema has
			defaults to: {}
		"""
		self.schema = schema
		self.schema_name = schema_name
		id = initial_values["id"] if "id" in initial_values else ObjectId()
		self.id = ObjectId(id) if type(id) is str else id

		is_empty = False
		if "empty" in initial_values:
			is_empty = initial_values["empty"]

		
		if not is_empty:
			if len(initial_values) == 0:
				initial_values = {}
			
			clean_schema = {}
			for key in self.schema.keys():
				clean_schema[key] = self.get_default_value(key, initial_values)

			self.__dict__.update(clean_schema)
	
	def fromJson(self, json_obj):
		for key in self.schema.keys():
			if methods.debug_log:
				Logger.printLog(f"Setting {key}")
			setattr(self, key, self.get_default_value(key, json_obj))
			
		if methods.debug_log:
			Logger.printLog(f"Setting _id")
		self.id = self.get_default_value("_id", json_obj)

	def toJson (self, full=True):
		"""
		Method to convert current Schema object to a dictionary
		# Parameters
		------------
		### full: bool
			If true, will attach id to dictionary
			defaults to: True
		# Returns
		------------
		- dict
		"""
		json_obj = {}

		for key in self.schema.keys():
			json_obj[key] = getattr(self, key)

		if full:
			json_obj["id"] = self.id

		return json_obj

	def save(self, id = None):
		"""
		Function to save current object into a mongoDB collection
		# Parameters
		------------
		### id: ObjectId
			Set a forced id to save method
			defaults to: None
		# Returns
		------------
		- ObjectId -> Saved id
		"""
		if not self.validate_required(self.toJson(False), self.schema):
			raise MongoException(message="Required fields missing", mongoError=MongoError.Required_field)
		elif not self.validate_type(self.toJson(False), self.schema):
			raise MongoException(message="Type fields are wrong", mongoError=MongoError.Bad_type, bt=sys.exc_info())

		else:
			json_obj = self.toJson(False)
			if id is not None:
				json_obj["_id"] = id

			retval = methods.insert_one(self.schema_name, json_obj)
			self.id = retval
		return self.id

	def parse_schema_value(self, value):
		"""
		From current schema, will get default value if exists, None if not.
		# Parameters:
		--------------
		- value: string
		Name of field
		"""
		isList = False
		valAux = value
		if type(value) is list:
			isList = True
			valAux = value[0]
		
		if "default" in valAux:
			return valAux["default"] if not isList else [valAux["default"]]
		else:
			dictionary = {}
			for k in valAux:
				if type(valAux[k]) is dict:
					e = self.parse_schema_value(valAux[k])
					dictionary[k] = e
			if isList:
				return [] if len(dictionary) == 0 else [dictionary]
			else:
				return None if len(dictionary) == 0 else dictionary

	def extract(self, key, json_obj):
		"""
		Extract a value from a dictionary, if it doesn't exists then will get default value, else None
		# Parameters:
		------------
		- key: String
		Required key from dictionary
		- json_obj: dict
		Dictionary where it will be looked
		# Returns: [Value] or None
		"""
		return json_obj[key] if key in json_obj else self.get_default_value(key, [])

	def type_validator(self, type, value) -> bool:
		if type == Types.String:
			return True if type(value) is str else False
		elif type == Types.Number:
			return True if type(value) is float or type(value) is int else False
		elif type == Types.Date:
			return True if type(value) is datetime.datetime else False
		else: return True

	def _item_type_check(self, key, type, item_type):
		if item_type == None or item_type == dict:
			if methods.debug_log:
				Logger.printLog(f"key {key} doesn't come in json, returning True")
			return True

		if type == Types.Number:
			if item_type is int or item_type is float:
				return True
			else:
				Logger.printError(f"key {key} has an incorrect type") 
				return False
		elif type == Types.String:
			if item_type is str:
				return True
			else:
				Logger.printError(f"key {key} has an incorrect type") 
				return False
		elif type == Types.Date:
			if "datetime.datetime" in str(item_type):
				return True
			else:
				Logger.printError(f"key {key} has an incorrect type") 
				return False
		elif type == Types.ObjectId:
			if item_type is ObjectId:
				return True
			else:
				Logger.printError(f"key {key} has an incorrect type") 
				return False
		elif type == Types.Boolean:
			if item_type is bool:
				return True
			else:
				Logger.printError(f"key {key} has an incorrect type")
				return False

	def _validate_type_cycle(self, scAux, json_obj, last_key):

		if "type" in scAux:
			tp = type(json_obj) if json_obj is not None else None
			retval = self._item_type_check(last_key, scAux["type"], tp)

			if retval:
				if methods.debug_log:
					Logger.printSuccess(f"(type) key={last_key} in schema has a correct value type")
			else:
				Logger.printError(f"(type) key={last_key} in schema has an incorrect value type")

			return retval

		retval = True
		for k in scAux:
			retval = True
			if type(scAux[k]) is dict or type(scAux[k]) is list:
				if "type" in scAux[k]:
					tp = type(json_obj[k]) if k in json_obj and json_obj[k] is not None else None
					retval = self._item_type_check(k, scAux[k]["type"], tp)
					
				elif type(scAux[k]) is list or dict in list(map(type, scAux[k].values())):
					retval = self.validate_type(
						json_obj[k] if k in json_obj and json_obj[k] is not None else
							[{}] if type(scAux[k]) is list else {},
						scAux[k], 
						k
					)
				else:
					if methods.debug_log:
						Logger.printWarn(f"(type) key={k} in schema doesn't contain any type, returning True")
					retval = True

				if not retval:
					Logger.printError(f"(type) key={k} in schema has an incorrect value type")
					return retval
				
				if methods.debug_log:
					Logger.printSuccess(f"(ty!pe) key={k} in schema has a correct value type")
			else:
				if methods.debug_log:
					Logger.printWarn(f"(type) key={k} schema is not a dict, returning True")
			
		return retval

	def validate_type(self, json_obj: dict, sc=schema, last_key = None) -> bool:
		scAux = sc
		is_list = False
		if type(sc) is list:
			scAux = sc[0]
			is_list = True

		retval = False
		if is_list:
			if len(json_obj) == 0:
				retval = self._validate_type_cycle(scAux, {}, last_key)
			else:
				for i, obj in enumerate(json_obj):
					retval = self._validate_type_cycle(scAux, obj, last_key)

					if retval:
						if methods.debug_log:
							Logger.printSuccess(f"(type) key '{last_key}-{i}' has a valid type")
					else:
						return False

		else:
			retval = self._validate_type_cycle(scAux, json_obj, last_key)

		return retval

	def _validate_required_cycle(self, scAux, json_obj) -> bool:
		if "required" in scAux and scAux["required"]:
			return json_obj is not None

		retval = True
		for k in scAux:
			retval = True
			if type(scAux[k]) is dict or type(scAux[k]) is list:
				if "required" in scAux[k] and scAux[k]["required"]:
					if not k in json_obj or json_obj[k] is None:
						Logger.printError(f"(req) key '{k}' is required but value doesn't come")
						return False
					else:
						retval = True
				elif type(scAux[k]) is list or dict in list(map(type, scAux[k].values())):
						retval = self.validate_required(
							json_obj[k] if k in json_obj and json_obj[k] is not None else
								[{}] if type(scAux[k]) is list else {}, 
							scAux[k], 
							k
						)
				else:
					if methods.debug_log:
						Logger.printLog(f"(req) key={k} doesn't contain required value, setting by default in False")
					retval = True

				if retval:
					if methods.debug_log:
						Logger.printSuccess(f"(req) key '{k}' has a valid argument")

				if not retval: 
					Logger.printError(f"(req) key '{k}' is required but value doesn't come")
					return retval
			else:
				if methods.debug_log:
					Logger.printLog(f"(req) key={k} current schema isn't a dict, setting by default in False")

		return retval

	def validate_required(self, json_obj: dict, sc=schema, last_key="") -> bool:
		"""
		Check if current schema object contains all required fields dicted by schema
		# Parameters:
		------------
		- json_obj: dict
		Dictionary where it will be looked
		# Returns: bool
		"""
		scAux = sc
		is_list = False
		if type(sc) is list:
			scAux = sc[0]
			is_list = True

		retval = False
		if is_list:
			if len(json_obj) == 0:
				retval = self._validate_required_cycle(scAux, {})
			else:
				for i, obj in enumerate(json_obj):
					retval = self._validate_required_cycle(scAux, obj)

					if retval:
						if methods.debug_log:
							Logger.printSuccess(f"(req) key '{last_key}-{i}' has a valid argument")
					else:
						return False

		else:
			retval = self._validate_required_cycle(scAux, json_obj)

		return retval
		
	def get_default_value(self, name, kwargs):
		"""
		Wrapper function for parse_schema_value
		# Parameters:
		----------
		- name: str
		Name of the variable looking for
		- kwargs: tuple
		Array of variables that may contain looking variable
		# Returns:
		[value] or None
		"""
		try:
			cond = name in kwargs
			if(cond and "ignore_none" in kwargs and kwargs["ignore_none"]):
				cond = cond and kwargs[name] is not None
			return kwargs[name] if cond else self.parse_schema_value(self.schema[name])

		except:
			return None

	def convert_json(self, json_obj):
		"""
		Function to convert json to an acceptable serializable json
		# Parameters:
		----------
		- json_obj: dict
		Dictionary containing object ids, datetimes or another non serializable value
		# Returns:
		Serializable dictionary
		"""
		obj = json_util.dumps(json_obj, json_options=json_util.STRICT_JSON_OPTIONS)
		obj = json.loads (obj)
		return obj

	@classmethod
	def exists(cls, query):
		retval = methods.exists(cls.schema_name, query)
		return retval

	@classmethod
	def count(cls, query: dict) -> int:
		"""
		Count a number of documents inside a collection by query
		# Parameters
		------------
		### query: dict
			Dictionary containing query
		# Returns
		------------
		- int
		"""
		if methods.debug_log:
			Logger.printLog(cls.schema_name + " Count")
		retval = methods.count_documents(cls.schema_name, query)
		return retval

	@classmethod
	def find(
		cls, query, select = None, populate=None, one=False, 
		skip = 0, limit=None, sort=None, parse=True, cursor=AS_DEFAULT
	):
		"""
		Find a document inside a collection
		# Parameters
		------------
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
			defaults to: None
		### sort: dict
			Dictionary to set an order of documents based on a field
			defaults to: None
		### parse: bool
			If one is True, then document could be parsed and returned as a Schema object
			defaults to: True
		### cursor: int
			If cursor is not AS_DEFAULT(0), will give it a special traitment
			- IF AS_DICT(1), will return a list of dicts if one == False, else as serializable dict
			- IF AS_STRING(2), will return a parsed list of dicts as str if one == False, else as a str parsed serializable dict
			*Note: In case you don't need a serializable dict, left cursor AS_DEFAULT
			defaults to: AS_DEFAULT (0)
		# Returns
		------------
		- Cursor -> one == False, populate == None
		- CommandCursor -> populate != None
		- dict -> one == True, parse == False
		- Schema object -> one == True, parse == True
		- list -> cursor == AS_DICT, one == False
		- str -> cursor == AS_STRING, one == False
		- None -> not found
		"""
		if methods.debug_log:
			Logger.printLog(cls.schema_name)
		retval = methods.find(cls.schema_name, query, select, populate, one, skip, limit, sort)
		if one and parse:
			retval = cls.parse(retval) if retval is not None else retval
		elif cursor == AS_DICT:
			# if type(retval) is dict:
			retval = json.loads(json_util.dumps(retval))
		elif cursor == AS_STRING:
			retval = json_util.dumps(retval)
		return retval

	@classmethod
	def find_one (cls, query, select = None, populate=None, 
		skip = 0, limit=None, sort=None, parse=True, cursor=AS_DEFAULT
	):
		"""
		Find one document inside a collection
		# Parameters
		------------
		### query: dict
			Dictionary containing query
		### select: dict
			Dictionary containing requested fields
			defaults to: {}
		### populate: dict
			Dictionary containing lookup structure of the fields required to populate
			defaults to: None
		### skip: int
			Integer to skip to 'n' values to the left in the collection
			defaults to: 0
		### limit: int
			Integer to limit number of documents returned from the collection
			defaults to: None
		### sort: dict
			Dictionary to set an order of documents based on a field
			defaults to: None
		### parse: bool
			If one is True, then document could be parsed and returned as a Schema object
			defaults to: True
		### cursor: int
			If cursor is not AS_DEFAULT(0), will give it a special traitment
			- IF AS_DICT(1), will return a list of dicts if one == False, else as serializable dict
			- IF AS_STRING(2), will return a parsed list of dicts as str if one == False, else as a str parsed serializable dict
			*Note: In case you don't need a serializable dict, left cursor AS_DEFAULT
			defaults to: AS_DEFAULT (0)
		# Returns
		------------
		- Cursor -> one == False, populate == None
		- CommandCursor -> populate != None
		- dict -> one == True, parse == False
		- Schema object -> one == True, parse == True
		- list -> cursor == AS_DICT, one == False
		- str -> cursor == AS_STRING, one == False
		- None -> not found
		"""
		return cls.find (query, select, populate, True, skip, limit, sort, parse, cursor)

	@classmethod
	def find_by_id(cls, id, select = None, populate=None, parse=True, cursor=AS_DEFAULT):
		"""
		Find a document inside a collection by id
		# Parameters
		------------
		### id: str | ObjectId
			Id of the document to lookup
		### select: dict
			Dictionary containing requested fields
			defaults to: {}
		### populate: dict
			Dictionary containing lookup structure of the fields required to populate
			defaults to: None
		### parse: bool
			If true, document will be returned as an Schema Object
			defaults to: True
		### cursor: int
			If cursor is not AS_DEFAULT(0), will give it a special traitment
			- IF AS_DICT(1), will return a serializable dict
			- IF AS_STRING(2), will return a str parsed serializable dict
			*Note: In case you don't need a serializable dict, left cursor AS_DEFAULT
			defaults to: AS_DEFAULT (0)
		# Returns
		------------
		- dict -> parse = False
		- Schema object -> parse = True 
		"""
		retval = methods.find_by_id(cls.schema_name, id, select, populate)

		if parse:
			retval = cls.parse(retval) if retval is not None else retval
		elif cursor == AS_DICT:
			retval = json_util.dumps(retval)
			retval = json.loads(retval)
		elif cursor == AS_STRING:
			retval = json_util.dumps(retval)
		
		return retval

	@classmethod
	def aggregate(cls, aggregate):
		"""
		Generate an Aggregate inside a collection
		# Parameters
		-------------
		### aggregate: list
		List of dicts following aggregation mongodb rules
		# Returns
		------------
		- commandCursor
		"""
		retval = methods.aggregate(cls.schema_name, aggregate)
		return retval

	@classmethod
	def update(cls, query, update, many = False, complete_response = False):
		"""
		Update document(s) inside a collection by query
		# Parameters
		------------
		### query: dict
			Dictionary containing query
		### update: dict
			Dictionary containing update, following mongoDB rules
		### many: bool
			If True, will modify all documents found with that query
		defaults to False
		### complete_response: bool
			If True, Pymongo Response will be returned, otherwise will return modified_count
		default to False
		# Returns
		------------
		- int -> Modified count
		"""
		retval = methods.update(cls.schema_name, query, update, many, complete_response)
		return retval

	@classmethod
	def update_many(cls, query, update, complete_response = False):
		"""
		Update many documents inside a collection by query
		# Parameters
		------------
		### query: dict
			Dictionary containing query
		### update: dict
			Dictionary containing update, following mongoDB rules
		# Returns
		------------
		- int -> Modified count
		"""
		return cls.update (query, update, True, complete_response)

	@classmethod
	def delete(cls, query, many = False):
		"""
		Delete document(s) inside a collection by query
		# Parameters
		------------
		### query: dict
			Dictionary containing query
		### many: bool
			If True, will modify all documents found with that query
		defaults to False
		# Returns
		------------
		- int -> Modified count
		"""
		retval = methods.delete(cls.schema_name, query, many)
		return retval

	@classmethod
	def delete_many(cls, query):
		"""
		Delete one document inside a collection by query
		# Parameters
		------------
		### query: dict
			Dictionary containing query
		# Returns
		------------
		- int -> Modified count
		"""
		return cls.delete (query, True)

	@classmethod
	def parse(cls, dictionary):
		"""
		Converts a dictionary into a Schema object
		# Parameters
		------------
		### dictionary: dict
			Dictionary containing document information
		# Returns
		------------
		- Schema object -> Result
		"""
		schema = cls()
		schema.fromJson(dictionary)
		return schema