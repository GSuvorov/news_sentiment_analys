# coding=utf-8
import sys
import time
import datetime

class Logger():
	def __print__(self, levl, msg):
		if levl == 'DEB' and self.debug == False:
			return

		time_stmp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
		if self.log is None:
			print "[{}]{}: {}".format(time_stmp, levl, msg)
		else:
			self.log.write("[{}]{}: {}\n".format(time_stmp, levl, msg))

	def __init__(self, log=None):
		self.log = log
		if self.log is None:
			return

		try:
			self.log = open(log, 'a')
		except Exception as e:
			self.__print__('ERR', str(e))
			sys.exit(1)

