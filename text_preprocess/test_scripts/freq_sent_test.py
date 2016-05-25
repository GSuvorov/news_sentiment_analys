# coding=utf-8
from freq_senti_dict import FreqSentDict
import pickle

def main():
	obj_name = "FreqSentiDictObj"
	d_obj = FreqSentDict()
	d_obj.serialize(obj_name)
	print "serialized"

	f = open(obj_name, 'r')
	d_s = pickle.load(f)
	f.close()

	print d_s.senti_m_by_word('абонент'.decode('utf-8'))
	print d_s.freq_by_word('абонент'.decode('utf-8'))

if __name__ == '__main__':
	main()
