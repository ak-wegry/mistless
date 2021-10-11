# coding: shift_jis 
# =============================================================================
# プログラム・トレース・ツール
# =============================================================================
# [変更履歴]
# Ver0.00  2021/06/05 作成開始
# Ver1.00  2021/10/11 新規作成

usage = """
プログラム・トレース・ツール  [Ver1.00  2021/10/11]

mistless.py [option] filename ...
   [option]
    -m filename : タグファイルの作成
    -t filename : タグファイルの指定(指定なし:tags)
    -x n        : タブストップの指定(指定なし:4)
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
## ESCシーケンス有効化用
from ctypes import windll, wintypes, byref
from functools import reduce

# 固定値
MAX_HISTORY = 20	# コマンド履歴の最大数

SCROLL_PAGE = 2	# 検索でスクロール移動する前後のページ数(それ以上はジャンプ)

MODE_WORD = 0	# ワード単位の移動
MODE_CHAE = 1	# 文字単位の移動

DIR_FORWARD = 1	# 順方向
DIR_REVERSE = 2	# 逆方向

MORE_CHAR = "$"     # マルチバイト文字が途中で途切れる際の表示文字
TAG_FILE = "tags"   # defaultのタグファイル名

ESC_PTN       = "\x1b\[[0-9;]*m"	# ESCシーケンスのパターン
ESC_INIT      = "\x1b[m"	# 色の初期化
ESC_REVERSE   = "\x1b[7m"	# 反転
ESC_UNDERLINE = "\x1b[4m"	# 下線
ESC_BLACK     = "\x1b[30m"	# フォント:黒
ESC_RED       = "\x1b[31m"	# フォント:赤
ESC_GREEN     = "\x1b[32m"	# フォント:緑
ESC_YELLOW    = "\x1b[33m"	# フォント:黄色
ESC_BLUE      = "\x1b[34m"	# フォント:青
ESC_PURPLE    = "\x1b[35m"	# フォント:紫
ESC_CYAN      = "\x1b[36m"	# フォント:シアン
ESC_WHITE     = "\x1b[37m"	# フォント:白
ESC_BG_BLACK  = "\x1b[40m"	# 背景色:黒
ESC_BG_RED    = "\x1b[41m"	# 背景色:赤
ESC_BG_GREEN  = "\x1b[42m"	# 背景色:緑
ESC_BG_YELLOW = "\x1b[43m"	# 背景色:黄色
ESC_BG_BLUE   = "\x1b[44m"	# 背景色:青
ESC_BG_PURPLE = "\x1b[45m"	# 背景色:紫
ESC_BG_CYAN   = "\x1b[46m"	# 背景色:シアン
ESC_BG_WHITE  = "\x1b[47m"	# 背景色:白

syntax_list = ()
syntax_list_py = ("break", "continue", "del", "except", "exec", "finally", "pass", "print", "raise", "return", "try", "with", "global", "assert", "lambda", "yield", "def", "class", "for", "while", "if", "elif", "else", "and", "in", "is", "not", "or", "import", "from", "as")	# pythonのkeyword
syntax_list_c = ("void", "char", "short", "int", "long", "float", "double", "auto", "static", "const", "signed", "unsigned", "extern", "volatile", "register", "return", "goto", "if", "else", "switch", "case", "default", "break", "for", "while", "do", "continue", "typedef", "struct", "enum", "union", "sizeof") # C言語
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
	引数に関する情報

	Attributes:
		read_files[]  : 入力ファイル名
		read_tag_file : 入力タグファイル名
		make_tag_file : 出力タグファイル名
		tab_stop      : タブストップ数
		err_msg       : 解析時のエラーメッセージ
	"""


	def __init__(self):
		self.read_files = []
		self.read_tag_file = ""
		self.make_tag_file = ""
		self.tab_stop = 4
		self.err_msg = ""


	def analyze(self, argv):
		"""
		引数の解析
		Args:
			argv (list): 引数

		Returns:
			boolean: True チェックOK, False チェックNG
		"""
		opt_id = ""
		for arg in argv[1:]:
			if opt_id == "":
				if re.match(r"^-[mtx]$", arg) is not None:
					opt_id = arg
				elif arg[0] == "-":
					self.err_msg = f"不明なオプション({arg})です。"
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
							self.err_msg = f"ファイル({arg})が存在しません。"
							break
			else:
				if opt_id == "-m":
					self.make_tag_file = arg
					opt_id = ""
				elif opt_id == "-t":
					if Path(arg).exists() == True:
						self.read_tag_file = arg
					else:
						self.err_msg = f"タグファイル({arg})が存在しません。"
						break
					opt_id = ""
				elif opt_id == "-x":
					self.tab_stop = int(arg)
					opt_id = ""

		return (self.err_msg == "")


