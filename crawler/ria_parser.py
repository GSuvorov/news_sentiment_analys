from news_parser import BaseNewsParser
from bs4 import BeautifulSoup

class RIAParser(BaseNewsParser):
	def __init__(self, config='', debug=False):
		super(RIAParser, self).__init__(config, debug)
		self.news_agent_name = "риа"

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

		print("INF: RIA_html page: {}".format(web_page))

