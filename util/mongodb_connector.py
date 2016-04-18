import pymongo
from pymongo import MongoClient

class DBConnector():
	def __init__(self, host='localhost', port=27017, debug=False):
		self.client = None
		self.debug = debug

		self.__connect__(host, port)
		self.db = self.client.news_db

	def __connect__(self, host, port):
		if self.client is not None:
			self.client.close()
		try:
			self.client = MongoClient(host, port)
			return True
		except pymongo.errors.ConnectionFailure:
			print("ERR: mongodb: connection to db failed")
			return False

	# news_agent collection
	def find_or_insert_news_agent(self, news_agent_name):
		if news_agent_name is None:
			print("ERR: no news agent name")
			return None
		coll_news_agent = self.db.news_agent
		news_agent_doc = coll_news_agent.find_one({'name': news_agent_name.lower()})
		if news_agent_doc is not None:
			print("None")
			return news_agent_doc['_id']

		print("Not found")
		try:
			news_agent_id = coll_news_agent.insert_one({'name': news_agent_name.lower()}).inserted_id
			if self.debug:
				print("INF: news_agent: inserted {}, id = {}".format(news_agent_name, news_agent_id))
			return news_agent_id
		except:
			print("ERR: news_agent: unable to insert news_agent {}".format(news_agent_name))
			return None

	# news_subagent collection
	def find_or_insert_news_subagent(self, news_subagent):
		req_fields = ['link', 'title']
		for r in req_fields:
			if r not in news_subagent.keys():
				print("ERR: new_subagent: {} not in news_agent data".format(r))
				return None

		coll_news_subagent = self.db.news_subagent
		news_subagent_doc = coll_news_subagent.find_one({	'title': news_subagent['title'],
															'link': news_subagent['link']})
		if news_subagent_doc is not None:
			return news_subagent_doc['_id']

		try:
			news_subagent_id = coll_news_subagent.insert_one(news_subagent).inserted_id
			if self.debug:
				print("INF: news_subagent: inserted {} , id = {}".format(news_subagent, news_subagent_id))
			return news_subagent_id
		except:
			print("ERR: news_subagent: unable to insert title={} link={}".format(	news_subagent['title'],
																					news_subagent['link']))
			return None

	# news_item collection
	def insert_news_item(self, news_item):
		if	'title' not in news_item.keys() or \
			'link' not in news_item.keys():
			print("ERR: news_items has to contain 'title' and 'link'")
			return None

		coll_news_item = self.db.news_item
		try:
			news_item_id = coll_news_item.insert_one(news_item).inserted_id
			if self.debug:
				print("INF: news_item: inserted {}, id = {}".format(news_item['title'], news_item_id))
			return news_item_id
		except:
			if self.debug:
				print("INF: news_item: already exist title={} link={}".format(	news_item['title'],
																			news_item['link']))
			return None

	def select_news_items(self, start, end, batch_size):
		if start < 0 or start > end:
			print "ERR: incorrect start index {}".format(start)
			return None

		try:
			cursor = self.db.news_item.find(skip=start, limit=end - start + 1, batch_size=batch_size)
			return cursor
		except Exception as e:
			print "ERR: {}".format(e)
			return None
