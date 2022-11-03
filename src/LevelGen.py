from Level import *
from Monsters import *
from Spells import *
from Consumables import *
from Shrines import *
from RareMonsters import *
from Variants import roll_variant
import random
from collections import namedtuple
LEVEL_SIZE = 28

USE_VARIANTS = True

import sys

import logging
level_logger = logging.getLogger("Level")
level_logger.setLevel(logging.DEBUG)
level_logger.propagate = False
level_logger.addHandler(logging.FileHandler('level_log.txt', mode='w'))

class Biome():

	def __init__(self, tileset, tags=None, waters=None, stars=None, limit_walls=False, needs_chasms=True, min_level=0):
		self.tileset = tileset
		self.tags = tags
		self.waters = waters if waters is not None else default_water_table
		self.stars = stars
		self.limit_walls = limit_walls
		self.needs_chasms = needs_chasms
		self.min_level = min_level

	def can_spawn(self, levelgen):
		if not self.tags:
			return True

		if levelgen.difficulty < self.min_level:
			return False

		if self.limit_walls:
			wall_count = len([t for t in levelgen.level.iter_tiles() if t.is_wall()])
			if wall_count > 150:
				return False

		if self.needs_chasms:
			chasm_count = len([t for t in levelgen.level.iter_tiles() if t.is_chasm])
			if chasm_count < 50:
				return False

		if self.tags:
			has_tags = False
			monsters = [s[0]() for s in levelgen.spawn_options]
			for tag in self.tags:
				for m in monsters:
					if tag in m.tags:
						has_tags = True
			# DIsable tags?
			#if not has_tags:
			#	return False

		return True

WATER_BLUE = "water4/blue1"
WATER_TEAL = "water4/blue2"
WATER_BROWN = "water4/brown1"
WATER_GREEN = "water4/green1"
WATER_RED = "water4/red1"

default_water_table = [
	WATER_BLUE,
	WATER_BLUE,
	WATER_BLUE,
	WATER_RED,
	WATER_RED,
	WATER_BROWN,
	WATER_TEAL,
	WATER_GREEN,
	None,
	None
]

all_biomes = [
	Biome('stone'),
	Biome('cavern'),
	Biome('dead woods', tags=[Tags.Nature, Tags.Undead]),
	#Biome('dark woods', tags=[Tags.Living]),
	Biome('dying woods', tags=[Tags.Undead, Tags.Dark], limit_walls=True, needs_chasms=True),
	Biome('flesh', tags=[Tags.Demon], needs_chasms=True),
	Biome('fossil', tags=[Tags.Nature, Tags.Dragon]),
	Biome('giant skull', tags=[Tags.Undead, Tags.Dragon]),
	Biome('glass', tags=[Tags.Arcane], needs_chasms=True, limit_walls=True),
	#Biome('ruby', tags=[Tags.Fire]),
	#Biome('winter', tags=[Tags.Ice]),
	#Biome('winter woods', tags=[Tags.Nature, Tags.Ice]),
	#Biome('spooky', tags=[Tags.Dark, Tags.Undead]),
	#Biome('sea cave', tags=[Tags.Dragon, Tags.Arcane]),
	#Biome('night stone', tags=[Tags.Dark, Tags.Undead]),
	Biome('brown mushroom', tags=[Tags.Living, Tags.Arcane], limit_walls=True),
	Biome('dungeon', tags=[Tags.Construct, Tags.Dark]),
	Biome('orc fortress', tags=[Tags.Construct, Tags.Dark]),
	#Biome('winter mushroom', tags=[Tags.Ice]),
	Biome('purple bubble', tags=[Tags.Arcane, Tags.Demon], needs_chasms=True, limit_walls=True),
	Biome('green mushroom', tags=[Tags.Living, Tags.Nature], limit_walls=True),
	#Biome('giant ice skull', tags=[Tags.Ice, Tags.Undead, Tags.Dark]),
	Biome('giant dirt skull', tags=[Tags.Undead, Tags.Nature, Tags.Dark]),
	#Biome('giant blood skull', tags=[Tags.Demon, Tags.Undead]),
	Biome('dark mushroom', tags=[Tags.Dark], limit_walls=True),
	#Biome('brown desert', tags=[Tags.Dark]),
	Biome('green bubble', tags=[Tags.Arcane, Tags.Nature], needs_chasms=True),
	#Biome('red bubble', tags=[Tags.Arcane, Tags.Demon]),
	#Biome('bug forest', tags=[Tags.Ice]),
	#Biome('arcane dream', tags=[Tags.Arcane]),
	#Biome('blood crater', tags=[Tags.Demon, Tags.Fire]),
	#Biome('dark dream', tags=[Tags.Dark]),
	Biome('mossy hills', tags=[Tags.Nature], needs_chasms=True, limit_walls=True),
	Biome('green mystery', tags=[Tags.Nature, Tags.Arcane, Tags.Construct]),
	Biome('blue mystery', tags=[Tags.Arcane, Tags.Holy, Tags.Construct]),
	Biome('brown crater', tags=[Tags.Living], limit_walls=True)

]

