# -*- coding: utf-8 -*-

from urllib.parse import urlencode
import json
import logging
from datetime import datetime, timedelta
import requests
import sys

class CallkeeperApi:
	def __init__(self, api_key, project_key, timezone=None):
		self.project_key = project_key
		self.timezone = 'Europe/Moscow' if timezone is None else timezone
		self.__token = api_key
		self.__url = 'https://api.callkeeper.ru'
		self.testAuth()
	def testAuth(self):
		touch_request = requests.get('{0!s}/getUserInfo?api_key={1!s}'.format(self.__url, self.__token))
		self.auth_status = touch_request.status_code
		if touch_request.status_code == 200:
			self.user = json.loads(touch_request.text)[0]
		else:
			logging.error('CK : {0!s} : INIT : ERROR : {1!s}'.format(self.project_key, str(touch_request.text)))
			return

		payment_date = datetime.strptime(self.user.get('paid_till')[:-6], '%Y-%m-%dT%H:%M:%S')
		if payment_date <= (datetime.now() + timedelta(days=2)):
			logging.warning('Paid period for this account is about to expire. Expiration date: {0!r}'.format(
				payment_date.strftime('%d %B %Y')))
	def endSession(self):
		return True
	def getAuthStatus(self):
		return self.auth_status
	def captureStats(self, start_date, end_date=None, statuses=[]):
		if type(start_date) == datetime:
			start_date = start_date + timedelta(seconds=1)
		else:
			start_date = datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')
		if end_date is None:
			end_date = datetime.now()
		else:
			if type(end_date) != datetime:
				end_date = datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S')
		query = urlencode({
			'api_key': self.__token,
			'date[from]': start_date.strftime('%Y-%m-%dT%H:%M:%S'),
			'date[to]': end_date.strftime('%Y-%m-%dT%H:%M:%S')
		})
		cmd = 'getCallsCompleted'
		if len(statuses) > 0:
			i = 0
			combined = []
			while i < len(statuses):
				combined.append('/'.join(statuses[i:i + 2]))
				i += 2
			query['statuses'] = ','.join(combined)
			cmd = 'getCallsByStatus'
		request = requests.get('{0!s}{1!s}?{2!s}'.format(self.__url, 'getCallsCompleted', query))
		if request.status_code == 200:
			response = json.loads(request.text)
		else:
			error_message = 'CK : {0!s} : FETCH : ERROR : [{1!s}:{2!s}] : {3!s} '.format(
				self.project_key,
				start_date,
				end_date,
				request.text
			)
			logging.error(error_message)
			sys.exit(error_message)
		return response.get('result', [])
