from feature_getter import FeatureGetter

def main():
	fg = FeatureGetter()
	texts = fg.read_json_texts('res.json')
	features = fg.create_features(texts)


if __name__ == '__main__':
	main()


