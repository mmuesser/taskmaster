import os, sys, time, subprocess, logging, yaml, readline, shlex
from typing import List, Dict, Optional

class ProgramConfig:
	cmd = (str, None)
	numprocs = (int, 1)
	umask = (str, "000")
	workingdir = (str, "/tmp")
	autostart = (bool, True)
	autorestart = (str, None)
	exitcodes = (list, [])
	startretries = (int, 0)
	starttime = (int, 0)
	stopsignal = (str, "stop")
	stoptime = (int, 0)
	stdout = (str, '/dev/null')
	stderr = (str, '/dev/null')
	env = (dict, None)

	def __init__(self, prog, name):
		self.name = name
		lst_attr = {k: v for k, v in ProgramConfig.__dict__.items() if not callable(v) and not k.startswith("__")}
		for key in lst_attr:
			setattr(self, key, prog[key] if isinstance(prog.get(key, None), lst_attr[key][0]) else print(self.name, ": Base value", lst_attr[key][1], "is set for", key) and lst_attr[key][1])

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
		self.stdout = open(stdout, 'a') if stdout != '/dev/null' else stdout
		self.stderr = open(stderr, 'a') if stderr != '/dev/null' else stderr

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

	def __init__(self):
		self.pid
		self.config: ProgramConfig
		self.fds: FdManager = FdManager(self.config.stdout, self.config.stdout)
		pass
	
	def start(self):
		self.pid = subprocess.Popen(
			args=shlex.split(self.config),
			stdout=self.fds.stdout,
			stderr=self.fds.stderr,
			umask=self.config.umask,
			env=self.config.env,
			cwd=self.config.workingdir
		)
		pass


class Taskmaster:

	def __init__(self, configs: List[ProgramConfig]):
		self.configs: Dict[str, ProgramConfig] = {c.name:c for c in configs}
		self.instance: Dict[str, List[ProcessInstance]] = {} # à remplir
		self.running: bool = True
		TabComplete.key_words.extend(list(self.configs.keys()))
		TabComplete.key_words.extend(["start", "stop", "restart", "reload"])
		print(TabComplete.key_words)

	def setup(self):
		"lancer tout les process avec process.start()"
		"lancer la main loop avec run shell"
		"clean les process pour l'exit"
		self.run_shell()
		pass

	def clean_up(self):
		"sig STOP or KILL pour tout les process."
		pass

	def status(self):
		"afficher le status des process (running, existed, etc.)"
		print("status GENERAL")

	def reload(self):
		"relancer le parsing du yml"
		print("reload du yml")
		pass

	def start(self, parts):
		"démarrer si besoin le programme avec le bon nombre de process"
		print("start de", parts)
		pass

	def stop(self, parts):
		"arrêter le programme s'il existe avec tout ses process"
		print("stop de", parts)
		pass

	def restart(self, parts):
		"sûrment moyen de faire self.stop et self.start l'un après l'autre"
		print("restart de", parts)
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
					self.start(parts[1:])
				case "stop":
					self.stop(parts[1:])
				case "restart":
					self.restart(parts[1:])
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