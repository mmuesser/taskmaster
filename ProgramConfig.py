from enum import Enum
import signal
from main import logger
from utils import State



def get_signal(string: str):
	sig = signal.Signals.SIGSTOP
	try :
		sig = signal.Signals.__getitem__(string).value
	except KeyError:
		pass
	return sig


"Verifier comportement si config a des champs en TROP"
class ProgramConfig:
	cmd = (str, "")
	numprocs = (int, 1)
	umask = (int, 0o000)
	workingdir = (str, "/tmp")
	autostart = (bool, True)
	autorestart = (str, None)
	exitcodes = (list, [])
	startretries = (int, 0)
	starttime = (int, 0)
	stopsignal = (str, "SIGSTOP")
	stoptime = (int, 0)
	stdout = (str, "/dev/null")
	stderr = (str, "/dev/null")
	env = (dict, {})


	def __init__(self, prog, name):
		self.name = name
		lst_attr = {k: v for k, v in ProgramConfig.__dict__.items() if not callable(v) and not k.startswith("__")}
		for key in lst_attr:
			# setattr(self, key, prog[key] if isinstance(prog.get(key, None), lst_attr[key][0]) else (lst_attr[key][1] and print(self.name, ": Base value ", lst_attr[key][1], "is set for", key)))
			value = prog.get(key, None)
			if not isinstance(value, lst_attr[key][0]):
				value = lst_attr[key][1]
				# print(self.name, ": Base value", value, "is set for", key)
				logger.info(f"{self.name}: Base value {value} is set for {key}")
			setattr(self, key, value)
		self.stopsignal = get_signal(self.stopsignal)
		# print(self)

	def __str__(self) -> str:
		return str(vars(self))

	def __eq__(self, other):
		if not isinstance(other, ProgramConfig):
			return False
		return vars(self) == vars(other)
