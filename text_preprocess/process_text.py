# coding=utf-8
from __future__ import division
import re
import sys
sys.path.append("../util")
sys.path.append("../util/numword/")

import nltk
from nltk import word_tokenize
from nltk import RegexpTokenizer
from nltk.corpus import stopwords
# from util
from mongodb_connector import DBConnector
from numword_ru import NumWordRU

sent_re = r'([\.\?\!]|//)\s*[A-ZА-ЯёЁ]'
percent_re = r'(\d(?:[\.,]\d)\d*\s*%)'
date_re = r"(?P<date>(([12]\d|0[1-9]|3[01]|[1-9])\s+(август|сентябр|октябр|ноябр|декабр|январ|феврал|март|апрел|ма|июн|июл)[а-яА-Я]*))"
dd_mm_yy_re= r'(((0[1-9]|[12]\d|3[01])\.(0[13578]|1[02])\.((19|[2-9]\d)\d{2}))|((0[1-9]|[12]\d|30)\.(0[13456789]|1[012])\.((19|[2-9]\d)\d{2}))|((0[1-9]|1\d|2[0-8])\.02\.((19|[2-9]\d)\d{2}))|(29\.02\.((1[6-9]|[2-9]\d)(0[48]|[2468][048]|[13579][26])|((16|[2468][048]|[3579][26])00))))'
number_re = r'(\-?\d+[\.,]?\d*)'
time_re = r'((?:1?[0-9]|2[0-3]):[0-5][0-9](?::[0-5][0-9])?)'

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
		self.re = [
			{
				'name':		'percent',
				're':		re.compile(percent_re),
				'remove':	True
			},
			{
				'name':		'time',
				're':		re.compile(time_re),
				'remove':	True
			},
			{
				'name':		'date',
				're':		re.compile(date_re),
				'remove':	False
			},
			{
				'name':		'dd_mm_yy',
				're':		re.compile(dd_mm_yy_re),
				'remove':	False
			},
			{
				'name':		'number',
				're':		re.compile(number_re),
				'remove':	True
			}
		]
		self.numword = NumWordRU()

	def split_dash_abbr(self, token):
		pos = token.find('-')
		if pos == -1:
			pos = token.find('—'.decode('utf-8'))
			if pos == -1:
				return [token]

		if pos == 0 and len(token) <= 5:
			return None

		if pos < 3:
			if len(token) - pos - 1 <= 2:
				return None
			else:
				return token[pos + 1:]

		if token[:pos].isdigit() and token[pos + 1:].isdigit():
			return [token[:pos], token[pos + 1:]]

		if pos > 4 and len(token) - pos - 1 >= 4:
			return [token]

		if len(token) == pos + 1:
			return token[:pos]

		if len(token) - pos - 1 <= 2:
			if pos < 2:
				return None
			else:
				return [token[:pos]]

		return [token[:pos], token[pos + 1:]]

	def __numb_to_word__(self, string):
		number_str = string.replace(',', '.')
		try:
			index = number_str.index('.')
			if index != -1 and (len(number_str) - 4 - index) > 0:
				number_str = number_str[: - (len(number_str) - 4 - index)]
		except:
			index = -1

		return self.numword.cardinal(float(number_str))

	# XXX: extract features as dates: date / dd_mm_yy
	def __split_by_regexp__(self, re, string, feature, name, remove=True):
		tokens = []
		prev = 0
		for m in re.finditer(string):
			if name == 'date':
				m_start = m.start('date')
				m_end = m.end('date')

				date = string[m.start('date') : m.end('date')]
				#print "TEST: detected date {}".format(date)
			else:
				m_start = m.start()
				m_end = m.end()

			if name not in feature.keys():
				feature[name] = 1
			else:
				feature[name] += 1

			if remove == True or \
			   name == 'number' or name == 'percent' or name == 'time':
				if m_start > 0 and len(tokens) == 0:
					tokens.append(string[:m_start])
				else:
					tokens.append(string[prev : m_start])

				prev = m_end

			# convert number to word
			if name == 'number':
				try:
					#print "TEST: process number {}".format(string[m_start : m_end])
					number_str = self.__numb_to_word__(string[m_start : m_end])
					tokens.append(number_str.encode('utf-8'))
				except Exception as e:
					print "ERR: failed to convert {} to float: {}".format(string[m_start : m_end], e)

			# remove '%' and convert number to word
			if name == 'percent':
				#print "TEST: process percent {}".format(string[m_start : m_end])
				percent_str = string[m_start : m_end]
				percent_str = percent_str.replace('%', '').strip()
				try:
					percent_str = self.__numb_to_word__(percent_str)
					tokens.append(percent_str.encode('utf-8') + ' процент ')
				except Exception as e:
					print "ERR: failed to convert {} to float: {}".format(string[m_start : m_end], e)

			if name == 'time':
				#print "TEST: process time {}".format(string[m_start : m_end])
				times = string[m_start : m_end].strip().split(':')
				try:
					hour = self.numword.cardinal(float(times[0]))
					mins = self.numword.cardinal(float(times[1]))
					time_str = hour.encode('utf-8') + ' час ' + mins.encode('utf-8') + ' минута '
					if len(times) == 3:
						secs = self.numword.cardinal(float(times[2]))
						time_str += secs.encode('utf-8') + ' секунда '
					tokens.append(time_str)
				except Exception as e:
					print "ERR: failed to convert {} to time: {}".format(string[m_start : m_end], e)

		if remove or len(tokens) > 0:
			if prev < len(string):
				tokens.append(string[prev :])
			return ' '.join(tokens)

		return string

	def split_sent_to_tokens(self, sent, features):
		tokens = []
		pattern = '|'.join(map(re.escape, self.punct))

		# Process regexp and remove some of them
		for r in self.re:
			sent = self.__split_by_regexp__(r['re'], sent, features, r['name'], r['remove'])

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
				elif d not in self.stop_words and len(d) > 1:
					tokens.append(d)

		return tokens

	# TODO: normalization / stemming?
	def split_text_to_sent(self, text, features):
		sentences = []
		start_pos = 0
		text = text.encode('utf-8')
		for m in self.sent_re.finditer(text):
			#print m.group() + ' ' + str(m.start())
			sentences.append(self.split_sent_to_tokens(text[start_pos:m.start()], features))
			start_pos = m.start() + 1

		if start_pos < len(text):
			sentences.append(self.split_sent_to_tokens(text[start_pos:], features))

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
					features[f] = {'text': '', 'feature': {}}

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
						print w.encode('utf-8')

	def preprocess(self):
		texts_features = self.get_texts(1, -1)
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


