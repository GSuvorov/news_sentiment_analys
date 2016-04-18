import sys
sys.path.append("../util")
from mongodb_connector import DBConnector

from optparse import OptionParser
from process_text import TextProcess

def parse_options():
		parser = OptionParser()
		parser.add_option("-d", "--debug", dest="debug",
						  help="debug mode", action="store_false")

		(opt, args) = parser.parse_args()
		return opt

def main():
		opt = parse_options()
		if opt is None:
				return

		text_p = TextProcess(batch_size=10, debug=opt.debug)

		#text_p.process_from_file("text_from_db.txt")
		#text_p.store_into_file("text_form_db.txt")
		texts = text_p.preprocess()
		print "************"
		text_p.get_fixed_word_len(texts, 1, 5)

if __name__ == '__main__':
		main()
