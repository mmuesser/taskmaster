import os, sys, time, subprocess, logging, yaml, readline, shlex
from typing import List, Dict, Optional
from enum import Enum

class State(Enum):
	INIT = "INITIALISATION"
	STARTING = "STARTING"
	RUNNING = "RUNNING"
	STOPPED = "STOPPED"
	FAILED = "FAILED"
	KILLED = "KILLED"
	SUCCESS = "SUCCESS"


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
	stopsignal = (str, "stop")
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
				print(self.name, ": Base value", value, "is set for", key)
			setattr(self, key, value)
		print(self)

	def __str__(self) -> str:
		return str(vars(self))

	def __eq__(self, other):
		if not isinstance(other, ProgramConfig):
			return False
		return vars(self) == vars(other)
	
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

class ProcessInstance:
	"Identity : PID PPID"
	"State : State  CPU TIME"
	"Files : FD"
	"ENV : ENVP CWD ROOT DIR"
	"SIGNALS : "
	"PATH"
	"ARG"

	"HERITE DE :"
	"FD - ENVP - CWD - UID/GID"

	def __init__(self, config: ProgramConfig, index: int):
		self.pid: int = 0
		self.index = index
		self.config: ProgramConfig = config
		self.fds: FdManager = FdManager(self.config.stdout, self.config.stdout)
		self.state: State = State.STOPPED
	
	def start(self):
		print(shlex.split(self.config.cmd))
		print(self.config)
		# env = os.environ
		# env.update(self.config.env)
		# print(env)
		if not self.config.env:
			self.config.env = {}

		self.state = State.INIT

		try:
			self.pid = subprocess.Popen(
				args=shlex.split(self.config.cmd),
				stdout=self.fds.stdout,
				stderr=self.fds.stderr,
				umask=self.config.umask,
				env= dict(os.environ, **self.config.env),
				cwd=self.config.workingdir
			)
			self.state = State.STARTING
		except OSError:
			self.state = State.FAILED
			return # ?

		print(self.pid)

	def stop(self):
		if self.state != State.RUNNING:
			return
		
		self.pid.terminate()
		self.state = State.STOPPED
		try:
			self.pid.wait(timeout=self.config.stoptime)
		except subprocess.TimeoutExpired:
			self.pid.kill()
			self.state = State.KILLED

	def status(self):
		if self.pid.poll() == None:
			# TODO
			print(f"{self.config.name}_{self.index} is RUNNING")
			self.state = State.RUNNING  # à changer
		else:
			print(f"{self.config.name}_{self.index} is {self.state.value}")


class Taskmaster:

	def __init__(self, configs: List[ProgramConfig]):
		self.configs: Dict[str, ProgramConfig] = {c.name:c for c in configs}
		self.instance: Dict[str, List[ProcessInstance]] = {} # à remplir
		self.running: bool = True
		TabComplete.key_words.extend(list(self.configs.keys()))
		TabComplete.key_words.extend(["start", "stop", "restart", "reload"])
		# print(TabComplete.key_words)

	def setup(self):
		"lancer tout les process avec process.start()"
		"lancer la main loop avec run shell"
		"clean les process pour l'exit"
		
		for name, conf in self.configs.items():
			if conf.autostart:
				self.start(name)
		
		self.run_shell()
		pass

	def clean_up(self):
		"sig STOP or KILL pour tout les process."
		pass

	def status(self):
		"afficher le status des process (running, existed, etc.)"
		print("status GENERAL")
		for k, v in self.instance.items():
			for proc in v:
				proc.status()
		# if self.instance.Popen.poll() == None:
			# print("instance X is RUNNING")
			# return
		# print("instance X is ", self.instance.state)

	def reload(self):
		"relancer le parsing du yml"
		print("reload du yml")
		pass

	def start(self, prog):
		"démarrer si besoin le programme avec le bon nombre de process"
		print("start de", prog)

		if not prog in self.configs:
			return
		
		# if self.state == State.RUNNING:
			# return

		proc_instance = []

		config: ProgramConfig = self.configs[prog]

		for i in range(config.numprocs):
			process = ProcessInstance(config, i)
			process.start()
			proc_instance.append(process)

		self.instance[prog] = proc_instance

		pass

	def stop(self, prog):
		"arrêter le programme s'il existe avec tout ses process"
		print("stop de", prog)
		if not prog in self.configs:
			return
		
		print(self.instance)
		
		for process in self.instance[prog]:
			process.stop()

		pass

	def restart(self, prog):
		"sûrment moyen de faire self.stop et self.start l'un après l'autre"
		print("restart de", prog)
		self.stop(prog)
		self.start(prog)
		pass

	def run_shell(self):
		print("<<Taskmaster shell>>")

		while self.running:
			line = input()
			if not line:
				continue # entrée vide

			parts = line.split()
			if not parts:
				continue # sécu

			match parts[0]:
				case "status":
					self.status()
				case "reload":
					self.reload()
				case "start":
					self.start(parts[1])
				case "stop":
					self.stop(parts[1])
				case "restart":
					self.restart(parts[1])
				case "exit":
					self.running = False
				case _:
					print("Commande inconnue")

if __name__ == "__main__":
	readline.parse_and_bind("tab: complete")
	readline.set_completer(TabComplete.auto_complete)

	with open("config.yml") as file:
		config = [ProgramConfig(v, k) for k, v in yaml.load(file, Loader=yaml.FullLoader)["programs"].items()]
	
	# config = [
		# ProgramConfig("nginx"), ProgramConfig("vogsphere")
	# ]

	# with open("config.yml") as file:
	# 	config = yaml.load(file, Loader=yaml.FullLoader)
	# 	config = list(config.values())[0]

	# prog = []

	# for key in config:
	# 	tmp = ProgramConfig(config[key], key)
	# 	prog.append(tmp)

	tm = Taskmaster(config)
	try:
		tm.setup()
	except (EOFError, KeyboardInterrupt):
		tm.clean_up()