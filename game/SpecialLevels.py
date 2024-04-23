from Monsters import *
from Variants import *
from RareMonsters import *
from LevelTools import mutators

class LevelMutator():

	def __init__(self, levelgen):
		self.levelgen = levelgen

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

class HillFort():

	def on_terrain(self):
		# Make a big rect of stone, and punch out a grid.
		self.sublevel = self.levelgen.level.get_random_sublevel()
		
		# Make a solid block of wall, surronded by chasm moat, with a grid of empty spaces that will eventually be connected (via connectivity ensurence) into a mazelike thing
		
		self.sublevel.fill_with_walls()
		mutators.grid(self.sublevel)

		# Maybe make some rooms
		if random.random() < .5:
			mutators.squares()

		mutators.border(self.sublevel, force_walls=True, size=2)
		mutators.border(self.sublevel, force_chasm=True, size=1)


		self.sublevel.set_tileset(TILESET_ORC_FORT)

	def on_spawn(self):

		# totally fill all empty spaces with appropriate monster or spawners
		for tile in self.sublevel.iter_tiles():
			
			if tile.unit or tile.prop:
				continue

			monster = random.choice([Goblin, Kobold, Orc])()
			sublevel.add_obj(monster)


# Levelgen modifier fn, min level, max level
vault_table = [
	(HillFort, 5, 25),
]


def roll_vault(difficulty):
	# temp
	return HillFort()

	# 95% of the time do not make a special level
	if random.random() < .95:
		return None
	else:
		candidates = [l for (l, mn, mx) in vault_table if mn <= difficulty <= mx]
		if not candidates:
			return None
		return random.choice(candidates)()

	# TODO- cmd line arg to force special level