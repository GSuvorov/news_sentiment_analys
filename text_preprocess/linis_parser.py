# coding=utf-8
from __future__ import division
import sys
import csv

from text_parser import TextParser

class LinisParser(TextParser):
	def __init__(self, debug=False, log=None, data_dir="data"):
		# TODO: to config
		TextParser.__init__(self, debug, log, data_dir)
		senti_dict = "sentiment_words.csv"
		self.senti_dict = {}

		try:
			f = open(data_dir + "/" + senti_dict, 'rb')
			# schema: "Words";"mean";"dispersion";"average rate";
			self.senti_dict_file = csv.reader(f, delimiter=";", quotechar="\"")

			w_cnt = 0
			for e in self.senti_dict_file:
				w_cnt += 1
				if w_cnt == 1:
					continue
				print e[0].decode('utf-8') + " " + str(e[3])
				self.senti_dict[e[0].decode('utf-8')] = e[3]

			f.close()
		except Exception as e:
			self.__print__('ERR', str(e))
			sys.exit(1)



