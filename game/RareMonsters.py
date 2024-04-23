from Level import *
from Monsters import *
from copy import copy
from CommonContent import *
import Spells
from Variants import *
import sys

class Dampen(Buff):

	def __init__(self, attr, amt):
		Buff.__init__(self)
		self.stack_type = STACK_INTENSITY
		self.buff_type = BUFF_TYPE_CURSE
		self.color = Tags.Holy.color
		self.global_bonuses[attr] = -amt
		self.name = "Curse of the Idol"
		self.asset = ['status', 'idol_curse']

class DampenSpell(Spell):

	def __init__(self, attr, amt, label):
		Spell.__init__(self)
		self.attr = attr
		self.amt = amt
		self.stack_type = STACK_INTENSITY
		self.label = label
		self.damage_type = Tags.Holy

		self.name = "Curse of the %s" % self.label
		self.description = "Decreases player spell and skill %s by %d" % (self.attr, self.amt)

		self.range = RANGE_GLOBAL
		self.requires_los = False

		self.duration = 8
		self.cool_down = 8

	def get_buff(self):
		buff = Dampen(self.attr, self.amt)
		buff.name = "%sness Curse" % self.label
		return buff

	def get_ai_target(self):
		return self.caster.level.player_unit

	def can_threaten(self, x, y):
		return False

	def cast_instant(self, x, y):
		u = self.caster.level.get_unit_at(x, y)
		if u:
			u.apply_buff(self.get_buff(), self.get_stat('duration'))
			self.caster.level.show_path_effect(self.caster, u, Tags.Holy, minor=True)

def Idol():
	idol = Unit()
	idol.sprite.char = 'I'
	idol.sprite.color = Tags.Construct.color
	idol.asset_name = "idol"

	idol.max_hp = 35
	idol.shields = 2
	idol.stationary = True

	idol.tags = [Tags.Construct]
	idol.resists[Tags.Fire] = 50
	idol.resists[Tags.Lightning] = 50
	idol.resists[Tags.Physical] = 50
	return idol

def DampenerIdol(label, attr, amt):

	idol = Idol()
	idol.sprite.color = Tags.Construct.color
	idol.spells.append(DampenSpell(attr, amt, label))
	idol.name = "Idol of the %s" % label
	idol.asset_name = '%s_idol' % label.lower()

	return idol

class UndeathIdolBuff(Buff):

	def on_init(self):
		self.name = "Aura of Undeath"
		self.description = "Each turn all friendly undead units heal for 1 and all enemy living units take 1 dark damage"
		self.color = Tags.Undead.color

	def on_advance(self):
		for u in self.owner.level.units:
			if Tags.Undead in u.tags and not self.owner.level.are_hostile(u, self.owner):
				u.deal_damage(-1, Tags.Heal, self)
			if Tags.Living in u.tags and self.owner.level.are_hostile(u, self.owner):
				u.deal_damage(1, Tags.Dark, self)

		for p in self.owner.level.get_points_in_ball(self.owner.x, self.owner.y, 1, diag=True):
			if self.owner.level.get_unit_at(p.x, p.y):
				continue
			if not self.owner.level.tiles[p.x][p.y].can_see:
				continue
			self.owner.level.show_effect(p.x, p.y, Tags.Dark, minor=True)


def IdolOfUndeath():
	idol = Idol()
	idol.sprite.color = Tags.Undead.color
	idol.name = "Idol of Undeath"
	idol.asset_name = "undeath_idol"
	idol.buffs.append(UndeathIdolBuff())
	return idol

class LifeIdolBuff(Buff):

	def on_init(self):
		self.name = "Aura of Life"
		self.description = "Each turn all friendly living units are healed for 3"

	def on_advance(self):
		for u in self.owner.level.units:
			if Tags.Living in u.tags and not self.owner.level.are_hostile(u, self.owner):
				u.deal_damage(-3, Tags.Heal, self)
		
		for p in self.owner.level.get_points_in_ball(self.owner.x, self.owner.y, 1, diag=True):
			if self.owner.level.get_unit_at(p.x, p.y):
				continue
			if not self.owner.level.tiles[p.x][p.y].can_see:
				continue
			self.owner.level.show_effect(p.x, p.y, Tags.Holy, minor=True)

	def get_tooltip(self):
		return self.description

def IdolOfLife():
	idol = Idol()
	idol.sprite.color = Tags.Living.color
	idol.name = "Idol of Life"
	idol.buffs.append(LifeIdolBuff())
	idol.asset_name = "life_idol"

	return idol

class ClarityIdolBuff(Buff):

	def on_init(self):
		self.name = "Aura of Clarity"
		self.description = "Each turn cure stun or berserk on a random ally"

	def get_tooltip(self):
		return "Cure stun, berserk, or petrify on a random ally each turn"

	def on_advance(self):
		units = list(self.owner.level.units)
		random.shuffle(units)
		for u in units:
			if are_hostile(u, self.owner):
				continue
			buf = u.get_buff(Stun) or u.get_buff(BerserkBuff)
			if buf:
				u.remove_buff(buf)
				self.owner.level.show_path_effect(self.owner, u, Tags.Holy, minor=True)
				return

def IdolOfClarity():

	idol = Idol()
	idol.sprite.color = Tags.Living.color
	idol.name = "Idol of Clarity"
	idol.buffs.append(ClarityIdolBuff())
	idol.asset_name = "clarity_idol"

	return idol


class GrantSorcery(Spell):

	def on_init(self):
		self.name = "Grant Sorcery"
		self.range = 0

	def get_description(self):
		return "Grants a ranged Fire or Lightning attack to a random ally, along with immunity to that element."

	def get_ai_target(self):
		candidates = [u for u in self.caster.level.units if not are_hostile(u, self.caster) and not u.has_buff(TouchedBySorcery)]
		if not candidates:
			return None
		return random.choice(candidates)

	def can_cast(self, x, y):
		return True

	def cast_instant(self, x, y):

		unit = self.caster.level.get_unit_at(x, y)
		if not unit:
			return

		element = random.choice([Tags.Fire, Tags.Lightning])

		buff = TouchedBySorcery(element)
		unit.apply_buff(buff)

		self.caster.level.show_path_effect(self.caster, unit, element, minor=True)

def IdolOfSorcery():
	idol = Idol()
	idol.sprite.color = Tags.Sorcery.color
	idol.name = "Idol of Sorcery"
	idol.asset_name = "sorcery_idol"

	idol.spells.append(GrantSorcery())

	return idol

def Necromancer():
	unit = Unit()
	unit.sprite.char = 'N'
	unit.sprite.color = Color(155, 42, 184)
	unit.name = "Necromancer"
	unit.description = "Drains life and raises the dead"
	unit.max_hp = 35
	unit.shields = 1
	unit.buffs.append(NecromancyBuff())
	unit.spells.append(LifeDrain())
	unit.resists[Tags.Dark] = 50
	unit.resists[Tags.Holy] = -50
	unit.tags = [Tags.Dark, Tags.Arcane]
	return unit

class DarkPriestHeal(Spell):

	def on_init(self):
		self.name = "Mass Heal"
		self.cool_down = 3
		self.range = 0
		self.description = "Heal all allies for 15"

		self.tags = [Tags.Heal]

	def cast_instant(self, x, y):
		for u in self.caster.level.units:
			if not are_hostile(u, self.caster):
				u.deal_damage(-15, Tags.Heal, self)

def DarkPriests():
	priest = Unit()
	priest.name = "Dark Priest"
	priest.asset_name = "dark_priest"
	priest.sprite.char = 'P'
	priest.sprite.color = Tags.Dark.color

	priest.max_hp = 32
	priest.shields = 1

	priest.tags = [Tags.Dark, Tags.Living]

	priest.spells.append(DarkPriestHeal())
	priest.spells.append(SimpleRangedAttack(damage=7, damage_type=Tags.Dark, range=7))

	return priest

class BannerBuff(Buff):

	def on_applied(self, owner):
		self.global_triggers[EventOnUnitAdded] = self.on_unit_added
		self.owner_triggers[EventOnDeath] = self.on_death

		for unit in self.owner.level.units:
			if unit.is_lair:
				unit.buffs[0].min_turns -= 1
				unit.buffs[0].max_turns -= 1

	def on_unit_added(self, evt):
		if evt.unit.is_lair:
			evt.unit.buffs[0].min_turns -= 1
			evt.unit.buffs[0].max_turns -= 1

	def on_death(self, evt):
		for u in self.owner.level.units:
			if u.is_lair:
				u.buffs[0].min_turns += 1
				u.buffs[0].max_turns += 1

	def get_tooltip(self):
		return "Gates spawn units 1 turn faster"

def WarBanner():
	banner = Unit()
	banner.name = "War Banner"
	banner.sprite.char = 'W'
	banner.sprite.color = Tags.Construct.color
	banner.stationary = True
	banner.max_hp = 35

	banner.buffs.append(BannerBuff())

	return banner

def Watcher():
	unit = Unit()
	unit.sprite.char = 'W'
	unit.sprite.color = Color(220, 220, 150)
	unit.name = "Watcher"
	unit.description = "A tough stationary unit with a long ranged lightning attack"
	unit.max_hp = 40
	unit.spells.append(SimpleRangedAttack(name="Lightning Eye", damage=10, range=30, damage_type=Tags.Lightning, beam=True))
	unit.stationary = True
	unit.tags = [Tags.Construct, Tags.Lightning]
	unit.resists[Tags.Lightning] = 50
	unit.resists[Tags.Fire] = 50
	return unit

def VoidWatcher():
	unit = Watcher()
	unit.name = "Void Watcher"
	unit.resists[Tags.Lightning] = 0
	unit.resists[Tags.Arcane] = 50
	unit.spells[0] = SimpleRangedAttack(name="Void Eye", damage=5, range=30, damage_type=Tags.Arcane, beam=True, melt=True)
	unit.spells[0].cool_down = 3
	unit.tags = [Tags.Construct, Tags.Arcane]
	return unit

# Ally bat- if an ally is in melee range of self and closer to target than self, can cast.
# Deals physical damage to target and to the ally, teleports the ally to a summon point near the player
# Does leap attack anim of ally
class CyclopsAllyBat(Spell):

	def on_init(self):
		self.name = "Swat Ally"
		self.description = "Bats an adjacent unit towards an enemy"
		self.damage = 13
		self.range = 15
		self.damage_type = Tags.Physical

	def get_chump(self, x, y):
		target = Point(x, y)
		adj_points = self.caster.level.get_adjacent_points(self.caster, filter_walkable=False)
		possible_chumps = []
		for p in adj_points:
			unit = self.caster.level.get_unit_at(p.x, p.y)
			if unit == self.caster:
				continue
			if not unit:
				continue
			if not self.caster.level.can_see(target.x, target.y, p.x, p.y):
				continue
			possible_chumps.append(unit)
		if possible_chumps:
			return random.choice(possible_chumps)
		else:
			return None

	def can_cast(self, x, y):
		if self.get_chump(x, y) is None:
			return False
		if not self.caster.level.get_summon_point(x, y, radius_limit=1, diag=True):
			return False
		return self.get_chump(x, y) is not None and Spell.can_cast(self, x, y)

	def cast(self, x, y):
		
		target = self.caster.level.get_unit_at(x, y)
		if not target:
			return

		chump = self.get_chump(target.x, target.y)
		if not chump:
			return

		dest = self.caster.level.get_summon_point(x, y, radius_limit=1, diag=True)
		if not dest:
			return

		for p in self.caster.level.get_points_in_line(chump, dest, find_clear=True):
			self.caster.level.leap_effect(p.x, p.y, Tags.Physical.color, chump)
			yield

		self.caster.level.act_move(chump, dest.x, dest.y, teleport=True)
		
		target.deal_damage(self.get_stat('damage'), Tags.Physical, self)
		chump.deal_damage(self.get_stat('damage'), Tags.Physical, self)


