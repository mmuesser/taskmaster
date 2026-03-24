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
		self.instance: Dict[str, List[ProcessInstance]] = {} # à remplir
		self.running: bool = True
		TabComplete.key_words.extend(list(self.configs.keys()))
		TabComplete.key_words.extend(["start", "stop", "restart", "reload", "status", "exit"])
		self.cmd = {"status": self.status, "reload": self.reload, "start": self.start, "restart": self.restart, "stop": self.stop}

	async def setup(self):
		"lancer tout les process avec process.start()"
		"lancer la main loop avec run shell"
		"clean les process pour l'exit"

		for name, conf in self.configs.items():
			if conf.autostart:
				asyncio.create_task(self.start(name))
		
		await self.run_shell()
		pass

	@classmethod
	def load_config(self) -> List[ProgramConfig]:
		with open(self.config_file, 'r', encoding='utf-8') as file:
			config = [ProgramConfig(v, k) for k, v in yaml.load(file, Loader=yaml.FullLoader).get("programs", {}).items()]
		return config

	def clean_up(self):
		"sig STOP or KILL pour tout les process."
		logger.info("CLEAN UP")
		pass

	async def status(self, _):
		"afficher le status des process (running, existed, etc.)"
		logger.info("General Status")
		if not self.instance:
			logger.info("Nothing has been launched yet")
			return
		
		for k, v in self.instance.items():
			for proc in v:
				proc.status()

	async def reload(self, _):
		"relancer le parsing du yml"
		new_config: List[ProgramConfig] = Taskmaster.load_config()
		# to_reload: Set[ProgramConfig] = set(self.configs.values()) & set(new_config)

		# logger.debug(f"to reload {to_reload}")

		# for conf in to_reload:
			# name = conf.name
			# self.configs[name] = conf
			# 
			# await self.stop(name)
			# asyncio.create_task(self.start(name))

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

		pass

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

		self.instance[prog] = proc_instance

		pass

	async def stop(self, prog):
		"arrêter le programme s'il existe avec tout ses process"
		logger.info(f"Stop de {prog}")
		if not prog in self.configs or not prog in self.instance:
			return
		
		print(self.instance)
		
		for process in self.instance[prog]:
			await process.stop()

		pass

	async def restart(self, prog):
		"sûrment moyen de faire self.stop et self.start l'un après l'autre"
		logger.info(f"Restart de {prog}")
		self.stop(prog)
		self.start(prog)
		pass
	
	def parsing(self, line) -> tuple[str, str]:
		parts = line.split()
		cmd = parts[0]
		match len(parts):
			case 1:
				prg = ""
			case 2:
				prg = parts[1]
			case _:
				logger.warning("Trop d'arguments")
		
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
			asyncio.create_task(self.cmd[cmd](prg))
		return