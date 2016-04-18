from __future__ import division
import re
import sys
sys.path.append("../util")

import nltk
from nltk import word_tokenize
from mongodb_connector import DBConnector

#number_re = r'-?(\d+(?[\.,]\d+))';

class TextProcess():
	def __read_from_file__(self, filename, array_like=True):
		try:
			store = {}
			f = open(filename, "r")
			for line in f.readlines():
				line.replace("\n", "")
				words = [w.decode('utf-8').lower() for w in line.split()]

				if array_like == True:
					if 'all' not in store.keys():
						store['all'] = [words]
					else:
						for w in words:
							if w not in store['all']:
								store['all'].append(w)
					continue

				if words[0] not in store.keys():
					store[words[0]] = words[1:]
					continue

			f.close()

			if array_like == True:
				return store['all']

			return store
		except Exception as e:
			print "ERR: {}".format(e)
			return

	def __init__(self, batch_size=50, debug=False, data_dir="data", \
				 stop_words="stop_words.txt", punct="punct_symb.txt", sent_end="sentence_end.txt", \
				 abbr="abbr.txt"):
		self.db_cn = DBConnector()
		self.iterator = None
		self.batch_size = batch_size
		self.debug = debug

		self.stop_words = self.__read_from_file__(data_dir + "/" + stop_words)
		self.punct = self.__read_from_file__(data_dir + "/" + punct)
		self.abbr = self.__read_from_file__(data_dir + "/" + abbr, False)

	def sentence_process(self, sent):
		new_sent = []
		for i in range(len(sent)):
			if sent[i] not in self.abbr.keys() and len(sent[i]) > 0:
				new_sent.append(sent[i])
				continue
			new_sent.extend(self.abbr[sent[i]])

		# TODO: remove all (, ) + punct or 1 symb word
		return new_sent

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
					new_sent.append(self.sentence_process(new_tokens))
					new_tokens = []
					continue

				t = t.lower()
				if  t not in self.stop_words and \
					t not in self.punct:
					new_tokens.append(t)

			new_sent.append(self.sentence_process(new_tokens))

		if self.debug is False:
			return new_sent

		print text
		for s in new_sent:
			print "DEB: Sent: ========="
			for t in s:
				print t

		return new_sent

	def get_texts(self, start, end_limit):
		all_texts = []
		assert(start > 0)
		i =  start - 1
		while (end_limit == -1 or start < end_limit):
			end = start + self.batch_size - 1
			if end > end_limit and end_limit != -1:
				end = end_limit

			t_cursor = self.db_cn.select_news_items(start, end, self.batch_size)
			if t_cursor is None:
				break

			i_prev = i
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

			if i_prev == i:
				break

			start = end + 1

		return all_texts

	# TODO: remove, use for analys
	def get_fixed_word_len(self, texts, low_len, up_len):
		for text in texts:
			for sent in text:
				for w in sent:
					if len(w) <= up_len and len(w) >= low_len:
						print w

	def preprocess(self):
		texts = self.get_texts(1, -1)
		return texts

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


