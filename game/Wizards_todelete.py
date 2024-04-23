from Spells import *

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
		
		self.caster.level.deal_damage(x, y, self.get_stat('damage'), self.element)
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
				self.caster.level.deal_damage(p.x, p.y, self.damage, Tags.Lightning)
				unit.apply_buff(BlindBuff(), 1)
				yield
			elif random.random() < .05:
				self.caster.level.deal_damage(p.x, p.y, self.damage, Tags.Lightning)
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

	thorns = ThornyPrisonSpell()
	thorns.max_charges = 0
	thorns.cool_down = 13
	thorns.description = "Surrounds a group of units with thorny plants"
	thorns.minion_damage = 1

	voidorb = VoidOrbSpell()
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
	unit.buffs.append(TeleportyBuff(chance=.7, radius=7))

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
					self.caster.level.deal_damage(p.x, p.y, self.get_stat('damage'), Tags.Arcane)
				else:
					self.caster.level.deal_damage(p.x, p.y, self.get_stat('damage'), Tags.Dark)
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
				buff = BloodlustBuff()
				buff.extra_damage = 4
				unit.apply_buff(buff, self.duration)

				# For the graphic
				unit.deal_damage(0, Tags.Fire)
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
		return wolf

	wolves = SimpleSummon(wolf, cool_down=8, num_summons=1)
	wolves.name = "Summon Clay Hound"

	bloodboil = WizardBloodboil()

	regen = WizardHealAura()

	melee = SimpleMeleeAttack(10)
	unit.spells = [petrify, wolves, bloodboil, regen, melee]

	unit.tags.append(Tags.Nature)
	return unit

class WizardMaw(VoidMaw):

	def on_init(self):
		VoidMaw.on_init(self)
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

	glassorb = GlassOrbSpell()
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

	unit.tags.append(Tags.Glass)

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

	impswarm = ImpGateSpell()
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
		buff = IceEyeBuff(self.get_stat('damage'), 1)
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
		self.duration = 9
		self.range = 0

	def cast_instant(self, x, y):
		buff = FireEyeBuff(self.get_stat('damage'), 1)
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
						unit.deal_damage(self.get_stat('damage'), Tags.Ice)
					else:
						unit.deal_damage(-self.get_stat('heal'), Tags.Heal)
				else:
					self.caster.level.deal_damage(p.x, p.y, 0, Tags.Ice)
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
		for point in self.caster.level.get_points_in_line(self.caster, Point(x, y))[1:-1]:
			i += 1
			i = i % 2
			dtype = self.damage_type[i]
			self.caster.level.flash(point.x, point.y, dtype.color)
			yield

		for dtype in self.damage_type:
			self.caster.level.deal_damage(x, y, self.get_stat('damage'), dtype)
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
		for p in self.caster.level.get_points_in_line(self.caster, Point(x, y))[1:-1]:
			i += 1
			i %= 2
			self.caster.level.deal_damage(p.x, p.y, 0, dtypes[i])
			yield True

		# Why would we ever not have the buff?  Some krazy buff triggers probably
		target = self.caster.level.get_unit_at(x, y)
		assert(target)

		buff = target.get_buff(Poison)
		if buff:
			target.deal_damage(buff.turns_left, Tags.Fire)
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

	def cast(self, x, y):
		points = [p for p in self.caster.level.get_points_in_los(self.caster) if not (p.x == self.caster.x and p.y == self.caster.y)]

		random.shuffle(points)
		points.sort(key = lambda u: distance(self.caster, u))

		for p in points:
			unit = self.caster.level.get_unit_at(p.x, p.y)
			if unit:
				self.caster.level.deal_damage(p.x, p.y, 0, Tags.Ice)
				unit.apply_buff(FrozenBuff(), 3)
				yield
			elif random.random() < .05:
				self.caster.level.deal_damage(p.x, p.y, 0, Tags.Ice)
				yield				

class WizardFrostfireHydra(Spell):

	def on_init(self):
		self.name = "Summon Frostfire Hydra"
		self.cool_down = 15
		self.minion_range = 9

	def can_cast(self, x, y):
		tile = self.caster.level.tiles[x][y]
		return not tile.unit and tile.can_walk

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
			self.caster.level.deal_damage(p.x, p.y, self.get_stat('damage'), Tags.Fire)

		for p in side_beam:
			self.caster.level.deal_damage(p.x, p.y, self.get_stat('damage'), Tags.Lightning)

class StarfireOrb(OrbSpell):

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
				u.deal_damage(1, Tags.Fire)
			else:
				u.deal_damage(-1, Tags.Heal)

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

	unit.spells = [summon, fatbeam, orb, starfirebolt]
	unit.tags = [Tags.Arcane, Tags.Fire, Tags.Living]
	unit.resists[Tags.Arcane] = 50
	unit.resists[Tags.Fire] = 50
	return unit
