from ProgramConfig import ProgramConfig
from ProcessInstance import ProcessInstance
from utils import TabComplete, State
from main import logger
import asyncio
from typing import Dict, List

class Taskmaster:

	def __init__(self, configs: List[ProgramConfig]):
		self.configs: Dict[str, ProgramConfig] = {c.name:c for c in configs}
		self.instance: Dict[str, List[ProcessInstance]] = {} # à remplir
		self.running: bool = True
		TabComplete.key_words.extend(list(self.configs.keys()))
		TabComplete.key_words.extend(["start", "stop", "restart", "reload", "status"])

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

	async def reload(self):
		"relancer le parsing du yml"
		logger.info("Reload du yml")
		pass

	async def start(self, prog):
		"démarrer si besoin le programme avec le bon nombre de process"
		logger.info(f"Start de {prog}")

		if not prog in self.configs:
			return
		
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