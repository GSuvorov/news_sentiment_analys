# coding=utf-8
from __future__ import division
import codecs
import pickle
import sys
from optparse import OptionParser
import time

import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.linear_model import LogisticRegression

from text_parser import TextParser

class SentiAnalys(TextParser):
	def __init__(self, debug=False, log=None, data_dir="data", clf_type=None):
		if clf_type is None:
			self.__print__('ERR', 'unable to create SentiAnalys obj: no classificator type')
			sys.exit(1)

		TextParser.__init__(self, debug, log, data_dir)
		self.senti_class = ['нейтральная', 'позитивная', 'негативная']

		if clf_type == 0:
			clf_fname = 'log_clf.model'
		elif clf_type == 1:
			clf_fname = 'xgboost_clf.model'
		else:
			self.__print__('ERR', 'unable to create SentiAnalys obj: incorrect classificator type {}'.format(clf_type))
			sys.exit(1)

		self.clf_type = clf_type
		try:
			clf_f = open(clf_fname, 'r')
			self.clf = pickle.load(clf_f)
			# TODO: check clf type
			clf_f.close()
		except Exception as e:
			self.__print__('ERR', "unable to init SentiAnalys obj: {}".format(e))

	def __predict__(self, pd_data):
		try:
			print pd_data.shape
			if self.clf_type == 0:
				pred = self.clf.predict(pd_data)
			else:
				pred = self.clf.predict_proba(pd_data)

			pred_class = np.argmax(pred, axis=1)

			return {'pred_class': pred_class, 'pred': pred}
		except Exception as e:
			self.__print__('ERR', "unable to classify objects: {}".format(e))
			return None

	def get_class_desc(self):
		return self.senti_class

	def text_senti(self, fname):
		try:
			schema = self.get_schema(as_utf8=True)
			all_features = []

			f = codecs.open(fname, mode='r', encoding='utf-8')

			index = 0
			text = ''
			time_text_all = 0
			for line in f:
				if line[:10] != '==========':
					text = text + line
					continue

				index += 1
				if index % 100 == 0:
					self.__print__('INF', "processed {} texts".format(index))

				print text[:20]
				time_text = time.time()
				features = self.text_to_features(text, as_utf8=True)
				time_text_all += time.time() - time_text

				text = ''
				if features is None:
					self.__print__("WARN", "text {} has no features".format(index))
					continue

				features_arr = []
				for s in schema:
					if s in features.keys() and features[s] != None:
						features_arr.append(float(features[s]))
					else:
						features_arr.append(0)

				all_features.append(features_arr)

			if text != '':
				features = self.text_to_features(text, as_utf8=True)
				if features != None:
					text = ''
					index += 1
					features_arr = []
					for s in schema:
						if s in features.keys() and features[s] != None:
							features_arr.append(float(features[s]))
						else:
							features_arr.append(0)

			self.__print__('DEF', "analysed text {}".format(index))
			self.__print__('DEF', "formed features matrix {} * {}".format(len(all_features), len(schema)))

			pd_data = pd.DataFrame(index=np.arange(0, len(all_features)), columns=schema)
			for x in range(len(all_features)):
				pd_data.loc[x] = np.array(all_features[x])

			pd_data = pd_data.convert_objects(convert_numeric=True)
			self.__print__('DEF', "prediction..")
			time_pred = time.time()
			pred = self.__predict__(pd_data)
			time_pred = time.time() - time_pred

			print "Текстов {}".format(index)
			print "\tВремя предобработки текста: {}".format(float(time_text_all) / index)
			print "\tВремя классификации текста: {}".format(float(time_pred) / index)

			f.close()

			return pred
		except Exception as e:
			self.__print__('ERR', "unable to analys text: " + str(e))
			return None

def parse_options():
		parser = OptionParser()
		parser.add_option("-d", "--debug", dest="debug",
						help=u"режим отладки", action="store_true")
		parser.add_option("-f", "--file", dest="text_file",
						help=u"файл с текстам")
		parser.add_option("-l", "--log", dest="log_file",
						help=u"файл логирования")

		parser.add_option(
						"-t", "--type", dest="clf",
						help=u'Тип класификатора: \
								0 - Logistic regression, \
								1 - XGBoost')

		(opt, args) = parser.parse_args()
		if opt.text_file is None or opt.clf is None or \
			(opt.clf != '0' and opt.clf != '1'):
			parser.print_help()
			return None


		return opt

def main():
	opt = parse_options()
	if opt is None:
			return

	fname = opt.text_file
	flog = opt.log_file
	debug = opt.debug

	sa = SentiAnalys(debug=debug, log=flog, clf_type=int(opt.clf))
	res = sa.text_senti(fname)
	sent_class = sa.get_class_desc()

	if res is None:
		print "Невозможно определить эмоциональный окрас текстов: см лог файл"
		sys.exit(1)

	index = 0
	for i in range(len(res['pred_class'])):
		index += 1
		x = res['pred_class'][i]
		print "Текст: {} эмоциональная окраска: {} " \
				"[вероятность: нейтральный класс {}, позитивный класс {}, негативный класс {}]".format(	index, \
																										sent_class[x], \
																										res['pred'][i][0], \
																										res['pred'][i][1], \
																										res['pred'][i][2])

if __name__ == '__main__':
	main()
