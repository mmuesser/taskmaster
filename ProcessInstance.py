from ProgramConfig import ProgramConfig
from utils import FdManager
from logger import Logger
from utils import State
import asyncio
import subprocess # TODO
import os

logger = Logger()

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

