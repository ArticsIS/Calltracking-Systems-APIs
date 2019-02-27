import requests
import hashlib
import json
import time
from datetime import datetime, timedelta

class SCBApi:
	def __init__(self, config):
		self.config = config
		self.__url = 'http://smartcallback.ru/api/v2/'
		self.testAuth()
	def testAuth(self):
		touch_request = self.__requestProto('getDomains', {'client_id': self.config['client_id']})
		self.domains = touch_request.get('data', {})
		if type(self.domains) == dict:
			self.auth_status = 200
			return True
		self.auth_status = 403
		return False
	def endSession(self):
		return True
	def getAuthStatus(self):
		return self.auth_status
	def getDomains(self):
		return self.domains.get('domains') if type(self.domains) == dict else []
	def getBalance(self):
		return self.__requestProto('getBalance', {'client_id': self.config['client_id']})
	def getStatusesList(self):
		return self.__requestProto('StatusesGetList')
	def getQueries(self, domain_id, start_date, end_date=None):
		if type(start_date) != datetime:
			start_date = datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')
		if end_date is None:
			end_date = start_date
		else:
			if type(end_date) != datetime:
				end_date = datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S')
		body = {
			'client_id': self.config['client_id'],
			'date_from': int(time.mktime(start_date.timetuple())),
			'date_to': int(time.mktime(end_date.timetuple())),
			'domen_id': int(domain_id)
		}
		return self.__requestProto('getQueryList', body)
	def getMessengerQueries(self, domain_id, start_date, end_date=None):
		if type(start_date) != datetime:
			start_date = datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')
		if end_date is None:
			end_date = start_date
		else:
			if type(end_date) != datetime:
				end_date = datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S')
		body = {
			'client_id': self.config['client_id'],
			'date_from': int(time.mktime(start_date.timetuple())),
			'date_to': int(time.mktime(end_date.timetuple())),
			'domen_id': int(domain_id)
		}
		return self.__requestProto('getMQueryList', body)
	def captureStats(self, start_date, end_date=None, include_messengers = True, domain_id = None):
		if domain_id is None:
			domain_id = self.config['site_id']
		result = []
		messenger_queries = []
		queries = self.getQueries(domain_id, start_date, end_date)
		queries = queries.get('data', {}).get('queries') if type(queries) != str else []
		if include_messengers:
			messenger_queries = self.getMessengerQueries(domain_id, start_date, end_date)
			messenger_queries = messenger_queries.get('data', {}).get('queries') if type(messenger_queries) != str else []
		return queries + messenger_queries
	def __requestProto(self, method, body={}):
		request_url = '{0!s}{1!s}/'.format(self.__url, method)
		body['apiToken'] = self.config['token']
		body['apiSignature'] = hashlib.md5((''.join([str(v) for v in body.values()]) + str(self.config['signature'])).encode('utf-8')).hexdigest()
		headers = {
			'Content-Type': 'application/json; charset=utf-8'
		}
		request = requests.post(request_url, data=json.dumps(body, ensure_ascii=False).encode('utf8'),headers=headers)
		if request.status_code != 200:
			return {
				'success': False,
				'data': request.text
			}
		try:
			return {
				'success': True,
				'data': json.loads(request.text)['response']
			}
		except Exception as e:
			return {
				'success': True,
				'data': request.text
			}