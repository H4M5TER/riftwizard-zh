import math
import random
import sys
import datetime
import RareMonsters
import BossSpawns

from Level import *
from CommonContent import *
from Monsters import *
from LevelGen import *
from Equipment import *


class Mutator(object):

	def __init__(self, mutseed=0):
		self.global_triggers = {}
		self.random = None
		self.name = self.__class__.__name__

	def set_seed(self, seed):
		self.random = random.Random()
		self.random.seed(seed)

	def on_levelgen(self, levelgen):
		pass

	def on_levelgen_pre(self, levelgen):
		pass

	def on_generate_spells(self, spells):
		pass

	def on_generate_skills(self, skills):
		pass

	def on_game_begin(self, game):
		pass

class EveryXTurnsBuff(Buff):

	def __init__(self, mutator, interval):
		Buff.__init__(self)
		self.interval = interval
		self.mutator = mutator
		self.turn_counter = 0

	def on_init(self):
		self.name = "EveryXTurnsBuff"
		self.buff_type = BUFF_TYPE_NONE

	def on_advance(self):
		if self.owner.game.has_granted_xp:
			return  # Don't trigger effects if the level is already won

		if self.owner.level.turn_no % self.interval == 0:
			self.mutator.do_effect(self.owner.level)

class EveryXTurnsMutator(Mutator):

	def __init__(self, interval):
		Mutator.__init__(self)
		self.interval = interval

	def on_game_begin(self, game):
		game.p1.apply_buff(EveryXTurnsBuff(self, self.interval))

	def do_effect(self, level):
		pass


class Forgetful(EveryXTurnsMutator):

	def __init__(self, interval):
		EveryXTurnsMutator.__init__(self, interval)
		self.description = "Lose a charge from a random spell every %d turns" % interval

	def do_effect(self, level):
		player = level.player_unit
		if not player:
			return
		candidates = [s for s in player.spells if s.cur_charges > 0]
		if not candidates:
			return  # Nothing to lose

		spell = random.choice(candidates)
		spell.cur_charges = max(0, spell.cur_charges - 1)
		level.combat_log.debug("[Wizard] lost a charge from %s due to mutator." % spell.name)

class Awestruck(EveryXTurnsMutator):

	def __init__(self, interval):
		EveryXTurnsMutator.__init__(self, interval)
		self.description = "Get Stunned for one turn every %d turns" % interval

	def do_effect(self, level):
		player = level.player_unit
		level.combat_log.debug("[Wizard] stunned for 1 turn due to mutator.")
		player.apply_buff(Stun(), 1)

class Treachery(EveryXTurnsMutator):

	def __init__(self, interval):
		EveryXTurnsMutator.__init__(self, interval)
		self.description = "A random ally joins the enemy team every %d turns" % interval

	def do_effect(self, level):
		player = level.player_unit
		units = list(level.units)
		random.shuffle(units)
		u = next((u for u in units if u.team == player.team and not u==player), None)
		if u:
			u.team = TEAM_ENEMY
			level.combat_log.debug("[%s:ally] joined the enemy team due to mutator." % u.name)

class Thieving(EveryXTurnsMutator):

	def __init__(self, interval):
		EveryXTurnsMutator.__init__(self, interval)
		self.description = "A random object is removed from the level every %d turns" % interval

	def do_effect(self, level):
		if not level.props:
			return
		prop = random.choice(level.props)
		level.remove_prop(prop)
		level.combat_log.debug("Object removed from level due to mutator.")

class Crumbling(EveryXTurnsMutator):

	def __init__(self, interval):
		EveryXTurnsMutator.__init__(self, interval)
		self.description = "Unoccupied floor and wall tiles adjacent to chasms have a 10%% chance to become chasms every %d turns" % interval

	def do_effect(self, level):
		to_crumble = set()
		seen = set()
		for tile in level.iter_tiles():
			if not tile.is_chasm:
				continue
			for t in level.get_tiles_in_ball(tile.x, tile.y, 1.5):
				if t.unit:
					continue
				if t.prop:
					continue
				if t not in seen and (t.is_floor() or t.is_wall()) :
					seen.add(t)
					if random.random() < .1:
						to_crumble.add(t)

		for t in to_crumble:
			level.show_effect(t.x, t.y, Tags.Physical, minor=True)
			level.make_chasm(t.x, t.y)
			level.combat_log.debug("Chasm created due to mutator.")

class StackLimit(Mutator):

	def __init__(self, stack_max):
		Mutator.__init__(self)
		self.stack_max = stack_max
		self.description = "A maximum of %d of each consumable can be held at any one time" % stack_max

	def on_game_begin(self, game):
		game.p1.stack_max = self.stack_max

class EmptyPockets(Mutator):

	def __init__(self):
		Mutator.__init__(self)
		self.description = "No consumables"

	def on_game_begin(self, game):
		game.p1.items = []

	def on_levelgen_pre(self, levelgen):
		levelgen.items = []

class LairMultiplier(Mutator):
	
	def __init__(self, mult):
		Mutator.__init__(self)
		self.mult = mult
		self.description = "Levels contain %dx Monster Spawners" % self.mult

	def on_levelgen_pre(self, levelgen):
		levelgen.num_generators *= self.mult

