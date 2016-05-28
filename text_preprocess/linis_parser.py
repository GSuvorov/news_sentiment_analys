# coding=utf-8
from __future__ import division
import sys
import csv

from text_parser import TextParser

class LinisParser(TextParser):
	def __init__(self, debug=False, log=None, data_dir="data"):
		TextParser.__init__(self, debug, log, data_dir)

	# fname contains texts
	def parse_text_set(self, fname, res_fname):
		try:
			f = open(fname, 'r')

			text_features = []
			for text in f.readline():
				features = {}
				print "process text"
				sentences = self.text_to_sent(text, features)
				features['text'] = sentences
				text_features.append(features)
				break

			f.close()

			print "store as json"
			self.store_as_json(text_features, res_fname)
		except Exception as e:
			self.__print__('ERR', str(e))
			sys.exit(1)