# Enemy bat- if an enemy is in melee range, teleport the enemy to a random point in LOS (again with leap anim).
# The random point must be one such that the distance from the point to the enemy is less than point to the cyclops
class CyclopsEnemyBat(Spell):

	def on_init(self):
		self.name = "Swat Enemy"
		self.description = "Bats an enemy away"
		self.damage = 13
		self.range = 1
		self.melee = True
		self.damage_type = Tags.Physical

	def get_destination(self, target):
		possibles = list(self.caster.level.get_points_in_los(self.caster))
		def is_valid_dest(dest):
			if self.caster.level.get_unit_at(dest.x, dest.y):
				return False
			if distance(dest, target) >= distance(dest, self.caster):
				return False
			if not self.caster.level.can_stand(dest.x, dest.y, target):
				return False
			return True

		possibles = [p for p in possibles if is_valid_dest(p)]
		if possibles:
			return random.choice(possibles)
		else:
			return None

	def cast(self, x, y):
		unit = self.caster.level.get_unit_at(x, y)
		if not unit:
			return
		# If the level is totally full, just whack the guy and call it a day
		unit.deal_damage(self.get_stat('damage'), Tags.Physical, self)
		target = self.get_destination(unit)
		if not target:
			return

		for p in self.caster.level.get_points_in_line(unit, target, find_clear=True):
			self.caster.level.leap_effect(p.x, p.y, Tags.Physical.color, unit)
			yield

		self.caster.level.act_move(unit, target.x, target.y, teleport=True)


def RedCyclops():
	unit = Unit()
	unit.sprite.char = 'C'
	unit.sprite.color = Color(180, 180, 185)
	unit.name = "Red Cyclops"
	unit.max_hp = 126
	unit.spells.append(CyclopsEnemyBat())
	unit.spells.append(CyclopsAllyBat())
	unit.tags = [Tags.Living]
	return unit

class DreamerBuff(Buff):

	def on_init(self):
		self.description = "50% chance to teleport each other unit up to 4 squares away each turn"
		self.color = Tags.Translocation.color

	def get_tooltip(self):
		return self.description

	def on_advance(self):
		level = self.owner.level
		for u in level.units:

			if u == self.owner:
				continue

			if random.random() < .5:
				targets = [t for t in level.iter_tiles() if level.can_stand(t.x, t.y, u) and distance(t, u) < 4]
				if targets:
					teleport_target = random.choice(targets)
					level.flash(u.x, u.y, Tags.Translocation.color)
					level.act_move(u, teleport_target.x, teleport_target.y, teleport=True)
					level.flash(u.x, u.y, Tags.Translocation.color)

def Dreamer():
	dreamer = Unit()
	dreamer.name = "The Dreamer"
	dreamer.max_hp = 1
	dreamer.shields = 10
	dreamer.tags = [Tags.Arcane, Tags.Demon, Tags.Eye]
	dreamer.sprite.char = 'D'
	dreamer.sprite.color = Tags.Arcane.color
	dreamer.resists[Tags.Arcane] = 100
	dreamer.spells.append(SimpleRangedAttack(damage=4, range=12, damage_type=Tags.Arcane))
	dreamer.buffs.append(DreamerBuff())
	dreamer.flying = True
	return dreamer

class WailOfPain(Spell):

	def on_init(self):
		self.name = "Cacophony"
		self.range = 0
		self.radius = 6
		self.damage = 22
		self.cool_down = 7
		self.description = "Deals %d damage to all enemies within %d tiles" % (self.damage, self.radius)
		self.damage_type = Tags.Dark

	def cast_instant(self, x, y):
		for p in self.caster.level.get_points_in_ball(self.caster.x, self.caster.y, self.radius):
			unit = self.caster.level.get_unit_at(p.x, p.y)
			if unit and not are_hostile(self.caster, unit):
				continue

			if not self.caster.level.tiles[p.x][p.y].can_see:
				continue

			self.caster.level.deal_damage(p.x, p.y, self.damage, Tags.Dark, self)

def FallenAngel():
	angel = Unit()
	angel.name = "Fallen Angel"
	angel.max_hp = 400
	angel.shields = 2

	angel.flying = True

	angel.sprite.char = 'A'
	angel.sprite.color = Tags.Demon.color

	shield_spell = ShieldSightSpell(4, 2)
	fire = SimpleRangedAttack(damage=12, damage_type=Tags.Fire, range=4)
	fire.name = "Hellfire"

	angel.spells.append(WailOfPain())
	angel.spells.append(shield_spell)
	angel.spells.append(fire)

	angel.resists[Tags.Dark] = 100
	angel.resists[Tags.Fire] = 50
	angel.resists[Tags.Holy] = 100

	angel.tags = [Tags.Demon, Tags.Holy]

	return angel

def SporeAncient():

	man = SporeBeast()

	man.name = "Spore Man Ancient"
	man.max_hp = 672
	man.buffs[0].healing = 16
	man.buffs[0].radius = 9
	man.spells[0].damage = 28

	return man

class TombstoneSummon(Spell):

	def on_init(self):
		self.name = "Haunt"
		self.description = "Summons a ghost near the wizard"
		self.cool_down = 4
		self.requires_los = False
		self.range = 50

	def get_ai_target(self):
		return self.caster.level.player_unit

	def can_cast(self, x, y):
		return True

	def cast_instant(self, x, y):

		p = self.caster.level.get_summon_point(x, y, sort_dist = False, flying=True)

		if p:
			self.caster.level.show_path_effect(self.caster, p, Tags.Dark, minor=True)
			ghost = Ghost()
			ghost.team = self.caster.team
			self.caster.level.add_obj(ghost, p.x, p.y)

def Tombstone():
	idol = Idol()
	idol.name = "Tombstone"
	idol.asset_name = "tombstone"

	idol.spells.append(TombstoneSummon())
	idol.resists[Tags.Dark] = 100
	return idol

class TreeThornSummon(Spell):

	def on_init(self):
		self.name = "Grow Thorns"
		self.num_thorns = 3
		self.cool_down = 3
		self.range = 100
		self.requires_los = False

	def get_description(self):
		return "Summons %d fae thorns near the player" % self.num_thorns

	def get_ai_target(self):
		return self.caster.level.player_unit

	def cast_instant(self, x, y):
		for i in range(self.num_thorns):
			p = self.caster.level.get_summon_point(x, y, sort_dist = False, flying=True)
			if p:
				self.caster.level.add_obj(FaeThorn(), p.x, p.y)

class TreeHealAura(Buff):

	def on_init(self):
		self.name = "Twisted Healing"

	def get_tooltip(self):
		return "Fully heal most damaged ally each turn"

	def on_advance(self):
		allies = sorted((u for u in self.owner.level.units if u != self.owner and not are_hostile(u, self.owner)), key=lambda u: u.max_hp - u.cur_hp)
		if not allies:
			return

		target = allies[0]
		if target.cur_hp < target.max_hp:
			target.deal_damage(-target.max_hp, Tags.Heal, self)

def TwistedTree():
	tree = Unit()
	tree.name = "Yggdrasil"
	tree.tags = [Tags.Nature, Tags.Demon]

	tree.sprite.char = 'Y'
	tree.sprite.color = Tags.Demon.color

	tree.resists[Tags.Physical] = 50
	tree.resists[Tags.Arcane] = 50
	tree.resists[Tags.Dark] = 50
	tree.resists[Tags.Fire] = -100

	#tree.buffs.append(TreeHealAura())
	aura = DamageAuraBuff(damage=1, damage_type=[Tags.Arcane, Tags.Dark], radius=30)
	aura.name = "Nightmare Aura"
	tree.buffs.append(aura)
	tree.spells.append(TreeThornSummon())
	tree.spells.append(SimpleRangedAttack(damage=8, range=9, damage_type=Tags.Lightning))

	tree.stationary = True

	tree.max_hp = 550

	return tree

class TimeKeeperTimestop(Spell):

	def on_init(self):
		self.name = "Timestop"
		self.description = "Stun all enemies for 1 turn"
		self.cool_down = 3
		self.range = 0

	def cast_instant(self, x, y):
		for unit in self.caster.level.units:
			if are_hostile(self.caster, unit):
				unit.apply_buff(Stun(), 1)

	def can_cast(self, x, y):
		return True

def TimeKeeper():
	lord = Unit()
	lord.name = "Time Keeper"
	lord.tags = [Tags.Arcane, Tags.Construct]

	lord.max_hp = 300
	lord.shields = 3

	lord.spells.append(TimeKeeperTimestop())
	lord.spells.append(SimpleRangedAttack(damage=9, range=6, damage_type=Tags.Arcane))

	lord.resists[Tags.Arcane] = 75
	return lord

def RainbowDragon():
	dragon = Unit()
	dragon.name = "Rainbow Drake"

	dragon.max_hp = 38
	dragon.flying = True

	dragon.resists[Tags.Fire] = 75
	dragon.resists[Tags.Lightning] = 75
	dragon.resists[Tags.Arcane] = 75

	dragon.spells.append(VoidBreath())
	dragon.spells.append(StormBreath())
	dragon.spells.append(FireBreath())

	dragon.spells.append(SimpleMeleeAttack(8))

	dragon.tags = [Tags.Dragon, Tags.Living, Tags.Lightning, Tags.Fire, Tags.Arcane]

	return dragon

class BatBreath(BreathWeapon):

	def on_init(self):
		self.name = "Torrent of Bats"
		self.damage = 7
		self.damage_type = Tags.Physical

	def get_description(self):
		return "Breathes a cone of bats dealing %d damage to occupied tiles and summoning bats in empty ones." % self.damage

	def per_square_effect(self, x, y):
		
		unit = self.caster.level.get_unit_at(x, y)
		if unit:
			self.caster.level.deal_damage(x, y, self.damage, self.damage_type, self)
		else:
			self.summon(Bat(), Point(x, y))

def BatDragon():
	dragon = Unit()
	dragon.name = "Bat Dragon"

	dragon.max_hp = 38
	dragon.flying = True

	dragon.resists[Tags.Dark] = 50
	
	dragon.spells.append(BatBreath())

	dragon.spells.append(SimpleMeleeAttack(8))
	dragon.tags = [Tags.Dragon, Tags.Living, Tags.Dark]

	return dragon

class JarAlly(Spell):

	def on_init(self):
		self.name = "Pickle Soul"
		self.range = 10

	def get_description(self):
		return "A non construct ally loses 10 max hp but cannot die until the Giant Soul Jar is destroyed."

	def get_ai_target(self):
		candidates = [u for u in self.caster.level.get_units_in_los(self.caster) if not are_hostile(u, self.caster) and not u.has_buff(Soulbound) and Tags.Construct not in u.tags]
		candidates = [u for u in candidates if self.can_cast(u.x, u.y)]
		
		if not candidates:
			return None
		return random.choice(candidates)

	def cast(self, x, y):

		for p in self.caster.level.get_points_in_line(self.caster, Point(x, y), find_clear=True)[1:-1]:
			self.caster.level.deal_damage(p.x, p.y, 0, Tags.Dark, self)
			yield

		unit = self.caster.level.get_unit_at(x, y)
		if not unit:
			return

		unit.max_hp -= 10
		unit.max_hp = max(1, unit.max_hp)
		unit.cur_hp = min(unit.cur_hp, unit.max_hp)

		buff = Soulbound(self.caster)
		unit.apply_buff(buff)


def GiantSoulJar():
	jar = Unit()
	jar.stationary = True

	jar.max_hp = 100

	jar.tags = [Tags.Construct, Tags.Dark, Tags.Arcane]

	jar.name = "Giant Soul Jar"

	jar.spells.append(JarAlly())

	jar.resists[Tags.Physical] = -50
	jar.resists[Tags.Holy] = -100
	jar.resists[Tags.Fire] = 50
	jar.resists[Tags.Dark] = 100
	jar.resists[Tags.Arcane] = 50

	return jar

class MedusaSnakeBuff(Buff):

	def on_init(self):
		self.owner_triggers[EventOnDamaged] = self.on_damaged

	def on_damaged(self, evt):
		for i in range(math.ceil(evt.damage / 5)):
			self.summon(Snake())
			
	def get_tooltip(self):
		return "Spawns snakes when damaged.  One snake is spawned per 5 hp damage taken, rounded up."

class MedusaGaze(Spell):

	def on_init(self):
		self.name = "Medusa's Gaze"
		self.description = "Petrifies all units in line of sight for 3 turns"
		self.cool_down = 6
		self.range = 0

	def get_ai_target(self):
		if any(are_hostile(self.caster, u) for u in self.caster.level.get_units_in_los(self.caster)):
			return self.caster
		else:
			return None

	def get_impacted_tiles(self, x, y):
		return self.caster.level.get_points_in_los(self.caster)

	def cast_instant(self, x, y):
		for u in self.caster.level.get_units_in_los(self.caster):
			if u == self.caster:
				continue
			u.apply_buff(PetrifyBuff(), 3)

