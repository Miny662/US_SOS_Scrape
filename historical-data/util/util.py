def safeget(_dict: dict, *keys, cast_as=None, default=None):
	"""Retrieve values from nested keys in a dict safely.

	Args:
		_dict: The dict containing the desired keys and values.
		*keys: Key structure in the dict leading to the desired value.
			(Must be str for dictionary, int for array)
		cast_as: Optional type to cast the result to.
		default: Value returned if any key doesn't exist or casting fails.

	Returns:
		The value at the nested keys path, or default if not found or casting fails.
	"""
	try:
		val = _dict
		for key in keys:
			val = val[key]

		if val is None:
			return default

		if cast_as is not None:
			return cast_as(val)

		return val
	except:
		return default