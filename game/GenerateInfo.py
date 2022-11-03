from Monsters import *
from LevelGen import *

for o in spawn_options:
	ex = o[0]()
	print(ex.name)