def Medusa():
	unit = Unit()

	unit.name = "Medusa"

	unit.max_hp = 57

	unit.spells.append(MedusaGaze())
	melee = SimpleMeleeAttack(damage=4, attacks=5, buff=Poison, buff_duration=3)
	melee.name = "Snake Bites"
	unit.spells.append(melee)

	unit.tags = [Tags.Nature, Tags.Arcane, Tags.Living, Tags.Dark]

	unit.buffs.append(MedusaSnakeBuff())
	return unit

def FlyTrap():
	unit = Unit()
	unit.name = "Fly Trap"
	unit.stationary = True
	unit.max_hp = 7

	unit.tags = [Tags.Living, Tags.Nature]

	fly_summon = SimpleSummon(FlyCloud, num_summons=3, cool_down=15)
	fly_summon.name = "Spawn Flies"
	fly_summon.description = "Summons 3 swarms of flies"
	unit.spells.append(fly_summon)
	tongue_attack = PullAttack(damage=2, range=10, color=Tags.Tongue.color)
	tongue_attack.name = "Tongue"
	tongue_attack.cool_down = 2
	unit.spells.append(tongue_attack)

	return unit

class WriteChaosScrolls(Spell):

	def on_init(self):
		self.name = "Scribe Chaos Scrolls"
		self.description = "Summon 2-4 living fireball or lightning scrolls"
		self.range = 0
		self.cool_down = 6

	def cast(self, x, y):

		for i in range(random.randint(2, 4)):
			unit = random.choice([LivingFireballScroll(), LivingLightningScroll()])
			self.summon(unit, sort_dist=False)
			yield

def ChaosQuill():
	unit = Unit()
	unit.name = "Chaos Quill"

	unit.max_hp = 15
	unit.shields = 6

	unit.spells.append(WriteChaosScrolls())

	unit.resists[Tags.Fire] = 75
	unit.resists[Tags.Lightning] = 75
	unit.resists[Tags.Arcane] = 100

	unit.stationary = True
	unit.flying = True
	unit.tags = [Tags.Chaos, Tags.Arcane, Tags.Construct]
	unit.buffs.append(TeleportyBuff(chance=.1, radius=5))
	return unit

class BoxOfWoeBuff(Buff):

	def on_init(self):

		self.owner_triggers[EventOnDeath] = self.on_death
		self.description = "Releases 3 evil spirits when destroyed"

	def on_death(self, evt):

		pain = Ghost()
		pain.name = "Pain"
		pain.asset_name = "pain_ghost"
		pain.max_hp = 24
		pain.spells.append(SimpleRangedAttack(damage=6, range=4, damage_type=Tags.Lightning))

		pain.resists[Tags.Lightning] = 50

		self.summon(pain)

		death = Ghost()
		death.name = "Death"
		death.asset_name = "death_ghost"
		death.max_hp = 24
		death.spells.append(SimpleRangedAttack(damage=6, range=4, damage_type=Tags.Dark))
		
		death.resists[Tags.Dark] = 100

		self.summon(death)

		sorrow = Ghost()
		sorrow.name = "Sorrow"
		sorrow.asset_name = "sorrow_ghost"
		sorrow.max_hp = 24
		sorrow.spells.append(SimpleRangedAttack(damage=6, range=4, damage_type=Tags.Ice))
		
		sorrow.resists[Tags.Ice] = 50
		
		self.summon(sorrow)


def BoxOfWoe():
	unit = Unit()
	unit.name = "Box of Woe"
	unit.max_hp = 25
	unit.shields = 2

	unit.stationary = True
	aura = DamageAuraBuff(damage=2, radius=9, damage_type=[Tags.Ice, Tags.Dark, Tags.Lightning])
	aura.name = "Aura of Woe"
	unit.buffs.append(aura)
	unit.buffs.append(BoxOfWoeBuff())

	unit.tags = [Tags.Arcane, Tags.Dark, Tags.Construct]

	unit.resists[Tags.Physical] = 50
	unit.resists[Tags.Dark] = 75

	return unit

class JackolanternBuff(Buff):
	def on_init(self):
		self.stack_type = STACK_INTENSITY
		self.name = "Halloween"
		self.asset = ['status', 'orange_bloodlust']
		self.global_bonuses['damage'] = 1
		self.color = Color(249, 168, 37)

class JackolanternSpell(Spell):
	def on_init(self):
		self.name = "Dark Winter Night"
		self.description = "Up to 4 random allied Dark units gain +1 damage for 25 turns"
		self.range = 0

	def can_cast(self, x, y):
		return any(u for u in self.caster.level.units if u != self.caster and not are_hostile(self.caster, u) and Tags.Dark in u.tags)		

	def cast_instant(self, x, y):
		targets = [u for u in self.caster.level.units if u != self.caster and not are_hostile(self.caster, u) and Tags.Dark in u.tags]
		random.shuffle(targets)
		for i in range(4):
			if not targets:
				break
			targets.pop().apply_buff(JackolanternBuff(), 25)

def Jackolantern():
	unit = Unit()
	unit.max_hp = 19
	unit.name = "Jack O' Lantern"
	unit.asset_name = "pumpkin"
	unit.spells.append(JackolanternSpell())
	unit.tags = [Tags.Dark, Tags.Nature, Tags.Construct]
	unit.stationary = True
	unit.resists[Tags.Dark] = 50
	unit.resists[Tags.Holy] = -50
	return unit


def AvianWizard():

	unit = Unit()
	unit.name = "Avian Wizard"

	unit.max_hp = 44
	unit.shields = 3

	def eagle():
		unit = Unit()
		unit.name = "Eagle"

		dive = LeapAttack(damage=7, range=5, is_leap=True)
		peck = SimpleMeleeAttack(damage=3)

		dive.name = 'Dive'
		peck.name = 'Claw'

		unit.spells.append(peck)
		unit.spells.append(dive)

		unit.max_hp = 18
		unit.flying = True

		unit.tags = [Tags.Living, Tags.Holy, Tags.Nature]
		unit.shields = 1
		return unit

	eagles = SimpleSummon(eagle, num_summons=2, cool_down=16)

	windride = MonsterTeleport()
	windride.cool_down = 18
	windride.requires_los = True
	windride.range = 20
	windride.name = "Ride the Wind"
	windride.description = "Teleports to a random tile in line of sight"

	healaura = WizardHealAura(heal=5, duration=7, cool_down=15)

	def make_clouds(caster, target):
		points = [p for p in target.level.get_points_in_ball(target.x, target.y, radius=3) if not target.level.tiles[p.x][p.y].cloud]
		random.shuffle(points)
		for i in range(4):
			if not points:
				break
			p = points.pop()
			target.level.add_obj(StormCloud(caster), p.x, p.y)

	stormy = SimpleRangedAttack(damage=4, damage_type=Tags.Lightning, range=9, onhit=make_clouds)
	stormy.name = "Storm Strike"
	stormy.description = "Creates storm clouds near the target"

	unit.spells = [eagles, windride, healaura, stormy]

	unit.resists[Tags.Lightning] = 100
	unit.resists[Tags.Holy] = 100

	unit.tags = [Tags.Living, Tags.Nature, Tags.Lightning]
	return unit

class WizardThunderStrike(Spell):

	def on_init(self):
		self.range = 8
		self.name = "Thunder Strike"
		self.damage = 9
		self.element = Tags.Lightning
		self.radius = 2
		self.duration = 3
		self.cool_down = 12

	def get_ai_target(self):
		# Try to hit something directly but settle for stunning something
		return Spell.get_ai_target(self) or self.get_corner_target(self.radius)

	def get_description(self):
		return "Stuns all enemies in an area around the target"

	def cast(self, x, y):
		duration = self.get_stat('duration')
		radius = self.get_stat('radius')
		
		self.caster.level.deal_damage(x, y, self.get_stat('damage'), self.element, self)
		yield 
		for stage in Burst(self.caster.level, Point(x, y), radius):
			for point in stage:

				self.caster.level.flash(point.x, point.y, Tags.Physical.color)
				cur_target = self.caster.level.get_unit_at(point.x, point.y)
				if cur_target and self.caster.level.are_hostile(cur_target, self.caster):
					cur_target.apply_buff(Stun(), self.get_stat('duration'))
			yield

class WizardGrounding(Spell):
	
	def on_init(self):
		self.name = "Lightning Protection"
		self.duration = 8
		self.description = "Grants caster and allies 50%% resistance to Lightning for %d turns" % self.duration
		self.cool_down = 12
		self.range = 0

	def cast(self, x, y):
		for u in self.caster.level.units:
			if not are_hostile(u, self.caster):
				u.apply_buff(ResistLightning(), self.get_stat('duration'))
				yield

class WizardLightningFlash(Spell):

	def on_init(self):
		self.damage = 3
		self.name = "Flash of Lightning"
		self.description = "Teleports the caster.  Blinds and deals damage to all units in line of sight on arrival for 1 turn."
		self.range = 20
		self.can_target_self = True

		self.cool_down = 16

	def get_ai_target(self):
		return self.caster

	def cast(self, x, y):
		randomly_teleport(self.caster, self.range, flash=True, requires_los=False)
		yield

		points = [p for p in self.caster.level.get_points_in_los(self.caster) if not (p.x == self.caster.x and p.y == self.caster.y)]

		random.shuffle(points)
		points.sort(key = lambda u: distance(self.caster, u))

		for p in points:
			unit = self.caster.level.get_unit_at(p.x, p.y)
	
			if unit:
				if are_hostile(self.owner, unit):
					continue
			
				self.caster.level.deal_damage(p.x, p.y, self.damage, Tags.Lightning, self)
				unit.apply_buff(BlindBuff(), 1)
				yield
			elif random.random() < .05:
				self.caster.level.deal_damage(p.x, p.y, self.damage, Tags.Lightning, self)
				yield				

def LightningWizard():
	unit = Unit()
	unit.name = "Lightning Master"
	unit.asset_name = "lightning_wizard"
	unit.max_hp = 32
	unit.shields = 8

	insulate = WizardGrounding()
	electrocute = SimpleRangedAttack(damage=6, damage_type=Tags.Lightning, range=9, beam=True)
	electrocute.name = "Lightning Bolt"

	thunderstrike = WizardThunderStrike()

	lflash = WizardLightningFlash()

	unit.tags = [Tags.Living, Tags.Lightning]

	unit.resists[Tags.Lightning] = 50

	unit.spells = [insulate, thunderstrike, lflash, electrocute]

	return unit

def FireWizard():
	unit = Unit()
	unit.max_hp = 70
	unit.name = "Fire Wizard"
	unit.asset_name = "fire_wizard"
	unit.tags = [Tags.Living, Tags.Fire]

	firedrake = SimpleSummon(FireDrake, cool_down=20)
	fireprot = FireProtection()
	fireball = SimpleRangedAttack(damage=9, damage_type=Tags.Fire, range=8, radius=2)

	unit.spells = [firedrake, fireprot, fireball]

	unit.resists[Tags.Fire] = 100

	return unit

class WizardStoneSkin(Spell):
	
	def on_init(self):
		self.name = "Stoneskin"
		self.duration = 8
		self.description = "Grants caster and allies 50%% resistance to Physical damage for %d turns" % self.duration
		self.cool_down = 12
		self.range = 0

	def cast(self, x, y):
		for u in self.caster.level.units:
			if not are_hostile(u, self.caster):
				u.apply_buff(Stoneskin(), self.get_stat('duration'))
				yield

class WizardEarthEle(Spell):

	def on_init(self):
		self.name = "Earthen Sentinel"
		self.description = "Summons a temporary earth elemental"
		self.range = 5
		self.cool_down = 5

	def get_ai_target(self):
		# Target something near an enemy
		return self.get_corner_target(2)

	def cast_instant(self, x, y):
		ele = Unit()
		ele.name = "Earth Elemental"
		ele.sprite.char = 'E'
		ele.sprite.color = Color(190, 170, 140)
		ele.spells.append(SimpleMeleeAttack(12))
		ele.max_hp = 55
		ele.turns_to_death = 15
		ele.stationary = True
		ele.team = self.caster.team
		ele.resists[Tags.Physical] = 50
		ele.resists[Tags.Fire] = 50
		ele.resists[Tags.Lightning] = 50
		ele.tags = [Tags.Elemental]
		self.summon(ele, Point(x, y))


