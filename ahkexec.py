import sublime, sublime_plugin
import subprocess
import re
from ctypes import *

class ahkexec(sublime_plugin.TextCommand):

	# SET YOUR SETTINGS HERE
	# Specify a 'key'(name it whatever you want) and assign it
	# a 'value'(string) containing the path to the AHK executable.
	# This allows the user to run code using different AHK flavors.
	# When calling the command, pass the 'key' as the argument and
	# the command will use the corresponding AHK executable.
	# NOTE: By default, it passes the key 'default', do not rename
	#       this key.
	ahk = {'default': 'C:\\Program Files\\AutoHotkey\\AutoHotkey.exe'}
	# ahk = {'default': 'D:\\PortableApps\\AutoHotkey\\AutoHotKey_C\\AutoHotkey.exe'}

	def get_code(self):
		# check if there's a selection
		code_sel = self.view.substr(self.view.sel()[0])
		if len(code_sel) != 0:
			return {'code': code_sel, "sel": True}

		# return full code if there is no selection
		code_full = self.view.substr(sublime.Region(0, self.view.size()))
		if len(code_full) != 0:
			return {'code': code_full, "sel": False}

		return False


	def run_code(self, code):
		PIPE_ACCESS_OUTBOUND = 0x00000002
		PIPE_UNLIMITED_INSTANCES = 255
		INVALID_HANDLE_VALUE = -1

		pipename = "AHK_" + str(windll.kernel32.GetTickCount())
		pipe = "\\\\.\\pipe\\" + pipename

		__PIPE_GA_ = windll.kernel32.CreateNamedPipeW(c_wchar_p(pipe),
		                                              PIPE_ACCESS_OUTBOUND,
		                                              0,
		                                              PIPE_UNLIMITED_INSTANCES,
		                                              0,
		                                              0,
		                                              0,
		                                              None)

		__PIPE_ = windll.kernel32.CreateNamedPipeW(c_wchar_p(pipe),
		                                           PIPE_ACCESS_OUTBOUND,
		                                           0,
		                                           PIPE_UNLIMITED_INSTANCES,
		                                           0,
		                                           0,
		                                           0,
		                                           None)

		if (__PIPE_ == INVALID_HANDLE_VALUE or __PIPE_GA_ == INVALID_HANDLE_VALUE):
			print("Failed to create named pipe.")
			return False

		pid = subprocess.Popen([self.ahkpath, pipe]).pid
		if not pid:
			print('Could not open file: "' + pipe + '"')
			return False

		windll.kernel32.ConnectNamedPipe(__PIPE_GA_, None)
		windll.kernel32.CloseHandle(__PIPE_GA_)
		windll.kernel32.ConnectNamedPipe(__PIPE_, None)

		script = unichr(0xfeff) + code
		written = c_ulong(0)

		fSuccess = windll.kernel32.WriteFile(__PIPE_,
		                                     script,
		                                     (len(script)+1)*2,
		                                     byref(written),
		                                     None)
		if not fSuccess:
			return False

		windll.kernel32.CloseHandle(__PIPE_)
		return pid


class ahkexecCommand(ahkexec):

	def run(self, edit, version='default'):
		# Set AHK dir
		self.ahkpath = ahkexec.ahk[version]
		# Peform case-insensitive search
		re.I
		# Continue only if syntax used is AutoHotkey or Plain text
		if not re.search("(AutoHotkey|AHK|Plain text)", self.view.settings().get('syntax')):
			print("ahkexec[cancelled] - Not an AHK code")
			return False

		filename = self.view.file_name()
		x = self.get_code()
		if filename:
			if x['sel']:
				self.run_code(x['code'])
			else:
				subprocess.Popen([self.ahkpath, filename])
			print("ahkexec[file" +
			     ("/selection] - " if x['sel'] else "] - '") +
			     filename + "'")
		else:
			pid = self.run_code(x['code'])
			print("ahkexec[unsaved" +
			     ("/selection] - " if x['sel'] else "] - ") +
			     str(pid) + "[PID]")

		# cleanup
		if hasattr(self, "ahkpath"): del self.ahkpath
