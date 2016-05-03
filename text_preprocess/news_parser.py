# coding=utf-8
from __future__ import division
import sys
sys.path.append("../util")

from text_parser import TextParser
from mongodb_connector import DBConnector

news_features = {
	'subagent':		None,
	'news_agent':	None,
	'title':		None,
	'text':			None,
	'summary':		None,
	'authors':		None,
	'term':			None,
	'link':			None,
}

class NewsParser(TextParser):
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

	def __init__(self, batch_size=50, debug=False, log=None, data_dir="data", \
				 stop_words="stop_words.txt", punct="punct_symb.txt", sent_end="sentence_end.txt", \
				 abbr="abbr.txt", senti_words="product_senti_rus.txt"):
		TextParser.__init__(self, debug, log, data_dir,\
							stop_words, punct, sent_end, abbr, senti_words)

		self.db_cn = DBConnector()
		self.__select_news_agent_info__()
		self.batch_size = batch_size

	def get_news_texts(self, start, end_limit):
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

				features = {}
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
				for f in news_features.keys():
					if f not in t.keys():
						continue

					if f != 'text':
						features[f] = t[f]
						continue

					# TODO: title and summary ?
					# store features only for text
					new_features = {}
					features['text'] = self.text_to_sent(t['text'], new_features)
					if features['text'] is None:
						text_is_empty = True
						break

					features.update(new_features)

				if text_is_empty:
					continue

				self.stat['text_cnt'] += 1
				all_texts.append(features)

				if self.debug is True:
						self.__print__('DEB', "Text features =============")
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
						self.__print__('DEB', "================")

			if i_prev == i:
				break

			start = end + 1

		return all_texts

	def news_parse(self, start_index, end_index):
		texts_features = self.get_news_texts(start_index, end_index)
		self.compute_final_stat()
		return texts_features

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



