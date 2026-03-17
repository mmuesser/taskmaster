import os, sys, time, subprocess, logging
from typing import List, Dict, Optional

class ProgramConfig:
	cmd = (str, None)
	numprocs = (int, 1)
	umask = (str, "000")
	workingdir = (str, "/tmp")
	autostart = (bool, True)
	autorestart = (str, None)
	exitcodes = (list, [])
	startretries = (int, 0)
	starttime = (int, 0)
	stopsignal = (str, "stop")
	stoptime = (int, 0)
	stdout = (str, None)
	stderr = (str, None)
	env = (dict, None)

	def __init__(self, prog, name):
		self.name = name
		lst_attr = {k: v for k, v in ProgramConfig.__dict__.items() if not callable(v) and not k.startswith("__")}
		for key in lst_attr:
			setattr(self, key, prog[key] if isinstance(prog.get(key, None), lst_attr[key][0]) else print(self.name, ": Base value", lst_attr[key][1], "is set for", key) and lst_attr[key][1])

	def __str__(self) -> str:
		return str(vars(self))

	def __eq__(self, other):
		if not isinstance(other, ProgramConfig):
			return False
		return vars(self) == vars(other)

class ProcessInstance:
    
    pass

class Taskmaster:

    def __init__(self, configs: List[ProgramConfig]):
        self.configs: Dict[str, ProgramConfig] = {c.name:c for c in configs}
        self.instance: Dict[str, List[ProcessInstance]] = {} # à remplir
        self.running: bool = True

    def setup(self):
        "lancer tout les process avec process.start()"
        "lancer la main loop avec run shell"
        "clean les process pour l'exit"
        self.run_shell()
        pass

    def clean_up(self):
        "sig STOP or KILL pour tout les process."
        pass

    def status(self):
        "afficher le status des process (running, existed, etc.)"
        print("status GENERAL")

    def reload(self):
        "relancer le parsing du yml"
        print("reload du yml")
        pass

    def start(self, parts):
        "démarrer si besoin le programme avec le bon nombre de process"
        print("start de", parts)
        pass

    def stop(self, parts):
        "arrêter le programme s'il existe avec tout ses process"
        print("stop de", parts)
        pass

    def restart(self, parts):
        "sûrment moyen de faire self.stop et self.start l'un après l'autre"
        print("restart de", parts)
        pass

    def run_shell(self):
        print("<<Taskmaster shell>>")

        while self.running:
            line = input()
            if not line:
                break # entrée vide

            parts = line.split()
            if not parts:
                continue # sécu

            match parts[0]:
                case "status":
                    self.status()
                case "reload":
                    self.reload()
                case "start":
                    self.start(parts[1:])
                case "stop":
                    self.stop(parts[1:])
                case "restart":
                    self.restart(parts[1:])
                case "exit":
                    self.running = False
                case _:
                    print("Commande inconnue")

if __name__ == "__main__":
    config = [
        ProgramConfig("nginx"), ProgramConfig("vogsphere")
    ]

    tm = Taskmaster(config)
    try:
        tm.setup()
    except (EOFError, KeyboardInterrupt):
        tm.clean_up()