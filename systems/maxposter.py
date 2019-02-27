from datetime import datetime, timedelta
import requests
import logging
import json
import base64

class MaxposterApi:
	def __init__(self, config, project_key, zone = '+03:00'):
		self.config = config
		self.project_key = project_key
		self.zone_str = zone
		self.__url = 'https://api.maxposter.ru/partners-api'
		self.__token = base64.b64encode(bytes('{0!s}:{1!s}'.format(self.config['login'], self.config['token']),'utf-8')).decode()
		self.__request_headers = {
			'Content-Type': 'application/json; charset=utf-8',
			'Authorization': 'Basic {0!s}'.format(self.__token)
		}
		self.testAuth()
	def testAuth(self, simulate = True):
		if not simulate:
			request = requests.get(
				'{0!s}/directories/call-sources.json'.format(self.__url),
				data = json.dumps({ 'limit': 10, 'offset': 0, 'orders': ['-id']}, ensure_ascii=False),
				headers = self.__request_headers
			)
			try:
				response = json.loads(request.text)
			except Exception as e:
				logging.error('MP: PARSE: ERROR: {1!s} :{0!s}'.format(str(e), request.text))
				raise Exception('Auth Failed')
			if request.status_code != 200 or response.get('status', '') == 'error':
				self.auth_status = 403
				logging.error('MP : AUTH : ERROR :{0!s}'.format(response.get('message')))
				raise Exception('Auth Failed')
		self.auth_status = 200
		return True
	def endSession(self):
		return True
	def getAuthStatus(self):
		return self.auth_status
	def captureStats(self, start_date, end_date=None):
		if type(start_date) != datetime:
			start_date = datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')
		if end_date is None:
			end_date = datetime.now()
		else:
			if type(end_date) != datetime:
				end_date = datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S')
		result = []
		limit = 100
		results_len = 1
		offset = 0
		while offset < results_len:
			body = {
				'limit': limit,
				'offset': offset,
				'orders': ['-sessionStartedAt'],
				'filters': [{
					'fields': 'sessionStartedAt',
					'type': 'between',
					'value': [start_date.strftime('%Y-%m-%dT%H:%M:%S') + self.zone_str, end_date.strftime('%Y-%m-%dT%H:%M:%S') + self.zone_str]
				}]
			}
			request = requests.post('{0!s}/calls'.format(self.__url), json.dumps(body, ensure_ascii=False), headers = self.__request_headers)
			try:
				response = json.loads(request.text)
			except Exception as e:
				logging.error('MP: PARSE: ERROR: {1!s} : {0!s}'.format(str(e), request.text))
				raise Exception('Bad format')
			if request.status_code != 200 or response.get('status', '') == 'error':
				logging.error('MP : AUTH : ERROR : {0!s}'.format(response.get('message')))
				raise Exception('Query Failed')
			calls = response.get('data', {}).get('calls', [])
			result += calls
			offset = (offset + len(calls)) if len(calls) > 0 else 1
			results_len = int(response.get('data', {}).get('meta', {}).get('range', {}).get('total', '0'))
		return result

