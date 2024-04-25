from Level import *
from Upgrades import *
from Spells import *
from Consumables import *
import random
from collections import OrderedDict
from Monsters import *
from Variants import *
from RareMonsters import *
from Equipment import *

import os

def random_spell_tag():
	roll = random.random()
	if roll < .50:
		return random.choice([Tags.Fire, Tags.Lightning, Tags.Dark, Tags.Arcane, Tags.Nature, Tags.Holy, Tags.Ice])
	if roll < .85:
		return random.choice([Tags.Sorcery, Tags.Enchantment, Tags.Conjuration])
	else:
		return random.choice([Tags.Word, Tags.Dragon, Tags.Translocation, Tags.Eye, Tags.Chaos, Tags.Orb, Tags.Metallic, Tags.Blood])

def hp_shrine(difficulty, prng):
	shrine = HeartDot(25)
	return shrine

def library(level=None):
	lib = PlaceOfPower(random_spell_tag())
	return lib


class Shrine(object):

	def __init__(self):
		self.name = "Unnamed Shrine"
		self.description = None
		self.tags = []
		self.conj_only = False
		self.no_conj = False
		self.attr_bonuses = {}
		self.buff_class = ShrineBuff
		self.on_init()

	def get_description(self):

		def get_bonus_str(attr, amt):
			if isinstance(amt, float):
				return "+[%d%%_%s:%s]" % (amt*100, attr, attr)
			else:
				return "+[%d_%s:%s]" % (amt, attr, attr)

		bonus_list = [get_bonus_str(attr, amt) for (attr, amt) in self.attr_bonuses.items()]
		if self.description:
			bonus_list = bonus_list + [self.description]

		tags_str = " or ".join('[' + t.name.lower() + ']' for t in self.tags)
		spell_str = "spell"
		if self.conj_only:
			spell_str = "[conjuration] spell"
		target_str = "%s %s" % (tags_str, spell_str) if tags_str else spell_str

		fmt = "Enhances %s with:\n%s" % (target_str, '\n'.join(bonus_list))
		fmt += "\nLimit 1 shrine per spell."
		if self.no_conj:
			fmt += "\nCan be applied only to [sorcery] and [enchantment] spells."

		return fmt

	def on_init(self):
		pass

	def can_enhance(self, spell):
		if self.conj_only and Tags.Conjuration not in spell.tags:
			return False
		if self.no_conj and Tags.Conjuration in spell.tags and Tags.Sorcery not in spell.tags and Tags.Enchantment not in spell.tags:
			return False
		if self.tags and not any(t in self.tags for t in spell.tags):
			return False
		# Hacky- assume any shrine with a description has benefits beyond attr bonuses
		# Could also maybe check if buff class is ShrineBuff or no?
		if not self.description and self.attr_bonuses and not any(hasattr(spell, a) for a in self.attr_bonuses):
			return False
		return True

	def get_buff(self, spell):
		buff = self.buff_class(spell, self)
		for (attr, amt) in self.attr_bonuses.items():
			if not hasattr(spell, attr):
				continue
			if isinstance(amt, float):
				amt = math.ceil(getattr(spell, attr) * amt)
			buff.spell_bonuses[type(spell)][attr] = amt

		return buff

	def get_buffs(self, player):
		for s in player.spells:
			if self.can_enhance(s):
				yield self.get_buff(s)

class ShrineBuff(Upgrade):
	def __init__(self, spell, shrine):

		self.spell_class = type(spell)
		self.spell_level = spell.level
		
		Upgrade.__init__(self)
		
		self.shrine_name = shrine.name

		self.name = "%s Attunement (%s)" % (shrine.name, spell.name)
		self.description = self.description or shrine.description

		self.prereq = spell
		self.level = 0 # ugh
		self.tags = []
		self.buff_type = BUFF_TYPE_PASSIVE
		
	# Return true if the spell is the enhanced spell- 
	# if allow minions is true, also returns true if the spell is owned by a minion summoned by the enhanced spell
	def is_enhanced_spell(self, source, allow_minion=True):
		if not source or not source.owner:
			return False

		if allow_minion:
			if source.owner and source.owner.source and type(source.owner.source) == self.spell_class:
				return True

		# Do not return true for enemies- but do return true for allies (say, dragon mages) casting the spell
		if are_hostile(source.owner, self.owner):
			return False

		if type(source) == self.spell_class:
			return True

		return False


class CallingShrine(Shrine):

	def on_init(self):
		self.name = "Calling"
		self.conj_only = True
		self.attr_bonuses['num_summons'] = .5
		self.attr_bonuses['minion_duration'] = 3

class LifeBuff(ShrineBuff):
	def on_init(self):
		self.owner_triggers[EventOnSpellCast] = self.on_spell_cast

	def on_spell_cast(self, evt):
		if type(evt.spell) == self.spell_class:
			self.owner.deal_damage(-5*self.spell_level, Tags.Heal, self)

class LifeShrine(Shrine):

	def on_init(self):
		self.name = "Life"
		self.tags = [Tags.Holy, Tags.Nature]
		self.description = "Heal for 5 HP on cast"
		self.buff_class = LifeBuff

class OtherworldyShrineBuff(ShrineBuff):

	def on_init(self):
		self.spell_conversions[self.spell_class][Tags.Arcane][Tags.Holy] = .50
		self.spell_conversions[self.spell_class][Tags.Arcane][Tags.Dark] = .50

class OtherworldlyShrine(Shrine):

	def on_init(self):
		self.name = "Otherworldly"
		self.tags = [Tags.Arcane]
		self.no_conj = True
		self.description = "Half of all [arcane] damage dealt by this spell is redealt as [holy] damage, and then again as [dark] damage."
		self.buff_class = OtherworldyShrineBuff

class RedFlameShrine(Shrine):

	def on_init(self):
		self.name = "Red Flame"
		self.tags = [Tags.Fire]
		self.attr_bonuses['damage'] = .5
		self.attr_bonuses['radius'] = 1
		self.attr_bonuses['max_charges'] = .15

class OnKillShrineBuff(ShrineBuff):

	def on_init(self):
		self.global_triggers[EventOnDeath] = self.on_death

	def on_death(self, evt):
		# Todo- minions?
		if not evt.damage_event:
			return
		if type(evt.damage_event.source) == self.spell_class:
			self.on_kill(evt.unit)

	def on_kill(self, unit):
		pass

class DamageCounterShrineBuff(ShrineBuff):

	def __init__(self, spell, shrine):
		self.counter_max = 20
		ShrineBuff.__init__(self, spell, shrine)
		self.global_triggers[EventOnDamaged] = self.on_damaged
		self.counter = 0
		self.targets = []

	# Clear target list each turn- dont spawn things on things that were dealt damage on previous turns
	def on_advance(self):
		self.targets = []

	def on_damaged(self, evt):
		if not evt.source:
			return

		if not self.is_enhanced_spell(evt.source, allow_minion=True):
			return

		self.counter += evt.damage
		if evt.unit not in self.targets:
			self.targets.append(evt.unit)
		
		if self.counter > self.counter_max:
			while self.counter > self.counter_max:
				target = random.choice(self.targets)
				self.owner.level.queue_spell(self.trigger(target))
				self.counter -= self.counter_max
			self.targets.clear()

			# If there is any damage remaining, it must be from the most recent damage event, so keep the most recent unit
			if self.counter > 0:
				self.targets.append(evt.unit)

	def trigger(self, target):
		pass

class StormCloudShrineBuff(ShrineBuff):

	def on_init(self):
		self.global_triggers[EventOnDamaged] = self.on_damage


	def on_damage(self, evt):
		if not evt.source:
			return
		if not isinstance(evt.source, self.spell_class):
			return
		if not evt.source.owner == self.owner:
			return

		if type(self.owner.level.tiles[evt.unit.x][evt.unit.y].cloud) in [StormCloud, BlizzardCloud]:
			self.owner.level.queue_spell(self.deal_damage(evt))

	def deal_damage(self, evt):
		dmg = math.ceil(evt.damage * .75)
		evt.unit.deal_damage(dmg, Tags.Lightning, self)
		yield
		yield
		yield
		evt.unit.deal_damage(dmg, Tags.Ice, self)
		yield

class StormCloudShrine(Shrine):

	def on_init(self):
		self.name = "Storm Cloud"
		self.description = "On damaging an enemy in a thunderstorm or blizzard, redeal 75% of the damage as [lightning] and 75% of the damage as [ice]."
		self.tags = [Tags.Lightning, Tags.Ice]
		self.buff_class = StormCloudShrineBuff
		self.no_conj = True

class ShrineSummonBuff(ShrineBuff):

	def on_init(self):
		self.global_triggers[EventOnUnitAdded] = self.on_unit_add

	def on_unit_add(self, evt):
		if not isinstance(evt.unit.source, self.spell_class):
			return
		if evt.unit.source.owner != self.owner:
			return

		self.on_summon(evt.unit)

	def on_summon(self):
		assert(False)