def MountainWizard():
	unit = Unit()
	unit.name = "Mountain Mage"
	unit.asset_name = "mountain_wizard"
	unit.max_hp = 86

	stoneskin = WizardStoneSkin()
	quakeport = WizardQuakeport()
	earthele = WizardEarthEle()

	def wolf():
		wolf = Unit()
		wolf.max_hp = 12
		wolf.name = "Wolf"
		wolf.spells.append(SimpleMeleeAttack(5))
		wolf.spells.append(LeapAttack(5, damage_type=Tags.Physical, range=5))
		wolf.tags = [Tags.Living, Tags.Nature]
		return wolf

	wolves = SimpleSummon(wolf, cool_down=8, num_summons=1)
	wolves.name = "Summon Wolf"
	spikes = SimpleRangedAttack(damage=3, range=5)

	unit.spells = [stoneskin, earthele, wolves, quakeport, spikes]

	unit.tags = [Tags.Living, Tags.Nature]
	return unit

def MaskWizard():
	unit = Unit()
	unit.name = "Masked Wizard"
	unit.asset_name = "mask_wizard"
	unit.max_hp = 1
	unit.shields = 13

	voidbeam = SimpleRangedAttack(damage=6, damage_type=Tags.Arcane, range=14, beam=True, melt=True, cool_down=6)
	voidbeam.name = "Void Beam"

	def warp(caster, target):
		randomly_teleport(target, 5)

	disperse = SimpleRangedAttack(damage=3, damage_type=Tags.Arcane, range=8, radius=3, onhit=warp, cool_down=4)
	disperse.description = "Teleports units up to 5 tiles away"
	disperse.name = "Warp Ball"

	teleport = MonsterTeleport()
	teleport.cool_down = 9

	warptouch = SimpleMeleeAttack(damage=17, damage_type=Tags.Arcane)
	warptouch.name = "Warptouch"

	unit.resists[Tags.Arcane] = 100

	unit.tags = [Tags.Arcane]

	unit.spells = [voidbeam, disperse, teleport, warptouch]
	return unit

def ArachnidWizard():
	unit = Unit()
	unit.name = "Arachnid Wizard"

	unit.max_hp = 28
	unit.shields = 3

	unit.resists[Tags.Arcane] = 100
	unit.resists[Tags.Physical] = 75

	thorns = Spells.ThornyPrisonSpell()
	thorns.max_charges = 0
	thorns.cool_down = 13
	thorns.description = "Surrounds a group of units with thorny plants"
	thorns.minion_damage = 1

	voidorb = Spells.VoidOrbSpell()
	voidorb.max_charges = 0
	voidorb.cool_down = 9
	voidorb.range = 18
	voidorb.description = "Conjures a slow moving void orb"
	voidorb.damage = 7

	bite = SimpleMeleeAttack(4, damage_type=Tags.Arcane, buff=Poison, buff_duration=10)
	bite.name = "Spider Bite"

	unit.spells = [thorns, voidorb, bite]

	unit.tags = [Tags.Spider, Tags.Living, Tags.Arcane]

	unit.buffs.append(SpiderBuff())
	unit.buffs.append(TeleportyBuff(chance=.5, radius=7))

	return unit


class BeckonDragons(Spell):

	def on_init(self):
		self.name = "Beckon Dragons"
		self.description = "Calls 2 random dragons up from the chasms"
		self.cool_down = 22
		self.range = 0

	def cast(self, x, y):
		for i in range(2):
			
			tiles = [t for t in self.caster.level.iter_tiles() if t.is_chasm]
			
			if not tiles:
				tiles = [t for t in self.caster.level.iter_tiles()]

			tile = random.choice(tiles)

			dragon = random.choice([FireDrake, StormDrake, FireDrake, StormDrake, FireDrake, GoldDrake, VoidDrake, IceDrake])()
			self.summon(dragon, tile)
			yield

class StormBall(Spell):

	def on_init(self):
		self.name = "Storm Ball"
		self.description = "Creates thunderstorms and blizzards"
		self.radius = 2
		self.cool_down = 3

	def get_ai_target(self):
		return self.get_corner_target(self.get_stat('radius'))

	def cast(self, x, y):
		target = Point(x, y)
		for stage in Burst(self.caster.level, target, self.get_stat('radius')):
			for p in stage:
				if not self.caster.level.tiles[p.x][p.y].cloud:
					cloud = random.choice([StormCloud, BlizzardCloud])(self.caster)
					self.caster.level.add_obj(cloud, p.x, p.y)
			yield

class DarkBall(Spell):

	def on_init(self):
		self.name = "Dark Ball"
		self.description = "Deals dark and arcane damage, melts walls"
		self.radius = 2
		self.damage = 7
		self.cool_down = 3

	def get_ai_target(self):
		return self.get_corner_target(self.get_stat('radius'), requires_los=False)

	def cast(self, x, y):
		target = Point(x, y)
		for stage in Burst(self.caster.level, target, self.get_stat('radius'), ignore_walls=True):
			for p in stage:
				if random.random() < .5:
					if self.caster.level.tiles[p.x][p.y].is_wall():
						self.caster.level.make_floor(p.x, p.y)
					self.caster.level.deal_damage(p.x, p.y, self.get_stat('damage'), Tags.Arcane, self)
				else:
					self.caster.level.deal_damage(p.x, p.y, self.get_stat('damage'), Tags.Dark, self)
			yield

def DragonWizard():
	unit = Unit()
	unit.name = "Dragon Mage"
	unit.asset_name = "dragon_wizard"
	unit.max_hp = 160

	beckon = BeckonDragons()
	
	ball_range = 8
	chaosball = SimpleRangedAttack(damage=7, radius=2, range=ball_range, cool_down=3,
								   damage_type=[Tags.Fire, Tags.Lightning, Tags.Physical])
	chaosball.name = "Chaos Ball"
	stormball = StormBall()
	stormball.range = ball_range
	darkball = DarkBall()
	darkball.range = ball_range

	bite = SimpleMeleeAttack(8)

	unit.spells = [beckon, chaosball, stormball, darkball, bite]

	unit.resists[Tags.Fire] = 50
	unit.resists[Tags.Lightning] = 50
	unit.resists[Tags.Ice] = 50
	unit.resists[Tags.Arcane] = 50
	
	unit.tags = [Tags.Dragon, Tags.Living]

	return unit


class WizardBloodboil(Spell):

	def on_init(self):
		self.name = "Boiling Blood"
		self.description = "Allies in line of sight temporarily gain +4 damage to physical and fire attacks"
		self.duration = 7
		self.cool_down = 4
		self.range = 0

	def cast(self, x, y):

		for unit in self.caster.level.get_units_in_los(self.caster):
			if not self.caster.level.are_hostile(self.caster, unit) and unit != self.caster:
				buff = Spells.BloodlustBuff(self)
				buff.extra_damage = 4
				unit.apply_buff(buff, self.duration)

				# For the graphic
				unit.deal_damage(0, Tags.Fire, self)
				yield

def EarthTrollWizard():
	unit = EarthTroll()
	unit.max_hp = 120
	unit.name = "Troll Geomancer"
	unit.asset_name = "troll_wizard"

	def onhit(caster, target):
		target.apply_buff(PetrifyBuff(), 3)

	petrify = SimpleRangedAttack(damage=0, damage_type=Tags.Physical, range=5, cool_down=15)
	petrify.name = "Petrify"
	petrify.description = "Petrifies the target for 3 turns"

	def wolf():
		wolf = Unit()
		wolf.max_hp = 12
		wolf.name = "Clay Hound"
		wolf.asset_name = "earth_hound"

		wolf.resists[Tags.Physical] = 50
		wolf.resists[Tags.Fire] = 50
		wolf.resists[Tags.Lightning] = 50
		
		wolf.spells.append(SimpleMeleeAttack(5))
		wolf.spells.append(LeapAttack(5, damage_type=Tags.Physical, range=5))
		wolf.tags = [Tags.Living, Tags.Nature]
		wolf.buffs.append(RegenBuff(3))
		return wolf

	wolves = SimpleSummon(wolf, cool_down=8, num_summons=1)
	wolves.name = "Summon Clay Hound"

	bloodboil = WizardBloodboil()

	regen = WizardHealAura()

	melee = SimpleMeleeAttack(10)
	unit.spells = [petrify, wolves, bloodboil, regen, melee]

	unit.tags.append(Tags.Nature)
	return unit

class WizardMaw(Spells.VoidMaw):

	def on_init(self):
		Spells.VoidMaw.on_init(self)
		self.max_charges = 0
		self.cool_down = 5
		self.name = "Void Maw"
		self.description = "Summons a hungry maw"
		self.minion_damage = 4

	def get_ai_target(self):
		return self.get_corner_target(self.get_stat('minion_range'))

def VoidWizard():
	unit = Unit()
	unit.name = "Void Magus"
	unit.asset_name = "tentacled_wizard"
	unit.max_hp = 40
	unit.shields = 5

	maw = WizardMaw()
	shields = ShieldSightSpell(cool_down=7, shields=1)
	teleport = MonsterTeleport()
	teleport.cool_down = 8
	darkball = DarkBall()
	darkball.range = 6
	darkball.cool_down = 0
	darkball.damage = 4
	darkball.radius = 1

	darkball.name = "Nightmare Spark"

	unit.spells = [maw, shields, teleport, darkball]

	unit.resists[Tags.Arcane] = 75
	unit.resists[Tags.Dark] = 50

	unit.tags = [Tags.Arcane]
	return unit

def GlassWizard():
	unit = Unit()
	unit.name = "Glass Master"
	unit.asset_name = "glass_wizard"

	unit.max_hp = 34
	unit.shields = 7

	glassorb = Spells.GlassOrbSpell()
	glassorb.max_charges = 0
	glassorb.cool_down = 9
	glassorb.shield = 1
	glassorb.damage = 12
	glassorb.range = 14
	glassorb.duration = 1
	glassorb.description = "Conjures a glass orb that glassifies enemies, shields allies, and deals physical damage in a radius once it reaches its target."

	summon = SimpleSummon(GlassGolem, num_summons=2, cool_down=15, duration=10)
	teleport = MonsterTeleport()
	teleport.cool_down = 9

	shard = SimpleRangedAttack(damage=7, range=6)
	shard.name = "Glass Shard"

	unit.spells = [glassorb, summon, teleport, shard]

	unit.tags = [Tags.Arcane]

	unit.resists[Tags.Physical] = -50
	unit.resists[Tags.Arcane] = 50
	unit.resists[Tags.Fire] = 50
	unit.resists[Tags.Lightning] = 50
	unit.resists[Tags.Ice] = 50

	unit.tags = [Tags.Glass, Tags.Living]

	return unit

class WizardChaosWord(Spell):

	def on_init(self):
		self.name = "Invoke Chaos"
		self.description = "Teleport all other units to random locations.  All of those units are then stunned for 1 turn, with the exception of the Wizard."
		self.duration = 1
		self.cool_down = 20
		self.range = 0

	def cast(self, x, y):
		units = list(self.caster.level.units)
		random.shuffle(units)
		for unit in units:
			
			if unit == self.caster:
				continue


			teleport_targets = [t for t in self.caster.level.iter_tiles() if self.caster.level.can_stand(t.x, t.y, unit)]
			if not teleport_targets:
				continue

			teleport_target = random.choice(teleport_targets)

			for p in self.caster.level.get_points_in_line(unit, teleport_target):
				self.caster.level.show_effect(p.x, p.y, Tags.Translocation)

			self.caster.level.act_move(unit, teleport_target.x, teleport_target.y, teleport=True)

			if not unit.is_player_controlled:
				duration = self.get_stat('duration')
				unit.apply_buff(Stun(), self.get_stat('duration'))



			yield	

def ChaosWizard():

	unit = Unit()
	unit.name = "Demon Sorcerer"
	unit.asset_name = 'chaos_demon_wizard'
	unit.max_hp = 95
	unit.shields = 2

	impswarm = Spells.ImpGateSpell()
	impswarm.description = "Summons %d imps each turn for %d turns" % (impswarm.num_summons, impswarm.duration)
	impswarm.num_summons = 3
	impswarm.max_charges = 0
	impswarm.cool_down = 20		

	chaosword = WizardChaosWord()

	chaosaura = WizardNightmare(damage_type=[Tags.Physical, Tags.Fire, Tags.Lightning])
	chaosaura.name = "Chaos Aura"

	chaosball = SimpleRangedAttack(damage=6, radius=1, range=7, damage_type=[Tags.Fire, Tags.Lightning, Tags.Physical])
	chaosball.name = "Destruction"

	unit.spells = [impswarm, chaosword, chaosaura, chaosball]

	unit.resists[Tags.Physical] = 75
	unit.resists[Tags.Fire] = 75
	unit.resists[Tags.Lightning] = 75
	
	unit.tags = [Tags.Demon]

	return unit