class Escape():
	"""
	ESCコードの設定に関する処理

	Attributes:
		only_text : ESCコードを除外した文字列
		esc_list  : 1文字毎に対応したESCコード
	"""

	def __init__(self):
		self.only_text= ""	# ESCコードを除外した文字列
		self.esc_list = []	# 1文字毎に対応したESCコード

	def analyze_text(self, esc_text):
		# ESC除外した文字列、[位置, ESCコード]リストを作成
		pre_end = 0
		esc_info = []		# [位置, ESCコード]
		self.only_text = ""	# ESCコードを除外した文字列
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

		# 1文字毎に対応したESCリストを作成
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
		# ESC除外した文字列内の文字列を検索し、ESCリストにESCコード設定
		iter = re.finditer(srch_text, self.only_text)
		for n in iter:
			start = n.span()[0]
			end   = n.span()[1]
			for i in range(start, end):
				self.esc_list[i] = re.sub(r"\x1b\[|m", "", esc_code)


	def coating_pos(self, start, end, esc_code):
		# 特定位置のESCリストにESCコード設定
		for i in range(start, end):
			self.esc_list[i] = re.sub(r"\x1b\[|m", "", esc_code)


	def get_esc_text(self):
		# ESCリストからESCコードを埋め込んだ文字列を作成
		pre_idx = 0
		pre_num = ""
		esc_text = ""
		for i, esc_num in enumerate(self.esc_list):
			if pre_num != esc_num:
				esc_text += self.only_text[pre_idx:i]
				if pre_num in list("0123456789"):
					# 1つ前が反転/強調等の場合は、終了コードを入れる
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
	キー変換に関する情報
	Attributes:
		map[] : キー変換情報([[入力キー, 変換キー]])
		store : 蓄積文字列(変換した取得途中のキー)
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
			# mapファイル読込み
			with open(file, "rb") as f:
				txt = f.read()
			guess = chardet.detect(txt).get("encoding")
			if guess is None:
				guess = locale.getpreferredencoding()
			data = txt.decode(guess).splitlines()

			# map情報登録
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
		# 蓄積文字がある場合、変換しない
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
	表示に関する情報

	Attributes:
		term_width : 画面幅数
		term_lines : 画面行数
		vscroll    : 縦スクロール数
		hscroll    : 横スクロール数
		tab_stop   : タブストップ数
		move_mode  : カーソルの移動モード
		read_files : 入力ファイルのリスト
		file_ctrl  : 入力ファイルに対応するFileCtrlリスト
		read_index : 表示する入力ファイルのリスト内位置
		read_count : 入力ファイル数
		tag_file   : タグジャンプした時に追加するFileCtrlリスト
		srch_str   : 検索の文字列
		srch_dir   : 検索の方向
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
		print(f"\x1b[0K", end="") # カーソル位置から右側消去


	def clear_eob(self):
		print(f"\x1b[0J", end="") # カーソル位置から画面右下まで消去


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
【(キー)コマンド】
    ^X          Ctrl+Xを表す
    <n>         コマンド直前に数字キーで指定される値
    <a-z>       'a'～'z'の1文字キー入力を表す
				
  ＜基本＞
    ^H          コマンドのヘルプを表示
    q           終了

  ＜スクロール＞
	f,SPACE     <n>画面先にスクロール(<n>指定なし:1画面)
    b           <n>画面前にスクロール(<n>指定なし:1画面)
    d           <n>半画面先にスクロール(<n>指定なし:半画面)
    u           <n>半画面前にスクロール(<n>指定なし:半画面)
    j           <n>行先にスクロール(<n>指定なし:1行)
    k           <n>行前にスクロール(<n>指定なし:1行)
	>           右へ<n>カラム分スクロール(<n>指定なし:画面幅の半分)
    <           左へ<n>カラム分スクロール(<n>指定なし:画面幅の半分)

  ＜タグジャンプ＞
    i           カーソル位置の文字列でタグジャンプ
	I           カーソル位置の文字列でタグジャンプ(複数タグ:メニューから選択)
    o           タグジャンプ前の位置へ戻る
    r           指定したタグファイルを追加読込み

  ＜カーソル移動＞
    J           カーソルを<n>行下に移動(<n>指定なし:1行)
    K           カーソルを<n>行上に移動(<n>指定なし:1行)
    M           カーソルを画面内中央行に移動
    l           カーソルを次の<n>番目のキーワードに移動(<n>指定なし:1番目)
    h           カーソルを前の<n>番目のキーワードに移動(<n>指定なし:1番目)
    g           ファイルの<n>行目を表示(<n>指定なし:先頭行)
    G           ファイルの<n>行目を表示(<n>指定なし:最終行)
    {,},[,]     カーソル位置の括弧に対応する括弧へ移動
    m<a-z>      現在の画面/カーソル位置を入力キー文字へ設定
    @           現在の画面/カーソル位置を設定
    '<a-z>      入力キー文字に設定された画面/カーソル位置へ移動
    ''          移動直前の画面/カーソル位置へ戻る


  ＜検索＞
    /           指定した文字列で順方向検索(完全一致)
    ?           指定した文字列で逆方向検索(完全一致)
                  ^G     カーソル位置の文字列を取込み
                  ^F     カーソルを右に移動
                  ^B     カーソルを左に移動
                  ^D     カーソル位置の文字を削除
                  ^H     カーソル前の文字を削除
                  ^N, ^P 検索履歴の文字列リストを表示
                  ESC    入力のキャンセル
    n           直前に実行された検索を順方向へ<n>回実行(<n>指定なし:1回)
    p           直前に実行された検索を逆方向へ<n>回実行(<n>指定なし:1回)

  ＜ファイル切替＞
	N           複数ファイル読込み時、<n>番後のファイルを表示(<n>指定なし:直後)
    P           複数ファイル読込み時、<n>番前のファイルを表示(<n>指定なし:直前)

  ＜その他＞
    t           タブストップ幅を<n>に変更
    ^G          ファイル名、カーソル位置を表示
    ^L          画面の再表示(画面サイズを再取得)

