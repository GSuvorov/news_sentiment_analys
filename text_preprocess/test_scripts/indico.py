# coding=utf-8
import indicoio

def main():
	indicoio.config.api_key = '123273ff84fe220626891873d499ea07'
	indicoio.config.language = 'russian'

	# results:
	#0.94399955814
	#print indicoio.sentiment('хороший кот', language='russian')
	#0.777086528524
	#print indicoio.sentiment('постановление правительство', language='russian')
	print indicoio.sentiment('хороший', language='russian')
	print indicoio.sentiment('правительство', language='russian')
	print indicoio.sentiment('кот', language='russian')

	return

	res = indicoio.sentiment_hq([
		'хороший кот',
		'постановление правительство',
		'состоятельный оказаться',
		'коррупционный правонарушение',
		'конфликт интерес',
		'первое квартал'
	])

	for r in res:
		print r

if __name__ == '__main__':
	main()
