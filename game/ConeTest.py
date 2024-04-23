from Level import *
import math


#13, 17 to 14, 15 
level = Level(28, 28)

origin = Point(13, 17)
target = Point(14, 15)

level.make_wall(14, 16)
level.make_wall(14, 17)

burst = Burst(level, 
					 origin ,
				     7, 
				     burst_cone_params=BurstConeParams(target, math.pi / 8.0))

for stage in burst:
	for point in stage:
		print(point)

burst = Burst(level, 
					 origin,
				     7, 
				     burst_cone_params=BurstConeParams(target, math.pi / 8.0))

points = [p for stage in burst for p in stage]

print('break')

for p in points:
	print(p)

