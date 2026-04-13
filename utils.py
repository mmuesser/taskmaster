from enum import Enum

class State(Enum):
	INIT = "INITIALISATION"
	STARTING = "STARTING"
	RUNNING = "RUNNING"
	STOPPED = "STOPPED"
	FAILED = "FAILED"
	KILLED = "KILLED"
	SUCCESS = "SUCCESS"

class TabComplete:

	key_words = set()

	@classmethod
	def auto_complete(cls, text, state):
		return [i for i in cls.key_words if i.startswith(text)][state]

class FdManager:

	def __init__(self, stdout, stderr):
		# /dev/null -> -3
		self.stdout = stdout
		self.stderr = stderr

	def open(self):
		self.stdout_fd = open(self.stdout, 'a')
		self.stderr_fd = open(self.stderr, 'a')

	def close(self):
		[fd.close() for fd in (self.stdout_fd, self.stderr_fd)]