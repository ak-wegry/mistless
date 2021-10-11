# coding: shift_jis 
# =============================================================================
# �v���O�����E�g���[�X�E�c�[��
# =============================================================================
# [�ύX����]
# Ver0.00  2021/06/05 �쐬�J�n
# Ver1.00  2021/10/11 �V�K�쐬

usage = """
�v���O�����E�g���[�X�E�c�[��  [Ver1.00  2021/10/11]

mistless.py [option] filename ...
   [option]
    -m filename : �^�O�t�@�C���̍쐬
    -t filename : �^�O�t�@�C���̎w��(�w��Ȃ�:tags)
    -x n        : �^�u�X�g�b�v�̎w��(�w��Ȃ�:4)
"""

# import
import os
import sys
import chardet
import locale
import re
import shutil
import math
import unicodedata
from pathlib import Path
from msvcrt import getch
from tkinter import messagebox
## ESC�V�[�P���X�L�����p
from ctypes import windll, wintypes, byref
from functools import reduce

# �Œ�l
MAX_HISTORY = 20	# �R�}���h�����̍ő吔

SCROLL_PAGE = 2	# �����ŃX�N���[���ړ�����O��̃y�[�W��(����ȏ�̓W�����v)

MODE_WORD = 0	# ���[�h�P�ʂ̈ړ�
MODE_CHAE = 1	# �����P�ʂ̈ړ�

DIR_FORWARD = 1	# ������
DIR_REVERSE = 2	# �t����

MORE_CHAR = "$"     # �}���`�o�C�g�������r���œr�؂��ۂ̕\������
TAG_FILE = "tags"   # default�̃^�O�t�@�C����

ESC_PTN       = "\x1b\[[0-9;]*m"	# ESC�V�[�P���X�̃p�^�[��
ESC_INIT      = "\x1b[m"	# �F�̏�����
ESC_REVERSE   = "\x1b[7m"	# ���]
ESC_UNDERLINE = "\x1b[4m"	# ����
ESC_BLACK     = "\x1b[30m"	# �t�H���g:��
ESC_RED       = "\x1b[31m"	# �t�H���g:��
ESC_GREEN     = "\x1b[32m"	# �t�H���g:��
ESC_YELLOW    = "\x1b[33m"	# �t�H���g:���F
ESC_BLUE      = "\x1b[34m"	# �t�H���g:��
ESC_PURPLE    = "\x1b[35m"	# �t�H���g:��
ESC_CYAN      = "\x1b[36m"	# �t�H���g:�V�A��
ESC_WHITE     = "\x1b[37m"	# �t�H���g:��
ESC_BG_BLACK  = "\x1b[40m"	# �w�i�F:��
ESC_BG_RED    = "\x1b[41m"	# �w�i�F:��
ESC_BG_GREEN  = "\x1b[42m"	# �w�i�F:��
ESC_BG_YELLOW = "\x1b[43m"	# �w�i�F:���F
ESC_BG_BLUE   = "\x1b[44m"	# �w�i�F:��
ESC_BG_PURPLE = "\x1b[45m"	# �w�i�F:��
ESC_BG_CYAN   = "\x1b[46m"	# �w�i�F:�V�A��
ESC_BG_WHITE  = "\x1b[47m"	# �w�i�F:��

syntax_list = ()
syntax_list_py = ("break", "continue", "del", "except", "exec", "finally", "pass", "print", "raise", "return", "try", "with", "global", "assert", "lambda", "yield", "def", "class", "for", "while", "if", "elif", "else", "and", "in", "is", "not", "or", "import", "from", "as")	# python��keyword
syntax_list_c = ("void", "char", "short", "int", "long", "float", "double", "auto", "static", "const", "signed", "unsigned", "extern", "volatile", "register", "return", "goto", "if", "else", "switch", "case", "default", "break", "for", "while", "do", "continue", "typedef", "struct", "enum", "union", "sizeof") # C����
syntax_list_cpp = ("new", "delete", "this", "friend", "using", "public", "protected", "private", "inline", "virtual", "explicit", "export", "bool", "wchar_t", "throw", "try", "catch", "operator", "typeid", "and", "bitor", "or", "xor", "compl", "bitand", "and_eq", "or_eq", "xor_eq", "not", "not_eq", "const", "static", "dynamic", "reinterpret", "mutable", "class", "true", "false") + syntax_list_c # C++
syntax_list_awk = ("BEGIN", "END", "if", "else", "while", "for", "do", "contained", "TODO", "break", "continue", "delete", "exit", "function", "getline", "next", "print", "printf", "return", "nextfile", "atan2", "close", "cos", "exp", "fflush", "int", "log", "rand", "sin", "sqrt", "srand", "gsub", "index", "length", "match", "split", "sprintf", "sub", "substr", "system", "asort", "gensub", "mktime", "strftime", "strtonum", "systime", "tolower", "toupper", "and", "or", "xor", "compl", "lshift", "rshift", "dcgettext", "bindtextdomain", "ARGC", "ARGV", "FILENAME", "FNR", "FS", "NF", "NR", "OFMT", "OFS", "ORS", "RLENGTH", "RS", "RSTART", "SUBSEP", "ARGIND", "BINMODE", "CONVFMT", "ENVIRON", "ERRNO", "FIELDWIDTHS", "IGNORECASE", "LINT", "PROCINFO", "RT", "RLENGTH", "TEXTDOMAIN") # awk
syntax_dic = {".py":syntax_list_py, ".c":syntax_list_c, ".cpp": syntax_list_cpp, ".h":syntax_list_cpp, ".awk":syntax_list_awk }

multi_line_ptn = []
multi_line_ptn_py  = ["\"\"\"", "\"\"\"", "\"\"\"", ESC_CYAN]
multi_line_ptn_c   = ["/\*|\*/", "/*", "*/", ESC_BLUE]
multi_line_ptn_cpp = ["(?<!/)/\*|\*/", "/*", "*/", ESC_BLUE]
multi_line_dic ={".py": multi_line_ptn_py, ".c": multi_line_ptn_c, ".cpp":multi_line_ptn_cpp, ".h":multi_line_ptn_cpp}

comment_ptn = ""
comment_ptn_py = "#.*"
comment_ptn_c = "/\*.*?\*/|([^/]|/[^*])*?(\*/)|/\*.*(?<!\*/)$"
comment_ptn_cpp = "/\*.*?\*/|([^/]|/[^*])*?(\*/)|/\*.*(?<!\*/)$|//.*"
comment_ptn_awk = "#.*"
comment_dic = {".py": comment_ptn_py, ".c": comment_ptn_c, ".cpp": comment_ptn_cpp, ".h":comment_ptn_cpp, ".awk":comment_ptn_awk}

quote_ptn = ""
quote_ptn_std = "\"(.*?)(?<!\\\\)\"|\'(.*?)(?<!\\\\)\'"
quote_ptn_py = "\"\"\"|" + quote_ptn_std 
quote_dic = {".py": quote_ptn_py, ".c": quote_ptn_std, ".cpp": quote_ptn_std, ".h":quote_ptn_std, ".awk": quote_ptn_std}


#=== define class ===============================================================
class ParamInfo():
	"""
	�����Ɋւ�����

	Attributes:
		read_files[]  : ���̓t�@�C����
		read_tag_file : ���̓^�O�t�@�C����
		make_tag_file : �o�̓^�O�t�@�C����
		tab_stop      : �^�u�X�g�b�v��
		err_msg       : ��͎��̃G���[���b�Z�[�W
	"""


	def __init__(self):
		self.read_files = []
		self.read_tag_file = ""
		self.make_tag_file = ""
		self.tab_stop = 4
		self.err_msg = ""


	def analyze(self, argv):
		"""
		�����̉��
		Args:
			argv (list): ����

		Returns:
			boolean: True �`�F�b�NOK, False �`�F�b�NNG
		"""
		opt_id = ""
		for arg in argv[1:]:
			if opt_id == "":
				if re.match(r"^-[mtx]$", arg) is not None:
					opt_id = arg
				elif arg[0] == "-":
					self.err_msg = f"�s���ȃI�v�V����({arg})�ł��B"
					break
				else:
					if re.search(r"[*?]", arg) != None:
						path = os.path.dirname(arg)
						file = os.path.basename(arg)
						for pathfile in Path(path).glob(file):
							pathfile = str(pathfile)
							if pathfile not in self.read_files:
								self.read_files.append(pathfile)
					else:
						if Path(arg).exists() == True:
							if arg not in self.read_files:
								self.read_files.append(arg)
						else:
							self.err_msg = f"�t�@�C��({arg})�����݂��܂���B"
							break
			else:
				if opt_id == "-m":
					self.make_tag_file = arg
					opt_id = ""
				elif opt_id == "-t":
					if Path(arg).exists() == True:
						self.read_tag_file = arg
					else:
						self.err_msg = f"�^�O�t�@�C��({arg})�����݂��܂���B"
						break
					opt_id = ""
				elif opt_id == "-x":
					self.tab_stop = int(arg)
					opt_id = ""

		return (self.err_msg == "")