class NumPortals(Mutator):

	def __init__(self, num):
		Mutator.__init__(self)
		self.num = num
		self.description = "All levels contain %d rifts" % self.num

	def on_levelgen_pre(self, levelgen):
		levelgen.num_exits = self.num


class MonsterHPMult(Mutator):

	def __init__(self, mult):
		Mutator.__init__(self)
		self.mult = mult
		self.description = "All enemy units have %d%% HP" % (self.mult*100)
		self.global_triggers[EventOnUnitPreAdded] = self.on_enemy_added

	def on_enemy_added(self, evt):
		if not evt.unit.ever_spawned:
			self.modify_unit(evt.unit)

	def on_levelgen(self, levelgen):
		for u in levelgen.level.units:
			self.modify_unit(u)

	def modify_unit(self, unit):
		if unit.is_lair:
			return
		if unit.team == TEAM_PLAYER:
			return
		# Do not buff the HP of splitting units
		if isinstance(unit.source, SplittingBuff):
			return
		unit.max_hp *= self.mult
		unit.cur_hp *= self.mult

class SuperSpawners(Mutator):

	def __init__(self, cdr):
		Mutator.__init__(self)
		self.cdr = cdr
		self.description = "Enemy Spawner health multiplied by 2 and spell cool downs decreased by %d" % (self.cdr)
		self.global_triggers[EventOnUnitPreAdded] = self.on_enemy_added

	def on_enemy_added(self, evt):
		if not evt.unit.ever_spawned:
			self.modify_unit(evt.unit)

	def on_levelgen(self, levelgen):
		for u in levelgen.level.units:
			self.modify_unit(u)

	def modify_unit(self, unit):
		if unit.team == TEAM_PLAYER:
			return
		if not unit.is_lair:
			return
		unit.max_hp *= 2
		unit.cur_hp *= 2
		for s in unit.spells:
			if s.cool_down:
				s.cool_down -= self.cdr

class MoreSpawners(Mutator):

	def __init__(self, val):
		Mutator.__init__(self)
		self.val = val
		self.description = "Levels have %d more spawners in them." % self.val

	def on_levelgen_pre(self, levelgen):
		levelgen.num_generators += self.val


class FewerSpawners(Mutator):

	def __init__(self, val):
		Mutator.__init__(self)
		self.val = val
		self.description = "Levels have %d fewer spawners in them." % self.val

	def on_levelgen_pre(self, levelgen):
		levelgen.num_generators = max(0, levelgen.num_generators -self.val)

class EnemyShields(Mutator):

	def __init__(self, shields):
		Mutator.__init__(self)
		self.shields = shields
		self.description = "All enemy units have %d extra SH" % self.shields
		self.global_triggers[EventOnUnitPreAdded] = self.on_enemy_added

	def on_enemy_added(self, evt):
		self.modify_unit(evt.unit)

	def on_levelgen(self, levelgen):
		for u in levelgen.level.units:
			self.modify_unit(u)

	def modify_unit(self, unit):
		if unit.is_lair:
			return
		if unit.team == TEAM_PLAYER:
			return
		# Do not buff the HP of splitting units
		if isinstance(unit.source, SplittingBuff):
			return
		unit.shields += self.shields

class EnemyBuff(Mutator):

	def __init__(self, buff, exclude_named=None):
		Mutator.__init__(self)
		self.buff = buff
		self.description = "All enemy units have %s" % buff().name
		self.global_triggers[EventOnUnitAdded] = self.on_enemy_added
		self.exclude_named = exclude_named

	def on_enemy_added(self, evt):
		self.modify_unit(evt.unit)

	def on_levelgen(self, levelgen):
		for u in levelgen.level.units:
			self.modify_unit(u)

	def modify_unit(self, unit):
		if unit.team != TEAM_ENEMY:
			return
		if unit.is_lair:
			return
		if unit.name == self.exclude_named:
			return

		buff = self.buff()
		buff.buff_type = BUFF_TYPE_PASSIVE
		unit.apply_buff(buff)

class RespawnAsMutator(Mutator):

	def __init__(self, monster):
		Mutator.__init__(self)
		self.monster = monster # monster constructor
		self.example_monster = self.monster()
		self.description = "All enemy units respawn as %s" % self.example_monster.name
		self.global_triggers[EventOnUnitAdded] = self.on_enemy_added

	def on_enemy_added(self, evt):
		self.modify_unit(evt.unit)

	def on_levelgen(self, levelgen):
		for u in levelgen.level.units:
			self.modify_unit(u)

	def modify_unit(self, unit):
		if unit.team != TEAM_ENEMY:
			return
		if unit.is_lair:
			return
		if unit.name == self.example_monster.name:
			return

		buff = RespawnAs(self.monster)
		buff.buff_type = BUFF_TYPE_PASSIVE
		unit.apply_buff(buff)

class RandomSkillRestriction(Mutator):

	def __init__(self, chance_pct):
		Mutator.__init__(self)		
		self.chance = chance_pct / 100
		self.description = "A random %d%% of the skillbook is removed" % chance_pct

	def on_generate_skills(self, skills):
		num_removed = math.ceil(self.chance * len(skills))
		removals = list(skills)
		self.random.shuffle(removals)
		removals = removals[:num_removed]
		for s in removals:
			skills.remove(s)

