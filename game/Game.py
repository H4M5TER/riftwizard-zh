from Level import *
from LevelGen import *
import sys
import math
import Consumables
import os
from Spells import make_player_spells

from collections import OrderedDict, defaultdict

import dill as pickle
import random

BUILD_NUM = 3

def safe_int(f):
	if f.isdigit():
		return int(f)
	return 0

def can_continue_game():
	# Can continue if latest run has a game dat
	if os.path.exists('saves'):
		run_folders = os.listdir('saves')
		run_folders.sort(reverse=True, key=lambda f: safe_int(f))
		if run_folders:
			filename = os.path.join('saves', run_folders[0], 'game.dat')
			return os.path.exists(filename)
	return False

def continue_game(filename=None):
	if filename and os.path.exists(filename):
		with open(filename, 'rb') as savefile:
			game = pickle.load(savefile)
			
			if getattr(game, 'build_compat_num', 0) != BUILD_NUM:
				raise Exception("Error: Incompatible save file.")
			game.on_loaded(filename)

			return game

	# Return latest game dat
	if os.path.exists('saves'):
		run_folders = os.listdir('saves')
		run_folders.sort(reverse=True, key=lambda f: safe_int(f))
		if run_folders:
			filename = os.path.join('saves', run_folders[0], 'game.dat')
			with open(filename, 'rb') as savefile:
				game = pickle.load(savefile)

			# Setup up logging (and other systems that needs to be reset on load)
			game.on_loaded(filename)
			if getattr(game, 'build_compat_num', 0) != BUILD_NUM:
				raise Exception("Error: Incompatible save file.")
			return game

def abort_game():
	if os.path.exists('saves'):
		run_folders = os.listdir('saves')
		run_folders.sort(reverse=True, key=lambda f: safe_int(f))
		if run_folders:
			filename = os.path.join('saves', run_folders[0], 'game.dat')
			if os.path.exists(filename):
				os.remove(filename)

