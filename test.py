#!/usr/bin/env python3
from ProgramConfig import ProgramConfig
import yaml

with open("config.yml") as file:
    conf = yaml.load(file, Loader=yaml.FullLoader)
    conf = list(conf.values())[0]

prog = []

for key in conf:
    tmp = ProgramConfig(conf[key], key)
    prog.append(tmp)

print(tmp.name)


print(prog[0] == prog[1])



