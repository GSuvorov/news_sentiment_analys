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
	def __init__(self, data_dir="data", log=None, debug=False, dict_obj="FreqSentDictObj"):
		Logger.__init__(self, log)
		self.debug = debug
		self.not_found_words = {}
		self.stat = {
			'not_found': 0,
			'all': 0
		}

		try:
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

	def tfidf_form_features(self, text_features):
		doc_cnt = 38369
		tfidf_f = []

		progress_cnt = 0

		for t in text_features:
			if 'text' not in t.keys():
				print "ERR: no text in text + feature list"
				continue

			progress_cnt += 1
			if progress_cnt % 100:
				self.__print__('DEB', progress_cnt)

			text_words = {}
			total_words = 0
			for sent in t['text']:
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

				text_words[word] = float(text_words[word]) / total_words * math.log(float(doc_cnt) / docs)
				#print "TEST: {} -> {}".format(word.encode('utf-8'), text_words[word])

			tfidf_f.append(text_words)
			self.stat['all'] += total_words

		return tfidf_f

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

	# TODO: correct this function
	def form_features(self, text_features):
		exclude_keys = ['text', 'title', 'summary']
		features = []
		sorted_bigrams = self.vocab_bigrams.keys()
		sorted_bigrams.sort()
		text_index = 0
		for t in text_features:
			text_index += 1
			new_feature = {}
			if 'text' not in t.keys():
				continue

			# collect given features
			for f in t.keys():
				if f in exclude_keys:
					continue

				new_feature[f] = t[f]

			# bigram -> freq
			new_feature['bigrams'] = [0] * len(sorted_bigrams)
			text_words = {}
			words_cnt = 0
			for sent in t['text']:
				for b_index in range(len(sent)):
					b = sent[b_index]
					index = sorted_bigrams.index(b)
					if index == -1:
						print "ERR: not found"
						continue

					new_feature['bigrams'][index] += 1
					# words cnt
					if b_index == 0:
						analys_words = b.split()
					else:
						analys_words = [b.split()[1]]

					for w in analys_words:
						if w not in text_words.keys():
							text_words[w] = 1
						else:
							text_words[w] += 1
						words_cnt += 1

			for b_index in range(len(new_feature['bigrams'])):
				if new_feature['bigrams'][b_index] == 0:
					continue

				# tf-idf
				bigrams = sorted_bigrams[b_index].split()

				print "w1 = {} in text {} cnt ;  w2 {} in text cnt {} ;  w_cnt {} doc with w1 {} doc with w2 {}".format(\
						bigrams[0].encode('utf-8'),\
						text_words[bigrams[0]],\
						bigrams[1].encode('utf-8'),\
						text_words[bigrams[1]],\
						words_cnt, self.vocab[bigrams[0]], self.vocab[bigrams[1]])

				tf_idf = float(text_words[bigrams[0]]) / words_cnt * float(self.doc_cnt) / self.vocab[bigrams[0]]

				tf_idf *= float(text_words[bigrams[1]]) / words_cnt * float(self.doc_cnt) / self.vocab[bigrams[1]]

				new_feature['bigrams'][b_index] *= tf_idf

			print "=========="
			print "Text " + str(text_index)
			string = ""
			for freq in new_feature['bigrams']:
				string += " " + str(freq)
			print string

			if text_index == 2:
				return