class Game():
#	cur_game = None

	def save_game(self, filename=None):
		main_save = False
		if not filename:
			main_save = True
			filename = os.path.join('saves', str(self.run_number), 'game.dat.tmp')

		dirname = os.path.dirname(filename)
		if not os.path.exists(dirname):
			os.makedirs(dirname)

		with open(filename, 'wb') as save:
			pickle.dump(self, file=save)

		# If the save is succesful, overwrite the main save file
		# Do this to avoid corrupting save files when pickle crashes
		# Ideally pickle would not crash but this way atleast we retain a usable save file and can try to repro the bug
		if main_save:
			main_filename = os.path.join('saves', str(self.run_number), 'game.dat')
			
			if os.path.exists(main_filename):
				os.remove(main_filename)
			
			os.rename(filename, main_filename)

	def write_stats(self):

		filename = os.path.join('saves', str(self.run_number), 'level.%d.txt')

		dirname = os.path.dirname(filename)
		if not os.path.exists(dirname):
			os.makedirs(dirname)

		with open(filename, 'wb') as save:
			pickle.dump(self, file=save)

	def get_run_number(self):
		if os.path.exists('saves'):
			run_folders = os.listdir('saves')
			if run_folders:
				return max(safe_int(f) for f in run_folders) + 1
			else:
				return 1
		else:
			os.mkdir('saves')
			return 1

	def on_loaded(self, filename):		
		# Infer logdir and run number from filename
		self.logdir = os.path.join(os.path.dirname(filename), 'log')
		if not os.path.exists(self.logdir):
			os.mkdir(self.logdir)
		
		self.run_number = safe_int(os.path.split(os.path.dirname(filename))[1])

		self.cur_level.setup_logging(logdir=self.logdir, level_num=self.level_num)

	def finalize_save(self, victory):

		# Finalize current level first
		self.finalize_level(victory)

		filename = os.path.join('saves', str(self.run_number), 'game.dat')
		if os.path.exists(filename):
			os.remove(filename)


	def finalize_level(self, victory):
		filename = os.path.join('saves', str(self.run_number), 'stats.level_%d.txt' % self.level_num)
		self.total_turns += self.cur_level.turn_no

		dirname = os.path.dirname(filename)
		if not os.path.exists(dirname):
			os.makedirs(dirname)

		with open(filename, 'w') as stats:
			stats.write("Realm %d\n" % self.level_num)
			if self.trial_name:
				stats.write(self.trial_name + "\n")
			stats.write("Outcome: %s\n" % ("VICTORY" if victory else "DEFEAT"))
			stats.write("\nTurns taken:\n")
			stats.write("%d (L)\n" % self.cur_level.turn_no)
			stats.write("%d (G)\n" % self.total_turns)

			counts = sorted(self.cur_level.spell_counts.items(), key=lambda t: -t[1])

			spell_counts = [(s, c) for (s, c) in counts if not s.item]
			if spell_counts:
				stats.write("\nSpell Casts:\n")
				for s, c in spell_counts:
					stats.write("%s: %d\n" % (s.name, c))

			dealers = sorted(self.cur_level.damage_dealt_sources.items(), key=lambda t: -t[1])
			if dealers:
				stats.write("\nDamage to Enemies:\n")
				for s, d in dealers[:5]:
					stats.write("%d %s\n" % (d, s))
				if len(dealers) > 6:
					total_other = sum(d for s,d in dealers[5:])
					stats.write("%d Other\n" % total_other)

			sources = sorted(self.cur_level.damage_taken_sources.items(), key=lambda t: -t[1])
			if sources:
				stats.write("\nDamage to Wizard:\n")				
				for s, d in sources[:5]:
					stats.write("%d %s\n" % (d, s))
				if len(sources) > 6:
					total_other = sum(d for s,d in sources[5:])
					stats.write("%d Other\n" % total_other)

			item_counts = [(s, c) for (s, c) in counts if s.item]
			if item_counts:
				stats.write("\nItems Used:\n")
				for s, c in item_counts:
					stats.write("%s: %d\n" % (s.name, c))

			if self.recent_upgrades:
				stats.write("\nPurchases:\n")
				for u in self.recent_upgrades:
					fmt = u.name
					if getattr(u, 'prereq', None):
						fmt = "%s %s" % (u.prereq.name, u.name)
					stats.write("%s\n" % fmt)

			self.recent_upgrades.clear()

	# For the consumer of the Game object
	def __init__(self, generate_level=True, save_enabled=False, mutators=None, trial_name=None, seed=None):

		self.build_compat_num = BUILD_NUM
		self.seed = seed
		if self.seed:
			random.seed(self.seed)
		else:
			random.seed()


		self.level_seeds = {}
		for i in range(26):
			seeds_per_difficulty = 12
			self.level_seeds[i] = [random.random() for i in range(seeds_per_difficulty)]

		self.mutators = mutators
		if not self.mutators:
			self.mutators = []

		for mutator in self.mutators:
			mutator.set_seed(random.random())

		self.trial_name = trial_name

		self.p1 = self.make_player_character()

		self.run_number = self.get_run_number()

		self.generate_level = generate_level
		if generate_level:
			self.cur_level = LevelGenerator(1, self, self.seed).make_level()
		else:
			self.cur_level = Level(32, 32)
			self.cur_level.start_pos = Point(0, 0)

		self.cur_level.spawn_player(self.p1)

		self.gameover = False
		self.level_num = 1

		self.deploying = False
		self.next_level = None
		self.prev_next_level = None

		self.victory = False

		self.has_granted_xp = False

		self.victory_evt = False

		self.recent_upgrades = []

		self.total_turns = 0

		self.all_player_spells = make_player_spells()
		self.all_player_skills = make_player_skills()

		for mutator in self.mutators:
			mutator.on_generate_spells(self.all_player_spells)
			mutator.on_generate_skills(self.all_player_skills)
			mutator.on_game_begin(self)

		# Gather all spell tags for UI and other consumers
		self.spell_tags = []
		self.spell_tags.extend(t for t in Tags if any(t in s.tags for s in self.all_player_spells))
		self.spell_tags.extend(t for t in Tags if any(t in s.tags for s in self.all_player_skills) if t not in self.spell_tags)

		self.subscribe_mutators()

		if save_enabled:
			self.save_game()
			self.logdir = os.path.join('saves', str(self.run_number), 'log')
			os.mkdir(self.logdir)
		else:
			self.logdir = None

		self.cur_level.setup_logging(logdir=self.logdir, level_num=self.level_num)

	# Take a levelseed, return the list of seeds that level leads to
	def get_seeds(self, difficuty):
		# Just return ranndom seeds for levels above 25
		if difficuty > 25:
			return [random.random() for i in range(10)]
		return list(self.level_seeds[difficuty])

	def subscribe_mutators(self):
		for mutator in self.mutators:
			for event_type, handler in mutator.global_triggers.items():
				self.cur_level.event_manager.register_global_trigger(event_type, handler)

	def make_player_character(self):
		# eventually tie in char creation here
		player = Unit()
		player.max_hp = 50
		player.cur_hp = 50
		player.sprite.char = chr(1)
		player.sprite.color = Color(128, 255, 0)
		player.is_player_controlled = True
		player.mana = 250
		player.name = "Player"
		player.team = TEAM_PLAYER

		player.tags = [Tags.Living]

		player.xp = 1
		player.discount_tag = None
		player.scroll_discounts = {}

		# player only fields
		player.knowledges = OrderedDict()
		for knowledge in Knowledges:
			player.knowledges[knowledge] = 0
		player.num_knowledges = 0
		player.num_upgrades = 0
		player.num_spells = 0

		player.add_item(Consumables.heal_potion())
		player.add_item(Consumables.mana_potion())
		player.add_item(Consumables.teleporter())
		player.add_item(Consumables.portal_disruptor())

		player.gets_clarity = True

		return player

	# Request to move the currently active controlled unit in the requested direction
	def try_move(self, xdir, ydir):
		if not self.cur_level.is_awaiting_input:
			return False
		
		new_x = self.p1.x + xdir
		new_y = self.p1.y + ydir

		if self.cur_level.can_move(self.p1, new_x, new_y):
			self.cur_level.set_order_move(new_x, new_y)
			#self.advance()
			return True

	# Request to cast a spell
	def try_cast(self, spell, x, y):
		if spell.can_cast(x, y):
			self.cur_level.set_order_cast(spell, x, y)
			return True
		else:
			return False

	def can_shop(self, item):
		if self.cur_level.cur_shop:

			if isinstance(item, Upgrade) and self.has_upgrade(item):
				return False

			if self.cur_level.cur_shop.can_shop(self.p1, item):
				return True
			return False

		elif isinstance(item, Upgrade) or isinstance(item, Spell):
			if self.can_buy_upgrade(item):
				return True
			return False

		return False

	def try_shop(self, item):
		if not self.can_shop(item):
			return False

		if self.cur_level.cur_shop:
			self.cur_level.act_shop(self.p1, item)

		elif isinstance(item, Upgrade) or isinstance(item, Spell):
			self.buy_upgrade(item)

		if item:
			self.recent_upgrades.append(item)

		return True


	def try_pass(self):
		self.cur_level.set_order_pass()

	def has_upgrade(self, upgrade):
		# Spells you can have only one of
		if any(s.name == upgrade.name for s in self.p1.spells):
			return True

		# General upgrades (non spell upgrades) are like spells
		if any(s.name == upgrade.name for s in self.p1.get_skills()):
			return True

		# Shrine upgrades are infinitely stackable
		if getattr(upgrade, 'shrine_name', None):
			return False

		# Non shrine upgrades- check name, prereq pair
		if any(isinstance(b, Upgrade) and b.name == upgrade.name and b.prereq == upgrade.prereq and not b.shrine_name for b in self.p1.buffs):
			return True
		return False

	def get_upgrade_cost(self, upgrade):
		level = upgrade.level
		if level == 0:
			return 0
			
		if self.p1.discount_tag in upgrade.tags:
			level = level - 1
		
		level -= self.p1.scroll_discounts.get(upgrade.name, 0)
		level = max(level, 1)
		return level		

	def buy_upgrade(self, upgrade):
		self.p1.xp -= self.get_upgrade_cost(upgrade)
		if isinstance(upgrade, Upgrade):
			self.p1.apply_buff(upgrade)
		elif isinstance(upgrade, Spell):
			self.p1.add_spell(upgrade)

	def get_upgrade_distance(self, upgrade):
		
		# To buy an upgrade of level n you need n-1 upgrades sharing tags
		level_needed = upgrade.level - 1
		level_posessed = 0
		for spell in self.p1.spells:
			if any((tag in upgrade.tags) for tag in spell.tags):
				level_posessed += 1
		for buff in self.p1.buffs:
			if not isinstance(buff, Upgrade):
				continue
			if any((tag in upgrade.tags) for tag in buff.tags):
				level_posessed += 1
		return max(0, level_needed - level_posessed)

	def can_buy_upgrade(self, upgrade):

		# Limit 20 spells
		if isinstance(upgrade, Spell) and len(self.p1.spells) >= 20:
			return False

		if self.has_upgrade(upgrade):
			return False

		if isinstance(upgrade, Upgrade) and upgrade.prereq:
			if not self.has_upgrade(upgrade.prereq):
				return False

		if self.p1.xp < self.get_upgrade_cost(upgrade):
			return False

		if hasattr(upgrade, 'exc_class') and upgrade.exc_class:
			# Non shrine upgrades- check name, prereq pair
			if any(isinstance(b, Upgrade) and getattr(b, 'exc_class', None) == upgrade.exc_class and b.prereq == upgrade.prereq for b in self.p1.buffs):
				return False

		#if self.get_upgrade_distance(upgrade) > 0:
		#	return False

		return True

	# Request to advance the simulation- update anims, move enemies, ect.
	def advance(self):
		self.changed_level = False
		if "profile" in sys.argv:
			import time
			import cProfile
			import pstats
			pr = cProfile.Profile()

			start = time.time()
			
			pr.enable()

		advanced = self.cur_level.advance()
		if not self.cur_level.active_spells:
			self.check_triggers()
		
		if "profile" in sys.argv:
			pr.disable()

			finish = time.time()
			frame_time = finish - start

			if frame_time > 1 / 60.0:
				stats = pstats.Stats(pr)
				stats.sort_stats("cumtime")
				stats.dump_stats("profile.stats")
				stats.print_stats()
		
			print("frame time ms: %f" % (frame_time * 1000))

	# Check if we should respond to something that happened in the current level
	def check_triggers(self):
		if self.cur_level.cur_portal and not self.deploying:
			self.enter_portal()
		
		if all([u.team == TEAM_PLAYER for u in self.cur_level.units]):
				
			if not self.has_granted_xp:
				#self.p1.xp += 3
				self.has_granted_xp = True
				self.victory_evt = True
				self.finalize_level(victory=True)

		if self.p1.cur_hp <= 0:
			self.gameover = True
			self.finalize_save(victory=False)

		if self.level_num == LAST_LEVEL and not any(u.name == "Mordred" for u in self.cur_level.units):
			self.victory = True
			self.victory_evt = True
			self.finalize_save(victory=True)

	def is_awaiting_input(self):

		if self.victory:
			return True

		if self.next_level:
			return True
		
		return self.cur_level.is_awaiting_input

	# Internal stuff
	def enter_portal(self):
		
		if self.generate_level:
			if not self.cur_level.cur_portal.next_level:
				self.cur_level.cur_portal.next_level = self.cur_level.cur_portal.level_gen_params.make_level()
			self.next_level = self.cur_level.cur_portal.next_level

		else:
			self.next_level = Level(32, 32)

		self.deploying = True

	def try_deploy(self, x, y):
		assert(self.deploying)

		if not self.next_level.can_stand(x, y, self.p1):
			return False

		self.p1.Anim = None

		self.cur_level.remove_obj(self.p1)

		self.next_level.start_pos = Point(x, y)
		self.next_level.spawn_player(self.p1)
		self.cur_level = self.next_level
		self.next_level = None
		self.deploying = False

		self.level_num += 1
		self.has_granted_xp = False
		
		self.cur_level.setup_logging(logdir=self.logdir, level_num=self.level_num)

		import gc
		gc.collect()

		self.subscribe_mutators()
		self.save_game()

		if self.cur_level.gen_params:
			logging.getLogger("Level").debug("\nEntering level %d, id=%d" % (self.level_num, self.cur_level.gen_params.level_id))

		return True

	def try_abort_deploy(self):
		self.deploying = False
		self.prev_next_level = self.next_level
		self.next_level = None
		self.cur_level.cur_portal = None

	def can_fast_forward(self):
		return self.cur_level.can_fast_forward()

#def new_game():
#	Game.cur_game = Game()
#	return Game.cur_game

# todo- load_game, ect