class WizardIceEye(Spell):
	def on_init(self):
		self.name = "Eye of Ice"
		self.description = "Deals ice damage to a random enemy in line of sight each turn"
		self.cool_down = 25
		self.damage = 5
		self.duration = 9
		self.range = 0

	def cast_instant(self, x, y):
		buff = Spells.IceEyeBuff(self.get_stat('damage'), 1, self)
		self.caster.apply_buff(buff, self.get_stat('duration'))

def IceLich():
	unit = Unit()
	unit.max_hp = 75
	unit.shields = 2
	unit.name = "Ice Lich"
	unit.asset_name = "dark_ice_lich_wizard"

	iceeye = WizardIceEye()

	def freeze(caster, target):
		target.apply_buff(FrozenBuff(), 3)

	freezeball = SimpleRangedAttack(damage=7, radius=3, range=8, damage_type=Tags.Ice, onhit=freeze)
	freezeball.cool_down = 10
	freezeball.name = "Ice Ball"
	freezeball.description = "Freezes for 3 turns"

	deathtouch = SimpleMeleeAttack(23, damage_type=Tags.Dark)
	deathtouch.name = "Death Touch"

	sealsoul = LichSealSoulSpell()

	unit.spells = [deathtouch, iceeye, freezeball, sealsoul]

	unit.tags = [Tags.Undead, Tags.Dark, Tags.Ice]

	unit.resists[Tags.Dark] = 100
	unit.resists[Tags.Arcane] = 50
	unit.resists[Tags.Ice] = 75
	unit.resists[Tags.Fire] = -100

	return unit

class WizardFireEye(Spell):
	def on_init(self):
		self.name = "Eye of Fire"
		self.description = "Deals fire damage to a random enemy in line of sight each turn"
		self.cool_down = 25
		self.damage = 5
		self.damage_type = Tags.Fire
		self.duration = 9
		self.range = 0

	def cast_instant(self, x, y):
		buff = Spells.FireEyeBuff(self.get_stat('damage'), 1, self)
		self.caster.apply_buff(buff, self.get_stat('duration'))

def FireLich():

	unit = Unit()
	unit.max_hp = 75
	unit.shields = 2
	unit.name = "Fire Lich"
	unit.asset_name = "dark_fire_lich_wizard"
	
	fireeye = WizardFireEye()

	fireball = SimpleRangedAttack(damage=13, radius=4, range=8, damage_type=Tags.Fire)
	fireball.cool_down = 8
	fireball.name = "Fireball"

	deathtouch = SimpleMeleeAttack(23, damage_type=Tags.Dark)
	deathtouch.name = "Death Touch"

	sealsoul = LichSealSoulSpell()

	unit.spells = [deathtouch, fireeye, fireball, sealsoul]

	unit.resists[Tags.Dark] = 100
	unit.resists[Tags.Arcane] = 50
	unit.resists[Tags.Fire] = 75
	unit.resists[Tags.Ice] = -100

	unit.tags = [Tags.Undead, Tags.Dark, Tags.Fire]
	return unit


class WizardIceAge(Spell):

	def on_init(self):
		self.name = "Ice Age"
		self.description = "A burst of ice freezes all units in the radius.\nAllies are healed.\nEnemies take ice damage."
		self.duration = 4
		self.heal = 25
		self.damage = 8
		self.cool_down = 25
		self.range = 0
		self.radius = 8

	def get_ai_target(self):
		for stage in Burst(self.caster.level, self.caster, self.get_stat('radius')):
			for p in stage:
				unit = self.caster.level.get_unit_at(p.x, p.y)
				if unit and are_hostile(unit, self.caster):
					return self.caster
		return None

	def cast(self, x, y):
		for stage in Burst(self.caster.level, Point(x, y), self.get_stat('radius')):
			for p in stage:
				unit = self.caster.level.get_unit_at(p.x, p.y)
				if unit:
					unit.apply_buff(FrozenBuff(), 3)
					if are_hostile(unit, self.caster):
						unit.deal_damage(self.get_stat('damage'), Tags.Ice, self)
					else:
						unit.deal_damage(-self.get_stat('heal'), Tags.Heal, self)
				else:
					self.caster.level.deal_damage(p.x, p.y, 0, Tags.Ice, self)
			yield

class WizardIcicle(Spell):

	def on_init(self):
		self.name = "Icicle"
		self.description = "Deals ice and physical damage"
		self.damage = 4
		self.range = 6
		self.damage_type = [Tags.Physical, Tags.Ice]

	def cast(self, x, y):
		i = 0
		for point in self.caster.level.get_points_in_line(self.caster, Point(x, y), find_clear=True)[1:-1]:
			i += 1
			i = i % 2
			dtype = self.damage_type[i]
			self.caster.level.flash(point.x, point.y, dtype.color)
			yield

		for dtype in self.damage_type:
			self.caster.level.deal_damage(x, y, self.get_stat('damage'), dtype, self)
			for i in range(7):
				yield

def IceWizard():

	unit = Unit()
	unit.max_hp = 50
	unit.shields = 2

	unit.name = "Ice Wizard"

	blizzard = WizardBlizzard()

	icehounds = SimpleSummon(IceHound, num_summons=2, cool_down=16)

	iceage = WizardIceAge()

	icicle = WizardIcicle()

	unit.spells = [blizzard, icehounds, iceage, icicle]

	unit.resists[Tags.Ice] = 75

	unit.tags = [Tags.Ice, Tags.Living]

	return unit

class WizardIgnitePoison(Spell):

	def on_init(self):
		self.name = "Ignite Poison"
		self.description = "Target poisoned unit loses all poison stacks and takes that much fire damage"
		self.range = 10
		self.cool_down = 3

	def can_cast(self, x, y):
		unit = self.caster.level.get_unit_at(x, y)
		if not unit:
			return False
		return unit.has_buff(Poison)

	def cast(self, x, y):

		i = 0
		dtypes = [Tags.Fire, Tags.Poison]
		for p in self.caster.level.get_points_in_line(self.caster, Point(x, y), find_clear=True)[1:-1]:
			i += 1
			i %= 2
			self.caster.level.deal_damage(p.x, p.y, 0, dtypes[i], self)
			yield True

		# Why would we ever not have the buff?  Some krazy buff triggers probably
		target = self.caster.level.get_unit_at(x, y)
		assert(target)

		buff = target.get_buff(Poison)
		if buff:
			target.deal_damage(buff.turns_left, Tags.Fire, self)
			target.remove_buff(buff)

		yield False


def GoblinWizard():

	unit = Unit()
	unit.max_hp = 27
	unit.shields = 2

	unit.name = "Goblin Wizard"

	spiders = SimpleSummon(GiantSpider, num_summons=3, duration=20, cool_down=10)

	swap = HagSwap()
	swap.cool_down = 13
	swap.range = 6

	ignitepoison = WizardIgnitePoison()

	def poison(caster, target):
		target.apply_buff(Poison(), 4)

	sting = SimpleRangedAttack(damage=1, range=7, onhit=poison)
	sting.name = "Poison Sting"
	sting.description = "Applies poison for 7 turns"
	unit.spells = [spiders, ignitepoison, swap, sting]

	unit.tags = [Tags.Arcane, Tags.Nature, Tags.Living]

	return unit

class TwilightProtection(Spell):

	def on_init(self):
		self.name = "Twilight Protection"
		self.duration = 8
		self.description = "Grants caster and allies 50%% resistance to Dark and Holy damage for %d turns" % self.duration
		self.cool_down = 12
		self.range = 0

	def cast(self, x, y):
		for u in self.caster.level.units:
			if not are_hostile(u, self.caster):
				u.apply_buff(ResistDark(), self.get_stat('duration'))
				u.apply_buff(ResistHoly(), self.get_stat('duration'))
				yield	



class FireProtection(Spell):

	def on_init(self):
		self.name = "Fire Protection"
		self.duration = 8
		self.description = "Grants caster and allies 50%% resistance to Fire for %d turns" % self.duration
		self.cool_down = 12
		self.range = 0

	def cast(self, x, y):
		for u in self.caster.level.units:
			if not are_hostile(u, self.caster):
				u.apply_buff(ResistFire(), self.get_stat('duration'))
				yield	

class FrostfireProtection(Spell):
	
	def on_init(self):
		self.name = "Frostfire Protection"
		self.duration = 8
		self.description = "Grants caster and allies 50%% resistance to Fire and Ice for %d turns" % self.duration
		self.cool_down = 12
		self.range = 0

	def cast(self, x, y):
		for u in self.caster.level.units:
			if not are_hostile(u, self.caster):
				u.apply_buff(ResistFire(), self.get_stat('duration'))
				u.apply_buff(ResistIce(), self.get_stat('duration'))
				yield

class WizardIceGaze(Spell):

	def on_init(self):
		self.name = 'Gaze of Winter'
		self.description = "Freezes all units in line of sight for 3 turns"
		self.range = 0
		self.cool_down = 18

	def get_ai_target(self):
		for p in self.caster.level.get_points_in_los(self.caster):
			unit = self.caster.level.get_unit_at(p.x, p.y)
			if unit and are_hostile(self.caster, unit):
				return self.caster

	def get_impacted_tiles(self, x, y):
		return self.caster.level.get_points_in_los(self.caster)

	def can_threaten(self, x, y):
		return self.caster.level.can_see(self.caster.x, self.caster.y, x, y)

	def cast(self, x, y):
		points = [p for p in self.caster.level.get_points_in_los(self.caster) if not (p.x == self.caster.x and p.y == self.caster.y)]

		random.shuffle(points)
		points.sort(key = lambda u: distance(self.caster, u))

		for p in points:
			unit = self.caster.level.get_unit_at(p.x, p.y)
			if unit:
				self.caster.level.deal_damage(p.x, p.y, 0, Tags.Ice, self)
				unit.apply_buff(FrozenBuff(), 3)
				yield
			elif random.random() < .05:
				self.caster.level.deal_damage(p.x, p.y, 0, Tags.Ice, self)
				yield				

class WizardFrostfireHydra(Spell):

	def on_init(self):
		self.name = "Summon Frostfire Hydra"
		self.cool_down = 15
		self.minion_range = 9

	def can_cast(self, x, y):
		tile = self.caster.level.tiles[x][y]
		return not tile.unit and tile.can_walk and Spell.can_cast(self, x, y)

	def get_ai_target(self):
		return self.get_corner_target(self.get_stat('minion_range'))

	def cast_instant(self, x, y):

		unit = Unit()
		unit.max_hp = 18

		unit.name = "Frostfire Hydra"
		unit.asset_name = 'fire_and_ice_hydra'

		fire = SimpleRangedAttack(damage=6, range=9, damage_type=Tags.Fire, beam=True)
		fire.name = "Fire"
		fire.cool_down = 2

		ice = SimpleRangedAttack(damage=6, range=9, damage_type=Tags.Ice, beam=True)
		ice.name = "Ice"
		ice.cool_down = 2

		unit.stationary = True
		unit.spells = [ice, fire]

		unit.resists[Tags.Fire] = 100
		unit.resists[Tags.Ice] = 100

		unit.turns_to_death = 18
		
		unit.tags = [Tags.Fire, Tags.Ice, Tags.Dragon]
		
		self.summon(unit, Point(x, y))

def FrostfireWizard():
	unit = Unit()
	unit.name = "Frostfire Mage"
	unit.asset_name = 'fire_ice_wizard'

	unit.max_hp = 66
	unit.shields = 2

	summon = WizardFrostfireHydra()
	insulate = FrostfireProtection()

	gaze = WizardIceGaze()

	ball = SimpleRangedAttack(damage=7, damage_type=[Tags.Ice, Tags.Fire], range=7, radius=1)
	ball.name = "Hurl Frostfire"

	unit.spells = [summon, insulate, gaze, ball]

	unit.resists[Tags.Fire] = 50
	unit.resists[Tags.Ice] = 50
	unit.tags = [Tags.Fire, Tags.Ice, Tags.Living]
	return unit

