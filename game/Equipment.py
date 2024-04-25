from Level import *
from CommonContent import *
import random
from Variants import *
from Monsters import *
import BossSpawns

import Spells

import sys

# Items per chest.  3?  4?  5?
CHEST_SIZE = 3


class StaffOfLesserTag(Equipment):

	def __init__(self, tag):
		self.tag = tag
		Equipment.__init__(self)

	def on_init(self):
		self.slot = ITEM_SLOT_STAFF
		self.name = '%s Staff' % self.tag.name
		self.tag_bonuses_pct[self.tag]['damage'] = 25
		self.tag_bonuses[self.tag]['max_charges'] = 1
		self.tag_bonuses[self.tag]['range'] = 1

class BladeStaff(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_STAFF
		self.name = "The Bladestaff"
		self.global_bonuses['damage'] = 4

class GeometerStaff(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_STAFF
		self.name = "Geometer's Staff"
		self.global_bonuses['radius'] = 1
		self.global_bonuses['range'] = 1

class ConjurersStaff(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_STAFF
		self.name = "Summoner's Staff"
		self.global_bonuses_pct['minion_health'] = 25
		self.global_bonuses_pct['minion_duration'] = 25

class EnchantmentStaff(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_STAFF
		self.name = "Enchanter's Staff"
		self.tag_bonuses_pct[Tags.Enchantment]['damage'] = 25
		self.tag_bonuses[Tags.Enchantment]['max_charges'] = 1
		self.tag_bonuses_pct[Tags.Enchantment]['duration'] = 25

class StaffOfMemory(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_STAFF
		self.name = "Memory Staff"
		self.global_bonuses['max_charges'] = 1

class HordeLordStaff(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_STAFF
		self.name = "Banner of the Horde"
		self.global_bonuses['num_summons'] = 1

class StaffOfWinter(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_STAFF
		self.name = "Staff of Winter"
		self.tag_bonuses_pct[Tags.Ice]['duration'] = 50
		self.tag_bonuses_pct[Tags.Nature]['duration'] = 50
		self.tag_bonuses_pct[Tags.Ice]['minion_duration'] = 50
		self.tag_bonuses_pct[Tags.Nature]['minion_duration'] = 50

		self.description = "Summons one friendly polar bear and one friendly storm spirit at the start of each level."

		self.owner_triggers[EventOnUnitAdded] = self.on_unit_added

	def on_unit_added(self, evt):
		bear = PolarBear()
		apply_minion_bonuses(self, bear)
		self.summon(bear)

		spirit = StormSpirit()
		apply_minion_bonuses(self, spirit)
		self.summon(spirit)

	def get_extra_examine_tooltips(self):
		return [PolarBear(), StormSpirit()]

class StaffOfSummer(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_STAFF
		self.name = "Staff of Summer"
		self.tag_bonuses_pct[Tags.Fire]['duration'] = 50
		self.tag_bonuses_pct[Tags.Nature]['duration'] = 50
		self.tag_bonuses_pct[Tags.Fire]['minion_duration'] = 50
		self.tag_bonuses_pct[Tags.Nature]['minion_duration'] = 50

		self.description = "Summons a friendly swarm of fire flies and a friendly fire spirit at the start of each level."

		self.owner_triggers[EventOnUnitAdded] = self.on_unit_added

	def on_unit_added(self, evt):
		flies = FireFlies()
		apply_minion_bonuses(self, flies)
		self.summon(flies)

		spirit = FireSpirit()
		apply_minion_bonuses(self, spirit)
		self.summon(spirit)

	def get_extra_examine_tooltips(self):
		return [FireFlies(), FireSpirit()]

class SeasonCrown(Equipment):

	def __init__(self, name, minor_summon, num_minor_summons, major_summon, num_major_summons, tag):
		self.minor_summon = minor_summon
		self.minor_summon_name = minor_summon().name
		self.num_minor_summons = num_minor_summons
		self.major_summon = major_summon
		self.major_summon_name = major_summon().name
		self.num_major_summons = num_major_summons
		Equipment.__init__(self)
		self.name = name
		self.resists[tag] = 30

	def on_init(self):
		self.slot = ITEM_SLOT_HEAD
		self.counter = 0
		self.owner_triggers[EventOnUnitAdded] = self.on_enter
		self.description = "After 25 turns, summon %d %ss and %d %ss." % (self.num_minor_summons, self.minor_summon_name, self.num_major_summons, self.major_summon_name)

	def on_advance(self):
		self.counter += 1
		if self.counter == 25:
			for i in range(self.num_minor_summons):
				unit = self.minor_summon()
				self.summon(unit, sort_dist=False, radius=2)
			for i in range(self.num_major_summons):
				unit = self.major_summon()
				self.summon(unit, sort_dist=False, radius=6)

	def on_enter(self, evt):
		self.counter = 0

	def get_extra_examine_tooltips(self):
		return [self.major_summon(), self.minor_summon()]

class GenericOculusDebuff(Buff):

	def __init__(self, tag):
		Buff.__init__(self)
		self.buff_type = BUFF_TYPE_CURSE
		self.color = tag.color
		self.name = "%s Weakness" % tag.name
		self.stack_type = STACK_NONE
		self.resists[tag] = -25

class GenericOculusEquip(Equipment):

	def __init__(self, name, tags):
		self.tags = tags
		Equipment.__init__(self)
		self.global_triggers[EventOnDamaged] = self.on_damage
		self.slot = ITEM_SLOT_STAFF
		self.name = "%s Oculus" % name
		damage_str = ' or '.join(t.name for t in self.tags)
		resist_str = ' and '
		self.description = "Whenever an enemy unit takes [%s] or [%s] damage, it gets -25 [%s] and [%s] resist.  This debuff does not stack." % (self.tags[0].name, self.tags[1].name, self.tags[0].name, self.tags[1].name)

	def on_damage(self, evt):
		if are_hostile(evt.unit, self.owner) and evt.damage_type in self.tags:
			buff = GenericOculusDebuff
			for tag in self.tags:
				evt.unit.apply_buff(GenericOculusDebuff(tag))

class RobeOfFire(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_ROBE
		self.name = "Robe of Fire"

		self.resists[Tags.Fire] = 50
		self.resists[Tags.Ice] = 25
		self.tag_bonuses_pct[Tags.Fire]['damage'] = 25
		self.tag_bonuses_pct[Tags.Fire]['minion_damage'] = 25

class RobeOfIce(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_ROBE
		self.name = "Robe of Ice"

		self.resists[Tags.Ice] = 50
		self.resists[Tags.Fire] = 25
		self.tag_bonuses[Tags.Ice]['duration'] = 3
		self.tag_bonuses_pct[Tags.Ice]['damage'] = 25

class RobeOfVoid(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_ROBE
		self.name = "Robe of Void"

		self.resists[Tags.Arcane] = 75
		self.resists[Tags.Dark] = 50
		self.tag_bonuses_pct[Tags.Arcane]['max_charges'] = 20
		self.tag_bonuses_pct[Tags.Translocation]['max_charges'] = 20

class RobeOfStorms(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_ROBE
		self.name = "Robe of Storms"
		self.resists[Tags.Ice] = 50
		self.resists[Tags.Lightning] = 50
		self.global_triggers[EventOnDamaged] = self.on_damage

		self.description = "Whenever an enemy takes [ice] or [lightning] damage, gain 1 SH up to a max of 1"

	def on_damage(self, evt):
		if not are_hostile(self.owner, evt.unit):
			return

		if not evt.damage_type in [Tags.Ice, Tags.Lightning]:
			return

		if self.owner.shields < 1:
			self.owner.add_shields(1)

class FaeRobe(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_ROBE
		self.name = "Fae Plate"
		self.description = "Gain 1 SH each turn, up to a maximum of 1"

	def on_advance(self):
		if self.owner.shields < 1:
			self.owner.shields += 1

class RobeOfTheDruid(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_ROBE
		self.name = "Robe of the Druids"
		self.resists[Tags.Poison] = 100
		self.tag_bonuses[Tags.Nature]['max_charges'] = 2

class VampiricVestments(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_ROBE
		self.name = "Vampiric Vestments"
		self.resists[Tags.Dark] = 50
		self.resists[Tags.Ice] = 50
		self.description = "Whenever a [Living] unit dies, gain 5 HP"
		self.global_triggers[EventOnDeath] = self.on_death

	def on_death(self, evt):
		if Tags.Living in evt.unit.tags:
			self.owner.deal_damage(-5, Tags.Heal, self)

class DwarvenChainmail(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_ROBE
		self.name = "Dwarven Chainmail"
		self.resists[Tags.Physical] = 50
		self.resists[Tags.Fire] = 50
		self.resists[Tags.Dark] = 50

class ElvenChainmail(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_ROBE
		self.name = "Elven Chainmail"
		self.resists[Tags.Physical] = 50
		self.resists[Tags.Arcane] = 50
		self.resists[Tags.Lightning] = 50


class EarthtrollArmor(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_ROBE
		self.name = "Earthtroll Armor"

		self.resists[Tags.Physical] = 50
		self.description = "Regenerate 1 HP each turn"

	def on_advance(self):
		if self.owner.cur_hp < self.owner.max_hp:
			self.owner.deal_damage(-1, Tags.Heal, self)

class StormtrollArmor(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_ROBE
		self.name = "Stormtroll Armor"

		self.resists[Tags.Lightning] = 50
		self.description = "Regenerate 1 HP each turn"

	def on_advance(self):
		if self.owner.cur_hp < self.owner.max_hp:
			self.owner.deal_damage(-1, Tags.Heal, self)

class HolyVestments(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_ROBE
		self.name = "Holy Vestments"
		self.description = "Start each level with 7 SH."

	def on_unit_added(self, evt):
		self.owner.add_shields(7
			)

class HunterCrown(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_HEAD
		self.name = "Marksman Cap"
		self.global_bonuses['range'] = 2
		self.global_bonuses['minion_range'] = 1

class ElementalCrown(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_HEAD
		self.name = "Elemental Crown"
		self.description = "Start level with a chaos spirit lair."
		self.resists[Tags.Lightning] = 25
		self.resists[Tags.Fire] = 25
		self.resists[Tags.Ice] = 25

		self.owner_triggers[EventOnUnitAdded] = self.on_unit_added

	def on_unit_added(self, evt):	
		lair = MonsterSpawner(ChaosSpirit)
		apply_minion_bonuses(self, lair)
		self.summon(lair, sort_dist=False)

	def get_extra_examine_tooltips(self):
		return [ChaosSpirit()]

class CrownOfTheFireFiend(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_HEAD
		self.name = "Fire Fiend Crown"
		self.description = "Start each level with 2 fire imp spawners"
		self.resists[Tags.Fire] = 25
		self.resists[Tags.Dark] = 25
		self.owner_triggers[EventOnUnitAdded] = self.on_unit_added

	def on_unit_added(self, evt):
		for i in range(2):
			lair = MonsterSpawner(FireImp)
			apply_minion_bonuses(self, lair)
			self.summon(lair, sort_dist=False)

	def get_extra_examine_tooltips(self):
		return [FireImp()]

class CrownOfTheSparkFiend(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_HEAD
		self.name = "Spark Fiend Crown"
		self.description = "Start each level with 2 spark imp spawners"
		self.resists[Tags.Lightning] = 25
		self.resists[Tags.Dark] = 25
		self.owner_triggers[EventOnUnitAdded] = self.on_unit_added

	def on_unit_added(self, evt):
		for i in range(2):
			lair = MonsterSpawner(SparkImp)
			apply_minion_bonuses(self, lair)
			self.summon(lair, sort_dist=False)

	def get_extra_examine_tooltips(self):
		return [SparkImp()]

class CrownOfTheIronFiend(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_HEAD
		self.name = "Iron Fiend Crown"
		self.description = "Start each level with 2 iron imp spawners"
		self.resists[Tags.Physical] = 25
		self.resists[Tags.Dark] = 25
		self.owner_triggers[EventOnUnitAdded] = self.on_unit_added

	def on_unit_added(self, evt):
		for i in range(2):
			lair = MonsterSpawner(IronImp)
			apply_minion_bonuses(self, lair)
			self.summon(lair, sort_dist=False)

	def get_extra_examine_tooltips(self):
		return [IronImp()]

class TrollHelm(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_HEAD
		self.name = "Troll Helm"
		self.resists[Tags.Fire] = -25
		self.description = "Regenerate 2 HP per turn"

	def on_advance(self):
		if self.owner.cur_hp < self.owner.max_hp:
			self.owner.deal_damage(-2, Tags.Heal, self)

class WarlordCrown(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_HEAD
		self.name = "Warlord Helm"
		self.global_bonuses['minion_damage'] = 4

class SpiritVisor(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_HEAD
		self.name = "Spirit Visor"
		self.resists[Tags.Arcane] = -25
		self.resists[Tags.Physical] = -25
		self.description = "Upon taking damage, gain 1 SH"
		self.owner_triggers[EventOnDamaged] = self.on_damaged

	def on_damaged(self, evt):
		if evt.damage <= 0:
			return

		self.owner.add_shields(1)

class MemoryHelm(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_HEAD
		self.name = "Brain Hat"
		self.global_bonuses['max_charges'] = 1

class ArmorOfSouls(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_ROBE
		self.name = "Soulmail"
		
		self.resists[Tags.Physical] = 25
		self.resists[Tags.Dark] = 25
		self.resists[Tags.Arcane] = 25

		self.global_triggers[EventOnDeath] = self.on_death

		self.description = "Whenever a [living] unit dies, gain 1 SH, up to a max of 2"

	def on_death(self, evt):
		if Tags.Living not in evt.unit.tags:
			return

		if self.owner.shields < 2:
			self.owner.add_shields(1)

class BasiliskScaleMail(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_ROBE
		self.name = "Basilisk Scale Armor"

		self.resists[Tags.Physical] = 25

		self.owner_triggers[EventOnDamaged] = self.on_damaged
		self.description = "On taking damage, the source is petrified for 1 turn"

	def on_damaged(self, evt):
		if not evt.source:
			return

		if not evt.source.owner:
			return

		if evt.source.owner == self.owner:
			return

		evt.source.owner.apply_buff(PetrifyBuff(), 2)
		

class TranslocationBoots(Equipment):

	def on_init(self):

		self.slot = ITEM_SLOT_BOOTS
		self.name = "Translocation Boots"
		self.tag_bonuses_pct[Tags.Translocation]['max_charges'] = 25
		self.tag_bonuses[Tags.Translocation]['range'] = 2

class Earthboots(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_BOOTS
		self.name = "Earthmeld Boots"
		self.description = "Gain 2 HP each turn unless you moved"
		self.last_pos = (-1, -1)

	def on_pre_advance(self):
		self.last_pos = (self.owner.x, self.owner.y)

	def on_advance(self):
		if self.last_pos == (self.owner.x, self.owner.y):
			self.owner.deal_damage(-2, Tags.Heal, self)

class WingedBoots(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_BOOTS
		self.name = "Winged Shoes"
		self.description = "Grants Flying"

	# Wont work if other stuff starts messing with the wizard's flyingness
	def on_applied(self, owner):
		self.owner.flying = True

	def on_unapplied(self):
		self.owner.flying = False

class DrillShoes(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_BOOTS
		self.name = "Drill Shoes"
		self.description = "Grants Burrowing"

	# Wont work if other stuff starts messing with the wizard's flyingness
	def on_applied(self, owner):
		self.owner.burrowing = True

	def on_unapplied(self):
		self.owner.burrowing = False

class SilkenSandals(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_BOOTS
		self.name = "Silken Sandals"
		self.tag_bonuses[Tags.Holy]['max_charges'] = 1
		self.tag_bonuses[Tags.Holy]['minion_duration'] = 5

		self.tag_bonuses_pct[Tags.Holy]['damage'] = 25

class SnowShoes(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_BOOTS
		self.name = "Snow Shoes"
		self.tag_bonuses[Tags.Ice]['max_charges'] = 1
		self.tag_bonuses[Tags.Ice]['range'] = 1
		self.tag_bonuses[Tags.Ice]['damage'] = 6

class ThunderingHooves(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_BOOTS
		self.name = "Thundering Hooves"
		self.description = "On moving, stun all adjacent non flying enemies for 1 turn"
		self.owner_triggers[EventOnMoved] = self.on_moved

	def on_moved(self, evt):
		if evt.teleport:
			return

		for t in self.owner.level.get_adjacent_points(self.owner, filter_walkable=False):
			if (t.x, t.y) == (self.owner.x, self.owner.y):
				continue
			self.owner.level.show_effect(t.x, t.y, Tags.Physical, minor=True)
			u = self.owner.level.get_unit_at(t.x, t.y)
			if u and not u.flying:
				u.apply_buff(Stun(), 1)

class TravellersBoots(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_BOOTS
		self.name = "Travellers Shoes"
		self.resists[Tags.Fire] = 25
		self.resists[Tags.Lightning] = 25
		self.resists[Tags.Ice] = 25

class SummonShoes(Equipment):

	def __init__(self, steps, spawn_fn, name):
		self.spawn_fn = spawn_fn
		self.steps = steps
		Equipment.__init__(self)
		self.name = name

	def on_init(self):
		self.slot = ITEM_SLOT_BOOTS
		self.description = "Every %d steps, summon a %s" % (self.steps, self.spawn_fn().name)
		self.charges = 0
		self.owner_triggers[EventOnMoved] = self.on_move
		self.owner_triggers[EventOnUnitAdded] = self.on_enter_level

	def on_move(self, evt):
		if evt.teleport:
			return

		self.charges += 1
		if self.charges >= self.steps:
			unit = self.spawn_fn()
			apply_minion_bonuses(self, unit)
			self.summon(unit)
			self.charges = 0

	def on_enter_level(self, evt):
		self.charges = 0

	def get_extra_examine_tooltips(self):
		return [self.spawn_fn()]

class HedgewizShoes(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_BOOTS
		self.name = "Cantrip Clogs"
		self.description = "Every 7 steps, regain a charge of each level 1 spell you know"

		self.charges = 0
		self.owner_triggers[EventOnMoved] = self.on_move

	def on_move(self, evt):
		if evt.teleport:
			return
			
		self.charges += 1
		if self.charges >= 7:
			for s in self.owner.spells:
				if s.level == 1:
					s.refund_charges(1)
			self.charges = 0

class TimeStriders(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_BOOTS
		self.name = "Timestriders"
		self.description = "Upon entering a level, all enemies are stunned for 1 turns"

		self.owner_triggers[EventOnUnitAdded] = self.on_enter


	def on_enter(self, evt):
		for u in self.owner.level.units:
			if are_hostile(self.owner, u):
				u.apply_buff(Stun(), 1)

class FingerSix(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_AMULET
		self.name = "Finger 6"

		self.global_bonuses['num_summons'] = 1
		self.global_bonuses['num_targets'] = 1

class Ankh(Equipment): 

	def on_init(self):
		self.slot = ITEM_SLOT_AMULET
		self.name = "Ankh"
		self.tag_bonuses[Tags.Holy]['minion_health'] = 10
		self.tag_bonuses[Tags.Dark]['minion_health'] = 10
		self.tag_bonuses[Tags.Holy]['minion_duration'] = 2
		self.tag_bonuses[Tags.Dark]['minion_duration'] = 2

class Drakentooth(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_AMULET
		self.name = "Drakentooth"

		self.tag_bonuses[Tags.Dragon]['minion_damage'] = 9
		self.tag_bonuses[Tags.Dragon]['minion_range'] = 1

class Drakenstaff(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_STAFF
		self.name = "Drakenstaff"

		self.tag_bonuses[Tags.Dragon]['breath_damage'] = 12
		self.tag_bonuses[Tags.Dragon]['minion_range'] = 1
		self.tag_bonuses_pct[Tags.Dragon]['minion_health'] = 25

class Bloodruby(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_AMULET
		self.name = "Blood Ruby"

		self.tag_bonuses_pct[Tags.Blood]['damage'] = 30
		self.tag_bonuses[Tags.Blood]['range'] = 1

class VampireScepte(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_STAFF
		self.name = "Vampire Wand"

		self.tag_bonuses[Tags.Blood]['max_charges'] = 1
		self.tag_bonuses[Tags.Dark]['max_charges'] = 1

		self.tag_bonuses[Tags.Blood]['range'] = 1
		self.tag_bonuses[Tags.Dark]['range'] = 1

		self.tag_bonuses_pct[Tags.Blood]['minion_damage'] = 25
		self.tag_bonuses_pct[Tags.Dark]['minion_damage'] = 25

class EyeNecklace(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_AMULET
		self.name = "Eye Rock Pendant"
		self.tag_bonuses[Tags.Eye]['shot_cooldown'] = -1

class AmberCube(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_AMULET
		self.name = "Amber Cube"
		self.tag_bonuses[Tags.Nature]['minion_health'] = 10

class SkullNecklace(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_AMULET
		self.name = "Skull Necklace"
		self.tag_bonuses[Tags.Dark]['minion_damage'] = 4

class RedObsidianShard(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_AMULET
		self.name = "Red Obsidian Shard"
		self.description = "Each turn, each enemy adjacent to an allied [demon] or [undead] unit takes 2 [fire] damage."

	def on_advance(self):
		targets = set()
		# Build a list of enemies adjacent to allies
		for u in self.owner.level.units:
			if u == self.owner:
				continue
			if are_hostile(u, self.owner):
				continue
			if not (Tags.Undead in u.tags or Tags.Demon in u.tags):
				continue

			for w in self.owner.level.get_units_in_ball(u, radius=1, diag=True):
				if are_hostile(w, self.owner):
					targets.add(w)

		for u in targets:
			u.deal_damage(2, Tags.Fire, self)

class JadeShard(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_AMULET
		self.name = "Jade Shard"
		self.description = "Each turn, each enemy adjacent to an allied [living] unit is poisoned for 3 turns."

	def on_advance(self):
		targets = set()
		# Build a list of enemies adjacent to allies
		for u in self.owner.level.units:
			if u == self.owner:
				continue
			if are_hostile(u, self.owner):
				continue
			if not (Tags.Living in u.tags):
				continue

			for w in self.owner.level.get_units_in_ball(u, radius=1, diag=True):
				if are_hostile(w, self.owner):
					targets.add(w)

		for u in targets:
			u.apply_buff(Poison(), 3)

class RealityAnchor(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_AMULET
		self.name = "Reality Anchor"
		self.global_bonuses['minion_duration'] = 3

class AmuletOfUndeath(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_AMULET
		self.name = "Amulet of Undeath"
		self.description = "Undead allies regenerate 3 HP per turn"

	def on_advance(self):
		for u in self.owner.level.units:
			if u == self.owner:
				continue
			if are_hostile(u, self.owner):
				continue
			if Tags.Undead not in u.tags:
				continue
			if u.cur_hp >= u.max_hp:
				continue

			u.deal_damage(-3, Tags.Heal, self)

class VialOfAmbrosia(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_AMULET
		self.name = "Vial of Ambrosia"
		self.description = "Whenever you enter a new level, gain immunity to stun effects for 10 turns."
		self.owner_triggers[EventOnUnitAdded] = self.on_unit_added

	def on_unit_added(self, evt):
		self.owner.apply_buff(StunImmune(), 10)

class IceCrystalStaff(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_STAFF
		self.name = "Ice Crystal Staff"
		self.conversions[Tags.Ice][Tags.Arcane] = .5
		self.description = "Half of all [ice] damage dealt to enemies is redealt as [arcane] damage."

class BloodburnStaff(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_STAFF
		self.name = "Bloodburn Staff"
		self.conversions[Tags.Fire][Tags.Poison] = .5
		self.description = "Half of all [fire] damage dealt to enemies is redealt as [poison] damage."

class ThunderforceStaff(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_STAFF
		self.name = "Thunderforce Staff"
		self.conversions[Tags.Lightning][Tags.Physical] = .5
		self.description = "Half of all [lightning] damage dealt to enemies is redealt as [physical] damage."

class ArcaneAmplifier(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_STAFF
		self.name = "Arcane Amplifier"
		self.description = "Redeal half of all damage you deal with [sorcery] as [arcane] damage."
		self.global_triggers[EventOnDamaged] = self.on_damage

	def on_damage(self, evt):
		if not isinstance(evt.source, Spell):
			return

		if Tags.Sorcery not in evt.source.tags:
			return

		if evt.source.owner != self.owner:
			return

		dmg = evt.damage // 2
		if dmg:
			evt.unit.deal_damage(dmg, Tags.Arcane, self)

class Flamenweaver(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_STAFF
		self.name = "The Flamenweaver"
		self.global_triggers[EventOnDamaged] = self.on_damage
		self.description = "Redeal half of all damage you deal with [enchantment] as [fire] damage."

	def on_damage(self, evt):
		if not isinstance(evt.source, Spell):
			return

		if Tags.Enchantment not in evt.source.tags:
			return

		if evt.source.owner != self.owner:
			return

		dmg = evt.damage // 2
		if dmg:
			evt.unit.deal_damage(dmg, Tags.Fire, self)	

class TreelordStaff(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_STAFF
		self.name = "Treelord Staff"
		self.description = "Whenever you cast a level 1 or 2 [nature] spell, summon a spriggan.\nWhenever you cast a level 3 or higher [nature] spell, summon a treant."
		self.owner_triggers[EventOnSpellCast] = self.on_spell_cast

	def on_spell_cast(self, evt):
		if Tags.Nature not in evt.spell.tags:
			return

		if evt.spell.level <= 2:
			unit = Spriggan()
		else:
			unit = Treant()

		apply_minion_bonuses(self, unit)
		self.summon(unit)

	def get_extra_examine_tooltips(self):
		return [Spriggan(), Treant()]

class AetherlordStaff(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_STAFF
		self.name = "Aetherlord Staff"
		self.description = "Whenever you cast a level 1 or 2 [arcane] spell, summon a boggart.\nWhenever you cast a level 3 or higher [arcane] spell, summon a phase spider."
		self.owner_triggers[EventOnSpellCast] = self.on_spell_cast

	def on_spell_cast(self, evt):
		if Tags.Arcane not in evt.spell.tags:
			return

		if evt.spell.level <= 2:
			unit = Boggart()
		else:
			unit = PhaseSpider()

		apply_minion_bonuses(self, unit)
		self.summon(unit)

	def get_extra_examine_tooltips(self):
		return [Boggart(), PhaseSpider()]

class FlylordStaff(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_STAFF
		self.name = "Filthlord Staff"
		self.description = "Whenever you cast a level 1 or 2 [dark] spell, summon a fly swarm.\nWhenever you cast a level 3 or higher [dark] spell, summon a bag of bugs."
		self.owner_triggers[EventOnSpellCast] = self.on_spell_cast

	def on_spell_cast(self, evt):
		if Tags.Dark not in evt.spell.tags:
			return

		if evt.spell.level <= 2:
			unit = FlyCloud()
		else:
			unit = BagOfBugs()

		apply_minion_bonuses(self, unit)
		self.summon(unit)

	def get_extra_examine_tooltips(self):
		return [FlyCloud(), BagOfBugs()]

class FireClawStaff(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_STAFF
		self.name = "Flaming Claw Staff"
		self.description = "Whenever a minion you control deals damage to an enemy, redeal half that much damage as [fire] damage."
		self.global_triggers[EventOnDamaged] = self.on_damage

	def on_damage(self, evt):
		if not evt.source:
			return

		if not evt.source.owner:
			return

		if evt.source.owner == self.owner:
			return

		if not are_hostile(self.owner, evt.unit):
			return

		if are_hostile(evt.source.owner, self.owner):
			return

		dmg = evt.damage // 2
		if dmg <= 0:
			return

		evt.unit.deal_damage(dmg, Tags.Fire, self)

class IceClawStaff(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_STAFF
		self.name = "Icy Claw Staff"
		self.description = "Whenever a minion you control deals damage to an enemy, redeal half that much damage as [ice] damage."
		self.global_triggers[EventOnDamaged] = self.on_damage

	def on_damage(self, evt):
		if not evt.source:
			return

		if not evt.source.owner:
			return

		if evt.source.owner == self.owner:
			return

		if not are_hostile(self.owner, evt.unit):
			return

		if are_hostile(evt.source.owner, self.owner):
			return

		dmg = evt.damage // 2
		if dmg <= 0:
			return

		evt.unit.deal_damage(dmg, Tags.Ice, self)

class BootsOfDramaticArrival(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_BOOTS
		self.name = "Boots of Dramatic Arrival"
		self.description = "Upon entering a rift, immediately casts your highest level self targeted spell for free."

		self.owner_triggers[EventOnUnitAdded] = self.on_enter

	def on_enter(self, evt):
		spells = [s for s in self.owner.spells if s.range == 0]
		if not spells:
			return

		max_level = max([s.level for s in spells])
		spells = [s for s in spells if s.level == max_level]

		choice = random.choice(spells)

		self.owner.level.act_cast(self.owner, choice, self.owner.x, self.owner.y, pay_costs=False)

class TricksterStaff(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_STAFF
		self.name = "Scepter of Mischief"
		self.description = "For every 50 damage dealt to enemies by [enchantments:enchantment], summon 3 Troublers for 7 turns."
		self.tag_bonuses_pct[Tags.Enchantment]['damage'] = 25

		self.charge = 0
		self.global_triggers[EventOnDamaged] = self.on_damage

		self.minion_duration = 6

	def on_damage(self, evt):
		if not are_hostile(evt.unit, self.owner):
			return

		if not evt.source:
			return

		if not isinstance(evt.source, Spell):
			return

		if Tags.Enchantment not in evt.source.tags:
			return

		self.charge += evt.damage

		while self.charge > 50:
			for i in range(3):
				self.charge -= 50
				troubler = Troubler()
				troubler.turns_to_death = 7
				apply_minion_bonuses(self, troubler)
				self.summon(troubler)

	def get_extra_examine_tooltips(self):
		return [Troubler()]

class AmuletOfEmeraldFlame(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_AMULET
		self.name = "Amulet of Emerald Flame"
		self.description = "For every 30 damage dealt to enemies by [enchantments:enchantment], the closest enemy takes 10 fire damage."
		self.damage = 10
		self.global_triggers[EventOnDamaged] = self.on_damage
		self.charge = 0

	def on_damage(self, evt):
		if not are_hostile(evt.unit, self.owner):
			return

		if not evt.source:
			return

		if not isinstance(evt.source, Spell):
			return

		if Tags.Enchantment not in evt.source.tags:
			return

		self.charge += evt.damage

		while self.charge > 30:
			self.charge -= 30
			enemies = [u for u in self.owner.level.units if are_hostile(self.owner, u)]
			if enemies:
				random.shuffle(enemies)
				enemies.sort(key = lambda u: distance(u, self.owner))

				target = enemies[0]
				self.owner.level.show_path_effect(self.owner, target, Tags.Fire, minor=True)
				target.deal_damage(10, Tags.Fire, self)

class TrollCrown(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_HEAD
		self.name = "Troll Crown"
		self.description = "Start each level with a friendly troll spawner"
		self.owner_triggers[EventOnUnitAdded] = self.on_start

	def on_start(self, evt):
		for i in range(1):
			lair = MonsterSpawner(Troll)
			apply_minion_bonuses(self, lair)
			self.summon(lair, sort_dist=False)

	def get_extra_examine_tooltips(self):
		return [Troll()]

class FlyCrown(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_HEAD
		self.name = "Crown of Beelzebub"
		self.description = "Start each level with 2 friendly bag of bugs spawners"
		self.owner_triggers[EventOnUnitAdded] = self.on_start

	def on_start(self, evt):
		for i in range(2):
			lair = MonsterSpawner(BagOfBugs)
			apply_minion_bonuses(self, lair)
			self.summon(lair, sort_dist=False)

	def get_extra_examine_tooltips(self):
		return [BagOfBugs()]

class MonkeySkull(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_AMULET
		self.name = "Monkey Skull Amulet"
		self.tag_bonuses[Tags.Sorcery]['duration'] = 3
		self.tag_bonuses[Tags.Conjuration]['radius'] = 1
		self.tag_bonuses[Tags.Enchantment]['minion_damage'] = 6

class CannibalCrown(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_HEAD
		self.name = "Cannibal Mask"
		self.description = "Whenever a [living] ally dies, a random wounded ally up to 3 tiles away receives healing equal to the dead ally's max hp."
		self.global_triggers[EventOnDeath] = self.on_death

	def on_death(self, evt):
		if are_hostile(evt.unit, self.owner):
			return

		if not Tags.Living in evt.unit.tags:
			return

		heal_targets = [u for u in self.owner.level.get_units_in_ball(evt.unit, 3) if not are_hostile(self.owner, u)]
		if not heal_targets:
			return

		target = random.choice(heal_targets)
		target.heal(evt.unit.max_hp, self)
		self.owner.level.show_path_effect(target, evt.unit, Tags.Blood, minor=True)

class FreeCastStaff(Equipment):

	def __init__(self, name, tag, counter_max, free_spell_class):
		
		self.tag = tag
		self.counter_max = counter_max
		self.spell = free_spell_class()
		Equipment.__init__(self)	
		self.name = name
		self.counter = 0
		
	def on_init(self):
		self.global_triggers[EventOnDamaged] = self.on_damage
		self.slot = ITEM_SLOT_STAFF

		self.description = "For every %d damage dealt to enemies with %s spells, cast %s on a random enemy" % (self.counter_max, self.tag.name, self.spell.name)

	def on_damage(self, evt):
		if not are_hostile(self.owner, evt.unit):
			return

		if not evt.source:
			return

		if not isinstance(evt.source, Spell):
			return

		if self.tag not in evt.source.tags:
			return

		self.counter += evt.damage

		self.owner.level.queue_spell(self.do_freecast(evt))

	# Queue this so that in the highly likely event that the spell kills its target the freecast isnt wasted
	def do_freecast(self, evt):
		while self.counter > self.counter_max:

			# Pick a random enemy as the target
			targets = [u for u in self.owner.level.units if are_hostile(self.owner, u)]

			if not targets:
				return

			target = random.choice(targets)

			self.spell.caster = self.owner
			self.spell.owner = self.owner
			self.owner.level.act_cast(self.owner, self.spell, target.x, target.y, pay_costs=False)
			self.counter -= self.counter_max
			yield

	def get_extra_examine_tooltips(self):
		return [self.spell]

class RandomLittleRing(Equipment):

	def __init__(self, forced_tag_tup=None, forced_stat_tup=None):
		self.forced_stat_tup = forced_stat_tup
		self.forced_tag_tup = forced_tag_tup
		Equipment.__init__(self)

	def on_init(self):
		
		tag, stat = None, None
			
		if self.forced_tag_tup:
			tag, tag_name = self.forced_tag_tup
		else:
			tag, tag_name, _ = random.choices(ring_tags, weights=ring_tag_weights, k=1)[0]
		
		if self.forced_stat_tup:
			stat, stat_name, stat_amt = self.forced_stat_tup
		else:
			stat, stat_name, stat_amt, _ = random.choices(ring_stats, weights=ring_stat_weights, k=1)[0]

		self.name = "%s %s" % (tag_name, stat_name.capitalize())

		if isinstance(stat_amt, int):
			self.tag_bonuses[tag][stat] = stat_amt
		else:
			self.tag_bonuses_pct[tag][stat] = int(stat_amt*100)

		self.slot = ITEM_SLOT_AMULET

		# Make icon
		self.asset_name = 'trinket_%s' % stat_name
		self.recolor_primary = tag.color

class RandomSheild(Equipment):

	def on_init(self):

		self.tag = random.choice(damage_tags)

		self.name = "%s Shield" % self.tag.name
		self.resists[self.tag] = 25
		self.slot = ITEM_SLOT_AMULET

class ConversionHat(Equipment):

	def on_init(self):

		self.slot = ITEM_SLOT_HEAD

		tags = random.sample(hat_tag_names, k=2)
		self.from_tag, from_name = tags[0]
		self.to_tag, to_name = tags[1]

		self.name = ("%s%s Cap" % (from_name, to_name)).capitalize()

		self.description = "Redeal 50%% of [%s] damage dealt to enemies as [%s] damage" % (self.from_tag.name, self.to_tag.name)
		self.conversions[self.from_tag][self.to_tag] = .5

		self.asset_name = 'damage_conversion_hat'
		self.recolor_primary = self.from_tag.color
		self.recolor_secondary = self.to_tag.color


class RandomWand(Equipment):

	def roll_bonus(self, mult):

		stat, _, stat_amt, _ = random.choices(ring_stats, weights=ring_stat_weights)[0]

		if isinstance(stat_amt, int):
			self.tag_bonuses[self.tag][stat] += mult*stat_amt
		else:
			self.tag_bonuses_pct[self.tag][stat] += mult*stat_amt*100

	def on_init(self):

		self.slot = ITEM_SLOT_STAFF
		self.tag = random.choice(ring_tags)[0]

		self.roll_bonus(2)
		if random.random() < .5:	
			self.roll_bonus(1)
			self.roll_bonus(1)
			self.roll_bonus(1)
		else:
			self.roll_bonus(2)

		if random.random() < .25:
			self.roll_bonus(1)

		self.name = "%s Wand" % self.tag.name

class SummonOnDeathStaff(Equipment):

	def __init__(self, monster, name, monster_name=None, duration=None):
		self.monster = monster
		self.monster_name = monster_name
		Equipment.__init__(self)
		self.name = name
		self.duration = duration

		if self.duration:
			self.description += " for %d turns" % self.duration

	def on_init(self):
		self.slot = ITEM_SLOT_STAFF
		self.global_triggers[EventOnDeath] = self.on_death

		monster_name = self.monster_name if self.monster_name else self.monster().name
		self.description = "Whenever an enemy dies, summon a %s where it was" % monster_name


	def on_death(self, evt):
		if not are_hostile(self.owner, evt.unit):
			return

		# Do not raise temporary summons
		if evt.unit.turns_to_death is not None:
			return

		self.owner.level.queue_spell(self.do_summon(evt))

	def do_summon(self, evt):
		unit = self.monster()

		if self.duration:
			unit.turns_to_death = self.duration

		apply_minion_bonuses(self, unit)
		self.summon(unit, target=evt.unit)
		yield

	def get_extra_examine_tooltips(self):
		return [self.monster()]

class Crackledark(Equipment):

	def on_init(self):
		self.name = "Crackledarkener"
		self.slot = ITEM_SLOT_STAFF
		self.num_targets = 2
		self.radius = 6
		self.global_triggers[EventOnDamaged] = self.on_damage
		self.description = "Whenever an enemy takes [dark] damage, deal that much [lightning] damage to up to 2 enemy units in a 6 tile burst."


	def on_damage(self, evt):
		if not are_hostile(evt.unit, self.owner):
			return

		if evt.damage_type == Tags.Dark:
			self.owner.level.queue_spell(self.send_bolts(evt.unit, evt.damage))

	def bolt(self, damage, source, target):
		for point in Bolt(self.owner.level, source, target):
			self.owner.level.show_effect(point.x, point.y, Tags.Lightning)
			yield True

		target.deal_damage(damage, Tags.Lightning, self)
		yield False

	def send_bolts(self, source, damage):

		targets = self.owner.level.get_units_in_ball(source, self.radius)
		targets = [t for t in targets if are_hostile(t, self.owner) and t != source and self.owner.level.can_see(t.x, t.y, source.x, source.y)]
		random.shuffle(targets)

		bolts = [self.bolt(damage, source, t) for t in targets[:self.num_targets]]

		while bolts:
			bolts = [b for b in bolts if next(b)]
			yield

class CoilOfCharging(Equipment):

	def __init__(self, name, hightag, lowtag):
		Equipment.__init__(self)
		self.name = name
		self.hightag = hightag
		self.lowtag = lowtag
		self.slot = ITEM_SLOT_AMULET
		self.description = "Whenever you cast a [%s] spell, gain a charge of a random lower level [%s] spell" % (hightag.name, lowtag.name)

	def on_init(self):
		self.owner_triggers[EventOnSpellCast] = self.on_cast

	def on_cast(self, evt):
		if self.hightag not in evt.spell.tags:
			return

		candidates = [s for s in self.owner.spells if self.lowtag in s.tags and s.cur_charges < s.get_stat('max_charges') and s.level < evt.spell.level]
		if not candidates:
			return

		choice = random.choice(candidates)
		choice.refund_charges(1)

class HelmOfTheHost(Equipment):

	def on_init(self):
		self.slot = ITEM_SLOT_HEAD
		self.name = "Helm of the Host"
		self.global_triggers[EventOnDamaged] = self.on_damage
		self.description = "Each turn, all allied units heal for 1 hp per 100 damage dealt to enemies by allied units."
		self.counter = 0

	def on_damage(self, evt):
		if not evt.source:
			return

		if not evt.source.owner:
			return

		if evt.damage <= 0:
			return

		if evt.source.owner == self.owner:
			return

		if are_hostile(self.owner, evt.source.owner):
			return

		self.counter += evt.damage

	def on_pre_advance(self):

		heal = self.counter // 100
		self.counter = self.counter % 100

		if heal:
			for u in self.owner.level.units:
				
				if are_hostile(self.owner, u):
					continue

				if u == self.owner:
					continue

				u.heal(heal, self)

class ScepterOfSorrows(Equipment):

	def on_init(self):
		self.name = "Scepter of Sorrows"
		self.description = "Whenever an enemy takes [ice] and [dark] damage in the same turn, summon a spirit of sorrow near that enemy for 10 turns."
		self.slot = ITEM_SLOT_STAFF

		self.global_triggers[EventOnDamaged] = self.on_damaged

		self.ice_victims = set()
		self.dark_victims = set()
		self.blackice_victims = set()

	def on_advance(self):
		self.ice_victims.clear()
		self.dark_victims.clear()
		self.blackice_victims.clear()

	def on_damaged(self, evt):
		if evt.damage_type not in [Tags.Ice, Tags.Dark]:
			return

		if evt.unit in self.blackice_victims:
			return

		if not are_hostile(self.owner, evt.unit):
			return

		if evt.damage_type == Tags.Ice:
			self.ice_victims.add(evt.unit)
			if evt.unit in self.dark_victims:
				self.blackice_victims.add(evt.unit)
				self.owner.level.queue_spell(self.do_summon(evt.unit.x, evt.unit.y))
			
		if evt.damage_type == Tags.Dark:
			self.dark_victims.add(evt.unit)
			if evt.unit in self.ice_victims:
				self.blackice_victims.add(evt.unit)
				self.owner.level.queue_spell(self.do_summon(evt.unit.x, evt.unit.y))

	def monster(self):
		ghost = Ghost()
		ghost.max_hp = 4
		ghost.spells[0] = SimpleRangedAttack(damage=7, range=5, damage_type=Tags.Ice)
		ghost.name = "Sorrow Spirit"
		ghost.asset_name = "sorrow_ghost"
		ghost.resists[Tags.Ice] = 100
		return ghost

	def do_summon(self, x, y):
		
		p = self.owner.level.get_summon_point(x, y, flying=True)
		if not p:
			return

		ghost = self.monster()

		ghost.turns_to_death = 10
		self.summon(ghost, target=Point(x, y))
		
		yield

	def get_extra_examine_tooltips(self):
		return [self.monster()]

class ThornItem(Equipment):

	def __init__(self, name, dtype):
		self.dtype = dtype
		Equipment.__init__(self)
		self.name = name

	def on_init(self):
		self.description = "Your summoned allies deal 6 [%s] damage to melee attackers" % self.dtype.name
		self.slot = ITEM_SLOT_AMULET
		self.global_triggers[EventOnUnitAdded] = self.on_unit_added

	def on_unit_added(self, evt):
		if evt.unit == self.owner:
			return

		if are_hostile(evt.unit, self.owner):
			return

		buff = Thorns(6, dtype=self.dtype)
		buff.buff_type = BUFF_TYPE_PASSIVE
		evt.unit.apply_buff(buff)

class MaskOfIcyChill(Equipment):

	def on_init(self):
		self.name = "Icy Chill Mask"
		self.slot = ITEM_SLOT_HEAD
		self.description = "Whenever you cast an [ice] spell, deal 2 [ice] damage to all enemy units in line of sight of the target"
		self.owner_triggers[EventOnSpellCast] = self.on_cast

	def on_cast(self, evt):
		if Tags.Ice in evt.spell.tags:
			for u in list(self.owner.level.units):
				if not self.owner.level.are_hostile(u, self.owner):
					continue
				if not self.owner.level.can_see(evt.x, evt.y, u.x, u.y):
					continue

				u.deal_damage(2, Tags.Ice, self)

class StoneMask(Equipment):

	def on_init(self):
		self.name = "Stone Mask"
		self.slot = ITEM_SLOT_HEAD
		self.description = "Each turn, petrify a random unpetrified enemy in line of sight for 3 turns"
		self.resists[Tags.Physical] = 25

	def on_advance(self):
		candidates = [u for u in self.owner.level.get_units_in_los(self.owner) if are_hostile(self.owner, u) and not u.has_buff(PetrifyBuff)]
		if not candidates:
			return

		target = random.choice(candidates)
		target.apply_buff(PetrifyBuff(), 3)

class EyeHelm(Equipment):

	def on_init(self):
		self.name = "Eye Helm"
		self.slot = ITEM_SLOT_HEAD
		self.description = "Whenever you cast an [eye] spell, gain 3 SH, up to a maximum of 20."
		self.owner_triggers[EventOnSpellCast] = self.on_cast

	def on_cast(self, evt):
		if Tags.Eye in evt.spell.tags:
			self.owner.add_shields(3)

class GenericFrenzyStack(Buff):

	def __init__(self, tag, damage):
		Buff.__init__(self)
		self.name = "%s Frenzy" % tag.name
		self.color = tag.color
		self.stack_type = STACK_INTENSITY
		self.tag_bonuses[tag]['damage'] = damage

class GenericFrenzyMask(Equipment):

	def __init__(self, tag):
		self.tag = tag
		Equipment.__init__(self)

	def on_init(self):
		self.slot = ITEM_SLOT_HEAD
		self.name = "%s Frenzy Mask" % self.tag.name
		self.owner_triggers[EventOnSpellCast] = self.on_spell_cast
		self.bonus = 2
		self.buff_duration = 6
		self.description = "Whenever you cast a [%s] spell, your [%s] spells and skills gain [%d_damage:damage] for [%d_turns:duration]" % (self.tag.name, self.tag.name, self.bonus, self.buff_duration)

	def on_spell_cast(self, evt):
		if self.tag in evt.spell.tags:
			self.owner.apply_buff(GenericFrenzyStack(self.tag, self.bonus), duration=self.buff_duration)

class GlassAnimaStaff(Equipment):

	def on_init(self):
		self.name = "Glassy Fae Staff"
		self.slot = ITEM_SLOT_STAFF
		self.description = "Whenever a glassified enemy takes physical damage, it is unglassified and a glass faery is summoned."
		self.global_triggers[EventOnDamaged] = self.on_damage

	def on_damage(self, evt):
		if not are_hostile(self.owner, evt.unit):
			return

		if not evt.unit.has_buff(GlassPetrifyBuff):
			return

		if evt.damage_type != Tags.Physical:
			return

		evt.unit.remove_buff(GlassPetrifyBuff)

		faery = FairyGlass()
		self.summon(faery, target=evt.unit)

class QuillStaff(Equipment):

	def on_init(self):
		self.name = "Quill Staff"
		self.slot = ITEM_SLOT_STAFF
		self.description = "Whenever a [living] ally deals damage to an enemy, if that enemy is in your line of sight, deal 8 [physical] damage to that enemy."
		self.global_triggers[EventOnDamaged] = self.on_damage

	def on_damage(self, evt):
		if not evt.source or not evt.source.owner:
			return

		if evt.source.owner == self.owner:
			return

		# living
		if Tags.Living not in evt.source.owner.tags:
			return

		# ally
		if are_hostile(self.owner, evt.source.owner):
			return

		# to an enemy
		if not are_hostile(self.owner, evt.unit):
			return

		if not self.owner.level.can_see(self.owner.x, self.owner.y, evt.unit.x, evt.unit.y):
			return

		self.owner.level.queue_spell(self.quill(evt.unit))

	def quill(self, target):
		# Dont shoot at dead targets, it slows down the game
		if not target.is_alive():
			return

		for point in Bolt(self.owner.level, self.owner, target):
			self.owner.level.projectile_effect(point.x, point.y, proj_name='physical_bolt', proj_origin=self.owner, proj_dest=target)
			yield

		target.deal_damage(8, Tags.Physical, self)

class TwoElementShotRobe(Equipment):

	def __init__(self, name, tag1, tag2):
		self.tag1 = tag1
		self.tag2 = tag2
		Equipment.__init__(self)
		self.name = "Robe of %s" % name

	def on_init(self):
		self.slot = ITEM_SLOT_ROBE
		self.resists[self.tag1] = 25
		self.resists[self.tag2] = 25

		self.description = "Whenever you cast a [%s] or [%s] spell, deal 8 [%s] to a random enemy in line of sight, and 8 [%s] damage to another." % (self.tag1.name, self.tag2.name, self.tag1.name, self.tag2.name)

		# Make it global so it works with armorer tee hee
		self.global_triggers[EventOnSpellCast] = self.on_cast

	def on_cast(self, evt):
		
		if not evt.caster.is_player_controlled:
			return

		if self.tag1 not in evt.spell.tags and self.tag2 not in evt.spell.tags:
			return

		self.owner.level.queue_spell(self.bolts())

	def bolts(self):

		candidates = [u for u in self.owner.level.get_units_in_los(self.owner) if are_hostile(self.owner, u)]
		random.shuffle(candidates)

		dtypes = [self.tag1, self.tag2]
		random.shuffle(dtypes)

		for dtype in dtypes:
			
			# Translate weird tags to damage types
			if dtype == Tags.Metallic:
				dtype = Tags.Physical

			if not candidates:
				continue


			target = candidates.pop()
			self.owner.level.show_beam(self.owner, target, dtype)
			target.deal_damage(8, dtype, self)
			yield

class RobeOfTwilight(TwoElementShotRobe):

	def __init__(self):
		TwoElementShotRobe.__init__(self, 'Twilight', Tags.Dark, Tags.Holy)

class RobeOfAgony(TwoElementShotRobe):

	def __init__(self):
		TwoElementShotRobe.__init__(self, 'Agony', Tags.Lightning, Tags.Dark)

class RobeOfFrostfire(TwoElementShotRobe):

	def __init__(self):
		TwoElementShotRobe.__init__(self, 'Frostfire', Tags.Fire, Tags.Ice)

class RobeOfCrystals(TwoElementShotRobe):

	def __init__(self):
		TwoElementShotRobe.__init__(self, 'Crystals', Tags.Arcane, Tags.Ice)

class DamageToPetsAmulet(Equipment):

	def __init__(self, name, counter_max, dtype, spawn_fn):
		self.spawn_fn = spawn_fn
		self.dtype = dtype
		self.counter_max = counter_max
		self.counter = 0
		Equipment.__init__(self)
		self.name = name

	def on_init(self):
		example = self.spawn_fn()
		self.monster_name = example.name
		self.slot = ITEM_SLOT_AMULET

		self.owner_triggers[EventOnUnitAdded] = self.on_enter
		self.global_triggers[EventOnDamaged] = self.on_damage

	def get_description(self):
		return "For every %d [%s] damage dealt to enemies, summon a %s.\nCurrent: %d" % (self.counter_max, self.dtype.name, self.monster_name, self.counter)

	def on_enter(self, evt):
		self.counter = 0

	def on_damage(self, evt):
		if not are_hostile(self.owner, evt.unit):
			return

		if evt.damage_type != self.dtype:
			return

		self.counter += evt.damage
		while self.counter > self.counter_max:
			unit = self.spawn_fn()
			self.summon(unit)
			self.counter -= self.counter_max

	def get_extra_examine_tooltips(self):
		return [self.spawn_fn()]

class PrinceOfRuinLike(Equipment):

	def __init__(self, name, tags):
		self.tags = tags
		Equipment.__init__(self)
		self.name = name

	def on_init(self):
		self.slot = ITEM_SLOT_AMULET
		self.global_triggers[EventOnDeath] = self.on_death
		self.damage = 9
		self.radius = 5

		dtype_str = ' or '.join(['[' + t.name + ']' for t in self.tags])
		self.description = "Whenever an enemy dies to %s damage, deal 9 damage of that type to a random enemy in line of sight of the target up to 5 tiles away." % dtype_str

	def on_death(self, evt):
		if not are_hostile(evt.unit, self.owner):
			return
		damage_event = evt.damage_event
		if damage_event and damage_event.damage_type in self.tags:
			self.owner.level.queue_spell(self.trigger(evt))

	def trigger(self, evt):
		candidates = [u for u in self.owner.level.get_units_in_ball(evt.unit, self.radius) if are_hostile(self.owner, u)]
		candidates = [u for u in candidates if self.owner.level.can_see(evt.unit.x, evt.unit.y, u.x, u.y)]

		if candidates:
			target = random.choice(candidates)
			for p in self.owner.level.get_points_in_line(evt.unit, target, find_clear=True)[1:-1]:
				self.owner.level.show_effect(p.x, p.y, evt.damage_event.damage_type)
			target.deal_damage(self.damage, evt.damage_event.damage_type, self)
		yield

class JarOfBossness(Equipment):

	def __init__(self, name, boss_type, tag=None):
		self.boss_type = boss_type
		self.tag = tag

		Equipment.__init__(self)
		self.slot = ITEM_SLOT_AMULET
		self.name = name
		
		self.owner_triggers[EventOnSpellCast] = self.on_spell_cast
		self.global_triggers[EventOnUnitAdded] = self.on_unit_added

		self.counter = 0

	def get_description(self):
		if self.tag:
			return ("Each non-%s ally you summon has a one in three chance to be %s.\n") % (self.tag.name, BossSpawns.get_boss_mod_name(self.boss_type))
		else:
			return ("Each ally you summon as a one in three chance to be %s.\n") % BossSpawns.get_boss_mod_name(self.boss_type)

	def on_spell_cast(self, evt):
		if self.tag in evt.spell.tags:
			self.counter = 1

	def on_unit_added(self, evt):

		# Dont boss the wizard2
		if evt.unit == self.owner:
			return

		if are_hostile(self.owner, evt.unit):
			return

		if random.random() > 1 / 3:
			return

		# Do not apply boss modifiers to monsters that already have them
		# Especialy not if its the same boss modifier but we dont have a good way to check that
		if evt.unit.recolor_primary:
			return

		if self.tag and self.tag in evt.unit.tags:
			return

		BossSpawns.apply_modifier(self.boss_type, evt.unit)

		for b in evt.unit.buffs:
			if not b.applied:
				# Apply unapplied buffs- these can come from boss modifiers
				b.apply(evt.unit)
				b.buff_type = BUFF_TYPE_PASSIVE

class CursePipe(Equipment):

	def __init__(self, name, buff_t, duration, num_targets, cool_down, visual_tag):
		Equipment.__init__(self)
		self.name = name
		self.slot = ITEM_SLOT_AMULET
		self.buff_t = buff_t
		self.num_targets = num_targets
		self.cool_down = cool_down
		self.cur_cooldown = 0
		self.owner_triggers[EventOnUnitAdded] = self.on_enter
		self.visual_tag = visual_tag
		self.duration = duration

		self.description = "Every %d turns, the nearest %d enemy units are afflicted with %s for %d turns.\nDoes not target units already afflicted with %s."
		self.description = self.description % (self.cool_down, self.num_targets, self.buff_t().name, self.duration, self.buff_t().name)

	def on_enter(self, evt):
		self.cur_cooldown = self.cool_down

	def on_advance(self):
		self.cur_cooldown -= 1
		if self.cur_cooldown == 0:
			targets = [u for u in self.owner.level.units if are_hostile(u, self.owner) and not u.has_buff(self.buff_t)]
			random.shuffle(targets)
			targets.sort(key=lambda u: distance(self.owner, u))
			targets = targets[:self.num_targets]
			for t in targets:
				self.owner.level.show_path_effect(self.owner, t, self.visual_tag, minor=True, inclusive=False)
				t.apply_buff(self.buff_t(), self.duration)
			self.cur_cooldown = self.cool_down

class BloodspikeHelm(Equipment):

	def on_init(self):
		self.name = "Bloodspike Crown"
		self.slot = ITEM_SLOT_HEAD
		self.num_targets = 3
		self.owner_triggers[EventOnSpendHP] = self.on_spend

	def on_spend(self, evt):
		self.owner.level.queue_spell(self.fire_spikes(evt.hp))

	def fire_spikes(self, damage):
		targets = [u for u in self.owner.level.get_units_in_los(self.owner) if are_hostile(u, self.owner)]
		random.shuffle(targets)
		for target in targets[:self.num_targets]:
			for point in Bolt(self.owner.level, self.owner, target):
				self.owner.level.projectile_effect(point.x, point.y, proj_name='physical_bolt', proj_origin=self.owner, proj_dest=target)
			target.deal_damage(damage, Tags.Physical, self)
			yield


	def get_description(self):
		return "On spending HP to cast a [blood] spell, deal that much [physical] damage to up to 3 enemies in line of sight."


class CurseDoll(Equipment):

	def __init__(self, name, tag, spell):
		Equipment.__init__(self)
		self.name = "%s Curse Doll" % name
		self.tag = tag
		self.spell = spell
		self.spell_name = spell().name

	def on_init(self):
		self.slot = ITEM_SLOT_AMULET
		self.global_triggers[EventOnDeath] = self.on_death

	def get_description(self):
		return "Whenever one of your [%s] minions dies, it casts your %s on the killer." % (self.tag.name, self.spell_name)

	def on_death(self, evt):
		if are_hostile(evt.unit, self.owner):
			return

		if self.tag not in evt.unit.tags:
			return

		if evt.damage_event is None:
			return

		source = evt.damage_event.source
		if not source:
			return

		source_unit = source.owner
		if not source_unit:
			return

		s = self.owner.get_or_make_spell(self.spell)
		s.statholder = self.owner
		s.caster = evt.unit
		s.owner = evt.unit

		self.owner.level.act_cast(evt.unit, s, source_unit.x, source_unit.y, pay_costs=False)

class TagHelm(Equipment):

	def __init__(self, tag):
		Equipment.__init__(self)
		self.tag = tag
		self.slot = ITEM_SLOT_HEAD
		self.name = "%s Helm" % self.tag.name

		resist = self.tag
		if resist == Tags.Nature or resist == Tags.Metallic:
			resist = Tags.Physical

		self.resists[resist] = 25
		self.tag_bonuses_pct[self.tag]['damage'] = 25
		self.tag_bonuses[self.tag]['range'] = 1

class SpellBoots(Equipment):

	def __init__(self, name, spell, steps):
		self.spell = spell
		self.steps = steps

		Equipment.__init__(self)

		self.name = name
		self.spell_name = self.spell().name

	def on_init(self):
		self.slot = ITEM_SLOT_BOOTS
		self.counter = self.steps
		self.owner_triggers[EventOnMoved] = self.on_move

	def on_move(self, evt):
		if evt.teleport:
			return

		self.counter -= 1
		if self.counter <= 0:
			spell = self.owner.get_or_make_spell(self.spell)
			self.owner.level.act_cast(self.owner, spell, self.owner.x, self.owner.y, pay_costs=False)
			self.counter = self.steps

	def get_description(self):
		return "Every %s steps, casts your %s spell.\n%d steps until cast." % (self.steps, self.spell_name, self.counter)


Staves = [
	RandomWand,
	RandomWand,
	RandomWand,
	RandomWand,
	RandomWand,
	RandomWand,
	RandomWand,
	RandomWand,
	RandomWand,
	RandomWand,

	BladeStaff,
	GeometerStaff,
	StaffOfMemory,
	HordeLordStaff,
	
	lambda: GenericOculusEquip("Storm", [Tags.Ice, Tags.Lightning]),
	lambda: GenericOculusEquip("Void", [Tags.Dark, Tags.Arcane]),
	lambda: GenericOculusEquip("Pyrostatic", [Tags.Fire, Tags.Lightning]),
	lambda: GenericOculusEquip("Twilight", [Tags.Dark, Tags.Holy]),
	lambda: GenericOculusEquip("Crystal", [Tags.Ice, Tags.Arcane]),
	lambda: GenericOculusEquip("Purity", [Tags.Fire, Tags.Holy]),

	ArcaneAmplifier,
	Flamenweaver,
	
	TreelordStaff,
	AetherlordStaff,
	FlylordStaff,
	
	FireClawStaff,
	IceClawStaff,
	
	TricksterStaff,

	Drakenstaff,

	lambda : FreeCastStaff("The Purifier", Tags.Holy, 50, Spells.ImmolateSpell),
	lambda : FreeCastStaff("Silvermelt", Tags.Fire, 60, Spells.MercurizeSpell),
	lambda : FreeCastStaff("Sorcwinter", Tags.Sorcery, 75, Spells.DeathChill),
	lambda : FreeCastStaff("The Dynamo", Tags.Lightning, 40, Spells.AnnihilateSpell),
	lambda : FreeCastStaff("The Blazeloom", Tags.Enchantment, 50, Spells.Blazerip),
	lambda : FreeCastStaff("Starblesser", Tags.Arcane, 40, Spells.HolyBlast),
	lambda : FreeCastStaff("The Sparkloom", Tags.Enchantment, 50, Spells.LightningBoltSpell),
	lambda : FreeCastStaff("Wintersting", Tags.Ice, 30, Spells.PoisonSting),
	lambda : FreeCastStaff("Red Majesty", Tags.Blood, 30, Spells.ScourgeSpell),

	lambda : SummonOnDeathStaff(FireBomber, "Blastmaker"),
	lambda : SummonOnDeathStaff(FireFlies, "Embermaker"),
	lambda : SummonOnDeathStaff(Mantis, "Mantismaker"),
	lambda : SummonOnDeathStaff(Spriggan, "Sprigganmaker"),
	lambda : SummonOnDeathStaff(RandomImp, "Impmaker", monster_name="random imp", duration=5),

	Crackledark,
	ScepterOfSorrows,
	GlassAnimaStaff,
	QuillStaff,
]

Robes = [
	RobeOfIce,
	RobeOfFire,
	RobeOfVoid,
	RobeOfStorms,
	RobeOfTheDruid,
	FaeRobe,
	VampiricVestments,
	DwarvenChainmail,
	ElvenChainmail,
	ArmorOfSouls,
	BasiliskScaleMail,
	EarthtrollArmor,
	StormtrollArmor,
	RobeOfTwilight,
	RobeOfAgony,
	RobeOfFrostfire,
	RobeOfCrystals
]

Hats = [
	HunterCrown,
	WarlordCrown,
	SpiritVisor,
	MemoryHelm,
	CannibalCrown,
	# TODO- some helmets that give resistances or something

	HelmOfTheHost,
	MaskOfIcyChill,
	StoneMask,
	EyeHelm,

	lambda : TagHelm(Tags.Fire),
	lambda : TagHelm(Tags.Ice),
	lambda : TagHelm(Tags.Lightning),
	lambda : TagHelm(Tags.Dark),
	lambda : TagHelm(Tags.Nature),
	lambda : TagHelm(Tags.Holy),
	lambda : TagHelm(Tags.Arcane),
	lambda : TagHelm(Tags.Metallic),

	lambda : GenericFrenzyMask(Tags.Fire),
	lambda : GenericFrenzyMask(Tags.Ice),
	lambda : GenericFrenzyMask(Tags.Arcane),

	lambda : SeasonCrown("Summer Crown", FireFlies, 11, FireSpirit, 4, Tags.Fire),
	lambda : SeasonCrown("Winter Crown", Yeti, 2, StormSpirit, 3, Tags.Ice),
	lambda : SeasonCrown("Spring Crown", Gnome, 7, Mycobeast, 2, Tags.Arcane),
	lambda : SeasonCrown("Autumn Crown", Raven, 7, Witch, 4, Tags.Dark),

	BloodspikeHelm
]

Boots = [
	Earthboots,
	
	#ThunderingHooves,
	TravellersBoots,
	HedgewizShoes,
	TimeStriders,
	
	DrillShoes,
	WingedBoots,

	#BootsOfDramaticArrival  # Disabling until I can figure out why it crashes, cool idea tho

	SilkenSandals,
	SnowShoes,
	TranslocationBoots,

	lambda : SummonShoes(8, Gnome, "Gnome Shoes"),
	lambda : SummonShoes(6, GreenSlime, "Slime Shoes"),
	lambda : SummonShoes(4, Kobold, "Kobold Clogs"),
	lambda : SummonShoes(11, Ogre, "Ogre Boots"),
	lambda : SummonShoes(4, Ghost, "Ghost Slippers"),

	lambda : SpellBoots("Storm Boots", Spells.StormNova, 15),
	lambda : SpellBoots("Exploding Boots", Spells.FlameBurstSpell, 15)
]

Amulets = [
	FingerSix,
	Ankh,
	Drakentooth,
	EyeNecklace,
	AmberCube,
	SkullNecklace,
	RedObsidianShard,
	JadeShard,
	RealityAnchor,
	AmuletOfUndeath,
	VialOfAmbrosia,
	AmuletOfEmeraldFlame,
	MonkeySkull,
	Bloodruby,

	# Sometimes these come in normal chests
	RandomLittleRing,
	RandomLittleRing,
	RandomLittleRing,

	RandomSheild,
	RandomSheild,
	RandomSheild,

	lambda : ThornItem("Bramblethorn", Tags.Physical),
	lambda : ThornItem("Toadthorn", Tags.Poison),
	lambda : ThornItem("Devilthorn", Tags.Fire),

	lambda : DamageToPetsAmulet("Witch Whistle", 100, Tags.Dark, Witch),
	lambda : DamageToPetsAmulet("Snowy Fursphere", 300, Tags.Ice, Yeti),
	lambda : DamageToPetsAmulet("Living Emberstone", 100, Tags.Fire, FireSpirit),

	lambda : PrinceOfRuinLike("Silken Links", [Tags.Poison, Tags.Arcane]),
	lambda : PrinceOfRuinLike("Winter Links", [Tags.Ice, Tags.Dark]),
	lambda : PrinceOfRuinLike("Wrath Links", [Tags.Holy, Tags.Lightning]),

	lambda : JarOfBossness("Jar of Trollblood", BossSpawns.Trollblooded),
	lambda : JarOfBossness("Jar of Embers", BossSpawns.Flametouched, Tags.Fire),
	#lambda : JarOfBossness("Jar of Moonlight", BossSpawns.Lycanthrope),
	lambda : JarOfBossness("Jar of Quicksilver", BossSpawns.Metallic, Tags.Metallic),
	lambda : JarOfBossness("Jar of Ectoplasm", BossSpawns.Ghostly, Tags.Undead),

	lambda : CursePipe("Poison Pipe", Poison, 3, 3, 3, Tags.Poison),
	lambda : CursePipe("Time Pipe", Stun, 3, 7, 10, Tags.Arcane),
	lambda : CursePipe("Ink Pipe", BlindBuff, 4, 2, 3, Tags.Dark),
	lambda : CursePipe("Ice Pipe", FrozenBuff, 4, 2, 6, Tags.Ice),

	#lambda : CoilOfCharging("Embersnow Coil", Tags.Fire, Tags.Ice),
	#lambda : CoilOfCharging("Glimmerspark Coil", Tags.Arcane, Tags.Lightning),
	#lambda : CoilOfCharging("Witherbloom Coil", Tags.Dark, Tags.Nature),
	#lambda : CoilOfCharging("Scalesmith Coil", Tags.Dragon, Tags.Metallic),
	#lambda : CoilOfCharging("Goldweave Coil", Tags.Holy, Tags.Enchantment),

	lambda : CurseDoll("Purple", Tags.Arcane, Spells.MagicMissile),
	lambda : CurseDoll("Ugly", Tags.Holy, Spells.CallSpirits),
	lambda : CurseDoll("Red", Tags.Demon, Spells.AnnihilateSpell)
]

class PetCollar(Equipment):

	def __init__(self, spawn_fn):
		self.spawn_fn = spawn_fn
		self.example = spawn_fn()
		Equipment.__init__(self)


	def on_init(self):
		self.name = self.example.name
		self.description = "Start each level with a %s" % self.example.name
		self.owner_triggers[EventOnUnitAdded] = self.on_add
		self.slot = ITEM_SLOT_AMULET

	def on_add(self, evt):
		monster = self.spawn_fn()
		apply_minion_bonuses(self, monster)
		self.summon(monster)

	def get_extra_examine_tooltips(self):
		return [self.spawn_fn()]

class PetSigil(Equipment):

	def __init__(self, spawn_fn):
		self.spawn_fn = spawn_fn
		self.example = spawn_fn()
		Equipment.__init__(self)

	def on_init(self):
		self.name = "%s Sigil" % self.example.name
		self.description = "Start each level with a %s spawner" % self.example.name
		self.owner_triggers[EventOnUnitAdded] = self.on_add
		self.slot = ITEM_SLOT_AMULET
		self.asset_name = "trinket_sigil"

	def on_add(self, evt):
		monster = MonsterSpawner(self.spawn_fn)
		apply_minion_bonuses(self, monster)
		self.summon(monster)

	def get_extra_examine_tooltips(self):
		return [self.spawn_fn()]

# Tag, Name, Weight
ring_tags = [
	(Tags.Fire, "Fiery", 1),
	(Tags.Ice, "Icy", 1),
	(Tags.Lightning, "Electric", 1),
	(Tags.Nature, "Living", 1),
	(Tags.Dark, "Sinister", 1),
	(Tags.Holy, "Golden", 1),
	(Tags.Arcane, "Mystic", 1),
	(Tags.Sorcery, "Sorcerous", 1),
	(Tags.Enchantment, "Enchanting", 1),
	(Tags.Conjuration, "Conjured", 1)
]

ring_tag_weights = [r[2] for r in ring_tags]

# Stat, 
ring_stats = [
	("damage", "dagger", 3, 1.5),
	("damage", "orb", 0.25, 1.2),
	("max_charges", "tome", 1, .75),
	("range", "lens", 1, 1),
	("num_summons", "flag", 1, .5),
	("radius", "disk", 1, .5),
	("minion_health", "scale", .25, .5),
	("minion_damage", "claw", .25, .5),
	("minion_damage", "fang", 3, .5),
	("duration", "hourglass", .25, .75),
	("minion_duration", "horn", 4, .25)
]

ring_stat_weights = [r[3] for r in ring_stats]

def ring_chest(difficulty, prng=random):
	num_rings = CHEST_SIZE + 2

	roll = prng.random()
	shop = Shop()

	# Fixed attr
	if roll < .5:
		stat, stat_name, stat_amt, _ = random.choices(ring_stats, weights=ring_stat_weights, k=1)[0]
		shop.name = "%s Chest" % stat_name.capitalize()

		tag_tups = random.sample(ring_tags, k=num_rings)

		items = [RandomLittleRing(forced_stat_tup=(stat, stat_name, stat_amt), forced_tag_tup=tag_tup[:2]) for tag_tup in tag_tups]

	# Fixed tag
	else:
		tag, tag_name, _ = random.choices(ring_tags, weights=ring_tag_weights, k=1)[0]
		shop.name = "%s Trinket Chest" % tag_name

		stat_tups = random.sample(ring_stats, k=num_rings)
		items = [RandomLittleRing(forced_tag_tup=(tag, tag_name), forced_stat_tup=stat_tup[:3]) for stat_tup in stat_tups]
		
	content_str = '\n'.join(" %s" % i.name for i in items)
	shop.description = "Obtain one of:\n%s" % content_str

	shop.items = items
	shop.asset = ['tiles', 'chest', 'trinket_chest']
	return shop

all_items = Staves + Robes + Hats + Boots + Amulets

hat_tag_names = [
	(Tags.Fire, "flame"),
	(Tags.Physical, "force"),
	(Tags.Lightning, "spark"),
	(Tags.Dark, "dark"),
	(Tags.Poison, "toxin"),
	(Tags.Ice, "ice"),
	(Tags.Holy, "gold"),
	(Tags.Arcane, "star"),
]

def damage_hat_chest(level, prng):

	shop = Shop()
	shop.name = "Box of Wizard Caps"

	shop.items = [ConversionHat() for i in range(4)]
	content_str = '\n'.join(" %s" % i.name for i in shop.items)
	shop.description = "Obtain one of:\n%s" % content_str

	shop.asset = ['tiles', 'chest', 'wizard_hat_chest']

	return shop

def get_forced_equip():

	assert('forceequip' in sys.argv)
	forced_item_arg = sys.argv[sys.argv.index('forceequip')+1]

	forced_item_arg = forced_item_arg.replace('_', ' ')

	for item in all_items:
		i = item()
		if forced_item_arg in i.name.lower():
			return i

	# Crash if the item isnt found, its debug anyway
	assert(False)


def roll_equipment(difficulty):
	category = random.choice([Staves, Robes, Hats, Boots, Amulets])
	return random.choice(category)()

def roll_staff(difficulty, prng=random):
	# For now return random staff.  Maybe break them out into freeproc staves, attr staffs, random wands, ect later.
	return prng.choice(Staves)()

def roll_armor(difficulty, prng=random):
	# For now return random armor.
	return prng.choice(Robes)()

def roll_shoes(difficulty, prng=random):
	# For now return random boots.
	return prng.choice(Boots)()

def roll_trinket(difficulty, prng=random):
	# 50-50 named trinket vs random generic trinket
	roll = prng.random()

	if roll < .5:
		return prng.choice(Amulets)()
	elif roll < .60:
		return RandomSheild()
	elif roll < .65:
		return roll_crown(difficulty, prng)
	else:
		return RandomLittleRing()

def roll_crown(difficulty, prng=random):
	min_level, max_level = get_spawn_min_max(difficulty+2)
	cur_options = [s for (s, l) in spawn_options if min_level <= l <= max_level]
	return PetSigil(random.choice(cur_options))

# Create a random hat for a hat box or treasure chest
def roll_hat(difficulty, prng=random):
	roll = prng.random()

	# 35% chance of damage cap
	if roll < .35:
		return ConversionHat()
	# 30% random chance named hat
	else:
		return random.choice(Hats)()

# Chest full of crowns
def crown_chest(difficulty, prng):

	items = []
	while len(items) < CHEST_SIZE:
		item = roll_crown(difficulty, prng)
		if item.name not in [i.name for i in items]:
			items.append(item)

	shop = Shop()
	shop.name = "Sigil Chest"
	shop.items = items
	shop.asset = ['tiles', 'chest', 'crown_chest']

	return shop

# Chest full of hats.
def hat_chest(difficulty, prng=random):
	items = []

	while len(items) < CHEST_SIZE:
		item = roll_hat(difficulty, prng)
		if item.name in set(i.name for i in items):
			continue
		items.append(item)

	shop = Shop()
	shop.name = "Hat Chest"
	shop.items = items
	shop.asset = ['tiles', 'chest', 'chest']

	return shop

def staff_chest(difficulty, prng=random):
	items = []

	while len(items) < CHEST_SIZE:
		item = roll_staff(difficulty, prng)
		if item.name in [i.name for i in items]:
			continue
		items.append(item)

	shop = Shop()
	shop.name = "Staff Chest"
	shop.items = items
	shop.asset = ['tiles', 'chest', 'wand_chest']

	return shop

def armor_chest(difficulty, prng=random):
	items = []

	while len(items) < CHEST_SIZE:
		item = roll_armor(difficulty, prng)
		if item.name in [i.name for i in items]:
			continue
		items.append(item)

	shop = Shop()
	shop.name = "Armor Chest"
	shop.items = items
	shop.asset = ['tiles', 'chest', 'armor_chest']

	return shop

def shoe_chest(difficulty, prng=random):
	items = []

	while len(items) < CHEST_SIZE:
		item = roll_shoes(difficulty, prng)
		if item.name in [i.name for i in items]:
			continue
		items.append(item)

	shop = Shop()
	shop.name = "Shoe Box"
	shop.items = items

	# TODO- shoe box asset
	shop.asset = ['tiles', 'chest', 'chest']

	return shop

def trinket_chest(difficulty, prng=random):
	items = []

	while len(items) < CHEST_SIZE + 1:
		item = roll_trinket(difficulty, prng)
		if item.name in [i.name for i in items]:
			continue
		items.append(item)

	shop = Shop()
	shop.name = "Trinket Box"
	shop.items = items

	# TODO- shoe box asset
	shop.asset = ['tiles', 'chest', 'chest']

	return shop
# Chest full of completely random stuff
# TODO- controlled chances per slot?
#  Maybe make a staff chest, armor chest, hat chest, boot chest, and amulet chest, and sample from each with % chance?
def treasure_chest(difficulty, prng=random):
	items = Staves + Robes + Hats + Boots + Amulets
	k = CHEST_SIZE + 1
	prng.shuffle(items)
	items = items[:k]
	items = [i() for i in items]

	shop = Shop()
	shop.name = "Treasure Chest"
	content_str = '\n'.join(" %s" % i.name for i in items)
	shop.description = "Obtain one of:\n%s" % content_str

	shop.items = items
	shop.asset = ['tiles', 'chest', 'chest']
	return shop

def mini_treasure_chest(difficulty, prng=random):

	items = []
	while len(items) < CHEST_SIZE:
		roll = prng.random()
		if roll < .25:
			item = roll_hat(difficulty, prng)
		elif roll < .5:
			item = roll_staff(difficulty, prng)
		elif roll < .85:
			item = roll_armor(difficulty, prng)
		else:
			item = roll_shoes(difficulty, prng)
		if item.name not in [i.name for i in items]:
			item.slot = ITEM_SLOT_AMULET
			item.name = "Mini %s" % item.name
			items.append(item)

	shop = Shop()
	shop.name = "Miniature Treasure Chest"
	shop.items = items
	shop.asset = ['tiles', 'chest', 'chest']
	return shop

def exotic_pet_chest(difficulty, prng):
	min_level, max_level = get_spawn_min_max(difficulty + 2)
	pet_level = max_level
	cur_options = [s for (s, l) in spawn_options if pet_level <= l <= pet_level]
	k = CHEST_SIZE

	random.shuffle(cur_options)
	monster_opts = cur_options[:k]

	final_opts = []

	for m in monster_opts:
		v = random.choice(BossSpawns.modifiers)[0]
		final_opts.append(lambda m=m, v=v: BossSpawns.apply_modifier(v, m(), apply_hp_bonus=True))

	items = [PetCollar(o) for o in final_opts]

	shop = Shop()
	shop.name = "Exotic Pet Shop"	
	content_str = '\n'.join(" %s" % i().name for i in monster_opts)
	shop.description = "Obtain one of:\n%s" % content_str
	shop.items = items
	shop.asset = ['tiles', 'chest', 'menagerie_icon']

	return shop

def test_equipment():
	for item in all_items:
		item = item()
		assert(item.name)
		assert(item.name != "Unnamed buff")
		assert(item.slot >= 0)
		if item.global_triggers or item.owner_triggers:
			assert(item.get_description())

def print_item_blurbs():
	for item in all_items:
		item = item()

		asset = ['tiles', 'items', 'equipment', item.name.lower().replace(' ', '_')]
		# use generic trinket asset if specific asset is not present
		theoretical_fn = os.path.join('rl_data', *asset) + '.png'
		if os.path.exists(theoretical_fn):
			continue

		print(item.name)
		if item.slot == ITEM_SLOT_AMULET:
			slot_str = "Amulet"
		elif item.slot == ITEM_SLOT_STAFF:
			slot_str = "Staff"
		elif item.slot == ITEM_SLOT_HEAD:
			slot_str = "Helmet"
		elif item.slot == ITEM_SLOT_ROBE:
			slot_str = "Robe"
		elif item.slot == ITEM_SLOT_BOOTS:
			slot_str = "Boots"
		print(slot_str)

		print(item.get_description())

		for attr, bonus in item.global_bonuses.items():
			print("+%d %s" % (bonus, attr))

		for attr, bonus in item.global_bonuses_pct.items():
			print("+%d%% %s" % (bonus, attr))

		for tag in item.tag_bonuses:
			for attr, bonus in item.tag_bonuses[tag].items():
				print("+%d %s for %s" % (bonus, attr, tag.name))

		for tag in item.tag_bonuses_pct:
			for attr, bonus in item.tag_bonuses_pct[tag].items():
				print("+%d%% %s for %s" % (bonus, attr, tag.name))

		for tag, resist in item.resists.items():
			print("%d%% resist %s" % (resist, tag.name))



		print('\n')

if __name__ == "__main__":
	#roll_equipment(5)
	#test_equipment()
	#print_item_blurbs()
	for i in range(100):
		ring_chest(5)