# Various methods for randomly modifying level tile
from Level import *

import logging
level_logger = logging.getLogger("Level")
level_logger.setLevel(logging.DEBUG)
level_logger.propagate = False

def expand_floor(levelgen):

	level = levelgen.level

	floor_tiles = [t for t in level.iter_tiles() if t.can_walk]
	blocked_tiles = [t for t in level.iter_tiles() if not t.can_walk]

	invert = len(floor_tiles) > len(blocked_tiles) 

	chasm = False
	if invert:
		chasm = levelgen.random.choice([True, False])


	chance = levelgen.random.choice([.05, .1, .3, .5])

	level_logger.debug("Floor Exp: %.1f" % chance)

	tiles = blocked_tiles if invert else floor_tiles
	for t in tiles:
		for p in level.get_points_in_ball(t.x, t.y, 1, diag=True):
			if levelgen.random.random() < chance:
				if invert:
					level.make_wall(p.x, p.y)
				else:
					if chasm:
						level.make_chasm(p.x, p.y)
					else:
						level.make_floor(p.x, p.y)

# Randomly convert some number of walls to chasms
def walls_to_chasms(levelgen):
	level = levelgen.level
	num_chasms = levelgen.random.choice([1, 1, 1, 2, 3, 4, 6, 7, 10, 15, 40, 40, 40, 40])
	level_logger.debug("Wallchasms: %d" % num_chasms)

	for i in range(num_chasms):
		choices = [t for t in level.iter_tiles() if not t.can_see]
		if not choices:
			break

		start_point = levelgen.random.choice(choices)
		choices = [start_point]
		for i in range(levelgen.random.randint(10, 100)):

			if not choices:
				break

			current = levelgen.random.choice(choices)
			choices.remove(current)

			level.make_chasm(current.x, current.y)

			for p in level.get_points_in_ball(current.x, current.y, 1):
				if not level.tiles[p.x][p.y].can_see:
					choices.append(p)

# Turns all tiles surrounded by floors into chasms
def chasmify(levelgen):
	level = levelgen.level
	level_logger.debug("Chasmify")
	# A tile can be a chasm if all adjacent tiles are pathable without this tile
	chasms = []
	for i in range(1, levelgen.level.size - 1):
		for j in range(1, levelgen.level.size - 1):
			neighbors = level.get_points_in_rect(i-1, j-1, i+1, j+1)
			if all(level.can_walk(p.x, p.y) for p in neighbors):
				chasms.append(Point(i, j))

	for p in chasms:
		level.make_chasm(p.x, p.y)

# Turns all tiles surrounded by visible tiles into walls
def wallify(levelgen):
	level = levelgen.level
	level_logger.debug("Wallify")
	# A tile can be a chasm if all adjacent tiles are pathable without this tile
	chasms = []
	for i in range(1, levelgen.level.size - 1):
		for j in range(1, levelgen.level.size - 1):
			neighbors = level.get_points_in_rect(i-1, j-1, i+1, j+1)
			if all(level.tiles[p.x][p.y].can_see for p in neighbors):
				chasms.append(Point(i, j))

	for p in chasms:
		level.make_wall(p.x, p.y)

def grid(levelgen, stagger=None, chance=None):
	level = levelgen.level

	if not stagger:
		stagger = levelgen.random.choice([2, 3, 4, 7])
	if not chance:
		chance = levelgen.random.choice([.1, .5, 1, 1])

	floor_tiles = [t for t in level.iter_tiles() if t.can_walk]
	blocked_tiles = [t for t in level.iter_tiles() if not t.can_walk]

	invert = len(floor_tiles) > len(blocked_tiles) 

	chasm = False
	if invert:
		chasm = levelgen.random.choice([True, False])

	modestr = 'floor' if not invert else 'chasm' if chasm else 'wall'
	level_logger.debug("Grid: %d, %.2f, (%s)" % (stagger, chance, modestr))

	for i in range(levelgen.level.width):
		for j in range(levelgen.level.height):
			p = Point(i, j)
			if levelgen.random.random() > chance:
				continue
			if (i % stagger) == (j % stagger) == 0:
				if invert:
					level.make_wall(p.x, p.y)
				else:
					if chasm:
						level.make_chasm(p.x, p.y)
					else:
						level.make_floor(p.x, p.y)


