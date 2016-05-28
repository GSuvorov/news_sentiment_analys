# coding=utf-8
from __future__ import division
import re
import string
import sys
sys.path.append("../util")
sys.path.append("../util/numword/")
#import operator
import time
import datetime

import nltk
from nltk import word_tokenize
import pymorphy2

#from nltk import RegexpTokenizer
#from nltk.corpus import stopwords
# from util
from numword_ru import NumWordRU

sent_re = r'([\.\?\!]|//)\s*[A-ZА-ЯёЁ]'
percent_re = r'(\d(?:[\.,]\d)\d*\s*%)'
date_re = r"(?P<date>(([12]\d|0[1-9]|3[01]|[1-9])\s+(август|сентябр|октябр|ноябр|декабр|январ|феврал|март|апрел|ма|июн|июл)[а-яА-Я]*))"
dd_mm_yy_re= r'(((0[1-9]|[12]\d|3[01])\.(0[13578]|1[02])\.((19|[2-9]\d)\d{2}))|((0[1-9]|[12]\d|30)\.(0[13456789]|1[012])\.((19|[2-9]\d)\d{2}))|((0[1-9]|1\d|2[0-8])\.02\.((19|[2-9]\d)\d{2}))|(29\.02\.((1[6-9]|[2-9]\d)(0[48]|[2468][048]|[13579][26])|((16|[2468][048]|[3579][26])00))))'
number_re = r'(\-?\d+[\.,]?\d*)'
time_re = r'((?:1?[0-9]|2[0-3]):[0-5][0-9](?::[0-5][0-9])?)'
english_re = r'([a-zA-Z]+(?:\s+[a-zA-Z]+)*)'
emotion_punct = ['!', '?', '...']

# day of the week
week_day = [u'понедельник', u'вторник', u'среда', u'четверг', u'пятница', u'суббота', u'воскресение',
			u'пн', u'пон', u'вт', u'ср', u'чт', u'чет', u'пт', u'пят', u'сб', u'суб', u'вс', u'вос']

# token stat schema
token_stat_schema = {
	'abbr':			0,
	'stop_words':	0,
	'number':		0,
	'date':			0,
	'time':			0,
	'percent':		0,
	'english':		0,
	'punct':		0,
	'emotion_punct':0,
	'senti_words':	0,
	'token_cnt':	0,
	'bigram_cnt':	0,
	'sentence_cnt':	0,
	'senti_sentence':	0,
}

