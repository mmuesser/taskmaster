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
# tmp = Data(conf["nginx"], "test")
# prog.append(tmp)
    # print(tmp.cmd)
print(tmp.name)


# prog[0] == prog[1]
print(prog[0] == prog[1])
# print(len(list(prog[0].dict.keys())))



# print(data.umask)