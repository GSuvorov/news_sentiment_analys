conn = new Mongo()
db = conn.getDB("news_db")
db.dropDatabase()
db.news_agent.insert({'name': "коммерсантъ"})
db.news_agent.createIndex({'name': 1}, { unique: true })
db.news_agent.insert({'name': "частный корреспондент"})
db.news_agent.insert({'name': "лента"})
db.news_agent.insert({'name': "риа"})

db.createCollection("news_subagent")
db.news_subagent.createIndex({'link': 1, 'title': 1}, { unique : true })

db.createCollection("news_item")
db.news_item.createIndex({'link': 1}, { unique : true })

//db.createCollection("interview")

