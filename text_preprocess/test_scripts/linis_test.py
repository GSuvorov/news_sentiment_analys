from linis_parser import LinisParser

def main():
	linis_parser = LinisParser(debug=True)

	train_set = "linis_data/train_8000.txt"
	res_fname = "linis.json"

	linis_parser.parse_text_set(train_set, res_fname)


if __name__ == '__main__':
	main()