【初期設定】
   環境変数 MISTLESS_INIT に設定されたファイルを起動時に読み込み、
   ユーザキー定義を登録する。 
   ＜書式＞
     map 入力キーパターン 変換パターン
	 ※パターン内の制御コードを16進数(\\xFF)、8進数(\\777)で表記することが可能

【機能仕様】
  ・入力ファイルの文字コード(UTF8, euc等)を表示画面の文字コードに変換して表示
  ・入力ファイルの拡張子に応じて、キーワード/コメント等を色分け表示
    (.py .h .cpp .c .awk に対応)
  ・入力ファイルの拡張子に応じて、タグ情報を自動生成
    (ただし、起動時にタグファイルを読み込んだ場合は、自動生成しない)
  ・同一キーワードのタグ情報が複数ある場合は、選択してタグジャンプ可能

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
	入力ファイルに関する制御

	Attributes:
		read_file : 入力ファイル名
		act       : データ読込み表示
		data []   : 読込みデータ
		coating []: 読込みデータ行への強調表示
		max_line  : 読込みデータ行
		disp_top  : 表示開始行位置
		disp_left : 表示開始列位置
		cursor_x  : カーソル行位置
		cursor_y  : カーソル列位置
		tag_key   : タグジャンプ時のキーワード
		mark {}   : 画面/カーソル位置{'@a-z': [top, left, x, y]}
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
				# 入力文字列のエンコーディング判定
				guess = chardet.detect(txt).get("encoding")
				if guess is None:
					guess = locale.getpreferredencoding()
				elif guess == "ISO-2022-JP":
					# JIS7限定の特殊処理
					guess = "ISO-2022-JP-EXT"
				elif guess == "ISO-8859-1" or guess == "KOI8-R":
					# JIS8->JIS7変換(特殊処理)
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
		行全体の強調
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
		漢字コードを含む文字列の長さ取得

		Args:
			text (str): 文字列

		Returns:
			int: 画面表示上の幅(全角:2, 半角:1)
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
		開始位置/加算数/境界位置から境界位置の前後数判定

		Args:
			cur_pos (int): 開始位置(0～)
			add_len (int): 加算数
			border_pos (int): 境界位置

		Returns:
			touch (int): True:境界位置に接地(跨ぐ場合含む)
			left  (int): 境界位置より前の文字数
			right (int): 境界位置より後の文字数
		"""
		touch = False	# 境界位置との接地(跨ぐ場合含む)
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
		keywordの強調
		"""
		if line_coating != "":
			# 行の強調
			esc_ctrl.coating_word(".*", line_coating)
		else:
			# syntaxの強調
			iter = re.finditer("[a-zA-Z0-9_]+", esc_ctrl.only_text)
			for n in iter:
				start = n.span()[0]
				end   = n.span()[1]
				word  = n.group()
				if word in syntax_list:
					esc_ctrl.coating_pos(start, end, ESC_GREEN)

			# (ダブル)クォーテーションの強調設定
			esc_ctrl.coating_word(quote_ptn, ESC_CYAN)

			# コメントの強調
			esc_ctrl.coating_word(comment_ptn, ESC_BLUE)

		# 制御コードの強調
		esc_ctrl.coating_word("[\x00-\x08\x0a-\x1f]", ESC_REVERSE)

		# 検索キーの強調
		if display.srch_str != "":
			esc_ctrl.coating_word(display.srch_str, ESC_BG_YELLOW)


	def cut_text(self, line, start, width, coating):
		"""
		文字列から開始位置/幅で指定した文字列の切出し

		Args:
			line (char): 文字列
			start (int): 開始位置(1～)
			width (int): 切出し幅
			coating (str): 行強調ESCシーケンス


		Returns:
			str: 切出した文字列
		"""
		esc_ctrl = Escape()
		esc_ctrl.analyze_text(line)
		self.highlight_text(esc_ctrl, coating)

		cut_pid = "srch"  # 切出し開始位置の検索
		cut_txt = ""
		pre_esc_num = ""  # 1文字前の強調表示番号
		pos = 0           # 先頭からの文字幅
		stt = start - 1   # 切出し開始位置
		left_more = False # 切出し文字の先頭を"$"表示
		for i, in_char in enumerate(line):
			# 1文字の表示形式と長さ取得
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

			# 文字列の最初と最後を判定
			if (i == 0) or (i == (len(line) - 1)):
				line_edge = True
			else:
				line_edge = False

			if cut_pid == "srch":
				# 切出し開始位置の検索
				(touch, left, right) = self.judge_border(pos, wd, stt)
				if left == 0:
					add_ch = ch
				else:
					add_ch = MORE_CHAR * right

				if touch:
					cut_pid = "cut" # 切出しの開始
					if stt > 0 and right == 0:
						left_more = True
			else:
				# 切出しの開始
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
					cut_pid = "end" # 切出し終了

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
		前後のワード位置取得

		Args:
			text (str): 文字列
			cur_idx (str): 文字列の現在位置(0～, -1:不定)

		Returns:
			int: 一つ前のワード位置(0～:有, -1:無)
			int: 一つ後のワード位置(0～:有, -1:無)
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

		# 次の行のカーソル位置Xを算出
		(line, line_idx, char_idx, pos) = self.get_current_param()

		### index位置でなく、カーソル位置で比較するように修正 ###
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
		pre_char = ""	# 漢字入力の1Byte目コード保存用
		idx = 0			# cmd内のカーソル位置
		shift = 1		# cmd文字列が画面横幅内で表示できない場合の表示開始位置
		offset = 0		# ^Gの文字取込時の行内参照位置
		cmd = ""		# 入力したコマンド文字列
		end_flag = 	False
		while end_flag == False:
			#key = ord(getch())
			key = ord(keyctrl.getkey())
			if key == 0x06: # ^F
				# カーソル右移動
				idx = (idx + 1) if (idx < len(cmd)) else idx
			elif key == 0x02: # ^B
				# カーソル左移動
				idx = (idx - 1) if (idx > 0) else idx
			elif key == 0x01: # ^A
				# カーソル行頭移動
				idx = 0
			elif key == 0x05: # ^E
				# カーソル行末移動
				idx = len(cmd)
			elif key == 0x04: # ^D
				# カーソル位置の1文字削除
				if cmd != "":
					cmd = cmd[:idx] + cmd[idx+1:]
			elif key == 0x08: # ^H
				# カーソル左の1文字削除
				if cmd != "":
					cmd = cmd[:idx-1] + cmd[idx:]
					idx -= 1
				else:
					end_flag = True
			elif key == 0x09: # ^I
				if file_srch:
					pass # ファイル名補完
					arg = re.split(r"[ \t]",cmd[:idx])
					file = filesrch.isearch(arg[-1])
					ins_idx = idx - self.unicode_len(arg[-1])
					cmd = cmd[:ins_idx] + file
					idx = len(cmd)
				else:
					if limit == "" or re.match(limit, chr(key)) != None:
						cmd = cmd[:idx] + chr(key) + cmd[idx:]
						idx += 1
			elif key == 0x07 and limit == "": # ^G (文字制限なしの場合のみ)
				# カーソル位置文字取込み
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
				# 履歴(1つ前)
				cmd = history.get_prev()
				idx = len(cmd)
			elif key == 0x0e: # ^N
				# 履歴(1つ後)
				cmd = history.get_next()
				idx = len(cmd)
			elif key in (0x0d, 0x0a): # CR, LF
				# 入力終了
				history.reg_hist(cmd)
				end_flag = True
			elif key == 0x1b: # ESC
				# 入力キャンセル
				cmd = ""
				idx = 0
				end_flag = True
			else:
				if pre_char == "":
					if limit == "" or re.match(limit, chr(key)) != None:
						if key >= 0x80:
							pre_char = bytes([key]) # ()内の値は[]で囲む
						elif key >= 0x20 or key == 0x09:
							cmd = cmd[:idx] + chr(key) + cmd[idx:]
							idx += 1
				else:
					# 2Byteの漢字コード処理
					pre_char += bytes([key]) # ()内の値は[]で囲む
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
		# Y方向の表示調整
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

		# X方向の表示調整
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

		# 検索文字列の入力
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

		# 文字列の検索
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

		# 検索方向に一致が無くても、同一画面の逆方向の一致文字を強調表示
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
		# キーワードの取得
		keyword = self.get_current_word()

		# タグ情報テーブルの検索
		tag_list = taginfo.srch_keyword(keyword)
		if len(tag_list) == 0:
			return "E:No such tag"

		# タグ情報の選択
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

		# ジャンプ先ファイル読込み
		if Path(file).exists() == False:
			return f"E:No such file({file})"
		new_ctrl = FileCtrl()
		new_ctrl.set_file(file)

		# ジャンプ先ファイル内の検索
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

		# 表示エリアの算出
		list_max = len(tag_list)
		minus_idx = 2 * list_max + 2
		if minus_idx < display.term_lines:
			self.disp_fname(minus_idx)
		else:
			minus_idx = display.term_lines
			if minus_idx % 2 == 1:
				disp_data.append("")

		# 表示用タグ情報の保存
		(tag, file, srch) = tag_list[0]
		tag_width = display.term_width - 8
		tag_txt = self.cut_text(tag, 1, tag_width, "")
		title = f"{ESC_CYAN}No. tag={ESC_INIT}{tag_txt}"
		disp_data.append(title)

		file_width = display.term_width - 4	# "No. "の幅を減算
		srch_width = display.term_width - 6 # 先頭インデント幅を減算
		for i, tag_info in enumerate(tag_list):
			(tag, file, srch) = tag_info
			file_txt = self.reduce_text(file, file_width)
			srch_txt = self.cut_text(srch, 1, srch_width, "")
			disp_data.append(f"{i+1:3d} {file_txt}")
			disp_data.append(f"      {srch_txt}")

		# 表示用タグ情報のMore表示
		self.disp_more(disp_data, minus_idx)

		# タグ情報の選択
		tag_info = ["", "", ""]
		cmd = self.get_command("番号を選択してください: ", limit="[0-9]")
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
		対応する括弧((), {}, [])を探す
		"""
		match_cnt = 0
		add_idx = 1		# 対応する括弧を検索する方向
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
					# 次の検索文字あり
					if next_idx >= 0:
						srch_char = line[next_idx]
						idx = next_idx
				else:
					# 前の検索文字あり
					if prev_idx >= 0:
						srch_char = line[prev_idx]
						idx = prev_idx

			if idx != -1:
				# 次/前の検索文字あり
				if srch_char in ("(", "{", "["):
					match_cnt += 1
				elif srch_char in (")", "}", "]"):
					match_cnt -= 1

				# 対応する括弧発見
				if match_cnt == 0:
					self.scroll_caret(line_idx, idx)
					end_flag = True
			else:
				# 次/前の検索文字なし
				line_idx += add_idx
				if line_idx >=0 and line_idx < (self.max_line):
					# 次/前の行を検索
					line = self.data[line_idx]
					if add_idx > 0:
						idx = -1
					else:
						idx = len(line)
				else:
					end_flag = True


	def add_tagfile(self):
		# タグファイル名の入力
		file = self.get_command("Add TagFile: ", True)
		if Path(file).exists() == False:
			return "No such file"

		if file != "":
			# タグ情報テーブルの作成
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
	コマンド履歴制御

	Attributes:
		max_cnt     : 履歴の登録最大数
		hist_idx    : 参照する履歴位置(-1, 0, ..., max_cnt-1, max_cnt)
		hist_list[] : 履歴リスト
	"""
	def __init__(self, max_cnt=MAX_HISTORY):
		self.max_cnt = max_cnt
		self.hist_idx = 0
		self.hist_list = []


	def reg_hist(self, text):
		# 入力文字と同一文字をリストから削除
		if text in self.hist_list:
			self.hist_list.remove(text)

		# 履歴の最大数以上の場合、一番古い履歴をリストから削除
		if self.max_cnt <= len(self.hist_list):
			del self.hist_list[0]

		# 最新の履歴をリストの最後に追加
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
	タグジャンプに関する情報

	Attributes:
		tag_table[] : タグ情報(キーワード、ファイル名、行検索文字列)のリスト
		input_file  : タグファイルからの読込み有無(True/False)
	"""
	def __init__(self):
		self.tag_table = []
		self.input_file = False


	def read_file(self, tag_file):
		"""
		タグファイルを読込み、タグ情報テーブルへ登録
			Args:
				tag_file (str): タグファイル名

			Returns:
				なし
		"""
		# タグファイル名のチェック
		if tag_file != "":
			file = tag_file
		else:
			file = TAG_FILE

		if Path(file).exists() == False:
			return

		# タグファイル読込み
		with open(file, "rb") as f:
			txt = f.read()
		guess = chardet.detect(txt).get("encoding")
		if guess is None:
			guess = locale.getpreferredencoding()
		data = txt.decode(guess).splitlines()

		# タグ情報テーブルの登録
		for line in data:
			tag_info = line.split(maxsplit=2)
			if len(tag_info) == 3:
				if re.match(r"^/\^.*\$/$", tag_info[2]) != None:
					tag_info[2] = re.sub(r"^/\^|\$/$", "", tag_info[2])
				self.tag_table.append(tag_info)
		self.input_file = True


	def analyze_file(self, file, lines):
		"""
		ソースを解析して、タグ情報テーブルへ登録
			Args:
				file (str): ファイル名
				lines (list): ソースコード

			Returns:
				なし
		"""
		# タグファイルからの読込みしている場合、解析しない
		if self.input_file == True:
			return

		# ファイル拡張子により分岐
		ext = os.path.splitext(file)[-1]
		if ext == ".py":
			# pythonの解析
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
			# C/C++の解析
			ctags = Ctags()
			tag_info = ctags.analyze(file, lines)
			for list in tag_info:
				self.tag_table.append(list)
		elif ext == ".awk":
			# awkの解析
			for text in lines:
				words = re.findall(r"function|[a-zA-Z0-9_]+", text)
				if len(words) > 1:
					if words[0] == "function":
						list = [words[1], file, text]
						self.tag_table.append(list)


	def srch_keyword(self, keyword):
		"""
		タグ情報テーブルの検索
			Args:
				keyword (str): 検索するキーワード

			Returns:
				list: 検索結果[[タグ, ファイル名, 行検索文字列]]
		"""
		tag_list = []
		for record in self.tag_table:
			if keyword == record[0]:
				tag_list.append(record)

		return tag_list


class Ctags():
	"""
	C/C++のタグ情報を生成

	Attributes:
	"""
	def __init__(self):
		self.file = ""
		self.pre_word = ""
		self.cur_text = ""
		self.save_text = ""
		self.paren   = 0	# ()のネスト数
		self.brace   = 0	# {}のネスト数
		self.bracket = 0	# []のネスト数
		self.comment = 0	# /* */の開始(1)、終了(0)
		self.div_f   = False# 直後キーの";"チェック
		self.head_f  = False# 直後キーでタグ情報出力
		self.tail_n  = 0	# 以降の"};"でタグ情報出力
		self.class_n = 0	# class定義(0:定義外、brace+1:定義内)
		self.tag_info = []	# 生成したタグ情報[[タグ, ファイル名, 行検索文字列]]

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
	ファイル名補完処理
	Attributes:
		list[]    : 取得したファイル名候補
	"""


	def __init__(self):
		self.list = []


	def isearch(self, srch):
		"""
		ファイル名のインクリメント検索
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
	コマンドプロンプトのESCシーケンス有効化
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
	拡張子に応じた強調パターンの設定
	"""
	global syntax_list
	global multi_line_ptn
	global comment_ptn
	global quote_ptn

	ext = os.path.splitext(file)[-1]

	# syntaxリストの設定
	if ext in syntax_dic:
		syntax_list = syntax_dic[ext]
	else:
		syntax_list = ()

	# 複数行の強調パターンの設定
	if ext in multi_line_dic:
		multi_line_ptn = multi_line_dic[ext]
	else:
		multi_line_ptn = ["", "", ""]

	# コメント強調パターンの設定
	if ext in comment_dic:
		comment_ptn = comment_dic[ext]
	else:
		comment_ptn = ""

	# クォーテーション強調パターンの設定
	if ext in comment_dic:
		quote_ptn = quote_dic[ext]
	else:
		quote_ptn = ""

