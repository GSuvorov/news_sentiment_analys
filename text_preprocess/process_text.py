# coding=utf-8
from __future__ import division
import re
import sys
sys.path.append("../util")

import nltk
from nltk import word_tokenize
from nltk.corpus import stopwords
from mongodb_connector import DBConnector

sent_re = r'([\.\?\!]|//)\s*[A-ZА-ЯёЁ]'
percent_re = r'(\d+\s*%)'
date_re = r'((?:(?:[1-2][0-9])|(?:3[0-1])|(?:[1-9]))\s*(?:(?:август)|(?:сентябр)|(?:октябр)|(?:ноябр)|(?:декабр)|(?:январ)|(?:феврал)|(?:март)|(?:апрел)||(?:ма)|(?:июн)|(?:июл)){1}[а-яА-ЯёЁ]*)'
number_re = r'(\-?\d+[\.,]?\d*)'

news_schema = {
	'title':	'text',
	'text':		'text',
	'summary':	'text',
	'term':		'string',
	'authors':	'string'
}

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
						store['all'] = words
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
		self.stop_words.extend(stopwords.words('russian'))

		self.punct = self.__read_from_file__(data_dir + "/" + punct)
		self.abbr = self.__read_from_file__(data_dir + "/" + abbr, False)

		self.sent_re = re.compile(sent_re)
		self.percent_re = re.compile(percent_re)
		self.date_re = re.compile(date_re)
		self.number_re = re.compile(number_re)

	def split_dash_abbr(self, token):
		pos = token.find('-')
		if pos == -1:
			return [token]

		if pos == 1 and len(token) == 3:
			return None

		if token[:pos].isdigit() and token[pos + 1:].isdigit():
			return [token[:pos], token[pos + 1:]]

		if pos < 2 or pos > 4 or len(token) - pos - 1 < 2 or len(token) - pos - 1 > 4:
			return [token]

		return [token[:pos], token[pos + 1:]]

	def split_sent_to_tokens(self, sent):
		tokens = []
		pattern = '|'.join(map(re.escape, self.punct))
		for t in word_tokenize(sent.decode('utf-8')):
			t = t.lower()
			# remove stop words
			if  t in self.stop_words:
				continue

			# remove punctuation symbs
			t = ''.join(re.split(pattern, t))

			if len(t) < 2:
				continue

			# dash abbrs
			dash_tokens = self.split_dash_abbr(t)
			if dash_tokens is None:
				continue

			# ordinary abbrs
			for d in dash_tokens:
				if d in self.abbr.keys():
					tokens.extend(self.abbr[d])
				else:
					tokens.append(d)

		return tokens

	# TODO: convert numbers to words
	# TODO: feature extraction: numbers, percents, dates
	# TODO: normalization / stemming?
	def split_text_to_sent(self, text, features):
		sentences = []
		start_pos = 0
		text = text.encode('utf-8')
		for m in self.sent_re.finditer(text):
			#print m.group() + ' ' + str(m.start())
			sentences.append(self.split_sent_to_tokens(text[start_pos:m.start()]))
			start_pos = m.start() + 1

		if start_pos < len(text):
			sentences.append(self.split_sent_to_tokens(text[start_pos:]))

		if self.debug is False:
			return sentences

		for s in sentences:
			print "DEB: Sent: ========="
			for t in s:
				print t

		return sentences

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

				features = {}
				for f in news_schema.keys():
					features[f] = {'text': '', 'feature': ''}

					if f not in t.keys():
						continue

					if news_schema[f] == 'text':
						features[f]['text'] = self.split_text_to_sent(t[f], features[f]['feature'])
					elif news_schema[f] == 'string':
						features[f]['text'] = t[f]

				all_texts.append(features)

			if i_prev == i:
				break

			start = end + 1

		return all_texts

	# TODO: remove, use for analys
	def get_fixed_word_len(self, texts_features, low_len, up_len):
		for text_f in texts_features:
			for sent in text_f['text']['text']:
				for w in sent:
					if len(w) <= up_len and len(w) >= low_len:
						print w

	def preprocess(self):
		texts_features = self.get_texts(1, 5)
		return texts_features

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


