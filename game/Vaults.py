from Monsters import *
from Variants import *
from RareMonsters import *
import LevelGenHelpers
from Consumables import roll_consumable
from BossSpawns import *

import logging
level_logger = logging.getLogger("Level")
level_logger.setLevel(logging.DEBUG)
level_logger.propagate = False

class LevelMutator():

	def __init__(self, levelgen):
		self.levelgen = levelgen

		self.monster_spawns = []
		self.boss_spawns = []
		self.lair_spawns = []
		
		self.num_monsters = 10
		self.num_bosses = 1
		self.num_lairs = 1

		self.reward_props = [ManaDot()]

		self.on_init()

	def on_init(self, levelgen):
		# Called after initial level randomization happens.
		# Can override spawns, rewards, ect
		# Needed?  Well- wizard tower could maybe use this to eliminate all the *other* stuff in the level
		pass

	def on_terrain(self, levelgen):
		# Called after initial terraingen happens.
		# Can totally nuke terrain, or just add a little vault area.
		pass

		# Between on_terrain and on_spawn, levelgen does standard stuff like ensuring connectivity and making sure the level isnt boring
		#  (Disable boredom check for vaulted levels?)

	def on_spawn(self, levelgen):
		# Called before anything is spawned.
		# Use to add custom rewards, monsters, bosses, ect
		pass

	def do_spawns(self, floor_spawns, wall_spawns):
		# Default method for spawning monsters lairs and bosses

		# spawn bosses
		for i in range(random.randint(1, 2)):
			if not floor_spawns:
				break
			boss = random.choice(self.boss_spawns)()
			tile = floor_spawns.pop()
			self.levelgen.level.add_obj(boss, tile.x, tile.y)

		# spawn rewards
		for p in self.reward_props:
			if not floor_spawns:
				break
			spawn_point = floor_spawns.pop()
			self.levelgen.level.add_obj(p, spawn_point.x, spawn_point.y)

		# spawn lairs
		for i in range(4):
			if not wall_spawns:
				break
			spawn = random.choice(self.lair_spawns)
			lair = MonsterSpawner(spawn)
			spawn_point = wall_spawns.pop()
			self.levelgen.level.make_floor(spawn_point.x, spawn_point.y)
			self.levelgen.level.add_obj(lair, spawn_point.x, spawn_point.y)

		# spawn normals
		for i in range(self.num_monsters):
			if not floor_spawns:
				break
			tile = floor_spawns.pop()
			monster = random.choice(self.monster_spawns)()
			self.levelgen.level.add_obj(monster, tile.x, tile.y)

class HillFort(LevelMutator):

	def on_init(self):
		self.num_monsters = 999
		self.num_bosses = random.randint(1, 3)
		self.num_lairs = random.randint(2, 5)
		self.reward_props = [ItemPickup(roll_consumable(self.levelgen.random)) for i in range(2)]

	def on_terrain(self):
		# Make a big rect of stone, and punch out a grid.
		self.sublevel = self.levelgen.level.get_random_sublevel(self.levelgen.random)
		level_logger.debug("Vault placed at (%d, %d, %d, %d)" % (self.sublevel.xstart, self.sublevel.ystart, self.sublevel.width, self.sublevel.height))
		
		# Make a solid block of wall, surronded by chasm moat, with a grid of empty spaces that will eventually be connected (via connectivity ensurence) into a mazelike thing
		
		self.sublevel.fill_walls()
		LevelGenHelpers.grid(self.sublevel, stagger=2, chance=1)

		for tile in self.sublevel.iter_tiles():
			if tile.is_chasm:
				self.sublevel.make_floor(tile.x, tile.y)

		LevelGenHelpers.border(self.sublevel, force_wall=True, size=2, force_rect=True)
		LevelGenHelpers.border(self.sublevel, force_chasm=True, size=1, force_rect=True)

		self.sublevel.set_tileset('orc fortress')

		self.monster_spawns = [Goblin, Kobold, Orc]
		self.lair_spawns = self.monster_spawns
		self.boss_spawns = [
			lambda : apply_modifier(EliteWarrior, Orc),
			lambda : apply_modifier(King, Orc),
			lambda : apply_modifier(King, Kobold),
			lambda : apply_modifier(EliteWarrior, Kobold),
			lambda : apply_modifier(Metallic, Orc),
		]

	def on_spawn(self):

		floor_spawns, wall_spawns = self.sublevel.get_spawn_points()
		self.do_spawns(floor_spawns, wall_spawns)


# Then we could also make higher level variants of the fort via inheritance and overriding monster lists and maybe tileset

class FaeGarden(LevelMutator):

	def on_init(self):
		self.monster_spawns = [EvilFairy, Gnome, Troubler]
		self.num_monsters = 15
		self.lair_spawns = self.monster_spawns
		self.num_lairs = random.randint(0, 2)
		self.boss_spawns = [Thornface]
		self.num_bosses = 1

	def on_terrain(self):
		size = 100
		self.tiles = [self.levelgen.level.tiles[p.x][p.y] for p in self.levelgen.level.get_random_lump(size, self.levelgen.random)]
		for t in self.tiles:
			if random.random() > .6:
				self.levelgen.level.make_wall(t.x, t.y)
				t.tileset = "green mushroom"
			else:
				self.levelgen.level.make_floor(t.x, t.y)
			


	def on_spawn(self):
		floor_spawns = [t for t in self.tiles if t.is_floor()]
		wall_spawns = [t for t in self.tiles if t.is_wall()]
		self.do_spawns(floor_spawns, wall_spawns)

# Levelgen modifier fn, min level, max level
vault_table = [
	(HillFort, 5, 25),
	(FaeGarden, 5, 25),
]


def roll_vault(difficulty):
	#TEMP DEBUG
	#return FaeGarden
	return None
	
	novault_chance = .75

	if difficulty > 15:
		novault_chance = .5

	novault_chance = 0

	if random.random() < novault_chance:
		return None
	else:
		candidates = [l for (l, mn, mx) in vault_table if mn <= difficulty <= mx]
		if not candidates:
			return None
		return random.choice(candidates)

	# TODO- cmd line arg to force special level


	# TODO - generate a level with each vault to ensure it doesnt crash