# debug用Ctrlデータの表示設定
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
# Debug用
debug_print = []

# ESCシーケンス有効化
enable()

# 引数の解析
param = ParamInfo()
stat = param.analyze(sys.argv)
if stat == False:
	print(f"{param.err_msg}")
	sys.exit(0)

if len(param.read_files) == 0:
	print(f"{usage}")
	sys.exit(0)

# グローバル変数の定義
history = HistoryCtrl()
display = DispCtrl()
keyctrl = KeyCtrl()
display.tab_stop = param.tab_stop
taginfo = TagInfo()

# キーマップの設定
keyctrl.read_env()

if param.make_tag_file != "":
	# タグファイルの作成
	display.set_read_file(param.read_files)
	for i in range(0, display.read_count):
		display.read_index = i + 1
		file_ctrl = display.get_file_ctrl()

	with open(param.make_tag_file, "w") as f:
		for list in taginfo.tag_table:
			f.write(f"{list[0]}\t{list[1]}\t/^{list[2]}$/\n")
else:
	# タグ情報テーブルの作成
	taginfo.read_file(param.read_tag_file)

	# キー入力制御
	display.set_read_file(param.read_files)
	file_ctrl = display.get_file_ctrl()
	file_ctrl.disp_line()
	number = 0 # 入力中の数値

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
				if key in range(0x30, 0x3a):	# 数字？
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

	# 終了時にカーソルを画面最下行へ移動
	display.move_cursor(1, display.term_lines)
