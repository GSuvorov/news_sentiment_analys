# coding=utf-8
from __future__ import division
import sys
sys.path.append("../util/numword/")
from numword_ru import NumWordRU

def convert(numw_class, string):
	number_str = string.replace(',', '.')
	try:
		index = number_str.index('.')
		if index != -1 and (len(number_str) - 4 - index) > 0:
			number_str = number_str[: - (len(number_str) - 4 - index)]
	except:
		index = -1

	return numw_class.cardinal(float(number_str))

def main():
	numw_class = NumWordRU()
	#numw_class.inflection_case = u'им,мн,жр'
	print numw_class.cardinal(-12.5)
	print numw_class.cardinal(2016)
	print numw_class.ordinal(1246)
	print convert(numw_class, '53.583802')
	print convert(numw_class, '1234')

if __name__ == '__main__':
	main()