class RandomSpellRestriction(Mutator):

	def __init__(self, chance_pct):
		Mutator.__init__(self)		
		self.chance = chance_pct / 100
		self.description = "A random %d%% of the spellbook is removed" % chance_pct

	def on_generate_spells(self, spells):
		
		starters = [s for s in spells if s.level < 2]

		num_removed = math.ceil(self.chance * len(spells))
		removals = list(spells)
		self.random.shuffle(removals)
		removals = removals[:num_removed]
		for s in removals:
			spells.remove(s)

		# Ensure that atleast 1 level 1 spell is present
		if starters and not any(s in spells for s in starters):
			spells.insert(0, self.random.choice(starters))

class SpellTagRestriction(Mutator):

	def __init__(self, tag):
		Mutator.__init__(self)
		self.tag = tag
		self.description = "Only %s spells" % self.tag.name

	def on_generate_spells(self, spells):
		allowed = [s for s in spells if self.tag in s.tags]

		spells.clear()
		spells.extend(allowed)

class SpellLevelRestriction(Mutator):

	def __init__(self, val):
		Mutator.__init__(self)
		self.val = val
		self.description = "Only level %d spells" % self.val

	def on_generate_spells(self, spells):
		allowed = [s for s in spells if s.level == self.val]
		spells.clear()
		spells.extend(allowed)

class SpellTagElimination(Mutator):

	def __init__(self, tag):
		Mutator.__init__(self)
		self.tag = tag
		self.description = "All %s spells removed" % self.tag.name

	def on_generate_spells(self, spells):
		allowed = [s for s in spells if self.tag not in s.tags]
		spells.clear()
		spells.extend(allowed)

class SpellLevelElimination(Mutator):

	def __init__(self, val):
		Mutator.__init__(self)
		self.val = val
		self.description = "All level %d spells removed" % self.val

	def on_generate_spells(self, spells):
		allowed = [s for s in spells if s.level != self.val]
		spells.clear()
		spells.extend(allowed)

class SkillTagElimination(Mutator):

	def __init__(self, tag):
		Mutator.__init__(self)
		self.tag = tag
		self.description = "All %s skills removed" % self.tag.name

	def on_generate_skills(self, skills):
		allowed = [s for s in skills if self.tag not in s.tags]
		skills.clear()
		skills.extend(allowed)

class SkillTagRestriction(Mutator):

	def __init__(self, tag):
		Mutator.__init__(self)
		self.tag = tag
		self.description = "Only %s skills" % self.tag.name

	def on_generate_skills(self, skills):
		allowed = [s for s in skills if self.tag in s.tags]
		skills.clear()
		skills.extend(allowed)

class SkillLevelElimination(Mutator):

	def __init__(self, val):
		Mutator.__init__(self)
		self.val = val
		self.description = "All level %d skills removed" % self.val

	def on_generate_skills(self, skills):
		allowed = [s for s in skills if s.level == self.val]
		skills.clear()
		skills.extend(allowed)

class BonusRerolls(Mutator):

	def __init__(self, val):
		Mutator.__init__(self)
		self.val = val
		self.description = "%d extra rift rerolls on level completion" % self.val
		self.global_triggers[EventOnLevelComplete] = self.on_level_complete
		self.game = None

	def on_level_complete(self, _level):
		self.game.rift_rerolls += self.val

	def on_game_begin(self, game):
		self.game = game

class Amnesiac(Mutator):

	def __init__(self):
		Mutator.__init__(self)
		self.description = ("Your spells, spell upgrades, and skills, are removed and no longer available after you complete a level.\n"
							"Spent SP is refunded")
		self.global_triggers[EventOnLevelComplete] = self.on_level_complete
		self.restricted_spells = []
		self.restricted_skills = []
		self.game = None

	def on_level_complete(self, _level):

		if self.game.p1: # if there's a wizard
			wizard = self.game.p1 # grab wizard unit

			for upgrade in wizard.get_spell_upgrades(): # for each spell upgrade the wizard has
				wizard.xp += upgrade.level # refund
				wizard.remove_buff(upgrade) # unlearn the upgrade

			for spell in wizard.spells: # for each of their spells
				self.restricted_spells.append(spell) # add the spell to the restricted list
				wizard.xp += spell.level # refund
				wizard.remove_spell(spell) # unlearn the spell

			for skill in wizard.get_skills(): # for each skill the wizard has
				self.restricted_skills.append(skill) # add the skill to the restricted list
				wizard.xp += skill.level # refund
				wizard.remove_buff(skill) # unlearn the skill

			self.game.all_player_spells = [spell for spell in self.game.all_player_spells if not spell in self.restricted_spells] # make restricted spells unavailable
			self.game.all_player_skills = [skill for skill in self.game.all_player_skills if not skill in self.restricted_skills] # make restricted skills unavailable

	def on_game_begin(self, game):
		self.game = game # grab the game instance

