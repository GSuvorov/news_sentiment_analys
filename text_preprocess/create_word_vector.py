# coding=utf-8
from __future__ import division
import pickle
import json
import sys

from freq_sent_dict import FreqSentDict

def main():
	freq_dict_fname = "data/FreqSentDictObj"
	word_vec_file = "data/word_vec.json"

	try:
		f = open(freq_dict_fname, 'r')
		freq_dict = pickle.load(f)
		f.close()

		fw = open(word_vec_file, 'w')

		word_vec = {}

		print "freq dict processing"
		for w in freq_dict.freq_get_words():
			word_vec[w] = 1

		print "senti dict processing"
		for w in freq_dict.senti_get_words():
			if w not in word_vec.keys():
				word_vec[w] = 1

		json.dump(word_vec, fw)
		fw.close()
	except Exception as e:
		print 'ERR' + str(e)
		sys.exit(1)

if __name__ == '__main__':
	main()

