import sys
sys.path.append("../util")
from mongodb_connector import DBConnector

from optparse import OptionParser
from select_text import TextProcess

def parse_options():
		parser = OptionParser()
		parser.add_option("-d", "--debug", dest="debug",
						  help="debug mode", action="store_true")

		(opt, args) = parser.parse_args()
		return opt

def main():
		opt = parse_options()
		if opt is None:
				return

		text_p = TextProcess(batch_size=10)
		text_p.preprocess()

if __name__ == '__main__':
		main()
