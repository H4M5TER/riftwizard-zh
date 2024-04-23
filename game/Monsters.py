"""
Spells, monsters, items
"""
from Level import *
from CommonContent import *
import random


class Breath():
	# A sequencing tool for breath weapons and other gaseous blasts
	def __init__(self, level, target, origin, size):
		self.level = level
		assert(isinstance(level, Level))
		assert(isinstance(target, Point))
		assert(isinstance(origin, Point))
		self.target = target
		self.origin = origin
		self.size = size

	def __iter__(self):
		#yield self.origin
		visited = set([self.origin])

		for i in range(self.size):
			candidates = []
			for previous in visited:
				for adj in self.level.get_points_in_ball(previous.x, previous.y, 1.5):

					if adj in visited:
						continue

					if not self.level.can_walk(adj.x, adj.y):
						continue

					candidates.append(adj)

			# Cut out anything behind the self.caster
			candidates = [c for c in candidates if abs(get_min_angle(self.origin.x, self.origin.y, self.target.x, self.target.y, c.x, c.y)) < (math.pi / 2.0)]

			if not candidates:
				return

			# Rank them by angle from target
			best_candidate = min(candidates, key=lambda x, y: abs(get_min_angle(self.origin.x, self.origin.y, self.target.x, self.target.y, x, y)))

			yield best_candidate
			visited.add(best_candidate)



class FireCloud(Cloud):

	def __init__(self):
		Cloud.__init__(self)
		self.duration = 3
		self.damage = 5
		self.color = Color(230, 0, 0)

	def on_advance(self):
		self.level.deal_damage(self.x, self.y, self.damage, Tags.Fire, self)

class BreathWeapon(Spell):

	def __init__(self):
		Spell.__init__(self)
		self.range = 7
		self.cool_down = 3
		self.angle = math.pi / 6.0
		self.ignore_walls = False
 
	def aoe(self, x, y):
		target = Point(x, y)
		return Burst(self.caster.level, 
				     Point(self.caster.x, self.caster.y), 
				     self.get_stat('range'), 
				     burst_cone_params=BurstConeParams(target, self.angle), 
				     ignore_walls=self.ignore_walls)
		
	def cast(self, x, y):
		for stage in self.aoe(x, y):
			for point in stage:
				self.per_square_effect(point.x, point.y)
			yield

	# Do not allow targeting of tiles that canot be hit
	# Otherwise the ai wil do weird things
	def can_cast(self, x, y):
		if Point(x, y) not in self.get_impacted_tiles(x, y):
			return False
		return Spell.can_cast(self, x, y)

	def get_impacted_tiles(self, x, y):
		return [p for stage in self.aoe(x, y) for p in stage]

	def per_square_effect(self, x, y):
		pass

class StormBreath(BreathWeapon):

	def on_init(self):
		self.name = "Storm Breath"
		self.damage = 10
		self.damage_type = Tags.Lightning

	def get_description(self):
		return "Breathes a cone of storm clouds, dealing %d damage" % self.damage

	def per_square_effect(self, x, y):
		self.caster.level.add_obj(StormCloud(self.caster, self.damage), x, y)


class FireBreath(BreathWeapon):

	def on_init(self):
		self.name = "Fire Breath"
		self.damage = 9
		self.damage_type = Tags.Fire

	def get_description(self):
		return "Breathes a cone of %s dealing %d damage" % (self.damage_type.name.lower(), self.damage)

	def per_square_effect(self, x, y):
		self.caster.level.deal_damage(x, y, self.damage, self.damage_type, self)

class IceBreath(BreathWeapon):

	def on_init(self):
		self.name = "Ice Breath"
		self.damage = 7
		self.damage_type = Tags.Ice
		self.freeze_duration = 2

	def get_description(self):
		return "Breathes a cone of ice dealing %d damage and freezing units for 2 turns" % self.damage

	def per_square_effect(self, x, y):
		self.caster.level.deal_damage(x, y, self.damage, self.damage_type, self)
		unit = self.caster.level.get_unit_at(x, y)
		if unit:
			unit.apply_buff(FrozenBuff(), self.get_stat('freeze_duration'))


class VoidBreath(BreathWeapon):

	def __init__(self):
		BreathWeapon.__init__(self)
		self.name = "Void Breath"
		self.damage = 9
		self.damage_type = Tags.Arcane
		self.requires_los = False
		self.ignore_walls = True

	def get_description(self):
		return "Breathes a cone of void dealing arcane damage and melting walls"

	def per_square_effect(self, x, y):

		if not self.caster.level.tiles[x][y].is_chasm:
			self.caster.level.make_floor(x, y)
		
		self.caster.level.deal_damage(x, y, self.damage, Tags.Arcane, self)

class HolyBreath(BreathWeapon):

	def on_init(self):
		self.name = "Holy Breath"
		self.description = "Breathes a cone of holy flame, dealing holy damage to enemies and healing allies"
		self.damage = 9
		self.damage_type = Tags.Holy

	def per_square_effect(self, x, y):
		unit = self.caster.level.get_unit_at(x, y)
		if unit and not are_hostile(self.caster, unit):
			# Dont heal or hurt friendly players.
			if not unit.is_player_controlled:
				self.caster.level.deal_damage(x, y, -self.damage, Tags.Heal, self)
		else:
			self.caster.level.deal_damage(x, y, self.damage, self.damage_type, self)

class DarkBreath(BreathWeapon):

	def on_init(self):
		self.name = "Dark Breath"
		self.description = "Breathes a cone of dark energy, dealing dark damage and reanimating slain units as skeletons."
		self.damage = 11
		self.damage_type = Tags.Dark

	def per_square_effect(self, x, y):
		unit = self.caster.level.get_unit_at(x, y)
		damage = self.get_stat('damage')
		
		self.caster.level.deal_damage(x, y, self.damage, self.damage_type, self)

		if unit and not unit.is_alive():
			raise_skeleton(self.caster, unit)

class SpiritBuff(Buff):

	def __init__(self, tag):
		Buff.__init__(self)
		self.tag = tag
 
	def on_applied(self, owner):
		self.global_triggers[EventOnSpellCast] = self.on_spell_cast

	def on_spell_cast(self, spell_cast_event):
		hp_gain = 5
		if (self.tag in spell_cast_event.spell.tags 
			and spell_cast_event.caster.is_player_controlled 
			and self.owner.level.can_see(self.owner.x, self.owner.y, spell_cast_event.x, spell_cast_event.y)):
			self.owner.max_hp += hp_gain
			self.owner.cur_hp += hp_gain
			self.owner.level.queue_spell(self.effect(spell_cast_event.x, spell_cast_event.y))


	def effect(self, x, y):
		for p in self.owner.level.get_points_in_line(Point(x, y), self.owner, find_clear=True):
			self.owner.level.flash(p.x, p.y, self.tag.color)
			yield
		self.owner.level.flash(self.owner.x, self.owner.y, Tags.Heal.color)


	def get_tooltip(self):
		return "Gain 5 max HP whenever witnessing %s spell" % self.tag.name

class LifeDrain(Spell):

	def on_init(self):
		self.name = "Life Drain"
		self.mana_cost = 10
		self.range = 4
		self.damage = 7
		self.damage_type = Tags.Dark
		self.tags = [Tags.Dark]

	def cast(self, x, y):
		damage = self.caster.level.deal_damage(x, y, self.damage, Tags.Dark, self)
		yield

		start = Point(self.caster.x, self.caster.y)
		target = Point(x, y)

		for point in Bolt(self.caster.level, target, start):
			# TODO- make a flash using something other than deal_damag, selfe
			self.caster.level.deal_damage(point.x, point.y, 0, Tags.Dark, self)
			yield

		self.caster.level.deal_damage(self.caster.x, self.caster.y, -damage, Tags.Heal, self)
		yield

	def get_description(self):
		return "Heals caster for damage dealt"


class NecromancyBuff(Buff):

	def on_applied(self, owner):
		self.global_triggers[EventOnDeath] = self.on_death
		self.radius = 10

	def on_death(self, death_event):
		if Tags.Living in death_event.unit.tags: 
			self.owner.level.queue_spell(self.raise_skeleton(death_event.unit))

	def raise_skeleton(self, unit):
		raise_skeleton(self.owner, unit)
		yield

	def get_tooltip(self):
		return "Whenever a non-undead unit dies, raises that unit as a skeleton."



class SporeBeastBuff(Buff):

	def on_init(self):
		self.name = "Spores"
		self.healing = 8
		self.radius = 2
		self.owner_triggers[EventOnDamaged] = self.on_damage_taken

	def on_damage_taken(self, event):
		if random.random() < .3:
			self.owner.level.queue_spell(self.heal_burst())

	def heal_burst(self):
		for stage in Burst(self.owner.level, Point(self.owner.x, self.owner.y), self.radius):
			for p in stage:
				self.owner.level.deal_damage(p.x, p.y, -self.healing, Tags.Heal, self)
			yield

	def get_tooltip(self):
		return "When damaged, has a 30%% chance to heal all units within %d tiles %d HP" % (self.radius, self.healing)

class SpikeBeastBuff(Buff):

	def on_init(self):
		self.name = "Spikebeast Spikes"
		self.damage = 8
		self.radius = 2
		self.owner_triggers[EventOnDamaged] = self.on_damage_taken

	def on_damage_taken(self, event):
		if random.random() < .3:
			self.owner.level.queue_spell(self.heal_burst())

	def heal_burst(self):
		for stage in Burst(self.owner.level, Point(self.owner.x, self.owner.y), self.radius):
			for p in stage:
				if p.x == self.owner.x and p.y == self.owner.y:
					continue
				self.owner.level.deal_damage(p.x, p.y, self.damage, Tags.Physical, self)
			yield

	def get_tooltip(self):
		return "When damaged, has a 30%% chance to deal %d physical damage to all units within %d tiles" % (self.damage, self.radius)

class BlizzardBeastBuff(Buff):

	def on_init(self):
		self.name = "Ice Spores"
		self.radius = 2
		self.owner_triggers[EventOnDamaged] = self.on_damaged
		self.description = "When damaged, creates 2 blizzards up to %d tiles away" % self.radius

	def on_damaged(self, evt):
		for i in range(2):
			points = self.owner.level.get_points_in_ball(self.owner.x, self.owner.y, self.radius)
			points = [p for p in points if not self.owner.level.tiles[p.x][p.y].cloud and self.owner.level.tiles[p.x][p.y].can_see]
			if points:
				p = random.choice(points)
				cloud = BlizzardCloud(self.owner)
				self.owner.level.add_obj(cloud, p.x, p.y)

class VoidBomberBuff(Buff):

	def on_init(self):
		self.radius = 1
		self.clusters = 0
		self.name = "Suicide Explosion"

	def on_applied(self, owner):
		self.owner_triggers[EventOnDeath] = self.on_death

	def on_death(self, death_event):
		self.owner.level.queue_spell(self.explode(self.owner.level, self.owner.x, self.owner.y))

	def get_tooltip(self):
		if self.clusters:
			return "Spawns %d void bombers on death" % self.clusters

	def explode(self, level, x, y):
		for p in level.get_points_in_rect(x - self.radius, y - self.radius, x + self.radius, y + self.radius):
			level.deal_damage(p.x, p.y, 12, Tags.Arcane, self)

			# Demolish the tile
			cur_tile = level.tiles[p.x][p.y]
			if not cur_tile.is_chasm:
				level.make_floor(p.x, p.y)

		for i in range(self.clusters):
			p = self.owner.level.get_summon_point(self.owner.x, self.owner.y, sort_dist=False, radius_limit=2)
			if p:
				for q in self.owner.level.get_points_in_line(self.owner, p)[1:-1]:
					self.owner.level.deal_damage(q.x, q.y, 0, Tags.Arcane, self)
				bomb = VoidBomber()
				bomb.team = self.owner.team
				self.owner.level.add_obj(bomb, p.x, p.y)

		yield

class VoidBomberSuicide(Spell):

	def on_init(self):
		self.range = 1.5
		self.melee = True
		self.name = "Suicide Explosion"

		self.description = "Suicide attack\n3x3 square area\nAutocast on death"

		#For tooltips
		self.damage = 12
		self.damage_type = Tags.Arcane

	def cast(self, x, y):
		self.caster.kill()
		yield

class FireBomberBuff(Buff):

	def on_init(self):
		self.name = "Suicide Explosion"
		self.radius = 2
		self.damage = 12
		self.clusters = 0

	def on_applied(self, owner):
		self.owner_triggers[EventOnDeath] = self.on_death

	def on_death(self, death_event):
		self.owner.level.queue_spell(self.explode(self.owner.level, self.owner.x, self.owner.y))

	def explode(self, level, x, y):
		# This is a weird aoe b which matches cast range
		for point in self.owner.level.get_points_in_ball(self.owner.x, self.owner.y, self.radius):
			if not self.owner.level.can_see(self.owner.x, self.owner.y, point.x, point.y):
				continue
			self.owner.level.deal_damage(point.x, point.y, self.damage, Tags.Fire, self)


		for i in range(self.clusters):
			p = self.owner.level.get_summon_point(self.owner.x, self.owner.y, sort_dist=False, radius_limit=2)
			if p:
				for q in self.owner.level.get_points_in_line(self.owner, p)[1:-1]:
					self.owner.level.deal_damage(q.x, q.y, 0, Tags.Fire, self)
				bomb = FireBomber()
				bomb.team = self.owner.team
				self.owner.level.add_obj(bomb, p.x, p.y)

		yield

class FireBomberSuicide(Spell):

	def on_init(self):
		self.range = 2
		self.name = "Suicide Explosion"

		#For tooltips
		self.damage = 12
		self.damage_type = Tags.Fire

		self.description = "Suicide attack\n2 tile radius\nAutocast on death"

	def cast(self, x, y):
		self.caster.kill()
		yield


#----
# Monsters
#-----
RED = 0
BLUE = 1
WHITE = 2


def Kobold():
	unit = Unit()
	unit.sprite.char = 'k'
	unit.sprite.color = Color(200, 140, 140)
	unit.name = "Kobold"
	unit.description = "A small wretched creature"
	unit.max_hp = 4
	bow = SimpleRangedAttack(damage=1, range=10, proj_name="kobold_arrow")
	bow.name = "Bow"
	bow.cooldown = 2
	unit.spells.append(bow)
	unit.tags = [Tags.Living]
	return unit

def Golem():
	unit = Unit()
	unit.sprite.char = 'G'
	unit.sprite.color = Color(140, 140, 145)
	unit.name = "Golem"
	unit.max_hp = 25
	unit.description = "An animated creation of stone and steel"
	unit.spells.append(SimpleMeleeAttack(8))
	unit.tags = [Tags.Construct, Tags.Metallic]
	return unit

def Thunderbird():
	unit = Unit()
	unit.name = "Thunderbird"
	unit.max_hp = 22
	unit.shields = 1

	unit.flying = True

	claw = SimpleMeleeAttack(damage=5, damage_type=Tags.Lightning)
	claw.name = "Lightning Talons"

	dive = LeapAttack(damage=5, damage_type=Tags.Lightning, range=5, is_leap=True)
	dive.name = "Lightning Dive"
	dive.cool_down = 3

	unit.spells.append(dive)
	unit.spells.append(claw)

	unit.resists[Tags.Lightning] = 75
	unit.tags = [Tags.Lightning, Tags.Nature, Tags.Living]

	return unit

def SpikeBall():
	unit = Unit()
	unit.name = "Rolling Spike Ball"
	unit.max_hp = 60
	unit.spells.append(SimpleMeleeAttack(9, trample=True))
	unit.buffs.append(Thorns(6))
	unit.tags = [Tags.Construct, Tags.Metallic]
	return unit

def SpikeBallCopper():
	unit = SpikeBall()
	unit.name = "Copper Spike Ball"
	unit.asset_name = "rolling_spike_ball_copper"

	unit.buffs.append(DamageAuraBuff(damage_type=Tags.Lightning, damage=3, radius=2))
	return unit

def Cyclops():
	unit = Unit()
	unit.sprite.char = 'G'
	unit.sprite.color = Color(180, 180, 185)
	unit.name = "Cyclops"
	unit.max_hp = 55
	boulder = SimpleRangedAttack(damage=12, damage_type=Tags.Physical, range=10, radius=1)
	boulder.cool_down = 5
	boulder.onhit = lambda caster, target: target.apply_buff(Stun(), 1)
	boulder.cooldown = 6
	boulder.name = "Throw boulder"
	boulder.description = "Stuns for 1 turn"
	unit.spells.append(boulder)
	unit.spells.append(SimpleMeleeAttack(9))
	unit.tags = [Tags.Living]
	return unit

def StormDrake():
	unit = Unit()
	unit.sprite.char = 'D'
	unit.sprite.color = Color(190, 190, 250)
	unit.name = "Storm Drake"
	unit.description = "Breathes stormclouds"
	unit.max_hp = 38
	unit.flying = True
	unit.spells.append(StormBreath())
	unit.spells.append(SimpleMeleeAttack(8))
	unit.resists[Tags.Lightning] = 100
	unit.tags = [Tags.Dragon, Tags.Living, Tags.Lightning]
	return unit

def FireDrake():
	unit = Unit()
	unit.sprite.char = 'D'
	unit.sprite.color = Color(250, 60, 80)
	unit.name = "Fire Drake"
	unit.description = "Breathes fire"
	unit.max_hp = 38
	unit.flying = True
	unit.spells.append(FireBreath())
	unit.spells.append(SimpleMeleeAttack(8))
	unit.resists[Tags.Fire] = 100
	unit.resists[Tags.Ice] = -50
	unit.tags = [Tags.Dragon, Tags.Living, Tags.Fire]
	return unit

def VoidDrake():
	unit = Unit()
	unit.sprite.char = 'D'
	unit.sprite.color = Tags.Arcane.color
	unit.name = "Void Drake"
	unit.description = "Breathes void, destroying walls"
	unit.max_hp = 38
	unit.flying = True
	unit.spells.append(VoidBreath())
	unit.spells.append(SimpleMeleeAttack(8))
	unit.resists[Tags.Arcane] = 100
	unit.tags = [Tags.Dragon, Tags.Living, Tags.Arcane]
	return unit

def GoldDrake():
	unit = Unit()
	unit.sprite.char = 'D'
	unit.sprite.color = Tags.Holy.color
	unit.name = "Gold Drake"
	unit.description = "Breathes holy fire, damaging enemies but healing allies"
	unit.max_hp = 38
	unit.flying = True
	unit.spells.append(HolyBreath())
	unit.spells.append(SimpleMeleeAttack(8))
	unit.resists[Tags.Holy] = 100
	unit.tags = [Tags.Dragon, Tags.Living, Tags.Holy]
	return unit

def Dracolich():
	unit = Unit()
	unit.name = "Dracolich"
	unit.asset_name = "bone_drake"
	unit.max_hp = 38
	unit.flying = True
	unit.spells = [LichSealSoulSpell(), DarkBreath(), SimpleMeleeAttack(8)]
	unit.resists[Tags.Dark] = 100
	unit.tags = [Tags.Dragon, Tags.Undead, Tags.Dark]
	return unit

def IceDrake():
	unit = Unit()
	unit.name = "Ice Drake"
	unit.max_hp = 38
	unit.flying = True
	unit.spells.append(IceBreath())
	unit.spells.append(SimpleMeleeAttack(8))
	unit.resists[Tags.Ice] = 100
	unit.resists[Tags.Fire] = -50
	unit.tags = [Tags.Dragon, Tags.Living, Tags.Ice]
	return unit

def FireWyrm():
	unit = Unit()
	unit.name = "Fire Wyrm"
	unit.asset_name = "wyrm_red"
	unit.max_hp = 75

	unit.spells.append(FireBreath())
	unit.spells.append(SimpleMeleeAttack(14, trample=True))

	unit.buffs.append(RegenBuff(8))

	unit.tags = [Tags.Fire, Tags.Dragon, Tags.Living]

	unit.resists[Tags.Fire] = 100
	unit.resists[Tags.Ice] = -50

	return unit

def IceWyrm():
	unit = Unit()
	unit.name = "Ice Wyrm"
	unit.asset_name = "wyrm_blue"

	unit.max_hp = 75

	unit.spells.append(IceBreath())
	unit.spells.append(SimpleMeleeAttack(14, trample=True))

	unit.tags = [Tags.Ice, Tags.Dragon, Tags.Living]

	unit.resists[Tags.Ice] = 100
	unit.resists[Tags.Fire] = -50
	
	unit.buffs.append(RegenBuff(8))

	return unit

def FireWyrmEgg():
	unit = Unit()
	unit.name = "Fire Wyrm Egg"
	unit.asset_name = "red_wyrm_egg"

	unit.max_hp = 14

	unit.stationary = True
	unit.buffs.append(RespawnAs(FireWyrm))

	unit.resists[Tags.Fire] = 100
	unit.resists[Tags.Physical] = 50
	unit.tags = [Tags.Living, Tags.Fire]
	return unit