class MemoryLeak(Mutator):

	def __init__(self):
		Mutator.__init__(self)
		self.description = ("One of your spells is randomly removed and no longer available after you complete a level.\n"
							"Spent SP is refunded")
		self.global_triggers[EventOnLevelComplete] = self.on_level_complete
		self.restricted_spells = []
		self.game = None

	def on_level_complete(self, _level):

		if self.game.p1: # if there's a wizard
			wizard = self.game.p1 # grab wizard unit
			if len(wizard.spells) < 1:
				return
			s = random.choice(wizard.spells)

			for upgrade in wizard.get_spell_upgrades(): # for each spell upgrade the wizard has
				if upgrade.prereq == s:
					wizard.xp += upgrade.level # refund
					wizard.remove_buff(upgrade) # unlearn the upgrade

			self.restricted_spells.append(s) # add the spell to the restricted list
			wizard.xp += s.level # refund
			wizard.remove_spell(s) # unlearn the spell

			self.game.all_player_spells = [spell for spell in self.game.all_player_spells if not spell in self.restricted_spells] # make restricted spells unavailable

	def on_game_begin(self, game):
		self.game = game # grab the game instance

class WildMagic(Mutator):

	def __init__(self):
		Mutator.__init__(self)
		self.description = ("After you complete a level or reroll rifts, your spells and skills are randomly rerolled.\n"
							"Levels have no SP.")
		self.global_triggers[EventOnLevelComplete] = self.on_level_complete
		self.global_triggers[EventOnReroll] = self.on_level_complete # rerolls spells/skills on rift reroll
		self.game = None

	def on_level_complete(self, _evt):
		if not self.game.p1: # if there's no wizard
			return

		wizard = self.game.p1 # grab wizard unit

		for buff in wizard.buffs[:]:
			if buff.buff_type == BUFF_TYPE_PASSIVE: # covers Skills and SpellUpgrades
				wizard.remove_buff(buff)

		wizard.spells.clear() # get rid of spells

		wizard_spell_tags = set() # set up for skill synergy mercy

		spells = all_player_spell_constructors # grab all the spells
		random.shuffle(spells) # shuffle em up

		level_num = self.game.cur_level.level_no
		min_spells = max(3, (level_num * 1) // 3)
		max_spells = min(12, (level_num * 2) // 3)

		if min_spells > max_spells:
			num_spells = 3
		else:
			num_spells = random.randint(min_spells, max_spells) # average is half the level's number of spells

		while len(wizard.spells) < num_spells:
			for spell in spells: # for each one
				new_spell = spell() # instantiate

				if new_spell.hp_cost >= wizard.max_hp: # don't want spells they can't pay for
					continue

				wizard.add_spell(new_spell) # give it to the wizard
				wizard_spell_tags.update(new_spell.tags) # track what tags the wizard has for this level

				if new_spell.spell_upgrades: # if the spell has upgrades
					wizard.apply_buff(random.choice(new_spell.spell_upgrades)) # give it an upgrade

				if len(wizard.spells) >= num_spells: # get out if we have the right number of spells
					break

		wizard.spells.sort(key=lambda s: s.level) # QoL sort spells so lowest level spells at the top

		skills = [s for s in skill_constructors if any(tag in wizard_spell_tags for tag in s().tags)] # only grab skills with tags matching our spells
		random.shuffle(skills) # shuffle em up

		num_skills = random.randint((level_num  // 2), level_num) # average num_skills = level_num * .75
		num_skills += ((level_num // 2) - num_spells) # more or less spells than average grants more or less skills
		num_skills = max(1, num_skills) # don't want negative slicing for early levels giving a boatload of skills

		skills = skills[:num_skills] # only take as many as we want
		for skill in skills: # for each skill
			new_skill = skill() # instantiate it
			wizard.apply_buff(new_skill) # give it to the wizard

	def on_game_begin(self, game):
		self.game = game # grab the game instance
		game.p1.xp = 0
		game.p1.add_spell(self.get_random_cantrip())

	def get_random_cantrip(self):
		cantrips = [s for s in all_player_spell_constructors if s().level == 1]
		return random.choice(cantrips)()

	def on_levelgen_pre(self, levelgen):
		levelgen.num_xp = 0 # no SP

		if levelgen.shrine and levelgen.shrine.name == "Scroll of Spells": # replace spell scrolls since they'd be forgotten anyway
			levelgen.shrine = exotic_pet_chest(levelgen.difficulty, levelgen.random, player=None)
		if levelgen.shrine and levelgen.shrine.name == "Scroll of Skills": # replace skill scrolls since they'd be forgotten anyway
			levelgen.shrine = HeartDot(25)

class SpawnWizards(Mutator):

	def __init__(self):
		Mutator.__init__(self)
		self.description = "Each level beyond the first contains an extra enemy wizard"

	def on_levelgen_pre(self, levelgen):
		if levelgen.difficulty == 1:
			return
		wizard = self.random.choice(RareMonsters.all_wizards)[0]()
		levelgen.bosses.append(wizard)
				
class SpPerLevel(Mutator):

	def __init__(self, num):
		Mutator.__init__(self)
		self.num = num
		if num < 3:
			self.description = "Levels contain only %d SP orbs" % self.num
		else:
			self.description = "Levels contain %d SP orbs" % self.num

	def on_levelgen_pre(self, levelgen):
		levelgen.num_xp = self.num

class SpPenalty(Mutator):

	def __init__(self, num):
		Mutator.__init__(self)
		self.num = num
		self.description = "Levels have %d fewer SP orbs" % num

	def on_levelgen_pre(self, levelgen):
		levelgen.num_xp -= self.num

class SpBonus(Mutator):

	def __init__(self, num):
		Mutator.__init__(self)
		self.num = num
		self.description = "Levels have %d more SP orbs" % num

	def on_levelgen_pre(self, levelgen):
		levelgen.num_xp += self.num

class Trial():

	def __init__(self, name, mutators):
		self.name = name
		if isinstance(mutators, list):
			self.mutators = mutators
		elif isinstance(mutators, Mutator):
			self.mutators = [mutators]
		else:
			assert(False)

	def get_description(self):
		return "\n".join(m.description for m in self.mutators)

class ExtraElites(Mutator):

	def __init__(self, num):
		Mutator.__init__(self)
		self.num = num
		self.description = "Each level has %d extra random high level monsters" % self.num

	def on_levelgen_pre(self, levelgen):
		for i in range(self.num):
			unit = levelgen.get_elites()[0]
			levelgen.bosses.append(unit)

class SpellStatMultiplier(Mutator):

	def __init__(self, stat, mult_pct):
		Mutator.__init__(self)
		self.stat = stat
		self.mult = mult_pct / 100
		self.description = "Spells have %d%% %s" % (mult_pct, self.stat.replace('_', ' '))

	def on_generate_spells(self, spells):
		for s in spells:
			if hasattr(s, self.stat):
				setattr(s, self.stat, math.ceil(getattr(s, self.stat) * self.mult))
				if self.stat == 'max_charges':
					s.cur_charges = s.max_charges

class SpellCooldowns(Mutator):

	def __init__(self, cd):
		Mutator.__init__(self)
		self.cd = cd
		self.description = "The Wizard's spells have a %d turn cool down." % self.cd

	def on_generate_spells(self, spells):
		for s in spells:
			s.cool_down = self.cd

class SpellHPCostAdd(Mutator):

	def __init__(self, cost):
		Mutator.__init__(self)
		self.cost = cost
		self.description = "Each spell has +%d HP cost." % self.cost

	def on_generate_spells(self, spells):
		for s in spells:
			s.hp_cost += self.cost

class Attrition(Mutator):

	def __init__(self, val):
		Mutator.__init__(self)
		self.val = val
		self.description = "At the end of each level, lose %d max HP" % self.val
		self.global_triggers[EventOnLevelComplete] = self.attrition
		self.game = None

	def attrition(self, _):
		self.game.p1.max_hp = max(1, self.game.p1.max_hp - self.val)
		self.game.p1.cur_hp = self.game.p1.max_hp

	def on_game_begin(self, game):
		self.game = game

class Corrupted(Mutator):

	def __init__(self):
		Mutator.__init__(self)
		self.description = "Corrupts the level on completion."
		self.global_triggers[EventOnLevelComplete] = self.on_complete
		self.game = None

	def on_complete(self, _):
		wizard = self.game.p1
		s = OrbCorruption()
		s.owner = wizard
		s.caster = wizard
		wizard.level.act_cast(wizard, s, wizard.x, wizard.y, pay_costs=False)

	def on_game_begin(self, game):
		self.game = game

class ExtraSpawns(Mutator):

	def __init__(self, spawn, num_extra):
		Mutator.__init__(self)
		self.spawn = spawn
		self.num_extra = num_extra
		ex = spawn()
		self.description = "Levels beyond the first contain %d extra %ss" % (self.num_extra, ex.name)

	def on_levelgen(self, levelgen):
		if levelgen.difficulty == 1:
			return

		for i in range(self.num_extra):
			if not levelgen.empty_spawn_points:
				break
			obj = self.spawn()
			spawn_point = levelgen.empty_spawn_points.pop()
			levelgen.level.add_obj(obj, spawn_point.x, spawn_point.y)

class AllwaysExoticPet(Mutator):

	def __init__(self):
		Mutator.__init__(self)
		self.description = "All levels have an exotic pet reward"

	def on_levelgen_pre(self, levelgen):
		levelgen.shrine = exotic_pet_chest(levelgen.difficulty, levelgen.random, player=None)

class OneSpell(Mutator):

	def __init__(self):
		Mutator.__init__(self)
		self.description = "Spells are free, but only one can be purchased"
		self.global_triggers[EventOnLevelComplete] = self.on_complete
		self.chosen = False
		self.game = None

	def on_game_begin(self, game):
		game.max_spells = 1
		game.free_spells = True
		self.game = game

	def on_complete(self, _):
		if self.chosen:
			return
		if self.game.p1: # if there's a wizard
			wizard = self.game.p1 # grab wizard unit
			if not wizard.spells:
				return
			self.game.all_player_spells = wizard.spells # remove the other spells at the end of the first level, assuming they've bought one.
			self.chosen = True

	def on_levelgen_pre(self, levelgen):
		# Replace all spell scrolls with heartdots
		# Spell scrolls are just shops so have to compare name
		if levelgen.shrine and levelgen.shrine.name == "Scroll of Spells":
			levelgen.shrine = HeartDot(25)


class ExtraVariants(Mutator):

	def __init__(self):
		Mutator.__init__(self)
		self.description = "Each level has additional variant boss monsters"

	def on_levelgen_pre(self, levelgen):
		spawn = levelgen.get_spawns()[0]

		if not spawn:
			return

		unit = BossSpawns.roll_bosses(levelgen.difficulty, spawn)
		if not unit:
			return

		levelgen.bosses.extend(unit)

class GiantSlayer(Mutator):

	def __init__(self):
		Mutator.__init__(self)
		self.description = "Each level beyond the 4th has an additional giant monster"

	def on_levelgen_pre(self, levelgen):
		if levelgen.difficulty <= 4:
			return

		unit = random.choice(RareMonsters.big_monsters)()
		print(unit.name)
		levelgen.bosses.append(unit)

class OnlyHearts(Mutator):

	def __init__(self):
		Mutator.__init__(self)
		self.description = "Every level has a Ruby Heart"

	def on_levelgen_pre(self, levelgen):
		levelgen.shrine = HeartDot(25)

class FixedRewards(Mutator):

	def __init__(self, reward):
		Mutator.__init__(self)
		self.description = "Every level reward is a %s" % reward
		self.reward = reward

	def on_levelgen_pre(self, levelgen):
		if levelgen.shrine is None: # don't want to put one on the first level
			return
		reward = reward_opts.get(self.reward)
		if reward:
			levelgen.shrine = reward(levelgen.difficulty, levelgen.random, levelgen.game.p1)
		else:
			levelgen.shrine = None

class RemoveRewards(Mutator):

	def __init__(self, reward):
		Mutator.__init__(self)
		self.description = "Levels will not contain %s rewards" % reward
		self.leader = True
		self.reward = reward
		self.allowed = reward_table.copy()

	def on_levelgen_pre(self, levelgen):
		if not self.leader: # don't rerun shrine generation for every instance
			return
		if levelgen.shrine is None: # don't want to put one on the first level
			return
		if self.allowed: # if there's any possible reward options, roll one
			levelgen.shrine = self.roll_restricted(levelgen.difficulty, levelgen.random, levelgen.game.p1)
		else:
			levelgen.shrine = None

	def on_game_begin(self, game):
		if not self.leader: # just amalgamate all the removed rewards into one mutator for ease of access
			return

		banned = set()
		for m in game.mutators:
			if isinstance(m, RemoveRewards):
				fn = reward_opts.get(m.reward)
				if fn is not None:
					banned.add(fn)

		new_allowed = []
		for option in self.allowed:
			if option[0] not in banned:
				new_allowed.append(option)
		self.allowed = new_allowed

		for m in game.mutators:
			if isinstance(m, RemoveRewards) and m is not self:
				m.leader = False

	def roll_restricted(self, level, prng, player):

		def can_roll(o):
			if len(o) < 3:
				return True
			return o[2] <= level

		opts = [o for o in self.allowed if can_roll(o)]

		if not opts:
			return None

		if not prng:
			prng = random

		return prng.choices([o[0] for o in opts], weights=[o[1] for o in opts])[0](level, prng, player)

reward_opts = {"Chest":roll_chest, "Ruby Heart":hp_shrine, "Exotic Pet":exotic_pet_chest, "Sigil":crown_chest,
			   "Spell Scroll":scroll, "Skill Scroll":skill_scroll, "Miniaturization Shrine":mini_shrine,
			   "Amnesia Shrine":amnesia_shrine, "Duplication Shrine":duplicator_shrine, "None":None}

class BloodRites(Mutator):

	def __init__(self):
		Mutator.__init__(self)
		self.description = ("Each time you cast a spell, increase its HP cost by its spell level.\n"
							"If it doesn't have an HP cost, it gains one.\n"
							"Resets at the end of each level")
		self.global_triggers[EventOnSpellCast] = self.on_cast
		self.global_triggers[EventOnLevelComplete] = self.on_level_complete
		self.game = None

	def on_cast(self, evt):
		if evt.caster.is_player_controlled and hasattr(evt.spell, 'level'):
			evt.spell.hp_cost += evt.spell.level

	def on_level_complete(self, evt):
		for spell in self.game.p1.spells:
			spell.hp_cost = type(spell)().hp_cost

	def on_game_begin(self, game):
		self.game = game

class Flawless(Mutator):

	def __init__(self):
		Mutator.__init__(self)
		self.description = "You have 1 HP."

	def on_levelgen_pre(self, levelgen):
		if levelgen.shrine and levelgen.shrine.name == "Ruby Heart":
			while levelgen.shrine.name == "Ruby Heart":
				levelgen.shrine = roll_shrine(levelgen.difficulty, levelgen.random, levelgen.game.p1)

	def on_game_begin(self, game):
		game.p1.max_hp = 1
		game.p1.cur_hp = 1


def superchest():
	items = [s() for s in (Staves)]
	
	shop = Shop()

	shop.name = "Staff Chest"
	shop.items = items
	shop.asset = ['tiles', 'chest', 'wand_chest']

	return shop

def megachest():
	staves = [s() for s in (Staves)]
	hats = [h() for h in Hats]
	damage_hats = all_damage_hats()
	robes = [r() for r in Robes]
	boots = [b() for b in Boots]
	amulets = [a() for a in Amulets]
	rings = all_rings()

	for category in [staves, hats, damage_hats, robes, boots, amulets, rings]:
		category.sort(key=lambda i: i.name)

	equipment = staves + hats + damage_hats + robes + boots + amulets + rings

	shop = Shop()

	shop.name = "Mega Chest"
	shop.items = equipment
	shop.asset = ['tiles', 'chest', 'chest']

	return shop

class LevelOneSuperChest(Mutator):

	def __init__(self):
		Mutator.__init__(self)
		self.description = "The first level contains a super chest"

	def on_levelgen_pre(self, levelgen):
		if levelgen.difficulty == 1:
			levelgen.shrine = superchest()

class LevelOneMegaChests(Mutator):

	def __init__(self, num_chests):
		Mutator.__init__(self)
		self.num_chests = num_chests
		self.description = "The first level contains %d mega chests, containing every piece of equipment" % num_chests

	def on_levelgen(self, levelgen):
		if levelgen.difficulty == 1:
			for i in range(self.num_chests):
				p = levelgen.empty_spawn_points.pop()
				levelgen.level.add_prop(megachest(), p.x, p.y)

all_trials = [Trial(n, m) for n, m in [
	("Limited Spellbook", [RandomSpellRestriction(80)]),
	("Improviser", [RandomSpellRestriction(75), RandomSkillRestriction(75)]),
	("Pyromancer", SpellTagRestriction(Tags.Fire)),
	("Electromancer", SpellTagRestriction(Tags.Lightning)),
	("Cryomancer", SpellTagRestriction(Tags.Ice)),
	("Necromancer", SpellTagRestriction(Tags.Dark)),
	("Phytomancer", SpellTagRestriction(Tags.Nature)),
	("Manamancer", SpellTagRestriction(Tags.Arcane)),
	("Sanctumancer", SpellTagRestriction(Tags.Holy)),
	("Ferromancer", SpellTagRestriction(Tags.Metallic)),
	("Hemomancer", SpellTagRestriction(Tags.Blood)),
	("Menagerist", AllwaysExoticPet()),
	("Oner", OneSpell()),
	("Mutant Masher", ExtraVariants()),
	("Giant Slayer", GiantSlayer()),
	("Ogre Mage", [RandomSkillRestriction(100), OnlyHearts()]),
	("Staff Abuser", [SpPenalty(1), LevelOneSuperChest()]),
	("Amnesiac", Amnesiac()),
	("Wild Magic", WildMagic()),
	("Blood Rites", BloodRites()),
	("Flawless", Flawless()),
	("Corrupted", Corrupted())
]]

def get_weekly_seed():
	if 'weeklyseed' in sys.argv:
		seed = int(sys.argv[sys.argv.index('weeklyseed') + 1])
	else:
		first_weekly_date = datetime.date(2021, 4, 13)
		cur_date = datetime.date.today()
		days = (cur_date - first_weekly_date).days
		seed = days // 7

	return seed

def get_weekly_name():
	return "weekly_" + str(get_weekly_seed())

weekly_boons = [
	LevelOneMegaChests(1),
	LevelOneMegaChests(2),
	SpellStatMultiplier('damage', 200),
	SpellStatMultiplier('range', 200),
	SpellStatMultiplier('max_charges', 200),
	SpellStatMultiplier('duration', 200),
	SpBonus(1),
	SpBonus(2),
	BonusRerolls(1),
	BonusRerolls(2),
	NumPortals(5),
	FewerSpawners(1)
]

weekly_mods = [
	ExtraElites(5),
	ExtraElites(10),
	NumPortals(1),
	NumPortals(2),
	StackLimit(1),
	SpawnWizards(),
	MoreSpawners(2),
	MonsterHPMult(2),
	ExtraSpawns(Troubler, 6),
	ExtraSpawns(Gnome, 5),
	ExtraSpawns(GreyMushboom, 10),
	ExtraSpawns(VoidDrake, 1),
	ExtraSpawns(Cultist, 8),
	ExtraSpawns(EvilFairy, 4),
	ExtraSpawns(lambda: SlimeCube(GreenSlime), 2),
	EnemyBuff(TeleportyBuff),
	EnemyBuff(lambda: DamageAuraBuff(1, Tags.Poison, 4)),
	EnemyBuff(lambda: DamageAuraBuff(2, Tags.Fire, 2)),
	EnemyBuff(lambda: BloodrageBuff(2)),
	EnemyBuff(lambda: BloodrageBuff(5)),
	EnemyBuff(lambda: BloodrageBuff(10)),
	EnemyBuff(lambda: HealAuraBuff(1, 4)),
	EnemyShields(1),
	EnemyShields(2),
	OneSpell(),
	SpellHPCostAdd(2),
	SpellHPCostAdd(3),
	Attrition(5),
	Attrition(10),
	EnemyBuff(lambda: BurrowingBuff()),
	EnemyBuff(lambda: FlyingBuff()),
	Corrupted(),
	MemoryLeak(),
	EmptyPockets(),
	SuperSpawners(4),
	SpellStatMultiplier('damage', 50),
	SpellStatMultiplier('range', 50),
	SpellStatMultiplier('max_charges', 50),
	SpellStatMultiplier('duration', 50),
	SpellCooldowns(3),
	SpellCooldowns(5),
	Forgetful(3),
	Forgetful(6),
	Awestruck(5),
	Awestruck(10),
	Treachery(10),
	Treachery(15),
	Thieving(30),
	Thieving(20),
	Crumbling(10),
	Crumbling(20)
]

respawn_opts = [
	VampireBat,
	GreenSlime,
	Troubler,
	Gnome,
	FireSpirit,
	MindMaggot,
	SparkImp,
	EvilFairy,
	GhostMass,
	TwoHeadedSnake,
	BlackCat
]

mutator_buff_options = [
	lambda: TeleportyBuff(),
	lambda: BurrowingBuff(),
	lambda: FlyingBuff(),
	lambda: DamageAuraBuff(1, Tags.Poison, 4),
	lambda: DamageAuraBuff(2, Tags.Fire, 2),
	lambda: BloodrageBuff(2),
	lambda: HealAuraBuff(1, 4),
	lambda: TrollRegenBuff()
]

mutator_spawn_options = [m for m, _ in spawn_options]

mutator_param_options = {
	SpellStatMultiplier: ['damage', 'duration', 'max_charges', 'range'],
	SpellTagRestriction: spell_tags,
	SpellTagElimination: spell_tags,
	SkillTagRestriction: spell_tags,
	SkillTagElimination: spell_tags,
	EnemyBuff: mutator_buff_options,
	ExtraSpawns:mutator_spawn_options,
	RespawnAsMutator:mutator_spawn_options,
	FixedRewards: list(reward_opts.keys()),
	RemoveRewards: list(reward_opts.keys())[:-1] # don't include None
}

mutators_with_params = [
	SpellStatMultiplier,
	SpellTagRestriction,
	SpellTagElimination,
	SkillTagElimination,
	SkillTagRestriction,
	EnemyBuff,
	ExtraSpawns,
	FixedRewards,
	RemoveRewards,
	RespawnAsMutator
]

mutators_with_params_and_vals = [
	SpellStatMultiplier,
	ExtraSpawns
]

mutators_with_vals = [
	RandomSpellRestriction,
	RandomSkillRestriction,
	SpellLevelElimination,
	SpellLevelRestriction,
	SkillLevelElimination,
	SpBonus,
	SpPenalty,
	SpPerLevel,
	ExtraElites,
	NumPortals,
	StackLimit,
	MonsterHPMult,
	EnemyShields,
	SpellHPCostAdd,
	Attrition,
	SuperSpawners,
	SpellCooldowns,
	Forgetful,
	Awestruck,
	Treachery,
	Thieving,
	Crumbling,
	LevelOneMegaChests,
	BonusRerolls,
	MoreSpawners,
	FewerSpawners
]

mutators_with_no_args = [
	OneSpell,
	ExtraVariants,
	GiantSlayer,
	EmptyPockets,
	MemoryLeak,
	Amnesiac,
	WildMagic,
	BloodRites,
	Flawless,
	SpawnWizards,
]

all_mutators = sorted(mutators_with_params + mutators_with_vals + mutators_with_no_args, key=lambda cls: cls.__name__)

def get_random_mutators(seed=None, weekly=False):

	r = random.Random()
	
	if weekly:
		seed = get_weekly_seed()
		r.seed(seed)

	spell_restriction_roll = r.random()
	restriction_pct = r.choice([30, 40, 50, 60, 70, 80, 80, 90])
	# 40% chance: random spells
	# 20% chance: random spell tag
	# 20% chance: random spells and skills
	# 20% chance: no restrictions -> more mutators

	modifiers = []

	num_extras = r.choice([1, 1, 2, 2, 2, 2, 2, 3, 4, 5])
	if spell_restriction_roll < .4:
		modifiers.append(RandomSpellRestriction(restriction_pct))
	elif spell_restriction_roll < .6:
		modifiers.append(RandomSpellRestriction(restriction_pct))
		modifiers.append(RandomSkillRestriction(restriction_pct))
	elif spell_restriction_roll < .8:
		tag = r.choice([Tags.Fire, Tags.Ice, Tags.Dark, Tags.Holy, Tags.Nature, Tags.Lightning, Tags.Sorcery, Tags.Conjuration, Tags.Enchantment])
		modifiers.append(SpellTagRestriction(tag))
	else:
		num_extras += 2

	# 15% chance of using one respawn mod (dont use two, it makes the game impossible)
	if r.random() < 0.15:
		opt = r.choice(respawn_opts)
		respawn_mod = EnemyBuff(lambda: RespawnAs(opt), exclude_named=opt().name)
		modifiers.append(respawn_mod)
		num_extras -= 1

	while r.random() < 0.33: # chance to roll boons, which also cause more mutators to be thrown in
		cur_mod = r.choice(weekly_boons)
		modifiers.append(cur_mod)
		num_extras += 1

	for i in range(num_extras):
		cur_mod = r.choice(weekly_mods)
		modifiers.append(cur_mod)
		# seed rng of this mutator

	return modifiers

if __name__ == "__main__":
	print(get_weekly_mutators())


# Assert that all mutators have descrptions
for t in all_trials:
	t.get_description()

for m in weekly_mods:
	assert(m.description)
