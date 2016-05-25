# coding=utf-8
from __future__ import division
import csv
import sys
import pickle

class FreqSentDict():
	def __senti_words_load__(self, data_dir, senti_dict):
		self.senti_dict = {}

		# schema: "Words";"mean";"dispersion";"average rate";
		f = open(data_dir + "/" + senti_dict, 'rb')
		senti_dict_file = csv.reader(f, delimiter=";", quotechar="\"")

		w_cnt = 0
		for e in senti_dict_file:
			w_cnt += 1
			if w_cnt == 1:
				continue

			key_w = e[0].decode('utf-8')
			if key_w in self.senti_dict.keys():
				print "ERR: found double accurance of key '{}' in senti dict".format(e[0])
				continue

			self.senti_dict[key_w] = {'M': float(e[1].replace(',', '.')), 'D': float(e[2].replace(',', '.'))}

		f.close()

	def __freq_load__(self, data_dir, freq_dict):
		#schema: Lemma	PoS	Freq(ipm)	R	D	Doc
		# count middle value for double occured words
		self.freq_dict = {}

		f = open(data_dir + "/" + freq_dict, 'rb')
		freq_reader = csv.reader(f, delimiter="\t", quotechar="\"")

		first = True
		progress_cnt = 0
		for e in freq_reader:
			if first is True:
				first = False
				continue

			progress_cnt += 1
			if progress_cnt % 100 == 0:
				print 'DEB: ' + str(progress_cnt)

			key_w = e[0].decode('utf-8')
			if key_w in self.freq_dict.keys():
				self.freq_dict[key_w]['cnt'] += 1
				self.freq_dict[key_w]['FreqD'] += float(e[4].replace(',', '.'))

				freq = float(e[2].replace(',', '.'))
				if self.freq_dict[key_w]['F'] < freq:
					self.freq_dict[key_w]['F'] = freq

			else:
				self.freq_dict[key_w] = {
					'cnt': 1,
					'F': float(e[2].replace(',', '.')),
					'FreqD': float(e[4].replace(',', '.'))
				}

		# normalize D koef
		for e in self.freq_dict.keys():
			self.freq_dict[e]['FreqD'] /= self.freq_dict[e]['cnt']

		f.close()

	def __init__(self, obj=None, data_dir="data", senti="sentiment_words.csv", freq="freqrnc2011.csv"):
		try:
			print "DEB: Loading senti dict '" + senti + "'"
			self.__senti_words_load__(data_dir, senti)
			print "DEB: Loading freq dict '" + freq + "'"
			self.__freq_load__(data_dir, freq)
		except Exception as e:
			print 'ERR: ' + str(e)
			sys.exit(1)

	def serialize(self, fname):
		try:
			f = open(fname, 'w')
			pickle.dump(self, f, pickle.HIGHEST_PROTOCOL)
			f.close()
		except Exception as e:
			print 'ERR: ' + str(e)
			sys.exit(1)

	def senti_m_by_word(self, word):
		if word not in self.senti_dict.keys():
			return None

		return self.senti_dict[word]['M']

	def senti_d_by_word(self, word):
		if word not in self.senti_dict.keys():
			return None

		return self.senti_dict[word]['D']

	def freq_by_word(self, word):
		if word not in self.freq_dict.keys():
			return None

		return self.freq_dict[word]['F']

	def freq_d_by_word(self, word):
		if word not in self.freq_dict.keys():
			return None

		return self.freq_dict[word]['FreqD']
