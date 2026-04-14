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
		self.state: State = State.INIT
		self.restart_count: int = 0
		self.stopped: bool = False
		self.force_kill: bool = False
		self.process_name = f"{self.config.name}_{self.index}"

	def set_umask(self):
		os.umask(int(str(self.config.umask), 8))
	
	async def start(self):

		self.state = State.INIT

		try:
			await self.launch()
			while await self.monitor() == False:
				if self.force_kill:
					break
				await self.launch()
		except asyncio.CancelledError:
			await self.stop()

	async def launch(self):
		if self.config.autorestart != "always":
			logger.info(f"{self.process_name} INIT restart count : {self.restart_count}")
		self.stopped = False
		try:
			self.fds.open()
			self.pid = await asyncio.create_subprocess_shell(
				cmd=f"umask {str(oct(self.config.umask))[2:].zfill(3)} && {self.config.cmd}",
				stdout=self.fds.stdout_fd,
				stderr=self.fds.stderr_fd,
				env= dict(os.environ, **self.config.env),
				cwd=self.config.workingdir,
			)
			self.state = State.STARTING
			logger.info(f"{self.process_name} STARTING")

		except OSError:
			self.state = State.FAILED
			logger.info(f"{self.process_name} FAILED (start)")

	def set_state(self):
		if self.stopped:
			return
		
		if self.pid.returncode in self.config.exitcodes and self.state != State.FAILED:
			self.state = State.SUCCESS
			logger.info(f"{self.process_name} SUCCESS (code: {self.pid.returncode})")

		else:
			if self.state != State.FAILED:
				self.state = State.FAILED
				logger.info(f"{self.process_name} FAILED (unexpected exit code) {self.pid.returncode}")


	def _always_restart(self):
		self.set_state()
		logger.debug(f"{self.process_name} RESTART")
		return False
	
	def _unexpected_restart(self):
		self.set_state()
		if self.pid.returncode not in self.config.exitcodes:
			self.restart_count += 1
			if self.restart_count > self.config.startretries:
				return True
			logger.debug(f"{self.process_name} RESTART")
			return False
		return True
	
	def _never(self):
		self.set_state()
		logger.debug(f"{self.process_name} NO NEED TO RESTART")
		return True


	async def monitor(self) -> bool:
		try:
			await asyncio.wait_for(self.pid.wait(), timeout=self.config.starttime)
			self.state = State.FAILED
			logger.info(f"{self.process_name} FAILED (startup time) {self.pid.returncode}")
		except asyncio.TimeoutError:
			self.state = State.RUNNING
			logger.info(f"{self.process_name} RUNNING")

		await self.pid.wait()
		if self.force_kill:
			return True
		
		match (self.config.autorestart):
			case 'always':
				return self._always_restart()
			case 'unexpected':
				return self._unexpected_restart()
			case _:
				return self._never()

	def kill(self):
		if self.pid.returncode is not None:
			self.pid.terminate()
		self.state = State.KILLED
		logger.info(f"{self.process_name} killed ({self.pid.returncode})")

	async def stop(self):
		if not self.state in (State.RUNNING, State.STARTING):
			return

		self.pid.send_signal(self.config.stopsignal)
		self.stopped = True
		try:
			logger.info(f"signal {self.config.stopsignal} sent to {self.process_name}")
			await asyncio.wait_for(self.pid.wait(), timeout=self.config.stoptime)
			self.state = State.STOPPED
			logger.info(f"{self.process_name} stopped (code: {self.pid.returncode})")
		except asyncio.TimeoutError:
			logger.warning(f"{self.process_name} stop time exceeded, send kill")
			self.kill()
		self.fds.close()

	def status(self):
		logger.info(f"{self.config.name}_{self.index} is {self.state.value}")

