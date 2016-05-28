# coding=utf-8
def main():
	fname = 'test_news_db.txt'
	try:
		f = open(fname, 'r')
		results = []
		i = 0

		for line in f.readlines():
			line = line.replace("\n", '')
			index = line.find("Link: ")
			if index != -1:
				i += 1
				results.append([line[index + len("Link: "):]])
				continue

			index = line.find("Ответ: ")
			if index == -1:
				continue

			if len(results[-1]) != 1:
				print "ERR: cannot find  link for text " + str(i)
				del results[-1]
				continue

			try:
				results[-1].append(float((line[index + len("Ответ: "):])))
			except:
				print "ERR: for link {} unable to convert {} to float".format(results[-1][0], line[index + len('Ответ: '):])
				del results[-1]
				continue


		for r in results:
			assert(len(r) == 2)
			print "{}: {}".format(r[0], str(r[1]))

		print "STAT: found {} / {} answers".format(len(results), i)

		f.close()
	except Exception as e:
		print "ERR: " + str(e)

if __name__ == '__main__':
	main()
