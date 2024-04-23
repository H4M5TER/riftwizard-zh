from Level import *
from Monsters import *
from Spells import *
from Consumables import *
from Equipment import *
from Shrines import *
from RareMonsters import *
from Variants import roll_variant
from Equipment import roll_equipment
import random
from collections import namedtuple
from BossSpawns import *
from LevelGenHelpers import *
from Vaults import roll_vault, vault_table
from FinalBosses import *

LEVEL_SIZE = 33

def set_level_size(new_size):
	global LEVEL_SIZE
	LEVEL_SIZE = new_size

USE_VARIANTS = True

import sys

import logging
level_logger = logging.getLogger("Level")
level_logger.setLevel(logging.DEBUG)
level_logger.propagate = False
level_logger.addHandler(logging.FileHandler('level_log.txt', mode='w'))

class Biome():

	def __init__(self, tileset, tags=None, waters=None, stars=None, limit_walls=False, needs_chasms=False, min_level=0):
		self.tileset = tileset
		self.tags = tags
		self.waters = waters if waters is not None else default_water_table
		self.stars = stars
		self.limit_walls = limit_walls
		self.needs_chasms = needs_chasms
		self.min_level = min_level

	def can_spawn(self, levelgen):
		if levelgen.difficulty < self.min_level:
			return False

		# If the biome has tag reqs, insist that the primary spawn has those tags
		if self.tags:
			if not any(t for t in self.tags if t in levelgen.primary_spawn().tags):
				return False

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
	Biome('brown crater', tags=[Tags.Living], limit_walls=True),
	Biome('castle gray'),
	Biome('city gray'),
	#Biome('dragon fire', tags=[Tags.Fire]),
	#Biome('dragon ice', tags=[Tags.Ice]),
	Biome('flesh purple', tags=[Tags.Undead]),
	Biome('lab purple', tags=[Tags.Arcane, Tags.Dark]),
	Biome('library brown')
]

def random_point(levelgen):
	return Point(levelgen.random.randint(0, LEVEL_SIZE - 1), levelgen.random.randint(0, LEVEL_SIZE - 1))

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

