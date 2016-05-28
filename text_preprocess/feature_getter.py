# coding=utf-8
from __future__ import division
import json
import csv
import sys
import pickle
import math

from logger import Logger
from freq_sent_dict import FreqSentDict

class FeatureGetter(Logger):
	def __init__(self, data_dir="data", log=None, debug=False, \
				dict_obj="FreqSentDictObj", word_vec="word_vec.json", weight_func_type='tfidf'):
		Logger.__init__(self, log, debug)
		self.not_found_words = {}
		self.stat = {
			'not_found': 0,
			'all': 0
		}
		self.doc_cnt = 38369

		if weight_func_type == 'tfidf':
			self.weight_func = FeatureGetter.tfidf_weights
		else:
			self.__print__('ERR', "unknown weight function type ('{}')".format(weight_func_type))

		try:
			f = open(data_dir + '/' + word_vec, 'r')
			self.word_vec = json.load(f)
			f.close()

			index = 0
			for w in self.word_vec.keys():
				self.word_vec[w] = index
				index += 1

			self.__print__('DEB', 'word vec dimension is {}'.format(len(self.word_vec.keys())))

			f = open(data_dir + '/' + dict_obj, 'r')
			self.freq_dict = pickle.load(f)
			f.close()
		except Exception as e:
			self.__print__('ERR', str(e))
			sys.exit(1)

	def read_json_texts(self, fname):
		try:
			f = open(fname, 'r')
			text_feature = json.load(f)
			f.close()
			return text_feature
		except Exception as e:
			print "ERR: unable to create AllSentence object: " + str(e)
			sys.exit(1)

	# values must be an array of dict: [{'feature': value}] 
	def store_as_csv(self, filename, features, values):
		if type(values) != list or type(features) != list:
			self.__print__('ERR', "incorrect arguments")
			return

		try:
			f = open(filename, 'w')

			writer = csv.DictWriter(f, fieldnames=features)
			writer.writeheader()
			[writer.writerow(v) for v in values]

			f.close()
		except Exception as e:
			self.__print__('ERR', "unable to store as csv: " + str(e))

	def get_unfound_words_cnt(self):
		return len(self.not_found_words.keys())

	def print_stat(self):
		for w in self.not_found_words.keys():
			self.__print__('INF', "{} -> {}".format(w.encode('utf-8'), self.not_found_words[w]))

		self.__print__('INF', '===========')
		for k in self.stat.keys():
			if k == 'all':
				self.__print__('INF', "{} -> {}".format(k.encode('utf-8'), self.stat[k]))
			else:
				self.__print__('INF', "{} -> {}".format(k.encode('utf-8'), float(self.stat[k]) / self.stat['all']))

	# text = [ sent: [word] ]
	def tfidf_weights(self, text):
		text_words = {}
		total_words = 0
		for sent in text:
			for word in sent:
				total_words += 1

				if word not in text_words.keys():
					text_words[word] = 1
				else:
					text_words[word] += 1

		for word in text_words.keys():
			docs = self.freq_dict.freq_docs_by_word(word)

			if docs == None:
				del text_words[word]

				if word not in self.not_found_words.keys():
					self.not_found_words[word] = 1
				else:
					self.not_found_words[word] = +1

				self.stat['not_found'] +=1

				continue

			text_words[word] = float(text_words[word]) / total_words * math.log(float(self.doc_cnt) / docs)
			#print "TEST: {} -> {}".format(word.encode('utf-8'), text_words[word])

		self.stat['all'] += total_words

		return text_words

	def text_to_word_vec(self, text):
		word_weights = self.weight_func(self, text)

		word_features = [0] * len(self.word_vec.keys())
		for w in word_weights.keys():
			word_features[self.word_vec[w]] = word_weights[w]

		return word_features

	# features schema = [{'name', 'type'}]
	def form_features(self, features_schema, text_features):
		features = []

		text_index = 0
		# store non-word features according to given
		# features schema
		for t in text_features:
			text_index += 1
			new_feature = []
			if 'text' not in t.keys():
				continue

			# collect given features
			new_feature = []
			for f in features_schema:
				if f['name'] not in t.keys():
					if f['type'] == 'str':
						new_feature.append('')
					else:
						new_feature.append(0)
				else:
					new_feature.append(t[f['name']])

			new_feature.extend(self.text_to_word_vec(t['text']))

			features.append(new_feature)

			# TODO: remove break
			break

		return features

