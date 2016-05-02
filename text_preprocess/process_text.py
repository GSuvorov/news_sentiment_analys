# coding=utf-8
from __future__ import division
import re
import string
import json
import sys
sys.path.append("../util")
sys.path.append("../util/numword/")
import operator
import time
import datetime

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

# day of the week
week_day = [u'понедельник', u'вторник', u'среда', u'четверг', u'пятница', u'суббота', u'воскресение',
			u'пн', u'пон', u'вт', u'ср', u'чт', u'чет', u'пт', u'пят', u'сб', u'суб', u'вс', u'вос']

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

				if words[0].lower() not in store.keys():
					store[words[0].lower()] = words[1:]
					continue

			f.close()

			if array_like == True:
				return store['all']

			return store
		except Exception as e:
			self.__print__("ERR", str(e))
			return

	def __select_news_agent_info__(self):
		self.news_agent = self.db_cn.select_news_agent()
		if self.news_agent is None:
			self.__print__("ERR", "unable to select news agent info from db")
			sys.exit(1)

		self.subagent = self.db_cn.select_news_subagent()
		if self.subagent is None:
			self.__print__("ERR", "unable to select subagent info from db")
			sys.exit(2)

		#for s in self.subagent.keys():
		#	print "{} -> subtitle {} news_agent {}".format(s, self.subagent[s]['subtitle'].encode('utf-8'),
		#													  self.news_agent[str(self.subagent[s]['news_agent_id'])]['name'].encode('utf-8'))

	def __print__(self, levl, msg):
		if levl == 'DEB' and self.debug == False:
			return

		time_stmp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
		if self.log is None:
			print "[{}]{}: {}".format(time_stmp, levl, msg)
		else:
			self.log.write("[{}]{}: {}\n".format(time_stmp, levl, msg))

	def __init__(self, batch_size=50, debug=False, log=None, data_dir="data", \
				 stop_words="stop_words.txt", punct="punct_symb.txt", sent_end="sentence_end.txt", \
				 abbr="abbr.txt", senti_words="product_senti_rus.txt"):
		self.db_cn = DBConnector()
		self.__select_news_agent_info__()
		self.log = None

		if log != None:
			try:
				self.log = open(log, 'a')
			except Exception as e:
				self.__print__('ERR', str(e))
				sys.exit(1)

		self.iterator = None
		self.batch_size = batch_size
		self.debug = debug
		self.morphy = pymorphy2.MorphAnalyzer()

		self.stop_words = self.__read_from_file__(data_dir + "/" + stop_words)
		#self.stop_words.extend(stopwords.words('russian'))

		# read probably sentiment words
		# going to use them for additional koef for bigramms
		self.senti_words = self.__read_from_file__(data_dir + "/" + senti_words, False)
		for w in self.senti_words.keys():
			self.senti_words[w] = float(self.senti_words[w][0])

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
		self.week_day = week_day

		# found features in all texts
		self.stat = {
			'token stat': {
							'abbr':			0,
							'stop_words':	0,
							'number':		0,
							'date':			0,
							'time':			0,
							'percent':		0,
							'english':		0,
							'punct':		0,
							'senti_words':	0,
							'cnt':	0,
			},
			'bigrams':		0,
			'sentence_cnt':	0,
			'text cnt':		0,
			'average sentence per text': 0,
			'average bigrams per sentence': 0
		}

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

		if pos > 4 and pos <= 6 \
		   and len(token) - pos - 1 >= 4 \
		   and len(token) - pos - 1 <= 6:
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

			if name == 'dd_mm_yy':
				name = 'date'

			if name not in feature.keys():
				feature[name] = 1
			else:
				feature[name] += 1

			if remove == True:
				feature['cnt'] += 1

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
					self.__print__('ERR', "failed to convert {} to float: {}".format(string[m_start : m_end], e))

			# remove '%' and convert number to word
			if name == 'percent' and remove == False:
				#print "TEST: process percent {}".format(string[m_start : m_end])
				percent_str = string[m_start : m_end]
				percent_str = percent_str.replace('%', '').strip()
				try:
					percent_str = self.__numb_to_word__(percent_str)
					tokens.append(percent_str.encode('utf-8') + ' процент ')
				except Exception as e:
					self.__print__('ERR', "failed to convert {} to float: {}".format(string[m_start : m_end], e))

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
					self.__print__('ERR', "failed to convert {} to time: {}".format(string[m_start : m_end], e))

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

		has_senti_words = False
		for t in word_tokenize(sent):
			features['cnt'] += 1

			t = t.lower()
			# remove stop_words
			if t in self.stop_words:
				features['stop_words'] += 1
				continue

			# remove punctuation symbs
			prev_len = len(t)
			t = ''.join(re.split(pattern, t))
			if len(t) < prev_len:
				features['punct'] += prev_len - len(t)
				features['cnt'] += prev_len - len(t)

			if len(t) < 2:
				continue

			# dash abbrs
			dash_tokens = self.split_dash_abbr(t)
			if dash_tokens is None:
				continue

			features['cnt'] += len(dash_tokens)
			# ordinary abbrs
			for d in dash_tokens:
				if d in self.abbr.keys():
					# already normalized
					tokens.extend(self.abbr[d])
					features['abbr'] += 1
					continue

				if d in self.stop_words:
					features['stop_words'] += 1
					continue
				if len(d) <= 1:
					continue

				# normalization
				normalized = self.normalize_word(d)
				if normalized in self.stop_words:
					features['stop_words'] += 1
					continue

				if normalized in self.week_day:
					features['date'] += 1
				elif normalized in self.senti_words:
					features['senti_words'] += 1
					has_senti_words = True

				tokens.append(normalized)

		if len(tokens) <= 1:
			return None

		if has_senti_words:
			features['senti_sentence'] += 1

		bigrams = [' '.join(tokens[i:i+2]) for i in range(len(tokens) - 1)]

		return bigrams

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
				features['sentence_cnt'] += 1
			start_pos = m.start() + 1

		if start_pos < len(text):
			new_sent = self.split_sent_to_tokens(text[start_pos:], features)
			if new_sent != None:
				sentences.append(new_sent)
				features['sentence_cnt'] += 1

		if self.debug is False:
			return sentences

		for s in sentences:
			self.__print__('DEB', "Sent: =========")
			self.__print__('DEB', ' '.join(s).encode('utf-8'))

		if prev_fails < self.failed_to_parse_sentence:
			self.__print__('ERR', "failed to parse {} sentences".format(str(self.failed_to_parse_sentence)))

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
					print "{}".format(i)

				if 'text' not in t.keys():
					self.__print__('ERR', "no text for news")
					continue

				if (len(t['text']) == 0):
					continue

				common_features = {
					'subagent':		None,
					'news_agent':	None,
					'title':		None,
					'text':			None,
					'summary':		None,
					'authors':		None,
					'term':			None,
					'link':			None,
				}

				features_pattern = {
					'subagent':		None,
					'news_agent':	None,
					'title':		None,
					'text':			None,
					'summary':		None,
					'authors':		None,
					'term':			None,
					'link':			None,
					'abbr':			0,
					'stop_words':	0,
					'number':		0,
					'date':			0,
					'time':			0,
					'percent':		0,
					'english':		0,
					'punct':		0,
					'senti_words':	0,
					'senti_sentence': 0,
					'sentence_cnt':	0,
					'cnt':			0,
				}

				features = features_pattern.copy()

				# fill subagent and news agent info
				if 'subagent_id' in t.keys() and \
					str(t['subagent_id']) in self.subagent.keys():
					subagent_id = str(t['subagent_id'])
					features['subagent'] = self.subagent[subagent_id]['subtitle']

					try:
						features['news_agent'] = self.news_agent[str(self.subagent[subagent_id]['news_agent_id'])]['name']
					except:
						self.__print__('ERR', "unknown/empty news agent")
				else:
					self.__print__('ERR', "unknown/empty subagent")

				# fill other features and process text-type objects
				text_is_empty = False
				for f in common_features.keys():
					if f not in t.keys():
						continue

					# TODO: title and summary ?
					# store features only for text
					if f == 'text':
							features[f] = self.split_text_to_sent(t[f], features)
							if len(features[f]) <= 2:
								text_is_empty = True
								break

							# store common stat
							for k in self.stat['token stat'].keys():
								self.stat['token stat'][k] += features[k]
								# normalize parametrs
								if k != 'cnt':
									features[k] = float(features[k]) / features['cnt']

							for s in features[f]:
								self.stat['bigrams'] += len(s)

							self.stat['sentence_cnt'] += features['sentence_cnt']
					else:
						features[f] = t[f]

				if text_is_empty:
					continue

				self.stat['text cnt'] += 1

				if self.debug is True:
						for f in features:
							if type(features[f]) is str:
								self.__print__('DEB', "{} -> {}".format(f, features[f]))
							elif isinstance(features[f], unicode):
								self.__print__('DEB', "{} -> {}".format(f, features[f].encode('utf-8')))
							elif type(features[f]) is int:
								self.__print__('DEB', "{} -> {}".format(f, str(features[f])))
							elif type(features[f]) is float:
								self.__print__('DEB', "{} -> {}".format(f, str(features[f])))
							elif type(features[f]) is list:
								self.__print__('DEB', "{} is list".format(f))
							elif features[f] is None:
								continue
							else:
								self.__print__('ERR', "unknown type " + f)

				all_texts.append(features)

			if i_prev == i:
				break

			start = end + 1

		return all_texts

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
		if self.stat['text cnt'] == 0:
			self.__print__('ERR', "No texts have been analized")
			return

		self.stat['average sentence per text'] = float(self.stat['sentence_cnt']) / self.stat['text cnt']
		self.stat['average bigrams per sentence'] = float(self.stat['bigrams']) / self.stat['sentence_cnt']

		for k in self.stat.keys():
			if type(self.stat[k]) is dict:
				assert(k == 'token stat')
				for sub_k in self.stat[k].keys():
					self.__print__('INF', "{} -> {} / {} ({} %)".format(sub_k, self.stat[k][sub_k], self.stat[k]['cnt'], \
																		float(self.stat[k][sub_k]) / self.stat[k]['cnt']))
				continue

			self.__print__('INF', "{} -> {}".format(k, self.stat[k]))

	def preprocess(self, start_index, end_index):
		texts_features = self.get_texts(start_index, end_index)
		return texts_features

	def store_as_json(self, texts, out_file):
		try:
			f = open(out_file, 'w')
			f.write(json.dumps(texts, indent=4))
			f.close()
		except Exception as e:
			self.__print__('ERR', "unable to store as json: " + str(e))

	def store_into_file(self, filename, batch_size=0):
		ext_index = filename.find('.txt')
		if ext_index != -1:
			filename = filename[:ext_index]
		try:
			f = open(filename + '.txt', 'w')
		except:
			self.__print__('ERR', "unable to open file " + filename)
			return None

		self.__print__('DEB', "start storing texts to '{}'".format(filename))
		start = 0
		end = 0
		i = 0
		text_cnt = 0
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
					self.__print__('INF', "{}".format(i))

				if 'text' not in t.keys():
					self.__print__('ERR', "no text for news")
					continue

				if (len(t['text']) == 0):
					continue

				if batch_size != 0 and i % batch_size == 0:
					f.close()
					new_fname = filename + '_{}.txt'.format(str(i / batch_size)[:-2])
					try:
						f = open(new_fname, 'w')
					except:
						self.__print__('ERR', "unable to open file " + new_fname)
						return None

				f.write("========================\n")
				f.write("Номер текста {}\n".format(str(i)))
				f.write("Link: {}\n".format(t['link'].encode('utf-8')))
				f.write("Тема: {}\n".format(t['title'].encode('utf-8')))
				f.write("Новость:\n")

				text_cnt += 1
				step = 80
				for j in range(0, len(t['text']) , step):
					if j + step >= len(t['text']):
						f.write("{}\n".format(t['text'][j:].encode('utf-8')))
					else:
						f.write("{}\n".format(t['text'][j:j + step].encode('utf-8')))

				f.write("========================\nОтвет: \n")

				print "{}\n".format(str(text_cnt))

			start = end + 1

		f.close()


