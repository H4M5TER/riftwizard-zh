import re
from extracted import *

# 从loc.py手动复制粘贴进去
f = open("old.txt", "r", encoding="utf-8")
old = f.readlines()
f.close()

map = {}
for line in old:
    match = re.search("\"(.+)\":", line) 
    map[match.groups()[0]] = line

new = []
for x in tags: # monsters skills
    new.append(map[x])

f = open("new.txt", "w", encoding="utf-8")
f.write(''.join(new))
f.close()
