# coding=utf-8
from __future__ import division
import re
import string
import sys
sys.path.append("../util")
sys.path.append("../util/numword/")
import operator

import nltk
from nltk import word_tokenize
from nltk import RegexpTokenizer
from nltk.corpus import stopwords
import pymorphy2
# from util
from mongodb_connector import DBConnector
from numword_ru import NumWordRU

sent_re = r'([\.\?\!]|//)\s*[A-ZА-ЯёЁ]'
percent_re = r'(\d(?:[\.,]\d)\d*\s*%)'
date_re = r"(?P<date>(([12]\d|0[1-9]|3[01]|[1-9])\s+(август|сентябр|октябр|ноябр|декабр|январ|феврал|март|апрел|ма|июн|июл)[а-яА-Я]*))"
dd_mm_yy_re= r'(((0[1-9]|[12]\d|3[01])\.(0[13578]|1[02])\.((19|[2-9]\d)\d{2}))|((0[1-9]|[12]\d|30)\.(0[13456789]|1[012])\.((19|[2-9]\d)\d{2}))|((0[1-9]|1\d|2[0-8])\.02\.((19|[2-9]\d)\d{2}))|(29\.02\.((1[6-9]|[2-9]\d)(0[48]|[2468][048]|[13579][26])|((16|[2468][048]|[3579][26])00))))'
number_re = r'(\-?\d+[\.,]?\d*)'
time_re = r'((?:1?[0-9]|2[0-3]):[0-5][0-9](?::[0-5][0-9])?)'
english_re = r'([a-zA-Z]+(?:\s+[a-zA-Z]+)*)'

