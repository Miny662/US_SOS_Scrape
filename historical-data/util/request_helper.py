import os
import time
import random
import logging
from typing import List, Dict, Any, Optional
import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException
from urllib3.util.retry import Retry
from util.config import CONFIG
from util.cache import cache_get, cache_set
from util.proxy_manager import randomize_proxy

PROXY_GATEWAY_URL = os.getenv("PROXY_GATEWAY_URL", "https://gateway.getpalm.com/v1/proxies")
logger = logging.getLogger(__name__)

def make_request(
		url: str,
		method: str,
		headers: Optional[Dict[str, str]] = None,
		payload: Optional[Dict[str, Any]] = None,
		data: Optional[Dict[str, Any]] = None,
		params: Optional[Dict[str, Any]] = None,
		failed_codes: Optional[List[int]] = None,
		successful_codes: Optional[List[int]] = None,
		max_retries: int = 3,
		timeout: int = 10,
		proxies: Optional[List[str]] = None,
		backoff_factor: float = 0.3,
		use_session: bool = False
) -> requests.Response:
	"""
	Makes an HTTP request with retry logic.

	Args:
		url: Target URL for the request.
		method: HTTP method (GET, POST, PUT, etc.).
		headers: HTTP headers to include.
		payload: JSON payload for the request.
		data: Form data for the request.
		params: Query parameters for the request.
		failed_codes: Status codes that should trigger a retry.
		successful_codes: Status codes that indicate success (will not retry).
		max_retries: Maximum number of retry attempts.
		timeout: Request timeout in seconds.
		proxies: List of proxy URLs to cycle through.
		backoff_factor: Backoff factor for retry delay calculation.
		use_session: Whether to use requests.Session with HTTPAdapter for retries.

	Returns:
		Response object from the successful request.

	Raises:
		RequestException: If all retry attempts fail.
	"""
	method = method.upper()
	failed_codes = failed_codes or []
	successful_codes = successful_codes or []

	# Configure retry strategy
	retry_strategy = Retry(
		total=max_retries,
		status_forcelist=failed_codes,
		backoff_factor=backoff_factor,
		raise_on_status=True
	)

	if not proxies:
		proxy_lists = get_proxies(service="webshare")
		proxies = randomize_proxy(proxy_lists, limit=max_retries + 1, shuffle=True) if proxy_lists else []

	last_exception = None
	for attempt in range(max_retries + 1):
		# Set up session or direct request
		session = None
		if use_session:
			session = requests.Session()
			adapter = HTTPAdapter(max_retries=retry_strategy)
			session.mount("http://", adapter)
			session.mount("https://", adapter)

		# Use a proxy if available
		current_proxy = None
		if proxies and attempt < len(proxies):
			proxy_url = proxies[attempt % len(proxies)]
			current_proxy = {"http": proxy_url, "https": proxy_url}
			logger.info(f"Attempt {attempt+1}/{max_retries+1} using proxy: {proxy_url}")

		try:
			response = (session.request if session else requests.request)(
				method=method,
				url=url,
				headers=headers,
				json=payload,
				data=data,
				params=params,
				timeout=timeout,
				proxies=current_proxy
			)

			# If this was the last attempt, return the response anyway
			if attempt > max_retries:
				return response

			if failed_codes and response.status_code in failed_codes:
				logger.warning(f"Request to {url} returned failure status code {response.status_code}, not retrying.")
				return response

			# Handle response based on status codes
			if successful_codes and response.status_code not in successful_codes:
				logger.info(f"Response status code {response.status_code} not in successful codes {successful_codes}. Retrying...")
				continue

			if response.status_code == 200:
				return response

			logger.warning(
				f"Request to {url} returned status code {response.status_code}, Re-Attempting... {attempt+1}/{max_retries+1}"
			)

		except RequestException as e:
			last_exception = e
			logger.warning(f"Request failed with error: {str(e)}. Attempt {attempt+1}/{max_retries+1}")

			# If this was the last attempt, raise the exception
			if attempt >= max_retries:
				break

		# Calculate backoff time with optional randomization
		if attempt < max_retries:
			randomization = random.uniform(0, 1)
			backoff_time = (backoff_factor * (2 ** attempt)) + randomization
			time.sleep(min(backoff_time, 10))  # maximum sleep time of 10 seconds

	# If we got here, all retries failed
	if last_exception:
		raise last_exception
	raise RequestException(f"Max retries ({max_retries}) exceeded for request to {url}")


def get_proxies(service: str = "webshare") -> List[Dict]:
	"""Get a list of proxies from the gateway service."""
	cached_proxies = cache_get(f"proxies_{service}")

	if not cached_proxies:
		headers = {
			"Authorization": f"Bearer {CONFIG.proxy_gateway_api_key}"
		}
		try:
			response = requests.request(
				url=PROXY_GATEWAY_URL,
				method="GET",
				headers=headers,
				params={"service": service},
			)
			proxies = response.json().get('data')
			cache_set(f"proxies_{service}", proxies, ttl_seconds=3600)
			return proxies
		except Exception as e:
			logger.error(f"Failed to fetch proxies from {PROXY_GATEWAY_URL}: {str(e)}")
			return cached_proxies

	return cached_proxies