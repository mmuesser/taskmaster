import os, sys, time, subprocess, logging, yaml, readline, shlex, asyncio
from typing import List, Dict, Optional
from enum import Enum
import signal
from logger import Logger
import threading, queue

logger = Logger()

class State(Enum):
	INIT = "INITIALISATION"
	STARTING = "STARTING"
	RUNNING = "RUNNING"
	STOPPED = "STOPPED"
	FAILED = "FAILED"
	KILLED = "KILLED"
	SUCCESS = "SUCCESS"


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
		self.pid = None
		self.index = index
		self.config: ProgramConfig = config
		self.fds: FdManager = FdManager(self.config.stdout, self.config.stdout)
		self.state: State = State.STOPPED
		self.restart_count: int = 0
		self.killed: bool = False
		self.process_name = f"{self.config.name}_{self.index}"
	
	async def start(self):
		# print(shlex.split(self.config.cmd))
		# print(self.config)

		if not self.config.autostart:
			return

		logger.info(f"{self.process_name} INIT")

		self.state = State.INIT

		try:
			self.pid = await asyncio.create_subprocess_shell(
				cmd=self.config.cmd,
				stdout=self.fds.stdout,
				stderr=self.fds.stderr,
				umask=self.config.umask,
				env= dict(os.environ, **self.config.env),
				cwd=self.config.workingdir
			)
			self.state = State.STARTING
			logger.info(f"{self.process_name} STARTING")

		except OSError:
			self.state = State.FAILED
			logger.info(f"{self.process_name} FAILED (start)")
			return # ?

		print(self.pid)

		asyncio.create_task(self.monitor())

	async def monitor(self):
		if self.pid.returncode is None:
			try:
				await asyncio.wait_for(self.pid.wait(), self.config.starttime)
				if not self.pid.returncode in self.config.exitcodes:
					self.state = State.FAILED
					logger.info(f"{self.process_name} FAILED (monitor 1)")
			except asyncio.TimeoutError:
				self.state = State.RUNNING
				logger.info(f"{self.process_name} RUNNING")

		
		await self.pid.wait()
		if self.pid.returncode in self.config.exitcodes:
			self.state = State.SUCCESS
			logger.info(f"{self.process_name} SUCCESS (monitor)")
			return

		else:
			self.state = State.FAILED
			logger.info(f"{self.process_name} FAILED (monitor 2)")

		should_restart = False
		if self.config.autorestart in ("unexpected", "always"):
			should_restart = True

		if not should_restart or self.restart_count == self.config.startretries:
			return

		self.restart_count += 1

		logger.debug(f"{self.process_name} RESTART")

		
		#TODO REFACTO
		asyncio.create_task(self.start())


	async def stop(self):
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
		if self.pid.returncode is None:
			# TODO
			print(f"{self.config.name}_{self.index} is RUNNING")
			# self.state = State.RUNNING  # à changer
		else:
			print(f"{self.config.name}_{self.index} is {self.state.value}")


class Taskmaster:

	def __init__(self, configs: List[ProgramConfig]):
		self.configs: Dict[str, ProgramConfig] = {c.name:c for c in configs}
		self.instance: Dict[str, List[ProcessInstance]] = {} # à remplir
		self.running: bool = True
		TabComplete.key_words.extend(list(self.configs.keys()))
		TabComplete.key_words.extend(["start", "stop", "restart", "reload", "status"])
		# self.q = queue.Queue()
		# self.stop_event: any
		# print(TabComplete.key_words)

	# @classmethod
	# def read_input(cls, q):
		# while True:
			# line = input()
			# q.put(line)

	def stop_loop(self, *args):
		logger.warning("LOOP ABOUT TO END")
		self.running = False

	def set_sig(self):
		catchable_sigs = {
			signal.SIGTERM,
			signal.SIGINT
		}
		for sig in catchable_sigs:
			signal.signal(sig, self.stop_loop)
	
	

	async def setup(self):
		"lancer tout les process avec process.start()"
		"lancer la main loop avec run shell"
		"clean les process pour l'exit"

		for name, conf in self.configs.items():
			if conf.autostart:
				asyncio.create_task(self.start(name))
		
		await self.run_shell()
		pass

	def clean_up(self):
		"sig STOP or KILL pour tout les process."
		logger.info("CLEAN UP")
		pass

	async def status(self):
		"afficher le status des process (running, existed, etc.)"
		logger.info("General Status")
		for k, v in self.instance.items():
			for proc in v:
				proc.status()
		# if self.instance.Popen.poll() == None:
			# print("instance X is RUNNING")
			# return
		# print("instance X is ", self.instance.state)

	async def reload(self):
		"relancer le parsing du yml"
		logger.info("Reload du yml")
		pass

	async def start(self, prog):
		"démarrer si besoin le programme avec le bon nombre de process"
		logger.info(f"Start de {prog}")

		if not prog in self.configs:
			return
		
		# if self.state == State.RUNNING:
			# return

		proc_instance = []

		config: ProgramConfig = self.configs[prog]

		for i in range(config.numprocs):
			process = ProcessInstance(config, i)
			asyncio.create_task(process.start())
			proc_instance.append(process)

		self.instance[prog] = proc_instance

		pass

	async def stop(self, prog):
		"arrêter le programme s'il existe avec tout ses process"
		logger.info(f"Stop de {prog}")
		if not prog in self.configs:
			return
		
		print(self.instance)
		
		for process in self.instance[prog]:
			process.stop()

		pass

	async def restart(self, prog):
		"sûrment moyen de faire self.stop et self.start l'un après l'autre"
		logger.info(f"Restart de {prog}")
		self.stop(prog)
		self.start(prog)
		pass

	async def run_shell(self):
		print("<<Taskmaster shell>>")

		while self.running:
			logger.info("Before get")
			line = await asyncio.get_event_loop().run_in_executor(None, input)
			logger.info("After get")
			if not line:
				continue # entrée vide
			
			parts = line.split()
			if not parts:
				continue # sécu
			logger.info("Before case")
			match parts[0]:
				case "status":
					asyncio.create_task(self.status())
				case "reload":
					asyncio.create_task(self.reload())
				case "start":
					asyncio.create_task(self.start(parts[1]))
				case "stop":
					asyncio.create_task(self.stop(parts[1]))
				case "restart":
					asyncio.create_task(self.restart(parts[1]))
				case "exit":
					self.running = False
				case _:
					print("Commande inconnue")
			logger.info("After case")

if __name__ == "__main__":
	readline.parse_and_bind("tab: complete")
	readline.set_completer(TabComplete.auto_complete)

	with open("config.yml") as file:
		config = [ProgramConfig(v, k) for k, v in yaml.load(file, Loader=yaml.FullLoader)["programs"].items()]
	
	tm = Taskmaster(config)
	try:
		asyncio.run(tm.setup())
	except (EOFError):
		# TODO CTRL+C
		tm.clean_up()