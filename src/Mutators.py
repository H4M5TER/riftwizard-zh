import math
import random
import sys
import datetime
import RareMonsters
from Level import *
from CommonContent import *
from Monsters import *
from LevelGen import *

class Mutator(object):

	def __init__(self, mutseed=0):
		self.global_triggers = {}
		self.random = None

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

class StackLimit(Mutator):

	def __init__(self, stack_max):
		Mutator.__init__(self)
		self.stack_max = stack_max
		self.description = "A maximum of %d of each consumable can be held at any one time" % stack_max

	def on_game_begin(self, game):
		game.p1.stack_max = self.stack_max

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

	def __init__(self, mult=2):
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

class RandomSkillRestriction(Mutator):

	def __init__(self, chance=.5):
		Mutator.__init__(self)		
		self.chance = chance
		self.description = "A random %d%% of the skillbook is removed" % (self.chance*100)

	def on_generate_skills(self, skills):
		
		starters = [s for s in skills if s.level < 2]

		num_removed = math.ceil(self.chance * len(skills))
		removals = list(skills)
		self.random.shuffle(removals)
		removals = removals[:num_removed]
		for s in removals:
			skills.remove(s)

class RandomSpellRestriction(Mutator):

	def __init__(self, chance=.5):
		Mutator.__init__(self)		
		self.chance = chance
		self.description = "A random %d%% of the spellbook is removed" % (self.chance*100)

	def on_generate_spells(self, spells):
		
		starters = [s for s in spells if s.level < 2]

		num_removed = math.ceil(self.chance * len(spells))
		removals = list(spells)
		self.random.shuffle(removals)
		removals = removals[:num_removed]
		for s in removals:
			spells.remove(s)

		# Ensure that atleast 1 level 1 spell is present
		if not any(s in spells for s in starters):
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


class OnlySpell(Mutator):

	def __init__(self, spellname):
		Mutator.__init__(self)
		self.spellname = spellname
		self.description = "The only available spell is %s" % self.spellname

	def on_generate_spells(self, spells):
		allowed = [s for s in spells if s.name == self.spellname]
		assert(len(allowed) == 1)
		spells.clear()
		spells.append(allowed[0])


class NoSkills(Mutator):

	def __init__(self):
		Mutator.__init__(self)
		self.description = "Passive skills are unavailable"

	def on_generate_skills(self, skills):
		skills.clear()


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
			unit = levelgen.get_elites(levelgen.difficulty)[0]
			levelgen.bosses.append(unit)

class SpellChargeMultiplier(Mutator):

	def __init__(self, mult):
		Mutator.__init__(self)
		self.mult = mult
		self.description = "Each spell has %d%% max charges" % (self.mult * 100)

	def on_generate_spells(self, spells):
		for s in spells:
			s.max_charges = math.ceil(s.max_charges * self.mult)
			s.cur_charges = s.max_charges

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

all_trials = [Trial(n, m) for n, m in [
	("Limited Spellbook", [RandomSpellRestriction(.85)]),
	("Improviser", [RandomSpellRestriction(.85), RandomSkillRestriction(.7)]),
	("Menagerie", [ExtraElites(6)]),
	("Trollpath", [NumPortals(1), EnemyBuff(TrollRegenBuff)]),
	("Sorcerer Ascetic", [SpellChargeMultiplier(.5), SpellTagRestriction(Tags.Sorcery)]),
	("Thrifty Wizard", [StackLimit(1), RandomSpellRestriction(.9)]),
	("Wizard Warlords", [SpawnWizards(), LairMultiplier(2)]),
	("Humble Horde", [SpPerLevel(2), SpellTagRestriction(Tags.Conjuration)]),
	("Giantslayer", [MonsterHPMult(3)]),
	("Danger Brigade", [EnemyBuff(lambda: DamageAuraBuff(1, Tags.Poison, 4)), EnemyShields(2)]),
	("Flamefest", [MonsterHPMult(2), SpellTagRestriction(Tags.Fire)]),
	("Wolfer", OnlySpell("Wolf")),
	("Vampire Hunter", [EnemyBuff(lambda: RespawnAs(VampireBat), exclude_named="Vampire Bat"), SpellTagRestriction(Tags.Holy)]),
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

weekly_mods = [
	ExtraElites(5),
	ExtraElites(10),
	NumPortals(1),
	NumPortals(2),
	StackLimit(1),
	SpawnWizards(),
	MonsterHPMult(2),
	EnemyBuff(lambda: RespawnAs(VampireBat), exclude_named="Vampire Bat"),
	EnemyBuff(lambda: RespawnAs(GreenSlime), exclude_named="Green Slime"),
	EnemyBuff(lambda: RespawnAs(Troubler), exclude_named="Troubler"),
	EnemyBuff(lambda: RespawnAs(Gnome), exclude_named="Gnome"),
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
	#EnemyBuff(ReincarnationBuff),
	EnemyShields(1),
	EnemyShields(2)
]




def get_weekly_mutators():

	seed = get_weekly_seed()

	r = random.Random()
	r.seed(seed)

	spell_restriction_roll = r.random()
	restriction_pct = r.choice([.5, .6, .7, .8, .8, .9, .9, .95])
	# 40% chance: random spells
	# 20% chance: random spell tag
	# 20% chance: random spells and skills
	# 20% chance: no restrictions

	modifiers = []

	num_extras = r.choice([1, 1, 1, 1, 1, 2, 2, 3])
	if spell_restriction_roll < .4:
		modifiers.append(RandomSpellRestriction(restriction_pct))
	elif spell_restriction_roll < .6:
		modifiers.append(RandomSpellRestriction(restriction_pct))
		modifiers.append(RandomSkillRestriction(restriction_pct))
	elif spell_restriction_roll < .8:
		tag = r.choice([Tags.Fire, Tags.Ice, Tags.Dark, Tags.Holy, Tags.Nature, Tags.Lightning, Tags.Sorcery, Tags.Conjuration, Tags.Enchantment])
		modifiers.append(SpellTagRestriction(tag))
	else:
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
