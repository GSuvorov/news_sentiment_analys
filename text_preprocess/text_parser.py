# coding=utf-8
from __future__ import division
import json
import sys
import time
import datetime

from tokenizer import Tokenizer
from logger import Logger

class TextParser(Logger):
	def __init__(self, debug=False, log=None, data_dir="data"):
		Logger.__init__(self, log, debug)

		# TODO: to config
		stop_words = "stop_words.txt"
		punct = "punct_symb.txt"
		sent_end = "sentence_end.txt"
		abbr = "abbr.txt"
		senti_words = "product_senti_rus.txt"

		# found features in all texts
		self.stat = {
			'text_cnt':		0,
			'avg_sentence_per_text': 0,
			'avg_bigram_per_sentence': 0
		}

		self.tokenizer = Tokenizer(debug, log, data_dir, stop_words, punct, sent_end, abbr, senti_words)
		self.stat['token_stat'] = self.tokenizer.get_token_stat_schema()

	def compute_final_stat(self):
		if self.stat['text_cnt'] == 0:
			self.__print__('ERR', "No texts have been analized")
			return

		self.stat['avg_sentence_per_text'] = float(self.stat['token_stat']['sentence_cnt']) / self.stat['text_cnt']
		self.stat['avg_bigram_per_sentence'] = float(self.stat['token_stat']['bigram_cnt']) / self.stat['token_stat']['sentence_cnt']

	def text_to_sent(self, text, features):
		# text -> [sentence] , sentence -> [bigram]
		sentences = self.tokenizer.text_to_sent(text)
		if len(sentences) <= 2:
			return None

		# get extracted features
		token_features = self.tokenizer.get_token_stat()

		no_normalization = ['token_cnt', 'bigram_cnt', 'sentence_cnt']
		# store common stat
		for k in self.stat['token_stat'].keys():
			self.stat['token_stat'][k] += token_features[k]
			# normalize parametrs
			if k in no_normalization:
				continue

			division = 'token_cnt'
			if k == 'senti_sentence':
				division = 'sentence_cnt'

			token_features[k] = float(token_features[k]) / token_features[division]

		for k in token_features.keys():
			features[k] = token_features[k]

		return sentences

	# use for analys only
	def get_fixed_word_len(self, texts_features, low_len, up_len):
		words = {}
		for text_f in texts_features:
			for sent in text_f['text']:
				for w in sent:
					if len(w) > up_len or len(w) < low_len:
						continue
					if w in words.keys():
						words[w] += 1
					else:
						words[w] = 1

		words_freq = sorted(words.items(), key=operator.itemgetter(1))
		for w in words_freq:
			self.__print__('INF', w[0].encode('utf-8') + ' ' + str(w[1]))

	def print_stat(self):
		for k in self.stat.keys():
			if type(self.stat[k]) is dict:
				assert(k == 'token_stat')
				for sub_k in self.stat[k].keys():
					self.__print__('INF', "{} -> {} ".format(sub_k, self.stat[k][sub_k]))
				continue

			self.__print__('INF', "{} -> {}".format(k, self.stat[k]))

	def store_as_json(self, texts, out_file):
		try:
			f = open(out_file, 'w')
			f.write(json.dumps(texts, indent=4))
			f.close()
		except Exception as e:
			self.__print__('ERR', "unable to store as json: " + str(e))

