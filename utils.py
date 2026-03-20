class TabComplete:

	key_words = []

	@classmethod
	def auto_complete(cls, text, state):
		return [i for i in cls.key_words if i.startswith(text)][state]

class FdManager:

	def __init__(self, stdout, stderr):
		# /dev/null -> -3
		self.stdout = open(stdout, 'a') if stdout != '/dev/null' else stdout
		self.stderr = open(stderr, 'a') if stderr != '/dev/null' else stderr
		# self.stdout = stdout
		# self.stderr = stderr

	def close(self):
		for fd in (self.stdout, self.stderr):
			if fd == '/dev/null':
				continue
			fd.close()