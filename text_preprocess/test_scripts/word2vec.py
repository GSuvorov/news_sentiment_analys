import json
import sys
import gensim
from gensim.models import Word2Vec

# XXX: may process news here! as iterator
class AllSentence(object):
	def __init__(self, fname):
		try:
			f = open(fname, 'r')
			self.text_feature = json.load(f)
			f.close()
		except Exception as e:
			print "ERR: unable to create AllSentence object: " + str(e)
			sys.exit(1)

	def __iter__(self):
		for f in self.text_feature:
			if 'text' not in f.keys():
				continue
			for s in f['text']:
				yield s

def main():
	fname = 'res.json'

	sentences = AllSentence(fname)

	# gensim.models.load('w2vec.model')
	w2v_model = gensim.models.Word2Vec(sentences,
										min_count=5, size=200, workers=4)


	# continue training (info will me
	# w2v_model.train(new_sentences)
	w2v_model.save('w2vec.model')


	#words_set = get_vocabulary(text_feature)


if __name__ == '__main__':
	main()
