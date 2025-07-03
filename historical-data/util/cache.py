import os
import time
import threading
from typing import Any, Dict, Optional, Tuple

# In-memory cache storage with lock for thread safety
_cache: Dict[str, Tuple[Any, float]] = {}
_cache_lock = threading.RLock()
_MAX_CACHE_SIZE = os.getenv("SCRAPER_CACHE_SIZE", 1000)  # Default cache size limit, we have 1000 proxies, so keeping 1000, but needs to be increased if we ever use this cache for more than just proxies


def cache_set(key: str, value: Any, ttl_seconds: int = 3600) -> None:
	"""
	Store data in the in-memory cache with TTL support.

	Args:
		key: Key for the data to be cached
		value: Data to be cached
		ttl_seconds: Time-to-live in seconds (default: 1 hour)
	"""
	expiry_time = time.time() + ttl_seconds

	with _cache_lock:
		# Check if we need to clean up the cache due to size limits
		# this is useful, if we ever start using this cache for more than just proxies
		if len(_cache) > _MAX_CACHE_SIZE and key not in _cache:
			_cleanup_cache()

		_cache[key] = (value, expiry_time)


def cache_get(key: str) -> Optional[Any]:
	"""
	Retrieve data from the in-memory cache, respecting TTL.

	Args:
		key: Unique identifier for the cached item

	Returns:
		The cached value if found and not expired, None otherwise
	"""
	try:
		cache_entry = _cache.get(key)
		if cache_entry is None:
			return []

		value, expiry_time = cache_entry
		current_time = time.time()

		# If not expired, return immediately
		if current_time <= expiry_time:
			return value

		# Expired item
		return []
	except:
		return []


def cache_delete(key: str) -> bool:
	"""
	Delete an item from the cache.

	Args:
		key: Unique identifier for the cached item

	Returns:
		True if the item was deleted, False if it wasn't in the cache
	"""
	with _cache_lock:
		if key in _cache:
			del _cache[key]
			return True
		return False


def cache_clear() -> None:
	"""
	Clear all items from the cache.
	"""
	with _cache_lock:
		_cache.clear()


def _cleanup_cache() -> None:
	"""Important function to clean up expired items and reduce cache size.
	Should be called within a lock context.
	"""
	# removing expired items
	current_time = time.time()
	expired_keys = [k for k, (_, exp_time) in _cache.items() if current_time > exp_time]
	for k in expired_keys:
		del _cache[k]

	# If still too large, removing the oldest items (based on the expiry time)
	if len(_cache) > _MAX_CACHE_SIZE:
		sorted_keys = sorted(_cache.items(), key=lambda x: x[1][1])
		keys_to_remove = sorted_keys[:len(_cache) - _MAX_CACHE_SIZE + 1]
		for k, _ in keys_to_remove:
			del _cache[k]