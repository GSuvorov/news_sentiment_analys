# -*- coding: utf-8 -*-
# coding=utf-8
import re

abbr = {
	'q': "qwerty",
	'hel': "hel full"
}

def split_dash_abbr(token):
		pos = token.find('-')
		if pos == -1:
			return None

		if pos < 2 or pos > 4 or \
		   len(token) - pos - 1 < 2 or len(token) - pos - 1 > 4:
		   return None

		tokens = []
		if token[:pos] in abbr.keys():
			tokens.append(abbr[token[:pos]])
		else:
			tokens.append(token[:pos])

		if token[pos + 1:] in abbr.keys():
			tokens.append(abbr[token[pos + 1:]])
		else:
			tokens.append(token[pos + 1:])

		return tokens

punct = ['?', '!', ',']

def main():
	string = "hel-lo , wiza-vis?? world-!world q-w"

	print string
	pattern = '|'.join(map(re.escape, punct))
	string = ''.join(re.split(pattern, string))
	print string

	for t in string.split():
		print "analys: " + t
		tokens = split_dash_abbr(t)
		if tokens is None:
			print "no"
			continue
		for tok in tokens:
			print tok

if __name__ == '__main__':
		main()
