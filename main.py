import readline
import asyncio
from utils import TabComplete
from logger import logger
from Taskmaster import Taskmaster

readline.parse_and_bind("tab: complete")
readline.set_completer(TabComplete.auto_complete)


if __name__ == "__main__":
	tm = Taskmaster(Taskmaster.load_config())
	try:
		asyncio.run(tm.setup())
	except KeyboardInterrupt:
		print('Press Enter to exit')
		# asyncio.run(tm.clean_up())
		pass