# This is a tokenizer class.
# It splits text to sentences, sentence to bigrams
# Removes stop words, punctuation
# Deals with abbriviations
# Detects, stores as features and delete from text:
# dates (XX июля, dd_mm_yy format, week days),
# times, numbers, percents, english words
class Tokenizer():
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

	def __print__(self, levl, msg):
		if levl == 'DEB' and self.debug == False:
			return

		time_stmp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
		if self.log is None:
			print "[{}]{}: {}".format(time_stmp, levl, msg)
		else:
			self.log.write("[{}]{}: {}\n".format(time_stmp, levl, msg))

	def __token_stat_reset__(self):
		for k in self.stat['token_stat'].keys():
			self.stat['token_stat'][k] = 0

	def __init__(self, debug=False, log=None, data_dir="data", \
				 stop_words="stop_words.txt", punct="punct_symb.txt", sent_end="sentence_end.txt", \
				 abbr="abbr.txt", senti_words="product_senti_rus.txt", to_bigram=False):
		if log != None:
			try:
				self.log = open(log, 'a')
			except Exception as e:
				self.__print__('ERR', str(e))
				sys.exit(1)
		else:
			self.log = None

		self.debug = debug
		self.to_bigram = to_bigram
		self.morphy = pymorphy2.MorphAnalyzer()

		self.stop_words = self.__read_from_file__(data_dir + "/" + stop_words)
		#self.stop_words.extend(stopwords.words('russian'))

		# read probably sentiment words
		# going to use them for additional koef for bigramms
		self.senti_words = self.__read_from_file__(data_dir + "/" + senti_words, False)
		for w in self.senti_words.keys():
			self.senti_words[w] = float(self.senti_words[w][0])

		self.emotion_punct = emotion_punct
		self.punct = self.__read_from_file__(data_dir + "/" + punct)
		self.abbr = self.__read_from_file__(data_dir + "/" + abbr, False)
		for a in self.abbr.keys():
			self.abbr[a] = [self.morphy.parse(word)[0].normal_form for word in self.abbr[a]]

		self.week_day = week_day

		self.sent_re = re.compile(sent_re)
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
		# temporary not used
		self.numword = NumWordRU()

		# found features in all texts
		self.stat = {
			'fail': {
				'sentence_parse': 0
			}
		}
		self.stat['token_stat'] = token_stat_schema.copy()

	def get_token_stat_schema(self):
		return token_stat_schema.copy()

	def get_token_stat(self):
		return self.stat['token_stat']

	def __split_dash_abbr__(self, token):
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
	def __split_by_regexp__(self, re, string, name, remove=True):
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

			assert(name in self.stat['token_stat'].keys())
			self.stat['token_stat'][name] += 1

			if remove == True:
				self.stat['token_stat']['token_cnt'] += 1

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

	# single words or bigrams are supproted for now
	def sent_to_ngrams(self, sent, to_bigram):
		tokens = []
		pattern = '|'.join(map(re.escape, self.punct))

		# Process regexp and remove some of them
		try:
			for r in self.re:
				sent = self.__split_by_regexp__(r['re'], sent, r['name'], r['remove'])

			if isinstance(sent, unicode) is False:
				sent = sent.decode('utf-8')
		except:
			self.stat['fail']['sentence_parse'] += 1
			return None

		assert(isinstance(sent, unicode) == True)

		has_senti_words = False
		for t in word_tokenize(sent):
			self.stat['token_stat']['token_cnt'] += 1

			t = t.lower()
			# remove stop_words
			if t in self.stop_words:
				self.stat['token_stat']['stop_words'] += 1
				continue

			# remove punctuation symbs
			prev_len = len(t)
			t = ''.join(re.split(pattern, t))
			if len(t) < prev_len:
				for emotion_p in self.emotion_punct:
					if t.find(emotion_p):
						self.stat['token_stat']['emotion_punct'] += 1
				self.stat['token_stat']['punct'] += prev_len - len(t)
				self.stat['token_stat']['token_cnt'] += prev_len - len(t)

			if len(t) < 2:
				continue

			# dash abbrs
			dash_tokens = self.__split_dash_abbr__(t)
			if dash_tokens is None:
				continue

			self.stat['token_stat']['token_cnt'] += len(dash_tokens)
			# ordinary abbrs
			for d in dash_tokens:
				if d in self.abbr.keys():
					# already normalized
					tokens.extend(self.abbr[d])
					self.stat['token_stat']['abbr'] += 1
					continue

				if d in self.stop_words:
					self.stat['token_stat']['stop_words'] += 1
					continue
				if len(d) <= 1:
					continue

				# normalization
				normalized = self.normalize_word(d)
				if normalized in self.stop_words:
					self.stat['token_stat']['stop_words'] += 1
					continue

				if normalized in self.week_day:
					self.stat['token_stat']['date'] += 1
				elif normalized in self.senti_words:
					self.stat['token_stat']['senti_words'] += 1
					has_senti_words = True

				tokens.append(normalized)

		if len(tokens) <= 1:
			return None

		birgams = []
		if to_bigram:
			bigrams = [' '.join(tokens[i:i+2]) for i in range(len(tokens) - 1)]
			res_tokens = bigrams
		else:
			res_tokens = tokens

		self.stat['token_stat']['bigram_cnt'] += len(res_tokens)
		self.stat['token_stat']['sentence_cnt'] += 1
		if has_senti_words:
			self.stat['token_stat']['senti_sentence'] += 1

		return res_tokens

	def text_to_sent(self, text):
		sentences = []
		start_pos = 0
		text = text.encode('utf-8')
		prev_fails = self.stat['fail']['sentence_parse']

		# text features reset
		self.__token_stat_reset__()

		for m in self.sent_re.finditer(text):
			new_sent = self.sent_to_ngrams(text[start_pos:m.start()], self.to_bigram)
			if new_sent != None:
				sentences.append(new_sent)
			start_pos = m.start() + 1

		if start_pos < len(text):
			new_sent = self.sent_to_ngrams(text[start_pos:], self.to_bigram)
			if new_sent != None:
				sentences.append(new_sent)

		if self.debug is False:
			return sentences

		for s in sentences:
			self.__print__('DEB', "Sent: =========")
			self.__print__('DEB', ' '.join(s).encode('utf-8'))

		if prev_fails < self.stat['fail']['sentence_parse']:
			self.__print__('ERR', "failed to parse {} sentences".format(str(self.stat['fail']['sentence_parse'])))

		return sentences
