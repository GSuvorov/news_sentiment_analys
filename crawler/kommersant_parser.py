from news_parser import BaseNewsParser
from bs4 import BeautifulSoup
import icu
import re

class KommersantParser(BaseNewsParser):
	def __init__(self, config='', debug=False):
		super(KommersantParser, self).__init__(config, debug)
		self.news_agent_name = "коммерсантъ"

	def convert_encoding(self, data, new_coding='UTF-8'):
		coding = icu.CharsetDetector(data).detect().getName()
		print("Detected coding {}".format(coding))
		if new_coding.upper() != coding.upper():
			data =(data.decode(coding)).encode(new_coding)
		return data

	def __find_authors__(self, tag, news_item):
		for val in tag['class']:
			if val == 'document_authors':
				return re.findall(r"[\w]+\.?\s[\w]+", tag.get_text())
		return None

	def __find_intro__(self, tag):
		for t in tag.contents:
			if	t.name == 'span' and \
				t.has_attr('class'):
				for val in t['class']:
					if val == 'b-article__intro':
						return t.get_text()
		return None

	# TODO: add common {name: abbr} dict for news_item.keys()
	def __get_article_from_html__(self, news_item, web_page):
		#web_page = self.convert_encoding(web_page)

		bs = BeautifulSoup(web_page)

		# Find article_info
		def is_article_info(tag):
			if tag.name == 'p' and tag.has_attr('class'):
				for val in tag['class']:
					if val == 'b-article__text':
						return True
			return False
		res_tags = bs.find_all(is_article_info)

		# Set article info
		article_text = ""
		for tag in res_tags:
			authors = self.__find_authors__(tag, news_item)
			if authors is not None:
				print("authors {}".format(authors))
				news_item['authors'] = authors
				continue

			intro = self.__find_intro__(tag)
			if intro is not None:
				print("intro " + intro)
				news_item['intro'] = intro
				continue

			article_text += tag.get_text()

		news_item['text'] = article_text
		print("article_text: {}".format(article_text))
