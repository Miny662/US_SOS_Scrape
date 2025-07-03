import random
from typing import List, Dict, Any


def randomize_proxy(
		proxies: List[Dict[str, Any]],
		limit: int = 5,
		offset: int = 0,
		shuffle: bool = True,
		single_endpoint: bool = False
) -> List[Dict[str, str]]:
	"""
	Randomizes the proxy URL by changing the port to a random value.

	Args:
		proxies: List of proxy data. Each dictionary contain:
			- "proxyAddress": str (required)
			- "port": str (required)
			- "username": str (optional)
			- "password": str (optional)
		limit: Maximum number of proxies to return (default: 5).
		offset: Offset for the list of proxies (default: 0).
		shuffle: Whether to shuffle the proxies (default: True).
		single_endpoint: If True, returns a list of proxy URL instead of a list of proxy dictionary (default: False).

	Returns:
		A list of dictionaries with randomized proxy URLs.
	"""
	if not proxies or offset >= len(proxies):
		return []

	# Slice proxies based on offset and limit
	proxies = proxies[offset:]
	if shuffle:
		random.shuffle(proxies)
	proxies = proxies[:limit]

	randomized_proxies = []
	for proxy in proxies:
		url = proxy.get("proxyAddress")
		port = proxy.get("port")
		user = proxy.get("username", "")
		password = proxy.get("password", "")

		# Validate required fields
		if not url or not port:
			continue

		if single_endpoint:
			# If single_endpoint is True, use the first proxy only
			randomized_proxies.append(f"http://{user}:{password}@{url}:{port}")
		else:
			randomized_proxies.append({
				"http": f"http://{user}:{password}@{url}:{port}",
				"https": f"http://{user}:{password}@{url}:{port}"
			})

	return randomized_proxies


def parse_proxy(url: str, port: str, user: str, password: str) -> Dict:
	return {
		"http": f"http://{user}:{password}@{url}:{port}",
		"https": f"http://{user}:{password}@{url}:{port}"
	}