class OakenShrineBuff(ShrineSummonBuff):

	def on_summon(self, unit):
		unit.resists[Tags.Physical] += 50
		unit.resists[Tags.Holy] += 50

class OakenShrine(Shrine):

	def on_init(self):
		self.name = "Oaken"
		self.attr_bonuses['minion_health'] = .25
		self.attr_bonuses['minion_damage'] = .1
		self.description = "Summoned minions gain [50_physical:physical] resist and [50_holy:holy] resist."
		self.tags = [Tags.Holy, Tags.Nature]
		self.conj_only = True
		self.buff_class = OakenShrineBuff

class AfterlifeShrineBuff(ShrineSummonBuff):

	def on_summon(self, unit):
		if hasattr(unit, 'afterlife_buffed'):
			return
		unit.afterlife_buffed = True
		existing = unit.get_buff(ReincarnationBuff)
		if existing:
			existing.lives += 1
		unit.apply_buff(ReincarnationBuff(1))

class AfterlifeShrine(Shrine):

	def on_init(self):
		self.name = "Afterlife"
		self.conj_only = True
		self.buff_class = AfterlifeShrineBuff
		self.description = "Summoned minions reincarnate once"

class StillnessShrine(Shrine):

	def on_init(self):
		self.name = "Stillness"
		self.tags = [Tags.Ice, Tags.Arcane]
		self.attr_bonuses['duration'] = 1.0
		self.no_conj = True

class FrozenSkullShrineBuff(OnKillShrineBuff):

	def on_kill(self, unit):
		targets = self.owner.level.get_units_in_los(unit)
		targets = [t for t in targets if are_hostile(self.owner, t)]
		choices = random.choices(targets, k=min(len(targets), 4))
		for u in choices:
			u.apply_buff(FrozenBuff(), 2)

class FrozenSkullShrine(Shrine):

	def on_init(self):
		self.name = "Frozen Skull"
		self.attr_bonuses['damage'] = .2
		self.tags = [Tags.Dark, Tags.Ice]
		self.description = "On kill, [freeze] up to [4:num_targets] enemies in line of sight of the slain unit for [2_turns:duration]."
		self.buff_class = FrozenSkullShrineBuff
		self.no_conj = True

class NightmareShrineBuff(ShrineBuff):

	def on_init(self):
		self.spell_conversions[self.spell_class][Tags.Dark][Tags.Arcane] = .5
		self.spell_conversions[self.spell_class][Tags.Arcane][Tags.Dark] = .5

class NightmareShrine(Shrine):

	def on_init(self):
		self.name = 'Nightmare'
		self.description = "Half of all [arcane] damage dealt by this spell is redealt as [dark] damage and vice versa."
		self.buff_class = NightmareShrineBuff
		self.tags = [Tags.Dark, Tags.Arcane]
		self.no_conj = True

class ThunderShrineBuff(ShrineBuff):

	def on_init(self):
		self.global_triggers[EventOnDamaged] = self.on_spell_cast

	def on_spell_cast(self, evt):
		if not isinstance(evt.source, self.spell_class):
			return
		if not evt.damage_type == Tags.Lightning:
			return
		if not evt.source.owner == self.owner:
			return

		for p in self.owner.level.get_points_in_ball(evt.unit.x, evt.unit.y, 1, diag=True):
			unit = self.owner.level.get_unit_at(p.x, p.y)	
			if unit and are_hostile(self.owner, unit):
				if unit.has_buff(Stun):
					continue
				unit.apply_buff(Stun(), 1)

class ThunderShrine(Shrine):

	def on_init(self):
		self.name = "Thunder"
		self.description = "Damaged enemies and enemies adjacent to them are [stunned] for [1_turn:duration]"
		self.buff_class = ThunderShrineBuff
		self.tags = [Tags.Lightning]
		self.attr_bonuses['damage'] = .2
		self.no_conj = True

class BurningBuff(Buff):

	def __init__(self, damage):
		self.damage = damage
		Buff.__init__(self)

	def on_init(self):
		self.name = "Burning (%d)" % self.damage
		self.description = "At end of this units turn, it takes %d damage and burning expires."
		self.asset = ['status', 'burning']

	def on_advance(self):
		self.owner.deal_damage(self.damage, Tags.Fire, self)
		self.owner.remove_buff(self)

class BurningShrineBuff(ShrineBuff):

	def on_init(self):
		self.global_triggers[EventOnDamaged] = self.on_damage

	def on_damage(self, evt):
		if not isinstance(evt.source, self.spell_class) or evt.source.owner != self.owner:
			return
		evt.unit.apply_buff(BurningBuff(evt.damage))

class BurningShrine(Shrine):

	def on_init(self):
		self.name = "Burning"
		self.description = "Whenever this spell deals damage to an enemy, that enemy takes that much damage again as [fire] damage at the end of it's next turn."
		self.tags = [Tags.Fire]
		self.buff_class = BurningShrineBuff
		self.no_conj = True

class CruelShrineBuff(ShrineBuff):

	def on_init(self):
		self.global_triggers[EventOnDamaged] = self.on_damage

	def on_damage(self, evt):
		if self.is_enhanced_spell(evt.source, allow_minion=True):
			evt.unit.apply_buff(Poison(), evt.damage)

class CruelShrine(Shrine):

	def on_init(self):
		self.name = "Cruel"
		self.tags = [Tags.Dark]
		self.description = "Whenever this spell or a minion it summoned deals damage to an enemy, that enemy is [poisoned] for that many turns."
		self.buff_class = CruelShrineBuff

class TormentShrine(Shrine):

	def on_init(self):
		self.name = "Torment"
		self.tags = [Tags.Dark]
		self.attr_bonuses['damage'] = .50
		self.attr_bonuses['max_charges'] = 2

class MysticShrine(Shrine):

	def on_init(self):
		self.name = "Mystic"
		self.tags = [Tags.Arcane]
		self.attr_bonuses['range'] = 3
		self.attr_bonuses['max_charges'] = .5

class IcyShrine(Shrine):

	def on_init(self):
		self.name = "Icy"
		self.tags = [Tags.Ice]
		self.attr_bonuses['damage'] = .4
		self.attr_bonuses['duration'] = 3

class WhiteCandleShrineBuff(ShrineSummonBuff):

	def on_summon(self, unit):
		dtype = random.choice([Tags.Holy, Tags.Fire])
		damage = unit.source.get_stat('minion_damage')
		damage = max(1, damage)
		bolt = SimpleRangedAttack(damage=damage, damage_type=dtype, range=4)
		bolt.name = "Candle Bolt"
		bolt.cool_down = 2
		unit.add_spell(bolt, prepend=True)

class WhiteCandleShrine(Shrine):

	def on_init(self):
		self.name = "White Candle"
		self.conj_only = True
		self.buff_class = WhiteCandleShrineBuff
		self.description = "The chosen spell's summoned minions randomly gain a [holy] or [fire] bolt attack.  The attack deals damage equal to the spells minion damage stat, has a [2_turn:cooldown] cooldown and has a range of [4_tiles:range]."
		self.tags = [Tags.Fire, Tags.Holy]

class FrostfireShrineBuff(ShrineBuff):

	def on_init(self):
		self.spell_conversions[self.spell_class][Tags.Fire][Tags.Ice] = .5
		self.spell_conversions[self.spell_class][Tags.Ice][Tags.Fire] = .5

class FrostfireShrine(Shrine):

	def on_init(self):
		self.name = "Frostfire"
		self.description = "Half of all [ice] damage dealt by this shrine is redealt as [fire] damage and vice versa."
		self.buff_class = FrostfireShrineBuff
		self.tags = [Tags.Fire, Tags.Ice]
		self.no_conj = True

class FaeShrineHeal(HealAlly):
	pass

class FaeShrineBuff(ShrineSummonBuff):

	def on_summon(self, unit):

		phasing = TeleportyBuff()
		unit.apply_buff(phasing)

		heal = FaeShrineHeal(2 + self.spell_level, range=4)
		heal.name = "Fae Heal"
		heal.cool_down = 3
		unit.add_spell(heal, prepend=True)

class FaeShrine(Shrine):

	def on_init(self):
		self.name = "Fae"
		self.buff_class = FaeShrineBuff
		self.description = "Summoned minions gain a healing spell and passive short range teleportation.  The healing spell heals 2 plus the spell's level HP, and has a [4_tile:range] range."
		self.tags = [Tags.Nature, Tags.Arcane]
		self.conj_only = True

class Enveloping(Shrine):

	def on_init(self):
		self.name = "Enveloping"
		self.attr_bonuses['radius'] = 2

class Memory(Shrine):

	def on_init(self):
		self.name = "Memory"
		self.attr_bonuses['max_charges'] = 1.0

class LifeShrineBuff(ShrineSummonBuff):

	def on_summon(self, unit):
		regen = RegenBuff(4)
		regen.buff_type = BUFF_TYPE_PASSIVE
		unit.apply_buff(regen)

