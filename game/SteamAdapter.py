import steamworks
import dill as pickle
import os

import logging
stats_log = None
stats_log = logging.getLogger("Stats")
stats_log.setLevel(logging.DEBUG)
stats_log.propagate = False
stats_log_handler = logging.FileHandler('stats_log.txt', mode='a')
stats_log_formatter = logging.Formatter('%(asctime)s: %(message)s')
stats_log_handler.setFormatter(stats_log_formatter)
stats_log.addHandler(stats_log_handler)

from LevelGen import all_monster_names

import Mutators

default_vals = {
	'w': 0,
	'r': 0,
	's': 0,
	'l': 0,
	'steam_contact': False, # Has steam ever been contacted for stats
	'trials': set(), # Set of strings of names of finished trials
	'bestiary': set(), # Set of strings of defeated monster names
	'purchases': set(), # Set of strings of spells and skills ever purchased
	'victories': set(), # Set of strings of spells and skills ever won with
}


_sw = None
def try_get_sw():
	global _sw

	# If sw was succesfully initialized before, just return it
	if _sw:
		return _sw

	# Else try to initialize it
	try:
		initialized_sw = steamworks.STEAMWORKS()
		initialized_sw.initialize()
		initialized_sw.RequestCurrentStats()
		_sw = initialized_sw
		stats_log.debug("Steamworks initialized and connect")
	except:
		stats_log.debug("Steamworks failed to initialize or connect")
		pass

def init():

	# Try loading stats pickle
	global stats
	if os.path.exists('stats.dat'):
		with open('stats.dat', 'rb') as stats_file:
			stats = pickle.load(stats_file)
	else:
		stats = {}

	for k, v in default_vals.items():
		if k not in stats:
			stats[k] = v

	# Try to init sw
	try_get_sw()

	# do not log this as with the bestiary it is now massive
	#stats_log.debug("Stats: %s" % stats)


def get_stat(stat):
	# Disable for now
	# Try to init sw- updating stats dict if needed
	try_get_sw()
	stats_log.debug("Fetching %s, result %s" % (stat, stats[stat]))
	return stats[stat]
	
def set_stat(stat, val):
	stats_log.debug("Setting %s to %s" % (stat, val))
	stats[stat] = val

	with open('stats.dat', 'wb') as stats_file:
		pickle.dump(stats, file=stats_file)

	s = try_get_sw()
	if s:
		s.SetStatInt(stat.encode('ascii'), val)
		s.StoreStats()

def set_presence_menu():
	s = try_get_sw()
	if s:
		s.SetGameInfo('steam_display'.encode('ascii'), '#Status_AtMainMenu'.encode('ascii'))

def set_presence_level(level):
	s = try_get_sw()
	if s:		
		s.SetGameInfo('level'.encode('ascii'), str(level).encode('ascii'))
		s.SetGameInfo('steam_display'.encode('ascii'), '#Status_Level'.encode('ascii'))

def get_trial_status(trial_name):
	result = trial_name in stats["trials"]
	#print("%s: %s" % (trial_name, result))
	return result

def set_trial_complete(trial_name):
	stats_log.debug("Setting complete %s" % trial_name)
	stats["trials"].add(trial_name)

	with open('stats.dat', 'wb') as stats_file:
		pickle.dump(stats, file=stats_file)
	
	s = try_get_sw()
	if s:
		if trial_name.startswith("weekly"):
			trial_name = "WEEKLY"
		s.SetAchievement(trial_name.upper().replace(' ', '_').encode('ascii'))

		# Check ARCHMAGE ach (all trials completed)
		if all(t.name in stats["trials"] for t in Mutators.all_trials):
			name = "ARCHMAGE"
			s.SetAchievement(name.encode('ascii'))



def record_level_turns(num_turns):
	s = try_get_sw()
	if not s:
		return

	name = "INSTANT_WIN"
	if num_turns <= 1:
		s.SetAchievement(name.encode('ascii'))

def record_damage_dealt(damage):
	s = try_get_sw()
	if not s:
		return
	
	name = "BIG_DAMAGE_TURN"
	if damage > 15000:
		s.SetAchievement(name.encode('ascii'))

def record_total_turns(num_turns):

	s = try_get_sw()
	if not s:
		return

	pairs = [(1000, "BRISK_GAME"),
			 (500, "FAST_GAME"),
			 (250, "TURBO_GAME")
			]


	for (t, name) in pairs:
		if num_turns < t:
			s.SetAchievement(name.encode('ascii'))

def record_purchase(spell_name):
	if spell_name not in stats["purchases"]:
		stats["purchases"].add(spell_name)
		
		with open('stats.dat', 'wb') as stats_file:
			pickle.dump(stats, file=stats_file)

def has_been_purchased(spell_name):
	return spell_name in stats["purchases"]

def record_victory(spell_name):
	if spell_name not in stats["victories"]:
		stats["victories"].add(spell_name)
		
		with open('stats.dat', 'wb') as stats_file:
			pickle.dump(stats, file=stats_file)

def has_been_victoried(spell_name):
	return spell_name in stats["victories"]

def unlock_bestiary(monster_name):
	if monster_name not in stats["bestiary"]:
		stats["bestiary"].add(monster_name)

		with open('stats.dat', 'wb') as stats_file:
			pickle.dump(stats, file=stats_file)
	
		check_bestiary_ach()

def check_bestiary_ach():
	s = try_get_sw()
	if not s:
		return

	if get_num_slain() >= len(all_monster_names):
		name = "BESTIARY"
		s.SetAchievement(name.encode('ascii'))

def has_slain(monster_name):
	return monster_name in stats["bestiary"]

def get_num_slain():
	return len([m for m in stats["bestiary"] if m in all_monster_names])

init()