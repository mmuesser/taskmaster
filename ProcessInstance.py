from ProgramConfig import ProgramConfig
from utils import FdManager
from logger import logger
from utils import State
import asyncio
import signal
import os


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

		self.state = State.INIT

		await self.launch()
		while await self.monitor() == False:
			logger.info("boucle start")
			await self.launch()


	async def launch(self):
		logger.info(f"{self.process_name} INIT restart count : {self.restart_count}")
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

		print(self.pid)

	async def monitor(self) -> bool:
		try:
			await asyncio.wait_for(self.pid.wait(), self.config.starttime)
			if not self.pid.returncode in self.config.exitcodes:
				self.state = State.FAILED
				logger.info(f"{self.process_name} FAILED (startup time) {self.pid.returncode}")
		except asyncio.TimeoutError:
			self.state = State.RUNNING
			logger.info(f"{self.process_name} RUNNING")

		
		await self.pid.wait()
		if self.pid.returncode in self.config.exitcodes:
			self.state = State.SUCCESS
			logger.info(f"{self.process_name} SUCCESS (code: {self.pid.returncode})")
			return True

		else:
			if self.state != State.FAILED:
				self.state = State.FAILED
				logger.info(f"{self.process_name} FAILED (unexpected exit code) {self.pid.returncode}")

		should_restart = False
		if self.config.autorestart == "always" or (self.config.autorestart == "unexpected" and not self.pid.returncode in self.config.exitcodes):
			should_restart = True

		self.restart_count += 1

		if not should_restart or self.restart_count > self.config.startretries:
			return True


		logger.debug(f"{self.process_name} RESTART")
		return False


	async def stop(self):
		if self.state != State.RUNNING:
			return
		# 
		# self.pid.terminate()
		# self.state = State.STOPPED
		# try:
			# self.pid.wait(timeout=self.config.stoptime)
		# except subprocess.TimeoutExpired:
			# self.pid.kill()
			# self.state = State.KILLED

		self.pid.send_signal(self.config.stopsignal)
		try:
			await asyncio.wait_for(self.pid.wait(), timeout=self.config.stoptime)
			self.state = State.STOPPED
			logger.info(f"{self.process_name} stopped")
		except asyncio.TimeoutError:
			logger.warning(f"{self.process_name} stop time exceeded, send kill")
			self.pid.send_signal(signal.SIGTERM)
			await asyncio.wait()
			self.state = State.KILLED

	def status(self):
		if self.pid.returncode is None:
			# TODO
			print(f"{self.config.name}_{self.index} is RUNNING")
			# self.state = State.RUNNING  # à changer
		else:
			print(f"{self.config.name}_{self.index} is {self.state.value}")