class Escape():
	"""
	ESC�R�[�h�̐ݒ�Ɋւ��鏈��

	Attributes:
		only_text : ESC�R�[�h�����O����������
		esc_list  : 1�������ɑΉ�����ESC�R�[�h
	"""

	def __init__(self):
		self.only_text= ""	# ESC�R�[�h�����O����������
		self.esc_list = []	# 1�������ɑΉ�����ESC�R�[�h

	def analyze_text(self, esc_text):
		# ESC���O����������A[�ʒu, ESC�R�[�h]���X�g���쐬
		pre_end = 0
		esc_info = []		# [�ʒu, ESC�R�[�h]
		self.only_text = ""	# ESC�R�[�h�����O����������
		iter = re.finditer(ESC_PTN, esc_text)
		for n in iter:
			start = n.span()[0]
			end   = n.span()[1]
			if start > 0:
				self.only_text += esc_text[pre_end:start]
			esc_info.append([len(self.only_text), n.group()])
			pre_end = end

		if pre_end < len(esc_text):
			self.only_text += esc_text[pre_end:len(esc_text)]

		# 1�������ɑΉ�����ESC���X�g���쐬
		start = 0
		esc_num = ""
		self.esc_list = [""] * len(self.only_text)
		for info in esc_info:
			if esc_num == "":
				start = info[0]
			else:
				end = info[0]
				for i in range(start, end):
					self.esc_list[i] = esc_num
				start = end

			esc_num = re.sub(r"\x1b\[|m", "", info[1])

		if esc_num != "":
			for i in range(start, len(self.only_text)):
				self.esc_list[i] = esc_num


	def coating_word(self, srch_text, esc_code):
		# ESC���O������������̕�������������AESC���X�g��ESC�R�[�h�ݒ�
		iter = re.finditer(srch_text, self.only_text)
		for n in iter:
			start = n.span()[0]
			end   = n.span()[1]
			for i in range(start, end):
				self.esc_list[i] = re.sub(r"\x1b\[|m", "", esc_code)


	def coating_pos(self, start, end, esc_code):
		# ����ʒu��ESC���X�g��ESC�R�[�h�ݒ�
		for i in range(start, end):
			self.esc_list[i] = re.sub(r"\x1b\[|m", "", esc_code)


	def get_esc_text(self):
		# ESC���X�g����ESC�R�[�h�𖄂ߍ��񂾕�������쐬
		pre_idx = 0
		pre_num = ""
		esc_text = ""
		for i, esc_num in enumerate(self.esc_list):
			if pre_num != esc_num:
				esc_text += self.only_text[pre_idx:i]
				if pre_num in list("0123456789"):
					# 1�O�����]/�������̏ꍇ�́A�I���R�[�h������
					esc_text += ESC_INIT 
				esc_text += f"\x1b[{esc_num}m"
				pre_idx = i
				pre_num = esc_num

		if pre_idx < len(self.only_text):
			esc_text += self.only_text[pre_idx:]

		if pre_num != "":
			esc_text += ESC_INIT

		return esc_text


class KeyCtrl():
	"""
	�L�[�ϊ��Ɋւ�����
	Attributes:
		map[] : �L�[�ϊ����([[���̓L�[, �ϊ��L�[]])
		store : �~�ϕ�����(�ϊ������擾�r���̃L�[)
	"""


	def __init__(self):
		self.map = []
		self.store = ""


	def reg_map(self, cmd):
		arg = re.split(r"[ \t]", cmd)
		if len(arg) == 3 and arg[0] == "map":
			in_key  = self.cvt_ctrl(arg[1])
			cvt_key = self.cvt_ctrl(arg[2])
			self.map.append([in_key, cvt_key])


	def str_to_bin(self, text, base):
		total_bin = 0
		for n in text:
			bin = ord(n)
			if 0x30 <= bin and bin <= 0x39:
				bin -= 0x30
			elif 0x41 <= bin and bin <= 0x5a:
				bin = bin - 0x41 + 10
			elif 0x61 <= bin and bin <= 0x7a:
				bin = bin - 0x61 + 10
			else:
				bin = 0

			total_bin = base * total_bin + bin

		return total_bin


	def cvt_ctrl(self, text):
		pass
		cvt_txt = ""
		pre_end = 0
		expr = "\\\\x[0-9a-fA-F]{2}|\\\\[0-7]{3}|\\\\."
		iter = re.finditer(expr, text)
		for n in iter:
			start = n.span()[0]
			end   = n.span()[1]
			ctrl_txt = text[start:end]
			if ctrl_txt[0:2] == "\\x":
				ctrl_bin = self.str_to_bin(ctrl_txt[2:], 16)
				ctrl_txt = chr(ctrl_bin)
			elif re.match("\\[0-7]", ctrl_txt) != None:
				ctrl_bin = self.str_to_bin(ctrl_txt[1:], 8)
				ctrl_txt = chr(ctrl_bin)
			else:
				if ctrl_txt == "\\t":
					ctrl_txt = "\t"
				elif ctrl_txt == "\\n":
					ctrl_txt = "\n"
				else:
					ctrl_txt = ctrl_txt[1:]

			cvt_txt = cvt_txt + text[pre_end:start] + ctrl_txt
			pre_end = end

		cvt_txt = cvt_txt + text[pre_end:]

		return cvt_txt


	def read_env(self):
		file = os.getenv("MISTLESS_INIT")
		if file == None:
			return

		if Path(file).exists():
			# map�t�@�C���Ǎ���
			with open(file, "rb") as f:
				txt = f.read()
			guess = chardet.detect(txt).get("encoding")
			if guess is None:
				guess = locale.getpreferredencoding()
			data = txt.decode(guess).splitlines()

			# map���o�^
			for txt in data:
				self.reg_map(txt)


	def getkey(self):
		if self.store != "":
			ret_key = self.store[0]
			self.store = self.store[1:]
		else:
			in_key = chr(ord(getch()))
			ret_key = self.convert_key(in_key)

		return ret_key


	def convert_key(self, in_key):
		# �~�ϕ���������ꍇ�A�ϊ����Ȃ�
		if self.store != "":
			return in_key

		end_flag = False
		while end_flag == False:
			more_flag = False
			self.store = self.store + in_key
			for cvt_data in self.map:
				if cvt_data[0] == self.store:
					self.store = cvt_data[1]
					end_flag = True
					break
				else:
					store_len = len(self.store)
					key_len = len(cvt_data[0])
					if store_len < key_len:
						if self.store == cvt_data[0][:store_len]:
							more_flag = True
							break

			if more_flag == False:
				end_flag = True

			if end_flag == False:
				in_key = chr(ord(getch()))
				#if in_key == "\x1b":
				#	return "\x1b"

		ret_key = self.store[0]
		self.store = self.store[1:]
		return ret_key


