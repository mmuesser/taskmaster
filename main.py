import readline
import asyncio
from utils import TabComplete
from logger import logger
from Taskmaster import Taskmaster

readline.parse_and_bind("tab: complete")
readline.set_completer(TabComplete.auto_complete)


if __name__ == "__main__":
	# with open("config.yml") as file:
		# config = [ProgramConfig(v, k) for k, v in yaml.load(file, Loader=yaml.FullLoader)["programs"].items()]
	
	tm = Taskmaster(Taskmaster.load_config())
	try:
		asyncio.run(tm.setup())
	except (EOFError, KeyboardInterrupt):
		# TODO CTRL+C
		tm.clean_up()