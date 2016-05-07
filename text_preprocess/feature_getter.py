# coding=utf-8
from __future__ import division
import json

class FeatureGetter():
	def __init__(self, data_dir="data"):
		self.vocab = {}
		self.vocab_bigrams = {}
		self.doc_cnt = 0

		senti_dict = "sentiment_words.csv"
		self.senti_dict = {}

		try:
			f = open(data_dir + "/" + senti_dict, 'rb')
			# schema: "Words";"mean";"dispersion";"average rate";
			self.senti_dict_file = csv.reader(f, delimiter=";", quotechar="\"")

			w_cnt = 0
			for e in self.senti_dict_file:
				w_cnt += 1
				if w_cnt == 1:
					continue
				self.senti_dict[e[0].decode('utf-8')] = [e[1], e[3], e[4]]

			f.close()
		except Exception as e:
			self.__print__('ERR', str(e))
			sys.exit(1)


	def read_json_texts(self, fname):
		try:
			f = open(fname, 'r')
			text_feature = json.load(f)
			f.close()
			return text_feature
		except Exception as e:
			print "ERR: unable to create AllSentence object: " + str(e)
			sys.exit(1)

	def create_features(self, text_features):
		for t in text_features:
			if 'text' not in t.keys():
				print "ERR: no text in text + feature list"
				continue

			self.doc_cnt += 1
			text_words = {}
			for sent in t['text']:
				for bigram in sent:
					for w in bigram.split():
						if w not in text_words.keys():
							text_words[w] = 1
					if bigram not in self.vocab_bigrams.keys():
						self.vocab_bigrams[bigram] = 1
					else:
						self.vocab_bigrams[bigram] += 1

			for w in text_words.keys():
				if w not in self.vocab.keys():
					self.vocab[w] = 1
				else:
					self.vocab[w] += 1

		print "Texts cnt: " + str(self.doc_cnt)
		print "Vocab words: " + str(len(self.vocab.keys()))
		print "Vocab bigrams: " + str(len(self.vocab_bigrams.keys()))

		exclude_keys = ['text', 'title', 'summary']
		features = []
		sorted_bigrams = self.vocab_bigrams.keys()
		sorted_bigrams.sort()
		text_index = 0
		for t in text_features:
			text_index += 1
			new_feature = {}
			if 'text' not in t.keys():
				continue

			# collect given features
			for f in t.keys():
				if f in exclude_keys:
					continue

				new_feature[f] = t[f]

			# bigram -> freq
			new_feature['bigrams'] = [0] * len(sorted_bigrams)
			text_words = {}
			words_cnt = 0
			for sent in t['text']:
				for b_index in range(len(sent)):
					b = sent[b_index]
					index = sorted_bigrams.index(b)
					if index == -1:
						print "ERR: not found"
						continue

					new_feature['bigrams'][index] += 1
					# words cnt
					if b_index == 0:
						analys_words = b.split()
					else:
						analys_words = [b.split()[1]]

					for w in analys_words:
						if w not in text_words.keys():
							text_words[w] = 1
						else:
							text_words[w] += 1
						words_cnt += 1

			for b_index in range(len(new_feature['bigrams'])):
				if new_feature['bigrams'][b_index] == 0:
					continue

				# tf-idf
				bigrams = sorted_bigrams[b_index].split()

				print "w1 = {} in text {} cnt ;  w2 {} in text cnt {} ;  w_cnt {} doc with w1 {} doc with w2 {}".format(\
						bigrams[0].encode('utf-8'),\
						text_words[bigrams[0]],\
						bigrams[1].encode('utf-8'),\
						text_words[bigrams[1]],\
						words_cnt, self.vocab[bigrams[0]], self.vocab[bigrams[1]])

				tf_idf = float(text_words[bigrams[0]]) / words_cnt * float(self.doc_cnt) / self.vocab[bigrams[0]]

				tf_idf *= float(text_words[bigrams[1]]) / words_cnt * float(self.doc_cnt) / self.vocab[bigrams[1]]

				new_feature['bigrams'][b_index] *= tf_idf

			print "=========="
			print "Text " + str(text_index)
			string = ""
			for freq in new_feature['bigrams']:
				string += " " + str(freq)
			print string

			if text_index == 2:
				return