def random_point(levelgen):
	return Point(levelgen.random.randint(0, LEVEL_SIZE - 1), levelgen.random.randint(0, LEVEL_SIZE - 1))

def get_spawn_min_max(difficulty):

	spawn_levels = [
		(1, 1), # 1
		(1, 1), # 2
		(1, 2), # 3 
		(1, 3), # 4
		(2, 3), # 5 
		(2, 4), # 6
		(2, 4), # 7
		(2, 4), # 8
		(2, 4), # 9
		(3, 4), # 10
		(3, 5), # 11
		(3, 5), # 12
		(3, 5), # 13
		(4, 5), # 14
		(4, 5), # 15
		(4, 6), # 16
		(5, 6), # 17
		(5, 6), # 18
		(5, 6), # 19
		(5, 7), # 20
		(5, 7), # 21
		(5, 7), # 22
		(6, 8), # 23
		(7, 8), # 24
	]


	# This formula is weird and appears to do very strange things but im not going to change it now because balance is good
	index = min(difficulty - 1, len(spawn_levels) - 1)

	min_level, max_level = spawn_levels[index]
	return min_level, max_level 



def make_consumable_pickup(item):
	prop = ItemPickup(item)
	prop.sprite.char = chr(6)
	prop.sprite.color = COLOR_CONSUMABLE
	return prop

def make_scroll_shop():
	shop = Shop()
	shop.sprite.char = chr(20)
	shop.sprite.color = COLOR_MANA
	shop.items = [scroll(spell()) for spell in all_player_spells]
	self.random.shuffle(shop.items)
	shop.items = shop.items[:7]
	shop.currency = CURRENCY_PICK
	shop.name = "Arcane Library"
	shop.description = "Contains knowlege of:\n\n"
	for spell in shop.items:
		shop.description += spell.name + "\n"
	shop.description += "\n...but you will only have time to learn one"
	
	return shop

LevelParams = namedtuple("LevelParams", "monsters generators spells artifacts num_hearts")


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
	for i in range(1, LEVEL_SIZE - 1):
		for j in range(1, LEVEL_SIZE - 1):
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
	for i in range(1, LEVEL_SIZE - 1):
		for j in range(1, LEVEL_SIZE - 1):
			neighbors = level.get_points_in_rect(i-1, j-1, i+1, j+1)
			if all(level.tiles[p.x][p.y].can_see for p in neighbors):
				chasms.append(Point(i, j))

	for p in chasms:
		level.make_wall(p.x, p.y)

def grid(levelgen):
	level = levelgen.level
	stagger = levelgen.random.choice([2, 3, 4, 7])
	chance = levelgen.random.choice([.1, .5, 1, 1])

	floor_tiles = [t for t in level.iter_tiles() if t.can_walk]
	blocked_tiles = [t for t in level.iter_tiles() if not t.can_walk]

	invert = len(floor_tiles) > len(blocked_tiles) 

	chasm = False
	if invert:
		chasm = levelgen.random.choice([True, False])

	modestr = 'floor' if not invert else 'chasm' if chasm else 'wall'
	level_logger.debug("Grid: %d, %.2f, (%s)" % (stagger, chance, modestr))

	for i in range(LEVEL_SIZE):
		for j in range(LEVEL_SIZE):
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


