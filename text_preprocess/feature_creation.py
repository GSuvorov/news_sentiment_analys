from feature_getter import FeatureGetter

def main():
	fg = FeatureGetter(debug=True)

	texts = fg.read_json_texts('res.json')
	features = fg.tfidf_form_features(texts)

	# TODO: add cnt of not found words as feature
	print "Stat"
	fg.print_stat()

	print "unfound words cnt " + str(fg.get_unfound_words_cnt())

if __name__ == '__main__':
	main()


