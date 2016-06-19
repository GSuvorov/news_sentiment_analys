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
				dict_obj="FreqSentDictObj", word_vec="word_vec.json", weight_func_type='tfidf', range_val=None):
		Logger.__init__(self, log, debug)
		self.not_found_words = {}
		self.stat = {
			'not_found': 0,
			'all': 0
		}
		self.range_val = range_val
		self.doc_cnt = 38369
		self.feature_schema = ['pos_sent', 'neg_sent', 'pos_weight', 'neg_weight']

		if weight_func_type == 'tfidf':
			self.weight_func = FeatureGetter.tfidf_weights
		elif weight_func_type == 'senti_trigram':
			if self.range_val is None:
				self.__print__('ERR', "range val is not setted")
				sys.exit(1)
			self.weight_func = FeatureGetter.senti_freq_weights
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
			self.__print__('ERR', "unable to init: {}".format(str(e)))
			sys.exit(1)

	def stat_reset(self):
		for k in self.stat.keys():
			self.stat[k] = 0

		self.not_found_words.clear()

	def read_json_texts(self, fname):
		try:
			f = open(fname, 'r')
			text_feature = json.load(f)
			f.close()
			return text_feature
		except Exception as e:
			print "ERR: unable to create AllSentence object: " + str(e)
			sys.exit(1)

	# TODO: add unfound words to features
	def get_unfound_words_cnt(self):
		return len(self.not_found_words.keys())

	def get_unfound_percent(self):
		if self.stat['all'] == 0:
			return None

		return float(self.stat['not_found']) / self.stat['all']

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

	def senti_bigram(self, w1_val, w2_val):
		G1 = w1_val['G']
		if G1 == None:
			G1 = 1
		else:
			G1 = float(G1) / 100

		G2 = w2_val['G']
		if G2 == None:
			G2 = 1
		else:
			G2 = float(G2) / 100

		M1 = w1_val['M']
		D1 = w1_val['D']

		M2 = w2_val['M']
		D2 = w2_val['D']

		if M1 == None and M2 == None:
			# undef
			if G1 == 1:
				if G2 == 1:
					return 0
				return G2
			else:
				if G2 == 1:
					return G1
				return G1 * G2

		if M1 == None:
			return M2

		if M2 == None:
			return M1

		if M1 == 0:
			return M2

		if M2 == 0:
			return M1

		if M1 * M2 > 0:
			return float(M1 + M2) / 2

		if D1 == 0:
			D1 = abs(M1)

		if D2 == 0:
			D2 = abs(M2)

		res = M2 * D2 * G1 + M1 * D1 * G2
		res = float(res) / (D1 + D2)

		if M1 > M2:
			M_ = M1
			M1 = M2
			M2 = M_

		res += M1

		return res

	def __get_senti_freq__(self, word):
		M = self.freq_dict.senti_m_by_word(word)
		if M != None:
			D = self.freq_dict.senti_d_by_word(word)
		else:
			D = None

		G = self.freq_dict.freq_d_by_word(word)

		return {'M': M, 'D': D, 'G': G}

	def senti_trigram(self, w1, w2, w3):
		freq_sent_f = []
		empty_w = {'M': None, 'D': None, 'G': 0}

		if w1 != None:
			freq_sent_f.append(self.__get_senti_freq__(w1))
		else:
			freq_sent_f.append(empty_w)

		if w2 != None:
			freq_sent_f.append(self.__get_senti_freq__(w2))
		else:
			freq_sent_f.append(empty_w)

		if w3 != None:
			freq_sent_f.append(self.__get_senti_freq__(w3))
		else:
			freq_sent_f.append(empty_w)

		res = self.senti_bigram(freq_sent_f[0], freq_sent_f[1])
		res += self.senti_bigram(freq_sent_f[1], freq_sent_f[2])

		return res

	def senti_freq_weights(self, text):
		text_words = {}
		text_freq_words = {}
		total_words = 0
		for sent in text:
			for i in range(len(sent)):
				word = sent[i]
				w_prev = None
				w_next = None
				total_words += 1

				docs = self.freq_dict.freq_docs_by_word(word)

				if docs == None:
					if word not in self.not_found_words.keys():
						self.not_found_words[word] = 1
					else:
						self.not_found_words[word] = +1

					self.stat['not_found'] +=1
					continue

				if i != 0:
					w_prev = sent[i - 1]

				if i < (len(sent) - 1):
					w_next = sent[i + 1]

				if word not in text_words.keys():
					text_words[word] = self.senti_trigram(w_prev, word, w_next)
				else:
					text_words[word] += self.senti_trigram(w_prev, word, w_next)

				if word not in text_freq_words.keys():
					text_freq_words[word] = 1
				else:
					text_freq_words[word] += 1

		for word in text_words.keys():
			text_words[word] = float(text_words[word]) / (self.range_val * 2 * text_freq_words[word])
			assert(text_words[word] <= 1)

		return text_words

	def text_to_word_vec(self, text, as_utf8=False):
		text_words = self.weight_func(self, text)

		if as_utf8 == False:
			return text_words

		utf8_text_words = {}
		for w in text_words.keys():
			utf8_text_words[w.encode('utf-8')] = text_words[w]

		return utf8_text_words

	def form_senti_features(self, text):
		features = {
			'pos_sent': 0,
			'pos_weight': 0,
			'neg_sent': 0,
			'neg_weight': 0
		}

		for sent in text:
			sent_pos_weight = 0
			sent_neg_weight = 0

			for w in sent:
				weight = self.freq_dict.senti_m_by_word(w)
				if weight is None or weight == 0:
					continue

				if weight > 0:
					sent_pos_weight += weight
				else:
					sent_neg_weight -= weight

			features['pos_weight'] += sent_pos_weight
			features['neg_weight'] += sent_neg_weight

			if sent_pos_weight == sent_neg_weight:
				continue

			if sent_pos_weight > sent_neg_weight:
				features['pos_sent'] += 1
			else:
				features['neg_sent'] += 1

		features['pos_sent'] = float(features['pos_sent']) / len(text)
		features['neg_sent'] = float(features['neg_sent']) / len(text)

		return features

	# features schema = [(name, type)}]
	def form_features(self, features_schema, text_features, as_utf8=False):
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
			new_feature = {}
			for f in features_schema.keys():
				if f not in t.keys():
					continue
				new_feature[f] = t[f]

			new_feature.extend(self.text_to_word_vec(t['text'], as_utf8))
			new_feature.extend(self.form_senti_features(t['text']))

			features.append(new_feature)
			break

		return features

	def word_vec_senti_features(self, text, as_utf8=False):
		features = {}
		features.update(self.text_to_word_vec(text, as_utf8))
		features.update(self.form_senti_features(text))
		return features

	def get_word_vec_schema(self, as_utf8=False):
		if as_utf8:
			return [w.encode('utf-8') for w in self.word_vec.keys()]

		return self.word_vec.keys()

	def get_senti_schema(self):
		return self.feature_schema

	def get_schema(self, as_utf8=False):
		schema = self.get_senti_schema()
		schema.extend(self.get_word_vec_schema(as_utf8))

		return schema

	def store_train_set(self, feature_schema, train_fname, target_fname, res_fname):
		try:
			f = open(target_fname, 'r')

			target = []
			self.__print__('DEB', "reading targets..")

			for t in f.readline():
				if t == '\n':
					continue

				target.append(float(t))
			f.close()

			self.__print__('DEB', "reading train texts..")
			texts = self.read_json_texts(train_fname)

			# TODO: uncomment
			#assert(len(target) == len(texts))
			self.__print__('DEB', "creating features..")
			features = self.form_features(feature_schema, texts, as_utf8=True)

			features_headers = feature_schema.keys()
			# extend features with pos/neg features
			features_headers.extend(self.feature_schema)
			# store in utf-8 encoding for csv
			features_headers.extend(w.encode('utf-8') for w in self.word_vec.keys())
			features_headers.append('target')

			self.__print__('DEB', "forming schema..")
			for i in range(len(features)):
				features[i].update({'target': target[i]})

			self.__print__('DEB', "storing result as csv..")
			self.store_as_csv(res_fname, features_headers, features)
		except Exception as e:
			self.__print__('ERR', "unable to store train set: {}".format(str(e)))
			sys.exit(1)