class WizardStarfireBeam(Spell):

	def on_init(self):
		self.name = "Starfire Pulse"
		self.description = "Deals arcane damage in a beam, and fire damage adjacent to the beam.  Melts walls."
		self.cool_down = 17

		self.range = 12
		self.damage = 9

		self.requires_los = False

	def cast_instant(self, x, y):

		center_beam = self.caster.level.get_points_in_line(self.caster, Point(x, y))[1:]
		side_beam = []
		for p in center_beam:
			for q in self.caster.level.get_points_in_ball(p.x, p.y, 1.5):
				if q.x == self.caster.x and q.y == self.caster.y:
					continue
				if q not in center_beam and q not in side_beam:
					side_beam.append(q)

		for p in center_beam + side_beam:
			if self.caster.level.tiles[p.x][p.y].is_wall():
				self.caster.level.make_floor(p.x, p.y)

		for p in center_beam:
			self.caster.level.deal_damage(p.x, p.y, self.get_stat('damage'), Tags.Fire, self)

		for p in side_beam:
			self.caster.level.deal_damage(p.x, p.y, self.get_stat('damage'), Tags.Lightning, self)

class StarfireOrb(Spells.OrbSpell):

	def on_init(self):
		self.name = "Solar Orb"

		self.description = ("Create a slow moving searing orb"
							"\n\nEach turn, the orb deals damage to all enemies in line of sight."
							"\n\nAllies in line of sight are healed instead.")

		self.damage = 1
		self.cool_down = 12
		self.range = 12
		self.minion_health = 8

	def get_ai_target(self):
		return self.get_corner_target(6)

	def on_make_orb(self, orb):
		orb.asset_name = "searing_orb"
		orb.resists[Tags.Ice] = 0
		orb.resists[Tags.Arcane] = 0

	def on_orb_move(self, orb, next_point):
		for u in orb.level.get_units_in_los(next_point):
			if u == self.caster:
				continue
			if u == orb:
				continue
			if are_hostile(u, self.caster):
				u.deal_damage(1, Tags.Fire, self)
			else:
				u.deal_damage(-1, Tags.Heal, self)

def StarfireWizard():
	unit = Unit()
	unit.name = "Starfire Sorcerer"
	unit.asset_name = "starfire_wizard"
	
	unit.max_hp = 48
	unit.shields = 4

	summon = SimpleSummon(StarfireSpirit, num_summons=2, duration=8, cool_down=12)
	fatbeam = WizardStarfireBeam()
	orb = StarfireOrb()
	starfirebolt = SimpleRangedAttack(damage=6, radius=1, range=6, damage_type=[Tags.Arcane, Tags.Fire])
	starfirebolt.name = "Ball of Starfire"
	unit.spells = [summon, fatbeam, orb, starfirebolt]
	unit.tags = [Tags.Arcane, Tags.Fire, Tags.Living]
	unit.resists[Tags.Arcane] = 50
	unit.resists[Tags.Fire] = 50
	return unit

class TideOfSin(Spell):

	def on_init(self):
		self.name = "Tide of Sin"
		self.description = "All enemies in line of sight take damage and lose one random spell charge."
		self.damage = 1
		self.damage_type = Tags.Holy
		self.range = 0
		self.cool_down = 4

	def cast(self, x, y):
		for u in self.caster.level.get_units_in_los(self.caster):
			if not are_hostile(self.caster, u):
				continue
			self.caster.level.show_path_effect(self.caster, u, Tags.Holy, minor=True)
			u.deal_damage(self.damage, Tags.Holy, self)
			if u.is_player_controlled:
				drain_spell_charges(self.caster, u)
			yield

	def can_threaten(self, x, y):
		return self.caster.level.can_see(self.caster.x, self.caster.y, x, y)

class TideOfRot(Spell):

	def on_init(self):
		self.name = "Tide of Rot"
		self.description = "All enemies in line of sight lose 1 max hp and are poisoned for 4 turns."
		self.range = 0
		self.cool_down = 4

	def cast(self, x, y):
		for u in self.caster.level.get_units_in_los(self.caster):
			if not are_hostile(self.caster, u):
				continue
			self.caster.level.show_path_effect(self.caster, u, Tags.Poison, minor=True)
			u.apply_buff(Poison(), 4)
			
			drain_max_hp(u, 1)

			yield

	def can_threaten(self, x, y):
		return self.caster.level.can_see(self.caster.x, self.caster.y, x, y)

def BlackRider():
	unit = Unit()
	unit.max_hp = 374
	unit.name = "Black Rider"
	unit.asset_name = "black_horseman"

	unit.tags = [Tags.Holy, Tags.Demon]

	teleport = MonsterTeleport()
	teleport.cool_down = 20
	teleport.range = 50
	
	gaze = SimpleRangedAttack(damage=7, damage_type=Tags.Dark, range=8)

	unit.spells = [teleport, TideOfRot(), TideOfSin(), gaze]

	unit.resists[Tags.Dark] = 100
	unit.resists[Tags.Holy] = 100
	unit.resists[Tags.Poison] = 100

	return unit

def WhiteRider():
	unit = Unit()
	unit.max_hp = 374
	unit.name = "White Rider"
	unit.asset_name = "white_horseman"

	unit.tags = [Tags.Holy, Tags.Demon]

	unit.resists[Tags.Dark] = 100
	unit.resists[Tags.Holy] = 100
	unit.resists[Tags.Fire] = 50
	unit.resists[Tags.Physical] = 50

	teleport = MonsterTeleport()
	teleport.cool_down = 20
	teleport.range = 50

	halt = SimpleRangedAttack(damage=7, range=9, proj_name='gold_arrow', buff=Stun, buff_duration=1, cool_down=3)
	halt.name = "Arrow of Halting"
	poison = SimpleRangedAttack(damage=7, range=9, proj_name='gold_arrow', buff=Poison, buff_duration=10, cool_down=3)
	poison.name = "Arrow of Poison"
	fire = SimpleRangedAttack(damage=7, range=9, radius=3, damage_type=Tags.Fire, proj_name='gold_arrow', cool_down=3)
	fire.name = "Arrow of Flame"

	unit.spells = [teleport, halt, poison, fire]

	return unit

class RedRiderHealingBuff(Buff):

	def on_init(self):
		self.description = "Whenever another unit takes physical or fire damage, heals 5 hp."
		self.name = "Strife Healing"
		self.color = Tags.Fire.color
		self.global_triggers[EventOnDamaged] = self.on_damage

	def on_damage(self, evt):
		if evt.unit == self.owner:
			return

		if evt.damage_type not in [Tags.Fire, Tags.Physical]:
			return

		self.owner.deal_damage(-5, Tags.Heal, self)

class RedRiderBerserkingSpell(Spell):

	def on_init(self):
		self.name = "Strife"
		self.description = "Berserk all enemy summoned units in LOS for 3 turns"
		self.cool_down = 13
		self.duration = 3
		self.range = 0

	def get_ai_target(self):
		for u in self.caster.level.get_units_in_los(self.caster):
			if are_hostile(self.caster, u) and not u.is_player_controlled:
				return self.caster
		return None

	def cast(self, x, y):
		for u in self.caster.level.get_units_in_los(self.caster):
			if are_hostile(self.caster, u) and not u.is_player_controlled:
				u.apply_buff(BerserkBuff(), self.get_stat('duration'))
				yield

def RedRider():
	unit = Unit()

	unit.max_hp = 374
	unit.name = "Red Rider"
	unit.asset_name = "red_horseman"
	unit.tags = [Tags.Holy, Tags.Demon]

	teleport = MonsterTeleport()
	teleport.cool_down = 20
	teleport.range = 50

	unit.resists[Tags.Dark] = 100
	unit.resists[Tags.Holy] = 100
	unit.resists[Tags.Fire] = 50
	unit.resists[Tags.Physical] = 50

	unit.spells.append(teleport)
	unit.spells.append(RedRiderBerserkingSpell())
	unit.spells.append(SimpleMeleeAttack(damage=34))
	unit.spells.append(LeapAttack(damage=22, damage_type=Tags.Physical, range=10, is_leap=False))

	unit.buffs = [RedRiderHealingBuff()]
	return unit

def PaleRider():
	unit = Unit()

	unit.max_hp = 374

	unit.name = "Pale Rider"
	unit.asset_name = "pale_horseman"

	unit.tags = [Tags.Holy, Tags.Demon]
	unit.resists[Tags.Dark] = 100
	unit.resists[Tags.Holy] = 100
	unit.resists[Tags.Poison] = 100

	teleport = MonsterTeleport()
	teleport.cool_down = 20
	teleport.range = 50

	hades = SimpleSummon(Ghost, num_summons=7, cool_down=17)
	hades.name = "Army of Hades"

	earth = SimpleSummon(Bloodhound, num_summons=3, cool_down=17)
	earth.name = "Beasts of Earth"
	
	famine = SimpleRangedAttack(damage=5, damage_type=Tags.Poison, range=6, onhit=lambda caster, target: drain_max_hp(target, 3), cool_down=4)
	famine.name = "Famine Gaze"
	famine.description = "Drains 3 maximum hp"

	melee = SimpleMeleeAttack(26)

	unit.spells = [teleport, hades, earth, famine, melee]
	return unit

def TheFurnace():
	unit = Unit()
	unit.name = "The Furnace"
	unit.asset_name = "walking_furnace"

	unit.max_hp = 451

	unit.tags = [Tags.Fire, Tags.Construct, Tags.Metallic]
	unit.resists[Tags.Ice] = -100

	fire = SimpleRangedAttack(damage=6, range=4, beam=True, damage_type=Tags.Fire)
	unit.spells.append(fire)

	unit.buffs.append(DamageAuraBuff(damage=1, damage_type=Tags.Fire, radius=12))

	unit.buffs.append(GeneratorBuff(FurnaceHound, .1))
	unit.buffs.append(GeneratorBuff(FurnaceImp, .1))

	return unit

def PillarOfBone():
	unit = Unit()
	unit.max_hp = 400

	unit.name = "Pillar of Bones"
	unit.stationary = True

	summon_shambler = SimpleSummon(lambda: BoneShambler(32), cool_down=17, global_summon=True, max_channel=4, path_effect=Tags.Dark)
	summon_shambler.name = "Awaken Bone Shamblers"

	heal_undead = HealAlly(heal=32, range=RANGE_GLOBAL, tag=Tags.Undead)
	heal_undead.requires_los = False
	heal_undead.cool_down = 5

	bonespear = SimpleRangedAttack(damage=8, beam=True, range=12, cool_down=2)
	bonespear.name = "Bone Spear"

	unit.spells = [summon_shambler, heal_undead, bonespear]

	unit.resists[Tags.Physical] = 50

	unit.tags = [Tags.Undead, Tags.Dark]
	return unit

def PillarOfWorms():
	unit = Unit()
	unit.max_hp = 300

	unit.name = "Pillar of Worms"
	unit.stationary = True

	summon_shambler = SimpleSummon(WormShambler, cool_down=15, global_summon=True, max_channel=3, path_effect=Tags.Poison)

	heal_living = HealAlly(heal=20, range=RANGE_GLOBAL, tag=Tags.Living)
	heal_living.requires_los = False
	heal_living.cool_down = 5

	toxic_gaze = SimpleCurse(Poison, 20)
	toxic_gaze.name = "Poison"
	toxic_gaze.range = 10

	unit.spells = [summon_shambler, heal_living, toxic_gaze]

	unit.tags = [Tags.Living]

	unit.buffs.append(RegenBuff(3))
	return unit

class ImpHarvestBuff(Buff):

	def on_init(self):
		self.name = "Imp Harvest"
		self.description = "Cooldown counters reduced by 1 whenever a demon dies"
		self.global_triggers[EventOnDeath] = self.on_death
		self.color = Tags.Dark.color
		self.asset = ['status', 'soulbound']

	def on_death(self, evt):
		if not Tags.Demon in evt.unit.tags:
			return
		for spell in self.owner.spells:
			if self.owner.cool_downs.get(spell, 0):
				self.owner.cool_downs[spell] -= 1

def ImpCollector():
	unit = Unit()
	unit.max_hp = 54
	unit.shields = 1

	unit.name = "Imp Collector"

	def randomimp():
		return random.choice([FireImp, SparkImp, IronImp,
							  FurnaceImp, AshImp, ChaosImp,
							  TungstenImp, RotImp, CopperImp,
							  InsanityImp, VoidImp])()

	impspell = SimpleSummon(randomimp, num_summons=2, cool_down=5)
	impspell.name = "Call Imps"
	impspell.description = "Summon 2 random imps"

	harvest = WizardSelfBuff(ImpHarvestBuff, duration=5, cool_down=12)
	harvest.description = "For 5 turns, whenever a demon dies, reduce spell cool downs by 1"

	darkbolt = SimpleRangedAttack(damage=3, range=4, damage_type=Tags.Dark)

	unit.spells = [impspell, harvest, darkbolt]
	unit.resists[Tags.Dark] = 50

	unit.tags = [Tags.Living, Tags.Dark]
	return unit