def is_in_rect(i, j, border_size, level):
	if i < border_size:
		return False
	if level.width - i - 1 < border_size:
		return False
	if j < border_size:
		return False
	if level.height - j - 1 < border_size:
		return False
	return True

def is_in_circle(i, j, border_size, level):
	center = Point(level.width // 2 - .5, level.width // 2 - .5)
	radius = level.width // 2 - border_size
	return distance(Point(i, j), center) < radius

def is_in_diamond(i, j, border_size, level):
	halfsize = level.width // 2
	dist = abs(i - halfsize + .5) + abs(j - halfsize + .5)
	radius = halfsize - border_size + 4
	return dist < radius

def border(levelgen, force_chasm=False, force_wall=False, size=None, force_rect=False):
	level = levelgen.level

	if size is None:
		size = levelgen.random.randint(1, 6)

	chasm = levelgen.random.choice([True, False, False, False])
	if force_chasm:
		chasm = True
	if force_wall:
		chasm = False

	test = levelgen.random.choice([is_in_rect, is_in_circle, is_in_diamond])
	if force_rect:
		test = is_in_rect

	level_logger.debug("Border: %d (%s, %s)" % (size, 'c' if chasm else 'w', test.__name__))

	for i in range(levelgen.level.width):
		for j in range(levelgen.level.height):

			do = not test(i, j, size, levelgen.level)
			if do:
				if not chasm:
					level.make_wall(i, j)
				else:
					level.make_chasm(i, j)


def white_noise(levelgen):
	level = levelgen.level
	chance = levelgen.random.choice([.05, .1, .2, .3])

	floor_tiles = [t for t in level.iter_tiles() if t.can_walk]
	blocked_tiles = [t for t in level.iter_tiles() if not t.can_walk]

	if len(floor_tiles) > len(blocked_tiles):
		if levelgen.random.choice([True, False]):
			mode = 'chasm'
		else:
			mode = 'wall'
	else:
		mode = 'floor'

	level_logger.debug("White Noise: %.2f (%s)" % (chance, mode))

	for t in level.iter_tiles():
		if levelgen.random.random() < chance:
			if mode == 'wall':
				level.make_wall(t.x, t.y)
			elif mode == 'chasm':
				level.make_chasm(t.x, t.y)
			elif mode == 'floor':
				level.make_floor(t.x, t.y)
			else:
				assert(False)

def squares(levelgen):
	# TODO-
	# Borders not always walls

	level = levelgen.level
	max_size = levelgen.random.randint(6, 10)
	min_size = max_size // 2
	num = levelgen.random.randint(4, 10)
	floor_tiles = [t for t in level.iter_tiles() if t.can_walk]
	blocked_tiles = [t for t in level.iter_tiles() if not t.can_walk]

	if len(floor_tiles) > len(blocked_tiles):
		if levelgen.random.choice([True, False]):
			mode = 'chasm'
		else:
			mode = 'wall'
	else:
		mode = 'floor'

	level_logger.debug("Squares: s%d n%d (%s)" % (max_size, num, mode))

	border = True
	for i in range(num):

		x = levelgen.random.randint(0, levelgen.level.size - max_size)
		y = levelgen.random.randint(0, levelgen.level.size - max_size)
		w = levelgen.random.randint(min_size, max_size)
		h = levelgen.random.randint(min_size, max_size)
		for i in range(w):
			for j in range(h):
				cur_x = x + i
				cur_y = y + j
				if mode == 'wall':
					level.make_wall(cur_x, cur_y)
				elif mode == 'chasm':
					level.make_chasm(cur_x, cur_y)
				elif mode == 'floor':
					level.make_floor(cur_x, cur_y)
				else:
					assert(False)

		if border:
			for i in range(w):
				level.make_wall(x + i, y)
				level.make_wall(x + i, y + h - 1)
			for j in range(h):
				level.make_wall(x, y + j)
				level.make_wall(x + w - 1,  y + j)


def bisymmetry(levelgen):
	level = levelgen.level

	# Which axis does the symmetry come from
	axis = levelgen.random.choice(['x', 'y'])

	ideal_floors = levelgen.level.size*levelgen.level.size // 4

	mirror = levelgen.random.choice([True, False])

	level_logger.debug("Bisymmetry (%s, %s)" % (axis, 'mirror' if mirror else 'flip'))

	def get_src(i, j):
		if axis == 'y':
			return Point(i, j)
		elif axis == 'x':
			return Point(j, i)

	# Returns the tile we will be copying x, y to
	def get_tgt(x, y):
		if mirror:
			return Point(levelgen.level.size-x-1, levelgen.level.size-y-1)
		if axis == 'y':
			return Point(levelgen.level.size-x-1, y)
		if axis == 'x' and not mirror:
			return Point(x, levelgen.level.size-y-1)

	for i in range((levelgen.level.size // 2)):
		for j in range(levelgen.level.size):
			
			src_x, src_y = get_src(i, j)
			cur_tile = level.tiles[src_x][src_y]
			tgt_x, tgt_y = get_tgt(src_x, src_y)

			if cur_tile.is_wall():
				level.make_wall(tgt_x, tgt_y)
			if cur_tile.is_floor():		
				level.make_floor(tgt_x, tgt_y)
			if cur_tile.is_chasm:
				level.make_chasm(tgt_x, tgt_y)

def lumps(levelgen, num_lumps=None, space_size=None):
	if num_lumps is None:
		num_lumps = levelgen.random.randint(1, 12)
	if space_size is None:
		space_size = levelgen.random.randint(10, 100)

	level = levelgen.level

	options = []
	max_existing = 550
	if len([t for t in level.iter_tiles() if not t.can_walk]) < max_existing:
		options.append('wall')
		options.append('chasm')
	if len([t for t in level.iter_tiles() if t.is_floor()]) < max_existing:
		options.append('floor')

	mode = levelgen.random.choice(options)

	level_logger.debug("Lumps: %d %d (%s)" % (num_lumps, space_size, mode))

	for i in range(num_lumps):

		start_point = Point(levelgen.random.randint(0, levelgen.level.size-1), levelgen.random.randint(0, levelgen.level.size-1))
		candidates = [start_point]
		chosen = set()

		for j in range(space_size):
			cur_point = levelgen.random.choice(candidates)
			candidates.remove(cur_point)

			chosen.add(cur_point)

			for point in level.get_points_in_ball(cur_point.x, cur_point.y, 1):
				if point not in candidates and point not in chosen:
					candidates.append(point)

	for p in chosen:
		if mode == 'wall':
			level.make_wall(p.x, p.y)
		if mode == 'floor':
			level.make_floor(p.x, p.y)
		if mode == 'chasm':
			level.make_chasm(p.x, p.y)

def quads(levelgen):
	level = levelgen.level
	level_logger.debug("Quadrants")
	for i in range(levelgen.level.size // 2):
		for j in range(levelgen.level.size // 2):

			cur_tile = level.tiles[i][j]

			tgts = [
				Point(i, j + levelgen.level.size // 2),
				Point(i + levelgen.level.size // 2, j),
				Point(i + levelgen.level.size // 2, j + levelgen.level.size // 2)
			]
			for tgt_x, tgt_y in tgts:
				if cur_tile.is_wall():
					level.make_wall(tgt_x, tgt_y)
				if cur_tile.is_floor():		
					level.make_floor(tgt_x, tgt_y)
				if cur_tile.is_chasm:
					level.make_chasm(tgt_x, tgt_y)

def radialquads(levelgen):
	level = levelgen.level
	level_logger.debug("Radial Quadrants")
	for i in range(levelgen.level.size // 2):
		for j in range(levelgen.level.size // 2):

			cur_tile = level.tiles[i][j]

			tgts = [
				Point(i, levelgen.level.size - j - 1),
				Point(levelgen.level.size - i - 1, j),
				Point(levelgen.level.size - i - 1, levelgen.level.size - j - 1)
			]

			for tgt_x, tgt_y in tgts:
				if cur_tile.is_wall():
					level.make_wall(tgt_x, tgt_y)
				if cur_tile.is_floor():		
					level.make_floor(tgt_x, tgt_y)
				if cur_tile.is_chasm:
					level.make_chasm(tgt_x, tgt_y)

def paths(levelgen, num_points=None):
	level = levelgen.level
	if num_points is None:
		num_points = levelgen.random.choice([5, 8, 10, 15, 20, 30, 40, 50, 60, 75])
	all_points = [Point(i, j) for i in range(levelgen.level.size) for j in range(levelgen.level.size)]
	levelgen.random.shuffle(all_points)

	start_points = []
	for i in range(num_points):
		start_points.append(all_points.pop())

	options = []
	max_existing = 550
	if len([t for t in level.iter_tiles() if not t.can_walk]) < max_existing:
		options.append('wall')
		options.append('chasm')
	if len([t for t in level.iter_tiles() if t.is_floor()]) < max_existing:
		options.append('floor')

	reconnect_chance = levelgen.random.choice([0, 0, .2, .2, .5, .5])
	mode = levelgen.random.choice(options)
	level_logger.debug("Paths: %d, %.2f, %s" % (num_points, reconnect_chance, mode))


	# Make start points a list and use PRNG to pick paths so that levelgen is reproducable
	levelgen.random.shuffle(start_points)
	end_points = [start_points.pop()]

	# for each start point, connect it to the graph
	while start_points:

		cur_start_point = levelgen.random.choice(start_points)
		start_points.remove(cur_start_point)

		possible_end_points = sorted(end_points, key=lambda p: distance(p, cur_start_point))[:4]
		cur_end_point = levelgen.random.choice(possible_end_points)

		end_points.append(cur_start_point)

		cur_point = cur_start_point
		while (cur_point != cur_end_point):
			
			if mode == 'floor':
				level.make_floor(cur_point.x, cur_point.y)
			if mode == 'wall':
				level.make_wall(cur_point.x, cur_point.y)
			if mode == 'chasm':
				level.make_chasm(cur_point.x, cur_point.y)

			trydir = levelgen.random.randint(0, 3)
			if trydir == 0 and cur_point.x < cur_end_point.x:
				cur_point = Point(cur_point.x + 1, cur_point.y)
			if trydir == 1 and  cur_point.x > cur_end_point.x:
				cur_point = Point(cur_point.x - 1, cur_point.y)
			if trydir == 2 and cur_point.y < cur_end_point.y:
				cur_point = Point(cur_point.x, cur_point.y + 1)
			if trydir == 3 and cur_point.y > cur_end_point.y:
				cur_point = Point(cur_point.x, cur_point.y - 1)

		# 20% of the time re-add it- this way there are more paths
		if levelgen.random.random() < reconnect_chance:
			start_points.append(cur_start_point)

def conway(levelgen):
	n = levelgen.random.choice([1, 3, 10])
	level_logger.debug("Game of life: %d" % n)
	level = levelgen.level
	def populated(x, y):
		return level.tiles[x][y].is_wall()

	def populate(x, y):
		level.make_wall(x, y)

	def depopulate(x, y):
		level.make_floor(x, y)

	for i in range(n):
		grid = {}

		for x in range(levelgen.level.size):
			for y in range(levelgen.level.size):
				num_adj = len(list(p for p in level.get_points_in_ball(x, y, 1, diag=True) if populated(p.x, p.y)))
				if populated(x, y):
					if num_adj <= 2:
						grid[x, y] = False
					elif num_adj >= 5:
						grid[x, y] = False
					else:
						grid[x, y] = True
				else:
					if num_adj >= 3:
						grid[x, y] = True
					else:
						grid[x, y] = False

		for (x, y), v in grid.items():
			if v:
				populate(x, y)
			else:
				depopulate(x, y)

def section(levelgen):
	level = levelgen.level
	method = levelgen.random.choice([level.make_wall, level.make_floor, level.make_chasm])
	start = levelgen.random.randint(6, levelgen.level.size-6)
	axis = levelgen.random.choice(['x', 'y'])
	flip = levelgen.random.choice([True, False])

	level_logger.debug("Section: %s, %s, %s, %s" % (method, start, axis, flip))

	for i in range(levelgen.level.size):
		for j in range(levelgen.level.size):

			do = False
			to_check = i if axis == 'x' else j
			
			if flip:
				do = to_check < start
			else:
				do = to_check > start
			
			if do:
				method(i, j) 

seed_mutators = [
	paths,
	white_noise,
	lumps,
	squares,
	grid
]

mutator_table = [
	expand_floor,	
	walls_to_chasms,
	chasmify,
	white_noise,
	squares,
	bisymmetry,
	wallify,
	grid,
	border,
	quads,
	paths,
	conway,
	radialquads,
	lumps,
	section
]