class LifeShrine(Shrine):

	def on_init(self):
		self.name = "Life"
		self.description = "Summoned minions heal for [4_HP:heal] each turn."
		self.buff_class = LifeShrineBuff
		self.tags = [Tags.Nature, Tags.Holy]
		self.conj_only = True

class TundraShrineBuff(ShrineSummonBuff):

	def on_summon(self, unit):
		unit.resists[Tags.Ice] += 50
		icebolt = SimpleRangedAttack(damage=unit.source.get_stat('minion_damage'), range=self.spell_level + 1, damage_type=Tags.Ice)
		icebolt.name = "Tundra Bolt"
		icebolt.cool_down = 4
		unit.add_spell(icebolt, prepend=True)

class TundraShrine(Shrine):

	def on_init(self):
		self.name = "Tundra"
		self.tags = [Tags.Ice, Tags.Nature]
		self.buff_class = TundraShrineBuff
		self.description = "Summoned minions gain [50_ice:ice] resistance and a ranged attack.\nThe ranged attack deals [ice] damage equal to the spell's minion damage and has range equal to the spell's level."
		self.conj_only = True

class SwampShrineBuff(ShrineSummonBuff):

	def on_summon(self, unit):
		aura = DamageAuraBuff(damage=2, damage_type=Tags.Poison, radius=1+self.spell_level)
		aura.buff_type = BUFF_TYPE_PASSIVE
		aura.name = "Swamp Aura"
		unit.apply_buff(aura)
		unit.resists[Tags.Poison] = 100

class SwampShrine(Shrine):

	def on_init(self):
		self.name = "Swamp"
		self.conj_only = True
		self.buff_class = SwampShrineBuff
		self.description = "Summoned minions gain a [poison] damage aura and [100_poison:poison] resist.  The aura deals [2_poison:poison] damage to all enemies within the radius.  The radius is equal to the chosen spell's level plus 1."
		self.tags = [Tags.Nature, Tags.Dark]

class BlackSkyShrine(Shrine):

	def on_init(self):
		self.name = "Black Sky"
		self.tags = [Tags.Lightning, Tags.Dark]
		self.attr_bonuses['damage'] = .6
		self.attr_bonuses['max_charges'] = .3
		self.attr_bonuses['range'] = 2

class FrozenShrineBuff(ShrineBuff):

	def on_init(self):
		self.global_triggers[EventOnDamaged] = self.on_damage

	def on_damage(self, evt):
		if not evt.source:
			return

		sources = [evt.source]
		if evt.source.owner and evt.source.owner.source:
			sources.append(evt.source.owner.source)

		if not any(isinstance(source, self.spell_class) and source.owner == self.owner for source in sources):
			return

		if evt.damage_type != Tags.Ice:
			return

		evt.unit.apply_buff(FrozenBuff(), 2)

class FrozenShrine(Shrine):

	def on_init(self):
		self.name = "Frozen"
		self.tags = [Tags.Ice]
		self.buff_class = FrozenShrineBuff
		self.description = "[Ice] damage from this spell or minions summoned by this spell causes 2 turns of [freeze]."

class AngelicShrine(Shrine):

	def on_init(self):
		self.name = "Angelic"
		self.tags = [Tags.Holy]
		self.conj_only = True
		self.attr_bonuses['minion_duration'] = 7
		self.attr_bonuses['minion_damage'] = 7
		self.attr_bonuses['minion_health'] = 7
		self.attr_bonuses['max_charges'] = 1

class DemonBaneShrineBuff(OnKillShrineBuff):

	def on_kill(self, unit):
		if Tags.Demon in unit.tags:
			for spell in self.owner.spells:
				if isinstance(spell, self.spell_class):
					if spell.cur_charges < spell.get_stat('max_charges'):
						spell.cur_charges += 1

class DemonBaneShrine(Shrine):

	def on_init(self):
		self.name = "Demonbane"
		self.tags = [Tags.Holy, Tags.Fire, Tags.Lightning]
		self.description = "This spell regains 1 charge whenever it is used to kill a [demon]"
		self.buff_class = DemonBaneShrineBuff
		self.no_conj = True

class CracklingShrineBuff(ShrineBuff):

	def on_init(self):
		self.spell_conversions[self.spell_class][Tags.Fire][Tags.Lightning] = .5
		self.spell_conversions[self.spell_class][Tags.Lightning][Tags.Fire] = .5

class CracklingShrine(Shrine):

	def on_init(self):
		self.name = "Crackling"
		self.description = "Half of all [lightning] damage dealt by this shrine is redealt as [fire] damage and vice versa."
		self.tags = [Tags.Fire, Tags.Lightning]
		self.buff_class = CracklingShrineBuff
		self.no_conj = True

class SandStoneShrineBuff(ShrineSummonBuff):

	def on_summon(self, unit):
		unit.resists[Tags.Fire] += 50
		unit.resists[Tags.Physical] += 50

class SandStoneShrine(Shrine):

	def on_init(self):
		self.name = "Sandstone"
		self.tags = [Tags.Nature, Tags.Fire]
		self.attr_bonuses['minion_health'] = .75
		self.description = "Summoned minions gain [50_physical:physical] resist and [50_fire:fire] resist."
		self.buff_class = SandStoneShrineBuff
		self.conj_only = True