def is_in_square(i, j, size):
	if i < size:
		return False
	if LEVEL_SIZE - i - 1 < size:
		return False
	if j < size:
		return False
	if LEVEL_SIZE - j - 1 < size:
		return False
	return True

def is_in_circle(i, j, size):
	center = Point(LEVEL_SIZE // 2 - .5, LEVEL_SIZE // 2 - .5)
	radius = LEVEL_SIZE // 2 - size
	return distance(Point(i, j), center) < radius

def is_in_diamond(i, j, size):
	halfsize = LEVEL_SIZE // 2
	dist = abs(i - halfsize + .5) + abs(j - halfsize + .5)
	radius = halfsize - size + 4
	return dist < radius

def border(levelgen):
	level = levelgen.level
	size = levelgen.random.randint(1, 6)

	chasm = levelgen.random.choice([True, False, False, False])

	test = levelgen.random.choice([is_in_square, is_in_circle, is_in_diamond])

	level_logger.debug("Border: %d (%s)" % (size, 'c' if chasm else 'w'))

	for i in range(LEVEL_SIZE):
		for j in range(LEVEL_SIZE):

			do = not test(i, j, size)
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

		x = levelgen.random.randint(0, LEVEL_SIZE - max_size)
		y = levelgen.random.randint(0, LEVEL_SIZE - max_size)
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

	ideal_floors = LEVEL_SIZE*LEVEL_SIZE // 4

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
			return Point(LEVEL_SIZE-x-1, LEVEL_SIZE-y-1)
		if axis == 'y':
			return Point(LEVEL_SIZE-x-1, y)
		if axis == 'x' and not mirror:
			return Point(x, LEVEL_SIZE-y-1)

	for i in range((LEVEL_SIZE // 2)):
		for j in range(LEVEL_SIZE):
			
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

		start_point = Point(levelgen.random.randint(0, LEVEL_SIZE-1), levelgen.random.randint(0, LEVEL_SIZE-1))
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
	for i in range(LEVEL_SIZE // 2):
		for j in range(LEVEL_SIZE // 2):

			cur_tile = level.tiles[i][j]

			tgts = [
				Point(i, j + LEVEL_SIZE // 2),
				Point(i + LEVEL_SIZE // 2, j),
				Point(i + LEVEL_SIZE // 2, j + LEVEL_SIZE // 2)
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
	for i in range(LEVEL_SIZE // 2):
		for j in range(LEVEL_SIZE // 2):

			cur_tile = level.tiles[i][j]

			tgts = [
				Point(i, LEVEL_SIZE - j - 1),
				Point(LEVEL_SIZE - i - 1, j),
				Point(LEVEL_SIZE - i - 1, LEVEL_SIZE - j - 1)
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
	all_points = [Point(i, j) for i in range(LEVEL_SIZE) for j in range(LEVEL_SIZE)]
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

		for x in range(LEVEL_SIZE):
			for y in range(LEVEL_SIZE):
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
	start = levelgen.random.randint(6, LEVEL_SIZE-6)
	axis = levelgen.random.choice(['x', 'y'])
	flip = levelgen.random.choice([True, False])

	level_logger.debug("Section: %s, %s, %s, %s" % (method, start, axis, flip))

	for i in range(LEVEL_SIZE):
		for j in range(LEVEL_SIZE):

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
	section
]

class LevelGenerator():

	def __init__(self, difficulty, game=None, seed=None):
		
		self.next_level_seeds = None			
		self.random = random.Random()

		if seed:
			level_logger.debug("Seeding levelgen with %f" % seed)
			self.random = random.Random(seed)
			if game:
				self.next_level_seeds = game.get_seeds(difficulty)
				self.random.shuffle(self.next_level_seeds)

		self.difficulty = difficulty
		self.num_xp = 3
		self.level_id = self.random.randint(0, 1000000)
		self.is_town = False
		self.num_hearts = 0
		self.num_start_points = self.random.choice([5, 8, 10, 15, 20, 30, 40, 50, 60, 75])
		self.reconnect_chance = self.random.choice([0, 0, .2, .2, .5, .5])
		self.game = game
		self.num_open_spaces = self.random.choice([0, 0, 0, 2, 3, 5, 7, 12])
		self.num_exits = self.random.choice([2, 2, 3, 3, 3, 3, 4])

		self.spawn_options = self.get_spawn_options(difficulty)
		self.num_monsters = self.random.randint(5, 20)
		self.num_elites = 0
		self.elite_spawn = None

		max_generators = 3 if difficulty < 5 else 5 if difficulty < 10 else 7 if difficulty < 20 else 9
		min_generators = 3 if difficulty < 10 else 4 if difficulty < 20 else 5
		self.num_generators = 3 if difficulty == 2 else self.random.randint(min_generators, max_generators)

		self.num_hp_upgrades = 0 #self.random.choice([0, 0, 0, 0, 0, 0, 1, 1, 2])
		self.num_places_of_power = 0
		self.num_recharges = self.random.choice([0, 0, 0, 1, 1, 2])
		if self.difficulty < 5:
			self.num_recharges = 1
		
		self.num_heals = self.random.choice([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2])

		self.num_libraries = 0
		
		self.shrine = None
		if self.game:
			self.shrine = None if difficulty in [1, LAST_LEVEL] else roll_shrine(self.difficulty, self.random)(self.game.p1)

		self.extra_circle = None
		#if difficulty > 10:
		#	self.extra_circle = self.random.choice([None, None, None, library()])

		num_consumables = self.random.choice([0, 0, 0, 0, 1, 1, 2, 3]) # For now its 2
		if self.difficulty == 2:
			num_consumables = 1
		if self.difficulty == 1:
			num_consumables = 0

		num_scrolls = 0
		#if num_consumables < 2 and difficulty > 1:
		#	num_scrolls = self.random.choice([0, 0, 0, 1, 1, 1, 2, 3])

		self.scroll_spells = []
		for _ in range(num_scrolls):
			eligible = [s for s in all_player_spells if s.level > 1 and s.name not in [t.name for t in player.spells]]
			spell = self.random.choice(eligible)
			self.scroll_spells.append(spell)

		self.bosses = [] 

		num_boss_spawns = (0 if difficulty <= 1 else
						   1 if difficulty <= 3 else
						   2 if difficulty <= 8 else
						   3)

		# for debugging
		if 'forcevariant' in sys.argv:
			num_boss_spawns = 1

		for i in range(num_boss_spawns):

			spawn_type = self.random.choice(self.spawn_options)
			roll_result = roll_variant(spawn_type[0], self.random)

			# 50% chance to make a variant if we can, otherwise make an elite
			# Should be- 50% first time, 30% subsequent times

			chance = .5 if i == 0 else .3
			if 'forcevariant' in sys.argv:
				self.bosses.extend(roll_result)
			else:			
				if USE_VARIANTS and roll_result and self.random.random() < chance:
					self.bosses.extend(roll_result)
				else:
					self.bosses.extend(self.get_elites(difficulty))


		num_uniques = 0
		if 6 <= difficulty <= 10:
			num_uniques = self.random.choice([0, 0, 1])
		if 11 <= difficulty <= 19:
			num_uniques = self.random.choice([1, 1, 2])
		if 19 <= difficulty <= 22:
			num_uniques = self.random.choice([2, 3])
		if 23 <= difficulty < LAST_LEVEL:
			num_uniques = 3

		if 'forcerare' in sys.argv:
			num_uniques = 1

		for i in range(num_uniques):
			tags = set()
			
			for o in self.spawn_options:
				for t in o[0]().tags:
					tags.add(t)

			spawns = roll_rare_spawn(difficulty, tags, prng=self.random)
			self.bosses.extend(spawns)

		if difficulty == 1:
			self.num_generators = 1
			if 'forcespawn' not in sys.argv:
				self.num_monsters = 4
			else:
				self.num_monsters = 1
			self.num_libraries = 2
			self.num_elites = 0
			self.num_open_spaces = 5
			self.num_shrines = 0
			self.num_heals = 0
			self.num_recharges = 0
			self.num_exits = 3
			self.num_scrolls = 0

		if difficulty == LAST_LEVEL - 1:
			self.num_exits = 1

		if difficulty == LAST_LEVEL:
			self.bosses = [Mordred()]
			self.num_libraries = 0
			self.num_shrines = 0
			self.num_recharges = 0
			self.num_heals = 0
			self.num_generators = 0
			self.num_exits = 0

		self.items = []
		for _ in range(num_consumables):
			self.items.append(roll_consumable(prng=self.random))

		for _ in range(self.num_heals):
			self.items.append(heal_potion())

		for _ in range(self.num_recharges):
			self.items.append(mana_potion())

		# For mouseover- spice up the ordering
		self.random.shuffle(self.items)

		if self.game:
			for m in self.game.mutators:
				m.on_levelgen_pre(self)

		self.description = self.get_description()

	def get_elites(self, difficulty):
		_, level = get_spawn_min_max(difficulty)

		if difficulty < 5:
			modifier = 1
		else:
			modifier = self.random.choice([1, 1, 1, 1, 2, 2])

		level = min(level + modifier, 9)

		if modifier == 1:
			num_elites = self.random.choice([5, 6, 7])
		if modifier == 2:
			num_elites = self.random.choice([3, 4, 5])
		if modifier == 3:
			num_elites = self.random.choice([2, 3])

		options = [(s, l) for s, l in spawn_options if l == level]
		spawner = self.random.choice(options)[0]

		units = [spawner() for i in range(num_elites)] 
		return units

	def get_spawn_options(self, difficulty, num_spawns=None):

		if 'forcespawn' in sys.argv:
			forcedspawn_name = sys.argv[sys.argv.index('forcespawn') + 1]
			forced_spawn_options = [(spawn, cost) for (spawn, cost) in spawn_options if forcedspawn_name.lower() in spawn.__name__.lower()]
			assert(len(forced_spawn_options) > 0)
			return forced_spawn_options

		min_level, max_level = get_spawn_min_max(difficulty)
		if not num_spawns:
			num_spawns = self.random.choice([1, 2, 2, 2, 3, 3, 3])

		spawns = []
		# force 1 higher level spawn
		max_level_options = [(s, l) for s, l in spawn_options if (l == max_level) or (l == max_level - 1)]
		spawns.append(self.random.choice(max_level_options))

		# generate the rest randomly
		other_spawn_options = [(s, l) for s, l, in spawn_options if l >= min_level and l <= max_level and (s, l) not in spawns]
		for i in range(num_spawns - 2):
			if not other_spawn_options:
				break
			cur_option = self.random.choice(other_spawn_options)
			spawns.append(cur_option)
			other_spawn_options.remove(cur_option)

		return spawns

	def has_spawn(self, spawn_class):
		return any((s, _) for (s, _) in self.spawn_options if s == spawn_class)

	def get_description(self):
		description = "A portal to another realm"
		description += "num_start_points: %d" % self.num_start_points
		description += "reconnect_chance: %.2f" % self.reconnect_chance
		description += "num_open_spaces: %d" % self.num_open_spaces
		return description

	def make_child_generator(self, difficulty=None):
		if not difficulty:
			difficulty = self.difficulty + 1
		
		if self.next_level_seeds:
			seed = self.next_level_seeds.pop()
		else:
			seed = self.random.random()

		return LevelGenerator(difficulty, self.game, seed)

	def make_level(self):

		level_logger.debug("\nGenerating level for %d" % self.difficulty)
		level_logger.debug("Level id: %d" % self.level_id)
		level_logger.debug("num start points: %d" % self.num_start_points)
		level_logger.debug("reconnect chance: %.2f" % self.reconnect_chance)
		level_logger.debug("num open spaces: %d" % self.num_open_spaces)

		self.level = Level(LEVEL_SIZE, LEVEL_SIZE)
		self.make_terrain()
		
		self.populate_level()

		self.level.gen_params = self
		self.level.calc_glyphs()

		if self.difficulty == 1:
			self.level.biome = all_biomes[0]
		else:
			self.level.biome = self.random.choice([b for b in all_biomes if b.can_spawn(self)]) 

		self.level.tileset = self.level.biome.tileset
		
		self.level.water = self.random.choice(self.level.biome.waters + [None])
		# Always start with blue water so people understand what a chasm is
		if self.difficulty == 1:
			self.level.water = WATER_BLUE

		# Game looks better without water
		self.level.water = None

		# Record info per tile so that mordred corruption works
		for tile in self.level.iter_tiles():
			tile.tileset = self.level.tileset
			tile.water = self.level.water

		if self.game:
			for m in self.game.mutators:
				m.on_levelgen(self)
				
		self.log_level()

		return self.level

	def log_level(self):
		#Print ascii art of level
		for i in range(LEVEL_SIZE):
			row = ''
			for j in range(LEVEL_SIZE):
				t = self.level.tiles[i][j]
				c = '#'
				if t.can_walk:
					c='.'
				elif t.can_see:
					c = ' '
				row = row + c
			level_logger.debug(row)

	def ensure_connectivity(self, chasm=False):
		# For each tile
		# If it is 

		# Tile -> Label
		# For each (floor) tile
		#  If it is not labelled
		#  Label it i+1 and then traverse all connected tiles, assigning same label
		# At the end you have some number of labels
		# For each label
		# Find the shortest distance to a tile with another label
		# Connect those tiles by turning wall tiles into floor tiles
		def qualifies(tile):
			# When connecting chasms, it is ok for them to be connected over any non wall tile- just check LOS
			if chasm:
				return tile.can_see
			else:
				return tile.can_walk

		def make_path(x, y):
			if chasm:
				if not self.level.tiles[x][y].can_see:
					self.level.make_chasm(x, y)
			else:
				self.level.make_floor(x, y)

		def iter_neighbors(tile):
			visited = set([tile])
			to_visit = [tile]
			while to_visit:
				cur = to_visit.pop()

				for p in self.level.get_points_in_ball(cur.x, cur.y, 1, diag=True):
					t = self.level.tiles[p.x][p.y]
					
					if t in visited:
						continue

					if not qualifies(t):
						continue

					visited.add(t)
					to_visit.append(t)
					yield t

		cur_label = 0
		tile_labels = {}

		for tile in self.level.iter_tiles():
			# Do not label walls (or chasms when not doing the chasm pass)
			if not qualifies(tile):
				continue

			if tile not in tile_labels:
				cur_label += 1
				tile_labels[tile] = cur_label

				for neighbor in iter_neighbors(tile):
					tile_labels[neighbor] = cur_label
				
		# Instead of using a set, deterministically shuffle a list using the seeded randomizer
		labels_left = list(set(tile_labels.values()))

		# Sort first to derandomize initial ordering
		labels_left.sort()
		self.random.shuffle(labels_left)
		
		while len(labels_left) > 1:
			cur_label = labels_left.pop()
			best_dist = 100000
			best_inner = None
			best_outer = None
			for cur_inner in tile_labels.keys():
				
				if tile_labels[cur_inner] != cur_label:
					continue

				for cur_outer in tile_labels.keys():
					if tile_labels[cur_outer] not in labels_left:
						continue

					# Add random increment to randomly break ties
					cur_dist = distance(cur_inner, cur_outer) + self.random.random()
					if cur_dist < best_dist:
						best_dist = cur_dist
						best_inner = cur_inner
						best_outer = cur_outer

			for p in self.level.get_points_in_line(best_inner, best_outer):
				make_path(p.x, p.y)					

	def make_terrain(self):

		chasm = self.random.choice([True, False])
		level_logger.debug("Filling with %s" % 'chams' if chasm else 'walls')
		for x in range(LEVEL_SIZE):
			for y in range(LEVEL_SIZE):
				if not chasm:
					self.level.make_wall(x, y)
				else:
					self.level.make_chasm(x, y)

		if self.difficulty > 1:
			num_seeds = self.random.randint(0, 5)
			level_logger.debug("Seed mutators:")
			for i in range(num_seeds):
				mutator = self.random.choice(seed_mutators)
				mutator(self)

			# Mutate
			level_logger.debug("Extra mutators:")
			num_mutators = self.random.choice([0, 0, 1, 3, 5, 6, 9, 13])

			for i in range(num_mutators):
				mutator = self.random.choice(mutator_table)
				mutator(self)

		else:
			paths(self)
			lumps(self, num_lumps=5, space_size=140)

		# Generally end with paths- otherwise you end up with frequent bottlenecks
		#if self.random.random() < .8:
		#	points = self.random.randint(2, 10)
		#	paths(self, num_points=points)

		# Do border
		self.tidy_border()

		# Ensure atleast 20 walls and 20 floors
		fix_attempts = 10
		min_floors = 100
		min_walls = 100
		for i in range(fix_attempts):
			num_floors = len([t for t in self.level.iter_tiles() if t.can_walk])
			num_walls = len([t for t in self.level.iter_tiles() if not t.can_walk])
			level_logger.debug("%d floors, %d walls)" % (num_floors, num_walls))

			if min_floors > num_floors or min_walls > num_walls:
				level_logger.debug("Trying to fix boring level:")
				mutator = self.random.choice(seed_mutators)
				mutator(self)
			else:
				break

		# Ensure connectivity
		self.ensure_connectivity(chasm=False)
		self.ensure_connectivity(chasm=True)
	
		# make start point
		choices = [t for t in self.level.iter_tiles() if t.can_walk]
		if choices:
			self.level.start_pos = self.random.choice(choices)
		if not choices:
			self.level.make_floor(0, 0,)
			self.level.start_pos = Point(0, 0)

		
		# Find points to put stuff
		self.empty_spawn_points = []
		self.wall_spawn_points = []
		for i in range(LEVEL_SIZE):
			for j in range(LEVEL_SIZE):
				cur_point = Point(i, j)
				if self.difficulty == 1:
					if distance(cur_point, self.level.start_pos) < 8:
						continue

				if self.level.can_walk(i, j):
					self.empty_spawn_points.append(cur_point)
				else:
					if len([p for p in self.level.get_adjacent_points(cur_point)]) > 1:
						self.wall_spawn_points.append(cur_point)

		self.random.shuffle(self.empty_spawn_points)
		self.random.shuffle(self.wall_spawn_points)
		
	def tidy_border(self):
		# Count walls and edges on edge.
		# Make all edge floor tiles into most common type.
		walls = 0
		chasms = 0
		level = self.level
		for i in range(0, LEVEL_SIZE):
			
			tiles = [level.tiles[i][0], level.tiles[0][i],
					 level.tiles[i][LEVEL_SIZE-1], level.tiles[LEVEL_SIZE-1][i]]

			for tile in tiles:
				if tile.is_wall():
					walls += 1
				if tile.is_chasm:
					chasms += 1

		for i in range(0, LEVEL_SIZE):
			
			tiles = [level.tiles[i][0], level.tiles[0][i],
					 level.tiles[i][LEVEL_SIZE-1], level.tiles[LEVEL_SIZE-1][i]]

			for tile in tiles:
				if not tile.is_floor():
					continue
				if walls < chasms:
					level.make_chasm(tile.x, tile.y)
				else:
					level.make_wall(tile.x, tile.y)


	def populate_level(self):

		for i in range(self.num_exits):
			if self.wall_spawn_points:
				exit_loc = self.wall_spawn_points.pop()
			else:
				exit_loc = self.empty_spawn_points.pop()
			exit = Portal(self.make_child_generator())
			self.level.make_floor(exit_loc.x, exit_loc.y)
			self.level.add_prop(exit, exit_loc.x, exit_loc.y)

		for i in range(self.num_monsters):
			spawner, cost = self.random.choice(self.spawn_options)

			spawn_point = self.empty_spawn_points.pop()

			obj = spawner()

			unit = self.level.get_unit_at(*spawn_point)
			if unit:
				print(unit.name)
			self.level.add_obj(obj, spawn_point.x, spawn_point.y)

		for i in range(self.num_elites):
			spawner = self.elite_spawn

			obj = spawner()
			spawn_point = self.empty_spawn_points.pop()
			self.level.add_obj(obj, spawn_point.x, spawn_point.y)

		for i in range(self.num_generators):
			spawn_point = self.wall_spawn_points.pop()
			self.level.make_floor(spawn_point.x, spawn_point.y)

			spawner, cost = self.random.choice(self.spawn_options)

			obj = MonsterSpawner(spawner)
			obj.max_hp = 19 + cost * 8
			self.level.add_obj(obj, spawn_point.x, spawn_point.y)

		
		for item in self.items:
			p = self.wall_spawn_points.pop()
			self.level.make_floor(p.x, p.y)

			prop = make_consumable_pickup(item)
			self.level.add_prop(prop, p.x, p.y)

		for i in range(self.num_hp_upgrades):
			p = self.empty_spawn_points.pop()
			self.level.add_prop(HeartDot(), p.x, p.y)

		if self.shrine:
			p = self.empty_spawn_points.pop()
			self.level.add_prop(self.shrine, p.x, p.y)

		if self.extra_circle:
			p = self.empty_spawn_points.pop()
			self.level.add_prop(self.extra_circle, p.x, p.y)

		for i in range(self.num_xp):
			
			if not self.empty_spawn_points:
				break

			spawn_point = self.empty_spawn_points.pop()

			pickup = ManaDot()

			self.level.add_prop(pickup, spawn_point.x, spawn_point.y)

		for s in self.scroll_spells:

			if not self.empty_spawn_points:
				break

			spawn_point = self.empty_spawn_points.pop()
			self.level.add_prop(SpellScroll(s), spawn_point.x, spawn_point.y)

		for boss in self.bosses:
			if not self.empty_spawn_points:
				break

			spawn_point = self.empty_spawn_points.pop()
			
			self.level.add_obj(boss, spawn_point.x, spawn_point.y)


def blue_starry_sky(level):
	environment = StarrySkyChasms(level)
	environment.colors = [
			Color(100, 180, 255),
			Color(100, 100, 155),
			Color(50,  150, 255),
			Color(100, 255, 255),
			Color(100, 120, 250)
		]
	environment.star_freq = .00125
	environment.star_lifetime = 400
	environment.star_lifetime_var = 200
	return environment

def red_starry_sky(level):
	environment = StarrySkyChasms(level)
	environment.colors = [
			Color(255,  0,  0),
			Color(200,  0,  0),
			Color(220,  0,  50),
			Color(255, 100, 100),
			Color(220, 50, 0)
		]
	environment.star_freq = .00125
	environment.star_lifetime = 400
	environment.star_lifetime_var = 200
	return environment

def yellow_starry_sky(level):
	environment = StarrySkyChasms(level)
	environment.colors = [
			Color(255, 255, 100),
			Color(255, 255, 0),
			Color(255, 255, 180),
			Color(255, 255, 60),
		]
	environment.star_freq = .00125
	environment.star_lifetime = 400
	environment.star_lifetime_var = 200
	return environment

def galaxy_core_sky(level):
	environment = StarrySkyChasms(level)
	environment.colors = [
			Color(255, 255, 100),
			Color(255, 255, 0),
			Color(255, 255, 50),
			Color(100, 180, 255),
			Color(50,  150, 255),
			Color(100, 255, 255),
			Color(100, 120, 250)
		]
	environment.star_freq = .01125
	environment.star_lifetime = 200
	environment.star_lifetime_var = 600
	return environment

def water_chasms(level):
	environment = LiquidChasms(level)
	return environment

def lava_chasms(level):
	
	environment = LiquidChasms(level)

	environment.wave_color = Color(64, 0, 0)
	environment.bg_min_color = Color(80, 0, 0)
	environment.bg_max_color = Color(150, 0, 0)

	return environment

def roll_environment(level, difficulty):
	environment = self.random.choice([blue_starry_sky, red_starry_sky, yellow_starry_sky])

	if difficulty == LAST_LEVEL:
		environment = galaxy_core_sky
	return environment(level)

# Make a list of all monsters variants ect
all_monsters = []
seen_monster_names = set()
all_monster_names = []

def record(monster):
	if monster.name not in seen_monster_names:
		all_monsters.append(monster)
		seen_monster_names.add(monster.name)

		if monster.has_buff(RespawnAs):
			record(monster.get_buff(RespawnAs).spawner())

def make_bestiary():
	for s, l in spawn_options:
		record(s())

		for v in variants.get(s, []):
			record(v[0]())

	for r in rare_monsters:
		record(r[0]())

	all_monsters.append(Mordred())

	test_level = Level(1, len(all_monsters))
	i = 0
	for m in all_monsters:
		test_level.add_obj(m, 0, i)
		i += 1

	for m in all_monsters:
		all_monster_names.append(m.name)