class DispCtrl():
	"""
	�\���Ɋւ�����

	Attributes:
		term_width : ��ʕ���
		term_lines : ��ʍs��
		vscroll    : �c�X�N���[����
		hscroll    : ���X�N���[����
		tab_stop   : �^�u�X�g�b�v��
		move_mode  : �J�[�\���̈ړ����[�h
		read_files : ���̓t�@�C���̃��X�g
		file_ctrl  : ���̓t�@�C���ɑΉ�����FileCtrl���X�g
		read_index : �\��������̓t�@�C���̃��X�g���ʒu
		read_count : ���̓t�@�C����
		tag_file   : �^�O�W�����v�������ɒǉ�����FileCtrl���X�g
		srch_str   : �����̕�����
		srch_dir   : �����̕���
	"""


	def __init__(self):
		self.term_width = 80
		self.term_lines = 25
		self.vscroll = 24
		self.hscroll = 40
		self.tab_stop = 4
		self.mvmode = MODE_WORD
		self.read_files = []
		self.file_ctrl = []
		self.read_index = 0
		self.read_count = 0
		self.tag_file = []
		self.srch_str = ""
		self.srch_dir = DIR_FORWARD

		self.get_term()


	def get_term(self):
		terminal_size = shutil.get_terminal_size()
		self.term_width = terminal_size.columns
		self.term_lines = terminal_size.lines
		self.vscroll = self.term_lines - 1
		self.hscroll = int(self.term_width / 2) 


	def set_read_file(self, files):
		self.read_files = files
		self.read_count = len(files)
		if self.read_count > 0:
			self.read_index = 1
		for i in range(0, self.read_count):
			new_ctrl = FileCtrl()
			self.file_ctrl.append(new_ctrl)
			self.tag_file.append([])


	def get_file_ctrl(self):
		if self.read_count > 0:
			if len(self.tag_file[display.read_index - 1]) > 0:
				ctrl = display.tag_file[display.read_index - 1][-1]
			else:
				file = self.read_files[self.read_index - 1]
				ctrl = self.file_ctrl[self.read_index - 1]
				ctrl.set_file(file)

			return ctrl


	def next_file_ctrl(self, count):
		if (self.read_index + count) <= self.read_count:
			self.read_index += count
		else:
			self.read_index = self.read_count
		return self.get_file_ctrl()


	def prev_file_ctrl(self, count):
		if (self.read_index - count) > 0:
			self.read_index -= count
		else:
			self.read_index = 1
		return self.get_file_ctrl()


	def srch_act_ctrl(self, file):
		find_flag = False
		if file in self.read_files:
			idx = self.read_files.index(file)
			ctrl = self.file_ctrl[idx]
			if ctrl.act:
				find_flag = True

		if find_flag == False:
			for ctrl in self.tag_file[self.read_index - 1]:
				if ctrl.read_file == file:
					find_flag = True
					break

		if find_flag == False:
			ctrl = None

		return ctrl


	def clear_eol(self):
		print(f"\x1b[0K", end="") # �J�[�\���ʒu����E������


	def clear_eob(self):
		print(f"\x1b[0J", end="") # �J�[�\���ʒu�����ʉE���܂ŏ���


	def clear_screen(self):
		print(f"\x1b[2J", end="")
		self.move_cursor(1, 1)


	def move_cursor(self, x, y):
		print(f"\x1b[{y};{x}H", end="")
		sys.stdout.flush()


	def puts(self,  str):
		#print(f"{str}", end="")
		print(f"{str}", end="", flush=True)
		#sys.stdout.flush()


	def move_print(self, x, y, str):
		self.move_cursor(x, y)
		self.clear_eol()
		self.puts(f"{str}")


	def clear_tail_line(self):
		self.move_cursor(1, self.term_lines)
		self.clear_eol()


	def delete_top_line(self):
		self.move_cursor(1, 1)
		print(f"\x1b[M", end="")


	def insert_top_line(self):
		self.move_cursor(1, 1)
		print(f"\x1bM", end="")


	def backspace(self):
		self.puts(f"\x1b[D \x1b[D")


	def visible_cursor(self, flag=True):
		if flag:
			self.puts(f"\x1b[?25h")
		else:
			self.puts(f"\x1b[?25l")


	def disp_message(self, msg, minus=0):
		if self.term_lines > minus:
			self.move_cursor(1, self.term_lines - minus)
			self.clear_eob()
			self.puts(f"\x1b[7m{msg}\x1b[m")


	def set_help(self):
		help_str="""
�y(�L�[)�R�}���h�z
    ^X          Ctrl+X��\��
    <n>         �R�}���h���O�ɐ����L�[�Ŏw�肳���l
    <a-z>       'a'�`'z'��1�����L�[���͂�\��
				
  ����{��
    ^H          �R�}���h�̃w���v��\��
    q           �I��

  ���X�N���[����
	f,SPACE     <n>��ʐ�ɃX�N���[��(<n>�w��Ȃ�:1���)
    b           <n>��ʑO�ɃX�N���[��(<n>�w��Ȃ�:1���)
    d           <n>����ʐ�ɃX�N���[��(<n>�w��Ȃ�:�����)
    u           <n>����ʑO�ɃX�N���[��(<n>�w��Ȃ�:�����)
    j           <n>�s��ɃX�N���[��(<n>�w��Ȃ�:1�s)
    k           <n>�s�O�ɃX�N���[��(<n>�w��Ȃ�:1�s)
	>           �E��<n>�J�������X�N���[��(<n>�w��Ȃ�:��ʕ��̔���)
    <           ����<n>�J�������X�N���[��(<n>�w��Ȃ�:��ʕ��̔���)

  ���^�O�W�����v��
    i           �J�[�\���ʒu�̕�����Ń^�O�W�����v
	I           �J�[�\���ʒu�̕�����Ń^�O�W�����v(�����^�O:���j���[����I��)
    o           �^�O�W�����v�O�̈ʒu�֖߂�
    r           �w�肵���^�O�t�@�C����ǉ��Ǎ���

  ���J�[�\���ړ���
    J           �J�[�\����<n>�s���Ɉړ�(<n>�w��Ȃ�:1�s)
    K           �J�[�\����<n>�s��Ɉړ�(<n>�w��Ȃ�:1�s)
    M           �J�[�\������ʓ������s�Ɉړ�
    l           �J�[�\��������<n>�Ԗڂ̃L�[���[�h�Ɉړ�(<n>�w��Ȃ�:1�Ԗ�)
    h           �J�[�\����O��<n>�Ԗڂ̃L�[���[�h�Ɉړ�(<n>�w��Ȃ�:1�Ԗ�)
    g           �t�@�C����<n>�s�ڂ�\��(<n>�w��Ȃ�:�擪�s)
    G           �t�@�C����<n>�s�ڂ�\��(<n>�w��Ȃ�:�ŏI�s)
    {,},[,]     �J�[�\���ʒu�̊��ʂɑΉ����銇�ʂֈړ�
    m<a-z>      ���݂̉��/�J�[�\���ʒu����̓L�[�����֐ݒ�
    @           ���݂̉��/�J�[�\���ʒu��ݒ�
    '<a-z>      ���̓L�[�����ɐݒ肳�ꂽ���/�J�[�\���ʒu�ֈړ�
    ''          �ړ����O�̉��/�J�[�\���ʒu�֖߂�


  ��������
    /           �w�肵��������ŏ���������(���S��v)
    ?           �w�肵��������ŋt��������(���S��v)
                  ^G     �J�[�\���ʒu�̕�������捞��
                  ^F     �J�[�\�����E�Ɉړ�
                  ^B     �J�[�\�������Ɉړ�
                  ^D     �J�[�\���ʒu�̕������폜
                  ^H     �J�[�\���O�̕������폜
                  ^N, ^P ���������̕����񃊃X�g��\��
                  ESC    ���͂̃L�����Z��
    n           ���O�Ɏ��s���ꂽ��������������<n>����s(<n>�w��Ȃ�:1��)
    p           ���O�Ɏ��s���ꂽ�������t������<n>����s(<n>�w��Ȃ�:1��)

  ���t�@�C���ؑց�
	N           �����t�@�C���Ǎ��ݎ��A<n>�Ԍ�̃t�@�C����\��(<n>�w��Ȃ�:����)
    P           �����t�@�C���Ǎ��ݎ��A<n>�ԑO�̃t�@�C����\��(<n>�w��Ȃ�:���O)

  �����̑���
    t           �^�u�X�g�b�v����<n>�ɕύX
    ^G          �t�@�C�����A�J�[�\���ʒu��\��
    ^L          ��ʂ̍ĕ\��(��ʃT�C�Y���Ď擾)

�y�����ݒ�z
   ���ϐ� MISTLESS_INIT �ɐݒ肳�ꂽ�t�@�C�����N�����ɓǂݍ��݁A
   ���[�U�L�[��`��o�^����B 
   ��������
     map ���̓L�[�p�^�[�� �ϊ��p�^�[��
	 ���p�^�[�����̐���R�[�h��16�i��(\\xFF)�A8�i��(\\777)�ŕ\�L���邱�Ƃ��\

�y�@�\�d�l�z
  �E���̓t�@�C���̕����R�[�h(UTF8, euc��)��\����ʂ̕����R�[�h�ɕϊ����ĕ\��
  �E���̓t�@�C���̊g���q�ɉ����āA�L�[���[�h/�R�����g����F�����\��
    (.py .h .cpp .c .awk �ɑΉ�)
  �E���̓t�@�C���̊g���q�ɉ����āA�^�O������������
    (�������A�N�����Ƀ^�O�t�@�C����ǂݍ��񂾏ꍇ�́A�����������Ȃ�)
  �E����L�[���[�h�̃^�O��񂪕�������ꍇ�́A�I�����ă^�O�W�����v�\

		"""
		ctrl = FileCtrl()
		lines = help_str.splitlines()
		ctrl.data = lines[1:]
		ctrl.max_line = len(ctrl.data)
		ctrl.disp_top = 1
		ctrl.disp_left = 1
		ctrl.cursor_x = 1
		ctrl.cursor_y = 1
		ctrl.act = True
		for text in ctrl.data:
			ctrl.coating.append("")
		ctrl.coating[1] = ESC_RED
		ctrl.coating[2] = ESC_RED
		ctrl.coating[3] = ESC_RED

		return ctrl


	def set_help_msg(self):
		msg = "<HELP> Press SPACE-key for more, or q when done."
		return msg