class TextProcess():
	def __read_from_file__(self, filename, array_like=True):
		try:
			store = {}
			f = open(filename, "r")
			for line in f.readlines():
				line.replace("\n", "")
				words = [w.lower().decode('utf-8') for w in line.split()]

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

	def __select_news_agent_info__(self):
		self.news_agent = self.db_cn.select_news_agent()
		if self.news_agent is None:
			print "ERR: unable to select news agent info from db"
			sys.exit(1)

		self.subagent = self.db_cn.select_news_subagent()
		if self.subagent is None:
			print "ERR: unable to select subagent info from db"
			sys.exit(2)

		#for s in self.subagent.keys():
		#	print "{} -> subtitle {} news_agent {}".format(s, self.subagent[s]['subtitle'].encode('utf-8'),
		#													  self.news_agent[str(self.subagent[s]['news_agent_id'])]['name'].encode('utf-8'))

	def __init__(self, batch_size=50, debug=False, data_dir="data", \
				 stop_words="stop_words.txt", punct="punct_symb.txt", sent_end="sentence_end.txt", \
				 abbr="abbr.txt"):
		self.db_cn = DBConnector()
		self.__select_news_agent_info__()

		self.iterator = None
		self.batch_size = batch_size
		self.debug = debug
		self.morphy = pymorphy2.MorphAnalyzer()

		self.stop_words = self.__read_from_file__(data_dir + "/" + stop_words)
		#self.stop_words.extend(stopwords.words('russian'))

		self.punct = self.__read_from_file__(data_dir + "/" + punct)
		self.abbr = self.__read_from_file__(data_dir + "/" + abbr, False)
		for a in self.abbr.keys():
			self.abbr[a] = [self.morphy.parse(word)[0].normal_form for word in self.abbr[a]]

		self.sent_re = re.compile(sent_re)
		self.failed_to_parse_sentence = 0
		self.re = [
			{
				'name':		'english',
				're':		re.compile(english_re),
				'remove':	True
			},
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
				'remove':	True
			},
			{
				'name':		'dd_mm_yy',
				're':		re.compile(dd_mm_yy_re),
				'remove':	True
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
			if name == 'number' and remove == False:
				try:
					#print "TEST: process number {}".format(string[m_start : m_end])
					number_str = self.__numb_to_word__(string[m_start : m_end])
					tokens.append(number_str.encode('utf-8'))
				except Exception as e:
					print "ERR: failed to convert {} to float: {}".format(string[m_start : m_end], e)

			# remove '%' and convert number to word
			if name == 'percent' and remove == False:
				#print "TEST: process percent {}".format(string[m_start : m_end])
				percent_str = string[m_start : m_end]
				percent_str = percent_str.replace('%', '').strip()
				try:
					percent_str = self.__numb_to_word__(percent_str)
					tokens.append(percent_str.encode('utf-8') + ' процент ')
				except Exception as e:
					print "ERR: failed to convert {} to float: {}".format(string[m_start : m_end], e)

			if name == 'time' and remove == False:
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

	def normalize_word(self, word):
		return self.morphy.parse(word)[0].normal_form

	def split_sent_to_tokens(self, sent, features):
		tokens = []
		pattern = '|'.join(map(re.escape, self.punct))

		# Process regexp and remove some of them
		try:
			for r in self.re:
				sent = self.__split_by_regexp__(r['re'], sent, features, r['name'], r['remove'])

			if isinstance(sent, unicode) is False:
				sent = sent.decode('utf-8')
		except:
			self.failed_to_parse_sentence += 1
			return None

		assert(isinstance(sent, unicode) == True)

		for t in word_tokenize(sent):
			t = t.lower()
			# remove stop words
			if t in self.stop_words:
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
					# already normalized
					tokens.extend(self.abbr[d])
				elif d not in self.stop_words and len(d) > 1:
					normalized = self.normalize_word(d)
					if normalized not in self.stop_words:
						tokens.append(normalized)

		return tokens

	def split_text_to_sent(self, text, features):
		sentences = []
		start_pos = 0
		text = text.encode('utf-8')
		prev_fails = self.failed_to_parse_sentence
		for m in self.sent_re.finditer(text):
			#print m.group() + ' ' + str(m.start())
			new_sent = self.split_sent_to_tokens(text[start_pos:m.start()], features)
			if new_sent != None:
				sentences.append(new_sent)
			start_pos = m.start() + 1

		if start_pos < len(text):
			new_sent = self.split_sent_to_tokens(text[start_pos:], features)
			if new_sent != None:
				sentences.append(new_sent)

		if self.debug is False:
			return sentences

		for s in sentences:
			print "DEB: Sent: ========="
			for t in s:
				print t

		if prev_fails < self.failed_to_parse_sentence:
			print "ERR: failed to parse {} sentences".format(str(self.failed_to_parse_sentence))

		return sentences

	def get_texts(self, start, end_limit):
		all_texts = []
		assert(start > 0)
		i =  start - 1
		while (end_limit == -1 or start < end_limit):
			end = start + self.batch_size - 1
			if end > end_limit and end_limit != -1:
				end = end_limit

			if i % 10 == 0:
				print "{} / {}".format(i , end_limit)

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

				features = {
					'subagent': None,
					'news_agent': None,
					'title': None,
					'text': None,
					'summary': None,
					'authors': None,
					'term': None
				}

				# fill subagent and news agent info
				if 'subagent_id' in t.keys() and \
					str(t['subagent_id']) in self.subagent.keys():
					subagent_id = str(t['subagent_id'])
					features['subagent'] = self.subagent[subagent_id]['subtitle'].encode('utf-8')

					try:
						features['news_agent'] = self.news_agent[str(self.subagent[subagent_id]['news_agent_id'])]['name'].encode('utf-8')
					except:
						print "ERR: unknown/empty news agent"
				else:
					print "ERR: unknown/empty subagent"

				# fill other features and process text-type objects
				for f in features.keys():
					if f not in t.keys():
						continue

					if f in ['text', 'title', 'summary']:
						# store features only for text
						if f == 'text':
							features[f] = self.split_text_to_sent(t[f], features)
						else:
							new_features = {}
							features[f] = self.split_text_to_sent(t[f], new_features)
					elif type(t[f]) is str:
						features[f] = t[f]
					elif isinstance(t[f], unicode):
						features[f] = t[f].encode('utf-8')
					else:
						features[f] = t[f]

				#for f in features:
				#	if type(features[f]) is str:
				#		print "{} -> {}".format(f, features[f])
				#	elif type(features[f]) is int:
				#		print "{} -> {}".format(f, str(features[f]))
				#	elif type(features[f]) is list:
				#		print "{} is list".format(f)
				#	elif features[f] is None:
				#		continue
				#	else:
				#		print "ERR: unknown type " + f

				all_texts.append(features)

			if i_prev == i:
				break

			start = end + 1

		return all_texts

	# TODO: remove, use for analys
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
			print w[0].encode('utf-8') + ' ' + str(w[1])

	# TODO: frequency of n-gramms
	def preprocess(self, start_index, end_index):
		texts_features = self.get_texts(start_index, end_index)
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


