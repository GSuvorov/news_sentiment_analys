# -*- coding: utf-8 -*-
# coding=utf-8
import re
from nltk.tokenize import RegexpTokenizer

sent_re = r'([\.\?\!]|//)\s*[A-ZА-Я]'
percent_re = r'(\d+\s*%)'
date_re = r"(?P<date>(([12]\d|0[1-9]|3[01]|[1-9])\s+(август|сентябр|октябр|ноябр|декабр|январ|феврал|март|апрел|ма|июн|июл)[а-яА-Я]*))"
ddmmyy_re= r'(((0[1-9]|[12]\d|3[01])\.(0[13578]|1[02])\.((19|[2-9]\d)\d{2}))|((0[1-9]|[12]\d|30)\.(0[13456789]|1[012])\.((19|[2-9]\d)\d{2}))|((0[1-9]|1\d|2[0-8])\.02\.((19|[2-9]\d)\d{2}))|(29\.02\.((1[6-9]|[2-9]\d)(0[48]|[2468][048]|[13579][26])|((16|[2468][048]|[3579][26])00))))'
number_re = r'(\-?\d+[\.,]?\d*)'
time_re = r'((?:1?[0-9]|2[0-3]):[0-5][0-9](?::[0-5][0-9])?)'

def iter_over_re(p, string):
	print string
	for m in p.finditer(string):
		print m.group()
		#print str(m.start()) + ' ' + str(m.end())

def split_by_regexp(re, string, is_date=False):
		tokens = []
		prev = 0
		for m in re.finditer(string):
			if m.start() > 0 and len(tokens) == 0:
				tokens.append(string[:m.start()])
			else:
				tokens.append(string[prev : m.start()])

			prev = m.end()
			if is_date:
				date = string[m.start('date') : m.end('date')]
				print "TEST: " + date
				if len(date.strip().split()) < 2:
					prev = m.start()
					continue

			tokens.append(string[m.start() : m.end()])

		if prev < len(string):
			tokens.append(string[prev :])

		return tokens


def main():
	string = "Встреча стран-производителей нефти, которая должна была начаться в 8:30 мск, задерживается, пишет ТАСС. Это произошло в связи с поступившей в последний момент просьбой от Саудовской Аравии о внесении в соглашение изменений. Как сообщает источник «РИА Новости», встреча может начаться после полудня из-за изменений в программе мероприятия.Как сообщал «Ъ», Эр-Рияд сообщил, что не будет замораживать добычу нефти, если остальные страны-производители, включая Иран, также не ограничат добычу. Ранее Иран отказался от участия в запланированной на воскресенье встрече в катарской Дохе и сообщил, что не планирует замораживать добычу нефти, так как ему необходимо выйти на досанкционный уровень.Подронее о переговорах в Дохе читайте в материале «Ъ» «Переговоры в Дохе займут два часа». Встреча стран-производителей нефти, которая должна была начаться в 8:30 мск, задерживается, пишет ТАСС. Это произошло в связи с изменениями, которые попросила внести в соглашение Саудовская Аравия в последний момент.Как сообщал «Ъ», Эр-Рияд сообщил, что не будет замораживать добычу нефти, если остальные страны-производители, включая Иран, также не ограничат добычу. Ранее Иран отказался от участия в запланированной на воскресенье встрече в катарской Дохе и сообщил, что не планирует замораживать добычу нефти, так как ему необходимо выйти на досанкционный уровень.Подронее о переговорах в Дохе читайте в материале «Ъ» «Переговоры в Дохе займут два часа». Старт встречи в Дохе задержали из-за Саудовской Аравии, потребовавшей внести изменения в соглашение"
	string_percent = "hello every 23 % listener 2% fwe 1 % frwef %"
	string_date = "1 ноябрем fewfw 12 октября fwfe 3августа 34 июля 323 12 35 23"
	string_number = "1 ноябрем fewfw 12 октября fwfe 00:00 3августа 34 июля -12.34 89ddf 18 7fdf 90 12.30 9fer июль 12.11.2016 32.34.20 ada 8:30 24:01 13:89 14:37 5:20:23"

	p = re.compile(sent_re.decode('utf-8'))
	percent = re.compile(percent_re)
	date = re.compile(date_re.decode('utf-8'))
	number = re.compile(number_re)
	ddmmyy = re.compile(ddmmyy_re)
	time = re.compile(time_re)

	#iter_over_re(percent, string_percent.decode('utf-8'))
	iter_over_re(date, string_number.decode('utf-8'))
	#iter_over_re(number, string_number.decode('utf-8'))
	iter_over_re(ddmmyy, string_number.decode('utf-8'))
	iter_over_re(time, string_number.decode('utf-8'))

	print "======"
	for r in split_by_regexp(date, string_number.decode('utf-8'), True):
		print r

if __name__ == '__main__':
		main()
