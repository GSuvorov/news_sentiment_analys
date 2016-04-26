import sys
sys.path.append("../util")
from mongodb_connector import DBConnector

from optparse import OptionParser
from process_text import TextProcess

def parse_options():
		parser = OptionParser()
		parser.add_option("-d", "--debug", dest="debug",
						  help="debug mode", action="store_true")

		(opt, args) = parser.parse_args()
		if opt.debug is None:
			opt.debug = False

		return opt

def main():
		opt = parse_options()
		if opt is None:
				return

		text_p = TextProcess(batch_size=10, debug=opt.debug)
		out_fname = "res.json"

		#text_p.process_from_file("text_from_db.txt")
		#text_p.store_into_file("text_form_db.txt")
		texts = text_p.preprocess(1, -1)
		print "************"
		text_p.get_fixed_word_len(texts, 1, 3)
		print "Storing to " + out_fname
		text_p.store_as_json(texts, out_fname)

if __name__ == '__main__':
		main()
