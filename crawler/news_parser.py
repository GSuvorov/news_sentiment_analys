#!/usr/bin/python
import sys
sys.path.append("../util")

from datetime import datetime, timedelta
import calendar
import feedparser
import time
import re

from config_reader import ConfigReader
from connector import Connector
from mongodb_connector import DBConnector
from html_feed_parser import CutHTML

# from RSS 
class BaseNewsParser:
	def __init__(self, config=None, debug=False):
		self.req_fields = ['title', 'descriprion', 'link']
		self.opt_for_feed = {	'language': "",					\
								'subtitle': "",					\
								'updated': "",					\
								'updated_parsed': "",			}

		self.opt_for_items = {	'published': "",				\
								'published_parsed': "",			\
								'language': "",					\
								'term': {	'field': 'tags',	\
											'sub_field': 'term'},\
								'summary': ""					}
		self.debug = debug

		# Read config parametrs
		config_reader = ConfigReader()
		config_reader.read(config)
		self.rss_urls = config_reader.url_names
		self.freq = config_reader.freq

		# Fields that are needed to be without html tags
		self.text_extr_fields = set()
		self.__set_text_extract_fields__()

		self.cut_html = CutHTML()
		self.cut_html.reset()

		# Connect to db
		self.db_connector = DBConnector(debug=self.debug)

		# News agent name and time mark
		self.news_agent_name = ""
		# + 0000
		self.time_mark = None

	def __set_text_extract_fields__(self):
		text_extr = ['term', 'summary', 'title', 'description', 'subtitle']
		for extr in text_extr:
			self.text_extr_fields.add(extr)

	def __get_text_extr_data__(self, key, source):
		if source is None:
			return ''

		if key in self.text_extr_fields:
			self.cut_html.reset()
			self.cut_html.feed(source)
			if len(self.cut_html.get_data()) != 0:
				return self.cut_html.get_data()
		return source

	def __set_required_fields__(self, news_item, feed, keys):
		for key in keys:
			if key not in feed.keys():
				continue

			news_item[key] = self.__get_text_extr_data__(key, feed[key])

	def __parse_date__(self, date):
		m = re.match(r"(?P<weekday>\w+), (?P<day>\d{1,2}) (?P<month>\w{2,10}) "\
						"(?P<year>\d{4}) (?P<h>\d{2}):(?P<m>\d{2}):(?P<s>\d{2}) "\
						"\+(?P<diff_h>\d{2})(?P<diff_m>\d{2})""", date)
		if m is None:
			print("INF: date='{}' has incorrect format. pass".format(date))
			return None
		converted_time = datetime(year=int(m.group('year')),
								month=list(calendar.month_abbr).index(m.group('month')),
								day=int(m.group('day')), hour=(int(m.group('h'))),
								minute=int(m.group('m')), second=(int(m.group('s'))))
		# to +0000
		converted_time -= timedelta(hours=int(m.group('diff_h')), minutes=int(m.group('diff_m')))
		conv_time_str = converted_time.strftime("%a %b %d %H:%M:%S %Y")
		converted_time = time.strptime(conv_time_str)
		return converted_time

	def __store_parsed_date__(self, news_item, parsed_date_name, date_name):
		if	parsed_date_name not in news_item.keys() and \
			date_name in news_item.keys() and \
			news_item[date_name] != "":
			converted_date = self.__parse_date__(news_item[date_name])
			if converted_date is not None:
				news_item[parsed_date_name] = converted_date

	def __set_opt_fields__(self, news_item, feed, dict_keys):
		for (key, val) in dict_keys.items():
			news_item_data = None
			if val == "":
				if key in feed.keys():
					news_item_data = feed[key]
			elif val['field'] != None:
				if val['field'] not in feed.keys():
					continue

				feed_var = feed[val['field']]
				if isinstance(feed_var, list):
					if len(feed_var) == 0:
						continue
					feed_var = feed_var[0]

				if isinstance(feed_var, dict):
					if val.get('sub_field', None) is None or val['sub_field'] not in feed_var.keys():
						print("ERR: no sub_field in {} or sub_field not in feed".format(val['field']))
						continue

				if isinstance(feed_var, str):
					if val.get('sub_field', None) is not None:
						print("ERR: expect sub_field")
						continue
					news_item_data = feed_var
				else:
					news_item_data = feed_var[val['sub_field']]
			news_item[key] = self.__get_text_extr_data__(key, news_item_data)

		self.__store_parsed_date__(news_item, 'published_parsed', 'published')
		self.__store_parsed_date__(news_item, 'updated_parsed', 'updated')

	def __form_news_list__(self, rss_news):
		# Parse news_agent data 
		news_agent_data = dict()
		self.__set_required_fields__(news_agent_data, rss_news.feed, self.req_fields)
		self.__set_opt_fields__(news_agent_data, rss_news.feed, self.opt_for_feed)

		if self.debug:
			print("Print news.feed")
			for (k, v) in rss_news.feed.items():
				print("{} -> {}".format(k, v))

			print("\nStoring feed info")
			for (k, v) in news_agent_data.items():
				print("{} -> {}".format(k, v))

			print("\nPrint [0] news item:")
			for (k, v) in rss_news.entries[0].items():
				print("{} -> {}".format(k, v))

		# Parse each news item
		news = []
		for n in rss_news.entries:
			news_item = dict()
			self.__set_required_fields__(news_item, n, self.req_fields)
			self.__set_opt_fields__(news_item, n, self.opt_for_items)

			news.append(news_item)

			if self.debug:
				print("\nadding news item: ")
				for (k, v) in news_item.items():
					print("{} -> {}".format(k, v))

		return {'news_agent': news_agent_data,
				'news_items': news}

	def get_feed_list(self, url=None):
		if url is None:
			if self.news_url is None:
				print("ERR: unable to fetch news (no url)")
				return None
			url = self.news_url
		try:
			print("INF: Request RSS from '{}'".format(url))
			rss_news = feedparser.parse(url)
			return self.__form_news_list__(rss_news)
		except Exception as exp:
			print("ERR: {}".format(exp))
			return None

	def filter_by_time(self, news_data, time_mark):
		news_after_date = []
		for n in news_data['news_items']:
			if 'published_parsed' in n.keys():
				if n['published_parsed'] > time_mark:
					if self.debug:
						print("Append news item: {}".format(n['title']))
					news_after_date.append(n)
		return news_after_date

	def __get_article_from_html__(self, news_item, web_page):
		news_item['web_page'] = web_page
		print("INF: html page: {}".format(web_page))

	def fetch_news_by_feed_list(self, news_data):
		conn = Connector()
		for n in news_data['news_items']:
			print("INF: Fetching news page for '{}'".format(n['link']))
			news_item_page = conn.send_req('GET', url=n['link'])
			if news_item_page is None:
				continue

			self.__get_article_from_html__(n, news_item_page.data)

	def __store_news_data__(self, news_data, section_from_config, news_agent_name):
		news_agent_id = self.db_connector.find_or_insert_news_agent(news_agent_name)
		news_data['news_agent']['news_agent_id'] = news_agent_id
		news_subagent_id = self.db_connector.find_or_insert_news_subagent(news_data['news_agent'])

		try:
			for n in news_data['news_items']:
				if	'term' not in n.keys() and \
					section_from_config != "":
					n['term'] = section_from_config
				if 'published' in n.keys():
					if 'published_parsed' in n.keys():
						del n['published']
				n['subagent_id'] = news_subagent_id

				if 'text' in n.keys() and n['text'] != '':
					self.db_connector.insert_news_item(n)
		except:
			print("ERR: couldn't insert all news")

	# XXX: assume that db_connection is established
	def fetch_and_store_news(self, rss_url_info, time_mark):
		# Get news items list from rss 
		news_data = self.get_feed_list(rss_url_info['url'])
		# Filter by time mark
		if time_mark is not None:
			news_data = self.filter_by_time(news_data, time_mark)
		# Fetch web pages for news in list
		self.fetch_news_by_feed_list(news_data)

		# Store news in db
		self.__store_news_data__(news_data, rss_url_info['term'], self.news_agent_name)

	# Fetch feed lists according to config urls
	def fetch_all_feed_lists(self):
		if len(self.rss_urls) == 0:
			print("ERR: unable to fetch all feed lists: no feed lists")
			return -1
		if self.db_connector is None:
			print("ERR: unable to store news items: no db connection")
			return -2

		for rss_url in self.rss_urls:
			self.fetch_and_store_news(rss_url, self.time_mark)
