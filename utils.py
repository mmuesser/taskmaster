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

	key_words = []

	@classmethod
	def auto_complete(cls, text, state):
		return [i for i in cls.key_words if i.startswith(text)][state]

class FdManager:

	def __init__(self, stdout, stderr):
		# /dev/null -> -3
		self.stdout = open(stdout, 'a')
		self.stderr = open(stderr, 'a')

	def close(self):
		[fd.close() for fd in (self.stdout, self.stderr)]