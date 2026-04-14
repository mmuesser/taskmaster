import signal, os
from logger import logger

def get_signal(string: str):
	sig = signal.Signals.SIGSTOP
	try :
		sig = signal.Signals.__getitem__(string).value
	except KeyError:
		logger.warning(f"{string} not in signal, default to SIGSTOP")
		pass
	return sig


class ProgramConfig:
	cmd = (str, "")
	numprocs = (int, 1)
	umask = (int, 0o000)
	workingdir = (str, "/tmp")
	autostart = (bool, True)
	autorestart = (str, 'never')
	exitcodes = (list, [])
	startretries = (int, 0)
	starttime = (int, 0)
	stopsignal = (str, signal.Signals.SIGSTOP)
	stoptime = (int, 0)
	stdout = (str, "/dev/null")
	stderr = (str, "/dev/null")
	env = (dict, {})


	def __init__(self, prog, name):
		if prog is None:
			raise ValueError(f'Invalid yaml format')

		self.name = name
		self.errors = []
		lst_attr = {k: v for k, v in ProgramConfig.__dict__.items() if not callable(v) and not k.startswith("__")}
		for key in lst_attr:
			value = prog.get(key, None)
			if not isinstance(value, lst_attr[key][0]):
				value = lst_attr[key][1]
				self.errors.append(f"{self.name}: Base value {value} is set for {key}")
			elif isinstance(value, int) and value < 0:
				self.errors.append(f"{self.name}: Value {value} for {key} can't be negative, default to 0")
				value = 0
			setattr(self, key, value)
		
		if not self.cmd:
			raise ValueError(f'{self.name}: minimal config requiere cmd to not be empty')
		
		os.makedirs(self.workingdir, exist_ok=True)
		self.stopsignal = get_signal(self.stopsignal)
		[self.env.update({k: str(v)}) for k, v in self.env.items()]
		self.autorestart = self.autorestart.lower()
		print(self)

	def __str__(self) -> str:
		return f"{self.name} conf:\n" + '\n'.join(f"\t{k} : {v}" for k, v in vars(self).items() if v not in [self.name, self.errors])

	def __eq__(self, other):
		if not isinstance(other, ProgramConfig):
			return False
		return vars(self) == vars(other)
	
	def __hash__(self):
		return hash(vars(self).values())
