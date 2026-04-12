from ProgramConfig import ProgramConfig
from utils import FdManager
from logger import logger
from utils import State
import asyncio
import signal
import os


class ProcessInstance:
	def __init__(self, config: ProgramConfig, index: int):
		self.pid = None
		self.index = index
		self.config: ProgramConfig = config
		self.fds: FdManager = FdManager(self.config.stdout, self.config.stdout)
		self.state: State = State.STOPPED
		self.restart_count: int = 0
		self.killed: bool = False
		self.process_name = f"{self.config.name}_{self.index}"

	def set_umask(self):
		os.umask(int(str(self.config.umask), 8))
	
	async def start(self):

		self.state = State.INIT

		try:
			await self.launch()
			while await self.monitor() == False:
				await self.launch()
		except asyncio.CancelledError:
			await self.stop()

	async def launch(self):
		logger.info(f"{self.process_name} INIT restart count : {self.restart_count}")
		try:
			self.pid = await asyncio.create_subprocess_shell(
				cmd=f"umask {str(oct(self.config.umask))[2:].zfill(3)} && {self.config.cmd}",
				stdout=self.fds.stdout,
				stderr=self.fds.stderr,
				env= dict(os.environ, **self.config.env),
				cwd=self.config.workingdir,
				# preexec_fn=self.set_umask
			)
			self.state = State.STARTING
			logger.info(f"{self.process_name} STARTING")

		except OSError:
			self.state = State.FAILED
			logger.info(f"{self.process_name} FAILED (start)")

	async def monitor(self) -> bool:
		try:
			await asyncio.wait_for(self.pid.wait(), timeout=self.config.starttime)
			# if not self.pid.returncode in self.config.exitcodes:
			self.state = State.FAILED
			logger.info(f"{self.process_name} FAILED (startup time) {self.pid.returncode}")
		except asyncio.TimeoutError:
			self.state = State.RUNNING
			logger.info(f"{self.process_name} RUNNING")

		
		await self.pid.wait()
		# if self.killed:
		# 	return
		if self.pid.returncode in self.config.exitcodes and self.state != State.FAILED:
			self.state = State.SUCCESS
			logger.info(f"{self.process_name} SUCCESS (code: {self.pid.returncode})")
			# return True

		else:
			if self.state != State.FAILED:
				self.state = State.FAILED
				logger.info(f"{self.process_name} FAILED (unexpected exit code) {self.pid.returncode}")

		should_restart = False
		if self.config.autorestart == "always" or (self.config.autorestart == "unexpected" and not self.pid.returncode in self.config.exitcodes):
			should_restart = True

		self.restart_count += 1

		if not should_restart or (self.restart_count > self.config.startretries and self.config.autorestart == "unexpected"):
			print("test")
			return True


		logger.debug(f"{self.process_name} RESTART")
		return False


	async def stop(self):
		if not self.state in (State.RUNNING, State.STARTING):
			return

		self.pid.send_signal(self.config.stopsignal)
		self.killed = True #useless si on garde pas la condition dans monitor
		try:
			logger.info(f"signal {self.config.stopsignal} sent to {self.process_name} : {self}")
			await asyncio.wait_for(self.pid.wait(), timeout=self.config.stoptime)
			self.state = State.STOPPED
			logger.info(f"{self.process_name} stopped")
		except asyncio.TimeoutError:
			logger.warning(f"{self.process_name} stop time exceeded, send kill")
			# await asyncio.wait(self.pid)
			self.pid.kill()
			self.state = State.KILLED
			logger.info(f"{self.process_name} : {self} killed")
		self.fds.close()

	def status(self):
		logger.info(f"{self.config.name}_{self.index} is {self.state.value}")

