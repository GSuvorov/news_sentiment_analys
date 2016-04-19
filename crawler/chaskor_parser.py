from news_parser import BaseNewsParser
from bs4 import BeautifulSoup
import re

class ChaskorParser(BaseNewsParser):
	def __init__(self, config='', debug=False):
		super(ChaskorParser, self).__init__(config, debug)

		self.opt_for_items['text'] = {'field': 'yandex_full-text'}
		self.text_extr_fields.add('text')
		self.news_agent_name = "частный корреспондент"

	def __get_article_from_html__(self, news_item, web_page):
		bs = BeautifulSoup(web_page)

		def is_h(tag):
			if	tag.name == 'h1' or tag.name == 'h2' or \
				tag.name == "br" or tag.name == 'p' or \
				tag.name == 'h3' or tag.name == 'h4':
				return True
			return False

		res_tags = bs.find_all(is_h)
		for tag in res_tags:
			print("found tag {} text: {}".format(tag, tag.findAll(text=True)))

		if 'text' in news_item.keys():
			news_item['web_page'] = news_item['text']
			print("INF: chaskor_html page: {}".format(web_page))
			del news_item['text']
			return
		# parse web page
