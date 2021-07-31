import sys, traceback
from enum import Enum
import datetime
import bson.json_util as json_util
from pymongoose.logger import Logger
from pymongoose import methods
from bson import ObjectId
import json


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
		self.schema = schema
		self.schema_name = schema_name
		self.id = ObjectId()

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
			setattr(self, key, self.get_default_value(key, json_obj))

	def toJson (self, full=True):
		json_obj = {}

		for key in self.schema.keys():
			json_obj[key] = getattr(self, key)

		if full:
			json_obj["id"] = self.id

		return json_obj

	def save(self, id = None):
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
		if type == Types.Number:
			if item_type is int or item_type is float:
				return True
			else:
				if methods.debug_log:
					Logger.printError(f"key {key} has an incorrect type") 
				return False
		elif type == Types.String:
			if item_type is str:
				return True
			else:
				if methods.debug_log:
					Logger.printError(f"key {key} has an incorrect type") 
				return False
		elif type == Types.Date:
			if item_type is datetime:
				return True
			else:
				if methods.debug_log:
					Logger.printError(f"key {key} has an incorrect type") 
				return False
		elif type == Types.ObjectId:
			if item_type is ObjectId:
				return True
			else:
				if methods.debug_log:
					Logger.printError(f"key {key} has an incorrect type") 
				return False

	def validate_type(self, json_obj: dict, sc=schema, last_key = None) -> bool:
		scAux = sc
		if type(sc) is list:
			scAux = sc[0]

		if "type" in scAux:
			retval = True
			if type(json_obj) is list:
				for item in json_obj:
					retval = self._item_type_check(last_key, scAux["type"], type(item))
			else:
				retval = self._item_type_check(last_key, scAux["type"], type(json_obj))
			return retval
					

		for k in scAux:
			retval = True
			if "type" in scAux[k]:
				tp = type(json_obj[k])
				retval = self._item_type_check(k, scAux[k]["type"], tp)
				
			elif type(scAux[k]) is list or dict in list(map(type, scAux[k].values())):
				retval = self.validate_type(json_obj[k], scAux[k], last_key=k)
			else:
				if methods.debug_log:
					Logger.printWarn(f"key={k} in schema doesn't contain any type, returning True")
				retval = True

			if not retval: return retval

		return True

	def validate_required(self, json_obj: dict, sc=schema) -> bool:
		"""
		Check if current schema object contains all required fields dicted by schema
		# Parameters:
		------------
		- json_obj: dict
		Dictionary where it will be looked
		# Returns: bool
		"""
		scAux = sc
		if type(sc) is list:
			scAux = sc[0]

		if "required" in scAux:
			return json_obj is not None

		for k in scAux:
			retval = True
			if "required" in scAux[k]:
				if not k in json_obj or json_obj[k] is None:
					return False
				else:
					retval = True
			elif type(scAux[k]) is list or dict in list(map(type, scAux[k].values())):
				retval = self.validate_required(json_obj[k], scAux[k])
			else:
				if methods.debug_log:
					Logger.printLog(f"key={k} doesn't contain required value, setting by default in False")
				retval = True

			if retval:
				if methods.debug_log:
					Logger.printSuccess(f"key '{k}' has a valid argument")

			if not retval: return retval

		return True
			
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
		retval = methods.exists(cls.collection, query)
		return retval

	@classmethod
	def find(cls, query, select = None, populate=None, one=False, skip = 0, limit=None, sort=None):
		Logger.printLog(cls.schema_name)
		retval = methods.find(cls.schema_name, query, select, populate, one)
		if one:
			retval = cls.parse(retval)
		return retval

	@classmethod
	def find_by_id(cls, id, select = None, populate=None):
		retval = methods.find_by_id(cls.schema_name, id, select, populate)
		return cls.parse(retval)

	@classmethod
	def aggregate(cls, aggregate):
		retval = methods.aggregate(cls.schema_name, aggregate)

	@classmethod
	def update(cls, query, update, many = False):
		retval = methods.update(cls.schema_name, query, update, many)
		return retval

	@classmethod
	def delete(cls, query, many = False):
		retval = methods.delete(cls.schema_name, query, many)
		return retval

	@classmethod
	def parse(cls, dictionary):
		schema = cls()
		schema.fromJson(dictionary)
		return schema