class CoatlBreath(BreathWeapon):

	def __init__(self):
		BreathWeapon.__init__(self)
		self.name = "Emerald Breath"
		self.duration = 15
		self.damage_type = Tags.Poison
		self.cool_down = 6
		self.range = 7
		self.angle = math.pi / 6.0

	def get_description(self):
		return "Breath weapon, poisons living enemies and shields allies"

	def per_square_effect(self, x, y):
		unit = self.caster.level.get_unit_at(x, y)
		if unit and are_hostile(self.caster, unit) and Tags.Living in unit.tags:
			self.caster.level.deal_damage(x, y, 0, self.damage_type, self)
			unit.apply_buff(Poison(), self.get_stat('duration'))
		elif unit and not are_hostile(self.caster, unit):
			unit.add_shields(1)
		else:
			self.caster.level.deal_damage(x, y, 0, self.damage_type, self)

def FeatheredSerpent():
	unit = Unit()
	unit.max_hp = 97
	unit.shields = 1

	unit.flying = True

	unit.name = "Feathered Serpent"
	unit.asset_name = "coatl"

	teleport = MonsterTeleport()
	teleport.cool_down = 18
	teleport.range = RANGE_GLOBAL

	heal = HealAlly(25, range=10, tag=Tags.Living)
	heal.cool_down = 9

	abolt = SimpleRangedAttack(damage=3, damage_type=Tags.Arcane, range=16)
	abolt.cool_down = 2
	pbreath = CoatlBreath()

	melee = SimpleMeleeAttack(7)

	unit.spells = [teleport, heal, pbreath, abolt, melee]

	unit.resists[Tags.Poison] = 100
	unit.resists[Tags.Arcane] = 100
	unit.resists[Tags.Holy] = 100
	unit.resists[Tags.Dark] = -100

	unit.tags = [Tags.Living, Tags.Holy, Tags.Arcane]

	unit.buffs.append(ReincarnationBuff(2))
	return unit

def TwilightSeer():

	unit = Unit()
	unit.name = "Twilight Seer"
	unit.max_hp = 99
	unit.shields = 1

	protection = TwilightProtection()

	hblast = FalseProphetHolyBlast()
	hblast.range = 8
	hblast.cool_down = 2

	lifedrain = SimpleRangedAttack(damage=7, damage_type=Tags.Dark, drain=True, radius=2, range=8)
	lifedrain.name = "Life Siphon"
	lifedrain.cool_down = 2

	unit.spells = [protection, lifedrain, hblast]

	unit.resists[Tags.Dark] = 75
	unit.resists[Tags.Holy] = 75
	unit.tags = [Tags.Living, Tags.Dark, Tags.Holy]

	unit.buffs.append(ReincarnationBuff(1))
	return unit

def Enchanter():

	unit = Unit()
	unit.name = "Enchanter"
	unit.max_hp = 64

	regenaura = Spells.RegenAuraSpell()
	regenaura.cool_down = 32
	regenaura.duration = 8
	regenaura.heal = 8
	regenaura.radius = 4

	nightmare = WizardNightmare()
	
	freeze = SimpleCurse(FrozenBuff, 2)
	freeze.name = "Freeze"
	freeze.range = 5
	freeze.cool_down = 6

	shieldally = ShieldAllySpell(shields=3, range=9, cool_down=2)

	unit.spells = [regenaura, nightmare, freeze, shieldally]
	unit.tags = [Tags.Living, Tags.Enchantment]
	return unit

def Translocator():

	unit = Unit()
	unit.name = "Translocator"
	unit.asset_name = "translocation_master"

	unit.max_hp = 55
	unit.shields = 3

	teleport = MonsterTeleport()
	teleport.cool_down = 15

	swap = HagSwap()
	swap.cool_down = 2
	swap.requires_los = False
	swap.description += "\nIgnores walls."
	swap.range = 6

	phasebolt = SimpleRangedAttack(damage=2, range=4, damage_type=Tags.Arcane)
	phasebolt.onhit = lambda caster, target: randomly_teleport(target, 3)
	phasebolt.name = "Phase Bolt"
	phasebolt.description = "Teleports victims randomly up to 3 tiles away"

	unit.spells = [teleport, swap, phasebolt]

	unit.tags = [Tags.Arcane, Tags.Translocation]

	return unit


class ConstructShards(Buff):

	def on_init(self):
		self.name = "Necromechanomancery"
		self.global_triggers[EventOnDeath] = self.on_death
		self.description = "Whenever a friendly construct dies, deal 6 fire or physical damage to up to 3 enemies in a 4 tiles burst"

	def on_death(self, evt):
		if are_hostile(self.owner, evt.unit):
			return
		if not Tags.Construct in evt.unit.tags:
			return

		targets = self.owner.level.get_units_in_ball(evt.unit, 4)
		targets = [t for t in targets if self.owner.level.can_see(evt.unit.x, evt.unit.y, t.x, t.y) and are_hostile(self.owner, t)]

		random.shuffle(targets)
		for t in targets[:3]:

			for p in self.owner.level.get_points_in_line(evt.unit, t, find_clear=True)[1:-1]:
				dtype = random.choice([Tags.Fire, Tags.Physical])
				self.owner.level.show_effect(p.x, p.y, dtype, minor=True)

			dtype = random.choice([Tags.Fire, Tags.Physical])	
			t.deal_damage(6, dtype, self)

class IronShell(Buff):

	def on_init(self):
		self.resists[Tags.Physical] = 50
		self.resists[Tags.Fire] = 50
		self.buff_type = BUFF_TYPE_BLESS
		self.name = "Iron Plating"

def Mechanomancer():

	unit = Unit()
	unit.name = "Mechanomancer"
	unit.max_hp = 131

	golems = SimpleSummon(Golem, num_summons=2, cool_down=20)

	armor = SimpleCurse(IronShell, 16)
	armor.cool_down = 3
	armor.range = 6
	armor.name = "Iron Blessing"

	heal = HealAlly(25, 5, Tags.Construct)
	heal.cool_down = 5
	heal.name = "Reconstitution"

	spike = SimpleRangedAttack(damage=8, range=3)
	spike.name = 'Spikebolt'

	unit.spells = [golems, armor, heal, spike]


	unit.buffs.append(ConstructShards())

	unit.tags = [Tags.Construct]
	return unit

def GoldenBull():
	unit = Minotaur()
	unit.name = "Minos, The Golden Bull"
	unit.asset_name = "minotaur_gilded"

	unit.max_hp = 960

	for s in unit.spells:
		s.damage *= 2

	unit.resists[Tags.Dark] = 50
	unit.resists[Tags.Holy] = 50

	return unit

def TitanLord():
	unit = Titan()
	unit.is_boss = True
	unit.name = "Chronos, Titan Immortal"
	unit.asset_name = "titan_immortal"
	
	unit.max_hp = 1200
	unit.spells[1].damage = 28
	unit.spells[1].radius = 6
	unit.spells[1].cool_down = 3

	unit.buffs = [ReincarnationBuff(1), DamageAuraBuff(damage=2, damage_type=Tags.Fire, radius=9)]

	return unit

def AesirLord():
	unit = Aesir()
	unit.name = "Odin, Aesir Immortal"
	unit.asset_name = "aesir_immortal"
	unit.max_hp = 676

	unit.is_boss = True

	lightning = MonsterChainLightning()
	lightning.arc_range = 7
	lightning.damage = 14
	lightning.cool_down = 3

	thunder = WizardThunderStrike()

	melee = SimpleMeleeAttack(29)

	unit.spells = [thunder, lightning, melee]

	unit.buffs = [ReincarnationBuff(1)]

	return unit

class GeminiCloneSpell(Spell):

	def on_init(self):
		self.name = "Duplicate"
		self.description = ("Creates another Gemini Twin with equal HP to the current one.\n"
						    "Only two twins can exist at once.")
		self.range = 0

	def can_cast(self, x, y):
		num_geminis = len(list(u for u in self.caster.level.units if u.name == self.caster.name))
		return num_geminis < 2

	def cast_instant(self, x, y):
		clone = Gemini()
		clone.cur_hp = self.caster.cur_hp
		self.summon(clone)

def Gemini():
	unit = Unit()
	unit.name = "Gemini Twin"
	unit.asset_name = "gemini"
	unit.sprite.char = "G"
	unit.max_hp = 400
	
	unit.buffs = [HealAuraBuff(heal=3, radius=7)]

	unit.resists[Tags.Arcane] = 75
	unit.resists[Tags.Holy] = 75
	unit.resists[Tags.Dark] = 75
	
	clone = GeminiCloneSpell()

	teleport = MonsterTeleport()
	teleport.range = 15

	bolt = SimpleRangedAttack(range=25, damage_type=Tags.Arcane, damage=5)

	unit.tags = [Tags.Nature, Tags.Holy, Tags.Living, Tags.Arcane]

	unit.spells = [clone, teleport, bolt]

	return unit

def ThornTrouble(caster, target):
	randomly_teleport(target, 3)
	for i in range(3):
		thorn = FaeThorn()
		caster.level.summon(caster, thorn, target)

def Thornface():
	unit = Unit()
	unit.name = "The Mischief Maker"
	unit.asset_name = "gnomed_troubler"
	unit.max_hp = 1
	unit.shields = 33

	unit.stationary = True

	phasebolt = SimpleRangedAttack(damage=2, range=15, damage_type=Tags.Arcane)
	phasebolt.onhit = ThornTrouble
	phasebolt.name = "Thorncurse"
	phasebolt.description = "Teleports the target up to 3 tiles away and summons 3 fae thorns near them."
	unit.spells = [phasebolt]

	unit.resists[Tags.Arcane] = 100

	unit.tags = [Tags.Arcane]

	unit.buffs.append(TeleportyBuff(chance=.1, radius=8))

	return unit

def SlimeDrake():
	unit = Unit()
	unit.name = "Slime Drake"
	unit.flying = True
	unit.max_hp = 140

	unit.buffs.append(SlimeBuff(spawner=SlimeDrake, name="slime drakes"))
	
	unit.tags = [Tags.Slime, Tags.Dragon]

	unit.resists[Tags.Poison] = 100
	unit.resists[Tags.Physical] = 50

	poison_breath = FireBreath()
	poison_breath.damage_type = Tags.Poison
	poison_breath.name = "Poison Breath"

	melee = SimpleMeleeAttack(8)

	unit.spells = [poison_breath, melee]

	return unit

class ArcanePhoenixBuff(Buff):
	
	def on_init(self):
		self.color = Tags.Fire.color
		self.owner_triggers[EventOnDeath] = self.on_death
		self.name = "Phoenix Starfire"

	def get_tooltip(self):
		return "On death, deals 25 arcane damage to all tiles within 6.  Friendly units gain 2 SH instead of taking damage.  Melts walls."

	def on_death(self, evt):

		for p in self.owner.level.get_points_in_ball(self.owner.x, self.owner.y, 6):
			unit = self.owner.level.get_unit_at(*p)
			if unit and not are_hostile(unit, self.owner):
				unit.add_shields(2)
			else:
				self.owner.level.deal_damage(p.x, p.y, 25, Tags.Arcane, self)

			if not self.owner.level.tiles[p.x][p.y].can_see:
				self.owner.level.make_floor(p.x, p.y)

def VoidPhoenix():
	phoenix = Unit()
	phoenix.max_hp = 450
	phoenix.name = "Void Phoenix"
	phoenix.asset_name = "cosmic_bird"

	phoenix.tags = [Tags.Arcane, Tags.Holy]

	phoenix.buffs.append(ArcanePhoenixBuff())
	phoenix.buffs.append(ReincarnationBuff(1))

	phoenix.flying = True

	phoenix.resists[Tags.Arcane] = 100
	phoenix.resists[Tags.Dark] = -50

	phoenix.spells.append(SimpleRangedAttack(damage=9, range=5, damage_type=Tags.Arcane, melt=True))
	phoenix.buffs.append(DamageAuraBuff(damage=3, damage_type=Tags.Arcane, melt_walls=True, radius=9))
	return phoenix	


class IdolOfSlimeBuff(Buff):

	def on_init(self):

		self.description = "Whenever a non slime ally dies, summons a slime where that ally died."
		self.global_triggers[EventOnDeath] = self.on_death

	def on_death(self, evt):
		if Tags.Slime in evt.unit.tags:
			return

		if are_hostile(self.owner, evt.unit):
			return

		self.owner.level.queue_spell(self.make_slime(evt))

	def make_slime(self, evt):

		slime_options = [GreenSlime()]

		if Tags.Fire in evt.unit.tags:
			slime_options.append(RedSlime())
		if Tags.Ice in evt.unit.tags:
			slime_options.append(IceSlime())
		if Tags.Arcane in evt.unit.tags:
			slime_options.append(VoidSlime())
			
		slime = random.choice(slime_options)
		self.summon(slime, target=evt.unit)
		yield

