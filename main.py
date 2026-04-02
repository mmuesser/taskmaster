import readline
import asyncio
from sys import exit
import yaml
from utils import TabComplete
from logger import logger
from Taskmaster import Taskmaster

readline.parse_and_bind("tab: complete")
readline.set_completer(TabComplete.auto_complete)


if __name__ == "__main__":
	try:
		tm = Taskmaster(Taskmaster.load_config())
		asyncio.run(tm.setup())
	
	except (yaml.YAMLError):
		logger.warning("Cannot load config file, ending")
		exit()
	
	except (EOFError, KeyboardInterrupt):
		# TODO CTRL+C
		tm.clean_up()