def IceWyrmEgg():
	unit = Unit()
	unit.name = "Ice Wyrm Egg"
	unit.asset_name = "blue_wyrm_egg"

	unit.max_hp = 14

	unit.stationary = True
	unit.buffs.append(RespawnAs(IceWyrm))

	unit.resists[Tags.Ice] = 100
	unit.resists[Tags.Physical] = 50
	unit.tags = [Tags.Living, Tags.Ice]
	return unit

def FireImp():
	unit = Unit()
	unit.sprite.char = 'i'
	unit.sprite.color = Color(200, 60, 70)
	unit.name = "Fire Imp"
	unit.description = "Fires projectiles"
	unit.max_hp = 5
	unit.resists[Tags.Fire] = 75
	unit.resists[Tags.Ice] = -75
	unit.resists[Tags.Dark] = 75
	unit.spells.append(SimpleRangedAttack(name="Imp Fire", damage=3, range=3, damage_type=Tags.Fire))
	unit.tags = [Tags.Demon, Tags.Fire]
	unit.flying = True
	return unit

def SparkImp():
	unit = Unit()
	unit.sprite.char = 'i'
	unit.sprite.color = Color(190, 190, 250)
	unit.name = "Spark Imp"
	unit.description = "Fires projectiles"
	unit.max_hp = 5
	unit.resists[Tags.Lightning] = 75
	unit.resists[Tags.Dark] = 75
	unit.spells.append(SimpleRangedAttack(name="Imp Spark", damage=3, range=3, damage_type=Tags.Lightning))
	unit.tags = [Tags.Demon, Tags.Lightning]
	unit.flying = True
	return unit

def IronImp():
	unit = Unit()
	unit.sprite.char = 'i'
	unit.sprite.color = Color(140, 140, 145)
	unit.name = "Iron Imp"
	unit.description = "Fires projectiles"
	unit.max_hp = 5
	unit.resists[Tags.Dark] = 75
	unit.spells.append(SimpleRangedAttack(name="Imp Shot", damage=3, range=3, damage_type=Tags.Physical))
	unit.tags = [Tags.Demon, Tags.Metallic]
	unit.flying = True
	return unit

def ChaosImp():
	unit = FireImp()
	unit.max_hp = 12
	unit.name = "Chaos Imp"
	unit.asset_name = "imp_chaos"
	unit.resists[Tags.Lightning] = 75

	shards = SimpleRangedAttack(damage=6, range=3, damage_type=[Tags.Lightning, Tags.Fire], radius=1)
	shards.name = "Chaos Shards"
	unit.spells = [shards]

	unit.tags.append(Tags.Lightning)
	return unit

def FurnaceImp():
	unit = FireImp()
	unit.max_hp = 12
	unit.name = "Furnace Imp"
	unit.asset_name = "imp_furnace"
	unit.resists[Tags.Physical] = 75

	shards = SimpleRangedAttack(damage=4, range=3, damage_type=[Tags.Physical, Tags.Fire], radius=1)
	shards.name = "Furnace Shards"
	unit.spells = [shards]

	unit.buffs.append(DamageAuraBuff(damage=1, damage_type=Tags.Fire, radius=4))
	unit.resists[Tags.Ice] = -50
	unit.tags.append(Tags.Metallic)
	return unit

def AshImp():
	unit = FireImp()
	unit.max_hp = 16
	unit.name = "Ash Imp"
	unit.asset_name = "imp_ash"

	shards = SimpleRangedAttack(damage=6, range=3, damage_type=Tags.Fire, buff=BlindBuff, buff_duration=1)
	shards.name = "Ash Bolt"
	unit.spells = [shards]
	return unit

def TungstenImp():
	unit = IronImp()
	unit.name = "Tungsten Imp"
	unit.asset_name = "imp_tungsten"
	unit.max_hp = 14
	unit.resists[Tags.Physical] = 90
	unit.resists[Tags.Arcane] = 50
	return unit

def RotImp():
	unit = Unit()
	unit.max_hp = 12
	unit.name = "Rot Imp"
	unit.asset_name = "imp_rot"
	def onhit(caster, target):
		drain_max_hp(target, 1)

	rot = SimpleRangedAttack(damage=3, range=4, damage_type=Tags.Dark, onhit=onhit)
	rot.description = "Removes 1 max hp from the target"
	rot.name = 'Rot Bolt'

	unit.spells = [rot]
	unit.tags = [Tags.Dark, Tags.Demon]

	unit.resists[Tags.Dark] = 75
	return unit

def CopperImp():
	unit = IronImp()
	unit.max_hp = 12
	unit.name = "Copper Imp"
	unit.asset_name = "imp_copper"
	lbolt = SimpleRangedAttack(damage=4, range=5, beam=True, damage_type=Tags.Lightning)
	lbolt.name = "Lightning Bolt"
	lbolt.cool_down = 2
	coppershard = SimpleRangedAttack(damage=7, range=3, damage_type=Tags.Physical)
	coppershard.cool_down = 2
	unit.spells = [lbolt, coppershard]
	unit.tags.append(Tags.Lightning)
	return unit

def InsanityImp():
	unit = Unit()
	unit.flying = True
	unit.tags = [Tags.Demon, Tags.Arcane]
	unit.max_hp = 12
	unit.name = "Insanity Imp"
	unit.asset_name = "imp_insanity"

	unit.resists[Tags.Arcane] = 75
	unit.resists[Tags.Dark] = 75

	def onhit(caster, target):
		randomly_teleport(target, 4)

	insanity = SimpleRangedAttack(damage=3, range=6, damage_type=Tags.Arcane, onhit=onhit)
	insanity.description = "Teleports target unit up to 4 tiles away"
	insanity.name = "Phase Bolt"
	unit.spells = [insanity]

	return unit

def VoidImp():
	unit = Unit()
	unit.flying = True
	unit.tags = [Tags.Demon, Tags.Arcane]
	unit.max_hp = 12
	unit.name = "Void Imp"
	unit.asset_name = "imp_aether"
	unit.resists[Tags.Arcane] = 75
	unit.resists[Tags.Dark] = 75

	void = SimpleRangedAttack(damage=3, range=5, damage_type=Tags.Arcane, beam=True, melt=True)
	unit.spells.append(void)
	return unit

def IronImpGiant():
	unit = IronImp()
	unit.name = "Giant Iron Imp"
	unit.asset_name = "iron_imp_giant"
	unit.max_hp = 33
	unit.spells[0].damage = 9
	unit.spells[0].range = 4
	return unit
	
def FireImpGiant():
	unit = FireImp()
	unit.name = "Giant Fire Imp"
	unit.asset_name = "fire_imp_giant"
	unit.max_hp = 33
	unit.spells[0].damage = 9
	unit.spells[0].range = 4
	return unit

def SparkImpGiant():
	unit = SparkImp()
	unit.name = "Giant Spark Imp"
	unit.asset_name = "spark_imp_giant"
	unit.max_hp = 33
	unit.spells[0].damage = 9
	unit.spells[0].range = 4
	return unit

def FireSpirit():
	unit = Unit()
	unit.sprite.char = 'S'
	unit.sprite.color = Color(200, 60, 70)
	unit.name = "Fire Spirit"
	unit.description = "Gains 6 HP whenever a fire spell is cast"
	unit.max_hp = 10
	unit.buffs.append(SpiritBuff(Tags.Fire))
	unit.buffs.append(Thorns(4, Tags.Fire))
	unit.resists[Tags.Fire] = 100
	unit.resists[Tags.Ice] = -100
	unit.spells.append(SimpleRangedAttack(name="Spirit Fire", damage=5, range=5, damage_type=Tags.Fire))
	unit.tags = [Tags.Fire]
	return unit

def SparkSpirit():
	unit = Unit()
	unit.sprite.char = 'S'
	unit.sprite.color = Color(190, 190, 250)
	unit.name = "Spark Spirit"
	unit.description = "Fires projectiles"
	unit.max_hp = 10
	unit.buffs.append(SpiritBuff(Tags.Lightning))
	unit.buffs.append(Thorns(4, Tags.Lightning))
	unit.resists[Tags.Lightning] = 100
	unit.spells.append(SimpleRangedAttack(name="Spirit Spark", damage=5, range=5, damage_type=Tags.Lightning))
	unit.tags = [Tags.Lightning]
	return unit

def FlyCloud():
	unit = Unit()
	unit.name = "Fly Swarm"
	unit.asset_name = "fly_swarm"
	unit.tags = [Tags.Living, Tags.Dark]
	unit.max_hp = 6
	unit.resists[Tags.Physical] = 75
	unit.resists[Tags.Dark] = 75
	unit.resists[Tags.Ice] = -50
	unit.flying = 1
	unit.spells.append(SimpleMeleeAttack(1))
	return unit

class BagOfBugsBuff(Buff):

	def __init__(self, spawn):
		self.spawn = spawn
		self.spawns = 4
		Buff.__init__(self)

	def on_init(self):
		self.owner_triggers[EventOnDeath] = self.on_death

	def get_tooltip(self):
		return "Spawns %d %ss on death" % (self.spawns, self.spawn().name)

	def on_death(self, evt):
		self.make_flies()

	def make_flies(self):
		for i in range(self.spawns):
			flies = self.spawn()
			self.owner.level.summon(self.owner, flies)

def BagOfBugs(spawn=FlyCloud):
	unit = Unit()
	unit.name = "Bag of Bugs"
	unit.max_hp = 16

	unit.spells.append(SimpleMeleeAttack(4))
	unit.buffs.append(BagOfBugsBuff(spawn))

	unit.tags = [Tags.Dark, Tags.Construct]

	unit.resists[Tags.Dark] = 50
	unit.resists[Tags.Physical] = 25
	unit.resists[Tags.Fire] = -100

	unit.buffs.append(GeneratorBuff(spawn, .05))

	return unit

def SporeBeast():
	unit = Unit()
	unit.sprite.char = 'S'
	unit.sprite.color = Color(50, 160, 50)
	unit.name = "Spore Beast"
	unit.max_hp = 25
	unit.buffs.append(SporeBeastBuff())
	unit.spells.append(SimpleMeleeAttack(8))
	unit.tags = [Tags.Living, Tags.Nature]
	return unit

def GreaterSporeBeast():
	unit = Unit()
	unit.sprite.char = 'S'
	unit.sprite.color = Color(50, 220, 50)
	unit.name = "Greater Spore Beast"
	unit.max_hp = 65
	unit.buffs.append(SporeBeastBuff())
	unit.spells.append(SimpleMeleeAttack(8))
	unit.tags = [Tags.Living, Tags.Nature]
	return unit

def SpikeBeast():
	unit = Unit()
	unit.sprite.char = 'S'
	unit.sprite.color = Color(50, 160, 50)
	unit.name = "Spike Beast"
	unit.max_hp = 35
	unit.buffs.append(SpikeBeastBuff())
	unit.buffs.append(Thorns(3))
	unit.spells.append(SimpleMeleeAttack(8))
	unit.tags = [Tags.Living, Tags.Nature]
	unit.resists[Tags.Physical] = 75
	return unit

def BlizzardBeast():
	unit = Unit()
	unit.sprite.char = 'S'
	unit.sprite.color = Color(50, 160, 50)
	unit.name = "Blizzard Beast"
	unit.max_hp = 35
	unit.buffs.append(BlizzardBeastBuff())
	unit.spells.append(SimpleMeleeAttack(8))
	unit.tags = [Tags.Living, Tags.Nature, Tags.Ice]
	unit.resists[Tags.Ice] = 100
	unit.resists[Tags.Fire] = -50
	return unit

def VoidBomber():
	unit = Unit()
	unit.sprite.char = 'v'
	unit.sprite.color = Color(195, 42, 224)
	unit.name = "Void Bomber"
	unit.description = "Explodes on death, dealing arcane damage and melting adjacent walls"
	unit.max_hp = 1
	unit.buffs.append(VoidBomberBuff())
	unit.spells.append(VoidBomberSuicide())
	unit.tags = [Tags.Arcane]
	return unit


def FireBomber():
	unit = Unit()
	unit.sprite.char = 'f'
	unit.sprite.color = Tags.Fire.color
	unit.name = "Fire Bomber"
	unit.description = "Explodes on death, dealing fire damage"
	unit.max_hp = 1
	unit.buffs.append(FireBomberBuff())
	unit.spells.append(FireBomberSuicide())
	unit.tags = [Tags.Fire]
	return unit

def DisplacerBeast():
	unit = Unit()
	unit.sprite.char = 'd'
	unit.sprite.color = Color(217, 102, 255)
	unit.name = "Displacer Beast"
	unit.description = "A teleporting cat"
	unit.max_hp = 10
	unit.spells.append(SimpleMeleeAttack(3))
	unit.buffs.append(TeleportyBuff(flash=True))
	unit.tags = [Tags.Living, Tags.Arcane, Tags.Nature]
	unit.resists[Tags.Arcane] = 50
	return unit

def Orc():
	unit = Unit()
	unit.sprite.char = 'o'
	unit.sprite.color = Color(19, 125, 0)
	unit.name = "Orc"
	unit.max_hp = 20
	unit.spells.append(SimpleMeleeAttack(5))
	unit.tags = [Tags.Living]
	return unit


class SatyrWineSpell(Spell):

	def on_init(self):
		self.name = "Refresh"
		self.description = "Heal self or ally for 5 HP"
		self.range = 1.5
		self.melee = True
		self.can_target_self = True
		self.cool_down = 2

	def get_ai_target(self):
		units = [u for u in self.caster.level.get_units_in_ball(self.caster, 1, diag=True) if not are_hostile(u, self.caster) and u.cur_hp < u.max_hp]
		if units:
			return random.choice(units)
		else:
			return None

	def cast_instant(self, x, y):
		u = self.caster.level.get_unit_at(x, y)
		if u:
			u.deal_damage(-5, Tags.Heal, self)

def Satyr():
	unit = Unit()
	unit.name = "Satyr"
	unit.max_hp = 19

	unit.tags = [Tags.Living, Tags.Nature]

	unit.spells = [SimpleMeleeAttack(3), SatyrWineSpell()]

	return unit

def Boggart():
	unit = Unit()
	unit.name = "Boggart"
	unit.max_hp = 6
	unit.shields = 1

	unit.spells.append(SimpleMeleeAttack(4, damage_type=Tags.Arcane))

	unit.tags = [Tags.Living, Tags.Nature, Tags.Arcane]
	
	unit.resists[Tags.Arcane] = 75

	return unit

def drain_spell_charges(caster, target):
	possible_spells = [s for s in target.spells if s.cur_charges > 0]
	if possible_spells:
		spell = random.choice(possible_spells)
		spell.cur_charges = spell.cur_charges - 1

def MindMaggot():
	unit = Unit()
	unit.sprite.char = 'm'
	unit.sprite.color = Color(250, 220, 100)
	unit.name = "Mind Maggot"
	unit.max_hp = 5

	melee = SimpleMeleeAttack(3, damage_type=Tags.Arcane, onhit=drain_spell_charges)
	melee.description = "On hit, drains a charge of a random spell"
	melee.name = "Brain Bite"
	unit.spells.append(melee)

	unit.tags = [Tags.Living, Tags.Arcane]
	return unit

def MindMaggotQueen():
	unit = Unit()
	unit.sprite.char = 'M'
	unit.sprite.color = Color(250, 220, 100)
	unit.name = "Mind Maggot Queen"
	unit.max_hp = 90

	melee = SimpleMeleeAttack(9, onhit=drain_spell_charges)
	melee.name = "Brain Bite"
	melee.description = "On hit, drains a charge of a random spell"
	unit.spells.append(melee)

	unit.buffs.append(GeneratorBuff(spawn_func=MindMaggot, spawn_chance=.1))

	unit.tags = [Tags.Living, Tags.Arcane]
	return unit

def Centaur():
	unit = Unit()
	unit.name = "Centaur"
	unit.max_hp = 15
	
	javalin = SimpleRangedAttack(damage=5, range=5)
	javalin.cool_down = 8
	javalin.name = "Throw Spear"
	unit.spells.append(javalin)
	
	trample = SimpleMeleeAttack(4, trample=True)
	trample.name = "Trample"
	unit.spells.append(trample)
	
	leap = LeapAttack(damage=4, damage_type=Tags.Physical, range=4)
	leap.name = "Leap"
	leap.cool_down = 3
	unit.spells.append(leap)

	unit.tags = [Tags.Living]
	return unit

def Ogre():
	unit = Unit()
	unit.sprite.char = 'O'
	unit.sprite.color = Color(255, 166, 71)
	unit.name = "Ogre"
	unit.description = "A fat and hideous abombination longing to consume the flesh of the young and beautiful"
	unit.max_hp = 45
	unit.spells.append(SimpleMeleeAttack(15))
	unit.tags = [Tags.Living]
	return unit

def Troll():
	unit = Unit()
	unit.asset_name = "green_troll"
	unit.sprite.char = 'T'
	unit.sprite.color = Color(73, 214, 21)
	unit.name = "Troll"
	unit.description = "A big dumb regenerating troll.  Regenerates 5hp per turn.  Regeneration is disabled for one turn upon taking fire damage."
	unit.max_hp = 30
	unit.buffs.append(TrollRegenBuff())
	unit.spells.append(SimpleMeleeAttack(10))
	unit.tags = [Tags.Living]
	return unit

def EarthTroll():
	unit = Troll()
	unit.asset_name = "troll"
	unit.name = "Earth Troll"
	unit.resists[Tags.Physical] = 50
	unit.resists[Tags.Fire] = 50
	unit.resists[Tags.Lightning] = 50
	return unit

def StormTroll():
	unit = Troll()
	unit.asset_name = None
	unit.sprite.color = Tags.Lightning.color
	unit.name = "Storm Troll"
	unit.description = "A troll touched by thunder spirits.  Storm clouds form in its wake."
	unit.resists[Tags.Lightning] = 100
	unit.buffs.append(CloudGeneratorBuff(StormCloud, radius=3, chance=.1))
	unit.tags = [Tags.Living, Tags.Lightning]
	return unit

def Ghost():
	unit = Unit()
	unit.sprite.char = 'g'
	unit.sprite.color = Color(220, 220, 220)
	unit.name = "Ghost"
	unit.description = "A Malevolent spirit"
	unit.max_hp = 4
	unit.resists[Tags.Physical] = 100
	unit.resists[Tags.Dark] = 50
	unit.buffs.append(TeleportyBuff())
	unit.spells.append(SimpleMeleeAttack(1, damage_type=Tags.Dark))
	unit.flying = True
	unit.tags = [Tags.Dark, Tags.Undead]
	return unit

def GhostFire():
	unit = Ghost()
	unit.name = "Fire Ghost"
	unit.asset_name = "fire_ghost"
	unit.resists[Tags.Fire] = 100
	unit.resists[Tags.Ice] = -100
	fire = SimpleRangedAttack(damage=7, range=5, damage_type=Tags.Fire)
	fire.name = "Fire Bolt"
	unit.spells[0] = fire

	unit.tags.append(Tags.Fire)
	return unit

def GhostMass():
	unit = Ghost()
	unit.max_hp = 28
	unit.name = "Ghostly Mass"
	unit.asset_name = "ghostly_mass"
	unit.spells[0].damage *= 2
	unit.buffs.append(SpawnOnDeath(Ghost, 8))
	return unit

def GhostKing():
	unit = Ghost()
	unit.name = "Ghost King"
	unit.max_hp = 45
	unit.spells.insert(0, KingSpell(Ghost))
	return unit

def Goblin():
	unit = Unit()
	unit.sprite.char = 'g'
	unit.sprite.color = Color(0, 170, 0)
	unit.name = "Goblin"
	unit.max_hp = 7
	unit.spells.append(SimpleMeleeAttack(2))
	unit.tags = [Tags.Living]
	return unit

def Bat():
	unit = Unit()
	unit.name = "Bat"
	unit.max_hp = 4
	unit.flying = True
	unit.spells.append(SimpleMeleeAttack(2))
	unit.tags = [Tags.Living, Tags.Dark]
	return unit

class SlimeBuff(Buff):

	def __init__(self, spawner, name='slimes'):
		Buff.__init__(self)
		self.description = "50%% chance to gain 1 hp and 1 max hp per turn.  Upon reaching double max HP, splits into 2 %s." % name
		self.name = "Slime Growth"
		self.color = Tags.Slime.color
		self.spawner = spawner
		self.spawner_name = name

	def on_applied(self, owner):
		self.start_hp = self.owner.max_hp
		self.to_split = self.start_hp * 2
		self.growth = self.start_hp // 10
		self.description = "50%% chance to gain %d hp and max hp per turn.  Upon reaching %d HP, splits into 2 %s." % (self.growth, self.to_split, self.spawner_name)
		

	def on_advance(self):
		if random.random() < .5:
			return

		if self.owner.cur_hp == self.owner.max_hp:
			self.owner.max_hp += self.growth
		self.owner.deal_damage(-self.growth, Tags.Heal, self)
		if self.owner.cur_hp >= self.to_split:

			p = self.owner.level.get_summon_point(self.owner.x, self.owner.y)
			if p:
				self.owner.max_hp //= 2
				self.owner.cur_hp //= 2
				unit = self.spawner()
				unit.team = self.owner.team
				self.owner.level.add_obj(unit, p.x, p.y)

