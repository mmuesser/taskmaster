from ProgramConfig import ProgramConfig
from ProcessInstance import ProcessInstance
from utils import TabComplete, State
from logger import logger
import asyncio, yaml, signal, sys, os
from typing import Dict, List, Set
import readline

class Taskmaster:

	config_file = "config.yml"

	def __init__(self, configs: List[ProgramConfig]):
		self.configs: Dict[str, ProgramConfig] = {c.name:c for c in configs}
		self.instances: Dict[str, List[ProcessInstance]] = {}
		self.running: bool = True
		self._reload_event = asyncio.Event()
		self.cmd = {
			"status": self.status,
			"reload": self.reload,
			"start": self.start,
			"restart": self.restart,
			"stop": self.stop,
			"list": self.list,
			"unknown": self.unknown,
		}
		TabComplete.key_words.update(list(self.configs.keys()))
		TabComplete.key_words.update(list(self.cmd.keys()) + ["exit"])

	async def setup(self):
		for name, conf in self.configs.items():
			if conf.autostart:
				asyncio.create_task(self.start(name))
		try:
			await self.run_shell()
		except (asyncio.exceptions.CancelledError):
			print('Press Enter to exit')

		await self.clean_up()

	@classmethod
	def load_config(self) -> List[ProgramConfig]:
		config = []
		with open(self.config_file, 'r', encoding='utf-8') as file:
			for k, v in yaml.load(file, Loader=yaml.FullLoader).get("programs", {}).items():
				try:
					conf = ProgramConfig(v, k)
					[logger.info(err) for err in conf.errors]
					config.append(conf)
				except ValueError as e:
					logger.warning(e)
				
		return config

	async def clean_up(self):
		tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
	
		for task in tasks:
			task.cancel()
	
		await asyncio.gather(*tasks, return_exceptions=True)


	async def status(self, _):
		logger.info("General Status")
		if not self.instances:
			logger.info("Nothing has been launched yet")
			return
		
		for _, v in self.instances.items():
			for proc in v:
				proc.status()

	async def list(self, _):
		logger.info("Programs loaded")

		for _, conf in self.configs.items():
			logger.info(conf)

	async def reload(self, _):
		try:
			new_config: List[ProgramConfig] = Taskmaster.load_config()
		except yaml.YAMLError:
			logger.warning("Invalid config file, config cannot be reloaded")
			return
		if not (set(self.configs.values()) - set(new_config)):
			logger.info("Nothing to reload")
			return

		to_stop: Set[ProgramConfig] = set(self.configs.values()) - set(new_config)

		# logger.debug(f"to stop {to_stop}")

		for conf in to_stop:
			name = conf.name
			await self.stop(name)
			self.configs.pop(name, None)
			self.instances.pop(name, None)
			TabComplete.key_words.discard(name)

		to_start: Set[ProgramConfig] = set(new_config) - set(self.configs.values())

		# logger.debug(f"to start / restart {to_start}")

		for conf in to_start:
			name = conf.name
			self.configs[name] = conf

			if name in self.configs:
				await self.stop(name)
			
			if conf.autostart:
				asyncio.create_task(self.start(name))

	async def start(self, prog):
		if prog not in self.configs:
			return
		logger.info(f"Start {prog}")

		if not prog in self.configs:
			return
		
		proc_instance = []

		config: ProgramConfig = self.configs[prog]

		for i in range(config.numprocs):
			process = ProcessInstance(config, i)
			asyncio.create_task(process.start())
			proc_instance.append(process)
		if config.numprocs:
			logger.info(f'{config.numprocs} process as been started')

		self.instances[prog] = proc_instance

	async def stop(self, prog):
		if prog not in self.configs:
			return
		logger.info(f"Stop {prog}")
		if not prog in self.configs or not prog in self.instances:
			return
		
		for process in self.instances[prog]:
			asyncio.create_task(process.stop())

		# self.instances[prog] = []
		# del self.instances[prog]

	async def restart(self, prog):
		if prog not in self.configs:
			return
		logger.info(f"Restart {prog}")
		await self.stop(prog)
		asyncio.create_task(self.start(prog))
	
	async def unknown(self, cmd):
		logger.info(f'"{cmd}" command not found')

	def parsing(self, line) -> tuple[str, str]:
		parts = line.split()
		cmd = parts[0]
		
		if cmd not in self.cmd.keys():
			return 'unknown', line
		
		match len(parts):
			case 1:
				prg = ""
			case 2:
				prg = parts[1]
			case _:
				logger.warning("Command too long")
				return 'skip', None
		
		return cmd, prg

	async def run_shell(self):
		print("<<Taskmaster shell>>")

		while self.running:
			try:
				line = await asyncio.get_event_loop().run_in_executor(None, input)
				if not line:
					continue # entrée vide
				line = line.strip()
				cmd, prg = self.parsing(line)
				if cmd == "exit":
					break
				if cmd == "skip":
					continue

				asyncio.create_task(self.cmd[cmd](prg))
			except EOFError:
				break
		return