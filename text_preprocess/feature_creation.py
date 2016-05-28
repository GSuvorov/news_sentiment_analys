from feature_getter import FeatureGetter

def main():
	fg = FeatureGetter(debug=True)

	# TODO: features schema: export from tokenizer
	feature_schema = [{'name': 'time', 'type': 'int'}, {'name': 'punct', 'type': 'int'}]

	texts = fg.read_json_texts('res.json')
	features = fg.form_features(feature_schema, texts)

	print "features cnt {}".format(len(features[0]))
	i = 0
	for feat in feature_schema:
		print feat['name'] + ' ' + str(features[0][i])
		i += 1

	# TODO: add cnt of not found words as feature
	print "Stat"
	fg.print_stat()

	print "unfound words cnt " + str(fg.get_unfound_words_cnt())

if __name__ == '__main__':
	main()