def GreenSlime():

	unit = Unit()
	unit.name = "Green Slime"

	unit.max_hp = 10

	unit.tags = [Tags.Slime]

	unit.spells.append(SimpleMeleeAttack(3, damage_type=Tags.Poison))
	unit.buffs.append(SlimeBuff(spawner=GreenSlime))

	unit.resists[Tags.Poison] = 100
	unit.resists[Tags.Physical] = 50

	return unit

def RedSlime():

	unit = Unit()

	unit.name = "Red Slime"
	unit.max_hp = 10

	unit.tags = [Tags.Slime, Tags.Fire]

	unit.spells.append(SimpleRangedAttack(damage=3, damage_type=Tags.Fire, range=3))

	unit.buffs.append(SlimeBuff(spawner=RedSlime))

	unit.resists[Tags.Fire] = 100
	unit.resists[Tags.Ice] = -100
	unit.resists[Tags.Physical] = 50

	return unit

def IceSlime():

	unit = Unit()

	unit.name = "Ice Slime"
	unit.max_hp = 10

	unit.tags = [Tags.Slime, Tags.Ice]

	unit.spells.append(SimpleRangedAttack(damage=3, damage_type=Tags.Ice, range=3))

	unit.buffs.append(SlimeBuff(spawner=IceSlime))

	unit.resists[Tags.Ice] = 100
	unit.resists[Tags.Physical] = 50
	unit.resists[Tags.Fire] = -100

	return unit

def VoidSlime():

	unit = Unit()

	unit.name = "Void Slime"
	unit.max_hp = 10

	unit.tags = [Tags.Slime, Tags.Arcane]

	unit.spells.append(SimpleRangedAttack(damage=3, damage_type=Tags.Arcane, range=5, melt=True, beam=True))

	unit.buffs.append(SlimeBuff(spawner=VoidSlime))
	unit.buffs.append(TeleportyBuff(radius=7))

	unit.resists[Tags.Arcane] = 100
	unit.resists[Tags.Physical] = 50

	return unit

class GeneratorBuff(Buff):

	def __init__(self, spawn_func, spawn_chance):
		Buff.__init__(self)
		self.spawn_func = spawn_func
		self.spawn_chance = spawn_chance
		self.example_monster = self.spawn_func()

	def on_advance(self):
		if random.random() < self.spawn_chance:
			open_points = list(self.owner.level.get_adjacent_points(Point(self.owner.x, self.owner.y), check_unit=True))
			if not open_points:
				# TODO- queue blocked spawns?
				return
			p = random.choice(open_points)
			new_monster = self.spawn_func()
			new_monster.team = self.owner.team
			self.owner.level.add_obj(new_monster, p.x, p.y)

	def get_tooltip(self):
		return "Has a %d%% chance each turn to spawn a %s" % (int(100 * self.spawn_chance), self.example_monster.name)

def DisplacerBeastMother():
	unit = DisplacerBeast()
	unit.sprite.char = 'D'
	unit.name = "Displacer Broodmother"
	unit.spells[0].damage = 12
	unit.max_hp = 72
	unit.description = "Mother of displacer beasts"
	unit.buffs.append(GeneratorBuff(DisplacerBeast, .1))
	unit.tags = [Tags.Living, Tags.Arcane]
	return unit

def Efreet():
	unit = Unit()
	unit.sprite.char = 'E'
	unit.sprite.color = Color(255, 0, 0)
	unit.max_hp = 45
	unit.name = "Efreet"
	unit.description = "A Fiery demon which ignites the air around it, causing 2 fire damage to all creatures within 5 squares each turn."
	unit.buffs.append(DamageAuraBuff(damage_type=Tags.Fire, damage=2, radius=5, friendly_fire=False))
	unit.spells.append(SimpleRangedAttack(damage=5, range=3, damage_type=Tags.Fire))
	unit.resists[Tags.Fire] = 100
	unit.resists[Tags.Ice] = -50
	unit.flying = True
	unit.tags = [Tags.Fire]
	return unit

class SplittingBuff(Buff):
	# A buff that makes a creature split into smaller versions of itself when killed

	def __init__(self, spawner, children=2):
		Buff.__init__(self)
		self.spawner = spawner
		self.owner_triggers[EventOnDeath] = self.on_death
		self.children = children
		self.child_example = spawner()
		self.name = "Splitting"

	def on_death(self, evt):
		for i in range(self.children):
			unit = self.spawner()
			if unit.max_hp == 0:
				return
			self.summon(unit)
			
	def get_tooltip(self):
		return "On death, splits into %d smaller versions of itself" % self.children

