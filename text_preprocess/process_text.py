from __future__ import division
import re
import sys
sys.path.append("../util")

import nltk
from nltk import word_tokenize
from mongodb_connector import DBConnector

#number_re = r'-?(\d+(?[\.,]\d+))';

class TextProcess():
	def __read_from_file__(self, filename, store):
		try:
			f = open(filename, "r")
			lines = f.readlines()
			for l in lines:
				l.replace("\n", "")
				store.extend([w.lower().decode('utf-8') for w in l.split()])

			f.close()
			return
		except Exception as e:
			print "ERR: {}".format(e)
			return

	def __read_stop_words__(self, stop_words):
		self.stop_words = []
		self.__read_from_file__(stop_words, self.stop_words)

	def __punct_exclude__(self, punct):
		self.punct = []
		self.__read_from_file__(punct, self.punct)

	def __init__(self, batch_size=50, debug=False, data_dir="data", \
				 stop_words="stop_words.txt", punct="punct_symb.txt", sent_end="sentence_end.txt"):
		self.db_cn = DBConnector()
		self.iterator = None
		self.batch_size = batch_size
		self.debug = debug

		self.__read_stop_words__(data_dir + "/" + stop_words)
		self.__punct_exclude__(data_dir + "/" + punct)

	def split_text_to_sent(self, text):
		sent_detector = nltk.data.load('/Users/Kseniya/nltk_data/tokenizers/punkt/polish.pickle')
		sentences = sent_detector.tokenize(text.strip())

		new_sent = []
		for s in sentences:
			tokens = word_tokenize(text)
			new_tokens = []
			# remove stop words
			# remove punctuation symbs
			for t in tokens:
				if t == "//":
					new_sent.append(new_tokens)
					new_tokens = []
					continue

				if  t.lower() not in self.stop_words and \
					t.lower() not in self.punct:
					new_tokens.append(t)

			new_sent.append(new_tokens)

		if self.debug == False:
			return new_sent

		print text
		for s in new_sent:
			print "DEB: Sent: ========="
			for t in s:
				print t.encode('utf-8')

		return new_sent

	def get_texts(self, start, end_limit):
		all_texts = []
		i = start - 1
		while (start < end_limit):
			end = start + self.batch_size - 1
			if end > end_limit:
				end = end_limit

			t_cursor = self.db_cn.select_news_items(start, end, self.batch_size)
			if t_cursor is None:
				break

			if i == t_cursor.count():
				break

			for t in t_cursor:
				i += 1
				if self.debug and (i % 100 == 0):
					print "INF: {}".format(i)

				if 'text' not in t.keys():
					print "ERR: no text for news"
					continue

				if (len(t['text']) == 0):
					continue

				all_texts.append(self.split_text_to_sent(t['title']))

			start = end + 1

		return all_texts

	def preprocess(self):
		texts = self.get_texts(2, 4)

	def store_into_file(self, filename):
		try:
			f = open(filename, 'w')
		except:
			print "ERR: unable to open file " + filename
			return None

		if self.debug:
			print "INF: start storing texts to '{}'".format(filename)
		start = 0
		end = 0
		i = 0
		while (True):
			end = start + self.batch_size - 1

			t_cursor = self.db_cn.select_news_items(start, end, self.batch_size)
			if t_cursor is None:
				break

			if i == t_cursor.count():
				break

			for t in t_cursor:
				i += 1
				if self.debug and (i % 100 == 0):
					print "INF: {}".format(i)

				if 'text' not in t.keys():
					print "ERR: no text for news"
					continue

				if (len(t['text']) == 0):
					continue

				t['text'].replace("\n", " ");
				t['text'] += "\n"
				f.write(t['text'].encode('utf-8'))

			start = end + 1

		f.close()


