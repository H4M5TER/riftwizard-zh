from LevelGen import *

for i in range(1, 6):
	print(i)
	ops = get_spawn_options(difficulty=i+1, num_spawns=999)
	for op in ops:
		print(op[0]().name)
	print(' ')

for i in range(1, 25):
	print(get_spawn_min_max(i))