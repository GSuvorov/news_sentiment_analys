# coding=utf-8
from inspect import currentframe, getframeinfo
import sys
import time
import datetime

class Logger():
	def __print__(self, levl, msg):
		if levl == 'DEB' and self.debug == False:
			return

		time_stmp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
		if self.log is None:
			if levl == 'ERR':
				frameinfo = getframeinfo(currentframe())
				print "[{}]{}: {}".format(time_stmp, levl, msg, frameinfo.filename, frameinfo.lineno)
			else:
				print "[{}]{}: {}".format(time_stmp, levl, msg)
		else:
			self.log.write("[{}]{}: {}\n".format(time_stmp, levl, msg))

	def __init__(self, log=None, debug=False):
		self.log = log
		self.debug = debug
		if self.log is None:
			return

		try:
			self.log = open(log, 'a')
		except Exception as e:
			self.__print__('ERR', str(e))
			sys.exit(1)

