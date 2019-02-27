# -*- coding: utf-8 -*-

from urllib.parse import urlencode
from random import randint
from datetime import datetime, timedelta
import json
import time
import logging
import requests

class ComagicApi:
	def __init__(self, config, project_key):
		self.config = config
		self.meta = {}
		self.project_key = project_key
		self.__url = 'https://dataapi.uiscom.ru/v2.0'
		self.testAuth()
	def testAuth(self):
		if self.config['auth_flow'] == 'token':
			self.__token = self.config['token']
			self.auth_status = 200
		else:
			data = self.requestProto('login.user', {'login': self.config['login'], 'password': self.config['token']})
			if data is not None:
				self.__token = data['data']['access_token']
				self.auth_status = 200
			else:
				self.auth_status = 403
				logging.error('CM : {0!s} : INIT : ERROR'.format(self.config['site_id']))
	def endSession(self):
		if self.config['auth_flow'] == 'token':
			return True
		exit_event = self.requestProto('logout.user', {})
		return exit_event != None
	def getAuthStatus(self):
		return self.auth_status
	def getMeta(self):
		return self.meta
	def getPartnerIds(self, customer_id=None):
		method = 'get.customer_users'
		params = {
			'fields': ['id', 'login', 'customer_id']
		}
		if customer_id is not None:
			params['user_id'] = customer_id
		return self.requestProto(method, params)
	def getAvailableSites(self, customer_id=None):
		method = 'get.sites'
		params = {
			'fields': ['id', 'domain_name', 'site_key']
		}
		if customer_id is not None:
			params['user_id'] = customer_id
		return self.requestProto(method, params)
	def getTags(self, customer_id=None):
		method = 'get.tags'
		query = {
			'fields': ['id', 'name', 'is_system']
		}
		if customer_id is not None:
			query['customer_id'] = customer_id
		return self.requestProto(method, query)['data']
	def captureStats(self, start_date, end_date=None, customer_id=None):
		if type(start_date) != datetime:
			start_date = datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')
		if end_date is None:
			end_date = datetime.now()
		else:
			if type(end_date) != datetime:
				end_date = datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S')
		result = []
		method = 'get.calls_report'
		params = {
			'limit': 10000,
			'fields': ['start_time', 'communication_id', 'direction', 'communication_number', 'contact_phone_number',
					   'total_duration', 'call_records', 'virtual_phone_number', 'ua_client_id', 'ym_client_id',
					   'entrance_page', 'tags', 'site_id', 'utm_source', 'utm_medium', 'utm_campaign', 'utm_content',
					   'utm_term', 'visitor_type', 'attributes', 'campaign_name', 'campaign_id'],
			'filter': {
				'field': 'site_id',
				'operator': '=',
				'value': int(self.config['site_id'])
			}
		}
		if (end_date - start_date).days >= 90:
			requested_date = start_date
			while True:
				from_date = requested_date
				to_date = requested_date + timedelta(days=45, seconds=1)
				if to_date > end_date:
					to_date = end_date
				params['date_from'] = from_date.strftime('%Y-%m-%d %H:%M:%S')
				params['date_till'] = to_date.strftime('%Y-%m-%d %H:%M:%S')
				response = self.requestProto(method, params)
				if response is not None:
					result += response
				else:
					logging.error('CM : {0!s} : LOAD : NONE : [{1!s};{2!s}]'.format(
						self.config['site_id'], 
						params['date_from'], 
						params['date_till'])
					)
					return None
				time.sleep(.3)
				requested_date = to_date
				if requested_date == end_date:
					break
		else:
			params['date_from'] = start_date.strftime('%Y-%m-%d %H:%M:%S')
			params['date_till'] = end_date.strftime('%Y-%m-%d %H:%M:%S')
			response = self.requestProto(method, params)
			if response is not None:
				return response
			else:
				logging.error('CM : {0!s} : LOAD : NONE : [{1!s};{2!s}]'.format(
					self.config['site_id'], 
					params['date_from'], 
					params['date_till'])
				)
				return None
		return result

	def requestProto(self, method, params, offset=0, limit=10000):
		request_id = randint(1, 1000)
		if method != 'login.user':
			params['access_token'] = self.__token
		if 'get' in method:
			params['offset'] = offset
			params['limit'] = limit
		request_headers = {
			'Content-Type': 'application/json; charset=utf-8'
		}
		query = {
			'jsonrpc': '2.0',
			'id': request_id,
			'method': method,
			'params': params
		}
		request = requests.post(self.__url, headers=request_headers, data=json.dumps(query))
		response = json.loads(request.text)
		if response.get('error', False):
			logging.error('COMAGIC: {0!s}: {1!s}'.format(method, response['error']['message']))
			if response['error']['data']['mnemonic'] == 'limit_exceeded':
				limit_type = response['error']['data']['params']['limit_type']  # day,minute
				reset = response['error']['data']['metadata']['limits'][limit_type + '_reset']
				if int(reset) <= 900:
					logging.warning('sleeping')
					time.sleep(reset)
					return self.requestProto(method, params)
			return None
		else:
			self.metadata = response['result']['metadata']
			if 'get' in method:
				result = response['result']['data']
				if len(result) == 10000:
					result += self.requestProto(method, params, offset=len(result) + 1)
				return result
			else:
				return response['result']
