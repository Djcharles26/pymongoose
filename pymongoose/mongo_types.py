import sys
from enum import Enum
import datetime
import bson.json_util as json_util
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
	Bad_action		= 3

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
		self.bt = kwargs["bt"]
		exc_type, exc_obj, exc_tb = sys.exc_info()
		super().__init__(f"{self.bt}, line: {exc_tb.tb_lineno}")
		print(exc_tb.tb_lineno)	

class Schema(object):
	"""
	Parent class of any schema that is created
	"""
	schema = {}
	def __init__(self, schema):
		self.schema = schema

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

	def validate_required(self, json_obj, sc=schema) -> bool:
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
				retval = True

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