class FileCtrl():
	"""
	���̓t�@�C���Ɋւ��鐧��

	Attributes:
		read_file : ���̓t�@�C����
		act       : �f�[�^�Ǎ��ݕ\��
		data []   : �Ǎ��݃f�[�^
		coating []: �Ǎ��݃f�[�^�s�ւ̋����\��
		max_line  : �Ǎ��݃f�[�^�s
		disp_top  : �\���J�n�s�ʒu
		disp_left : �\���J�n��ʒu
		cursor_x  : �J�[�\���s�ʒu
		cursor_y  : �J�[�\����ʒu
		tag_key   : �^�O�W�����v���̃L�[���[�h
		mark {}   : ���/�J�[�\���ʒu{'@a-z': [top, left, x, y]}
	"""
	def __init__(self):
		self.read_file = ""
		self.act = False
		self.data = []
		self.coating = []
		self.max_line = 0
		self.disp_top = 0
		self.disp_left = 0
		self.cursor_x = 0
		self.cursor_y = 0
		self.tag_key = ""
		self.mark = {}


	def set_file(self, file):
		set_ext_pattern(file)
		self.read_file = file
		if self.act == False:
			ctrl = display.srch_act_ctrl(file)
			if ctrl == None:
				with open(file, "rb") as f:
					txt = f.read()
				# ���͕�����̃G���R�[�f�B���O����
				guess = chardet.detect(txt).get("encoding")
				if guess is None:
					guess = locale.getpreferredencoding()
				elif guess == "ISO-2022-JP":
					# JIS7����̓��ꏈ��
					guess = "ISO-2022-JP-EXT"
				elif guess == "ISO-8859-1" or guess == "KOI8-R":
					# JIS8->JIS7�ϊ�(���ꏈ��)
					cnv_txt = bytearray(txt)
					for i, ascii in enumerate(cnv_txt):
						if ascii >= 0xa1 and ascii <= 0xdf:
							cnv_txt[i] = ascii - 0x80
					txt = bytes(cnv_txt)
					guess = "ISO-2022-JP-EXT"
				self.data = txt.decode(guess).splitlines()
				self.set_line_coating()

				taginfo.analyze_file(file, self.data)
			else:
				self.data = ctrl.data
				self.coating = ctrl.coating

			self.max_line = len(self.data)
			self.disp_top = 1
			self.disp_left = 1
			self.cursor_x = 1
			self.cursor_y = 1
			self.act = True


	def add_esc(self, text):
		return re.sub("([*+.?(){}^$\[\]\-])", "\\\\\\1", text)


	def set_line_coating(self):
		"""
		�s�S�̂̋���
		"""
		if len(multi_line_ptn) == 4:
			(srch_ptn, start_ptn, end_ptn, esc_ptn) = multi_line_ptn
		else:
			(srch_ptn, start_ptn, end_ptn, esc_ptn) = ["", "", "", ""]

		mark_flag = False
		for text in self.data:
			ptn = re.findall(srch_ptn, text)
			if mark_flag == False:
				if ptn != []:
					if ptn[-1] == start_ptn:
						mark_flag = True
				self.coating.append("")
			else:
				if ptn != []:
					if ptn[0] == end_ptn:
						mark_flag = False

				if mark_flag == True:
					self.coating.append(esc_ptn)
				else:
					self.coating.append("")


	def unicode_len(self, text):
		"""
		�����R�[�h���܂ޕ�����̒����擾

		Args:
			text (str): ������

		Returns:
			int: ��ʕ\����̕�(�S�p:2, ���p:1)
		"""
		width = 0
		for char in text:
			if unicodedata.east_asian_width(char) in ("F", "W", "A"):
				width += 2
			else:
				width += 1
		return width

	def judge_border(self, cur_pos, add_len, border_pos):
		"""
		�J�n�ʒu/���Z��/���E�ʒu���狫�E�ʒu�̑O�㐔����

		Args:
			cur_pos (int): �J�n�ʒu(0�`)
			add_len (int): ���Z��
			border_pos (int): ���E�ʒu

		Returns:
			touch (int): True:���E�ʒu�ɐڒn(�ׂ��ꍇ�܂�)
			left  (int): ���E�ʒu���O�̕�����
			right (int): ���E�ʒu����̕�����
		"""
		touch = False	# ���E�ʒu�Ƃ̐ڒn(�ׂ��ꍇ�܂�)
		if (cur_pos + add_len) <= border_pos:
			left_len = add_len
			right_len = 0
			if (cur_pos + add_len) == border_pos:
				touch = True
		elif cur_pos < border_pos and border_pos < (cur_pos + add_len):
			left_len = border_pos - cur_pos
			right_len = (cur_pos + add_len) - border_pos
			touch = True
		elif border_pos <= cur_pos:
			left_len = 0
			right_len = add_len
			if border_pos == cur_pos:
				touch = True

		return touch, left_len, right_len


	def highlight_text(self, esc_ctrl, line_coating):
		"""
		keyword�̋���
		"""
		if line_coating != "":
			# �s�̋���
			esc_ctrl.coating_word(".*", line_coating)
		else:
			# syntax�̋���
			iter = re.finditer("[a-zA-Z0-9_]+", esc_ctrl.only_text)
			for n in iter:
				start = n.span()[0]
				end   = n.span()[1]
				word  = n.group()
				if word in syntax_list:
					esc_ctrl.coating_pos(start, end, ESC_GREEN)

			# (�_�u��)�N�H�[�e�[�V�����̋����ݒ�
			esc_ctrl.coating_word(quote_ptn, ESC_CYAN)

			# �R�����g�̋���
			esc_ctrl.coating_word(comment_ptn, ESC_BLUE)

		# ����R�[�h�̋���
		esc_ctrl.coating_word("[\x00-\x08\x0a-\x1f]", ESC_REVERSE)

		# �����L�[�̋���
		if display.srch_str != "":
			esc_ctrl.coating_word(display.srch_str, ESC_BG_YELLOW)


	def cut_text(self, line, start, width, coating):
		"""
		�����񂩂�J�n�ʒu/���Ŏw�肵��������̐؏o��

		Args:
			line (char): ������
			start (int): �J�n�ʒu(1�`)
			width (int): �؏o����
			coating (str): �s����ESC�V�[�P���X


		Returns:
			str: �؏o����������
		"""
		esc_ctrl = Escape()
		esc_ctrl.analyze_text(line)
		self.highlight_text(esc_ctrl, coating)

		cut_pid = "srch"  # �؏o���J�n�ʒu�̌���
		cut_txt = ""
		pre_esc_num = ""  # 1�����O�̋����\���ԍ�
		pos = 0           # �擪����̕�����
		stt = start - 1   # �؏o���J�n�ʒu
		left_more = False # �؏o�������̐擪��"$"�\��
		for i, in_char in enumerate(line):
			# 1�����̕\���`���ƒ����擾
			key_code = ord(in_char)
			if key_code == 0x09:	# tab
				wd = int(pos / display.tab_stop + 1) * display.tab_stop - pos
				ch = " " * wd
			elif key_code < 0x20:	# ctrl
				wd = 2
				ch = "^" + chr(0x40 + key_code)
			else:
				wd = self.unicode_len(in_char)
				ch = in_char

			# ������̍ŏ��ƍŌ�𔻒�
			if (i == 0) or (i == (len(line) - 1)):
				line_edge = True
			else:
				line_edge = False

			if cut_pid == "srch":
				# �؏o���J�n�ʒu�̌���
				(touch, left, right) = self.judge_border(pos, wd, stt)
				if left == 0:
					add_ch = ch
				else:
					add_ch = MORE_CHAR * right

				if touch:
					cut_pid = "cut" # �؏o���̊J�n
					if stt > 0 and right == 0:
						left_more = True
			else:
				# �؏o���̊J�n
				(touch, left, right) = self.judge_border(pos, wd, stt + width)
				if right == 0:
					if left_more or (touch and line_edge == False):
						add_ch = MORE_CHAR * wd
						left_more = False
					else:
						add_ch = ch
				else:
					add_ch = MORE_CHAR * left

				if touch:
					cut_pid = "end" # �؏o���I��

			esc_num = esc_ctrl.esc_list[i]
			if (add_ch != "") and (pre_esc_num != esc_num):
				add_ch = f"\x1b[{esc_num}m" + add_ch
				if re.match(r"[0-9]|4[0-9]", pre_esc_num) != None:
					add_ch = ESC_INIT + add_ch
			pre_esc_num = esc_num
			cut_txt += add_ch

			if cut_pid == "end":
				break

			pos += wd

		if pre_esc_num != "":
			cut_txt += ESC_INIT

		return cut_txt


	def disp_line(self):
		display.clear_screen()
		display.visible_cursor()
		start_idx = self.disp_top - 1
		end_idx = self.disp_top + display.vscroll - 1
		if self.max_line < end_idx:
			end_idx = self.max_line
		for i in range(start_idx, end_idx):
			cut_txt = self.cut_text(self.data[i],
									self.disp_left,
									display.term_width,
									self.coating[i])
									
			print(f"{cut_txt}")
		self.disp_fname()


	def goto_line(self, row, number):
		self.set_mark("@")
		disp_top = 1
		if number > 0:
			disp_top = number
			if self.max_line < disp_top:
				disp_top = self.max_line 
			self.disp_top = disp_top
			self.disp_line()
		else:
			if row == 0:
				disp_top = self.max_line - display.term_lines + 2
			else:
				disp_top = row

			if self.max_line < disp_top:
				disp_top = self.max_line 
			if disp_top <= 0:
				disp_top = 1

			self.disp_top = disp_top
			self.disp_line()


	def set_mark(self, char):
		if char == "":
			display.move_print(1, display.term_lines, "mark: ")
			char = chr(ord(getch()))

		msg = ""
		if ("a" <= char and char <= "z") or char == "@":
			self.mark[char] = [self.disp_top, self.disp_left,
			                   self.cursor_x, self.cursor_y]
		else:
			msg = "Choose a letter between 'a' and 'z'"

		return msg


	def goto_mark(self, char):
		if char == "":
			display.move_print(1, display.term_lines, "goto mark: ")
			char = chr(ord(getch()))

		msg = ""
		if ("a" <= char and char <= "z") or char == "\'":
			if char == "\'":
				char = "@"

			if char in self.mark:
				save_pos = self.mark[char]
				self.set_mark("@")
				(self.disp_top, self.disp_left,
				 self.cursor_x, self.cursor_y) = save_pos
				self.disp_line()
			else:
				msg = "No mark"
		else:
			msg = "Choose a letter between 'a' and 'z'"

		return msg


	def vscroll(self, count, dir):
		msg = ""
		if dir == DIR_FORWARD:
			if (self.disp_top + display.vscroll) <= self.max_line:
				display.clear_tail_line()
				idx = self.disp_top + display.vscroll - 1
				for i in range(0, count):
					if idx < len(self.data):
						cut_txt = self.cut_text(self.data[idx],
												self.disp_left,
												display.term_width,
												self.coating[idx])
						display.delete_top_line()
						display.move_print(1, display.term_lines - 1, cut_txt)
						idx += 1
						self.disp_top += 1
					else:
						break
				self.disp_fname()
			else:
				msg = "(END)"
		else:
			if self.disp_top > 1:
				idx = self.disp_top - 1 - 1
				for i in range(0, count):
					if idx >= 0:
						cut_txt = self.cut_text(self.data[idx],
												self.disp_left,
												display.term_width,
												self.coating[idx])
						display.insert_top_line()
						display.move_print(1, 1, cut_txt)
						idx -= 1
						self.disp_top -= 1
					else:
						break
				self.disp_fname()

		self.first_word()
		return msg


	def hscroll(self, dir, count):
		if dir == DIR_FORWARD:
			if count > 0:
				self.disp_left += count
			else:
				self.disp_left += display.hscroll
		else:
			if count > 0:
				self.disp_left -= count
			else:
				self.disp_left -= display.hscroll

			if self.disp_left < 1:
				self.disp_left = 1

		self.first_word()
		self.disp_line()


	def cursor_to_index(self, line, x):
		pos = 0
		index = 0
		for i, in_char in enumerate(line):
			key_code = ord(in_char)
			if key_code == 0x09:	# tab
				wd = int(pos / display.tab_stop + 1) * display.tab_stop - pos
			elif key_code < 0x20:	# ctrl
				wd = 2
			else:
				wd = self.unicode_len(in_char)

			pos += wd
			if (x - 1) < pos:
				index = i
				break

		return index


	def index_to_cursor(self, line, idx):
		pos = 0
		for i, in_char in enumerate(line):
			key_code = ord(in_char)
			if key_code == 0x09:	# tab
				wd = int(pos / display.tab_stop + 1) * display.tab_stop - pos
			elif key_code < 0x20:	# ctrl
				wd = 2
			else:
				wd = self.unicode_len(in_char)

			if (idx <= i):
				break
			pos += wd

		return (pos + 1)
	

	def get_word_index(self, text, cur_idx, match_ptn=""):
		"""
		�O��̃��[�h�ʒu�擾

		Args:
			text (str): ������
			cur_idx (str): ������̌��݈ʒu(0�`, -1:�s��)

		Returns:
			int: ��O�̃��[�h�ʒu(0�`:�L, -1:��)
			int: ���̃��[�h�ʒu(0�`:�L, -1:��)
		"""
		prev_idx = -1
		next_idx = -1
		if match_ptn == "":
			match_ptn = "[a-zA-Z0-9_{}]+"
		ptn = re.compile(match_ptn)
		iter = ptn.finditer(text)
		for n in iter:
			start = n.span()[0]

			if start < cur_idx:
				prev_idx = start

			if cur_idx < start:
				next_idx = start
				break

		return prev_idx, next_idx


	def first_word(self):
		#line = self.data[(self.disp_top - 1) + (self.cursor_y - 1)]
		(line, line_idx, char_idx, pos) = self.get_current_param()
		find_flag = False
		iter = re.finditer(r"[a-zA-Z0-9_]+", line)
		for n in iter:
			idx = n.span()[0]
			pos = self.index_to_cursor(line, idx)
			if self.disp_left <= pos:
				find_flag = True
				break

		if find_flag == True:
			self.cursor_x = pos - (self.disp_left - 1)
		else:
			self.cursor_x = 1


	def get_current_param(self):
		line_idx = (self.disp_top - 1) + (self.cursor_y - 1)
		line = self.data[line_idx]
		pos = self.disp_left + self.cursor_x - 1
		char_idx = self.cursor_to_index(line, pos)
		return line, line_idx, char_idx, pos


	def next_word(self, count):
		(line, line_idx, idx, pos) = self.get_current_param()
		end_flag = False
		while end_flag == False:
			(prev_idx, next_idx) = self.get_word_index(line, idx)
			if next_idx >= 0:
				self.scroll_caret(line_idx, next_idx)
				count -= 1
				if count <= 0:
					end_flag = True
				idx = next_idx
			else:
				if line_idx < (self.max_line - 1):
					line_idx += 1
					line = self.data[line_idx]
					pos = 1
					idx = -1
				else:
					end_flag = True


	def prev_word(self, count):
		(line, line_idx, idx, pos) = self.get_current_param()
		end_flag = False
		while end_flag == False:
			(prev_idx, next_idx) = self.get_word_index(line, idx)
			if prev_idx >= 0:
				self.scroll_caret(line_idx, prev_idx)
				count -= 1
				if count <= 0:
					end_flag = True
				idx = prev_idx
			else:
				if line_idx > 0:
					line_idx -= 1
					line = self.data[line_idx]
					pos = display.term_width
					idx = len(line)
				else:
					end_flag = True


	def next_line(self, move_cnt):
		next_csr_y = self.cursor_y + move_cnt
		if next_csr_y < 1:
			self.vscroll(-1 * (next_csr_y - 1), DIR_REVERSE)
			self.cursor_y = 1
		elif (display.term_lines - 1) < next_csr_y:
			self.vscroll(next_csr_y - (display.term_lines - 1), DIR_FORWARD)
			self.cursor_y = display.term_lines - 1
		else:
			if ((self.disp_top - 1) + (next_csr_y - 1)) < self.max_line:
				self.cursor_y = next_csr_y
			else:
				self.cursor_y = self.max_line - (self.disp_top - 1)

		# ���̍s�̃J�[�\���ʒuX���Z�o
		(line, line_idx, char_idx, pos) = self.get_current_param()

		### index�ʒu�łȂ��A�J�[�\���ʒu�Ŕ�r����悤�ɏC�� ###
		pre_idx = -1
		iter = re.finditer(r"[a-zA-Z0-9_]+", line)
		for n in iter:
			idx = n.span()[0]
			if idx == char_idx:
				break;
			elif char_idx < idx:
				if (idx - char_idx) > (char_idx - pre_idx):
					if pre_idx == -1:
						char_idx = idx
					else:
						char_idx = pre_idx
				else:
					char_idx = idx
				break
			else:
				pre_idx = idx

		pos = self.index_to_cursor(line, char_idx)
		self.cursor_x = pos - (self.disp_left - 1)

		display.move_cursor(self.cursor_x, self.cursor_y)


	def middle_line(self):
		last_idx = (self.disp_top - 1) + (display.term_lines - 1)
		if last_idx < self.max_line:
			bottom_cursor_y = display.term_lines - 1
		else:
			bottom_cursor_y = self.max_line - (self.disp_top - 1)

		file_ctrl.cursor_y = (bottom_cursor_y // 2) + (bottom_cursor_y % 2)
		display.move_cursor(file_ctrl.cursor_x, file_ctrl.cursor_y)
		file_ctrl.first_word()


	def get_command(self, prompt, file_srch=False, limit=""):
		display.clear_tail_line()
		display.move_print(1, display.term_lines, f"{prompt}")
		history.init_idx()
		filesrch = FileSearch()
		def_enc = locale.getpreferredencoding()
		pre_char = ""	# �������͂�1Byte�ڃR�[�h�ۑ��p
		idx = 0			# cmd���̃J�[�\���ʒu
		shift = 1		# cmd�����񂪉�ʉ������ŕ\���ł��Ȃ��ꍇ�̕\���J�n�ʒu
		offset = 0		# ^G�̕����捞���̍s���Q�ƈʒu
		cmd = ""		# ���͂����R�}���h������
		end_flag = 	False
		while end_flag == False:
			#key = ord(getch())
			key = ord(keyctrl.getkey())
			if key == 0x06: # ^F
				# �J�[�\���E�ړ�
				idx = (idx + 1) if (idx < len(cmd)) else idx
			elif key == 0x02: # ^B
				# �J�[�\�����ړ�
				idx = (idx - 1) if (idx > 0) else idx
			elif key == 0x01: # ^A
				# �J�[�\���s���ړ�
				idx = 0
			elif key == 0x05: # ^E
				# �J�[�\���s���ړ�
				idx = len(cmd)
			elif key == 0x04: # ^D
				# �J�[�\���ʒu��1�����폜
				if cmd != "":
					cmd = cmd[:idx] + cmd[idx+1:]
			elif key == 0x08: # ^H
				# �J�[�\������1�����폜
				if cmd != "":
					cmd = cmd[:idx-1] + cmd[idx:]
					idx -= 1
				else:
					end_flag = True
			elif key == 0x09: # ^I
				if file_srch:
					pass # �t�@�C�����⊮
					arg = re.split(r"[ \t]",cmd[:idx])
					file = filesrch.isearch(arg[-1])
					ins_idx = idx - self.unicode_len(arg[-1])
					cmd = cmd[:ins_idx] + file
					idx = len(cmd)
				else:
					if limit == "" or re.match(limit, chr(key)) != None:
						cmd = cmd[:idx] + chr(key) + cmd[idx:]
						idx += 1
			elif key == 0x07 and limit == "": # ^G (���������Ȃ��̏ꍇ�̂�)
				# �J�[�\���ʒu�����捞��
				(line, line_idx, char_idx, pos) = self.get_current_param()
				start_idx = char_idx + offset
				expr = r"[a-zA-Z0-9_]+|[^a-zA-Z0-9_]+"
				words = re.findall(expr, line[start_idx:])
				if len(words) > 0:
					word = words[0]
					offset += len(word)
				else:
					word = ""
				cmd = cmd[:idx] + word + cmd[idx:]
				idx += len(word)
			elif key == 0x10: # ^P
				# ����(1�O)
				cmd = history.get_prev()
				idx = len(cmd)
			elif key == 0x0e: # ^N
				# ����(1��)
				cmd = history.get_next()
				idx = len(cmd)
			elif key in (0x0d, 0x0a): # CR, LF
				# ���͏I��
				history.reg_hist(cmd)
				end_flag = True
			elif key == 0x1b: # ESC
				# ���̓L�����Z��
				cmd = ""
				idx = 0
				end_flag = True
			else:
				if pre_char == "":
					if limit == "" or re.match(limit, chr(key)) != None:
						if key >= 0x80:
							pre_char = bytes([key]) # ()���̒l��[]�ň͂�
						elif key >= 0x20 or key == 0x09:
							cmd = cmd[:idx] + chr(key) + cmd[idx:]
							idx += 1
				else:
					# 2Byte�̊����R�[�h����
					pre_char += bytes([key]) # ()���̒l��[]�ň͂�
					char = pre_char.decode(def_enc)
					cmd = cmd[:idx] + char + cmd[idx:]
					idx += 1
					pre_char = ""

			pos = self.index_to_cursor(cmd, idx)
			prompt_len = self.unicode_len(prompt)
			disp_width = display.term_width - prompt_len
			if idx > 0:
				char_len = self.unicode_len(cmd[idx-1])
			else:
				char_len = 0

			if (shift + display.term_width - char_len) <= (prompt_len + pos):
				shift += (disp_width // 2)
			elif pos <= shift:
				shift -= (disp_width // 2)
				if shift < 1:
					shift = 1
			disp_cmd = self.cut_text(cmd, shift, disp_width , "")
			display.move_print(1, display.term_lines, f"{prompt}{disp_cmd}")
			csr_x = pos - (shift - 1)
			display.move_cursor(prompt_len + csr_x, display.term_lines)

		display.clear_tail_line()
		return cmd


	def scroll_caret(self, line_idx, char_idx):
		stat = 0
		# Y�����̕\������
		if (self.disp_top + display.vscroll) <= (line_idx + 1):
			dir = DIR_FORWARD
			cnt = (line_idx + 1) - (self.disp_top + display.vscroll) + 1
			if cnt <= (SCROLL_PAGE * display.vscroll):
				self.vscroll(cnt, dir)
				self.cursor_y = display.vscroll
			else:
				self.cursor_y = int(display.vscroll / 2)
				self.disp_top = (line_idx + 1) - self.cursor_y + 1
			stat = dir
		elif (line_idx + 1) < self.disp_top:
			dir = DIR_REVERSE
			cnt = self.disp_top - (line_idx + 1)
			if cnt <= (SCROLL_PAGE * display.vscroll):
				self.vscroll(cnt, dir)
				self.cursor_y = 1
			else:
				self.cursor_y = int(display.vscroll / 2)
				self.disp_top = (line_idx + 1) - self.cursor_y + 1
			stat = dir
		else:
			self.cursor_y = (line_idx + 1) - self.disp_top + 1

		# X�����̕\������
		cnt = 0
		line = self.data[line_idx]
		pos = self.index_to_cursor(line, char_idx)
		if (self.disp_left + display.term_width) <= pos:
			cnt = pos - (self.disp_left + display.term_width) + 1
			cnt = math.ceil(cnt / display.hscroll) * display.hscroll
			self.hscroll(DIR_FORWARD, cnt)
			stat = 10 * stat + DIR_FORWARD
		elif pos < self.disp_left:
			cnt = self.disp_left - pos
			cnt = math.ceil(cnt / display.hscroll) * display.hscroll
			self.hscroll(DIR_REVERSE, cnt)
			stat = 10 * stat + DIR_REVERSE
		self.cursor_x = pos - (self.disp_left - 1)

		return stat

	def srch_word(self, dir, count, input):
		global display

		# ����������̓���
		if input == True:
			prompt = "/" if (dir == DIR_FORWARD) else "?"
			srch_key = self.get_command(prompt)
			if srch_key != "":
				display.srch_str = srch_key
				display.srch_dir = dir
			else:
				display.srch_str = ""
				self.disp_line()
				return ""
		else:
			if display.srch_dir == DIR_REVERSE:
				dir = DIR_REVERSE if (dir == DIR_FORWARD) else DIR_FORWARD 

		if display.srch_str == "":
			return "No search word"

		# ������̌���
		self.set_mark("@")
		msg = ""
		end_flag = False
		(line, line_idx, char_idx, pos) = self.get_current_param()
		if dir == DIR_FORWARD:
			start_idx = char_idx + 1
			while end_flag == False:
				try:
					stat = re.search(display.srch_str, line[start_idx:])
				except:
					display.srch_str = ""
					msg = "No match"
					break

				if stat != None:
					idx = stat.span()[0] + start_idx
					stat = self.scroll_caret(line_idx, idx)
					if stat or input:
						self.disp_line()
					count -= 1
					if count <= 0:
						end_flag = True
					start_idx = idx + 1
				else:
					if line_idx < (self.max_line - 1):
						line_idx += 1
						line = self.data[line_idx]
						start_idx = 0
					else:
						msg = "No match"
						end_flag = True
		else:
			end_idx = char_idx
			while end_flag == False:
				idx = -1
				try:
					iter = re.finditer(display.srch_str, line[:end_idx])
				except:
					display.srch_str = ""
					msg = "No match"
					break

				for n in iter:
					idx = n.span()[0]

				if idx >= 0:
					stat = self.scroll_caret(line_idx, idx)
					if stat or input:
						self.disp_line()
					count -= 1
					if count <= 0:
						end_flag = True
					end_idx = idx - 1 if idx > 0 else 0
				else:
					if line_idx > 0:
						line_idx -= 1
						line = self.data[line_idx]
						end_idx = len(line)
					else:
						msg = "No match"
						end_flag = True

		# ���������Ɉ�v�������Ă��A�����ʂ̋t�����̈�v�����������\��
		if msg == "No match":
			self.disp_line()

		return msg


	def get_current_word(self):
		(line, line_idx, idx, pos) = self.get_current_param()
		stat = re.match(r"[a-zA-Z0-9_]+", line[idx:])
		if stat != None:
			start = idx + stat.span()[0]
			end   = idx + stat.span()[1]
			word = line[start:end]
		else:
			word = ""

		return word


	def tag_jump(self, select_f=False):
		# �L�[���[�h�̎擾
		keyword = self.get_current_word()

		# �^�O���e�[�u���̌���
		tag_list = taginfo.srch_keyword(keyword)
		if len(tag_list) == 0:
			return "E:No such tag"

		# �^�O���̑I��
		if select_f and len(tag_list) > 1:
			tag_info = self.select_list(tag_list)
			file = tag_info[1]
			srch = tag_info[2]
			if file == "":
				self.disp_line()
				return "E:Cancel"
		else:
			file = tag_list[0][1]
			srch = tag_list[0][2]

		# �W�����v��t�@�C���Ǎ���
		if Path(file).exists() == False:
			return f"E:No such file({file})"
		new_ctrl = FileCtrl()
		new_ctrl.set_file(file)

		# �W�����v��t�@�C�����̌���
		if srch.isnumeric():
			line_idx = int(srch)
			if line_idx <= new_ctrl.max_line:
				new_ctrl.disp_top = line_idx
				new_ctrl.cursor_y = 1
			else:
				return f"E:No such line number({line_idx})"
		else:
			if srch in new_ctrl.data:
				idx = new_ctrl.data.index(srch)
				new_ctrl.disp_top = idx + 1
				new_ctrl.cursor_y = 1
			else:
				return f"E:No such line({srch})"

		display.tag_file[display.read_index - 1].append(new_ctrl)
		new_ctrl.tag_key = keyword

		count = len(tag_list)
		if count > 1 and select_f == False:
			return f"I:Exist {count} tags"
		else:
			return ""


	def select_list(self, tag_list):
		disp_data = []

		# �\���G���A�̎Z�o
		list_max = len(tag_list)
		minus_idx = 2 * list_max + 2
		if minus_idx < display.term_lines:
			self.disp_fname(minus_idx)
		else:
			minus_idx = display.term_lines
			if minus_idx % 2 == 1:
				disp_data.append("")

		# �\���p�^�O���̕ۑ�
		(tag, file, srch) = tag_list[0]
		tag_width = display.term_width - 8
		tag_txt = self.cut_text(tag, 1, tag_width, "")
		title = f"{ESC_CYAN}No. tag={ESC_INIT}{tag_txt}"
		disp_data.append(title)

		file_width = display.term_width - 4	# "No. "�̕������Z
		srch_width = display.term_width - 6 # �擪�C���f���g�������Z
		for i, tag_info in enumerate(tag_list):
			(tag, file, srch) = tag_info
			file_txt = self.reduce_text(file, file_width)
			srch_txt = self.cut_text(srch, 1, srch_width, "")
			disp_data.append(f"{i+1:3d} {file_txt}")
			disp_data.append(f"      {srch_txt}")

		# �\���p�^�O����More�\��
		self.disp_more(disp_data, minus_idx)

		# �^�O���̑I��
		tag_info = ["", "", ""]
		cmd = self.get_command("�ԍ���I�����Ă�������: ", limit="[0-9]")
		if re.match(r"[0-9]+", cmd):
			idx = int(cmd)
			if idx > 0 and idx <= len(tag_list):
				tag_info = tag_list[idx - 1]
		return tag_info


	def reduce_text(self, text, width):
		txt_len = self.unicode_len(text)
		if width < txt_len:
			half_len = (width - 2) // 2
			suf_start = txt_len - half_len + 1
			pre_txt = self.cut_text(text, 1, half_len, "")
			suf_txt = self.cut_text(text, suf_start, half_len, "")
			dot_cnt = width - (2 * half_len)
			reduce_txt = pre_txt + dot_cnt * "." + suf_txt
		else:
			reduce_txt = text

		return reduce_txt


	def disp_more(self, data, lines):
		tail_row = display.term_lines
		idx = 0
		data_max = len(data)
		disp_rate = 0
		while disp_rate < 100:
			start = idx
			for i in range(0, lines - 1):
				if start == 0:
					row = tail_row - (lines - 1) + i
				else:
					row = tail_row

				if data_max <= idx:
					break
				display.move_print(1, row, data[idx] + "\n")
				idx += 1

			disp_rate = ((100 * idx) // data_max)
			if disp_rate < 100:
				display.move_print(1, tail_row, f"-- More ({disp_rate}%) --")
				key = ord(getch())
				if key == 0x1b:
					break


	def srch_brace(self):
		"""
		�Ή����銇��((), {}, [])��T��
		"""
		match_cnt = 0
		add_idx = 1		# �Ή����銇�ʂ������������
		(line, line_idx, idx, pos) = self.get_current_param()
		if self.coating[line_idx] != "":
			return

		cur_char = line[idx]
		if cur_char in ("(", "{", "["):
			match_cnt = 1
			add_idx = 1
		elif cur_char in (")", "}", "]"):
			match_cnt = -1
			add_idx = -1
		else:
			return

		ptn = "[(){}\[\]]|\".*\"|'.*'"
		if comment_ptn != "":
			ptn = ptn + "|" + comment_ptn 
		skip_flag = False
		next_flag = False
		end_flag = False
		while end_flag == False:
			srch_char = ""
			if self.coating[line_idx] != "":
				idx = -1
			else:
				(prev_idx, next_idx) = self.get_word_index(line, idx, ptn)
				idx = -1
				if add_idx > 0:
					# ���̌�����������
					if next_idx >= 0:
						srch_char = line[next_idx]
						idx = next_idx
				else:
					# �O�̌�����������
					if prev_idx >= 0:
						srch_char = line[prev_idx]
						idx = prev_idx

			if idx != -1:
				# ��/�O�̌�����������
				if srch_char in ("(", "{", "["):
					match_cnt += 1
				elif srch_char in (")", "}", "]"):
					match_cnt -= 1

				# �Ή����銇�ʔ���
				if match_cnt == 0:
					self.scroll_caret(line_idx, idx)
					end_flag = True
			else:
				# ��/�O�̌��������Ȃ�
				line_idx += add_idx
				if line_idx >=0 and line_idx < (self.max_line):
					# ��/�O�̍s������
					line = self.data[line_idx]
					if add_idx > 0:
						idx = -1
					else:
						idx = len(line)
				else:
					end_flag = True


	def add_tagfile(self):
		# �^�O�t�@�C�����̓���
		file = self.get_command("Add TagFile: ", True)
		if Path(file).exists() == False:
			return "No such file"

		if file != "":
			# �^�O���e�[�u���̍쐬
			taginfo.read_file(file)

			return "Add tag info"
		else:
			return ""


	def count_lines(self, text, width):
		lines = 1
		total_width = 0
		for chr in text:
			wd = self.unicode_len(chr)
			if width <= (total_width + wd):
				lines += 1
				total_width = (total_width + wd) - width
			else:
				total_width += wd

		return lines


	def disp_fname(self, minus=0, full=False):
		if (len(display.tag_file[display.read_index - 1]) > 0):
			tag_cnt = len(display.tag_file[display.read_index - 1])
			tag_idx = f" <{self.tag_key}({tag_cnt})>  "
		else:
			tag_idx = ""
		file_idx = f"({display.read_index} of {display.read_count})"

		pos_y = self.disp_top + self.cursor_y - 1
		pos_x = self.disp_left + self.cursor_x - 1

		if full == True:
			file_str = self.read_file
			minus = self.count_lines(file_str, display.term_width) - 1
			cursor = f"  line {pos_y}/{self.max_line}, column {pos_x}"
			disp_str = file_str + tag_idx + file_idx + cursor
			display.disp_message(disp_str, minus)
		else:
			cursor = f"  [{pos_y},{pos_x}]"
			idx_len = len(tag_idx + file_idx + cursor)
			file_width = (display.term_width - 1) - idx_len
			file_str = self.read_file
			file_len = self.unicode_len(file_str)
			diff_len = file_width - file_len
			if diff_len < 0:
				file_start = (-1 * diff_len) + 1
				adjust_space = ""
			else:
				file_start = 1
				adjust_space = " " * diff_len
			file_str = self.cut_text(file_str, file_start, file_width, "")

			disp_str = file_str + tag_idx + file_idx + adjust_space + cursor
			display.disp_message(disp_str, minus)


class HistoryCtrl():
	"""
	�R�}���h���𐧌�

	Attributes:
		max_cnt     : �����̓o�^�ő吔
		hist_idx    : �Q�Ƃ��闚���ʒu(-1, 0, ..., max_cnt-1, max_cnt)
		hist_list[] : �������X�g
	"""
	def __init__(self, max_cnt=MAX_HISTORY):
		self.max_cnt = max_cnt
		self.hist_idx = 0
		self.hist_list = []


	def reg_hist(self, text):
		# ���͕����Ɠ��ꕶ�������X�g����폜
		if text in self.hist_list:
			self.hist_list.remove(text)

		# �����̍ő吔�ȏ�̏ꍇ�A��ԌÂ����������X�g����폜
		if self.max_cnt <= len(self.hist_list):
			del self.hist_list[0]

		# �ŐV�̗��������X�g�̍Ō�ɒǉ�
		self.hist_list.append(text)
		self.hist_idx = len(self.hist_list)


	def init_idx(self):
		self.hist_idx = len(self.hist_list)


	def get_next(self):
		hist = ""
		if self.hist_idx < (len(self.hist_list)):
			self.hist_idx += 1

		if self.hist_idx >= 0 and self.hist_idx < (len(self.hist_list)):
			hist = self.hist_list[self.hist_idx]

		return hist


	def get_prev(self):
		hist = ""
		if 0 <= self.hist_idx:
			self.hist_idx -= 1

		if 0 <= self.hist_idx:
			hist = self.hist_list[self.hist_idx]

		return hist


class TagInfo():
	"""
	�^�O�W�����v�Ɋւ�����

	Attributes:
		tag_table[] : �^�O���(�L�[���[�h�A�t�@�C�����A�s����������)�̃��X�g
		input_file  : �^�O�t�@�C������̓Ǎ��ݗL��(True/False)
	"""
	def __init__(self):
		self.tag_table = []
		self.input_file = False


	def read_file(self, tag_file):
		"""
		�^�O�t�@�C����Ǎ��݁A�^�O���e�[�u���֓o�^
			Args:
				tag_file (str): �^�O�t�@�C����

			Returns:
				�Ȃ�
		"""
		# �^�O�t�@�C�����̃`�F�b�N
		if tag_file != "":
			file = tag_file
		else:
			file = TAG_FILE

		if Path(file).exists() == False:
			return

		# �^�O�t�@�C���Ǎ���
		with open(file, "rb") as f:
			txt = f.read()
		guess = chardet.detect(txt).get("encoding")
		if guess is None:
			guess = locale.getpreferredencoding()
		data = txt.decode(guess).splitlines()

		# �^�O���e�[�u���̓o�^
		for line in data:
			tag_info = line.split(maxsplit=2)
			if len(tag_info) == 3:
				if re.match(r"^/\^.*\$/$", tag_info[2]) != None:
					tag_info[2] = re.sub(r"^/\^|\$/$", "", tag_info[2])
				self.tag_table.append(tag_info)
		self.input_file = True


	def analyze_file(self, file, lines):
		"""
		�\�[�X����͂��āA�^�O���e�[�u���֓o�^
			Args:
				file (str): �t�@�C����
				lines (list): �\�[�X�R�[�h

			Returns:
				�Ȃ�
		"""
		# �^�O�t�@�C������̓Ǎ��݂��Ă���ꍇ�A��͂��Ȃ�
		if self.input_file == True:
			return

		# �t�@�C���g���q�ɂ�蕪��
		ext = os.path.splitext(file)[-1]
		if ext == ".py":
			# python�̉��
			pre_indent = 0
			indent = 0
			for text in lines:
				m = re.match(r"[ \t]+", text)
				if m != None:
					indent = m.span()[1]
				elif text != "":
					indent = 0

				words = re.findall(r"[a-zA-Z0-9_]+|[()=]+", text)
				if len(words) > 2:
					if words[0] == "class" or words[0] == "def":
						list = [words[1], file, text]
						self.tag_table.append(list)
					elif words[1] == "=" and indent == 0:
						list = [words[0], file, text]
						self.tag_table.append(list)

				pre_indent = indent
		elif ext in (".c", ".cpp", ".h"):
			# C/C++�̉��
			ctags = Ctags()
			tag_info = ctags.analyze(file, lines)
			for list in tag_info:
				self.tag_table.append(list)
		elif ext == ".awk":
			# awk�̉��
			for text in lines:
				words = re.findall(r"function|[a-zA-Z0-9_]+", text)
				if len(words) > 1:
					if words[0] == "function":
						list = [words[1], file, text]
						self.tag_table.append(list)


	def srch_keyword(self, keyword):
		"""
		�^�O���e�[�u���̌���
			Args:
				keyword (str): ��������L�[���[�h

			Returns:
				list: ��������[[�^�O, �t�@�C����, �s����������]]
		"""
		tag_list = []
		for record in self.tag_table:
			if keyword == record[0]:
				tag_list.append(record)

		return tag_list


class Ctags():
	"""
	C/C++�̃^�O���𐶐�

	Attributes:
	"""
	def __init__(self):
		self.file = ""
		self.pre_word = ""
		self.cur_text = ""
		self.save_text = ""
		self.paren   = 0	# ()�̃l�X�g��
		self.brace   = 0	# {}�̃l�X�g��
		self.bracket = 0	# []�̃l�X�g��
		self.comment = 0	# /* */�̊J�n(1)�A�I��(0)
		self.div_f   = False# ����L�[��";"�`�F�b�N
		self.head_f  = False# ����L�[�Ń^�O���o��
		self.tail_n  = 0	# �ȍ~��"};"�Ń^�O���o��
		self.class_n = 0	# class��`(0:��`�O�Abrace+1:��`��)
		self.tag_info = []	# ���������^�O���[[�^�O, �t�@�C����, �s����������]]

	def analyze(self, file, lines):
		self.file = file
		expr = "[a-zA-Z0-9_]+|[()\\[\\]{};]"
		expr += "|//|/\\*|\\*/"
		expr += "|#define|enum|class"
		expr += "|\".*\"|\'.*\'"

		for text in lines:
			self.cur_text = text
			words = re.findall(expr, text)
			self.srch_key(words)

		return self.tag_info


	def srch_key(self, words):
		pre_key = ""

		for idx, key in enumerate(words):
			if self.comment == 0:
				if self.div_f and key != ";" and self.brace == self.class_n:
					list = [self.pre_word, self.file, self.save_text]
					self.tag_info.append(list)
				self.div_f = False

				if self.head_f:
					list = [key, self.file, self.cur_text]
					self.tag_info.append(list)
					self.head_f = False

				if key == "/*":
					self.comment = 1
				elif key == "//":
					return
				elif key == "(":
					self.paren += 1
					self.pre_word = pre_key
					self.save_text = self.cur_text
				elif key == ")":
					self.paren -= 1
					self.div_f = True
				elif key == "{":
					self.brace += 1
				elif key == "}":
					self.brace -= 1
				elif key == "[":
					self.bracket += 1
				elif key == "]":
					self.bracket -= 1
				elif key == ";":
					if self.tail_n > 0 and self.brace == (self.tail_n - 1):
						list = [pre_key, self.file, self.cur_text]
						self.tag_info.append(list)
						self.tail_n = 0

					if self.class_n > 0 and self.brace == (self.class_n - 1):
						self.class_n = 0

				elif key in ("#define", "enum", "class") and idx == 0:
					self.head_f = True
					if key == "class":
						#self.clas_f = 1
						self.class_n = self.brace + 1
				elif key == "typedef" and idx == 0:
					self.tail_n = self.brace + 1
			else:
				if key == "*/":
					self.comment = 0

			pre_key = key


class FileSearch():
	"""
	�t�@�C�����⊮����
	Attributes:
		list[]    : �擾�����t�@�C�������
	"""


	def __init__(self):
		self.list = []


	def isearch(self, srch):
		"""
		�t�@�C�����̃C���N�������g����
		"""
		next_file = ""

		if srch in self.list:
			idx = self.list.index(srch)
			idx += 1
			if len(self.list) <= idx:
				idx = 0

			next_file = self.list[idx]
		else:
			self.list = []
			srch += "*"
			path = os.path.dirname(srch)
			file = os.path.basename(srch)
			for pathfile in Path(path).glob(file):
				pathfile = str(pathfile)
				self.list.append(pathfile)

			if len(self.list) > 0:
				next_file = self.list[0]

		return next_file


#=== common function ============================================================
def enable():
	"""
	�R�}���h�v�����v�g��ESC�V�[�P���X�L����
	"""
	INVALID_HANDLE_VALUE = -1
	STD_INPUT_HANDLE  = -10
	STD_OUTPUT_HANDLE = -11
	STD_ERROR_HANDLE  = -12
	ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
	ENABLE_LVB_GRID_WORLDWIDE = 0x0010

	hOut = windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
	if hOut == INVALID_HANDLE_VALUE:
		return False
	dwMode = wintypes.DWORD()
	if windll.kernel32.GetConsoleMode(hOut, byref(dwMode)) == 0:
		return False
	dwMode.value |= ENABLE_VIRTUAL_TERMINAL_PROCESSING
	if windll.kernel32.SetConsoleMode(hOut, dwMode) == 0:
		return False
	return True


def set_ext_pattern(file):
	"""
	�g���q�ɉ����������p�^�[���̐ݒ�
	"""
	global syntax_list
	global multi_line_ptn
	global comment_ptn
	global quote_ptn

	ext = os.path.splitext(file)[-1]

	# syntax���X�g�̐ݒ�
	if ext in syntax_dic:
		syntax_list = syntax_dic[ext]
	else:
		syntax_list = ()

	# �����s�̋����p�^�[���̐ݒ�
	if ext in multi_line_dic:
		multi_line_ptn = multi_line_dic[ext]
	else:
		multi_line_ptn = ["", "", ""]

	# �R�����g�����p�^�[���̐ݒ�
	if ext in comment_dic:
		comment_ptn = comment_dic[ext]
	else:
		comment_ptn = ""

	# �N�H�[�e�[�V���������p�^�[���̐ݒ�
	if ext in comment_dic:
		quote_ptn = quote_dic[ext]
	else:
		quote_ptn = ""

# debug�pCtrl�f�[�^�̕\���ݒ�
def set_ctrl_info():
	debug_print.append(f"read_files={display.read_files}")
	for i, ctrl in enumerate(display.file_ctrl):
		debug_print.append(f"file_ctrl[{i}]={ctrl.read_file}, {ctrl.act}")
	debug_print.append(f"read_index={display.read_index}")
	debug_print.append(f"read_count={display.read_count}")
	for i, tag_ctrl in enumerate(display.tag_file):
		for j, ctrl in enumerate(tag_ctrl):
			debug_print.append(f"tag_file[{i}][{j}]={ctrl.read_file}, {ctrl.act}")


#=== main ======================================================================
# Debug�p
debug_print = []

# ESC�V�[�P���X�L����
enable()

# �����̉��
param = ParamInfo()
stat = param.analyze(sys.argv)
if stat == False:
	print(f"{param.err_msg}")
	sys.exit(0)

if len(param.read_files) == 0:
	print(f"{usage}")
	sys.exit(0)

# �O���[�o���ϐ��̒�`
history = HistoryCtrl()
display = DispCtrl()
keyctrl = KeyCtrl()
display.tab_stop = param.tab_stop
taginfo = TagInfo()

# �L�[�}�b�v�̐ݒ�
keyctrl.read_env()

if param.make_tag_file != "":
	# �^�O�t�@�C���̍쐬
	display.set_read_file(param.read_files)
	for i in range(0, display.read_count):
		display.read_index = i + 1
		file_ctrl = display.get_file_ctrl()

	with open(param.make_tag_file, "w") as f:
		for list in taginfo.tag_table:
			f.write(f"{list[0]}\t{list[1]}\t/^{list[2]}$/\n")
else:
	# �^�O���e�[�u���̍쐬
	taginfo.read_file(param.read_tag_file)

	# �L�[���͐���
	display.set_read_file(param.read_files)
	file_ctrl = display.get_file_ctrl()
	file_ctrl.disp_line()
	number = 0 # ���͒��̐��l

	help_flag = False
	end_flag = False
	while end_flag == False:
		num_flag = False
		loop_cnt = 1 if number == 0 else number
		msg = ""

		#key = ord(getch())
		key = ord(keyctrl.getkey())
		if key in (0x20, 0x66):	# Space, 'f'
			msg = file_ctrl.vscroll(display.vscroll * loop_cnt, DIR_FORWARD)
		elif key == 0x62:	# 'b'
			msg = file_ctrl.vscroll(display.vscroll * loop_cnt, DIR_REVERSE)
		elif key == 0x64:	# 'd'
			msg = file_ctrl.vscroll(int(display.vscroll/2)*loop_cnt, DIR_FORWARD)
		elif key == 0x75:	# 'u'
			msg = file_ctrl.vscroll(int(display.vscroll/2)*loop_cnt, DIR_REVERSE)
		elif key in (0x6a, 0x0d, 0x0a, 0x0e):	# 'j', CR, LF, ^N
			msg = file_ctrl.vscroll(loop_cnt, DIR_FORWARD)
		elif key in (0x6b, 0x10):	# 'k', ^P
			msg = file_ctrl.vscroll(loop_cnt, DIR_REVERSE)
		elif key == 0x3e:	# '>'
			file_ctrl.hscroll(DIR_FORWARD, number)
		elif key == 0x3c:	# '<'
			file_ctrl.hscroll(DIR_REVERSE, number)
		elif key == 0x6c:	# 'l'
			file_ctrl.next_word(loop_cnt)
		elif key == 0x68:	# 'h'
			file_ctrl.prev_word(loop_cnt)
		elif key == 0x4a:	# 'J'
			file_ctrl.next_line(loop_cnt)
		elif key == 0x4b:	# 'K'
			file_ctrl.next_line(-1 * loop_cnt)
		elif key == 0x4d:	# 'M'
			file_ctrl.middle_line()
		elif key == 0x2f:	# '/'
			msg = file_ctrl.srch_word(DIR_FORWARD, loop_cnt, True)
		elif key == 0x3f:	# '?'
			msg = file_ctrl.srch_word(DIR_REVERSE, loop_cnt, True)
		elif key == 0x0c:	# '^L'
			display.get_term()
			file_ctrl.disp_line()
		elif key == 0x6e:	# 'n'
			msg = file_ctrl.srch_word(DIR_FORWARD, loop_cnt, False)
		elif key == 0x70:	# 'p'
			msg = file_ctrl.srch_word(DIR_REVERSE, loop_cnt, False)
		elif key == 0x74:	# 't'
			if number > 0:
				display.tab_stop = number
			file_ctrl.disp_line()
		elif key == 0x4e:	# 'N'
			if help_flag == False:
				file_ctrl = display.next_file_ctrl(loop_cnt)
				file_ctrl.disp_line()
		elif key == 0x50:	# 'P'
			if help_flag == False:
				file_ctrl = display.prev_file_ctrl(loop_cnt)
				file_ctrl.disp_line()
		elif key == 0x67:	# 'g'
			file_ctrl.goto_line(1, number)
		elif key == 0x47:	# 'G'
			file_ctrl.goto_line(0, number)
		elif key == 0x6d:	# 'm'
			msg = file_ctrl.set_mark("")
		elif key == 0x27:	# \'
			msg = file_ctrl.goto_mark("")
		elif key == 0x40:	# '@'
			msg = file_ctrl.set_mark("@")
		elif key == 0x07:	# ^G
			if help_flag == False:
				file_ctrl.disp_fname(full=True)
				getch()
				file_ctrl.disp_line()
		elif key in (0x7b, 0x7d, 0x5b, 0x5d):	# {}[]
			file_ctrl.srch_brace()
		elif key in (0x69, 0x49):	# 'i', 'I'
			if help_flag == False:
				select_f = True if key == 0x49 else False
				msg = file_ctrl.tag_jump(select_f)
				if re.search(r"^E:", msg) == None:
					file_ctrl = display.tag_file[display.read_index - 1][-1]
					file_ctrl.disp_line()
				msg = re.sub(r"^.:", "", msg)
		elif key == 0x6f:	# 'o'
			if help_flag == False:
				if len(display.tag_file[display.read_index - 1]) > 0:
					display.tag_file[display.read_index - 1].pop(-1)
					file_ctrl = display.get_file_ctrl()
					file_ctrl.disp_line()
		elif key == 0x72:	# 'r'
			msg = file_ctrl.add_tagfile()
		elif key == 0x21:	# '!'
			#display.clear_screen()
			#for line in debug_print:
			#	print(line)
			#getch()
			debug_print = []
			file_ctrl.disp_line()
		elif key == 0x08:	# ^H
			if number > 0:
				number = int(number / 10)
				if number != 0:
					num_flag = True
			else:
				if help_flag == False:
					help_flag = True
					save_ctrl = file_ctrl
					file_ctrl = display.set_help()
					file_ctrl.disp_line()
		elif key == 0x71:	# 'q'
			if help_flag == True:
				help_flag = False
				file_ctrl = save_ctrl
				save_ctrl = None
				file_ctrl.disp_line()
			else:
				end_flag = True
		else:
			if help_flag == False:
				if key in range(0x30, 0x3a):	# �����H
					number = 10 * number + (key - 0x30)
					num_flag = True
				else:
					msg = "Press ^H for help."

		if num_flag:
			display.clear_tail_line()
			display.move_print(1, display.term_lines, f":{number}")
		else:
			number = 0
			if help_flag == True:
				msg = display.set_help_msg()

			if msg != "":
				display.disp_message(msg)
			else:
				file_ctrl.disp_fname()

			display.move_cursor(file_ctrl.cursor_x, file_ctrl.cursor_y)

	# �I�����ɃJ�[�\������ʍŉ��s�ֈړ�
	display.move_cursor(1, display.term_lines)