def IdolOfSlime():
	unit = Idol()
	unit.name = "Slimesoul Idol"
	unit.buffs.append(IdolOfSlimeBuff())
	return unit

class CrucibleOfPainBuff(Buff):

	def on_init(self):

		self.global_triggers[EventOnDamaged] = self.on_damage
		self.counter = 0
		self.counter_max = 300
		self.description = "Spawn a furnace hound for every 300 damage dealt to any unit."

	def on_damage(self, evt):
		self.counter += evt.damage

		while self.counter >= self.counter_max:
			self.counter -= self.counter_max
			self.summon(FurnaceHound())

def CrucibleOfPain():
	unit = Idol()
	unit.name = "Crucible of Pain"
	unit.buffs.append(CrucibleOfPainBuff())
	return unit

class FieryVengeanceBuff(Buff):

	def on_init(self):
		self.global_triggers[EventOnDeath] = self.on_death
		self.description = "Whenever an ally dies, deals 9 fire damage to a random enemy unit up to 3 tiles away."
		self.name = "Idol of Fiery Vengeance"

	def on_death(self, evt):
		if are_hostile(evt.unit, self.owner):
			return

		self.owner.level.queue_spell(self.do_damage(evt))

	def do_damage(self, evt):
		units = self.owner.level.get_units_in_ball(evt.unit, 4)
		units = [u for u in units if are_hostile(self.owner, u)]
		random.shuffle(units)
		for unit in units[:1]:
			for p in self.owner.level.get_points_in_line(evt.unit, unit)[1:-1]:
				self.owner.level.show_effect(p.x, p.y, Tags.Fire)
			unit.deal_damage(9, Tags.Fire, self)
			yield

	def can_threaten(self, x, y):

		for u in self.owner.level.units:
			if are_hostile(u, self.owner):
				continue
			if distance(u, Point(x, y)) < 4:
				return True

		return False

def IdolOfFieryVengeance():
	unit = Idol()
	unit.name = "Idol of Fiery Vengeance"
	unit.buffs.append(FieryVengeanceBuff())
	return unit

class ConcussiveIdolBuff(Buff):

	def on_init(self):
		self.global_triggers[EventOnDamaged] = self.on_damage
		self.description = "Whenever an enemy takes damage, it is stunned for 1 turn."
		self.name = "Concussive Idol"

	def on_damage(self, evt):
		if not are_hostile(self.owner, evt.unit):
			return

		evt.unit.apply_buff(Stun(), 1)

def ConcussiveIdol():
	unit = Idol()
	unit.name = "Concussive Idol"
	unit.buffs.append(ConcussiveIdolBuff())
	return unit

class VampirismIdolBuff(Buff):

	def on_init(self):
		self.name = "Idol of Vampirism"
		self.global_triggers[EventOnDamaged] = self.on_damage
		self.description = "Whenever an ally deals damage, it heals for half that much HP."

	def on_damage(self, evt):
		if not evt.source:
			return

		if not evt.source.owner:
			return

		if are_hostile(self.owner, evt.source.owner):
			return

		heal = evt.damage // 2
		if heal <= 0:
			return

		evt.source.owner.deal_damage(-heal, Tags.Heal, self)

def VampirismIdol():
	unit = Idol()
	unit.buffs.append(VampirismIdolBuff())
	unit.name = "Idol of Vampirism"
	return unit


DIFF_EASY = 1
DIFF_MED = 2
DIFF_HARD = 3

# Spawner, Level, Rarity, Min, Max, (Req Tag)
rare_monsters = [
	(lambda : DampenerIdol('Weak', 'damage', 4), DIFF_EASY, 1, 4, None),
	(lambda: DampenerIdol('Foolish', 'range', 1), DIFF_EASY, 1, 4, None),
	(lambda: DampenerIdol('Fickle', 'duration', 3), DIFF_EASY, 1, 4, None),
	(Necromancer, DIFF_MED, 2, 3, Tags.Living),
	(WarBanner, DIFF_EASY, 1, 3, None),
	(Watcher, DIFF_EASY, 3, 7, None),
	(VoidWatcher, DIFF_MED, 2, 4, None),
	(FlyTrap, DIFF_EASY, 7, 13, None),
	(IdolOfUndeath, DIFF_MED, 2, 3, Tags.Undead),
	(IdolOfLife, DIFF_MED, 3, 5, Tags.Living),
	(DarkPriests, DIFF_MED, 2, 4, None),
	(OrcKing, DIFF_EASY, 1, 1, None),
	(OgreKing, DIFF_MED, 1, 1, None),
	(TrollKing, DIFF_MED, 1, 1, None),
	(GnomeKing, DIFF_MED, 1, 1, None),
	(MinotaurKing, DIFF_MED, 1, 1, None),
	(Dreamer, DIFF_HARD, 1, 1, None),
	(ChaosSpirit, DIFF_MED, 2, 4, None),
	(FallenAngel, DIFF_HARD, 1, 1, None),
	(SporeAncient, DIFF_HARD, 1, 1, None),
	(Tombstone, DIFF_MED, 2, 4, None),
	(TwistedTree, DIFF_HARD, 1, 1, None),
	(IdolOfSorcery, DIFF_MED, 2, 4, None),
	(IdolOfClarity, DIFF_EASY, 2, 4, None),
	(TimeKeeper, DIFF_HARD, 1, 1, None),
	(GiantSoulJar, DIFF_HARD, 3, 3, None),
	(Medusa, DIFF_HARD, 1, 1, None),
	(BatDragon, DIFF_EASY, 3, 4, None),
	(RedCyclops, DIFF_EASY, 2, 4, None),
	(SwampQueen, DIFF_EASY, 1, 1, None),
	(ChaosQuill, DIFF_EASY, 2, 3, None),
	(FireWyrmEgg, DIFF_MED, 6, 9, Tags.Fire),
	(IceWyrmEgg, DIFF_MED, 6, 9, Tags.Ice),
	(BoxOfWoe, DIFF_EASY, 1, 1, None),
	(Jackolantern, DIFF_EASY, 1, 1, Tags.Dark),
	(BoneWizard, DIFF_EASY, 1, 1, None),
	(AvianWizard, DIFF_EASY, 1, 1, None),
	(RavenMage, DIFF_EASY, 1, 1, None),
	(LightningWizard, DIFF_EASY, 1, 1, None),
	(MountainWizard, DIFF_EASY, 1, 1, None),
	(MaskWizard, DIFF_EASY, 1, 1, None),
	(ArachnidWizard, DIFF_EASY, 1, 1, None),
	(DragonWizard, DIFF_EASY, 1, 1, None),
	(EarthTrollWizard, DIFF_EASY, 1, 1, None),
	(VoidWizard, DIFF_EASY, 1, 1, None),
	(GlassWizard, DIFF_EASY, 1, 1, None),
	(ChaosWizard, DIFF_EASY, 1, 1, None),
	(TwilightSeer, DIFF_EASY, 1, 1, None),
	(IceLich, DIFF_EASY, 1, 1, None),
	(FireLich, DIFF_EASY, 1, 1, None),
	(IceWizard, DIFF_EASY, 1, 1, None),
	(GoblinWizard, DIFF_EASY, 1, 1, None),
	(FrostfireWizard, DIFF_EASY, 1, 1, None),
	(StarfireWizard, DIFF_EASY, 1, 1, None),
	(FireWizard, DIFF_EASY, 1, 1, None),
	(Enchanter, DIFF_EASY, 1, 1, None),
	(TroublerMass, DIFF_MED, 2, 3, None),
	(TroublerBig, DIFF_EASY, 2, 3, None),
	(VampireNecromancer, DIFF_MED, 1, 1, None),
	(VampireCount, DIFF_EASY, 2, 3, Tags.Dark),
	(BlackRider, DIFF_HARD, 1, 1, None),
	(WhiteRider, DIFF_HARD, 1, 1, None),
	(RedRider, DIFF_HARD, 1, 1, None),
	(PaleRider, DIFF_HARD, 1, 1, None),
	(TheFurnace, DIFF_HARD, 1, 1, None),
	(PillarOfBone, DIFF_MED, 1, 1, Tags.Undead),
	(PillarOfWorms, DIFF_MED, 1, 1, Tags.Living),
	(ImpCollector, DIFF_MED, 1, 1, None),
	(FeatheredSerpent, DIFF_MED, 1, 1, Tags.Living),
	(Translocator, DIFF_EASY, 1, 1, None),
	(Mechanomancer, DIFF_EASY, 1, 1, Tags.Construct),
	(GoldenBull, DIFF_HARD, 1, 1, None),
	(TitanLord, DIFF_HARD, 1, 1, None),
	(AesirLord, DIFF_HARD, 1, 1, None),
	(Gemini, DIFF_HARD, 1, 1, None),
	(Thornface, DIFF_HARD, 1, 1, None),
	(SlimeDrake, DIFF_HARD, 1, 1, None),
	(VoidPhoenix, DIFF_HARD, 1, 1, None),
	(IdolOfSlime, DIFF_MED, 1, 1, None),
	(CrucibleOfPain, DIFF_MED, 1, 1, None),
	(IdolOfFieryVengeance, DIFF_MED, 1, 1, None),
	(ConcussiveIdol, DIFF_MED, 1, 3, None),
	(VampirismIdol, DIFF_MED, 1, 1, None),
]

all_wizards = [
	(BoneWizard, DIFF_EASY, 1, 1, None),
	(AvianWizard, DIFF_EASY, 1, 1, None),
	(RavenMage, DIFF_EASY, 1, 1, None),
	(LightningWizard, DIFF_EASY, 1, 1, None),
	(MountainWizard, DIFF_EASY, 1, 1, None),
	(MaskWizard, DIFF_EASY, 1, 1, None),
	(ArachnidWizard, DIFF_EASY, 1, 1, None),
	(DragonWizard, DIFF_EASY, 1, 1, None),
	(EarthTrollWizard, DIFF_EASY, 1, 1, None),
	(VoidWizard, DIFF_EASY, 1, 1, None),
	(GlassWizard, DIFF_EASY, 1, 1, None),
	(ChaosWizard, DIFF_EASY, 1, 1, None),
	(TwilightSeer, DIFF_EASY, 1, 1, None),
	(IceLich, DIFF_EASY, 1, 1, None),
	(FireLich, DIFF_EASY, 1, 1, None),
	(IceWizard, DIFF_EASY, 1, 1, None),
	(GoblinWizard, DIFF_EASY, 1, 1, None),
	(FrostfireWizard, DIFF_EASY, 1, 1, None),
	(StarfireWizard, DIFF_EASY, 1, 1, None),
	(FireWizard, DIFF_EASY, 1, 1, None),
	(Enchanter, DIFF_EASY, 1, 1, None),
	(VampireNecromancer, DIFF_MED, 1, 1, None),
	(Translocator, DIFF_EASY, 1, 1, None),
	(Mechanomancer, DIFF_EASY, 1, 1, Tags.Construct)
]

for o in rare_monsters:
	assert(isinstance(o[0](), Unit))

def roll_rare_spawn(difficulty, tags, min_level=None, max_level=None, prng=None):

	if not prng:
		prng = random

	chosen_opt = None
	if 'forcerare' in sys.argv:
		forced = sys.argv[sys.argv.index('forcerare') + 1]
		chosen_opt = [o for o in rare_monsters if forced.lower() in o[0]().name.lower().replace(' ', '')][0]

	if not max_level:
		max_level = DIFF_EASY if difficulty < 10 else DIFF_MED if difficulty < 19 else DIFF_HARD

	def can_spawn(opt):
		if min_level is not None and opt[1] < min_level:
			return False
		if opt[1] > max_level:
			return False
		if opt[4] and opt[4] not in tags:
			return False
		return True

	if not chosen_opt:
		opts = [opt for opt in rare_monsters if can_spawn(opt)]
		chosen_opt = prng.choice(opts)

	spawner, diff, min_no, max_no, tag = chosen_opt

	numspawn = prng.randint(min_no, max_no)
	units = [spawner() for i in range(numspawn)]  

	if max_no == 1:
		for u in units:
			u.is_boss = True
			
	return units
