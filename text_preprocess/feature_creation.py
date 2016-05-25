from feature_getter import FeatureGetter

def main():
	fg = FeatureGetter(debug=True)

	header = ['f1', 'f2']
	values = [
		{'f1': 'v1', 'f2': 1},
		{'f1': 2, 'f2': 'v1'},
	]

	fg.store_as_csv('test.csv', header, values)
	#texts = fg.read_json_texts('res.json')
	#features = fg.create_features(texts)


if __name__ == '__main__':
	main()


