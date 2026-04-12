import readline
import asyncio
import yaml, signal
import string
from utils import TabComplete
from logger import logger
from Taskmaster import Taskmaster

readline.parse_and_bind("tab: complete")
readline.set_completer(TabComplete.auto_complete)

def on_sighup(task: Taskmaster):
	asyncio.create_task(task.reload(None))
	logger.warning("Signal catch")


async def main():
	try:
		tm = Taskmaster(Taskmaster.load_config())
		loop = asyncio.get_running_loop()
		loop.add_signal_handler(signal.SIGHUP, on_sighup, tm)
		# for conf in tm.configs.values():
		# 	print(f" {conf.name} signal : {conf.stopsignal}")
		# 	print(f"{type(conf.stopsignal)}")
		# 	loop.add_signal_handler(signal.Signals(conf.stopsignal), tm.stop, conf.name)
		await tm.setup()

	except (yaml.YAMLError):
		logger.warning("Cannot load config file, ending")

	except (EOFError, KeyboardInterrupt):
		await tm.clean_up()


if __name__ == "__main__":
	asyncio.run(main())