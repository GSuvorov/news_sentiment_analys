from feature_getter import FeatureGetter

def main():
	fg = FeatureGetter(debug=True)

	# TODO: features schema: export from tokenizer
	feature_schema = {'time': 0,  'punct': 0}

	train_fname = 'res.json'
	target_fname = 'res.target'
	res_fname = 'res_feature.csv'
	fg.store_train_set(feature_schema, train_fname, target_fname, res_fname)

	# TODO: add cnt of not found words as feature
	print "Stat"
	fg.print_stat()

if __name__ == '__main__':
	main()