class CharredBoneShrineBuff(ShrineBuff):

	def on_init(self):
		self.global_triggers[EventOnDeath] = self.on_death


	def on_death(self, evt):
		if not evt.unit.source:
			return
		if not isinstance(evt.unit.source, self.spell_class):
			return
		if not evt.unit.source.owner == self.owner:
			return

		self.owner.level.queue_spell(self.do_damage(evt))

	def do_damage(self, evt):
		units = self.owner.level.get_units_in_ball(evt.unit, 4)
		units = [u for u in units if are_hostile(self.owner, u)]
		random.shuffle(units)
		for unit in units[:4]:
			for p in self.owner.level.get_points_in_line(evt.unit, unit)[1:-1]:
				self.owner.level.show_effect(p.x, p.y, Tags.Fire)
			unit.deal_damage(evt.unit.max_hp // 2, Tags.Fire, self)
			yield

class CharredBoneShrine(Shrine):

	def on_init(self):
		self.name = "Charred Bone"
		self.tags = [Tags.Fire, Tags.Dark]
		self.buff_class = CharredBoneShrineBuff
		self.description = "Whenever a minion summoned by this spell dies, it deals half its HP as [fire] damage to up to [4:num_summons] random enemy units up to [4_tiles:radius] away."
		self.conj_only = True

class RedStarShrineBuff(ShrineBuff):

	def on_init(self):
		self.global_triggers[EventOnDamaged] = self.on_damage

	def on_damage(self, evt):
		if not evt.source:
			return

		if not evt.unit.is_alive():
			return

		sources = [evt.source]
		if evt.source.owner and evt.source.owner.source:
			sources.append(evt.source.owner.source)

		if not any(isinstance(source, self.spell_class) and source.owner == self.owner for source in sources):
			return

		if Tags.Arcane in evt.unit.tags or Tags.Dark in evt.unit.tags or Tags.Fire in evt.unit.tags:
			self.owner.level.queue_spell(self.do_damage(evt.unit, evt.damage))

	def do_damage(self, unit, damage):
		unit.deal_damage(damage, Tags.Holy, self)
		yield

class RedStarShrine(Shrine):

	def on_init(self):
		self.name = "Red Star"
		self.description = "Redeals all damage dealt by this spell or minions it summons to [arcane], [dark], or [fire] units as [holy] damage."
		self.tags = [Tags.Fire, Tags.Arcane]
		self.buff_class = RedStarShrineBuff

class BlueSkyShrineBuff(ShrineSummonBuff):

	def on_summon(self, unit):
		unit.resists[Tags.Lightning] += 100
		unit.flying = True

		regen = RegenBuff(2)
		regen.buff_type = BUFF_TYPE_PASSIVE
		unit.apply_buff(regen)

class BlueSkyShrine(Shrine):

	def on_init(self):
		self.name = "Blue Sky"
		self.description = "Summoned minions gain [100_lightning:lightning] resist, [2_HP:heal] regeneration per turn, and flying."
		self.buff_class = BlueSkyShrineBuff
		self.tags = [Tags.Nature, Tags.Lightning]
		self.conj_only = True

class EnergyShrineBuff(OnKillShrineBuff):

	def on_kill(self, unit):
		self.owner.add_shields(1)

class EnergyShrine(Shrine):

	def on_init(self):
		self.name = "Energy"
		self.description = "On kill, gain [1_SH:shields]"
		self.attr_bonuses['max_charges'] = 1
		self.tags = [Tags.Arcane, Tags.Lightning]
		self.buff_class = EnergyShrineBuff
		self.no_conj = True

class SoulpowerBuff(Buff):

	def on_init(self):
		self.name = "Soulpower"
		self.global_bonuses['damage'] = 4
		self.color = Tags.Holy.color
		self.stack_type = STACK_INTENSITY
		self.asset = ['status', 'soulpower']


class SoulpowerShrineBuff(OnKillShrineBuff):

	def on_kill(self, unit):
		if Tags.Living in unit.tags or Tags.Demon in unit.tags:
			self.owner.apply_buff(SoulpowerBuff(), 10)

class SoulpowerShrine(Shrine):

	def on_init(self):
		self.name = "Soulpower"
		self.description = "Whenever you kill a [living] or [demon] unit with this spell, all your spells gain [4_damage:damage] for [10_turns:duration]."
		self.buff_class = SoulpowerShrineBuff
		self.tags = [Tags.Dark, Tags.Holy]
		self.no_conj = True

class GroveShrine(Shrine):

	def on_init(self):
		self.name = "Grove"
		self.tags = [Tags.Nature]
		self.attr_bonuses['duration'] = .5
		self.attr_bonuses['minion_duration'] = .5
		self.attr_bonuses['range'] = 2
		self.attr_bonuses['max_charges'] = .5

class BrightShrineBuff(ShrineBuff):

	def on_init(self):
		self.global_triggers[EventOnDamaged] = self.on_damage

	def on_damage(self, evt):
		if not evt.source:
			return
		if not isinstance(evt.source, self.spell_class):
			return
		if not evt.source.owner == self.owner:
			return

		evt.unit.apply_buff(BlindBuff(), 3)

class BrightShrine(Shrine):

	def on_init(self):
		self.name = "Bright"
		self.tags = [Tags.Holy, Tags.Lightning]
		self.description = "Damaged targets are [blinded] for [3_turns:duration]"
		self.buff_class = BrightShrineBuff
		self.no_conj = True

class ProtectionShrineBuff(ShrineSummonBuff):

	def on_init(self):
		ex = self.spell_class()
		self.num_shields = 1 if hasattr(ex, 'num_summons') else self.spell_level
		ShrineSummonBuff.on_init(self)

	def on_summon(self, unit):
		unit.add_shields(self.num_shields)

class ProtectionShrine(Shrine):

	def on_init(self):
		self.name = "Protection"
		self.description = "Chosen spells summoned minions gain shields.  Spells that summon multiple minions get [1_SH:shields], other spells get [1_SH:shields] per spell level."
		self.tags = [Tags.Arcane, Tags.Holy, Tags.Nature]
		self.conj_only = True
		self.buff_class = ProtectionShrineBuff

class GreyBoneShrineBuff(ShrineSummonBuff):

	def on_summon(self, unit):
		hp = max(1, unit.max_hp // 4)
		spawn = lambda : BoneShambler(hp)
		buff = SpawnOnDeath(spawn, 2)
		buff.apply_bonuses = False
		buff.buff_type = BUFF_TYPE_PASSIVE
		unit.apply_buff(buff)

class GreyBoneShrine(Shrine):

	def on_init(self):
		self.name = "Grey Bone"
		self.description = "Summoned minions split into [2:num_summons] bone shamblers on death.  Each bone shambler has 1/4th the HP of the original summon."
		self.conj_only = True
		self.buff_class = GreyBoneShrineBuff

class StoningShrineBuff(ShrineBuff):

	def on_init(self):
		self.global_triggers[EventOnDeath] = self.on_death

	def on_death(self, evt):
		if not evt.damage_event or not self.is_enhanced_spell(evt.damage_event.source, allow_minion=True):
			return

		enemies = [u for u in self.owner.level.get_units_in_los(evt.unit) if are_hostile(u, self.owner) and u != evt.unit]
		random.shuffle(enemies)
		for e in enemies[:2]:
			e.apply_buff(PetrifyBuff(), 3)

class StoningShrine(Shrine):

	def on_init(self):
		self.name = "Stoning"
		self.description = "Whenever this spell or a minion it summons kills an enemy unit, 2 random enemies in line of sight are [petrified] for [3_turns:duration]."
		self.tags = [Tags.Arcane, Tags.Holy, Tags.Dark]
		self.buff_class = StoningShrineBuff

class BerserkShrineBuff(ShrineBuff):

	def on_init(self):
		self.global_triggers[EventOnDamaged] = self.on_damage

	def on_damage(self, evt):
		if not evt.source:
			return
		if not isinstance(evt.source, self.spell_class):
			return
		if not evt.source.owner == self.owner:
			return

		evt.unit.apply_buff(BerserkBuff(), 1)

class BerserkShrine(Shrine):

	def on_init(self):
		self.name = "Berserk"
		self.description = "Damaged enemies go [berserk] for [1_turn:duration]"
		self.tags = [Tags.Fire, Tags.Lightning, Tags.Nature]
		self.buff_class = BerserkShrineBuff
		self.no_conj = True

class DragonHeartShrine(Shrine):

	def on_init(self):
		self.name = "Dragon Heart"
		self.attr_bonuses['minion_range'] = 2
		self.attr_bonuses['breath_damage'] = 10
		self.attr_bonuses['minion_health'] = .5
		self.tags = [Tags.Dragon]

class FarsightShrine(Shrine):

	def can_enhance(self, spell):
		if spell.melee:
			return False
		if spell.range < 1:
			return False
		return Shrine.can_enhance(self, spell)

	def on_init(self):
		self.name = "Farsight"
		self.tags = [Tags.Sorcery]
		self.attr_bonuses['range'] = .75

class EntropyBuff(Buff):

	def on_init(self):
		self.name = "Entropy"
		self.resists[Tags.Arcane] = -25
		self.resists[Tags.Dark] = -25
		self.buff_type = BUFF_TYPE_CURSE

class EntropyShrineBuff(ShrineBuff):

	def on_init(self):
		self.global_triggers[EventOnDamaged] = self.on_damage

	def on_damage(self, evt):
		if not evt.source:
			return
		if not isinstance(evt.source, self.spell_class):
			return
		if not evt.source.owner == self.owner:
			return

		evt.unit.apply_buff(EntropyBuff(), 10)

class EntropyShrine(Shrine):

	def on_init(self):
		self.name = "Entropy"
		self.description = "Damaged enemies gain a non-stacking -25 [dark] and [arcane] resist for [10_turns:duration]."
		self.buff_class = EntropyShrineBuff
		self.tags = [Tags.Lightning]
		self.no_conj = True 


class EnervationBuff(Buff):

	def on_init(self):
		self.name = "Enervation"
		self.resists[Tags.Fire] = -25
		self.resists[Tags.Lightning] = -25
		self.resists[Tags.Ice] = -25
		self.buff_type = BUFF_TYPE_CURSE


class EnervationShrineBuff(ShrineBuff):

	def on_init(self):
		self.global_triggers[EventOnDamaged] = self.on_damage

	def on_damage(self, evt):
		if not evt.source:
			return
		if not isinstance(evt.source, self.spell_class):
			return
		if not evt.source.owner == self.owner:
			return

		evt.unit.apply_buff(EnervationBuff(), 10)

class EnervationShrine(Shrine):

	def on_init(self):
		self.name = "Enervation"
		self.description = "Damaged enemies gain a non stacking -25 [fire], [lightning], and [ice] resist for [10_turns:duration]."
		self.buff_class = EnervationShrineBuff
		self.tags = [Tags.Arcane]
		self.no_conj = True 

class ImpShrineBuff(ShrineBuff):

	def on_init(self):
		self.owner_triggers[EventOnSpellCast] = self.on_spell_cast
		self.minion_duration = 17

	def on_spell_cast(self, evt):
		if type(evt.spell) == self.spell_class:
			self.owner.level.queue_spell(self.do_summons(evt))

	def do_summons(self, evt):
		for i in range(self.spell_level):
			unit = ChaosImp()
			# Make permenance and other global buffs work
			unit.turns_to_death = self.get_stat('minion_duration')
			unit.spells[0].damage += self.get_stat('minion_damage')
			unit.spells[0].range += self.get_stat('minion_range')
			unit.max_hp += self.get_stat('minion_health')
			self.summon(unit, target=evt)
			yield

class ImpShrine(Shrine):

	def on_init(self):
		self.buff_class = ImpShrineBuff
		self.tags = [Tags.Chaos]
		self.description = "Whenever this spell is cast, summon chaos imps near the target for 17 turns.  The number of chaos imps summoned is equal to the level of the spell."
		self.name = "Chaos Imp"


class WyrmEggShrineBuff(ShrineBuff):

	def on_init(self):
		self.owner_triggers[EventOnSpellCast] = self.on_spell_cast

	def on_spell_cast(self, evt):
		if type(evt.spell) == self.spell_class:
			self.owner.level.queue_spell(self.do_summon(evt))

	def do_summon(self, evt):
		if evt.spell.cur_charges == 0:
			egg = random.choice([FireWyrmEgg(), IceWyrmEgg()])
			self.summon(egg, target=evt)
			yield

class WyrmEggShrine(Shrine):

	def on_init(self):
		self.buff_class = WyrmEggShrineBuff
		self.name = "Wyrmbrood"
		self.tags = [Tags.Nature, Tags.Fire, Tags.Ice, Tags.Dragon]
		self.description = "On casting the last charge of this spell, create a friendly wyrm egg near the target."

class BoonShrineBuff(ShrineBuff):

	def on_init(self):
		self.owner_triggers[EventOnSpellCast] = self.on_spell_cast

	def on_spell_cast(self, evt):
		if not type(evt.spell) == self.spell_class:
			return

		allies = [u for u in self.owner.level.units if u != self.owner and not are_hostile(self.owner, u)]
		if not allies:
			return

		newcaster = random.choice(allies)

		spell = type(evt.spell)()
		spell.cur_charges = 1
		spell.caster = newcaster
		spell.owner = newcaster
		spell.statholder = self.owner

		if spell.can_cast(newcaster.x, newcaster.y):
			self.owner.level.act_cast(newcaster, spell, newcaster.x, newcaster.y)

class BoonShrine(Shrine):

	def on_init(self):
		self.name = "Boon"
		self.tags = [Tags.Enchantment]
		self.description = "Self targeted spells only.\nWhenever you cast this spell, a random ally also casts it."
		self.buff_class = BoonShrineBuff

	def can_enhance(self, spell):
		return spell.range == 0 and Shrine.can_enhance(self, spell)

class SniperShrine(Shrine):

	def on_init(self):
		self.name = "Sniper"
		self.attr_bonuses['minion_range'] = 1.0

class ToxicAgonyBuff(ShrineBuff):

	def on_init(self):
		self.global_triggers[EventOnDamaged] = self.on_damaged

	def on_damaged(self, evt):
		if not evt.source:
			return

		if not evt.unit.has_buff(Poison):
			return

		sources = [evt.source]
		
		# For passive buffs or spells, potentially append the spell that summoned the minion with the passive or spell
		if isinstance(evt.source, Spell) or (isinstance(evt.source, Buff) and evt.source.buff_type == BUFF_TYPE_PASSIVE):
			if evt.source.owner and evt.source.owner.source:
				sources.append(evt.source.owner.source)

		if not any(isinstance(source, self.spell_class) and source.owner == self.owner for source in sources):
			return

		targets = self.owner.level.get_units_in_ball(evt.unit, 5)
		targets = [t for t in targets if are_hostile(t, self.owner) and t != evt.unit and self.owner.level.can_see(t.x, t.y, evt.unit.x, evt.unit.y)]
		random.shuffle(targets)

		for t in targets[:4]:
			self.owner.level.queue_spell(self.bolt(evt.damage, evt.unit, t))
	
	def bolt(self, damage, source, target):
		for p in self.owner.level.get_points_in_line(source, target, find_clear=True)[1:-1]:
			self.owner.level.show_effect(p.x, p.y, Tags.Lightning)
			yield
		target.deal_damage(damage, Tags.Lightning, self)

class ToxicAgonyShrine(Shrine):

	def on_init(self):
		self.name = "Toxic Agony"
		self.tags = [Tags.Nature, Tags.Lightning]
		self.description = "Whenever this spell or a minion it summoned deals damage to a [poisoned] enemy, deal that much [lightning] damage to up to [4:num_targets] enemy units in a [5_tile:radius] burst."
		self.buff_class = ToxicAgonyBuff

class BoneSplinterBuff(OnKillShrineBuff):

	def on_kill(self, unit):
		if (Tags.Living not in unit.tags) and (Tags.Undead not in unit.tags):
			return

		self.owner.level.queue_spell(self.burst(unit))

	def burst(self, unit):
		damage = unit.max_hp // 2
		for stage in Burst(unit.level, unit, 3):
			for point in stage:
				self.owner.level.deal_damage(point.x, point.y, damage, Tags.Physical, self)
			yield

		return

class BoneSplinterShrine(Shrine):

	def on_init(self):
		self.name = "Bone Splinter"
		self.tags = [Tags.Dark, Tags.Fire]
		self.description = "When this spell kills a [living] or [undead] unit, deal [physical] damage equal to half that unit's max HP in a [3_tile:radius] burst."
		self.buff_class = BoneSplinterBuff
		self.no_conj = True

class HauntingShrineBuff(DamageCounterShrineBuff):

	def on_init(self):
		self.counter_max = 15
		self.minion_duration = 8

	def trigger(self, target):
		unit = Ghost()
		unit.turns_to_death = self.get_stat('minion_duration')
		self.summon(unit, target, sort_dist=False)
		yield

class HauntingShrine(Shrine):

	def on_init(self):
		self.tags = [Tags.Holy, Tags.Dark]
		self.name = "Haunting"
		self.buff_class = HauntingShrineBuff
		self.description = "For each 15 damage dealt by this spell or a minion it summons, summon a ghost near a unit it dealt damage to for 8 turns."


class SwordShrine(Shrine):

	def on_init(self):
		self.name = "Sword"
		self.attr_bonuses['damage'] = .75

class DaggerShrine(Shrine):

	def on_init(self):
		self.name = "Dagger"
		self.attr_bonuses['damage'] = 7

class ClawShrine(Shrine):

	def on_init(self):
		self.name = "Claw"
		self.attr_bonuses['minion_damage'] = .75

class VigorShrine(Shrine):

	def on_init(self):
		self.name = 'Vigor'
		self.attr_bonuses['minion_health'] = .80

class ShellShrine(Shrine):

	def on_init(self):
		self.name = 'Shell'
		self.attr_bonuses['minion_health'] = 10

class PropagationShrine(Shrine):

	def on_init(self):
		self.name = 'Propagation'
		self.attr_bonuses['cascade_range'] = .5
		self.attr_bonuses['num_targets'] = .5

class ButterflyWingBuff(DamageCounterShrineBuff):

	def on_init(self):
		self.counter_max = 50
		self.minion_duration = 5

	def trigger(self, target):
		unit = ButterflyDemon()
		unit.turns_to_death = self.get_stat('minion_duration')
		self.summon(unit, target)
		yield

class ButterflyWingShrine(Shrine):

	def on_init(self):
		self.name = "Butterfly Wing"
		self.description = "For each 50 damage dealt by this spell or a minion it summons, summon a butterfly demon near the target for 5 turns."
		self.buff_class = ButterflyWingBuff
		self.tags = [Tags.Dark, Tags.Nature, Tags.Arcane, Tags.Lightning]


class GoldSkullBuff(ShrineBuff):

	def on_init(self):
		self.owner_triggers[EventOnSpellCast] = self.on_spell_cast

	def on_spell_cast(self, evt):
		if type(evt.spell) == self.spell_class:
			self.owner.level.queue_spell(self.do_summon(evt))

	def do_summon(self, evt):
		if evt.spell.cur_charges == 0:
			self.summon(GoldSkull(), target=evt)
			yield


class GoldSkullShrine(Shrine):

	def on_init(self):
		self.name = "Gold Skull"
		self.description = "On casting the last charge of this spell, summon a gold skull near the target."
		self.buff_class = GoldSkullBuff
		self.tags = [Tags.Holy, Tags.Dark]


class FurnaceShrineBuff(DamageCounterShrineBuff):

	def on_init(self):
		self.counter_max = 100

	def trigger(self, target):
		unit = FurnaceHound()
		self.summon(unit, target, sort_dist=False)
		yield

class FurnaceShrine(Shrine):

	def on_init(self):
		self.tags = [Tags.Fire, Tags.Dark]
		self.name = "Furnace"
		self.buff_class = FurnaceShrineBuff
		self.description = "For each 100 damage dealt by this spell or a minion it summons, summon a furnace hound near a unit it dealt damage to."


class HeavenstrikeBuff(OnKillShrineBuff):

	def on_kill(self, unit):
		if not are_hostile(self.owner, unit):
			return
		self.owner.level.queue_spell(self.do_damage(unit))

	def do_damage(self, unit):
		units = [u for u in self.owner.level.get_units_in_los(unit) if are_hostile(self.owner, u)]
		random.shuffle(units)
		units.sort(key=lambda u: distance(unit, u))
		if units:
			target = units[0]
			for p in self.owner.level.get_points_in_line(unit, target, find_clear=True):
				self.owner.level.show_effect(p.x, p.y, Tags.Holy, minor=True)
				yield
			target.deal_damage(18, Tags.Holy, self)

class HeavenstrikeShrine(Shrine):

	def on_init(self):
		self.name = "Heavenstrike"
		self.description = "Whenever this spell kills an enemy unit, deal [18_holy:holy] damage to the closest enemy in line of sight."
		self.buff_class = HeavenstrikeBuff
		self.tags = [Tags.Lightning, Tags.Holy]
		self.no_conj = True

class StormchargeBuff(DamageCounterShrineBuff):

	def on_init(self):
		self.counter_max = 15

	def trigger(self, target):
		enemies = [u for u in self.owner.level.units if are_hostile(u, self.owner)]
		if enemies:
			e = random.choice(enemies)
			dtype = random.choice([Tags.Lightning, Tags.Ice])
			e.deal_damage(9, dtype, self)
			yield

class StormchargeShrine(Shrine):

	def on_init(self):
		self.name = "Stormcharge"
		self.tags = [Tags.Ice, Tags.Lightning]
		self.buff_class = StormchargeBuff
		self.description = "For each 15 damage dealt by this spell or a minion it summons, deal [9_ice:ice] or [9_lightning:lightning] damage to a random enemy unit."


class DisintegrationBuff(DamageCounterShrineBuff):

	def on_init(self):
		self.counter_max = 30

	def trigger(self, target):
		enemies = [u for u in self.owner.level.units if are_hostile(u, self.owner)]
		for e in enemies:
			dtype = random.choice([Tags.Arcane, Tags.Physical])
			e.deal_damage(1, dtype, self)
			yield

class DisintegrationShrine(Shrine):

	def on_init(self):
		self.name = "Disintegration"
		self.tags = [Tags.Arcane, Tags.Lightning, Tags.Dark]
		self.description = "For each 30 damage dealt by this spell, deal [1_arcane:arcane] or [1_physical:physical] damage to all enemies."
		self.buff_class = DisintegrationBuff

class AlchemistShrineBuff(ShrineBuff):

	def on_init(self):
		self.owner_triggers[EventOnSpellCast] = self.on_spell_cast

	def on_spell_cast(self, evt):
		if evt.spell.item:
			for s in self.owner.spells:
				if type(s) == self.spell_class and s.cur_charges < s.get_stat('max_charges'):
					s.cur_charges += 1

class AlchemistShrine(Shrine):

	def on_init(self):
		self.name = "Alchemist"
		self.description = "Whenever you use an item, gain 1 charge of this spell."
		self.buff_class = AlchemistShrineBuff

class WarpedBuff(ShrineBuff):

	def on_init(self):
		self.owner_triggers[EventOnSpellCast] = self.on_spell_cast

	def on_spell_cast(self, evt):
		if type(evt.spell) == self.spell_class:
			self.do_damage()
			self.owner.level.queue_spell(self.do_damage_s())

	def do_damage(self):
		enemies = [u for u in self.owner.level.get_units_in_ball(self.owner, 4) if are_hostile(u, self.owner)]
		random.shuffle(enemies)
		for e in enemies:
			e.deal_damage(11, Tags.Arcane, self)

	def do_damage_s(self):
		self.do_damage()
		yield

class WarpedShrine(Shrine):

	def on_init(self):
		self.name = "Warped"
		self.description = "Whenever you cast this spell and then also after it is resolved, deal [11_arcane:arcane] damage to all enemies within [4_tiles:radius] of the caster."
		self.tags = [Tags.Translocation]
		self.buff_class = WarpedBuff

class TroublerShrineBuff(ShrineBuff):

	def on_init(self):
		self.owner_triggers[EventOnSpellCast] = self.on_spell_cast

	def on_spell_cast(self, evt):
		if type(evt.spell) == self.spell_class:
			self.owner.level.queue_spell(self.make_troubler(Point(self.owner.x, self.owner.y)))

	def make_troubler(self, point):
		for i in range(self.spell_level):
			troubler = Troubler()
			troubler.turns_to_death = 7
			apply_minion_bonuses(self, troubler)
			self.summon(troubler, target=point)
			yield

class TroublerShrine(Shrine):

	def on_init(self):
		self.name = "Troubler"
		self.description = "Whenever you cast this spell, summon several troublers near the location it was cast from for [7_turns:minion_duration].  The number of troublers summoned is equal to the spell's level."
		self.tags = [Tags.Translocation]
		self.buff_class = TroublerShrineBuff

class SphereShrine(Shrine):

	def on_init(self):
		self.name = "Sphere"
		self.attr_bonuses['max_charges'] = 2
		self.attr_bonuses['range'] = 4
		self.attr_bonuses['minion_health'] = 9
		self.tags = [Tags.Orb]

class ElementalClawBuff(ShrineBuff):

	def on_init(self):
		self.global_triggers[EventOnDamaged] = self.on_damage
		self.dtype = None

	def on_damage(self, evt):
		if not evt.source:
			return 
		if not evt.source.owner:
			return
		if not evt.source.owner.source:
			return
		if evt.damage_type != Tags.Physical:
			return
		if not type(evt.source.owner.source) == self.spell_class:
			return
		evt.unit.deal_damage(evt.damage, self.dtype, self)

class FireClawBuff(ElementalClawBuff):

	def __init__(self, *args):
		ElementalClawBuff.__init__(self, *args)
		self.dtype = Tags.Fire

class FireClawShrine(Shrine):

	def on_init(self):
		self.name = "Fire Claw"
		self.conj_only = True
		self.tags = [Tags.Nature, Tags.Dragon]
		self.description = "Redeal [physical] damage dealt by minions summoned as [fire] damage."
		self.buff_class = FireClawBuff

class IceClawBuff(ElementalClawBuff):

	def __init__(self, *args):
		ElementalClawBuff.__init__(self, *args)
		self.dtype = Tags.Ice

class IceClawShrine(Shrine):

	def on_init(self):
		self.name = "Ice Claw"
		self.conj_only = True
		self.tags = [Tags.Nature, Tags.Dragon]
		self.description = "Redeal [physical] damage dealt by minions summoned as [ice] damage."
		self.buff_class = IceClawBuff

class FaewitchShrineBuff(OnKillShrineBuff):

	def on_init(self):
		self.minion_duration = 7
		OnKillShrineBuff.on_init(self)

	def on_kill(self, unit):
		if any(b.buff_type == BUFF_TYPE_CURSE for b in unit.buffs):
			self.owner.level.queue_spell(self.do_summon(unit))

	def do_summon(self, target):
		unit = WitchFae()
		self.summon(unit, target, sort_dist=False)
		unit.turns_to_death = self.get_stat('minion_duration')
		yield

class FaewitchShrine(Shrine):

	def on_init(self):
		self.name = "Faewitch"
		self.description = "Whenever this spell kills a unit, if that unit had atleast one debuff, summon a faewitch for [7_turns:minion_duration]."
		self.buff_class = FaewitchShrineBuff
		self.tags = [Tags.Arcane, Tags.Dark]
		self.no_conj = True

class BomberShrineBuff(OnKillShrineBuff):

	def on_kill(self, unit):
		self.owner.level.queue_spell(self.do_summon(unit))

	def do_summon(self, target):
		unit = random.choice([FireBomber, VoidBomber])()
		self.summon(unit, target)
		yield

class BomberShrine(Shrine):

	def on_init(self):
		self.name = "Bomber"
		self.description = "Whenever this spell kills a unit, summon a fire bomber or a void bomber at that units location."
		self.buff_class = BomberShrineBuff
		self.tags = [Tags.Fire, Tags.Arcane]
		self.no_conj = True

class SorceryShieldStack(Buff):

	def __init__(self, tag):
		self.tag = tag
		Buff.__init__(self)

	def on_init(self):
		self.name = "%s Protection" % self.tag.name
		self.stack_type = STACK_NONE
		self.resists[self.tag] = 100
		self.color = self.tag.color

class SorceryShieldShrineBuff(ShrineBuff):

	def on_init(self):
		self.global_triggers[EventOnDamaged] = self.on_damage

	def on_damage(self, evt):
		
		if type(evt.source) != self.spell_class:
			return
		if evt.source.owner != self.owner:
			return

		shield_buff = SorceryShieldStack(evt.damage_type)
		self.owner.apply_buff(shield_buff, 3)

class SorceryShieldShrine(Shrine):

	def on_init(self):
		self.name = "Sorcery Shield"
		self.tags = [Tags.Sorcery]
		self.buff_class = SorceryShieldShrineBuff
		self.description = "Whenever this spell deals damage, you gain 100 resistance to that type of damage for 3 turns."

class FrostfaeShrineBuff(DamageCounterShrineBuff):

	def on_init(self):
		self.counter_max = 33
		self.minion_duration = 11

	def trigger(self, target):
		unit = FairyIce()
		unit.turns_to_death = self.get_stat('minion_duration')
		self.summon(unit, target)
		yield

class FrostfaeShrine(Shrine):

	def on_init(self):
		self.name = "Frost Faery"
		self.description = "For each 33 damage dealt by this spell or a minion it summons, summon an Ice Faery near a unit it dealt damage to."
		self.tags = [Tags.Arcane, Tags.Ice]
		self.buff_class = FrostfaeShrineBuff

class EssenseShrineBuff(OnKillShrineBuff):

	def on_kill(self, unit):
		for u in self.owner.level.units:
			if not are_hostile(self.owner, u) and u.turns_to_death:
				u.turns_to_death += 1

class EssenceShrine(Shrine):

	def on_init(self):
		self.name = "Essence"
		self.tags = [Tags.Dark, Tags.Arcane, Tags.Lightning]
		self.description = "Whenever this spell kills a unit, all your temporary allies gain 1 extra turn of duration."
		self.buff_class = EssenseShrineBuff
		self.no_conj = True

class ChaosConductanceShrineBuff(ShrineBuff):

	def on_init(self):
		self.global_triggers[EventOnDamaged] = self.on_damaged

	def on_damaged(self, evt):
		if not self.is_enhanced_spell(evt.source, allow_minion=True):
			return

		if evt.unit == self.owner:
			return

		if are_hostile(self.owner, evt.unit):
			return

		self.owner.level.queue_spell(self.do_damage(evt.unit, evt.damage, evt.damage_type))

	def do_damage(self, target, damage, dtype):
		first = True
		for unit in self.owner.level.get_units_in_ball(target, radius=4):
			if target != unit and are_hostile(self.owner, unit):
				unit.deal_damage(damage, dtype, self)
			yield

class ChaosConductanceShrine(Shrine):

	def on_init(self):
		self.name = "Chaos Relay"
		self.description = "Whenever this spell or a minion it summoned deals damage to an allied unit, redeal that damage to all enemy units in a [4_tile:radius] radius."
		self.tags = [Tags.Fire, Tags.Lightning, Tags.Chaos]
		self.buff_class = ChaosConductanceShrineBuff

class ElementalHarvestShrineBuff(ShrineBuff):

	def on_init(self):
		self.global_triggers[EventOnDeath] = self.on_death

	def on_death(self, evt):
		if self.prereq.cur_charges >= self.prereq.get_stat('max_charges'):
			return

		relevant_tags = [Tags.Fire, Tags.Lightning, Tags.Ice]
		if not any(t in evt.unit.tags for t in relevant_tags):
			return

		chance = .1
		if evt.damage_event and evt.damage_event.damage_type in relevant_tags:
			chance = .3

		if random.random() < chance:
			self.prereq.cur_charges += 1

class ElementalHarvestShrine(Shrine):

	def on_init(self):
		self.name = "Elemental Harvest"
		self.description = "Whenever a [fire], [lightning], or [ice] unit dies, this spell has a 10% chance of gaining a charge.\nIf the unit died to [fire], [lightning], or [ice] damage, this chance is increased to 30%."
		self.tags = [Tags.Fire, Tags.Lightning, Tags.Ice]
		self.buff_class = ElementalHarvestShrineBuff

class IceSprigganShrineBuff(ShrineBuff):

	def on_init(self):
		self.owner_triggers[EventOnSpellCast] = self.on_spell_cast

	def on_spell_cast(self, evt):
		if not self.is_enhanced_spell(evt.spell):
			return

		self.owner.level.queue_spell(self.do_summon(evt))

	def do_summon(self, evt):
		unit = IcySpriggan()
		apply_minion_bonuses(self, unit)
		self.summon(unit, target=evt)
		yield

class IcySprigganShrine(Shrine):

	def on_init(self):
		self.name = "Icy Spriggan"
		self.description = "Whenever you cast this spell, summon an Ice Spriggan near the target."
		self.tags = [Tags.Nature, Tags.Ice]
		self.buff_class = IceSprigganShrineBuff

class SunlightShrineBuff(ShrineBuff):

	def on_init(self):
		self.global_triggers[EventOnDamaged] = self.on_damage

	def on_damage(self, evt):
		if not are_hostile(evt.unit, self.owner):
			return
		if not self.is_enhanced_spell(evt.source):
			return
		self.owner.level.queue_spell(self.do_heal(evt))

	def do_heal(self, evt):
		heal = evt.damage // 2
		if heal <= 0:
			return

		for u in self.owner.level.get_units_in_los(evt.unit):
			if not are_hostile(u, self.owner) and u != self.owner:
				u.deal_damage(-heal, Tags.Heal, self)
		yield

class SunlightShrine(Shrine):

	def on_init(self):
		self.name = "Sunlight"
		self.description = "Whenever this spell deals damage to an enemy unit, all allied minions in line of sight of the damaged unit are healed for half that much damage."
		self.tags = [Tags.Nature, Tags.Fire, Tags.Holy]
		self.no_conj = True
		self.buff_class = SunlightShrineBuff

class ConflagurationBuff(ShrineBuff):

	def on_init(self):
		self.global_triggers[EventOnDamaged] = self.on_damage

	def on_damage(self, evt):
		if evt.damage <= 1:
			return
		if self.is_enhanced_spell(evt.source, allow_minion=True):
			self.owner.level.queue_spell(self.do_damage(evt))

	def do_damage(self, evt):
		targets = [u for u in self.owner.level.get_units_in_los(evt.unit) if are_hostile(u, self.owner) and u != evt.unit]
		if not targets:
			return

		target = random.choice(targets)

		target.deal_damage(evt.damage // 2, Tags.Fire, self)

		yield

class ConflagurationShrine(Shrine):

	def on_init(self):
		self.name = "Searing"
		self.description = "Whenever this spell deals damage, redeal half that damage to another random enemy in line of sight."
		self.tags = [Tags.Fire, Tags.Holy]
		self.buff_class = ConflagurationBuff

class ChaosQuillShrineBuff(ShrineBuff):

	def on_init(self):
		self.global_triggers[EventOnDeath] = self.on_death
		self.owner_triggers[EventOnSpellCast] = self.on_spell_cast

	def on_spell_cast(self, evt):
		if type(evt.spell) == self.spell_class:
			self.owner.level.queue_spell(self.do_summon(evt))

	def do_summon(self, evt):
		if evt.spell.cur_charges == 0:
			unit = ChaosQuill()
			unit.turns_to_death = 36
			apply_minion_bonuses(self, unit)
			self.summon(unit, target=evt)
			yield

	def on_death(self, evt):
		if not evt.damage_event:
			return
		if self.is_enhanced_spell(evt.damage_event.source, allow_minion=True) and (Tags.Fire in evt.unit.tags or Tags.Lightning in evt.unit.tags):
			self.on_kill(evt.unit)

	def on_kill(self, unit):
		s = random.choice([LivingFireballScroll, LivingLightningScroll])()
		apply_minion_bonuses(self, s)
		self.summon(s, unit)

class ChaosQuillShrine(Shrine):

	def on_init(self):
		self.buff_class = ChaosQuillShrineBuff
		self.tags = [Tags.Chaos, Tags.Fire, Tags.Lightning]
		self.name = "Chaos Quill"
		self.description = ("Whenever this spell kills a [lightning] or [fire] unit, summon a living scroll of fire or lightning at that unit's location.\n"
						    "Whenever you cast the last charge of this spell, summon a Chaos Quill for 36 turns.")

class FireflyShrineBuff(OnKillShrineBuff):

	def on_kill(self, unit):
		for i in range(2):
			flyswarm = FireFlies()
			flyswarm.turns_to_death = 20
			apply_minion_bonuses(self, flyswarm)
			self.summon(flyswarm, self.owner, sort_dist=False)

class FireflyShrine(Shrine):

	def on_init(self):
		self.buff_class = FireflyShrineBuff
		self.tags = [Tags.Nature, Tags.Fire, Tags.Dark]
		self.name = "Firefly"
		self.description = "Whenever this spell kills a unit, summon 2 firefly swarms near the caster for 20 turns."
		self.no_conj = True

class CauterizingShrineBuff(ShrineBuff):

	def on_init(self):
		self.global_triggers[EventOnDamaged] = self.on_damage

	def on_damage(self, evt):
		if are_hostile(evt.unit, self.owner) and self.is_enhanced_spell(evt.source):
			self.owner.level.queue_spell(self.burn_hp(evt))

	def burn_hp(self, evt):
		evt.unit.max_hp -= evt.damage
		evt.unit.max_hp = max(evt.unit.max_hp, 1)
		self.owner.level.show_effect(evt.unit.x, evt.unit.y, Tags.Dark, minor=True)
		yield

class CauterizingShrine(Shrine):

	def on_init(self):
		self.buff_class = CauterizingShrineBuff
		self.tags = [Tags.Dark, Tags.Fire]
		self.name = "Cauterizing"
		self.description = "Whenever this spell or a minion it summons deals damage to an enemy, that enemy loses that much max HP."

class DeathchillChimeraShrineBuff(DamageCounterShrineBuff):

	def on_init(self):
		self.counter_max = 80

	def trigger(self, target):
		u = DeathchillChimera()
		apply_minion_bonuses(self, u)
		self.summon(u, target)
		yield

class DeathchillChimeraShrine(Shrine):

	def on_init(self):
		self.tags = [Tags.Ice, Tags.Dark]
		self.name = "Deathchill Gate"
		self.buff_class = DeathchillChimeraShrineBuff
		self.description = "For each 80 damage dealt by this spell or a minion it summons, summon a deathchill chimera near a unit it dealt damage to."

class BloodrageShrineBuff(OnKillShrineBuff):

	def on_kill(self, unit):
		for u in self.owner.level.get_units_in_los(unit):
			if are_hostile(u, self.owner) or u == self.owner:
				continue
			u.apply_buff(BloodrageBuff(3), 5)


class BloodrageShrine(Shrine):

	def on_init(self):
		self.tags = [Tags.Nature, Tags.Chaos, Tags.Dark]
		self.name = "Bloodrage"
		self.description = "Whenever this spell kills a unit, all allied minions in line of sight gain +3 damage for 5 turns."
		self.buff_class = BloodrageShrineBuff
		self.no_conj = True


class RazorShrineBuff(ShrineBuff):

	def on_init(self):
		self.owner_triggers[EventOnSpellCast] = self.on_spell_cast

	def on_spell_cast(self, evt):
		if not self.is_enhanced_spell(evt.spell):
			return

		self.owner.level.queue_spell(self.do_razors(evt))

	def do_razors(self, evt):
		targets = [u for u in self.owner.level.get_units_in_los(evt) if are_hostile(self.owner, u)]
		random.shuffle(targets)

		for t in targets[:evt.spell.level]:
			for p in self.owner.level.get_points_in_line(evt, t)[1:-1]:
				self.owner.level.show_effect(p.x, p.y, Tags.Physical, minor=True)

			t.deal_damage(27, Tags.Physical, self)
			yield


class ShrapnelShrine(Shrine):

	def on_init(self):
		self.tags = [Tags.Metallic]
		self.name = "Razor"
		self.description = "Whenever you cast this spell, deal 27 [physical] damage to 1 enemy in line of sight per spell level."
		self.buff_class = RazorShrineBuff

COMMON = 1
UNCOMMON = 1
RARE = 1

new_shrines = [

	#F
	(RedFlameShrine, COMMON),
	(BurningShrine, UNCOMMON),
	(BoneSplinterShrine, UNCOMMON),

	(CracklingShrine, COMMON),
	(SandStoneShrine, COMMON),
	(RedStarShrine, UNCOMMON),
	(FrostfireShrine, COMMON),
	(WhiteCandleShrine, RARE),
	(CharredBoneShrine, UNCOMMON),

	#L
	(ThunderShrine, UNCOMMON),
	(BlackSkyShrine, UNCOMMON),

	(BlueSkyShrine, UNCOMMON),
	(EnergyShrine, UNCOMMON),
	(EntropyShrine, RARE),
	(StormCloudShrine, UNCOMMON),
	(BrightShrine, UNCOMMON),

	#N
	(OakenShrine, COMMON),
	(GroveShrine, COMMON),
	(ToxicAgonyShrine, RARE),

	(SwampShrine, UNCOMMON),
	(FaeShrine, UNCOMMON),
	(TundraShrine, UNCOMMON),
	(LifeShrine, COMMON),
	(WyrmEggShrine, RARE),
	
	#A
	(OtherworldlyShrine, UNCOMMON),
	(MysticShrine, COMMON),
	(EnervationShrine, RARE),

	(NightmareShrine, COMMON),
	(ProtectionShrine, COMMON),
	(StoningShrine, RARE),

	#D
	(CruelShrine, COMMON),
	(TormentShrine, COMMON),
	(HauntingShrine, UNCOMMON),

	(FrozenSkullShrine, UNCOMMON),
	
	#I
	(IcyShrine, COMMON),
 	(FrozenShrine, COMMON),

	(StillnessShrine, UNCOMMON),

	#H
	(AngelicShrine, COMMON),

	(SoulpowerShrine, UNCOMMON),

	#C
	(CallingShrine, COMMON),
	(AfterlifeShrine, UNCOMMON),
	(GreyBoneShrine, UNCOMMON),

	#S
	(FarsightShrine, UNCOMMON),
 
	#E
	(BoonShrine, UNCOMMON),

	#O
	(ImpShrine, UNCOMMON),

	#MISC
	(Enveloping, UNCOMMON),
	(Memory, COMMON),
	(DemonBaneShrine, UNCOMMON),
	(BerserkShrine, UNCOMMON),
	(SniperShrine, UNCOMMON),

	(SwordShrine, COMMON),
	(DaggerShrine, COMMON),
	(ClawShrine, COMMON),
	(VigorShrine, COMMON),
	(ShellShrine, COMMON),
	(PropagationShrine, UNCOMMON),

	(DragonHeartShrine, UNCOMMON),

	# More specialer shrines
	(ButterflyWingShrine, RARE),
	(GoldSkullShrine, RARE),
	(HeavenstrikeShrine, UNCOMMON),
	(FurnaceShrine, RARE),

	# Even more shrines!
	(StormchargeShrine, RARE),
	(DisintegrationShrine, RARE),
	(AlchemistShrine, UNCOMMON),
	(WarpedShrine, UNCOMMON),
	(TroublerShrine, RARE),
	(SphereShrine, UNCOMMON),
	(FireClawShrine, UNCOMMON),
	(IceClawShrine, UNCOMMON),

	(FaewitchShrine, RARE),
	(BomberShrine, UNCOMMON),
	(SorceryShieldShrine, UNCOMMON),
	(FrostfaeShrine, RARE),
	(EssenceShrine, UNCOMMON),

	(ChaosConductanceShrine, UNCOMMON),
	(ElementalHarvestShrine, UNCOMMON),
	(IcySprigganShrine, RARE),

	(SunlightShrine, RARE),
	(ConflagurationShrine, RARE),
	(ChaosQuillShrine, RARE),
	(FireflyShrine, RARE),
	(CauterizingShrine, RARE),
	(DeathchillChimeraShrine, RARE),
	(BloodrageShrine, RARE),

	(ShrapnelShrine, UNCOMMON),

]

# TODO- validation/unit test

for s in new_shrines:
	ex = s[0]()
	if ex.description:
		assert(ex.buff_class != ShrineBuff)


# Returns a prop which points to a shifitng shop with the appropriate buffs

def make_shrine(shrine, player):
	shrine_prop = ShrineShop(lambda : list(shrine.get_buffs(player)))
	shrine_prop.name = "%s Shrine" % shrine.name
	shrine_prop.description = shrine.get_description()

	# Use custom asset if exists
	maybe_asset = ['tiles', 'shrine', shrine.name.lower().replace(' ', '_')]
	if os.path.exists(os.path.join('rl_data', *maybe_asset) + '.png'):
		shrine_prop.asset = maybe_asset

	maybe_asset = ['tiles', 'shrine', 'animated', shrine.name.lower().replace(' ', '_')]
	if os.path.exists(os.path.join('rl_data', *maybe_asset) + '.png'):
		shrine_prop.asset = maybe_asset

	return shrine_prop

def shrine(player):
	shrine = random.choices([s[0] for s in new_shrines], [s[1] for s in new_shrines])[0]()
	return make_shrine(shrine, player)

def skill_scroll(level, player):
	if player:
		skill_opts = [s for s in player.game.all_player_skills if not player.game.has_upgrade(s)]
	else:
		skill_opts = make_player_skills()
	random.shuffle(skill_opts)
	skill_opts = skill_opts[:CHEST_SIZE]

	shop = Shop()
	shop.name = "Scroll of Skills"
	shop.description = "One skill may be learned for free from this text"
	shop.asset =  ['tiles', 'library', 'library_gold']
	shop.items = skill_opts

	return shop

def scroll(level, player):
	max_spell_level = 2
	if level >= 5:
		max_spell_level = 3
	if level >= 10:
		max_spell_level = 4
	if level >= 15:
		max_spell_level = 5

	min_spell_level = 1
	if level >= 4:
		min_spell_level = 2
	if level >= 14:
		min_spell_level = 3
	if level >= 20:
		min_spell_level = 4

	if player:
		spell_opts = [s for s in player.game.all_player_spells if min_spell_level <= s.level <= max_spell_level and s not in player.spells]
	else:
		spell_opts = make_player_spells()
	random.shuffle(spell_opts)
	spell_opts = spell_opts[:CHEST_SIZE+1]

	shop = Shop()
	shop.name = "Scroll of Spells"
	shop.description = "One spell may be learned for free from this text"
	shop.asset =  ['tiles', 'library', 'library_white']
	shop.items = spell_opts

	return shop


def roll_chest(level, prng=random):
	opts = [
		(treasure_chest, .5),
		(crown_chest, .08),
		(damage_hat_chest, .04),
		(hat_chest, .05),
		(ring_chest, .5),
		(staff_chest, .1),
		(shoe_chest, .05),
		(armor_chest, .05),
		(trinket_chest, .15),
		#(mini_treasure_chest, .08)
	]

	return prng.choices([o[0] for o in opts], weights=[o[1] for o in opts])[0](level, prng)

def roll_shrine(level, prng=None, player=None):

	# Level 2 always a circle or an item- something that directs the player towards some specific build ideas
	opts = [
		(roll_chest, 1.3),
		(hp_shrine, 1),
		(exotic_pet_chest, .25),
		(lambda level, prng : scroll(level, player), .2)
		# Miniaturization Shrine
		# Refund Shrine
		# Circle Replacement
		# Item bonanza?  (9 portal disruptors baby!)
		# other weird shit ect. (maybe put below too)
	]

	if level > 13:
		opts.append((lambda level, prng: skill_scroll(level, player), .3))

	if not prng:
		prng = random

	return prng.choices([o[0] for o in opts], weights=[o[1] for o in opts])[0](level, prng)

def roll_circle():
	return 

if __name__ == "__main__":
	for i in range(200):
		roll_shrine(2)
	#Print loot odds
