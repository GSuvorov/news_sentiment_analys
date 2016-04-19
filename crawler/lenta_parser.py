from news_parser import BaseNewsParser
from bs4 import BeautifulSoup

class LentaParser(BaseNewsParser):
	def __init__(self, config='', debug=False):
		super(LentaParser, self).__init__(config, debug)
		self.news_agent_name = "лента"

	def get_article_info(self, bs):
		def is_article_info(tag):
			if	tag.name == 'div' and tag.has_attr("class") and\
				tag.has_attr('itemprop'):
				class_elements = ['b-text', 'clearfix']
				for val in tag["class"]:
					for i, c_el in enumerate(class_elements):
						if val == c_el:
							del class_elements[i]
							break
				if len(class_elements) != 0:
					return False
				if	tag['itemprop'] == 'articleBody':
					return True
			return False
		return  bs.find_all(is_article_info)

	def cut_aside(self, bs, tag_article):
		def is_aside(tag):
			if tag.name == 'aside':
				return True
			return False

		aside_tags = bs.find_all(is_aside)
		aside_text = ""
		for at in aside_tags:
			aside_text += at.get_text()

		return tag_article.get_text().replace(aside_text, "")

	def get_text(self, bs):
		res_tags = self.get_article_info(bs)
		news_item_text = ""
		for tag in res_tags:
			bs_new = BeautifulSoup("<html>" + str(tag) + "</html>")
			news_item_text += self.cut_aside(bs_new, tag)

		return news_item_text

	def get_authors(self, bs):
		def is_author(tag):
			if	tag.name == 'div' and tag.has_attr('class') and \
				tag.has_attr('itemprop'):
				print("itemprop {} class {}".format(tag['itemprop'], tag['class']))
				class_elements = ['b-label__credits']
				for val in tag["class"]:
					for i, c_el in enumerate(class_elements):
						if val == c_el:
							del class_elements[i]
							break
				if len(class_elements) != 0:
					return False
				if	tag['itemprop'] == 'author':
					return True
			return False

		authors = ""
		res_tags = bs.find_all(is_author)
		if len(res_tags) == 0:
			return None

		for tag in res_tags:
			authors += tag.get_text()
		return authors

	def __get_article_from_html__(self, news_item, web_page):
		bs = BeautifulSoup(web_page)

		# XXX: no authors in lenta
		#authors = self.get_authors(bs)
		#if authors != None:
		#	news_item['authors'] = authors
		#	print("authors: {}".format(authors))

		news_item['text'] = self.get_text(bs)
		print("INF: Lenta_html page: {}".format(news_item['text']))
		print("INF: web page {}".format(web_page))

