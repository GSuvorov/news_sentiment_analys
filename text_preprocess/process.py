
from optparse import OptionParser

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

if __name__ == '__main__':
		main()