def BoneShambler(HP=32):
	unit = Unit()
	unit.sprite.char = 'B'
	unit.sprite.color = Color(201, 213, 214)
	unit.max_hp = HP
	unit.resists[Tags.Dark] = 100

	if HP >= 256:
		unit.name = "Bone Shambler Megalith"
	elif HP >= 64:
		unit.name = "Towering Bone Shambler"
	elif HP > 8:
		unit.name = "Bone Shambler"
	else:
		unit.name = "Bone Shambler Fragment"


	unit.description = "A disgusting mass of bone, animated by dark magic."
	if HP >= 8:
		unit.description += "  Splits into smaller chunks when destroyed."
		unit.buffs.append(SplittingBuff(spawner=lambda : BoneShambler(unit.max_hp // 2), children=2))

	unit.spells.append(SimpleMeleeAttack(HP // 4))
	unit.tags = [Tags.Undead]
	return unit

def ToweringBoneShambler(HP=128):
	return BoneShambler(128)

def BoneShamblerMegalith():
	return BoneShambler(256)

def WormShambler(HP=20):
	unit = WormBall()
	unit.sprite.char = 'W'
	unit.max_hp = HP

	unit.name = "Giant Worm Ball"
	unit.asset_name = "ball_of_worms_large"

	def summon_worms(caster, target):
		worms = WormBall(5)
		p = caster.level.get_summon_point(target.x, target.y, 1.5)
		if p:
			caster.level.add_obj(worms, p.x, p.y)

	spitworms = SimpleRangedAttack(damage=1, range=6, damage_type=Tags.Physical, onhit=summon_worms)
	
	spitworms.name = "Spit Worms"
	spitworms.cool_down = 3
	spitworms.description = "Summons a small worm ball adjacent to to the target"

	unit.spells.insert(0, spitworms)

	unit.tags = [Tags.Living]
	return unit

def WormBall(HP=10):
	unit = Unit()
	unit.sprite.char = 'W'
	unit.max_hp = HP

	if HP >= 10:
		unit.name = "Large Worm Ball"
		unit.asset_name = "ball_of_worms_med"
	else:
		unit.name = "Small Worm Ball"
		unit.asset_name = "ball_of_worms_small"

	if HP >= 10:
		unit.buffs.append(SplittingBuff(spawner=lambda : WormBall(unit.max_hp // 2), children=2))

	unit.buffs.append(RegenBuff(3))
	unit.spells.append(SimpleMeleeAttack(HP // 2))

	unit.tags = [Tags.Living]
	return unit

def FairyGlass():
	unit = EvilFairy()
	unit.name = "Glass Faery"
	unit.asset_name = "faery_glass"

	unit.shields += 1

	glassbolt = SimpleRangedAttack(damage=2, range=4, damage_type=Tags.Arcane, effect=Tags.Glassification, buff=GlassPetrifyBuff, buff_duration=1)
	glassbolt.name = "Glassification Bolt"

	unit.spells = [HealAlly(heal=7, range=6), glassbolt]

	unit.tags.append(Tags.Glass)
	return unit

def EvilFairy():
	unit = Unit()
	unit.sprite.char = 'f'
	unit.sprite.color = Color(252, 141, 249)
	unit.name = "Evil Faery"
	unit.flying = True
	unit.description = "A capricious creature who delights in providing comfort to evil beings"
	unit.max_hp = 9
	unit.shields = 1
	unit.buffs.append(TeleportyBuff(chance=.5))
	unit.spells.append(HealAlly(heal=7, range=6))
	unit.spells.append(SimpleRangedAttack(damage=2, range=4, damage_type=Tags.Arcane))
	unit.tags = [Tags.Nature, Tags.Arcane, Tags.Living]
	unit.resists[Tags.Arcane] = 50
	return unit

def HellHound():
	unit = Unit()
	unit.sprite.char = 'h'
	unit.sprite.color = unit.sprite.color = Color(200, 60, 70)
	unit.name = "Hell Hound"
	unit.max_hp = 19
	unit.resists[Tags.Fire] = 100
	unit.resists[Tags.Ice] = -50
	unit.resists[Tags.Dark] = 50
	unit.spells.append(SimpleMeleeAttack(damage=6, damage_type=Tags.Fire))
	unit.spells.append(LeapAttack(damage=6, damage_type=Tags.Fire, range=4))
	unit.buffs.append(Thorns(4, Tags.Fire))
	unit.tags = [Tags.Demon, Tags.Fire]
	return unit

def IceHound():
	unit = Unit()
	unit.name = "Ice Hound"
	unit.max_hp = 19
	unit.resists[Tags.Ice] = 100
	unit.resists[Tags.Dark] = 50
	unit.spells.append(SimpleMeleeAttack(damage=6, damage_type=Tags.Ice))
	unit.spells.append(LeapAttack(damage=6, damage_type=Tags.Ice, range=4))
	unit.buffs.append(Thorns(4, Tags.Ice))
	unit.tags = [Tags.Demon, Tags.Ice]
	return unit

def Minotaur():
	unit = Unit()
	unit.sprite.char = 'M'
	unit.sprite.color = Color(158, 134, 100)
	unit.name = "Minotaur"
	unit.description = "A man with the head of a bull"
	unit.max_hp = 45
	unit.spells.append(SimpleMeleeAttack(damage=8, trample=True))
	unit.spells.append(LeapAttack(damage=12, damage_type=Tags.Physical, range=10, is_leap=False))
	unit.tags = [Tags.Living]
	return unit

class CockatriceGaze(Spell):

	def __init__(self):
		Spell.__init__(self)
		self.name = "Stone Gaze"
		self.range = 12
		self.cool_down = 10

	def cast(self, x, y):
		start = Point(self.caster.x, self.caster.y)
		target = Point(x, y)

		for point in Bolt(self.caster.level, start, target):
			self.caster.level.flash(point.x, point.y, Tags.Petrification.color)
			yield

		unit = self.caster.level.get_unit_at(x, y)
		unit.apply_buff(PetrifyBuff(), 3)
		yield

	def get_description(self):
		return "Petrifies target for 3 turns"

def Cockatrice():
	unit = Unit()
	unit.sprite.char = 'B'
	unit.sprite.color = Color(50, 255, 50)
	unit.name = "Cockatrice"
	unit.description = "Its gaze turns foes to stone"
	unit.max_hp = 35
	peck = SimpleMeleeAttack(damage=4)
	peck.name = "Peck"
	unit.spells.append(peck)
	unit.spells.append(CockatriceGaze())
	
	unit.flying = True

	unit.resists[Tags.Arcane] = 50
	unit.resists[Tags.Physical] = 50
	unit.resists[Tags.Lightning] = -100
	
	unit.tags = [Tags.Arcane, Tags.Living]
	return unit

def VoidSpawner():

	unit = Unit()
	unit.sprite.char = 'R'
	unit.name = "Void Rift"
	unit.sprite.color = Color(195, 42, 224)
	unit.max_hp = 30
	unit.stationary = True
	unit.buffs.append(GeneratorBuff(VoidBomber, .2))
	unit.buffs.append(TeleportyBuff(chance=.1, radius=8))
	unit.spells.append(SimpleRangedAttack(damage=5, range=7, damage_type=Tags.Arcane))
	unit.resists[Tags.Arcane] = 100
	unit.tags = [Tags.Arcane]
	return unit

def FireSpawner():

	unit = Unit()
	unit.sprite.char = 'R'
	unit.name = "Flame Rift"
	unit.sprite.color = Tags.Fire.color
	unit.max_hp = 30
	unit.stationary = True
	unit.buffs.append(GeneratorBuff(FireBomber, .2))
	unit.buffs.append(TeleportyBuff(chance=.1, radius=8))
	unit.spells.append(SimpleRangedAttack(damage=5, range=7, damage_type=Tags.Fire))
	unit.resists[Tags.Fire] = 100
	unit.resists[Tags.Ice] = -100
	unit.resists[Tags.Arcane] = 50
	unit.tags = [Tags.Arcane, Tags.Fire]
	return unit

class MonsterVoidBeam(Spell):

	def on_init(self):
		self.requires_los = False
		self.range = 6
		self.name = "Void Beam"
		self.damage = 7
		self.damage_type = Tags.Arcane
		self.cool_down = 3

	def get_description(self):
		return "Deals damage and destroys walls in a line"

	def cast_instant(self, x, y):
		for p in self.caster.level.get_points_in_line(self.caster, Point(x, y))[1:]:
			self.caster.level.deal_damage(p.x, p.y, self.damage, Tags.Arcane, self)
			
			if not self.caster.level.tiles[p.x][p.y].can_see:
				self.caster.level.make_floor(p.x, p.y)

class ButterflyLightning(Spell):

	def on_init(self):
		self.range = 6
		self.name = "Lightning"
		self.damage = 9
		self.damage_type = Tags.Lightning
		self.cool_down = 3

	def get_description(self):
		return "Deals damage to all points in a line"

	def cast_instant(self, x, y):

		for p in self.caster.level.get_points_in_line(self.caster, Point(x, y), find_clear=True):
			self.caster.level.deal_damage(p.x, p.y, self.damage, self.damage_type, self)



def ButterflyDemon():

	unit = Unit()
	unit.name = "Butterfly Demon"
	unit.sprite.char = 'B'
	unit.sprite.color = Color(255, 50, 100)
	unit.flying = True
	unit.max_hp = 50
	unit.shields = 3
	unit.resists[Tags.Arcane] = 100
	unit.resists[Tags.Lightning] = 100
	unit.resists[Tags.Ice] = -50
	
	unit.buffs.append(TeleportyBuff())

	unit.spells.append(MonsterVoidBeam())
	unit.spells.append(ButterflyLightning())
	unit.spells.append(SimpleMeleeAttack(4))
	unit.tags = [Tags.Demon, Tags.Nature, Tags.Arcane, Tags.Lightning]
	return unit

class ToadHop(Spell):

	def on_init(self):
		self.name = "Frog Hop"
		self.description = "Hops to a random tile up to 4 tiles away"
		self.range = 0
		self.cool_down = 4

	def cast_instant(self, x, y):
		randomly_teleport(self.caster, 4, flash=True, requires_los=True)

def HornedToad():

	unit = Unit()
	unit.name = 'Horned Toad'
	unit.sprite.char = 'T'
	unit.sprite.color = Color(255, 200, 50)
	unit.max_hp = 18

	tongue_attack = PullAttack(damage=2, range=4, color=Tags.Tongue.color)
	tongue_attack.name = "Tongue Lash"
	unit.spells.append(ToadHop())
	unit.spells.append(SimpleMeleeAttack(damage=8))
	unit.spells.append(tongue_attack)
	unit.tags = [Tags.Living, Tags.Nature]
	unit.resists[Tags.Ice] = -50
	return unit

def GiantToad():

	unit = Unit()
	unit.name = 'Towering Toadbeast'
	unit.asset_name = 'big_toad'
	unit.sprite.char = 'T'
	unit.sprite.color = Color(255, 80, 0)
	unit.max_hp = 85

	unit.buffs.append(TrollRegenBuff())

	tongue_attack = PullAttack(damage=3, range=8, color=Tags.Tongue.color)
	tongue_attack.name = "Tongue Lash"
	unit.spells.append(ToadHop())
	unit.spells.append(SimpleMeleeAttack(damage=15, trample=True))
	unit.spells.append(tongue_attack)
	unit.tags = [Tags.Living, Tags.Nature]
	unit.resists[Tags.Ice] = -50
	return unit

def FlameToad():

	unit = Unit()
	unit.name = 'Flame Toad'
	unit.sprite.char = 'T'
	unit.sprite.color = Tags.Fire.color
	unit.max_hp = 25

	unit.resists[Tags.Fire] = 75
	unit.resists[Tags.Ice] = -100
	
	unit.spells.append(ToadHop())
	unit.spells.append(SimpleRangedAttack(name="Fireball", damage=7, range=6, radius=1, damage_type=Tags.Fire))
	unit.tags = [Tags.Living, Tags.Fire, Tags.Nature]
	return unit

def VoidToad():

	unit = Unit()
	unit.name = 'Void Toad'
	unit.sprite.char = 'T'
	unit.sprite.color = Tags.Fire.color
	
	unit.max_hp = 25
	unit.shields = 2

	unit.resists[Tags.Arcane] = 75
	unit.resists[Tags.Ice] = -50

	unit.spells.append(ToadHop())
	voidlick = SimpleRangedAttack(name="Void Lick", damage=7, range=6, damage_type=Tags.Arcane, beam=True, melt=True)
	voidlick.onhit = lambda caster, target: pull(target, caster, 1)
	voidlick.requires_los = False
	voidlick.description = "Pulls the target towards the caster.\nMelts walls."
	unit.spells.append(voidlick)

	unit.tags = [Tags.Living, Tags.Arcane, Tags.Nature]
	return unit

class SpiderBuff(Buff):

	def on_advance(self):

		# Do not make webs if there are no enemy units
		if not any(are_hostile(u, self.owner) for u in self.owner.level.units):
			return
		spawn_webs(self.owner)

	def get_tooltip(self):
		return "Weaves webs each turn"

def QueenMonster(base_spawner):
	unit = base_spawner()
	unit.name = "%s Queen" % unit.name
	unit.asset_name += '_mother'

	unit.max_hp = 96
	if unit.shields:
		unit.shields += 2

	def babyspider():
		unit = base_spawner()
		unit.name = "Baby %s" % unit.name
		unit.asset_name += '_child'
		unit.max_hp = 3
		for s in unit.spells:
			if hasattr(s, 'damage'):
				s.damage = 1

		unit.is_coward = True
		unit.buffs = [b for b in unit.buffs if not isinstance(b, SpiderBuff)]
		unit.buffs.append(MatureInto(base_spawner, 8))

		return unit

	unit.spells.insert(0, SimpleSummon(babyspider, num_summons=4, cool_down=12))
	return unit

def GiantSpiderQueen():
	return QueenMonster(GiantSpider)

def GiantSpider():

	unit = Unit()

	unit.name = "Giant Spider"
	unit.asset_name = "dark_spider"
	unit.max_hp = 14

	unit.sprite.char = 's'
	unit.sprite.color = Color(240, 130, 0)

	unit.buffs.append(SpiderBuff())
	unit.spells.append(SimpleMeleeAttack(2, buff=Poison, buff_duration=10))

	unit.tags = [Tags.Spider, Tags.Living, Tags.Nature]
	unit.resists[Tags.Ice] = -50
	return unit

def SteelSpiderQueen():
	return QueenMonster(SteelSpider)

def PhaseSpiderQueen():
	return QueenMonster(PhaseSpider)

def SteelSpider():

	unit = Unit()

	unit.name = "Steel Spider"
	unit.asset_name = "steel_spider"
	unit.max_hp = 14

	unit.buffs.append(SpiderBuff())
	unit.spells.append(SimpleMeleeAttack(6, buff=Poison, buff_duration=10))

	unit.tags = [Tags.Spider, Tags.Construct, Tags.Metallic]

	return unit

def PhaseSpider():

	unit = Unit()

	unit.name = "Aether Spider"
	unit.asset_name = "aether_spider"
	unit.max_hp = 14
	unit.shields = 1

	unit.resists[Tags.Arcane] = 100
	unit.resists[Tags.Physical] = 75
	unit.resists[Tags.Ice] = -50

	unit.sprite.char = 's'
	unit.sprite.color = Color(30, 240, 230)

	unit.buffs.append(SpiderBuff())
	unit.buffs.append(TeleportyBuff(chance=.5, radius=7))
	unit.spells.append(SimpleMeleeAttack(4, damage_type=Tags.Arcane, buff=Poison, buff_duration=10))

	unit.tags = [Tags.Spider, Tags.Living, Tags.Arcane]

	return unit

def VoidKnight():

	unit = Unit()

	unit.name = "Void Knight"

	unit.max_hp = 70
	unit.shields = 2

	unit.resists[Tags.Physical] = 50
	unit.resists[Tags.Arcane] = 100
	unit.resists[Tags.Dark] = 50

	unit.sprite.char = 'K'
	unit.sprite.color = Color(100, 255, 255)

	melee = SimpleMeleeAttack(damage=6, damage_type=Tags.Physical, onhit=lambda caster, target: randomly_teleport(target, 5))
	unit.spells.append(melee)
	melee.get_description = lambda : "Teleports the target to a random location up to 5 tiles away"

	charge = LeapAttack(damage=10, damage_type=Tags.Arcane, range=6, is_ghost=True)
	charge.name = "Aether Charge"
	charge.get_description = lambda : "Ignores obstacles"
	unit.spells.append(charge)
	
	unit.tags = [Tags.Arcane, Tags.Living]
	return unit

def extra_chaos_damage(caster, target, spell):
	dtype = random.choice([Tags.Physical, Tags.Fire, Tags.Lightning])
	damage = 5
	target.deal_damage(damage, dtype, spell)

def ChaosKnight():

	unit = Unit()

	unit.name = "Chaos Knight"

	unit.max_hp = 90

	unit.resists[Tags.Physical] = 75
	unit.resists[Tags.Fire] = 75
	unit.resists[Tags.Lightning] = 75

	unit.sprite.char = 'K'
	unit.sprite.color = Color(255, 155, 55)

	# Melee attack with extra chaos damage
	melee = SimpleMeleeAttack(damage=7)
	melee.onhit = lambda caster, target: extra_chaos_damage(caster, target, melee)
	melee.description = "Deals an additional 5 fire or lightning damage on hit."

	chaosball = SimpleRangedAttack(damage=11, radius=2, range=6, damage_type=[Tags.Fire, Tags.Lightning, Tags.Physical])
	chaosball.name = "Chaos Ball"
	chaosball.cool_down = 3

	unit.spells.append(chaosball)
	unit.spells.append(melee)

	unit.tags = [Tags.Fire, Tags.Lightning, Tags.Living]

	return unit

def StormKnight():

	unit = Unit()

	unit.name = "Storm Knight"

	unit.max_hp = 90

	unit.resists[Tags.Physical] = 50
	unit.resists[Tags.Lightning] = 75
	unit.resists[Tags.Ice] = 100

	leap = LeapAttack(damage=10, range=7, damage_type=Tags.Lightning)
	leap.name = "Flash of Lightning"
	leap.cool_down = 7
	unit.spells.append(leap)

	def freeze(caster, target):
		target.apply_buff(FrozenBuff(), 2)
	frost = SimpleBurst(damage=13, radius=2, damage_type=Tags.Ice, onhit=freeze)
	frost.name = "Frost"
	frost.description = "Applies frozen for 2 turns"
	frost.cool_down = 5
	unit.spells.append(frost)

	def make_cloud(caster, target):
		points = [p for p in target.level.get_points_in_ball(target.x, target.y, 1, diag=True) if not target.level.tiles[p.x][p.y].cloud and distance(caster, p) > 0]
		if points:
			point = random.choice(points)
			cloud = random.choice([StormCloud(caster), BlizzardCloud(caster)])
			target.level.add_obj(cloud, point.x, point.y)

	melee = SimpleMeleeAttack(damage=6, onhit=make_cloud)
	melee.name = "Storm Strike"
	melee.description = "Creates thunderstorms and blizzards"
	unit.spells.append(melee)

	unit.tags = [Tags.Ice, Tags.Lightning, Tags.Living]
	
	return unit

def TwilightKnight():
	unit = Unit()
	unit.name = "Twilight Knight"

	unit.max_hp = 90
	unit.resists[Tags.Dark] = 100
	unit.resists[Tags.Holy] = 100

	melee = SimpleMeleeAttack(damage=11, damage_type=Tags.Dark)	

	def drain(caster, target):
		if Tags.Living in target.tags:
			drain_max_hp(target, 7)

	melee.name = "Wight Blade"
	melee.description = "Living targets lose 7 max hp"

	melee.onhit = drain

	blast = FalseProphetHolyBlast()
	blast.cool_down = 3
	blast.damage = 14

	unit.spells = [blast, melee]

	unit.tags = [Tags.Dark, Tags.Holy, Tags.Living]

	unit.buffs.append(ReincarnationBuff(1))
	return unit

def EnergyKnight():
	unit = Unit()
	unit.name = "Energy Knight"

	unit.max_hp = 90
	unit.shields = 6

	unit.resists[Tags.Arcane] = 100
	unit.resists[Tags.Lightning] = 100

	melee = SimpleMeleeAttack(damage=6, damage_type=Tags.Physical, onhit=lambda caster, target: randomly_teleport(target, 5))
	unit.spells.append(melee)
	melee.description = "Teleports the target to a random location up to 5 tiles away"

	leap = LeapAttack(damage=10, range=7, damage_type=Tags.Lightning)
	leap.name = "Flash of Lightning"
	leap.cool_down = 7
	unit.spells.append(leap)


	unit.tags = [Tags.Lightning, Tags.Arcane, Tags.Living]
	return unit


def Lamasu():

	unit = Unit()
	unit.name = "Lamasu"
	unit.max_hp = 200
	unit.shields = 3

	unit.resists[Tags.Physical] = 50
	unit.resists[Tags.Arcane] = 50
	unit.resists[Tags.Dark] = 50
	unit.resists[Tags.Holy] = 75

	unit.sprite.char = 'L'
	unit.sprite.color = Color(255, 220, 100)

	unit.flying = True

	unit.spells.append(SimpleMeleeAttack(damage=5))
	leap = LeapAttack(damage=6, range=10)
	leap.name = "Charge"
	unit.spells.append(leap)
	unit.buffs.append(HealAuraBuff(heal=5, radius=6))



	unit.tags = [Tags.Nature, Tags.Living, Tags.Holy]

	return unit

class TurtleDefenseBonus(Stun):

	def on_init(self):
		Stun.on_init(self)
		self.resists[Tags.Physical] = 50
		self.resists[Tags.Fire] = 50
		self.resists[Tags.Lightning] = 50
		self.color = Color(0, 255, 0)
		self.name = "Inside Shell"

class TurtleBuff(Buff):

	def on_applied(self, owner):
		self.buff_type = BUFF_TYPE_BLESS
		self.owner_triggers[EventOnDamaged] = self.on_damaged

	def on_damaged(self, event):
		if not self.owner.is_stunned():
			self.owner.apply_buff(TurtleDefenseBonus(), 3)

	def get_tooltip(self):
		return "Withdraws into its shell upon taking damage, gaining 50% physical, fire, and lightning resistance"

def NightmareTurtle():

	unit = Unit()

	unit.name = "Nightmare Turtle"

	unit.sprite.char = 'T'
	unit.sprite.color = Tags.Arcane.color

	unit.max_hp = 95

	unit.resists[Tags.Dark] = 75
	unit.resists[Tags.Arcane] = 50

	aura = DamageAuraBuff(damage=1, damage_type=[Tags.Arcane, Tags.Dark], radius=7)
	aura.name = "Nightmare Aura"
	unit.buffs.append(aura)
	unit.buffs.append(TurtleBuff())

	unit.spells.append(SimpleMeleeAttack(damage=20))
	unit.tags = [Tags.Dark, Tags.Nature, Tags.Arcane, Tags.Demon]
	return unit

def VampireBat():
	unit = Unit()
	unit.name = "Vampire Bat"
	unit.asset_name = "bat_vampire"
	unit.max_hp = 4
	unit.flying = True
	
	unit.resists[Tags.Dark] = 100
	unit.tags = [Tags.Undead, Tags.Dark]
	unit.is_coward = True

	unit.buffs.append(MatureInto(Vampire, 20))
	return unit

def Vampire():

	unit = Unit()

	unit.name = "Vampire"

	unit.sprite.char = 'V'
	unit.sprite.color = Tags.Dark.color

	unit.resists[Tags.Fire] = -100

	unit.max_hp = 32
	unit.flying = True

	melee = SimpleMeleeAttack(damage=7, damage_type=Tags.Dark, drain=True)
	melee.name = "Drain Life"
	melee.get_description = lambda : "Drains life"
	unit.spells.append(melee)
	unit.tags = [Tags.Undead, Tags.Dark]
	unit.buffs.append(RespawnAs(VampireBat))
	return unit

def BoneKnight():

	unit = Unit()

	unit.name = "Bone Knight"

	unit.max_hp = 40
	unit.shields = 1

	unit.tags = [Tags.Undead]

	melee = SimpleMeleeAttack(damage=9, damage_type=Tags.Dark)
	melee.name = "Wight Blade"

	def drain(caster, target):
		if Tags.Living in target.tags:
			drain_max_hp(target, 2)

	melee.onhit = drain
	melee.description = "Living targets lose 2 max hp"
	unit.spells.append(melee)

	return unit

class WizardWheel(Spell):

	def on_init(self):
		self.name = "Wheel of Death"
		self.damage = 27
		self.damage_type = Tags.Dark
		self.range = 0
		self.cool_down = 27
		self.description = "Hits a random target anywhere on the battlefield."

	def cast(self, x, y):
		delay = 15
		for i in range(delay):
			yield

		targets = [u for u in self.caster.level.units if self.caster.level.are_hostile(self.caster, u)]
		if targets:
			target = random.choice(targets)
			target.deal_damage(self.get_stat('damage'), self.damage_type, self)

		for i in range(delay):
			yield

class WizardSwap(Spell):

	def __init__(self, tag):
		self.tag = tag
		Spell.__init__(self)
		

	def on_init(self):
		self.name = "%s Swap" % self.tag.name
		self.description = "Swaps places with a random %s unit" % self.tag.name
		self.cool_down = 18

	def can_swap(self, u):
		if u == self.caster:
			return False
		if not self.caster.flying:
			if not self.caster.level.tiles[u.x][u.y].can_walk:
				return False
		else:
			if not self.caster.level.tiles[u.x][u.y].can_fly:
				return False
		if self.tag not in u.tags:
			return False
		return True

	def can_cast(self, x, y):
		return any(self.can_swap(u) for u in self.caster.level.units)

	def cast_instant(self, x, y):
		target = random.choice([u for u in self.caster.level.units if self.can_swap(u)])
		self.caster.level.act_move(self.caster, target.x, target.y, teleport=True, force_swap=True)

def BoneWizard():
	unit = Unit()
	unit.name = "Bone Wizard"
	unit.max_hp = 54
	unit.shields = 1

	wheel = WizardWheel()
	nightmare = WizardNightmare()
	swap = WizardSwap(Tags.Undead)
	swap.name = "Bone Swap"
	summon = SimpleSummon(BoneKnight, num_summons=1, cool_down=24)
	summon.name = "Assemble Bone Knight"

	def make_skeleton(caster, target):
		raise_skeleton(caster, target)
		yield

	def try_raise(caster, target):
		if not target.is_alive():
			caster.level.queue_spell(make_skeleton(caster, target))

	dbolt = SimpleRangedAttack(damage=7, range=6, damage_type=Tags.Dark, onhit=try_raise)
	dbolt.description = "Raises slain targets as skeletons"

	# No wheel?
	unit.spells = [nightmare, swap, summon, dbolt]

	unit.resists[Tags.Dark] = 100
	unit.resists[Tags.Arcane] = 50
	unit.resists[Tags.Physical] = 50

	unit.tags = [Tags.Dark, Tags.Undead]

	return unit


class MushboomBuff(Buff):

	def __init__(self, buff, apply_duration):
		self.buff = buff
		self.apply_duration = apply_duration
		Buff.__init__(self)

	def on_init(self):
		self.owner_triggers[EventOnDeath] = self.on_death
		self.description = "On death, applies %d turns of %s to adjacent units" % (self.apply_duration, self.buff().name)
		self.name = "Mushboom Burst"
		
	def on_death(self, evt):
		self.owner.level.queue_spell(self.explode(self.owner.level, self.owner.x, self.owner.y))

	def explode(self, level, x, y):
		for p in level.get_points_in_rect(x - 1, y - 1, x + 1, y + 1):
			level.show_effect(p.x, p.y, Tags.Poison)
			unit = level.get_unit_at(p.x, p.y)
			if unit:
				unit.apply_buff(self.buff(), self.apply_duration)

		yield

class FalseProphetHolyBlast(Spell):

	def on_init(self):
		self.name = "Heavenly Blast"
		self.description = "Beam Attack\nHeals allies in the area"
		self.radius = 1
		self.range = 6
		self.damage = 7
		self.damage_type = Tags.Holy

	def get_ai_target(self):
		enemy = self.get_corner_target(1)
		if enemy:
			return enemy
		else:
			allies = [u for u in self.caster.level.get_units_in_ball(self.caster, self.get_stat('range')) if u != self.caster and not are_hostile(self.caster, u)]
			allies = [u for u in allies if self.caster.level.can_see(self.caster.x, self.caster.y, u.x, u.y)]
			allies = [u for u in allies if u.cur_hp < u.max_hp]
			if allies:
				return random.choice(allies)
		return None

	def cast(self, x, y):
		target = Point(x, y)

		def deal_damage(point):
			unit = self.caster.level.get_unit_at(point.x, point.y)
			if unit and not are_hostile(unit, self.caster) and not unit == self.caster:
				unit.deal_damage(-self.get_stat('damage'), Tags.Heal, self)
			elif unit == self.caster:
				pass
			else:
				self.caster.level.deal_damage(point.x, point.y, self.get_stat('damage'), Tags.Holy, self)

		points_hit = set()
		for point in Bolt(self.caster.level, self.caster, target):
			deal_damage(point)
			points_hit.add(point)
			yield

		stagenum = 0
		for stage in Burst(self.caster.level, target, self.get_stat('radius')):
			for point in stage:
				if point in points_hit:
					continue
				deal_damage(point)

			stagenum += 1
			for i in range(3):
				yield

def FalseProphet():

	unit = Unit()
	unit.name = "False Prophet"

	unit.max_hp = 28

	unit.spells.append(FalseProphetHolyBlast())
	unit.buffs.append(ReincarnationBuff(1))

	unit.resists[Tags.Holy] = 100
	unit.resists[Tags.Fire] = 50

	unit.tags = [Tags.Living, Tags.Holy]
	return unit

def GreenMushboom():

	unit = Unit()
	unit.name = "Green Mushboom"

	unit.asset_name = "mushboom_green"

	unit.max_hp = 11

	def spores(caster, target):
		target.apply_buff(Poison(), 4)

	spores = SimpleRangedAttack(damage=1, damage_type=Tags.Poison, range=2, onhit=spores)
	spores.cool_down = 3
	spores.name = "Poison Puff"
	spores.description = "Applies 4 turns of poison"
	unit.spells.append(spores)
	
	unit.buffs.append(MushboomBuff(Poison, 12))

	unit.resists[Tags.Fire] = -50
	unit.resists[Tags.Ice] = -50
	unit.resists[Tags.Poison] = 100
	unit.tags = [Tags.Nature]

	return unit

def GreyMushboom():

	unit = Unit()
	unit.name = "Grey Mushboom"

	unit.asset_name = "mushboom_grey"

	unit.max_hp = 11

	def spores(caster, target):
		target.apply_buff(Stun(), 2)

	spores = SimpleRangedAttack(damage=1, damage_type=Tags.Poison, range=2, onhit=spores)
	spores.cool_down = 5
	spores.name = "Spore Puff"
	spores.description = "Applies 2 turns of stun"
	unit.spells.append(spores)
	
	unit.buffs.append(MushboomBuff(Stun, 3))

	unit.resists[Tags.Fire] = -50
	unit.resists[Tags.Ice] = -50
	unit.resists[Tags.Poison] = 100
	unit.tags = [Tags.Nature]

	return unit

class RedMushboomBuff(Buff):

	def on_init(self):
		self.name = "Fire Spores"
		self.owner_triggers[EventOnDeath] = self.on_death
		self.description = "On death, deals 9 fire damage to adjacent units"

	def on_death(self, evt):
		self.owner.level.queue_spell(self.explode())

	def explode(self):
		for p in self.owner.level.get_adjacent_points(self.owner):
			self.owner.level.deal_damage(p.x, p.y, 9, Tags.Fire, self)
		yield

def GlassMushboom():
	unit = Unit()
	unit.name = "Glass Mushboom"
	unit.asset_name = "mushboom_glass"
	unit.max_hp = 11
	unit.shields = 2

	unit.resists[Tags.Poison] = 100

	unit.tags = [Tags.Nature, Tags.Glass, Tags.Construct, Tags.Arcane]
	
	def spores(caster, target):
		target.apply_buff(GlassPetrifyBuff(), 2)

	spores = SimpleRangedAttack(damage=1, damage_type=Tags.Physical, range=2, onhit=spores, effect=Tags.Glassification)
	spores.cool_down = 4
	spores.name = "Glass Gas"
	spores.description = "Applies 2 turns of glassification to living enemies"

	unit.spells.append(spores)

	unit.buffs.append(MushboomBuff(GlassPetrifyBuff, 3))
	return unit


def RedMushboom():
	unit = Unit()
	unit.name = "Red Mushboom"

	unit.asset_name = "mushboom_red"

	unit.max_hp = 11

	spores = SimpleRangedAttack(damage=5, damage_type=Tags.Fire, range=2)
	spores.cool_down = 3
	spores.name = "Fire Spores"
	unit.spells.append(spores)

	unit.buffs.append(RedMushboomBuff())

	unit.resists[Tags.Fire] = 100
	unit.resists[Tags.Ice] = -50
	unit.resists[Tags.Poison] = 100
	unit.tags = [Tags.Nature, Tags.Fire]
	return unit

def SwampQueen():
	unit = Unit()
	unit.name = "Swamp Queen"
	unit.max_hp = 59
	unit.shields = 2

	def mushboom():
		return random.choice([GreyMushboom(), GreenMushboom()])

	s1 = SimpleSummon(mushboom, num_summons=5, cool_down=12)
	s1.name = "Mushbloom"
	s1.description = "Summons 5 grey or green mushbooms"
	unit.spells.append(s1)

	heal = HealAlly(heal=18, range=9)
	heal.cool_down = 5
	unit.spells.append(heal)

	def spores(caster, target):
		if Tags.Living in target.tags:
			target.apply_buff(Poison(), 4)

	gaze = SimpleRangedAttack(damage=1, damage_type=Tags.Poison, onhit=spores, range=14)
	gaze.onhit = spores
	gaze.name = "Toxic Gaze"
	gaze.description = "Applies poison for 4 turns"
	unit.spells.append(gaze)

	unit.tags = [Tags.Poison, Tags.Living, Tags.Nature]
	return unit

def ThornPlant():
	unit = Unit()
	unit.name = "Spriggan Bush"
	unit.max_hp = 6

	unit.resists[Tags.Physical] = 50
	unit.resists[Tags.Fire] = -100

	unit.spells.append(SimpleMeleeAttack(3))
	unit.stationary = True
	unit.tags = [Tags.Nature]
	return unit

def Spriggan():

	unit = Unit()
	unit.name = "Spriggan"

	unit.max_hp = 9

	unit.resists[Tags.Physical] = 50
	unit.resists[Tags.Fire] = -100

	unit.buffs.append(RespawnAs(ThornPlant))
	unit.spells.append(SimpleMeleeAttack(2))

	unit.tags = [Tags.Living, Tags.Nature]
	return unit

def IcySprigganBush():
	unit = ThornPlant()
	unit.name = "Icy Spriggan Bush"
	unit.asset_name = "spriggan_bush_icy"

	ice = SimpleRangedAttack(damage=3, range=4, damage_type=Tags.Ice)
	ice.name = "Ice"
	unit.spells.append(ice)
	return unit

def IcySpriggan():
	unit = Spriggan()
	unit.name = "Icy Spriggan"
	unit.asset_name = "spriggan_icy"
	unit.buffs = [RespawnAs(IcySprigganBush)]
	unit.resists[Tags.Ice] = 100
	ice = SimpleRangedAttack(damage=3, range=4, damage_type=Tags.Ice)
	ice.name = "Ice"
	unit.spells = [ice]

	return unit

class Regrow(Spell):

	def on_init(self):
		self.name = "Regrow"
		self.description = "Heals self for 12 HP"
		self.cool_down = 3
		self.range = 0

	def cast_instant(self, x, y):
		self.caster.deal_damage(-12, Tags.Heal, self)

def Treant():

	unit = Unit()
	unit.name = "Treant"
	unit.asset_name = "cyclops_tree"

	unit.max_hp = 37

	unit.resists[Tags.Physical] = 50
	unit.resists[Tags.Fire] = -100

	unit.spells.append(Regrow())
	unit.spells.append(SimpleMeleeAttack(8))

	unit.tags = [Tags.Nature, Tags.Living]

	return unit

def VampireMist():
	unit = Ghost()
	unit.name = "Vampiric Mist"
	unit.asset_name = "ghost_vampire"

	unit.resists[Tags.Fire] = -100
	unit.max_hp = 12
	unit.buffs.append(MatureInto(GreaterVampire, 20))
	unit.is_coward = True

	unit.tags = [Tags.Undead, Tags.Dark]

	return unit


def GreaterVampire():

	unit = Unit()

	unit.name = "Greater Vampire"

	unit.sprite.char = 'V'
	unit.sprite.color = Color(185, 72, 214)

	unit.resists[Tags.Fire] = -100

	unit.max_hp = 48
	unit.flying = True

	def drain(self, target):
		self.max_hp += 7
		self.cur_hp += 7
		drain_max_hp(target, 7)

	melee = SimpleMeleeAttack(damage=7, damage_type=Tags.Dark, onhit=drain)
	melee.name = "Greater Life Drain"
	melee.description = "Drains max hp"
	unit.spells.append(melee)

	unit.buffs.append(RespawnAs(VampireMist))

	unit.tags = [Tags.Undead, Tags.Dark]

	return unit

def VampireEye():
	unit = Unit()
	unit.name = "Vampire Eye"
	unit.sprite.char = 'e'
	unit.sprite.color = Tags.Arcane.color
	unit.max_hp = 10
	unit.shields = 1
	unit.resists[Tags.Arcane] = 50
	unit.flying = True
	unit.is_coward = True

	drain = SimpleRangedAttack(damage=2, range=99, damage_type=Tags.Dark)
	drain.onhit = lambda caster, target: caster.deal_damage(-2, Tags.Heal, drain)
	drain.name = "Life Drain"
	drain.cool_down = 2
	drain.description = "Drains life"

	unit.spells.append(drain)

	unit.buffs.append(TeleportyBuff())

	unit.buffs.append(MatureInto(MindVampire, 20))

	unit.tags = [Tags.Arcane, Tags.Dark, Tags.Undead]
	return unit

def MindVampire():

	unit = Unit()

	unit.name = "Mind Vampire"

	unit.resists[Tags.Arcane] = 50
	unit.resists[Tags.Fire] = -100

	unit.max_hp = 25
	unit.shields = 3
	unit.flying = True

	def mind_drain(self, target):
		if self.shields < 3:
			self.add_shields(1)
		drain_spell_charges(self, target)
	
	melee = SimpleMeleeAttack(damage=7, damage_type=Tags.Arcane, onhit=mind_drain)
	melee.name = "Mind Drain"
	melee.description = "Drains spell charges from the target and adds 1 shield to the caster, to a max of 3."

	unit.spells.append(melee)

	unit.buffs.append(RespawnAs(VampireEye))

	unit.tags = [Tags.Arcane, Tags.Dark, Tags.Undead]

	return unit


def FaeThorn():
	unit = Unit()
	unit.name = "Fae Thorn"
	unit.sprite.char = 't'
	unit.sprite.color = Color(90, 130, 100)

	unit.max_hp = 10
	unit.spells.append(SimpleMeleeAttack(damage=4))
	unit.stationary = 10
	unit.turns_to_death = 6
	unit.tags = [Tags.Nature, Tags.Arcane]
	return unit

class ThornQueenFairySummonSpell(Spell):

	def on_init(self):
		self.range = 0
		self.name = "Fae Queen's Guard"
		self.cool_down = 10
		self.description = "Summons 4 Evil Faeries for 15 turns"

	def get_ai_target(self):
		return Point(self.caster.x, self.caster.y)

	def cast_instant(self, x, y):
		for i in range(4):
			unit = EvilFairy()
			unit.turns_to_death = 15
			unit.team = self.caster.team
			point = self.caster.level.get_summon_point(self.caster.x, self.caster.y)
			if point:
				self.caster.level.add_obj(unit, point.x, point.y)

class ThornQueenThornBuff(Buff):

	def on_init(self):
		self.radius = 6

	def get_tooltip(self):
		return "Summons a fae thorn up to %d tiles away each turn." % self.radius

	def is_target_valid(self, t):
		return self.owner.level.tiles[t.x][t.y].can_walk and self.owner.level.tiles[t.x][t.y].unit is None

	def on_advance(self):
		valid_summon_points = [t for t in self.owner.level.get_points_in_ball(self.owner.x, self.owner.y, self.radius) if self.is_target_valid(t)]
		if valid_summon_points:
			p = random.choice(valid_summon_points)
			thorn = FaeThorn()
			thorn.team = self.owner.team
			self.owner.level.add_obj(thorn, p.x, p.y)


def ThornQueen():

	unit = Unit()

	unit.name = "Fae Queen"
	unit.max_hp = 50
	unit.shields = 2

	unit.resists[Tags.Arcane] = 100
	unit.resists[Tags.Physical] = 50

	unit.sprite.char = 'Q'
	unit.sprite.color = Color(252, 141, 249)
	
	unit.spells.append(ThornQueenFairySummonSpell())
	unit.spells.append(SimpleRangedAttack(damage=7, range=4, damage_type=Tags.Arcane))
	unit.flying = True
		
	unit.buffs.append(TeleportyBuff(chance=.5))
	unit.buffs.append(ThornQueenThornBuff())
	unit.buffs.append(HealAuraBuff(heal=6, radius=8))
	unit.buffs.append(ShieldRegenBuff(shield_freq=3, shield_max=2))

	unit.tags = [Tags.Living, Tags.Nature, Tags.Arcane]
	# Summon 4 fae adjacent- 10 turn CD
	# Passive- each turn, if enemy in line of sight, summon thorn
	# Passive- each turn, heal all damaged allies in LOS for 6

	return unit

def FloatingEye():
	unit = Unit()
	unit.name = "Floating Eyeball"
	unit.sprite.char = 'e'
	unit.sprite.color = Tags.Arcane.color
	unit.max_hp = 1
	unit.shields = 4
	unit.resists[Tags.Arcane] = 100
	unit.flying = True
	unit.spells.append(SimpleRangedAttack(damage=2, range=99, damage_type=Tags.Arcane))
	unit.buffs.append(TeleportyBuff())

	unit.tags = [Tags.Arcane, Tags.Demon]
	return unit

def FlamingEye():
	unit = FloatingEye()
	unit.name = "Flaming Eyeball"
	unit.spells[0].radius = 1
	unit.spells[0].damage_type = Tags.Fire
	unit.spells[0].damage = 4
	unit.tags.append(Tags.Fire)
	unit.resists[Tags.Arcane] = 50
	unit.resists[Tags.Fire] = 100

	return unit

def Elf():
	unit = Unit()
	unit.name = "Aelf"
	unit.sprite.char = 'e'
	unit.sprite.color = Color(220, 220, 220)
	unit.max_hp = 18
	unit.shields = 1
	unit.resists[Tags.Dark] = 50
	unit.resists[Tags.Lightning] = 75
	unit.spells.append(SimpleMeleeAttack(damage=10, damage_type=Tags.Dark))
	unit.spells.append(SimpleRangedAttack(damage=3, range=12, damage_type=Tags.Lightning))
	unit.tags = [Tags.Living, Tags.Lightning, Tags.Dark]
	return unit

def Dwarf():
	unit = Unit()
	unit.name = "Duergar"
	unit.sprite.char = 'd'
	unit.sprite.color = Color(128, 122, 60)
	unit.max_hp = 25
	unit.resists[Tags.Physical] = 50
	unit.resists[Tags.Dark] = 50
	unit.resists[Tags.Lightning] = -50
	crossbow = SimpleRangedAttack(damage=8, range=16, damage_type=Tags.Physical, proj_name="duergar_bolt")
	crossbow.name = "Crossbow"
	crossbow.cool_down = 5
	sword = SimpleMeleeAttack(damage=3)
	sword.name = "Short Sword"
	unit.spells.append(crossbow)
	unit.spells.append(sword)
	unit.tags = [Tags.Living, Tags.Dark]
	return unit

def Redcap():
	unit = Unit()
	unit.name = "Redcap"
	unit.max_hp = 14
	unit.shields = 1
	unit.resists[Tags.Fire] = 75
	unit.resists[Tags.Arcane] = 50
	unit.resists[Tags.Ice] = -50

	unit.tags = [Tags.Living, Tags.Arcane, Tags.Fire]

	def summon_thorn(caster, target):
		thorn = RedMushboom()
		p = caster.level.get_summon_point(target.x, target.y, 2)
		if p:
			caster.level.summon(unit, thorn, p)

	attack = SimpleRangedAttack(damage=1, range=4, damage_type=Tags.Physical, onhit=summon_thorn, cool_down=2)
	attack.description = "Summons a red mushboom near the target"
	attack.name = "Fire Seed"
	
	unit.spells.append(attack)
	return unit

def Gnome():
	unit = Unit()
	unit.name = "Gnome"
	unit.sprite.char = 'g'
	unit.sprite.color = Color(50, 255, 150)
	unit.max_hp = 10
	unit.shields = 1

	unit.resists[Tags.Arcane] = 50

	def summon_thorn(caster, target):
		thorn = FaeThorn()
		p = caster.level.get_summon_point(target.x, target.y, 1.5)
		if p:
			caster.level.summon(unit, thorn, p)

	attack = SimpleRangedAttack(damage=1, range=4, damage_type=Tags.Physical, onhit=summon_thorn)
	attack.description = "Summons a fae thorn adjacent to the target"
	attack.name = 'Thorn Bolt'
	unit.spells.append(attack)

	unit.tags = [Tags.Living, Tags.Nature, Tags.Arcane]
	return unit

class MonsterChainLightning(Spell):

	def on_init(self):
		self.name = "Chain Lightning"
		self.range = 9
		self.tags = [Tags.Lightning, Tags.Sorcery]
		self.level = 4
		self.damage = 7
		self.element = Tags.Lightning
		self.arc_range = 4

		self.damage_type = Tags.Lightning

	def cast(self, x, y):

		prev = self.caster
		target = self.caster.level.get_unit_at(x, y) or Point(x, y)
		already_hit = set()

		while target or prev == self.caster:

			for p in self.caster.level.get_points_in_line(prev, target, find_clear=True)[1:]:
				self.caster.level.deal_damage(p.x, p.y, 0, Tags.Lightning, self)
				yield

			self.caster.level.deal_damage(target.x, target.y, self.get_stat('damage'), self.element, self)
			yield

			already_hit.add(target)

			def can_arc(u, prev):
				if not self.caster.level.are_hostile(self.caster, u):
					return False
				if u in already_hit:
					return False
				if not self.caster.level.can_see(prev.x, prev.y, u.x, u.y):
					return False
				return True

			units = [u for u in self.caster.level.get_units_in_ball(target, self.arc_range) if can_arc(u, target)]
			
			prev = target
			if units:
				target = random.choice(units)
			else:
				target = None			

	def get_description(self):
		return "Chains to targets up to %d tiles away." % self.arc_range

	def can_threaten(self, x, y):
		return self.can_threaten_corner(x, y, self.arc_range)

	def get_ai_target(self):
		# Target as if it were a fireball of radius arc_range
		return self.get_corner_target(self.arc_range)

def ElfLightningLord():
	unit = Unit()
	unit.name = "Aelf Lightning Artist"
	unit.asset_name = "aelf_lightning_lord"
	unit.sprite.char = 'e'
	unit.sprite.color = Tags.Lightning.color
	unit.max_hp = 27
	unit.shields = 2
	unit.resists[Tags.Dark] = 50
	unit.resists[Tags.Lightning] = 100
	unit.spells.append(SimpleMeleeAttack(damage=10, damage_type=Tags.Lightning))
	unit.spells.append(MonsterChainLightning())
	unit.tags = [Tags.Living, Tags.Lightning, Tags.Dark]
	return unit

def OrcFireShaman():
	unit = Unit()
	unit.sprite.char = 'o'
	unit.sprite.color = Tags.Fire.color
	unit.name = "Orc Pyromancer"
	unit.resists[Tags.Fire] = 50
	unit.max_hp = 26
	unit.spells.append(SimpleMeleeAttack(5))
	unit.spells.append(SimpleRangedAttack(name='Fireball', damage=8, damage_type=Tags.Fire, range=7, radius=2))
	unit.tags = [Tags.Living]
	return unit

def FaeArcanist():
	unit = Unit()
	unit.sprite.char = 'f'
	unit.sprite.color = Tags.Arcane.color
	unit.name = "Faery Arcanist"
	unit.max_hp = 15
	unit.shields = 2
	unit.buffs.append(TeleportyBuff(chance=.7))
	unit.buffs.append(ShieldRegenBuff(2, 3))
	unit.spells.append(HealAlly(heal=9, range=6))

	blast = SimpleRangedAttack(damage=4, range=5, radius=1, damage_type=Tags.Arcane, onhit=remove_buff)
	blast.name = "Arcane Blast"
	blast.description = "Removes 1 buff"

	unit.spells.append(blast)

	unit.resists[Tags.Arcane] = 50

	unit.tags = [Tags.Nature, Tags.Arcane, Tags.Living]
	return unit

def RedFiend():
	unit = Unit()
	unit.sprite.char = 'P'
	unit.sprite.color = Tags.Fire.color
	unit.name = "Fire Fiend"

	unit.asset_name = 'fire_demon'

	unit.max_hp = 166

	fireball = SimpleRangedAttack(damage=13, range=6, radius=2, damage_type=Tags.Fire)
	fireball.cool_down = 2

	deathgaze = SimpleRangedAttack(damage=5, range=16, beam=True, damage_type=Tags.Dark)
	deathgaze.cool_down = 2
	summon_imps = SimpleSummon(spawn_func=FireImp, num_summons=3, cool_down=7)

	unit.spells.append(fireball)
	unit.spells.append(deathgaze)
	unit.spells.append(summon_imps)

	unit.resists[Tags.Fire] = 100
	unit.resists[Tags.Dark] = 100
	unit.resists[Tags.Ice] = -50

	unit.tags = [Tags.Fire, Tags.Demon]

	return unit

def ChaosFiend():
	unit = Unit()

	unit.name = "Chaos Fiend"
	unit.asset_name = "fiend_chaos"

	unit.max_hp = 166

	chaosball = SimpleRangedAttack(damage=13, range=6, radius=3, damage_type=[Tags.Fire, Tags.Lightning, Tags.Physical])
	chaosball.name = "Chaos Ball"

	deathgaze = SimpleRangedAttack(damage=5, range=16, beam=True, damage_type=Tags.Dark)
	deathgaze.cool_down = 2

	summon_imps = SimpleSummon(spawn_func=ChaosImp, num_summons=3, cool_down=7)

	unit.spells = [summon_imps, chaosball, deathgaze]

	unit.tags = [Tags.Fire, Tags.Lightning, Tags.Demon]
	unit.resists[Tags.Fire] = 100
	unit.resists[Tags.Lightning] = 100
	unit.resists[Tags.Ice] = -50

	return unit

class FiendConductance(Buff):
	
	def on_init(self):
		self.name = "Conductivity"
		self.resists[Tags.Lightning] = -100
		self.color = Tags.Lightning.color
		self.asset = ['status', 'conductance']
		self.buff_type = BUFF_TYPE_CURSE

def CopperFiend():
	unit = Unit()

	unit.name = "Copper Fiend"
	unit.asset_name = "fiend_copper"

	unit.max_hp = 166

	conductance = SimpleCurse(FiendConductance, 7)
	conductance.cool_down = 3
	conductance.name = "Conductivity"
	conductance.range = 10

	summon_imps = SimpleSummon(CopperImp, num_summons=3, cool_down=7)

	deathgaze = SimpleRangedAttack(damage=5, range=16, beam=True, damage_type=Tags.Dark)
	deathgaze.cool_down = 2

	lightningbolt = SimpleRangedAttack(damage=5, range=11, beam=True, damage_type=Tags.Lightning)

	unit.spells = [summon_imps, conductance, deathgaze, lightningbolt]
	unit.tags = [Tags.Lightning, Tags.Metallic, Tags.Demon]

	unit.resists[Tags.Lightning] = 100

	return unit

def FurnaceFiend():
	unit = Unit()

	unit.name = "Furnace Fiend"
	unit.asset_name = "fiend_furnace"

	unit.max_hp = 166

	summon_imps = SimpleSummon(FurnaceImp, num_summons=3, cool_down=7)
	deathgaze = SimpleRangedAttack(damage=5, range=16, beam=True, damage_type=Tags.Dark)
	deathgaze.cool_down = 2
	
	unit.resists[Tags.Ice] = -50
	unit.resists[Tags.Lightning] = 75

	fireblast = FireBreath()

	fireblast.range = 5
	fireblast.damage = 13
	fireblast.name = "Fire Blast"
	fireblast.cool_down = 0	

	unit.spells = [summon_imps, deathgaze, fireblast]

	unit.buffs.append(DamageAuraBuff(damage=2, damage_type=Tags.Fire, radius=7))
	unit.tags = [Tags.Fire, Tags.Metallic, Tags.Demon]

	return unit

def InsanityFiend():
	unit = Unit()

	unit.name = "Insanity Fiend"
	unit.asset_name = "fiend_insanity"

	unit.max_hp = 166

	summon_imps = SimpleSummon(InsanityImp, num_summons=3, cool_down=7)
	deathgaze = SimpleRangedAttack(damage=5, range=16, beam=True, damage_type=Tags.Dark)
	deathgaze.cool_down = 2
	disrupt = lambda caster, target : randomly_teleport(caster, 3)
	bolt = SimpleRangedAttack(damage=3, range=7, onhit=disrupt, damage_type=Tags.Arcane)
	bolt.name = "Phase Bolt"
	unit.spells = [summon_imps, deathgaze, bolt]

	unit.resists[Tags.Arcane] = 100

	unit.tags = [Tags.Arcane, Tags.Demon]
	return unit

def RotFiend():
	unit = Unit()
	unit.name = "Rot Fiend"
	unit.asset_name = "fiend_rot"

	unit.max_hp = 166

	summon_imps = SimpleSummon(RotImp, num_summons=3, cool_down=7)
	deathgaze = SimpleRangedAttack(damage=5, range=16, beam=True, damage_type=Tags.Dark)
	deathgaze.cool_down = 2

	def rot(caster, target):
		drain_max_hp(target, 3)

	rotball = SimpleRangedAttack(damage=4, range=6, radius=2, damage_type=Tags.Dark, onhit=rot)
	rotball.description = "Targets permenantly lose 3 max hp."
	rotball.name = "Rot Blast"

	unit.spells = [summon_imps, deathgaze, rotball]

	unit.tags = [Tags.Dark, Tags.Demon]
	return unit

def AshFiend():
	unit = Unit()
	unit.name = "Ash Fiend"
	unit.asset_name = "fiend_ash"

	unit.max_hp = 166
	
	summon_imps = SimpleSummon(AshImp, num_summons=3, cool_down=7)
	
	deathgaze = SimpleRangedAttack(damage=5, range=16, beam=True, damage_type=Tags.Dark)
	deathgaze.cool_down = 2

	ashblast = SimpleRangedAttack(damage=7, range=6, radius=3, damage_type=[Tags.Fire, Tags.Dark, Tags.Poison], buff=BlindBuff, buff_duration=1)
	ashblast.cool_down = 2
	ashblast.name = "Ash Blast"	
	
	unit.spells = [summon_imps, ashblast, deathgaze]
	unit.tags = [Tags.Fire, Tags.Demon]
	unit.resists[Tags.Fire] = 100

	return unit


class FiendStormBolt(Spell):

	def on_init(self):
		self.name = "Storm Bolt"
		self.description = "A beam which leaves storm clouds along its path"
		self.damage = 9
		self.damage_type = Tags.Lightning
		self.cool_down = 2
		self.range = 7

	def cast_instant(self, x, y):
		for p in self.caster.level.get_points_in_line(self.caster, Point(x, y), find_clear=True)[1:]:
			self.caster.level.deal_damage(p.x, p.y, self.damage, self.damage_type, self)
			self.caster.level.add_obj(StormCloud(self.caster, self.damage), p.x, p.y)

def YellowFiend():
	unit = Unit()
	unit.sprite.char = 'P'
	unit.sprite.color = Tags.Lightning.color
	unit.name = "Storm Fiend"

	unit.asset_name = 'spark_demon'

	unit.max_hp = 166

	deathgaze = SimpleRangedAttack(damage=5, range=16, beam=True, damage_type=Tags.Dark)
	deathgaze.cool_down = 2
	summon_imps = SimpleSummon(spawn_func=SparkImp, num_summons=3, cool_down=7)

	unit.spells.append(FiendStormBolt())
	unit.spells.append(deathgaze)
	unit.spells.append(summon_imps)

	unit.tags = [Tags.Lightning, Tags.Demon]

	unit.resists[Tags.Lightning] = 100

	return unit

def IronFiend():
	unit = Unit()
	unit.sprite.char = 'P'
	unit.sprite.color = Tags.Construct.color
	unit.name = "Iron Fiend"

	unit.asset_name = 'iron_demon'

	unit.max_hp = 166

	ironshot = SimpleRangedAttack(damage=7, range=16, effect=Tags.Petrification)
	ironshot.name = "Iron Gaze"
	ironshot.description = "Petrifies target for 1 turn"
	ironshot.onhit = lambda caster, target: target.apply_buff(PetrifyBuff(), 1)
	ironshot.cool_down = 5

	deathgaze = SimpleRangedAttack(damage=5, range=16, beam=True, damage_type=Tags.Dark)
	deathgaze.name = "Death Beam"
	deathgaze.cool_down = 2
	summon_imps = SimpleSummon(spawn_func=IronImp, num_summons=3, cool_down=7)

	unit.spells.append(ironshot)
	unit.spells.append(deathgaze)
	unit.spells.append(summon_imps)

	unit.tags = [Tags.Metallic, Tags.Demon]

	return unit

def Troubler():
	unit = Unit()
	unit.sprite.char = 'T'
	unit.sprite.color = Tags.Arcane.color
	unit.name = "Troubler"

	unit.max_hp = 1
	unit.shields = 1

	unit.resists[Tags.Arcane] = 100

	phasebolt = SimpleRangedAttack(damage=2, range=10, damage_type=Tags.Arcane)
	phasebolt.onhit = lambda caster, target: randomly_teleport(target, 3)
	phasebolt.name = "Phase Bolt"
	phasebolt.description = "Teleports victims randomly up to 3 tiles away"

	unit.spells.append(phasebolt)
	unit.flying=True
	unit.stationary=True

	unit.buffs.append(TeleportyBuff(chance=.1, radius=8))

	unit.tags = [Tags.Arcane]
	unit.asset_name = 'mask'

	return unit

def Witch():

	unit = Unit()
	unit.sprite.char = 'w'
	unit.sprite.color = Tags.Dark.color
	unit.name = "Witch"

	unit.max_hp = 13
	unit.flying = True

	ghosty = SimpleSummon(Ghost, num_summons=1, duration=10, cool_down=5)
	deathbolt = SimpleRangedAttack(damage=3, range=5, damage_type=Tags.Dark)

	unit.spells.append(ghosty)
	unit.spells.append(deathbolt)

	unit.asset_name = 'witch'

	unit.tags = [Tags.Living, Tags.Dark]
	unit.resists[Tags.Dark] = 50
	unit.resists[Tags.Fire] = -50
	unit.resists[Tags.Holy] = -50
	return unit

def OldWitch():

	unit = Unit()
	unit.sprite.char = 'W'
	unit.sprite.color = Tags.Dark.color
	unit.name = "Old Witch"

	unit.max_hp = 24

	ghosty = SimpleSummon(Ghost, num_summons=2, duration=10, cool_down=5)

	lifedrain = SimpleRangedAttack(damage=7, range=6, damage_type=Tags.Dark, drain=True)
	lifedrain.name = "Life Drain"

	unit.spells.append(ghosty)
	unit.spells.append(lifedrain)

	unit.tags = [Tags.Living, Tags.Dark]
	unit.resists[Tags.Dark] = 50
	unit.resists[Tags.Fire] = -50
	unit.resists[Tags.Holy] = -50
	return unit

def WitchFire():
	unit = Witch()
	unit.name = "Fire Witch"
	unit.asset_name = "witch_fire"
	unit.max_hp += 9

	unit.resists[Tags.Fire] = 50
	unit.resists[Tags.Ice] = -50
	fireghosty = SimpleSummon(GhostFire, num_summons=1, duration=10, cool_down=5)
	

	def burn_ghost(caster, target):
		if target.cur_hp > 0:
			return
		if Tags.Living not in target.tags and Tags.Undead not in target.tags:
			return
		
		p = target.level.get_summon_point(target.x, target.y)
		if p:
			ghost = GhostFire()
			ghost.turns_to_death = 10
			target.level.add_obj(ghost, p.x, p.y)

	fireball = SimpleRangedAttack(damage=5, damage_type=[Tags.Fire, Tags.Dark], range=5, radius=2, onhit=burn_ghost)
	fireball.description = "Slain living and undead units are raised as fire ghosts."
	fireball.name = "Infernal Fireball"

	unit.tags.append(Tags.Fire)
	unit.spells = [fireghosty, fireball]

	return unit

def OldBloodWitch():
	unit = Unit()
	unit.name = "Old Blood Witch"

	unit.max_hp = 24

	ghosty = SimpleSummon(Bloodghast, num_summons=2, duration=10, cool_down=5)

	lifedrain = SimpleRangedAttack(damage=7, range=6, damage_type=Tags.Dark)

	lifedrain.onhit = lambda caster, target: drain_frenzy(caster, target, lifedrain, 2)
	lifedrain.name = "Life Drain Frenzy"
	lifedrain.description = "Drains life.\nGains 2 damage for 10 turns on hit."

	unit.spells.append(ghosty)
	unit.spells.append(lifedrain)

	unit.tags = [Tags.Living, Tags.Dark]
	unit.resists[Tags.Dark] = 50
	unit.resists[Tags.Fire] = -50
	unit.resists[Tags.Holy] = -50
	return unit

def YoungBloodWitch():

	unit = Unit()
	unit.name = "Blood Witch"
	unit.max_hp = 13
	unit.flying = True

	ghosty = SimpleSummon(Bloodghast, num_summons=1, duration=10, cool_down=5)

	lifedrain = SimpleRangedAttack(damage=3, range=5, damage_type=Tags.Dark)

	lifedrain.onhit = lambda caster, target: drain_frenzy(caster, target, lifedrain, 1)
	lifedrain.name = "Life Drain Frenzy"
	lifedrain.description = "Drains life.\nGains 1 damage for 10 turns on hit."

	unit.spells.append(ghosty)
	unit.spells.append(lifedrain)

	unit.tags = [Tags.Living, Tags.Dark]
	unit.resists[Tags.Dark] = 50
	unit.resists[Tags.Fire] = -50
	unit.resists[Tags.Holy] = -50
	return unit

def WildMan():
	unit = Unit()
	unit.name = "Wild Man"
	unit.asset_name = "werewolf_human"

	unit.max_hp = 8
	unit.is_coward = True

	unit.buffs.append(MatureInto(Werewolf, 20))

	unit.tags = [Tags.Living]
	return unit

def Werewolf():
	unit = Unit()
	unit.name = "Werewolf"
	unit.asset_name = "werewolf_transformed"
	unit.max_hp = 18

	unit.spells.append(SimpleMeleeAttack(6))
	leap = LeapAttack(damage=6, range=4)
	leap.cool_down = 3
	unit.spells.append(leap)

	unit.resists[Tags.Dark] = 75
	unit.resists[Tags.Holy] = -50

	unit.buffs.append(RespawnAs(WildMan))

	unit.tags = [Tags.Living, Tags.Nature, Tags.Dark]
	return unit

class CultistPain(Spell):

	def on_init(self):
		self.name = "Pain"
		self.description = "Deals 1 damage to caster\nIgnores walls"
		self.requires_los = False
		self.range = 6
		self.damage = 1
		self.damage_type = Tags.Dark

	def cast_instant(self, x, y):
		self.caster.deal_damage(1, Tags.Physical, self)
		for p in self.caster.level.get_points_in_line(self.caster, Point(x, y))[1:-1]:
			self.caster.level.show_effect(p.x, p.y, Tags.Dark)
		self.caster.level.deal_damage(x, y, self.get_stat('damage'), Tags.Dark, self)


def Cultist():
	unit = Unit()
	unit.name = "Cultist"
	unit.max_hp = 6

	unit.spells.append(CultistPain())

	unit.tags = [Tags.Living, Tags.Dark]
	
	unit.resists[Tags.Dark] = 50
	unit.resists[Tags.Holy] = -50

	return unit


class GreenGorgonBreath(BreathWeapon):

	def __init__(self):
		BreathWeapon.__init__(self)
		self.name = "Green Gorgon Breath"
		self.duration = 15
		self.damage_type = Tags.Poison
		self.cool_down = 10
		self.range = 5
		self.angle = math.pi / 6.0

	def get_description(self):
		return "Breathes poison gas, poisoning living enemies"

	def per_square_effect(self, x, y):
		unit = self.caster.level.get_unit_at(x, y)
		if unit and Tags.Living in unit.tags:
			self.caster.level.deal_damage(x, y, 0, self.damage_type, self)
			unit.apply_buff(Poison(), self.get_stat('duration'))
		else:
			self.caster.level.deal_damage(x, y, 0, self.damage_type, self)

def GreenGorgon():

	unit = Unit()
	unit.sprite.char = 'G'
	unit.sprite.color = Tags.Construct.color
	unit.asset_name = 'poison_gorgon'
	unit.name = 'Green Gorgon'

	unit.max_hp = 66

	unit.spells.append(GreenGorgonBreath())
	unit.spells.append(SimpleMeleeAttack(damage=13))
	
	unit.tags = [Tags.Poison, Tags.Living]
	unit.resists[Tags.Poison] = 100
	return unit

class GreyGorgonBreath(BreathWeapon):

	def __init__(self):
		BreathWeapon.__init__(self)
		self.name = "Grey Gorgon Breath"
		self.damage = 9
		self.damage_type = Tags.Physical
		self.cool_down = 10
		self.range = 5
		self.angle = math.pi / 6.0

	def get_description(self):
		return "Breathes a petrifying gas dealing %d physical damage and petrifying living creatures" % self.damage

	def per_square_effect(self, x, y):
		self.caster.level.show_effect(x, y, Tags.Petrification)
		unit = self.caster.level.get_unit_at(x, y)
		if unit and Tags.Living in unit.tags:
			self.caster.level.deal_damage(x, y, self.damage, self.damage_type, self)
			unit.apply_buff(PetrifyBuff(), 2)

def GreyGorgon():

	unit = Unit()
	unit.sprite.char = 'G'
	unit.sprite.color = Tags.Construct.color
	unit.asset_name = 'Gorgon'
	unit.name = 'Grey Gorgon'

	unit.max_hp = 88

	unit.spells.append(GreyGorgonBreath())
	unit.spells.append(SimpleMeleeAttack(damage=13))
	
	unit.tags = [Tags.Dark, Tags.Living]
	unit.resists[Tags.Physical] = 75
	unit.resists[Tags.Dark] = 75
	return unit


class LichSealSoulSpell(Spell):

	def on_init(self):
		self.name = "Soul Jar"
		self.description = "Summon a soul jar.  The caster is unkillable while the soul jar exists.  Limit one jar per lich."
		self.range = 0
		self.cool_down = 20

	def can_cast(self, x, y):
		return not self.caster.has_buff(Soulbound) and Spell.can_cast(self, x, y)

	def cast_instant(self, x, y):

		phylactery = Unit()
		phylactery.name = 'Soul Jar'
		phylactery.max_hp = 6
		phylactery.stationary = True
		phylactery.tags = [Tags.Construct, Tags.Dark]

		if self.summon(phylactery, Point(x, y)):
			self.caster.apply_buff(Soulbound(phylactery))

def Lich():

	lich = Unit()
	lich.max_hp = 55
	lich.shields = 2
	lich.name = 'Lich'

	lich.spells.append(SimpleRangedAttack(damage=8, range=6, damage_type=Tags.Dark))
	lich.spells.append(LichSealSoulSpell())
	
	lich.resists[Tags.Dark] = 100
	lich.resists[Tags.Arcane] = 50

	lich.tags = [Tags.Dark, Tags.Undead]

	return lich


class HagDrain(Spell):

	def on_init(self):
		self.name = "Life Siphon"
		self.description = "Steal health from all living creatures in line of sight"
		self.damage = 2
		self.range = 0

	def can_cast(self, x, y):
		if self.caster.cur_hp >= self.caster.max_hp:
			return False
		if not any(Tags.Living in u.tags and u != self.caster for u in self.caster.level.get_units_in_los(self.caster)):
			return False
		return Spell.can_cast(self, x, y)

	def get_impacted_tiles(self, x, y):
		return self.caster.level.get_tiles_in_los(self.caster)

	def bolt(self, target):
		damage = target.deal_damage(self.get_stat('damage'), Tags.Dark, self)
		yield
		for p in self.caster.level.get_points_in_line(target, self.caster, find_clear=True)[1:-1]:
			self.caster.level.show_effect(p.x, p.y, Tags.Dark, minor=True)
			yield
		if damage:
			self.owner.deal_damage(-damage, Tags.Heal, self)

	def cast_instant(self, x, y):
		total = 0
		for u in self.caster.level.get_units_in_los(self.caster):
			if u == self.caster:
				continue
			if Tags.Living not in u.tags:
				continue

			self.owner.level.queue_spell(self.bolt(u))

def NightHag():

	hag = Unit()
	hag.max_hp = 84

	hag.name = "Night Hag"

	ghosty = SimpleSummon(Ghost, num_summons=3, duration=10, cool_down=5)
	hag.spells.append(ghosty)

	hag.spells.append(HagDrain())

	sleep_touch = SimpleMeleeAttack(damage=1, damage_type=Tags.Dark, buff=Stun, buff_duration=1)
	sleep_touch.cool_down = 3
	sleep_touch.name = "Sleep Touch"

	hag.spells.append(sleep_touch)

	hag.resists[Tags.Dark] = 75
	hag.resists[Tags.Arcane] = 50
	hag.resists[Tags.Holy] = -50
	hag.resists[Tags.Fire] = -50

	hag.tags = [Tags.Dark, Tags.Arcane, Tags.Living]
	return hag

class HagSwap(Spell):

	def on_init(self):
		self.name = "Aether Swap"
		self.description = "Swaps places\nOnly targets the Wizard"
		self.range = 12
		self.cool_down = 9

	def can_threaten(self, x, y):
		return distance(self.caster, Point(x, y)) <= self.range and self.caster.level.can_see(self.caster.x, self.caster.y, x, y)

	def can_cast(self, x, y):
		unit = self.caster.level.get_unit_at(x, y)
		if not unit:
			return False
		if unit == self.caster:
			return False
		# No interest in swapping wolves and such
		if not unit.is_player_controlled:
			return False
		if not self.caster.level.tiles[x][y].can_walk:
			return False
		return Spell.can_cast(self, x, y)

	def cast(self, x, y):

		target = self.caster.level.get_unit_at(x, y)

		# Do an animation so players see something happening
		for p in self.caster.level.get_points_in_ball(target.x, target.y, 1):
			if p.x == target.x and p.y == target.y:
				continue
			self.caster.level.show_effect(p.x, p.y, Tags.Translocation)

		for p in self.caster.level.get_points_in_ball(x, y, 1):
			if p.x == x and p.y == y:
				continue
			self.caster.level.show_effect(p.x, p.y, Tags.Translocation)

		yield

		path = self.caster.level.get_points_in_line(self.caster, Point(x, y), find_clear=True)
		for i in range(len(path)):
			p1 = path[i]
			p2 = path[-i]
			for p in [p1, p2]:
				self.caster.level.deal_damage(p.x, p.y, 0, Tags.Arcane, self)
				yield
				#yield

		self.caster.level.act_move(self.caster, x, y, teleport=True, force_swap=True)

		for p in self.caster.level.get_points_in_ball(target.x, target.y, 1):
			if p.x == target.x and p.y == target.y:
				continue
			self.caster.level.show_effect(p.x, p.y, Tags.Translocation)

		for p in self.caster.level.get_points_in_ball(x, y, 1):
			if p.x == x and p.y == y:
				continue
			self.caster.level.show_effect(p.x, p.y, Tags.Translocation)

def VoidHag():

	hag = Unit()
	hag.name = "Dream Hag"
	hag.asset_name = "night_hag_2"
	hag.max_hp = 67
	hag.shields = 2

	sleep_touch = SimpleMeleeAttack(damage=1, damage_type=Tags.Dark, buff=Stun, buff_duration=1)
	sleep_touch.cool_down = 3
	sleep_touch.name = "Sleep Touch"

	hag.spells.append(HagSwap())
	hag.spells.append(sleep_touch)

	hag.resists[Tags.Dark] = 50
	hag.resists[Tags.Arcane] = 75
	hag.resists[Tags.Holy] = -50
	hag.resists[Tags.Fire] = -50


	hag.buffs.append(ShieldRegenBuff(2, 2))

	hag.tags = [Tags.Dark, Tags.Arcane, Tags.Living]
	return hag

def IceLizard():

	liz = Unit()
	liz.max_hp = 11
	liz.name = "Ice Lizard"

	liz.spells.append(SimpleRangedAttack(damage=4, range=4, damage_type=Tags.Ice))

	liz.resists[Tags.Ice] = 75
	liz.resists[Tags.Fire] = -50

	liz.tags = [Tags.Living, Tags.Ice]

	return liz

def FireLizard():


	liz = Unit()
	liz.max_hp = 11
	liz.name = "Fire Lizard"

	liz.spells.append(SimpleRangedAttack(damage=4, range=4, damage_type=Tags.Fire))

	liz.resists[Tags.Fire] = 75
	liz.resists[Tags.Ice] = -50

	liz.tags = [Tags.Living, Tags.Fire]

	return liz

def Snake():

	snek = Unit()
	snek.name = "Snake"
	snek.max_hp = 9
	snek.spells.append(SimpleMeleeAttack(3, buff=Poison, buff_duration=5))

	snek.resists[Tags.Ice] = -50

	snek.tags = [Tags.Living, Tags.Nature]

	return snek

def Mantis():

	mantis = Unit()
	mantis.name = "Mantis"
	mantis.max_hp = 4

	mantis.spells.append(SimpleMeleeAttack(damage=3))
	mantis.spells.append(LeapAttack(damage=3, range=4))	

	mantis.tags = [Tags.Living]

	return mantis

def MetalMantis():

	mantis = Unit()
	mantis.name = "Metal Mantis"
	mantis.asset_name = "mantis_metal"
	mantis.max_hp = 12

	mantis.spells.append(SimpleMeleeAttack(damage=6))
	mantis.spells.append(LeapAttack(damage=6, range=4))	

	mantis.tags = [Tags.Construct, Tags.Metallic]

	return mantis

class RavenBlind(Spell):

	def on_init(self):
		self.name = "Mass Blindness"
		self.description = "Blind all enemies for 3 turns"
		self.cool_down = 12
		self.range = 0

	def cast(self, x, y):
		tiles = [t for t in self.caster.level.iter_tiles()]
		random.shuffle(tiles)
		tiles.sort(key=lambda u: distance(self.caster, u))

		for t in tiles:

			u = t.unit
			if u and are_hostile(self.caster, u):
				u.apply_buff(BlindBuff(), 3)

			elif random.random() < .25:
				self.caster.level.deal_damage(t.x, t.y, 0, Tags.Dark, self)

			if random.random() < .05:
				yield

class CarrionChannel(Spell):

	def on_init(self):
		self.name = "Carrion Channel"
		self.description = "Summons 2 fly swarms each turn.\nCan channel for 5 turns."
		self.cool_down = 15
		self.max_channel = 5
		self.minion_duration = 10
		self.range = 7
		self.num_summons = 2

	def get_ai_target(self):
		# cast it... vaguely near enemies
		return self.get_corner_target(6)

	def cast(self, x, y, channel_cast=False):
		if self.max_channel and not channel_cast:
			self.caster.apply_buff(ChannelBuff(self.cast, Point(x, y)), self.max_channel)
			return

		for i in range(self.num_summons):
			unit = FlyCloud()
			unit.turns_to_death = self.minion_duration
			self.summon(unit, Point(x, y), sort_dist=False)
			yield

def RavenMage():
	unit = Unit()
	unit.name = "Raven Mage"
	unit.asset_name = "raven_wizard"
	unit.max_hp = 46
	unit.shields = 2


	windride = MonsterTeleport()
	windride.cool_down = 18
	windride.requires_los = True
	windride.range = 20
	windride.name = "Ride the Wind"
	windride.description = "Teleports to a random tile in line of sight"


	ravens = SimpleSummon(Raven, num_summons=3, cool_down=13)
	blind = RavenBlind()
	flies = CarrionChannel()
	deathtouch = SimpleMeleeAttack(damage=23, damage_type=Tags.Dark)
	deathtouch.name = "Death Touch"

	unit.spells = [ravens, windride, blind, flies, deathtouch]

	unit.tags = [Tags.Living, Tags.Dark]

	return unit

def Raven():

	unit = Unit()
	unit.name = "Raven"
	unit.max_hp = 13
	unit.flying = True

	peck = SimpleMeleeAttack(damage=3, buff=BlindBuff, buff_duration=3)
	peck.name = 'Peck'
	unit.spells.append(peck)

	unit.resists[Tags.Dark] = 50

	unit.tags = [Tags.Living, Tags.Dark]

	return unit

class Hibernate(Spell):

	def on_init(self):
		self.name = "Hibernate"
		self.description = "Freezes self for 4 turns"
		self.duration = 4
		self.healing = 20

		self.cool_down = 9
		self.range = 0

	def can_cast(self, x, y):
		return self.caster.cur_hp <= self.caster.max_hp - 15 and Spell.can_cast(self, x, y)

	def cast_instant(self, x, y):
		self.caster.apply_buff(FrozenBuff(), self.get_stat('duration'))

class IcyMetabolism(Buff):

	def on_init(self):
		self.name = "Icy Metabolism"
		self.color = Tags.Ice.color
		self.heal = 10

	def get_tooltip(self):
		return "Heals %d HP per turn while frozen" % self.heal 

	def on_advance(self):
		if self.owner.has_buff(FrozenBuff):
			self.owner.deal_damage(-self.heal, Tags.Heal, self)


def PolarBear():

	unit = Unit()
	unit.name = "Polar Bear"
	unit.max_hp = 50

	unit.spells.append(Hibernate())
	unit.spells.append(SimpleMeleeAttack(12))

	unit.buffs.append(IcyMetabolism())

	unit.resists[Tags.Ice] = 50
	unit.resists[Tags.Fire] = -50

	unit.tags = [Tags.Ice, Tags.Living]

	return unit

def MindDevourer():

	unit = Unit()
	unit.name = "Mind Devourer"

	unit.shields = 2
	unit.max_hp = 42

	melee = SimpleMeleeAttack(8, damage_type=Tags.Arcane, onhit=drain_spell_charges)
	melee.name = "Brain Bite"
	melee.description = "On hit, drains a charge of a random spell"
	unit.spells.append(melee)

	pull = PullAttack(damage=3, range=6, color=Tags.Tongue.color)
	pull.name = "Tentacle"
	unit.spells.append(pull)

	unit.tags = [Tags.Arcane, Tags.Living]
	unit.resists[Tags.Arcane] = 100

	return unit

def GiantSkull():
	unit = Unit()
	
	unit.max_hp = 78

	unit.name = "Giant Floating Skull"
	unit.asset_name = "giant_skull"
	unit.stationary = True

	deathgaze = SimpleRangedAttack(damage=13, damage_type=Tags.Dark, range=14, beam=True)
	deathgaze.name = "Death Gaze"
	deathgaze.cool_down = 2

	unit.spells.append(deathgaze)

	unit.buffs.append(TeleportyBuff(chance=.1, radius=8))
	unit.resists[Tags.Dark] = 100
	unit.tags = [Tags.Undead, Tags.Dark]
	return unit

def GoldSkull():

	unit = GiantSkull()
	unit.name = "Golden Skull"
	unit.asset_name = "giant_skull_gilded"
	unit.shields = 2

	unit.tags.append(Tags.Holy)
	unit.tags.append(Tags.Metallic)

	holybeam = SimpleRangedAttack(damage=13, damage_type=Tags.Holy, range=14, beam=True)
	holybeam.name = "Wrath Gaze"
	holybeam.cool_down = 2
	
	heal = HealAlly(heal=13, range=14)
	heal.cool_down = 2

	unit.spells = [holybeam, heal]

	unit.resists[Tags.Dark] = 50
	unit.resists[Tags.Holy] = 50
	
	return unit

def PurpleHand():

	unit = Unit()
	unit.name = "Purple Hand"
	unit.asset_name = "giant_hand"

	unit.shields = 1
	unit.max_hp = 38

	melee = SimpleMeleeAttack(13, damage_type=Tags.Arcane)
	melee.onhit = lambda caster, target: randomly_teleport(target, 5)
	melee.name = "Void Flick"
	melee.description = "Randomly teleport the target up to 5 tiles away."

	unit.spells.append(melee)

	unit.tags = [Tags.Arcane]

	unit.resists[Tags.Arcane] = 75
	return unit

def BloodBear():

	unit = Unit()
	unit.name = "Blood Bear"
	unit.tags = [Tags.Nature, Tags.Demon]
	unit.resists[Tags.Dark] = 75
	unit.max_hp = 65

	melee = SimpleMeleeAttack(10)
	melee.onhit = bloodrage(3)
	melee.name = "Frenzy Claw"
	melee.description = "Gain +3 damage for 10 turns with each attack"

	unit.spells.append(melee)
	return unit

def Bloodghast():

	unit = Ghost()
	unit.name = "Bloodghast"
	unit.asset_name = "blood_ghost"
	unit.spells[0].name = "Frenzy Haunt"
	unit.spells[0].onhit = bloodrage(1)
	unit.spells[0].description = "Gain +2 damage for 10 turns with each attack"

	unit.tags.append(Tags.Demon)

	unit.resists[Tags.Poison] = 100
	unit.resists[Tags.Dark] = 75

	return unit

def Bloodhound():

	unit = Unit()

	unit.name = "Blood Hound"
	unit.asset_name = "blood_wolf"
	unit.max_hp = 19

	melee = SimpleMeleeAttack(6)
	melee.onhit = bloodrage(2)
	melee.name = "Frenzy Bite"
	melee.description = "Gain +2 damage for 10 turns with each attack"
	unit.spells.append(melee)

	unit.spells.append(LeapAttack(damage=6, damage_type=Tags.Physical, range=3))
	unit.tags = [Tags.Demon, Tags.Nature]
	unit.resists[Tags.Dark] = 75

	return unit

def Wolf():

	wolf = Unit()
	wolf.max_hp = 9
	
	wolf.sprite.char = 'w'
	wolf.sprite.color = Color(102, 77, 51)
	wolf.name = "Wolf"
	wolf.description = "A medium sized beast"
	wolf.spells.append(SimpleMeleeAttack(5))

	wolf.spells.append(LeapAttack(damage=5, damage_type=Tags.Physical, range=4))

	wolf.tags = [Tags.Living, Tags.Nature]

	return wolf

def OrcWolf():
	wolf = Wolf()
	wolf.max_hp += 3
	wolf.name = "Orc Wolf"
	return wolf

def LivingLightningScroll():

	unit = Unit()
	unit.name = "Living Scroll of Lightning"
	unit.asset_name = "living_lightning_scroll"

	bolt = SimpleRangedAttack(damage=6, range=10, damage_type=Tags.Lightning, beam=True)

	unit.spells.append(bolt)
	bolt.suicide = True

	unit.flying = True

	unit.max_hp = 5

	unit.resists[Tags.Arcane] = 100
	unit.resists[Tags.Lightning] = 100

	unit.tags = [Tags.Arcane, Tags.Lightning, Tags.Construct]

	return unit


def LivingFireballScroll():

	unit = Unit()
	unit.name = "Living Scroll of Fireball"
	unit.asset_name = "living_fireball_scroll"

	ball = SimpleRangedAttack(damage=6, range=7, damage_type=Tags.Fire, radius=2)
	
	unit.spells.append(ball)
	ball.suicide = True

	unit.flying = True

	unit.max_hp = 5

	unit.resists[Tags.Arcane] = 100
	unit.resists[Tags.Fire] = 100

	unit.tags = [Tags.Arcane, Tags.Fire, Tags.Construct]

	return unit

def FieryTormentor():

	unit = Unit()
	unit.name = "Fiery Tormentor"
	unit.asset_name = "wisp_flame"
	unit.max_hp = 34

	
	burst = SimpleBurst(damage=7, damage_type=Tags.Fire, cool_down=5, radius=4)
	burst.name = "Fiery Torment"

	unit.spells.append(burst)
	lifedrain = SimpleRangedAttack(damage=2, range=2, damage_type=Tags.Dark, drain=True)
	lifedrain.name = "Soul Suck"
	unit.spells.append(lifedrain)

	unit.tags = [Tags.Fire, Tags.Demon]
	unit.resists[Tags.Dark] = 100
	unit.resists[Tags.Fire] = 100
	unit.resists[Tags.Ice] = -50
	return unit

def FrostfireTormentor():

	unit = Unit()
	unit.name = "Frostfire Tormentor"
	unit.asset_name = "tormentor_frostfire"
	unit.max_hp = 56

	burst = SimpleBurst(damage=7, damage_type=Tags.Fire, cool_down=5, radius=4)
	burst.name = "Fiery Torment"

	unit.spells.append(burst)

	def freeze(caster, target):
		target.apply_buff(FrozenBuff(), 1)

	burst = SimpleBurst(damage=7, damage_type=Tags.Ice, cool_down=5, radius=4, onhit=freeze, extra_desc="Applies 2 turns of freeze")
	burst.name = "Frosty Torment"

	unit.spells.append(burst)

	lifedrain = SimpleRangedAttack(damage=2, range=2, damage_type=Tags.Dark, drain=True)
	lifedrain.name = "Soul Suck"
	unit.spells.append(lifedrain)

	unit.tags = [Tags.Fire, Tags.Ice, Tags.Demon]
	unit.resists[Tags.Dark] = 100
	unit.resists[Tags.Fire] = 100
	unit.resists[Tags.Ice] = 100
	return unit

def GhostfireTormentor():

	unit = Unit()
	unit.name = "Ghostfire Tormentor"
	unit.asset_name = "tormentor_ghostfire"
	unit.max_hp = 56

	def freeze(caster, target):
		target.apply_buff(FrozenBuff(), 1)

	burst = SimpleBurst(damage=7, damage_type=Tags.Dark, cool_down=5, ignore_walls=True, radius=4)
	burst.name = "Dark Torment"

	unit.spells.append(burst)

	burst = SimpleBurst(damage=7, damage_type=Tags.Fire, cool_down=5, radius=4)
	burst.name = "Fiery Torment"

	unit.spells.append(burst)

	lifedrain = SimpleRangedAttack(damage=2, range=2, damage_type=Tags.Dark, drain=True)
	lifedrain.name = "Soul Suck"
	unit.spells.append(lifedrain)

	unit.tags = [Tags.Fire, Tags.Dark, Tags.Demon]
	unit.resists[Tags.Dark] = 100
	unit.resists[Tags.Fire] = 100
	unit.resists[Tags.Ice] = -50
	return unit

def DarkTormentor():

	unit = Unit()
	unit.name = "Dark Tormentor"
	unit.asset_name = "wisp_dark"
	unit.max_hp = 34

	burst = SimpleBurst(damage=7, damage_type=Tags.Dark, cool_down=5, ignore_walls=True, radius=4)
	burst.name = "Dark Torment"

	unit.spells.append(burst)
	lifedrain = SimpleRangedAttack(damage=2, range=2, damage_type=Tags.Dark, drain=True)
	lifedrain.name = "Soul Suck"
	unit.spells.append(lifedrain)

	unit.tags = [Tags.Dark, Tags.Demon]
	unit.resists[Tags.Dark] = 100
	return unit

def IcyTormentor():

	unit = Unit()
	unit.name = "Frosty Tormentor"
	unit.asset_name = "wisp_frost"
	unit.max_hp = 34

	def freeze(caster, target):
		target.apply_buff(FrozenBuff(), 1)

	burst = SimpleBurst(damage=7, damage_type=Tags.Ice, cool_down=5, radius=4, onhit=freeze)
	burst.description = "Applies frozen for 1 turn"
	burst.name = "Frosty Torment"

	unit.spells.append(burst)
	lifedrain = SimpleRangedAttack(damage=2, range=2, damage_type=Tags.Dark, drain=True)
	lifedrain.name = "Soul Suck"
	unit.spells.append(lifedrain)

	unit.tags = [Tags.Ice, Tags.Demon]
	unit.resists[Tags.Dark] = 100
	unit.resists[Tags.Ice] = 100
	unit.resists[Tags.Fire] = -50
	return unit

def Yeti():

	unit = Unit()

	unit.name = "Yeti"
	unit.max_hp = 75

	unit.spells.append(SimpleMeleeAttack(14))
	unit.buffs.append(DamageAuraBuff(damage=1, damage_type=Tags.Ice, radius=4, friendly_fire=False))


	unit.resists[Tags.Ice] = 100
	unit.resists[Tags.Fire] = -50

	unit.tags = [Tags.Ice, Tags.Living]

	return unit




class GoatHeadBray(Spell):

	def on_init(self):
		self.name = "Horrid Braying"
		self.description = "Increase the damage of an allied unit by 4"
		self.duration = 6
		self.range = 5
		self.cool_down = 3

	def get_ai_target(self):
		options = [u for u in self.caster.level.get_units_in_ball(self.caster, self.get_stat('range')) if not are_hostile(self.caster, u) and self.can_cast(u.x, u.y)]

		if options:
			return random.choice(options)

	def cast_instant(self, x, y):
		unit = self.caster.level.get_unit_at(x, y)

		if unit:
			unit.apply_buff(BloodrageBuff(4), self.get_stat('duration'))

def GoatHead():

	unit = Unit()

	unit.name = "Goatia"
	unit.asset_name = "floating_goat_head"
	unit.max_hp = 17

	unit.stationary = True
	unit.flying = True

	unit.spells = [GoatHeadBray(), SimpleMeleeAttack(5)]
	unit.buffs.append(TeleportyBuff(chance=.1, radius=8))
	unit.buffs.append(DeathExplosion(damage=7, radius=1, damage_type=Tags.Dark))
	unit.tags = [Tags.Demon, Tags.Nature]
	
	unit.resists[Tags.Dark] = 50

	return unit

def RedLion():

	unit = Unit()
	unit.max_hp = 20

	unit.name = "Fire Lion"
	unit.asset_name = "chaos_lion"

	unit.resists[Tags.Fire] = 100

	fire = SimpleRangedAttack(damage=5, range=5, damage_type=Tags.Fire, cool_down=2)
	fire.name = "Fire"
	melee = SimpleMeleeAttack(6)
	unit.spells = [fire, melee]

	unit.tags = [Tags.Fire, Tags.Living]

	return unit

def GoldenSnake():

	unit = Unit()
	unit.max_hp = 9
	unit.name = "Lightning Snake"
	unit.asset_name = "chaos_snake"

	unit.resists[Tags.Lightning] = 100

	spark = SimpleRangedAttack(damage=5, range=5, damage_type=Tags.Lightning, cool_down=2)
	spark.name = "Lightning"
	melee = SimpleMeleeAttack(4, buff=Poison, buff_duration=10)
	unit.spells = [spark, melee]

	unit.tags = [Tags.Lightning, Tags.Living]
	return unit

def ChaosChimera():

	unit = Unit()
	unit.max_hp = 26

	unit.resists[Tags.Fire] = 75
	unit.resists[Tags.Lightning] = 75

	unit.name = "Chaos Chimera"

	fire = SimpleRangedAttack(damage=5, range=5, damage_type=Tags.Fire, cool_down=2)
	fire.name = "Fire"
	spark = SimpleRangedAttack(damage=5, range=5, damage_type=Tags.Lightning, cool_down=2)
	spark.name = "Lightning"
	unit.spells = [fire, spark]
	unit.tags = [Tags.Fire, Tags.Lightning, Tags.Living]

	unit.buffs.append(RespawnAs(RedLion))
	unit.buffs.append(RespawnAs(GoldenSnake))

	return unit

def IceLion():

	unit = Unit()
	unit.max_hp = 20

	unit.name = "Ice Lion"
	unit.asset_name = "deathchill_lion"

	unit.resists[Tags.Ice] = 100

	ice = SimpleRangedAttack(damage=5, beam=True, range=5, damage_type=Tags.Ice, cool_down=2)
	ice.name = "Ice"
	melee = SimpleMeleeAttack(6)
	melee.name = "Claw"
	unit.spells = [ice, melee]

	unit.tags = [Tags.Ice, Tags.Living]

	return unit

def DeathSnake():

	unit = Unit()
	unit.max_hp = 9
	unit.name = "Death Snake"
	unit.asset_name = "deathchill_snake"

	unit.resists[Tags.Dark] = 100

	spark = SimpleRangedAttack(damage=5, beam=True, range=5, damage_type=Tags.Dark, cool_down=2)
	spark.name = "Darkness"
	melee = SimpleMeleeAttack(4, buff=Poison, buff_duration=10)
	melee.name = "Bite"
	unit.spells = [spark, melee]

	unit.tags = [Tags.Dark, Tags.Living]
	return unit

def DeathchillChimera():

	unit = Unit()
	unit.max_hp = 26

	unit.resists[Tags.Dark] = 75
	unit.resists[Tags.Ice] = 75

	unit.name = "Deathchill Chimera"

	fire = SimpleRangedAttack(damage=5, beam=True, range=5, damage_type=Tags.Ice, cool_down=2)
	fire.name = "Ice"
	spark = SimpleRangedAttack(damage=5, beam=True, range=5, damage_type=Tags.Dark, cool_down=2)
	spark.name = "Darkness"
	unit.spells = [fire, spark]
	unit.tags = [Tags.Dark, Tags.Ice, Tags.Living]

	unit.buffs.append(RespawnAs(IceLion))
	unit.buffs.append(RespawnAs(DeathSnake))

	return unit

def StarLion():

	unit = Unit()
	unit.max_hp = 20

	unit.name = "Star Lion"
	unit.asset_name = "starfire_lion"

	unit.resists[Tags.Arcane] = 100

	void = SimpleRangedAttack(damage=5, beam=True, range=5, melt=True, damage_type=Tags.Arcane, cool_down=2)
	void.name = "Void"
	melee = SimpleMeleeAttack(6)
	melee.name = "Claw"
	unit.spells = [void, melee]

	unit.tags = [Tags.Arcane, Tags.Living]

	return unit

def FireSnake():

	unit = Unit()
	unit.max_hp = 9
	unit.name = "Fire Snake"
	unit.asset_name = "starfire_snake"

	unit.resists[Tags.Fire] = 100

	fire = SimpleRangedAttack(damage=5, radius=2, range=5, damage_type=Tags.Fire, cool_down=2)
	fire.name = "Fire"
	melee = SimpleMeleeAttack(4, buff=Poison, buff_duration=10)
	melee.name = "Bite"
	unit.spells = [fire, melee]

	unit.tags = [Tags.Fire, Tags.Living]
	return unit

def StarfireChimera():

	unit = Unit()
	unit.max_hp = 26

	unit.resists[Tags.Fire] = 75
	unit.resists[Tags.Arcane] = 75

	unit.name = "Starfire Chimera"

	fire = SimpleRangedAttack(damage=5, range=5, radius=2, damage_type=Tags.Fire, cool_down=2)
	fire.name = "Fire"
	void = SimpleRangedAttack(damage=5, beam=True, range=5, melt=True, damage_type=Tags.Arcane, cool_down=2)
	void.name = "Void"
	unit.spells = [fire, void]
	unit.tags = [Tags.Arcane, Tags.Fire, Tags.Living]

	unit.buffs.append(RespawnAs(StarLion))
	unit.buffs.append(RespawnAs(FireSnake))

	return unit

class BeginConstructingSiege(Spell):

	def __init__(self, siegespawn):
		self.siegespawn = siegespawn
		self.siege_name = siegespawn().name
		Spell.__init__(self)
		

	def on_init(self):
		self.range = 5
		self.must_target_empty = True
		self.must_target_walkable = True
		self.cool_down = 30

		self.name = "Construct %s" % self.siegespawn().name
		self.description = "Begins construction of a %s." % self.siegespawn().name

	def cast_instant(self, x, y):
		unit = self.siegespawn()
		unit.cur_hp = unit.max_hp // 4
		
		for s in unit.spells:
			s.siege = True

		self.summon(unit, target=Point(x, y))

	def get_ai_target(self):
		# Do not cast if already adjacent to the target
		adj_points = self.caster.level.get_points_in_ball(self.caster.x, self.caster.y, 2, diag=True)
		for p in adj_points:
			unit = self.caster.level.get_unit_at(p.x, p.y)
			if unit and unit.name == self.siege_name and not are_hostile(self.caster, unit):
				return None

		#place in the openest area within range
		options = [p for p in self.caster.level.get_points_in_ball(self.caster.x, self.caster.y, 2) if self.can_cast(p.x, p.y)]

		# must be able to walk there
		options = [p for p in options if self.caster.level.find_path(self.caster, p, self.caster)]

		if options:
			return random.choice(options)
		else:
			return None

	def can_threaten(self, x, y):
		return False

class Approach(Spell):

	def __init__(self, target_name):
		self.target_name = target_name
		Spell.__init__(self)

	def on_init(self):
		# By default, only approach things up to 8 tiles away
		self.range = 8
		# By default, only approach things in los
		self.requires_los = False
		self.name = "Wander"
		self.description = "Walk towards a nearby %s" % self.target_name
		self.animate = False

	def can_cast(self, x, y):
		path = self.caster.level.find_path(self.caster, Point(x, y), self.caster, pythonize=True)
		if not path:
			return False
		if len(path) > self.range:
			return False
		return Spell.can_cast(self, x, y)

	def can_threaten(self, x, y):
		return False

	def get_ai_target(self):
		potentials = [u for u in self.caster.level.units if not are_hostile(u, self.caster) and u.name == self.target_name]

		# Filter LOS, range
		potentials = [u for u in potentials if self.can_cast(u.x, u.y)]

		if not potentials:
			return None

		# Always return closest to prevent thrashing
		potentials.sort(key = lambda u: distance(u, self.caster))

		# choose a random adjacent point to the target
		target = potentials[0]
		return target


	def cast_instant(self, x, y):
		adj_points = self.caster.level.get_points_in_ball(x, y, 1, diag=True)
		target_point = random.choice(list(adj_points))
		path = self.caster.level.find_path(self.caster, target_point, self.caster, pythonize=True)
		if not path:
			return

		p = path[0]
		if self.caster.level.can_move(self.caster, p.x, p.y):
			self.caster.level.act_move(self.caster, p.x, p.y)

class OperateSiege(Spell):

	def __init__(self, siege_name):
		self.siege_name = siege_name
		Spell.__init__(self)

	
	def on_init(self):
		self.name = "Operate %s" % self.siege_name
		self.melee = True
		self.range = 1
		self.heal = 2
		self.description = "Activate's a %s" % self.siege_name
		
	def get_ai_target(self):
		potentials = [u for u in self.caster.level.units if not are_hostile(u, self.caster) and u.name == self.siege_name]

		# Not max hp
		potentials = [u for u in potentials if u.cur_hp >= u.max_hp]

		# Filter LOS, range
		potentials = [u for u in potentials if self.can_cast(u.x, u.y)]

		# Filter by fireable
		potentials = [u for u in potentials if any(s for s in u.spells if s.can_pay_costs() and s.get_ai_target())]

		if not potentials:
			return None
		return random.choice(potentials)

	def cast_instant(self, x, y):
		unit = self.caster.level.get_unit_at(x, y)
		spell = unit.spells[0]
		target = spell.get_ai_target()
		if target:
			self.caster.level.act_cast(unit, spell, target.x, target.y)

class RepairSiege(Spell):

	def __init__(self, siege_name):
		self.siege_name = siege_name
		Spell.__init__(self)
		

	def on_init(self):
		self.name = "Repair %s" % self.siege_name
		self.melee = True
		self.range = 1
		self.heal = 1
		self.description = "Repair %d damage to a %s" % (self.heal, self.siege_name)
		

	def get_ai_target(self):
		potentials = [u for u in self.caster.level.units if not are_hostile(u, self.caster) and u.name == self.siege_name]

		# Not max hp
		potentials = [u for u in potentials if u.cur_hp < u.max_hp]

		# Filter LOS, range
		potentials = [u for u in potentials if self.can_cast(u.x, u.y)]
		if not potentials:
			return None
		return random.choice(potentials)

	def cast_instant(self, x, y):
		unit = self.caster.level.get_unit_at(x, y)
		if unit:
			unit.deal_damage(-self.heal, Tags.Heal, self)

		
		possible_positions = self.caster.level.get_points_in_ball(self.caster.x, self.caster.y, 1, diag=True)
		opts = [p for p in possible_positions if self.caster.level.can_move(self.caster, p.x, p.y)]
		opts = [p for p in opts if distance(p, unit, diag=True) == 1]

		if not opts:
			return

		# move unit around maybe
		if random.random() < 1 / len(opts):
			return

		p = random.choice(opts)
		self.caster.level.act_move(self.caster, p.x, p.y)


class ReloadSiege(Spell):
	def __init__(self, siege_name):
		self.siege_name = siege_name
		Spell.__init__(self)
		

	def on_init(self):
		self.name = "Resupply %s" % self.siege_name
		self.melee = True
		self.description = "Reduce cooldown of a %s by 1 turn" % self.siege_name
		self.heal = 1
		self.cool_down = 3
		self.range = 1

	def get_ai_target(self):
		potentials = [u for u in self.caster.level.units if not are_hostile(u, self.caster) and u.name == self.siege_name]

		# Filter LOS, range
		potentials = [u for u in potentials if self.can_cast(u.x, u.y)]

		# Filter by ability on cd
		potentials = [u for u in potentials if any(u.cool_downs.get(s, 0) > 0 for s in u.spells)]

		if not potentials:
			return None
		return random.choice(potentials)

	def cast_instant(self, x, y):
		unit = self.caster.level.get_unit_at(x, y)
		if unit:
			for s in unit.cool_downs:
				if unit.cool_downs[s] <= 0:
					continue
				unit.cool_downs[s] -= 1


def SiegeOperator(siegespawn):
	unit = Unit()
	example_siege = siegespawn()
	for s in example_siege.spells:
		s.siege = True
		
	unit.spells = [OperateSiege(example_siege.name),
				   RepairSiege(example_siege.name),
				   Approach(example_siege.name),
				   BeginConstructingSiege(siegespawn)]
	return unit

class WizardTeleport(Spell):

	def on_init(self):
		self.range = 0
		self.name = "Void Tango"
		self.cool_down = 11
		self.requires_los = False
		self.description = "Mordred teleports to a random tile.\nThe Wizard is teleported to Mordred's old location."

	def cast(self, x, y):
		old_loc = Point(self.caster.x, self.caster.y)
		choices = [t for t in self.caster.level.iter_tiles() if t.can_walk and not t.unit]
		
		if choices:
			target = random.choice(choices)
			for p in self.caster.level.get_points_in_line(self.caster, target):
				self.caster.level.leap_effect(p.x, p.y, Color(216, 27, 96), self.caster)
				yield
			self.caster.level.act_move(self.caster, target.x, target.y, teleport=True)

		
		for p in self.caster.level.get_points_in_line(self.caster.level.player_unit, old_loc):
			self.caster.level.leap_effect(p.x, p.y, Color(2, 136, 209), self.caster.level.player_unit)
			yield

		if self.caster.level.can_move(self.caster.level.player_unit, old_loc.x, old_loc.y, teleport=True):
			self.caster.level.act_move(self.caster.level.player_unit, old_loc.x, old_loc.y, teleport=True)

class MordredCorruption(Spell):

	def on_init(self):
		self.name = "Planar Interposition"
		self.description = "Mix the current realm with another.\nFriends and foes may be left behind, Mordred and the Wizard will always remain."
		self.cool_down = 13
		self.range = 0
		self.num_exits = 0
		self.forced_difficulty = None

	def cast(self, x, y):

		gen_params = self.caster.level.gen_params.make_child_generator(difficulty=self.forced_difficulty or self.caster.level.level_no)		
		gen_params.num_exits = self.num_exits
		gen_params.num_monsters = 25
		new_level = gen_params.make_level()

		# For the new level, pick some swaths of it.
		# For each tile in that swath, transport the tile and its contents to the new level
		# For units, remove then add them to make event subscriptions work...?
		chance = random.random() * .5 + .1
		targets = []

		num_portals = len(list(t for t in self.caster.level.iter_tiles() if isinstance(t.prop, Portal)))

		for i in range(len(new_level.tiles)):
			for j in range(len(new_level.tiles)):
				if random.random() > chance:
					if isinstance(self.caster.level.tiles[i][j].prop, Portal):
						if num_portals <= 1:
							continue
						else:
							num_portals -= 1
					targets.append((i, j))
		random.shuffle(targets)

		for i, j in targets:
			
			old_unit = self.caster.level.get_unit_at(i, j)
			if old_unit and (old_unit == self.caster or old_unit.is_player_controlled or old_unit.name == "Mordred"):
				continue
			elif old_unit:
				old_unit.kill(trigger_death_event=False)

			new_tile = new_level.tiles[i][j]

			calc_glyph = random.choice([True, True, False])
			if new_tile.is_chasm:
				self.caster.level.make_chasm(i, j, calc_glyph=calc_glyph)
			elif new_tile.is_floor():
				self.caster.level.make_floor(i, j, calc_glyph=calc_glyph)
			else:
				self.caster.level.make_wall(i, j, calc_glyph=calc_glyph)
			
			cur_tile = self.caster.level.tiles[i][j]				
			cur_tile.tileset = new_tile.tileset
			cur_tile.water = new_tile.water
			cur_tile.sprites = None

			unit = new_tile.unit
			if unit:
				new_level.remove_obj(unit)
			if unit and not cur_tile.unit:
				self.caster.level.add_obj(unit, i, j)

			prop = new_tile.prop
			if prop:
				old_prop = cur_tile.prop
				if old_prop:
					self.caster.level.remove_prop(old_prop)
				self.caster.level.add_prop(prop, i, j)

			# Remove props from chasms and walls
			if cur_tile.prop and not cur_tile.is_floor():
				self.caster.level.remove_prop(cur_tile.prop)

			self.caster.level.show_effect(i, j, Tags.Translocation)
			if random.random() < .25:
				yield
		yield

def Mordred():
	unit = Unit()
	unit.name = "Mordred"
	unit.sprite.color = Color(255, 50, 150)
	unit.sprite.char = 'M'

	unit.shields = 7
	unit.gets_clarity = True

	teleport = WizardTeleport()
	
	beam = MonsterVoidBeam()
	beam.cool_down = 3
	beam.range = 30
	beam.name = "Mordred's Gaze"
	
	touch = SimpleMeleeAttack(damage=200, damage_type=Tags.Dark)
	touch.name = "Mordred's Touch"

	corruption = MordredCorruption()
	corruption.forced_difficulty = 19
	unit.spells.append(corruption)
	
	unit.spells.append(teleport)
	unit.spells.append(touch)
	unit.spells.append(beam)
	
	unit.buffs.append(ReincarnationBuff(4))

	unit.max_hp = 697
	unit.resists[Tags.Dark] = 50
	unit.resists[Tags.Poison] = 0
	return unit


class GlassyGaze(Spell):

	def __init__(self):
		Spell.__init__(self)
		self.name = "Glassy Gaze"
		self.range = 12
		self.cool_down = 10
		self.duration = 3

	def cast(self, x, y):
		start = Point(self.caster.x, self.caster.y)
		target = Point(x, y)

		for point in Bolt(self.caster.level, start, target):
			self.caster.level.flash(point.x, point.y, Tags.Glassification.color)
			yield

		unit = self.caster.level.get_unit_at(x, y)
		unit.apply_buff(GlassPetrifyBuff(), self.duration)
		yield

	def get_description(self):
		return "Turns victim to glass for %d turns" % self.duration

def GlassButterfly():
	demon = ButterflyDemon()
	demon.name = "Glass Butterfly"
	demon.sprite.char = 'B'
	demon.sprite.color = Tags.Arcane.color
	demon.shields = 16
	demon.tags.append(Tags.Glass)
	return demon

def GlassGolem():
	golem = Golem()
	golem.name = "Glass Golem"
	golem.shields = 2
	golem.tags.append(Tags.Glass)
	golem.resists[Tags.Physical] = -100
	return golem

def GlassCockatrice():
	cockatrice = Cockatrice()
	cockatrice.name = "Glass Cockatrice"
	cockatrice.tags.append(Tags.Glass)
	cockatrice.spells[1] = GlassyGaze()
	cockatrice.shields = 2
	return cockatrice

def GiantFlamingSkull():
	unit = GiantSkull()
	
	unit.name = "Giant Flaming Skull"
	unit.asset_name = "giant_flaming_skull"
	
	fireball = SimpleRangedAttack(damage=25, damage_type=Tags.Fire, range=7, radius=4)
	fireball.name = "Giant Fireball"
	fireball.cool_down = 4

	unit.spells.append(fireball)

	unit.resists[Tags.Fire] = 100
	unit.tags.append(Tags.Fire)
	return unit

class PhoenixBuff(Buff):
	
	def on_init(self):
		self.color = Tags.Fire.color
		self.owner_triggers[EventOnDeath] = self.on_death
		self.name = "Phoenix Fire"

	def get_tooltip(self):
		return "On death, deals 25 fire damage to all tiles within 6.  Friendly units are healed instead of damaged."

	def on_death(self, evt):

		for p in self.owner.level.get_points_in_ball(self.owner.x, self.owner.y, 6):
			unit = self.owner.level.get_unit_at(*p)
			if unit and not are_hostile(unit, self.owner):
				unit.deal_damage(-25, Tags.Heal, self)
			else:
				self.owner.level.deal_damage(p.x, p.y, 25, Tags.Fire, self)

def Phoenix():

	phoenix = Unit()
	phoenix.max_hp = 250
	phoenix.name = "Phoenix"

	phoenix.tags = [Tags.Fire, Tags.Holy]

	phoenix.sprite.char = 'P'
	phoenix.sprite.color = Tags.Fire.color

	phoenix.buffs.append(PhoenixBuff())
	phoenix.buffs.append(ReincarnationBuff(1))

	phoenix.flying = True

	phoenix.resists[Tags.Fire] = 100
	phoenix.resists[Tags.Dark] = -50

	phoenix.spells.append(SimpleRangedAttack(damage=9, range=4, damage_type=Tags.Fire))
	return phoenix	

class VolcanoTurtleBuff(Buff):

	def on_init(self):
		self.description = ("Spews 3 meteors each turn at random locations within a radius of 6.\n\n"
						    "The meteors create explosions with 2 tiles radii, dealing 8 fire damage.\n\n"
						    "Tiles directly hit take 11 additional physical damage and become floor tiles.\n\n"
						    "Enemies directly hit are stunned for 1 turn.")
		self.name = "Volcano Shell"

	def on_advance(self):

		possible_points = [p for p in self.owner.level.get_points_in_ball(self.owner.x, self.owner.y, 6) if distance(p, self.owner) > 1]
		for i in range(3):
			p = random.choice(possible_points)

			self.owner.level.queue_spell(self.meteor(p))

	def meteor(self, target):

		self.owner.level.make_floor(target.x, target.y)
		self.owner.level.deal_damage(target.x, target.y, 11, Tags.Physical, self)
		unit = self.owner.level.get_unit_at(target.x, target.y)
		if unit:
			unit.apply_buff(Stun(), 1)

		self.owner.level.show_effect(0, 0, Tags.Sound_Effect, 'hit_enemy')
		yield

		for stage in Burst(self.owner.level, target, 2):
			for point in stage:
				damage = 8
				self.owner.level.deal_damage(point.x, point.y, damage, Tags.Fire, self)
		yield

def VolcanoTurtle():
	unit = Unit()

	unit.name = "Volcano Turtle"

	unit.sprite.char = 'T'
	unit.sprite.color = Tags.Fire.color

	unit.max_hp = 95

	unit.resists[Tags.Fire] = 100

	unit.buffs.append(TurtleBuff())
	unit.buffs.append(VolcanoTurtleBuff())

	unit.spells.append(SimpleMeleeAttack(damage=20))
	unit.tags = [Tags.Nature, Tags.Fire, Tags.Demon]
	return unit

def Titan():
	unit = Unit()
	unit.name = "Titan"

	unit.max_hp = 244

	unit.resists[Tags.Fire] = 100
	unit.resists[Tags.Holy] = 75
	unit.resists[Tags.Dark] = 75

	fire = SimpleRangedAttack(damage=19, damage_type=Tags.Fire, range=7, radius=3, cool_down=4)
	melee = SimpleMeleeAttack(damage=35)

	unit.spells = [melee, fire]

	unit.tags = [Tags.Fire, Tags.Living, Tags.Holy]
	return unit

def Aesir():
	unit = Unit()
	unit.name = "Aesir"
	unit.max_hp = 121
	unit.shields = 3

	unit.resists[Tags.Lightning] = 100
	unit.resists[Tags.Holy] = 75
	unit.resists[Tags.Dark] = 75

	lightning = SimpleRangedAttack(damage=22, damage_type=Tags.Lightning, range=12, beam=True, cool_down=4)
	melee = SimpleMeleeAttack(29)

	unit.spells = [melee, lightning]

	unit.tags = [Tags.Lightning, Tags.Living, Tags.Holy]
	return unit

def FleshFiend():
	unit = Unit()
	unit.name = "Fleshy Mass"
	unit.max_hp = 431

	unit.buffs.append(RegenBuff(21))
	unit.spells.append(SimpleMeleeAttack(19))
	unit.tags = [Tags.Demon, Tags.Living]

	unit.resists[Tags.Physical] = -50

	return unit

def Reaper():
	unit = Unit()
	unit.name = "Reaper"
	unit.max_hp = 31
	unit.shields = 2
	unit.resists[Tags.Physical] = 100
	unit.resists[Tags.Dark] = 100


	touch = SimpleMeleeAttack(damage=200, damage_type=Tags.Dark)
	touch.name = "Death Touch"
	unit.flying = True
	unit.buffs.append(TeleportyBuff())

	unit.spells = [touch]

	unit.tags = [Tags.Undead, Tags.Dark]

	return unit

def FloatingEyeMass():
	unit = FloatingEye()
	unit.name = "Mass of Eyes"
	unit.asset_name = "floating_eyeball_mass"
	unit.max_hp += 17
	unit.shields += 1
	unit.spells[0].radius = 2
	unit.spells[0].damage = 4
	unit.buffs.append(SpawnOnDeath(FloatingEye, 6))
	return unit

def GargoyleStatue():
	unit = Unit()
	unit.name = "Gargoyle Statue"
	unit.max_hp = 30
	unit.tags = [Tags.Metallic, Tags.Construct, Tags.Dark]
	unit.buffs.append(MatureInto(Gargoyle, 10))
	unit.resists[Tags.Dark] = 75
	unit.resists[Tags.Holy] = -50
	unit.stationary = True
	return unit

def Gargoyle():
	unit = Unit()
	unit.name = "Gargoyle"
	unit.flying = True
	unit.tags = [Tags.Metallic, Tags.Construct, Tags.Dark]
	unit.spells.append(SimpleMeleeAttack(12))
	unit.buffs.append(RespawnAs(GargoyleStatue))
	unit.max_hp = 40
	unit.resists[Tags.Dark] = 75
	unit.resists[Tags.Holy] = -50
	return unit



spawn_options = [
	(Goblin, 1),
	(Bat, 1),
	(VoidBomber, 2),
	(FireBomber, 2),
	(FireImp, 2),
	(SparkImp, 2),
	(Ghost, 2),
	(MindMaggot, 2),
	(DisplacerBeast, 2),
	(GreenMushboom, 2),
	(Mantis, 2),
	(Snake, 2),
	(Spriggan, 2),
	(Boggart, 2),
	(IronImp, 3),
	(Satyr, 3),
	(WormBall, 3),
	(Kobold, 3),
	(Witch, 3),
	(Orc, 3),
	(GiantSpider, 3),
	(IceLizard, 3),
	(FireLizard, 3),
	(GreyMushboom, 3),
	(HornedToad, 3),
	(Raven, 3),
	(GoatHead, 3),
	(Centaur, 4),
	(Ogre, 4),
	(SporeBeast, 4),
	(BagOfBugs, 4),
	#(Slime, 4),
	(Troll, 4),
	(Troubler, 4),
	(EvilFairy, 4),
	(Vampire, 4),
	(Gnome, 4),
	(SteelSpider, 4),
	(MetalMantis, 4),
	(GreenSlime, 4),
	(Bloodghast, 4),
	(PolarBear, 4),
	(HellHound, 4),
	(Cultist, 4),
	(Werewolf, 4),
	(BlizzardBeast, 4),
	(ChaosChimera, 5),
	(Thunderbird, 5),
	(BoneKnight, 5),
	(Bloodhound, 5),
	(SparkSpirit, 5),
	(FireSpirit, 5),
	(Golem, 5),
	(Redcap, 5),
	(GreenGorgon, 5),
	(EarthTroll, 5),
	(OrcFireShaman, 5),
	(PhaseSpider, 5),
	(SpikeBeast, 5),
	(OldWitch, 5),
	(RedSlime, 5),
	(IceSlime, 5),
	(BloodBear, 5),
	(LivingLightningScroll, 5),
	(LivingFireballScroll, 5),
	(Dwarf, 5),
	(FieryTormentor, 5),
	(DarkTormentor, 5),
	(VoidSpawner, 6),
	(FireSpawner, 6),
	(SpikeBall, 6),
	#(Necromancer, 6),
	(FloatingEye, 6),
	(StormDrake, 6),
	(FireDrake, 6),
	(BoneShambler, 6),
	(WormShambler, 6),
	(GreaterSporeBeast, 6),
	(DisplacerBeastMother, 6),
	(MindMaggotQueen, 6),
	(FlameToad, 6),
	(VoidToad, 6),
	(StormTroll, 6),
	(Minotaur, 6),
	(GreaterVampire, 6),
	(Elf, 6),
	(GhostMass, 6),
	(FaeArcanist, 6),
	(PurpleHand, 6),
	(GiantToad, 6),
	(DeathchillChimera, 6),
	(GlassGolem, 6),
	(StarfireChimera, 7),
	(MindVampire, 7),
	(FalseProphet, 7),
	(MindDevourer, 7),
	(FireWyrm, 7),
	(Gargoyle, 7),
	(VoidSlime, 7),
	(NightHag, 7),
	(Cyclops, 7),
	(GiantSkull, 7),
	(GreyGorgon, 7),
	(Efreet, 7),
	(Yeti, 7),
	(VoidDrake, 7),
	(Cockatrice, 7),
	(ButterflyDemon, 7),
	(ChaosKnight, 7),
	(GoldDrake, 7),
	(FlamingEye, 7),
	(IcyTormentor, 7),
	(lambda : QueenMonster(GiantSpider), 7),
	(VoidHag, 8),
	(IceDrake, 8),
	(IceWyrm, 8),
	(RedFiend, 8),
	(YellowFiend, 8),
	(IronFiend, 8),
	(Lich, 8),
	(ElfLightningLord, 8),
	(ThornQueen, 8),
	(ToweringBoneShambler, 8),
	(VoidKnight, 8),
	(StormKnight, 8),
	(NightmareTurtle, 8),
	(Lamasu, 8),
	(GlassCockatrice, 8),
	(GlassButterfly, 9),
	(GiantFlamingSkull, 9),
	(Phoenix, 9),
	(lambda : QueenMonster(SteelSpider), 9),
	(lambda : QueenMonster(PhaseSpider), 9),
	(VolcanoTurtle, 9),
	(Dracolich, 9),
	(Aesir, 9),
	(Titan, 9),
	(Reaper, 9),
	(FloatingEyeMass, 9),
	(FleshFiend, 9),
	(ChaosFiend, 9),
	(CopperFiend, 9),
	(FurnaceFiend, 9),
	(InsanityFiend, 9),
	(RotFiend, 9),
	(AshFiend, 9),
	(BoneShamblerMegalith, 9),
	(GoldSkull, 9),
	(EnergyKnight, 9),
	(TwilightKnight, 9)
]


monster_tags = set()

# Counts by level
#for i in range(9):
#	count = len([1 for (s, l) in spawn_options if l == i])
#	print(i, count)

for o in spawn_options:
	if not o[0]():
		print(o)
	assert(o[0]())
	assert(o[0]().tags)
	for t in o[0]().tags:
		monster_tags.add(t)

def BossMonster(spawn_func):
	unit = spawn_func()
	unit.max_hp *= 6
	unit.shields *= 2

	for spell in unit.spells:
		if hasattr(spell, 'damage'):
			spell.damage *= 2
			spell.damage += 5

	unit.name = "Boss %s" % unit.name
	unit.is_boss = True
	return unit