class LevelGenerator():

	def __init__(self, difficulty, game=None, seed=None, corrupted=False):
		
		self.difficulty = difficulty


		self.next_level_seeds = None			
		self.random = random.Random()

		if seed:
			level_logger.debug("Seeding levelgen with %f" % seed)
			self.random = random.Random(seed)
			if game:
				self.next_level_seeds = game.get_seeds(difficulty)
				self.random.shuffle(self.next_level_seeds)
		

		self.num_xp = 2

		if difficulty >= 5:
			self.num_xp = 3

		if difficulty >= 10:
			self.num_xp = 4

		if difficulty >= 15:
			self.num_xp = 5

		self.level_id = self.random.randint(0, 1000000)

		self.num_start_points = self.random.choice([5, 8, 10, 15, 20, 30, 40, 50, 60, 75])
		self.reconnect_chance = self.random.choice([0, 0, .2, .2, .5, .5])
		self.game = game
		self.num_open_spaces = self.random.choice([0, 0, 0, 2, 3, 5, 7, 12])
		self.num_exits = 3

		self.primary_spawn, self.secondary_spawn = self.get_spawns()

		if difficulty <= 3:
			self.biome = all_biomes[0]
		else:
			choices = [b for b in all_biomes if b.can_spawn(self)]
			self.biome = self.random.choice([b for b in all_biomes if b.can_spawn(self)])

		self.corrupted = corrupted
		self.corrupted_tiles = []


		if difficulty < 5:
			self.num_monsters = self.random.randint(6, 12)
		else:
			self.num_monsters = self.random.randint(12, 20)

		max_generators = 3 if difficulty < 5 else 5 if difficulty < 10 else 7 if difficulty < 20 else 9
		min_generators = 3 if difficulty < 10 else 4 if difficulty < 20 else 5
		self.num_generators = 2 if difficulty == 2 else self.random.randint(min_generators, max_generators)

		self.shrine = None
		if self.game:
			self.shrine = None if difficulty in [1, LAST_LEVEL] else roll_shrine(self.difficulty, self.random, self.game.p1)

		num_consumables = self.random.choice([0, 0, 0, 1, 1, 1, 2, 2, 2])
		if self.difficulty == 1:
			num_consumables = 0

		self.bosses = []

		# Add extras non spawned high level monsters
		if self.difficulty >= 2:
			self.add_elites()

		# As we go up in diff, add more stuff to the board
		# Add difficulty modifiers
		num_challenge_mods = 0 if difficulty <= 4 else 1 if difficulty < 8 else 2
		for i in range(num_challenge_mods):
			self.add_challenge_mod()

		if difficulty >= 14:
			self.add_super_challenge()

		if difficulty >= 19:
			self.add_super_challenge()

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
			self.num_scrolls = 0

		if difficulty == LAST_LEVEL - 2:
			self.num_exits = 2

		if difficulty == LAST_LEVEL - 1:
			self.bosses.append(roll_final_boss())
			self.num_exits = 1 # We will generate one later

		if difficulty == LAST_LEVEL:
			self.bosses = [Mordred()]
			self.num_libraries = 0
			self.num_shrines = 0
			self.num_generators = 0
			self.num_exits = 0

		if difficulty == 1 and 'forcerare' in sys.argv:
			self.num_monsters = 0
			self.num_generators = 0

		self.items = []
		for _ in range(num_consumables):
			self.items.append(roll_consumable(prng=self.random))

		if self.difficulty == 2:
			self.items.append(mana_potion())

		# For mouseover- spice up the ordering
		self.random.shuffle(self.items)

		if self.game:
			for m in self.game.mutators:
				m.on_levelgen_pre(self)

		self.description = self.get_description()

	def get_elites(self):
		_, level = get_spawn_min_max(self.difficulty)

		if self.difficulty < 5:
			modifier = 1
		else:
			modifier = self.random.choice([1, 1, 1, 1, 2, 2])

		level = min(level + modifier, 9)

		if modifier == 1:
			num_elites = self.random.choice([7, 8, 9])
		if modifier == 2:
			num_elites = self.random.choice([4, 5, 6])
		if modifier == 3:
			num_elites = self.random.choice([2, 3])

		if self.difficulty == 1:
			num_elites = self.random.choice([3, 4])

		options = [(s, l) for s, l in spawn_options if l == level]
		spawner = self.random.choice(options)[0]

		units = [spawner() for i in range(num_elites)] 
		return units

	def add_variant(self):
		spawner = self.get_spawns()[1]

		if 'forcespawn' in sys.argv:
			forcedspawn_name = sys.argv[sys.argv.index('forcespawn') + 1]
			forced_spawn_options = [(spawn, cost) for (spawn, cost) in spawn_options if forcedspawn_name.lower() in spawn.__name__.lower()]
			assert(len(forced_spawn_options) > 0)
			spawner = random.choice(forced_spawn_options)[0]
		
		self.bosses.extend(roll_bosses(self.difficulty, spawner))

	def add_boss(self):
		spawns = roll_rare_spawn(self.difficulty, prng=self.random)
		self.bosses.extend(spawns)

	def add_elites(self):
		elites = self.get_elites()
		self.bosses.extend(elites)

	def add_challenge_mod(self):
		challenges = [self.add_boss, self.add_variant]
		random.choice(challenges)()

	def add_boss_wizard(self):
		wizard = random.choice(all_wizards)[0]()
		boss_mod = random.choice(modifiers)[0]
		apply_modifier(boss_mod, wizard, apply_hp_bonus=True)
		self.bosses.append(wizard)

	def add_boss_spawner(self):
		monster, _ = self.get_spawns(-1)
		
		boss_mod = random.choice(modifiers)[0]
		spawn_fn = lambda: BossSpawns.apply_modifier(boss_mod, monster(), apply_hp_bonus=True)
		
		spawner = MonsterSpawner(spawn_fn)
		spawner.max_hp = 200

		self.bosses.append(spawner)

	def add_giant_monster(self):
		monster = random.choice(big_monsters)()
		self.bosses.append(monster)

	def add_super_challenge(self):
		challenges = [self.add_boss_wizard, self.add_boss_spawner, self.add_giant_monster]
		random.choice(challenges)()

	def get_spawns(self, level_mod=0):
		min_level, max_level = get_spawn_min_max(self.difficulty)

		primary = random.choice([m for m, l, in spawn_options if l == max_level])

		if 'forcespawn' in sys.argv:
			forcedspawn_name = sys.argv[sys.argv.index('forcespawn') + 1]
			forced_spawn_options = [(spawn, cost) for (spawn, cost) in spawn_options if forcedspawn_name.lower() in spawn.__name__.lower()]
			assert(len(forced_spawn_options) > 0)
			primary = random.choice(forced_spawn_options)[0]

		if self.difficulty > 2:
			secondary = random.choice([m for m, l in spawn_options if l == min_level])
		else:
			secondary = None

		return primary, secondary

	def get_spawn_options(self, difficulty, num_spawns=None, tags=None):
		if tags:
			tags = set(tags)



		min_level, max_level = get_spawn_min_max(difficulty)
		if not num_spawns:
			num_spawns = self.random.choice([1, 2, 2, 2, 3, 3, 3])

		choices = spawn_options
		if tags:
			choices = [(s, l) for s, l in spawn_options if tags.intersection(s().tags)]

		spawns = []
		# force 1 higher level spawn
		max_level_options = [(s, l) for s, l in choices if (l == max_level) or (l == max_level - 1)]
		spawns.append(self.random.choice(max_level_options))

		# generate the rest randomly
		other_spawn_options = [(s, l) for s, l, in choices if l >= min_level and l <= max_level and (s, l) not in spawns]
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

	def make_level(self, check_terrain=True):

		level_logger.debug("\nGenerating level for %d" % self.difficulty)
		level_logger.debug("Level id: %d" % self.level_id)
		level_logger.debug("num start points: %d" % self.num_start_points)
		level_logger.debug("reconnect chance: %.2f" % self.reconnect_chance)
		level_logger.debug("num open spaces: %d" % self.num_open_spaces)


		self.level = Level(LEVEL_SIZE, LEVEL_SIZE)


		self.level.set_tileset(self.biome.tileset)

		can_accept_terrain = False
		attempt = 0
		if check_terrain:
			while (not can_accept_terrain and attempt < 15):
				self.make_terrain()
				can_accept_terrain = self.check_terrain()
				attempt += 1
				if attempt >= 15:
					self.log_level()
					raise Exception("Failed 15 times to generate an acceptable level")
		else:
			self.make_terrain()

		level_logger.debug("Level generated in %d tries" % attempt)

		level_logger.debug("Final layout:")
		self.log_level()

		self.populate_level()

		self.level.gen_params = self
		self.level.calc_glyphs()

		# Always start with blue water so people understand what a chasm is
		if self.difficulty == 1:
			self.level.water = WATER_BLUE

		# Game looks better without water
		self.level.water = None

		if self.game:
			for m in self.game.mutators:
				m.on_levelgen(self)
				


		return self.level

	def log_level(self):
		level_logger.debug('---')
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

		level_logger.debug('---')

	def get_standable_tiles(self, radius=1, flying=False):
		# Return the list of tiles that a n x n monster could stand on
		test_unit = Unit()
		test_unit.radius = radius
		test_unit.can_fly = flying

		results = []

		for t in self.level.iter_tiles():
			if self.level.can_stand(t.x, t.y, test_unit):
				results.append(t)

		return results

	def expand_to_radius(self, radius, flying=False):
		# Put a pathable tile next to each pathable tile so monsters of
		#  the given radius can traverse the level
		
		standable = set(Point(t.x, t.y) for t in self.get_standable_tiles(radius=radius, flying=flying))

		to_enlarge = []
		for i in range(radius, LEVEL_SIZE - radius):
			for j in range(radius, LEVEL_SIZE - radius):

				# Dont enlarge tiles that can already be stood on, no point in doing this
				if Point(i, j) in standable:
					continue

				t = self.level.tiles[i][j]
				if flying:
					if t.can_see:
						to_enlarge.append(t)
				else:
					if t.can_walk:
						to_enlarge.append(t)

		for t in to_enlarge:
			for i in range(-radius, radius+1):
				for j in range(-radius, radius+1):
					cur_point = Point(t.x + i, t.y + j)
					if flying:
						cur_tile = self.level.tiles[cur_point.x][cur_point.y]
						
						# Dont mess with existing floors for the sake of big fliers
						if cur_tile.can_walk:
							continue
						# Otherwise, expand floors into floors, expand chasms into chasms
						elif t.can_walk:
							self.level.make_floor(cur_point.x, cur_point.y)	
						else:
							self.level.make_chasm(cur_point.x, cur_point.y)
					else:
						self.level.make_floor(cur_point.x, cur_point.y)

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

				for p in self.level.get_points_in_ball(cur.x, cur.y, 1, diag=False):
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

			for p in self.level.get_points_in_line(best_inner, best_outer, no_diag=True):
				make_path(p.x, p.y)

	def corrupt(self):
		subgen = LevelGenerator(difficulty=self.difficulty, corrupted=False)
		
		# No shrine on new level ofc
		subgen.shrine = None

		subgen.make_level()

		chance = .5
		# List of tiles to corrupt- white noise for now
		self.corrupted_tiles = []


		cor_type = random.choice([2, 5])

		# White Noise
		if cor_type == 1:
			for i in range(LEVEL_SIZE):
				for j in range(LEVEL_SIZE):
					if random.random() > chance:
						self.corrupted_tiles.append((i, j))

		# Border
		elif cor_type == 2:
			border_width = random.randint(2, 6)
			self.corrupted_tiles = [(t.x, t.y) for t in self.level.iter_tiles() if not is_in_rect(t.x, t.y, border_width, subgen.level)]

		# Circle
		elif cor_type == 3:
			border_width = random.randint(0, 5)
			self.corrupted_tiles = [(t.x, t.y) for t in self.level.iter_tiles() if not is_in_circle(t.x, t.y, border_width, subgen.level)]

		# Diamond
		elif cor_type == 4:
			border_width = random.randint(2, 6)
			self.corrupted_tiles = [(t.x, t.y) for t in self.level.iter_tiles() if not is_in_diamond(t.x, t.y, border_width, subgen.level)]		

		# Lump
		elif cor_type == 5:
			lump_size = random.randint(50, 500)
			self.corrupted_tiles.extend(self.level.get_random_lump(lump_size, self.random))


		# todo- 2 rounds of white noise on the edges?

		for x, y in self.corrupted_tiles:
			t = subgen.level.tiles[x][y]

			# Copy tile type
			if t.is_wall():
				self.level.make_wall(x, y)
			elif t.is_floor():
				self.level.make_floor(x, y)
			elif t.is_chasm:
				self.level.make_chasm(x, y)
			# Copy tile tileset
			self.level.tiles[x][y].tileset = t.tileset

			# Copy unit
			if t.unit and not t.unit.radius:
				unit = t.unit
				subgen.level.remove_obj(unit)
				self.level.add_obj(unit, t.x, t.y)

	# Check that terrain has enough walls and floors
	def check_terrain(self):
		min_floors = 50
		min_walls = 120
		num_floors = len([t for t in self.level.iter_tiles() if t.can_walk])
		num_walls = len([t for t in self.level.iter_tiles() if not t.can_walk])
		return (num_floors > min_floors) and (num_walls > min_walls)


	def make_terrain(self):

		brush_shift_chance = 0
		if self.difficulty > 5:
			brush_shift_chance = .05
		if self.difficulty > 10:
			brush_shift_chance = .1
		if self.difficulty > 15:
			brush_shift_chance = .15
		if self.difficulty > 20:
			brush_shift_chance = .35

		chasm = self.random.choice([True, False])
		level_logger.debug("Filling with %s" % 'chams' if chasm else 'walls')
		for x in range(LEVEL_SIZE):
			for y in range(LEVEL_SIZE):
				if not chasm:
					self.level.make_wall(x, y)
				else:
					self.level.make_chasm(x, y)

		if self.difficulty > 1:
			num_seeds = self.random.randint(1, 3)
			level_logger.debug("Seed mutators:")
			for i in range(num_seeds):
				mutator = self.random.choice(seed_mutators)
				mutator(self)

				if random.random() < brush_shift_chance:
					new_tileset = random.choice(all_biomes).tileset
					self.level.set_brush_tileset(new_tileset)

			# Mutate
			level_logger.debug("Extra mutators:")
			num_mutators = self.random.choice([0, 0, 1, 3, 4, ])

			for i in range(num_mutators):
				mutator = self.random.choice(mutator_table)
				mutator(self)

				if random.random() < brush_shift_chance:
					new_tileset = random.choice(all_biomes).tileset
					self.level.set_brush_tileset(new_tileset)

		else:
			paths(self)
			lumps(self, num_lumps=5, space_size=140)

		# Generally end with paths- otherwise you end up with frequent bottlenecks
		#if self.random.random() < .8:
		#	points = self.random.randint(2, 10)
		#	paths(self, num_points=points)

		self.tidy_border()

		# Ensure atleast 20 walls and 20 floors
		fix_attempts = 10
		min_floors = 50
		min_walls = 150
		for i in range(fix_attempts):
			num_floors = len([t for t in self.level.iter_tiles() if t.can_walk])
			num_walls = len([t for t in self.level.iter_tiles() if not t.can_walk])
			level_logger.debug("%d floors, %d walls)" % (num_floors, num_walls))
			self.log_level()

			if min_floors > num_floors or min_walls > num_walls:
				level_logger.debug("Trying to fix boring level:")
				mutator = self.random.choice(seed_mutators)
				mutator(self)
				if random.random() < brush_shift_chance:
					new_tileset = random.choice(all_biomes).tileset
					self.level.set_brush_tileset(new_tileset)
				self.log_level()
			else:
				break

		self.level.set_brush_tileset(None)

		max_fly_radius = 0
		for b in self.bosses:
			if b.stationary:
				continue
			if not b.flying:
				continue
			max_fly_radius = max(max_fly_radius, b.radius)

		max_walk_radius = 0
		for b in self.bosses:
			if b.stationary:
				continue
			if b.flying:
				continue
			max_walk_radius = max(max_walk_radius, b.radius)

		# Ensure connectivity
		self.ensure_connectivity(chasm=False)
		self.ensure_connectivity(chasm=True)

		# Make sure the level is navigable for big monsters
		if max_fly_radius:
			level_logger.debug("Expanding flyable corridors to %d" % max_walk_radius)
			self.expand_to_radius(max_fly_radius, flying=True)
			self.log_level()
		elif max_walk_radius:
			level_logger.debug("Expanding walkable corridors to %d" % max_walk_radius)
			self.expand_to_radius(max_walk_radius, flying=False)
			self.log_level()

		# Uniformize floors and chasms
		floor_tiles = [t for t in self.level.iter_tiles() if t.is_floor()]
		if floor_tiles:
			first = floor_tiles[0]
			for t in floor_tiles:
				t.tileset = first.tileset
		
		chasm_tiles = [t for t in self.level.iter_tiles() if t.is_chasm]
		if chasm_tiles:
			first = chasm_tiles[0]
			for t in chasm_tiles:
				t.tileset = first.tileset

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
				if walls < chasms:
					level.make_chasm(tile.x, tile.y)
				else:
					level.make_wall(tile.x, tile.y)


	def populate_level(self):

		# Find points to put stuff
		self.empty_spawn_points = []
		self.wall_spawn_points = []
		for i in range(LEVEL_SIZE):
			for j in range(LEVEL_SIZE):
				cur_point = Point(i, j)

				if cur_point in self.corrupted_tiles:
					continue

				if self.level.get_unit_at(i, j):
					continue

				if self.level.can_walk(i, j):
					self.empty_spawn_points.append(cur_point)
				else:
					if len([p for p in self.level.get_adjacent_points(cur_point)]) > 1:
						self.wall_spawn_points.append(cur_point)

		self.random.shuffle(self.empty_spawn_points)
		self.random.shuffle(self.wall_spawn_points)

		self.level.start_pos = self.empty_spawn_points.pop()

		for i in range(self.num_exits):
			exit_loc = self.wall_spawn_points.pop()
			exit = Portal(self.make_child_generator())
			self.level.make_floor(exit_loc.x, exit_loc.y)
			self.level.add_prop(exit, exit_loc.x, exit_loc.y)

		sorted_bosses = sorted(self.bosses, key=lambda boss: boss.radius, reverse=True)
		for boss in sorted_bosses:
			if not self.empty_spawn_points:
				break

			possible_spawn_points = self.empty_spawn_points

			# Do extra checks for multitile monsters
			if boss.radius:

				min_bound = boss.radius
				max_bound = LEVEL_SIZE - 1 - boss.radius

				possible_spawn_points = [p for p in self.empty_spawn_points if p.x >= min_bound and p.x <= max_bound and p.y >= min_bound and p.y <= max_bound]
				possible_spawn_points = [p for p in possible_spawn_points if all(self.level.get_unit_at(q.x, q.y) is None for q in self.level.get_points_in_ball(p.x, p.y, boss.radius, diag=True))]

			assert(possible_spawn_points)
			spawn_point = random.choice(possible_spawn_points)

			self.empty_spawn_points.remove(spawn_point)
			self.level.add_obj(boss, spawn_point.x, spawn_point.y)

			if boss.radius:
				for p in boss.iter_occupied_points():

					if p == spawn_point:
						continue

					self.level.make_floor(p.x, p.y)
					if p in self.empty_spawn_points:
						self.empty_spawn_points.remove(p)
					if p in self.wall_spawn_points:
						self.wall_spawn_points.remove(p)

		for item in self.items:
			p = self.empty_spawn_points.pop()
			
			self.level.make_floor(p.x, p.y)

			prop = ItemPickup(item)
			self.level.add_prop(prop, p.x, p.y)

		if self.shrine:
			p = self.empty_spawn_points.pop()
			self.level.add_prop(self.shrine, p.x, p.y)

		for i in range(self.num_xp):
			
			if not self.empty_spawn_points:
				break

			spawn_point = self.empty_spawn_points.pop()

			pickup = ManaDot()

			self.level.add_prop(pickup, spawn_point.x, spawn_point.y)

		for i in range(self.num_generators):
			if not self.empty_spawn_points and not self.wall_spawn_points:
				break

			if self.wall_spawn_points:
				spawn_point = self.wall_spawn_points.pop()
			else:
				spawn_point = self.empty_spawn_points.pop()

			self.level.make_floor(spawn_point.x, spawn_point.y)

			if self.secondary_spawn:
				spawner = self.random.choice([self.primary_spawn, self.secondary_spawn])
			else:
				spawner = self.primary_spawn

			obj = MonsterSpawner(spawner)
			self.level.add_obj(obj, spawn_point.x, spawn_point.y)

		for i in range(self.num_monsters):
			if not self.empty_spawn_points:
				break

			if self.secondary_spawn:
				spawner = self.random.choice([self.primary_spawn, self.secondary_spawn])
			else:
				spawner = self.primary_spawn
			spawn_point = self.empty_spawn_points.pop()

			obj = spawner()
 
			self.level.add_obj(obj, spawn_point.x, spawn_point.y)


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

	for r in rare_monsters:
		record(r[0]())


	all_monsters.append(Apep())
	all_monsters.append(Ophan())
	all_monsters.append(FrogPope())
	all_monsters.append(ApocalypseBeatle())

	all_monsters.append(Mordred())

	test_level = Level(5, len(all_monsters)*5)
	i = 0
	for m in all_monsters:
		test_level.add_obj(m, 1, i)
		i += 5

	for m in all_monsters:
		all_monster_names.append(m.name)


if __name__ == "__main__":
	for i in range(1000):
		print('Generating level %d' % i)
		gen = LevelGenerator(difficulty=random.randint(1, 21))
		test_boss = Unit()
		test_boss.radius = 1
		test_boss.flying = True

		test_boss2 = Unit()
		test_boss2.radius = 1
		test_boss2.flying = False

		gen.make_level()