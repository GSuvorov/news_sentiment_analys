from nltk.corpus import stopwords

def main():
	for w in stopwords.words('russian'):
		print w


if __name__ == '__main__':
		main()
