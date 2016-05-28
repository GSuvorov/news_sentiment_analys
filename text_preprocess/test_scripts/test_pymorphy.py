# coding=utf-8
import pymorphy2

def main():
	m = pymorphy2.MorphAnalyzer()
	for r in m.parse(u'хорошему'):
		print r.normal_form

if __name__ == '__main__':
	main()
