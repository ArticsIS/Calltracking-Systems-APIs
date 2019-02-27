# -*- coding: utf-8 -*-

from urllib.parse import urlencode
import json
import logging
from datetime import datetime, timedelta
import requests
import sys

class CalltouchApi:
	def __init__(self, siteId, api_key, project_key):
		self.siteId = siteId
		self.project_key = project_key
		self.__token = api_key
		self.__node = None
		self.testAuth()
	def testAuth(self):
		node_detect = requests.get('https://api.calltouch.ru/calls-service/RestAPI/{0!s}/getnodeid/'.format(self.siteId))
		self.auth_status = node_detect.status_code
		if node_detect.status_code == 200:
			node = json.loads(node_detect.text)
			self.__node = 'https://api-node{0!s}.calltouch.ru/'.format(node['nodeId'])
		else:
			self.auth_status = 403
		self.url = self.__node + 'calls-service/'
	def endSession(self):
		return True
	def getAuthStatus(self):
		return self.auth_status
	def captureRequests(self, start_date, end_date=None):
		if type(start_date) != datetime:
			start_date = datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')
		if end_date is None:
			end_date = datetime.now()
		else:
			if type(end_date) != datetime:
				end_date = datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S')
		requested_date = start_date
		result = []
		while requested_date <= end_date:
			query = urlencode({
				'clientApiId': self.__token,
				'dateFrom': requested_date.strftime('%d/%m/%Y'),
				'dateTo': requested_date.strftime('%d/%m/%Y'),
				'withRequestTags': 'true'
			})
			request = requests.get('{0!s}calls-service/RestAPI/requests?{1!s}'.format(self.__node, query))
			if request.status_code == 200:
				result += json.loads(request.text)
			else:
				logging.error('CT : {0!s} : {1!s} : ERROR : {2!s}'.format(self.__token, str(self.siteId), error_info))
				return None
			requested_date = requested_date + timedelta(days=1)
		return result
	def captureCalls(self, start_date, end_date=None):
		if type(start_date) != datetime:
			start_date = datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')
		if end_date is None:
			end_date = datetime.now()
		else:
			if type(end_date) != datetime:
				end_date = datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S')
		requested_date = start_date
		result = []
		while requested_date <= end_date:
			query = urlencode({
				'clientApiId': self.__token,
				'dateFrom': requested_date.strftime('%d/%m/%Y'),
				'dateTo': requested_date.strftime('%d/%m/%Y'),
				'withCallTags': 'true'
			})
			request = requests.get('{0!s}calls-service/RestAPI/{1!s}/calls-diary/calls?{2!s}'.format(self.__node, str(self.siteId), query))
			if request.status_code == 200:
				result += json.loads(request.text)
			else:
				logging.error('CT : {0!s} : {1!s} : ERROR : {2!s}'.format(self.__token, str(self.siteId), error_info))
				return None
			requested_date = requested_date + timedelta(days=1)
		return result
	def captureStats(self, start_date, end_date=None):
		return self.captureCalls(start_date, end_date)
		

