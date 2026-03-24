from ProgramConfig import ProgramConfig
from ProcessInstance import ProcessInstance
from utils import TabComplete, State
from logger import logger
import asyncio, yaml, signal
from typing import Dict, List, Set

class Taskmaster:

	config_file = "config.yml"

	def __init__(self, configs: List[ProgramConfig]):
		self.configs: Dict[str, ProgramConfig] = {c.name:c for c in configs}
		self.instances: Dict[str, List[ProcessInstance]] = {} # à remplir
		self.running: bool = True
		self.known_cmd = ["start", "stop", "restart", "reload", "status", "exit"]
		TabComplete.key_words.extend(list(self.configs.keys()))
		TabComplete.key_words.extend(self.known_cmd)
		self.cmd = {
			"status": self.status,
			"reload": self.reload,
			"start": self.start,
			"restart": self.restart,
			"stop": self.stop,
			"unknown": self.unknown,
		}

	async def setup(self):
		"lancer tout les process avec process.start()"
		"lancer la main loop avec run shell"
		"clean les process pour l'exit"

		for name, conf in self.configs.items():
			if conf.autostart:
				asyncio.create_task(self.start(name))
		
		await self.run_shell()
		await self.clean_up()
		pass

	@classmethod
	def load_config(self) -> List[ProgramConfig]:
		with open(self.config_file, 'r', encoding='utf-8') as file:
			config = [ProgramConfig(v, k) for k, v in yaml.load(file, Loader=yaml.FullLoader).get("programs", {}).items()]
		return config

	async def clean_up(self):
		for name in self.instances:
			await self.stop(name)
		

	async def status(self, _):
		"afficher le status des process (running, existed, etc.)"
		logger.info("General Status")
		if not self.instances:
			logger.info("Nothing has been launched yet")
			return
		
		for _, v in self.instances.items():
			for proc in v:
				proc.status()

	async def reload(self, _):
		"relancer le parsing du yml"
		new_config: List[ProgramConfig] = Taskmaster.load_config()
		if not (set(self.configs.values()) - set(new_config)):
			logger.info("Nothing to reload")
			return

		to_stop: Set[ProgramConfig] = set(self.configs.values()) - set(new_config)

		logger.debug(f"to stop {to_stop}")

		for conf in to_stop:
			name = conf.name
			await self.stop(name)
			del self.configs[name]

		to_start: Set[ProgramConfig] = set(new_config) - set(self.configs.values())

		logger.debug(f"to start / restart {to_start}")

		for conf in to_start:
			name = conf.name
			self.configs[name] = conf

			if name in self.configs:
				await self.stop(name)
			
			if conf.autostart:
				asyncio.create_task(self.start(name))

	async def start(self, prog):
		"démarrer si besoin le programme avec le bon nombre de process"
		logger.info(f"Start de {prog}")

		if not prog in self.configs:
			return
		
		proc_instance = []

		config: ProgramConfig = self.configs[prog]

		logger.debug(f"lancement de {config.numprocs} process")

		for i in range(config.numprocs):
			process = ProcessInstance(config, i)
			asyncio.create_task(process.start())
			proc_instance.append(process)

		self.instances[prog] = proc_instance

	async def stop(self, prog):
		"arrêter le programme s'il existe avec tout ses process"
		logger.info(f"Stop de {prog}")
		if not prog in self.configs or not prog in self.instances:
			return
		
		print(self.instances)
		
		for process in self.instances[prog]:
			await process.stop()

	async def restart(self, prog):
		logger.info(f"Restart de {prog}")
		await self.stop(prog)
		asyncio.create_task(self.start(prog))
	
	async def unknown(self, cmd):
		logger.info(f'"{cmd}" command not found')

	def parsing(self, line) -> tuple[str, str]:
		parts = line.split()
		cmd = parts[0]
		
		if cmd not in self.known_cmd:
			return 'unknown', line
		
		match len(parts):
			case 1:
				prg = ""
			case 2:
				prg = parts[1]
			case _:
				logger.warning("Trop d'arguments")
				return 'skip', None
		
		return cmd, prg

	async def run_shell(self):
		print("<<Taskmaster shell>>")

		while self.running:
			line = await asyncio.get_event_loop().run_in_executor(None, input)
			if not line:
				continue # entrée vide
			
			cmd, prg = self.parsing(line)
			if cmd == "exit":
				break
			if cmd == "skip":
				continue
			
			asyncio.create_task(self.cmd[cmd](prg))
		return