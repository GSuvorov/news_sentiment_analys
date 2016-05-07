# coding=utf-8
import codecs
from os import listdir
from os.path import isfile, isdir, join

class LinisTextSentParser():
	def __init__(self):
		# store fisrt n symbols of text and len
		# to detect one more accurance of text
		# struct:
		# text: { 'text': '', 'first_n': n, 'len': n_len, 'sum_senti': n_senti, 'cnt': cnt, 'number_in_file': number }
		self.text_features = []
		self.text_cnt = 0
		self.success_cnt = 0
		self.text_limit = 11000
		self.write_n = 0
		self.start_n_symbs = 700
		self.len_mismatch = 0

	def text_process(self, fname, fname_senti, f_out):
		try:
			f = codecs.open(fname, 'r', encoding='utf-8')
			f_senti = codecs.open(fname_senti, 'r', encoding='utf-8')

			for text in f:
				self.text_cnt += 1
				if self.text_cnt % 100 == 0:
					print "Text number: " + str(self.text_cnt)
				if self.text_cnt > self.text_limit:
					break

				senti = f_senti.readline()
				text_len = len(text)
				try:
					senti = float(senti)
				except:
					continue

				#print "text: {}".format(text[:100].encode('utf-8'))
				start_symbs = len(text)
				if start_symbs > self.start_n_symbs:
					start_symbs = self.start_n_symbs

				found = False
				for t in self.text_features:
					if t['first_n'] != start_symbs:
						continue

					if t['text'] == text[:start_symbs]:
						if text_len != t['len']:
							self.len_mismatch += 1
							print "ERR: mismatch len {} and {} for {}".format(t['len'], text_len, text[:20].encode('utf-8'))
							continue

						found = True
						t['cnt'] += 1
						t['sum_senti'] += senti
						self.success_cnt += 1
						break

				if found == False:
					self.write_n += 1
					self.success_cnt += 1
					f_out.write(text)
					self.text_features.append({
						'text': text[:start_symbs],
						'first_n': start_symbs,
						'len': text_len,
						'cnt': 1,
						'sum_senti': senti,
						'number_in_file': self.write_n
					})

			f.close()
			f_senti.close()
		except Exception as e:
			print str(e)

	def parse_texts(self, data_dir, train, target):
		file_cnt = 0
		failed_cnt = 0

		if isdir(data_dir) == False:
			print "ERR: {}is not directory".format(data_dir)
			return

		try:
			f_out = codecs.open(train, 'w', encoding='utf-8')
			f_target_out = codecs.open(target, 'w', encoding='utf-8')
		except Exception as e:
			print "ERR: {}".format(e)
			return

		for text_file in listdir(data_dir):
			# it is sentiment file
			if text_file.find('texts') == -1:
				continue

			full_fname = join(data_dir, text_file)
			if isfile(full_fname) == False:
				continue

			file_cnt += 1
			sent_file = data_dir + "/" + text_file.replace('texts', 'target')
			if isfile(sent_file) == False:
				failed_cnt +=1
				print "ERR: unable to find target file '{}' for '{}'".format(sent_file, full_fname)
				continue

			print "INF: file pair cnt: {} : process '{}' and '{}'".format(file_cnt, full_fname, sent_file)
			self.text_process(full_fname, sent_file, f_out)

		print "Stat:"
		print "\tfile: processed {}, failed {}".format(file_cnt, failed_cnt)
		print "\ttext:{} / {}".format(self.success_cnt, self.text_cnt)
		print "\tlen mismatch {}".format(self.len_mismatch)
		print "Storing results.."

		write_n = 0
		for t in self.text_features:
			write_n += 1
			if write_n != t['number_in_file']:
				print "ERR: mismatch : expect {} got {}".format(write_n, t['number_in_file'])
				return
			if t['cnt'] > 5:
				print "INF: sum senti {} cnt {}".format(t['sum_senti'], t['cnt'])
			f_target_out.write(str(int(t['sum_senti'] / t['cnt'])) + "\n")

		f_out.close()
		f_target_out.close()

def main():
	data_dir = "texts"
	train = "train.txt"
	target = "target.txt"

	parser = LinisTextSentParser()
	parser.parse_texts(data_dir, train, target)

if __name__ == '__main__':
	main()
