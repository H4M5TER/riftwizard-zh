from Monsters import *
import Spells
import sys

# TODO_ make these different.
WEIGHT_COMMON = 10
WEIGHT_UNCOMMON = 5
WEIGHT_RARE = 1

def NineTheCat():
	cat = DisplacerBeast()
	cat.name = "Nine the Cat"
	
	cat.sprite.char = '9'
	
	cat.buffs.append(ShieldRegenBuff(9, 9))
	cat.buffs.append(ReincarnationBuff(9))
	cat.spells[0].damage = 9

	return cat

def Haunter():
	haunter = Ghost()
	haunter.name = "Haunter"
	haunter.sprite.char = 'H'
	haunter.max_hp = 44
	haunter.buffs.append(ReincarnationBuff(4))
	aura = DamageAuraBuff(damage=2, damage_type=[Tags.Arcane, Tags.Dark], radius=8)
	aura.name = "Nightmare Aura"
	haunter.buffs.append(aura)
	return haunter

#Bats
def BatGiant():
	unit = Bat()
	unit.name = "Giant Bat"
	unit.asset_name = "bat_giant"
	unit.max_hp = 38
	unit.spells[0].damage = 5
	return unit

def BatToxic():
	unit = Bat()
	unit.name = "Toxic Bat"
	unit.asset_name = "bat_toxic"
	unit.max_hp = 20
	spit = SimpleRangedAttack(damage=1, damage_type=Tags.Poison, range=3, buff=Poison, buff_duration=10)
	spit.name = "Poison Spit"
	spit.cool_down = 2
	unit.spells.append(spit)
	unit.resists[Tags.Poison] = 100
	unit.tags.append(Tags.Poison)
	unit.buffs.append(DamageAuraBuff(damage=1, damage_type=Tags.Poison, radius=3))
	return unit

def BatFlame():
	unit = Bat()
	unit.name = "Flame Bat"
	unit.asset_name = "bat_flame"
	unit.max_hp = 20
	spit = SimpleRangedAttack(damage=7, damage_type=Tags.Fire, range=5)
	spit.cool_down = 3
	spit.name = "Flame Spit"
	unit.spells.append(spit)
	unit.resists[Tags.Fire] = 50
	unit.resists[Tags.Ice] = -50
	unit.tags.append(Tags.Fire)
	return unit

def BatKing():
	unit = Bat()
	unit.name = "Flappy, Bat King"
	unit.asset_name = "bat_king"
	unit.max_hp = 52
	unit.spells.insert(0, KingSpell(Bat))
	return unit

def GoblinGiant():
	return Giant(Goblin())

def GoblinArmored():
	unit = Goblin()
	unit.name = "Armored Goblin"
	unit.asset_name = "goblin_armored"

	unit.max_hp = 32
	unit.resists[Tags.Physical] = 50
	unit.resists[Tags.Lightning] = -50

	return unit

def GoblinPsychic():
	unit = Goblin()
	unit.name = "Psychic Goblin"
	unit.asset_name = "goblin_psychic"
	unit.shields = 2

	mind_blast = SimpleRangedAttack(damage=2, damage_type=Tags.Arcane, range=10)
	mind_blast.cool_down = 3
	mind_blast.name = "Mind Blast"

	unit.resists[Tags.Arcane] = 50
	unit.spells.append(mind_blast)
	unit.tags.append(Tags.Arcane)
	return unit

def GoblinRed():
	unit = Goblin()
	unit.name = "Red Goblin"
	unit.asset_name = "goblin_red"
	unit.max_hp = 25

	fire = SimpleRangedAttack(damage=1, damage_type=Tags.Fire, range=4)
	fire.name = "Fire"

	unit.resists[Tags.Fire] = 50
	unit.resists[Tags.Ice] = -50
	unit.spells.append(fire)
	return unit

class BombToss(Spell):

	def on_init(self):
		self.name = "Toss %s" % self.spawn().name
		self.description = "Toss a living bomb in the general direction of an enemy."
		self.range = 7
		self.cool_down = 3
		self.must_target_walkable = True

	def can_cast(self, x, y):
		blocker = self.caster.level.get_unit_at(x, y)
		if blocker:
			return False
		return Spell.can_cast(self, x, y)

	def get_ai_target(self):
		return self.get_corner_target(4)

	def cast(self, x, y):

		blocker = self.caster.level.get_unit_at(x, y)
		if blocker:
			return

		for q in self.caster.level.get_points_in_line(self.caster, Point(x, y), find_clear=True)[1:-1]:
			self.caster.level.deal_damage(q.x, q.y, 0, Tags.Arcane, self)
			yield

		bomb = self.spawn()
		self.summon(bomb, target=Point(x, y))

class VoidBombToss(BombToss):

	def __init__(self):
		self.spawn = VoidBomber
		BombToss.__init__(self)

class FireBombToss(BombToss):

	def __init__(self):
		self.spawn = FireBomber
		BombToss.__init__(self)

def GoblinVoidDemoman():
	unit = Goblin()
	unit.name = "Goblin Void Demolitionist"
	unit.max_hp = 16
	unit.resists[Tags.Arcane] = 50

	unit.spells.insert(0, VoidBombToss())
	return unit

def GoblinFireDemoman():
	unit = Goblin()
	unit.name = "Goblin Fire Demolitionist"

	unit.max_hp = 16
	unit.resists[Tags.Fire] = 50
	
	unit.spells.insert(0, FireBombToss())
	return unit

def GoblinLanky():
	unit = Goblin()
	unit.name = "Lanky Goblin"
	unit.asset_name = "goblin_lanky"

	unit.max_hp = 18
	unit.spells[0] = SimpleRangedAttack(damage=5, damage_type=Tags.Physical, name="Long Armed Melee")

	return unit

class GiantVoidBombSuicide(VoidBomberSuicide):

	def on_init(self):
		VoidBomberSuicide.on_init(self)
		self.range = 2
		self.diag_range = True
		self.melee = False
		self.requires_los = False		
		self.description = "Suicide attack\n5x5 square area\nAutocast on death"


def VoidBomberGiant():
	unit = VoidBomber()
	unit.name = "Giant Void Bomber"
	unit.asset_name = "void_bomber_giant"
	unit.max_hp = 20
	unit.buffs[0].radius = 2 
	unit.spells = [GiantVoidBombSuicide()]
	unit.resists[Tags.Arcane] = 50
	return unit

class GiantFireBombSuicide(FireBomberSuicide):

	def on_init(self):
		VoidBomberSuicide.on_init(self)
		self.range = 4
		self.melee = False
		self.requires_los = True		
		self.description = "Suicide attack\n4 tile radius\nAutocast on death"


def FireBomberGiant():
	unit = FireBomber()
	unit.name = "Giant Fire Bomber"
	unit.asset_name = "fire_bomber_giant"
	unit.max_hp = 20
	unit.buffs[0].radius = 4
	unit.spells = [GiantFireBombSuicide()]
	unit.resists[Tags.Fire] = 50
	return unit

def VoidClusterBomb():
	unit = VoidBomber()
	unit.name = "Void Cluster Bomber"
	unit.asset_name = "void_bomber_cluster"
	unit.buffs[0].clusters = 3
	return unit

def FireClusterBomb():
	unit = FireBomber()
	unit.name = "Fire Cluster Bomber"
	unit.asset_name = "fire_bomber_cluster"
	unit.buffs[0].clusters = 3
	return unit
# todo- prism bomber?
# What should it do?
# Fire and void and lightning damage?
# Arcs of lightning in addition to central explosion?

# Imps!


def FireImpKing():
	unit = FireImp()
	unit.name = "Krilt, Fire Imp King"
	unit.asset_name = "fire_imp_king"
	unit.max_hp = 45
	unit.spells.insert(0, KingSpell(FireImp))
	unit.spells[1].range = 4
	unit.spells[1].damage = 6
	return unit

def FirestormImp():
	unit = FireImp()
	unit.max_hp = 12

	unit.name = "Firestorm Imp"
	unit.asset_name = "imp_firestorm"

	unit.spells[0].radius = 2
	unit.spells[0].damage = 4
	unit.spells[0].range = 5

	return unit

def SparkImpKing():
	unit = SparkImp()
	unit.name = "Xilet, Spark Imp King"
	unit.asset_name = 'spark_imp_king'
	unit.asset_name
	unit.max_hp = 45
	unit.spells.insert(0, KingSpell(SparkImp))
	unit.spells[1].range = 4
	unit.spells[1].damage = 6
	return unit


def IronImpKing():
	unit = IronImp()
	unit.name = "Thrahn, Iron Imp King"
	unit.asset_name = "iron_imp_king"
	unit.max_hp = 45
	unit.spells.insert(0, KingSpell(IronImp))
	unit.spells[1].range = 4
	unit.spells[1].damage = 6
	return unit


class Enlarge(Spell):

	def __init__(self, monster_name):
		self.monster_name = monster_name
		Spell.__init__(self)

	def on_init(self):
		self.name = "Bless %s" % self.monster_name.lower()
		self.description = "Grant a friendly %s +5 max hp and +1 damage" % self.monster_name.lower()
		self.range = RANGE_GLOBAL
		self.requires_los = False

	def get_ai_target(self):
		imps = [u for u in self.caster.level.units if u != self.caster and self.monster_name.lower() in u.name.lower()]
		if imps:
			return random.choice(imps)
		else:
			return None

	def cast(self, x, y):
		unit = self.caster.level.get_unit_at(x, y)
		if unit:
			self.caster.level.show_path_effect(self.caster, unit, Tags.Dark)
			unit.max_hp += 5
			unit.cur_hp += 5
			for s in unit.spells:
				if hasattr(s, 'damage'):
					s.damage += 1
			yield

def Tablet(name):
	unit = Unit()
	unit.max_hp = 35
	unit.name = "%s Tablet" % name
	unit.asset_name = "tablet_%s" % name.lower()

	unit.resists[Tags.Physical] = 50

	unit.spells.append(Enlarge(name))
	unit.stationary = True
	unit.tags = [Tags.Construct, Tags.Dark]
	return unit

def ImpTablet():
	return Tablet("Imp")

def GhostGiant():
	unit = Ghost()
	unit.max_hp = 34
	unit.name = "Giant Ghost"
	unit.asset_name = "ghost_giant"
	unit.spells[0].damage = 6
	return unit

def GhostVoid():
	unit = Ghost()
	unit.resists[Tags.Arcane] = 100
	unit.name = "Void Ghost"
	unit.asset_name = "ghost_void"

	void = SimpleRangedAttack(damage=1, damage_type=Tags.Arcane, range=10)
	void.name = "Void Bolt"
	void.cool_down = 2
	unit.spells[0] = void
	unit.tags = [Tags.Arcane, Tags.Undead]
	return unit


def MindMaggotGiant():
	unit = MindMaggot()
	unit.name = "Giant Mind Maggot"
	unit.asset_name = "mind_maggot_giant"
	unit.max_hp = 52
	unit.spells[0].damage = 8
	return unit

def MindMaggotWinged():
	unit = MindMaggot()
	unit.flying = True
	unit.name = "Mind Maggot Drone"
	unit.asset_name = "mind_maggot_winged"
	dive = LeapAttack(damage=3, range=4, is_leap=True)
	dive.name = "Dive Attack"
	unit.spells.insert(0, dive)
	return unit

def MindMaggotKing():
	unit = MindMaggot()
	unit.name = "Flud, Mind Maggot King"
	unit.asset_name = "mind_maggot_king"
	unit.max_hp = 38
	unit.spells.insert(0, KingSpell(MindMaggot))
	return unit

def DisplacerBeastGiant():
	unit = DisplacerBeast()
	unit.name = "Giant Displacer Beast"
	unit.asset_name = "displacer_beast_giant"
	unit.max_hp *= 6
	unit.spells[0].damage = 9
	return unit

def DisplacerBeastRazor():
	unit = DisplacerBeast()
	unit.name = "Razor Beast"
	unit.asset_name = "displacer_beast_razor_feline"
	unit.max_hp *= 2
	unit.spells[0].damage = 18
	return unit

def DisplacerBeastGhost():
	unit = DisplacerBeast()
	unit.name = "Spirit Strider"
	unit.shields = 2
	unit.asset_name = "displacer_beast_spirit_walker"
	unit.resists[Tags.Physical] = 100
	unit.spells[0].damage_type = Tags.Dark
	unit.tags = [Tags.Undead, Tags.Arcane]
	return unit

def DisplacerBeastBlood():
	unit = DisplacerBeast()
	unit.name = "Bloodfrenzy Feline"
	unit.asset_name = "displacer_beast_blood_feline"
	unit.max_hp *= 3

	melee = unit.spells[0]
	melee.onhit = bloodrage(3)
	melee.name = "Frenzy Claw"
	melee.description = "Gain +3 damage for 10 turns with each attack"
	return unit

def GreenMushboomGiant():
	unit = GreenMushboom()
	unit.name = "Giant Green Mushboom"
	unit.asset_name = "mushboom_green_giant"
	unit.max_hp *= 6
	unit.spells[0].damage = 4
	unit.spells[0].radius = 1
	
	return unit

def GreenMushboomKing():
	unit = GreenMushboom()
	unit.name = "Acrinar, Green Mushboom King"
	unit.asset_name = "mushboom_green_king"
	unit.max_hp *= 4
	unit.spells.insert(0, KingSpell(GreenMushboom))
	return unit


def GreyMushboomGiant():
	unit = GreyMushboom()
	unit.name = "Giant Grey Mushboom"
	unit.asset_name = "mushboom_grey_giant"
	unit.max_hp *= 6
	unit.spells[0].damage = 4
	unit.spells[0].radius = 1
	
	return unit

def GreyMushboomKing():
	unit = GreyMushboom()
	unit.name = "Palinar, Grey Mushboom King"
	unit.asset_name = "mushboom_grey_king"
	unit.max_hp *= 4
	unit.spells.insert(0, KingSpell(GreyMushboom))
	return unit

def MantisGiant():
	unit = Mantis()
	unit.name = "Giant Mantis"
	unit.asset_name ="mantis_alpha"
	unit.max_hp *= 6
	for s in unit.spells:
		s.damage = 9
	return unit

def MantisVoid():
	unit = Mantis()
	unit.shields = 1
	unit.name = "Void Mantis"
	unit.asset_name = "mantis_void"
	chop = SimpleMeleeAttack(6)
	void_leap = LeapAttack(damage=6, damage_type=Tags.Arcane, is_ghost=True, range=5)
	unit.spells = [chop, void_leap]
	unit.resists[Tags.Arcane] = 75
	unit.tags.append(Tags.Arcane)
	return unit

def MantisElectric():
	unit = Mantis()
	unit.name = "Lightning Mantis"
	unit.asset_name = "mantis_lightning"
	chop = SimpleMeleeAttack(6)
	lightning_leap = LeapAttack(damage=6, damage_type=Tags.Lightning, range=14)
	unit.spells = [chop, lightning_leap]
	unit.resists[Tags.Lightning] = 75
	unit.tags.append(Tags.Lightning)
	return unit

def MantisGhost():
	unit = Mantis()
	unit.name = "Ghost Mantis"
	unit.asset_name = "mantis_ghost"
	chop = SimpleMeleeAttack(6, damage_type=Tags.Dark)
	leap = LeapAttack(damage=4, damage_type=Tags.Dark, range=4)
	unit.spells = [chop, leap]

	unit.resists[Tags.Dark] = 50
	unit.resists[Tags.Physical] = 100

	unit.tags = [Tags.Undead]

	unit.buffs.append(TeleportyBuff())
	return unit

def SnakeGiant():
	unit = Snake()
	unit.name = "Giant Snake"
	unit.asset_name = "snake_giant"
	unit.max_hp *= 6
	unit.spells[0].damage *= 2
	
	return unit

class SnakePhilosophy(Spell):

	def on_init(self):
		self.name = "Enlighten Serpent"
		self.description = "Transform a snake into a dragon."
		self.range = 9
		self.cool_down = 3

	def cast_instant(self, x, y):
		unit = self.caster.level.get_unit_at(x, y)
		assert(unit)
		unit.deal_damage(25, Tags.Fire, self)

		# If the snake somehow doesnt burn... ok whatever
		if unit.is_alive():
			return

		drake = random.choice([FireDrake(), StormDrake(), VoidDrake()])
		drake.team = self.caster.team
		self.summon(drake, target=unit)

	def can_cast(self, x, y):
		unit = self.caster.level.get_unit_at(x, y)
		return unit and unit.name == "Snake" and Spell.can_cast(self, x, y)

	def get_ai_target(self):
		candidates = [u for u in self.caster.level.get_units_in_los(self.caster) if u.name == "Snake"]
		candidates = [c for c in candidates if self.can_cast(c.x, c.y)]

		if candidates:
			return random.choice(candidates)

def SerpentPhilosopher():
	unit = Unit()
	unit.asset_name = "snake_man"

	unit.name = "Slazephan, Serpent Philosopher"

	unit.max_hp = 36

	unit.spells.append(SnakePhilosophy())
	unit.spells.append(SimpleRangedAttack(damage=5, damage_type=Tags.Poison, range=6))

	unit.tags = [Tags.Living, Tags.Nature]
	return unit

def BoggartToxic():
	unit = Boggart()
	unit.name = "Toxic Boggart"
	unit.asset_name = "boggart_toxic"

	poisonstab = SimpleMeleeAttack(damage=4, buff=Poison, buff_duration=10)
	unit.spells = [poisonstab]

	unit.resists[Tags.Poison] = 100

	unit.buffs.append(DamageAuraBuff(damage=1, damage_type=Tags.Poison, radius=3))

	return unit

def BoggartGiant():
	unit = Boggart()
	unit.name = "Giant Boggart"
	unit.asset_name = "boggart_giant"
	unit.max_hp *= 6
	unit.spells[0].damage *= 2

	return unit

def BoggartKing():
	unit = Boggart()
	unit.name = "Trafflerabus, Boggart King"
	unit.asset_name = "boggart_king"
	unit.max_hp *= 4
	unit.spells.insert(0, KingSpell(Boggart))
	return unit

def BoggartAetherZealot():
	unit = Boggart()
	unit.max_hp *= 2
	unit.name = "Boggart Aether Zealot"

	unit.shields += 1
	leap = LeapAttack(damage=4, damage_type=Tags.Arcane, is_ghost=True, range=5)
	leap.cool_down = 4
	leap.name = "Aether Charge"
	unit.spells.insert(0, leap)

	return unit


def BoggartVoidMage():
	unit = Boggart()
	unit.name = "Boggart Void Mage"
	unit.asset_name = "boggart_void_mage"
	unit.max_hp *= 3
	unit.shields += 2

	void_manti = SimpleSummon(MantisVoid, num_summons=2, cool_down=10, duration=15)
	void_manti.name = "Summon Void Mantises"
	void_manti.description = "Summons 2 Void Mantises"
	teleport = MonsterTeleport()
	voidbeam = SimpleRangedAttack(damage=9, range=10, damage_type=Tags.Arcane, beam=True, melt=True)
	voidbeam.name = "Void Beam"
	voidbeam.cool_down = 8
	voidbolt = SimpleRangedAttack(damage=4, range=4, damage_type=Tags.Arcane)
	voidbolt.name = "Void Bolt"
	unit.spells = [void_manti, teleport, voidbeam, voidbolt]

	return unit

def ToxicSprigganBush():
	unit = ThornPlant()
	unit.name = "Toxic Spriggan Bush"
	unit.asset_name = "spriggan_bush_toxic"

	unit.buffs.append(DamageAuraBuff(damage=1, damage_type=Tags.Poison, radius=3))
	unit.resists[Tags.Poison] = 100
	return unit

def ToxicSpriggan():
	unit = Spriggan()
	unit.name = "Toxic Spriggan"
	unit.asset_name = "spriggan_toxic"
	unit.buffs = [DamageAuraBuff(damage=1, damage_type=Tags.Poison, radius=3), RespawnAs(ToxicSprigganBush)]
	unit.resists[Tags.Poison] = 100
	return unit

class SmokeBomb(Spell):

	def on_init(self):
		self.name = "Blinding Powder"
		self.description = "Blind nearby units and teleport 6 to 10 tiles away.  Caster runs away while this ability is on cooldown."
		self.range = 0
		self.damage_type = Tags.Poison
		self.radius = 2
		self.duration = 3

	def get_ai_target(self):
		adj_enemies = [u for u in self.caster.level.units if are_hostile(u, self.caster) and distance(u, self.caster, diag=True) <= 1]
		if adj_enemies:
			return self.caster
		else:
			return None

	def cast(self, x, y):
		target = Point(x, y)

		for stage in Burst(self.caster.level, target, self.get_stat('radius')):
			for point in stage:
				damage = self.get_stat('damage')
				self.caster.level.deal_damage(point.x, point.y, 0, self.damage_type, self)
				unit = self.caster.level.get_unit_at(point.x, point.y)
				if unit and unit != self.caster:
					unit.apply_buff(BlindBuff(), self.duration)
			yield

		tp_targets = [t for t in self.caster.level.iter_tiles() if t.can_walk and 6 < distance(self.caster, t) < 10 and not t.unit]
		if tp_targets:
			tp_target = random.choice(tp_targets)
			self.caster.level.act_move(self.caster, tp_target.x, tp_target.y, teleport=True)
			self.caster.level.show_effect(self.caster.x, self.caster.y, Tags.Dark)
		self.caster.apply_buff(CowardBuff(), self.cool_down)
		return


def BoggartAssasin():
	unit = Boggart()
	unit.name = "Boggart Assassin"
	unit.asset_name = "boggart_assasin"

	unit.max_hp = 15
	unit.shields = 2

	leap = LeapAttack(damage=5, range=4)
	leap.name = "Lunge"
	leap.cool_down = 9

	poison = SimpleMeleeAttack(damage=4, buff=Poison, buff_duration=10)
	poison.name = "Poison Stab"
	poison.cool_down = 5

	smoke = SmokeBomb()
	smoke.cool_down = 9

	poke = SimpleMeleeAttack(2)
	poke.name = "Pointy Poke"

	unit.spells = [leap, poison, smoke, poke]

	return unit

def KoboldKing():
	unit = Kobold()
	unit.max_hp = 32
	unit.name = "Pakkatok, Kobold King"
	unit.asset_name = "kobold_king"
	unit.spells[0].damage = 3
	unit.spells.insert(0, KingSpell(Kobold))
	return unit

def KoboldLongbow():
	unit = Kobold()
	unit.name = "Kobold Longbowman"
	unit.max_hp = 6
	unit.spells[0].cast_after_channel = True
	unit.spells[0].max_channel = 3
	unit.spells[0].range *= 2
	unit.spells[0].damage += 1
	unit.spells[0].name = "Longbow"
	unit.spells[0].proj_name = "kobold_arrow_long"
	return unit

def KoboldCrossbow():
	unit = Kobold()
	unit.name = "Kobold Crossbowman"
	unit.max_hp = 6
	xbow = SimpleRangedAttack(damage=6, range=10, cool_down=5, proj_name="kobold_arrow")
	xbow.name = "Crossbow"
	unit.spells = [xbow]
	return unit

def KoboldBallista():
	unit = Unit()
	unit.tags = [Tags.Construct]
	unit.max_hp = 18
	unit.name = "Ballista"
	unit.asset_name = "kobold_ballista"
	unit.stationary = True

	unit.resists[Tags.Fire] = -50
	unit.resists[Tags.Lightning] = 50
	unit.resists[Tags.Physical] = 50

	ballistabolt = SimpleRangedAttack(damage=12, range=17)
	ballistabolt.anem = "Ballista Bolt"
	unit.spells = [ballistabolt]
	return unit

def KoboldSiegeOperator():
	unit = SiegeOperator(KoboldBallista)
	unit.name = "Kobold Siege Mechanic"
	unit.asset_name = "kobold_ballista_operator"

	unit.max_hp = 9
	unit.tags = [Tags.Living]
	return unit

def GoblinCannon():
	unit = Unit()
	unit.tags = [Tags.Construct, Tags.Metallic]
	unit.max_hp = 24
	unit.name = "Cannon"
	unit.asset_name = "goblin_cannon"
	unit.stationary = True

	unit.resists[Tags.Physical] = 50

	unit.resists[Tags.Fire] = -100
	unit.resists[Tags.Lightning] = -100

	cannonball = SimpleRangedAttack(damage=11, range=12, radius=2, damage_type=[Tags.Physical, Tags.Fire])
	cannonball.name = "Cannon Blast"
	unit.spells = [cannonball]

	unit.buffs.append(DeathExplosion(damage=11, damage_type=Tags.Fire, radius=1))
	unit.buffs.append(DeathExplosion(damage=6, damage_type=Tags.Physical, radius=3))
	return unit

def GoblinSiegeOperator():
	unit = SiegeOperator(GoblinCannon)
	unit.name = "Goblin Siege Mechanic"
	unit.asset_name = "goblin_cannon_crew_with_ball"
	unit.max_hp = 11

	unit.tags = [Tags.Living]
	return unit

def SatyrGiant():
	unit = Satyr()
	unit.name = "Giant Satyr"
	unit.asset_name = "satyr_giant"
	unit.max_hp *= 5
	unit.spells = [SatyrWineSpell(), SimpleMeleeAttack(8)]
	return unit

def SatyrKing():
	unit = Satyr()
	unit.name = "Zahlgrahd, Satyr King"
	unit.asset_name = "satyr_king"
	unit.max_hp *= 4
	unit.spells = [KingSpell(Satyr), SatyrWineSpell(), SimpleMeleeAttack(4)]
	return unit

def SatyrWild():
	unit = Satyr()
	unit.name = "Wild Satyr"
	unit.asset_name = "satyr_wild"
	unit.max_hp += 14
	wolfy = SimpleSummon(Wolf, cool_down=8, duration=13, num_summons=2)
	unit.spells.insert(0, wolfy)
	return unit

def SatyrDark():
	unit = Satyr()
	unit.name = "Dark Satyr"
	unit.asset_name = "satyr_dark"

	unit.max_hp += 14

	unit.tags.append(Tags.Dark)
	unit.resists[Tags.Dark] = 50

	darkball = SimpleRangedAttack(damage=5, radius=1, damage_type=Tags.Dark, range=5)
	darkball.name = "Deathball"
	darkball.cool_down = 2
	unit.spells.insert(0, darkball)
	return unit

def SatyrArmored():
	unit = Satyr()
	unit.max_hp += 9

	unit.name = "Armored Satyr"

	unit.resists[Tags.Physical] = 50
	unit.resists[Tags.Lightning] = -50

	return unit

class SpiritShield(Spell):

	def get_ai_target(self):
		# Cast only if there is atleast 1 unshielded undead ally in los
		units = self.caster.level.get_units_in_ball(self.caster, self.radius)
		for u in units:
			if are_hostile(self.caster, u):
				continue
			if Tags.Undead in u.tags and u.shields < 1:
				return self.caster
		return None
		
	def on_init(self):
		self.shields = 1
		self.name = "Spirit Shield"
		self.radius = 6
		self.description = "Grant all undead allies within 6 tiles 1 shield, to a max of %d" % self.shields
		self.range = 0

	def cast_instant(self, x, y):
		units = [u for u in self.caster.level.get_units_in_ball(Point(x, y), self.radius) if not self.caster.level.are_hostile(u, self.caster)]
		for unit in units:
			if Tags.Undead in unit.tags and unit.shields < self.shields:
				unit.add_shields(1)

def WitchFae():
	unit = EvilFairy()
	unit.max_hp += 7

	unit.name = "Faewitch"
	unit.asset_name = "faery_witch"

	ghosty = SimpleSummon(Ghost, num_summons=1, duration=10, cool_down=5)

	bolt = SimpleRangedAttack(damage=5, damage_type=Tags.Arcane, range=4)

	heal = HealAlly(heal=7, range=6)



	unit.spells = [ghosty, SpiritShield(), bolt, heal]

	unit.tags.append(Tags.Dark)

	unit.resists[Tags.Dark] = 50
	unit.resists[Tags.Fire] = -50
	unit.resists[Tags.Holy] = -50

	return unit

def OldWitchFae():
	unit = EvilFairy()
	unit.max_hp += 27

	unit.name = "Old Faewitch"
	unit.asset_name = "old_witch_fae"

	ghosty = SimpleSummon(Ghost, num_summons=2, duration=10, cool_down=5)

	bolt = SimpleRangedAttack(damage=8, damage_type=Tags.Arcane, range=5)

	heal = HealAlly(heal=11, range=6)

	unit.spells = [ghosty, SpiritShield(), bolt, heal]

	unit.tags.append(Tags.Dark)

	unit.resists[Tags.Dark] = 50
	unit.resists[Tags.Fire] = -50
	unit.resists[Tags.Holy] = -50

	return unit


class GhostFreeze(Spell):

	def on_init(self):
		self.name = "Witchfreeze"
		self.duration = 2
		self.range = 7
		self.cool_down = 13

	def get_description(self):
		return "Sacrifices an adjacent friendly ghost to freeze one target for %d turns" % self.duration

	def find_sacrifice(self):
		# Check for sacrificial ghost
		points = list(self.caster.level.get_points_in_ball(self.caster.x, self.caster.y, 1, diag=True))
		random.shuffle(points)
		for p in points:
			unit = self.caster.level.get_unit_at(p.x, p.y)
			if unit and "ghost" in unit.name.lower():
				return unit
		return None

	def can_cast(self, x, y):
		unit = self.caster.level.get_unit_at(x, y)
		if not unit:
			return False
		if unit.has_buff(FrozenBuff):
			return False
		if unit.has_buff(StunImmune):
			return False
		if unit.resists[Tags.Ice] == 100:
			return False
		if not unit.is_player_controlled and unit.max_hp < 30:
			return False
		return Spell.can_cast(self, x, y)


	def can_pay_costs(self):
		if not self.find_sacrifice():
			return False
		return Spell.can_pay_costs(self)

	def pay_costs(self):
		sacrifice = self.find_sacrifice()
		sacrifice.kill()
		Spell.pay_costs(self)

	def cast(self, x, y):

		for p in self.caster.level.get_points_in_line(self.caster, Point(x, y), find_clear=True):
			self.caster.level.show_effect(p.x, p.y, Tags.Ice)
			yield

		unit = self.caster.level.get_unit_at(x, y)
		if unit:
			unit.apply_buff(FrozenBuff(), self.get_stat('duration'))

def WitchIce():
	unit = Witch()
	unit.name = "Ice Witch"
	unit.asset_name = "witch_ice"
	unit.max_hp += 9

	ghosty = SimpleSummon(Ghost, num_summons=1, duration=10, cool_down=5)
	icebolt = SimpleRangedAttack(damage=5, damage_type=Tags.Ice, range=5)
	ghostfreeze = GhostFreeze()

	unit.spells = [ghostfreeze, ghosty, icebolt]
	unit.resists[Tags.Ice] = 75
	unit.resists[Tags.Fire] = -100

	unit.tags.append(Tags.Ice)
	return unit



def OldWitchIce():
	unit = WitchIce()
	unit.max_hp *= 2
	unit.name = "Old Ice Witch"
	unit.asset_name = "old_witch_ice"

	unit.spells[0].duration = 4
	unit.spells[1].num_summons = 2
	unit.spells[2].damage = 8
	unit.spells[2].range += 1

	return unit

def OldWitchFire():
	unit = WitchFire()
	unit.max_hp *= 2
	unit.name = "Old Fire Witch"
	unit.asset_name = "old_witch_fire"

	unit.spells[0].num_summons = 2
	unit.spells[1].radius = 3
	unit.spells[1].damage += 2
	unit.spells[1].range += 1

	return unit

def Armored(unit):
	unit.asset_name = "%s_armored" % unit.get_asset_name()
	unit.name = "Armored %s" % unit.name
	unit.max_hp += 14
	unit.resists[Tags.Physical] = 50
	unit.resists[Tags.Lightning] = -50
	return unit

def Giant(unit):
	unit.asset_name = "%s_giant" % unit.get_asset_name()
	unit.name = "Giant %s" % unit.name
	unit.max_hp *= 6
	for s in unit.spells:
		if hasattr(s, 'damage'):
			s.damage *= 2
	return unit

def King(base, name=None):
	unit = base()

	# try both possible paths
	p1 = os.path.join('rl_data', 'char', "%s_king.png" % unit.get_asset_name())
	p2 = os.path.join('rl_data', 'char', "%s.png" % name)

	if os.path.exists(p1):
		unit.asset_name = "%s_king" % unit.get_asset_name()
	elif os.path.exists(p2):
		unit.asset_name = "%s" % name

	if name:
		unit.name = "%s, %s King" % (name, unit.name)
	else:
		unit.name = "%s King" % unit.name

	unit.max_hp *= 4
	unit.spells.insert(0, KingSpell(base))
	return unit

def BelcherLizard(unit):
	unit.asset_name = "%s_belcher" % unit.get_asset_name()
	unit.name = "%s Belcher" % unit.name
	unit.max_hp += 12
	unit.spells[0].radius = 2
	unit.spells[0].range += 1
	return unit

def FireLizardGiant():
	return Giant(FireLizard())

def FireLizardArmored():
	return Armored(FireLizard())

def FireLizardBelcher():
	return BelcherLizard(FireLizard())

def IceLizardGiant():
	return Giant(IceLizard())

def IceLizardArmored():
	return Armored(IceLizard())

def IceLizardBelcher():
	return BelcherLizard(IceLizard())

def GhostToad():
	unit = HornedToad()
	unit.name = "Ghost Toad"
	unit.asset_name = "horned_toad_ghost"
	unit.resists[Tags.Physical] = 100
	del unit.resists[Tags.Ice]
	
	unit.max_hp += 4

	unit.tags = [Tags.Nature, Tags.Undead]

	return unit

def HornedToadKing():
	unit = King(HornedToad, "Rumplerog")
	unit.asset_name = "horned_toad_king"
	return unit

class FindBoarRider(Spell):

	def on_init(self):
		self.name = "Find Rider"
		self.description = "Find an adjacent nearby orc to serve as a mount"
		self.range = 0

	def find_rider(self):
		for p in self.caster.level.get_points_in_ball(self.caster.x, self.caster.y, diag=True, radius=1):
			unit = self.caster.level.get_unit_at(p.x, p.y)
			if unit:
				if unit.name == "Orc":
					return unit
		return None

	def can_cast(self, x, y):
		return self.find_rider() is not None and Spell.can_cast(self, x, y)

	def cast_instant(self, x, y):
		rider = self.find_rider()
		rider.kill(trigger_death_event=False)
		self.caster.kill(trigger_death_event=False)
		self.caster.level.add_obj(OrcBoarRider(), self.caster.x, self.caster.y)


def OrcBoar():
	unit = Unit()
	unit.max_hp = 12

	unit.name = "Orc Boar"
	unit.asset_name = "orc_pig"

	unit.is_coward = True
	unit.spells = [FindBoarRider()]
	unit.tags = [Tags.Living]

	return unit

def OrcBoarRider():
	unit = Orc()
	unit.max_hp += 12

	unit.name = "Orc Boar Rider"
	unit.asset_name = "orc_pig_rider"

	charge = LeapAttack(damage=5, is_leap=False, range=4)
	charge.name = "Charge"
	charge.cool_down = 3

	unit.buffs.append(RespawnAs(OrcBoar))
	unit.spells.append(charge)
	return unit

def OrcPyroZealot():
	unit = Orc()
	unit.max_hp += 10
	unit.name = "Orc Flame Zealot"
	unit.asset_name = "orc_pyro_zealot"

	firecharge = LeapAttack(damage=9, damage_type=Tags.Fire, range=5)
	firecharge.name = "Flame Charge"
	firecharge.cool_down = 4
	unit.spells.insert(0, firecharge)

	unit.tags.append(Tags.Fire)
	unit.resists[Tags.Fire] = 75
	return unit
	
def OgreKing():
	return King(Ogre, "Rogath")

def TrollKing():
	return King(Troll, "Yiggoroth")

def GnomeKing():
	return King(Gnome, "Gdeit")
	
def MinotaurKing():
	return King(Minotaur, "Dozadoka")

def OrcKing():
	return King(Orc,"Akabalah")

def OrcArmored():
	unit = Armored(Orc())
	unit.spells[0].damage = 9 # Cause its got a big spear thingy not a club
	unit.name = "Orc Juggernaut"
	return unit

def OrcHoundlord():
	unit = Orc()
	unit.name = "Orc Houndlord"
	unit.max_hp += 9
	houndy = SimpleSummon(OrcWolf, num_summons=2, cool_down=10)
	unit.spells.insert(0, houndy)
	return unit

def GoatHeadGiant():
	unit = Giant(GoatHead())
	unit.asset_name = "gotia_giant"
	return unit

def GoatHeadSteel():
	unit = GoatHead()
	unit.name = "Steel Goatia"
	unit.asset_name = "gotia_steel"

	unit.tags.append(Tags.Metallic)
	unit.max_hp += 4

	return unit

def GoatHeadGhost():
	unit = GoatHead()
	unit.name = "Ghostly Goatia"
	unit.asset_name = "gotia_ghostly"

	unit.tags.append(Tags.Undead)
	unit.max_hp += 4
	unit.resists[Tags.Physical] = 100

	return unit
	
def GoatHeadTablet():
	unit = Tablet("Goatia")
	unit.asset_name = "tablet_gotia"
	return unit

def RavenGiant():
	return Giant(Raven())

def RavenWolf():
	unit = Wolf()
	unit.buffs.append(MatureInto(RavenWere, 20))
	return unit

def RavenWere():
	unit = Raven()

	unit.name = "Wereraven"
	unit.asset_name = "raven_wereraven"
	unit.max_hp += 3

	unit.buffs.append(RespawnAs(RavenWolf))

	return unit

def RavenPossessed():
	unit = Raven()
	unit.name = "Possessed Raven"
	unit.asset_name = "raven_possessed"

	unit.max_hp += 4
	unit.resists[Tags.Fire] = 50

	unit.buffs.append(SpawnOnDeath(FireImp, 3))
	return unit

def RavenToxic():
	unit = Raven()
	unit.name = "Toxic Raven"
	unit.asset_name = "raven_toxic"
	unit.buffs.append(DamageAuraBuff(damage=1, damage_type=Tags.Poison, radius=3))
	unit.tags.append(Tags.Poison)
	unit.resists[Tags.Poison] = 100
	return unit

def WormBallGhostly(HP=10):
	unit = Unit()
	unit.max_hp = HP

	if HP >= 10:
		unit.name = "Large Ghost Worm Ball"
		unit.asset_name = "wormball_med_ghostly"
	else:
		unit.name = "Small Ghost Worm Ball"
		unit.asset_name = "wormball_small_ghostly"

	if HP >= 10:
		unit.buffs.append(SplittingBuff(spawner=lambda : WormBallGhostly(unit.max_hp // 2), children=2))

	unit.buffs.append(RegenBuff(3))
	unit.spells.append(SimpleMeleeAttack(HP // 2, damage_type=Tags.Dark))

	unit.resists[Tags.Physical] = 100
	unit.tags = [Tags.Undead]
	return unit

def WormBallToxic(HP=10):
	unit = Unit()
	unit.max_hp = HP

	if HP >= 10:
		unit.name = "Large Toxic Worm Ball"
		unit.asset_name = "wormball_med_toxic"
	else:
		unit.name = "Small Toxic Worm Ball"
		unit.asset_name = "wormball_small_toxic"

	if HP >= 10:
		unit.buffs.append(SplittingBuff(spawner=lambda : WormBallToxic(unit.max_hp // 2), children=2))

	unit.buffs.append(RegenBuff(3))
	unit.spells.append(SimpleMeleeAttack(HP // 2))
	unit.buffs.append(DamageAuraBuff(damage=2 if HP >= 10 else 1, damage_type=Tags.Poison, radius=3))

	unit.tags = [Tags.Living, Tags.Poison]
	unit.resists[Tags.Poison] = 100
	return unit

def WormBallIron(HP=10):
	unit = Unit()
	unit.max_hp = HP

	if HP >= 10:
		unit.name = "Large Iron Worm Ball"
		unit.asset_name = "wormball_med_iron"
	else:
		unit.name = "Small Iron Worm Ball"
		unit.asset_name = "wormball_small_iron"

	if HP >= 10:
		unit.buffs.append(SplittingBuff(spawner=lambda : WormBallIron(unit.max_hp // 2), children=2))

	unit.buffs.append(RegenBuff(3))
	unit.spells.append(SimpleMeleeAttack(3 + HP // 2))

	unit.tags = [Tags.Construct, Tags.Metallic]
	return unit

def OgreArmored():
	unit = Armored(Ogre())
	unit.name = "Ogre Juggernaut"
	unit.asset_name = "ogre_juggernaut"
	unit.spells[0].damage += 7
	return unit

def OgreThunderbone():
	unit = Ogre()
	unit.name = "Thunderbone Shaman"
	unit.asset_name = "ogre_shaman"
	unit.shields += 1
	unit.max_hp += 14

	tstrike = Spells.ThunderStrike()
	tstrike.description = "Stuns enemies near the target"
	tstrike.damage = 7
	tstrike.duration = 2
	tstrike.cool_down = 12
	tstrike.range = 6

	spirits = SimpleSummon(SparkSpirit, num_summons=2, duration=20)
	spirits.cool_down = 15

	lifedrain = SimpleRangedAttack(damage=7, range=4, damage_type=Tags.Dark, drain=True)
	lifedrain.name = "Life Drain"

	unit.spells = [tstrike, spirits, lifedrain]

	unit.resists[Tags.Dark] = 75
	unit.resists[Tags.Lightning] = 50

	return unit

def OgreBlackblaze():
	unit = Ogre()
	unit.name = "Blackblaze Shaman"
	unit.asset_name = "ogre_mage"
	unit.shields += 1
	unit.max_hp += 12

	nightmare = WizardNightmare(damage_type=[Tags.Dark, Tags.Fire])
	nightmare.cool_down = 12
	nightmare.name = "Blackfire Aura"

	regen = WizardHealAura()
	regen.cool_down = 12
	regen.duration = 6
	regen.heal = 3

	bloodlust = WizardBloodlust()
	bloodlust.cool_down = 6
	bloodlust.bonus = 4
	bloodlust.radius = 6

	bolt = SimpleRangedAttack(damage=5, damage_type=Tags.Fire, range=5)

	unit.spells = [nightmare, regen, bloodlust, bolt]

	return unit

# Centaur druid
# Heal aura, summon eagles (3 eagles), javalin charge ect

def CentaurDruid():
	unit = Centaur()
	unit.name = "Centaur Druid"

	unit.max_hp *= 2

	eagles = SimpleSummon(Thunderbird, num_summons=2, duration=10)
	eagles.cool_down = 20

	regen = WizardHealAura()
	regen.heal = 4
	regen.duration = 8
	regen.cool_down = 14

	unit.spells.insert(0, eagles)
	unit.spells.insert(0, regen)

	return unit

def CentaurArmored():
	return Armored(Centaur())

def Trolltaur():
	unit = Centaur()

	unit.name = "Trolltaur"

	unit.max_hp += 10
	unit.buffs.append(TrollRegenBuff())

	return unit

def SporeBeastAlpha():
	unit = Giant(SporeBeast())
	unit.name = "Spore Beast Alpha"
	unit.asset_name = "spore_beast_alpha"
	return unit

def SporeBeastToxic():
	unit = SporeBeast()
	unit.max_hp += 15

	unit.name = "Toxic Spore Beast"
	unit.asset_name = "spore_beast_toxic"

	unit.buffs.append(DamageAuraBuff(damage=1, damage_type=Tags.Poison, radius=3))
	return unit

def SporeBeastPossessed():
	unit = SporeBeast()
	unit.name = "Possessed Spore Beast"
	unit.asset_name = "spore_beast_possessed"
	unit.buffs.append(SpawnOnDeath(FireImp, 3))
	unit.resists[Tags.Fire] = 50
	unit.max_hp += 7
	return unit

def FireFlies():
	unit = FlyCloud()
	unit.name = "Fire Fly Swarm"
	unit.asset_name = "fly_swarm_fire"
	unit.spells = [SimpleRangedAttack(damage=1, damage_type=Tags.Fire, range=3)]
	unit.resists[Tags.Fire] = 75
	unit.tags.append(Tags.Fire)
	return unit

def BagOfBugsFire():
	unit = BagOfBugs(FireFlies)
	unit.name = "Bag of Fire Flies"
	unit.asset_name = "bag_of_bugs_fire"
	unit.resists[Tags.Fire] = 75
	unit.tags.append(Tags.Fire)
	return unit

def LightningFlies():
	unit = FlyCloud()
	unit.name = "Lightning Bug Swarm"
	unit.asset_name = "fly_swarm_lightning"
	unit.spells = [SimpleRangedAttack(damage=1, damage_type=Tags.Lightning, range=3)]
	unit.resists[Tags.Lightning] = 75
	unit.tags.append(Tags.Lightning)
	return unit

def BagOfBugsLightning():
	unit = BagOfBugs(LightningFlies)
	unit.name = "Bag of Lightning Bugs"
	unit.asset_name = "bag_of_bugs_lightning"
	unit.resists[Tags.Lightning] = 75
	unit.tags.append(Tags.Lightning)
	return unit

def BrainFlies():
	unit = FlyCloud()
	unit.name = "Brain Fly Swarm"
	unit.asset_name = "fly_swarm_brain"
	unit.spells[0].onhit = drain_spell_charges
	unit.spells[0].description = "On hit, drains a charge of a random spell"
	unit.spells[0].damage_type = Tags.Arcane
	unit.resists[Tags.Arcane] = 50
	unit.tags.append(Tags.Arcane)
	return unit
	
def BagOfBugsBrain():
	unit = BagOfBugs(BrainFlies)
	unit.name = "Bag of Brain Flies"
	unit.asset_name = "bag_of_bugs_brain"
	unit.resists[Tags.Arcane] = 50
	unit.tags.append(Tags.Arcane)
	return unit

def BagOfBugsGiant():
	unit = Giant(BagOfBugs())
	unit.get_buff(BagOfBugsBuff).spawns *= 8
	unit.get_buff(GeneratorBuff).spawn_chance *= 2
	return unit

def TroublerTiny():
	unit = Troubler()
	unit.name = "Baby Troubler"
	unit.asset_name = "troubler_little"
	
	phasebolt = SimpleRangedAttack(damage=1, range=5, damage_type=Tags.Arcane)
	phasebolt.onhit = lambda caster, target: randomly_teleport(target, 2)
	phasebolt.name = "Tiny Phase Bolt"
	phasebolt.description = "Teleports victims randomly up to 2 tiles away"

	unit.spells = [phasebolt]

	unit.buffs.append(MatureInto(Troubler, 50))

	return unit

def TroublerMass():
	unit = Troubler()
	unit.max_hp = 20
	unit.name = "Troubling Mass"
	unit.asset_name = "troubler_mass"
	unit.buffs.append(SpawnOnDeath(TroublerTiny, 9))
	return unit

def TroublerBig():
	unit = Troubler()
	unit.name = "Big Troubler"
	unit.asset_name = "troubler_big"

	unit.max_hp = 35

	phasebolt = SimpleRangedAttack(damage=1, range=10, damage_type=Tags.Arcane, max_channel=2, cast_after_channel=True, radius=2)
	phasebolt.onhit = lambda caster, target: randomly_teleport(target, 9)
	phasebolt.name = "Massive Phase Bolt"
	phasebolt.description = "Teleports victims randomly up to 9 tiles away"

	unit.spells = [phasebolt]

	return unit

def TroublerIron():
	unit = Troubler()
	unit.max_hp = 15
	unit.name = "Iron Troubler"
	unit.asset_name = "troubler_iron"

	ironshot = SimpleRangedAttack(damage=1, range=10, effect=Tags.Petrification)
	ironshot.name = "Iron Gaze"
	ironshot.description = "Petrifies target for 1 turn"
	ironshot.onhit = lambda caster, target: target.apply_buff(PetrifyBuff(), 1)

	unit.spells = [ironshot]

	unit.tags.append(Tags.Metallic)
	return unit

def TroublerGlass():
	unit = Troubler()

	unit.name = "Glass Troubler"
	unit.asset_name = "mask_glass"

	glassify = SimpleRangedAttack(damage=1, damage_type=Tags.Arcane, range=10, effect=Tags.Glassification)
	glassify.name = "Glass Gaze"
	glassify.description = "Glassifies target for 1 turn"
	glassify.onhit = lambda caster, target: target.apply_buff(PetrifyBuff(), 1)

	unit.spells = [glassify]
	unit.tags.append(Tags.Glass)
	return unit

def FairyIce():
	unit = EvilFairy()
	unit.name = "Ice Faery"
	unit.asset_name = "faery_ice"

	icebolt = SimpleRangedAttack(damage=2, range=4, damage_type=Tags.Ice, buff=FrozenBuff, buff_duration=1)
	icebolt.name = "Freezing Bolt"

	unit.spells = [HealAlly(heal=7, range=6), icebolt]
	unit.tags.append(Tags.Ice)
	unit.resists[Tags.Ice] = 100
	return unit

def ArmoredBat():
	unit = Bat()
	unit.asset_name = "bat_vampire_armored"
	unit.is_coward = True
	unit.buffs.append(MatureInto(VampireArmored, 20))
	unit.resists[Tags.Physical] = 50
	unit.resists[Tags.Lightning] = -50
	return unit

def VampireArmored():
	unit = Armored(Vampire())
	unit.get_buff(RespawnAs).spawner = ArmoredBat
	return unit

class VampireCountBuff(Buff):

	def on_init(self):
		self.name = "Blood Tax"
		self.color = Tags.Dark.color
		self.description = "Whenever any enemy unit takes dark damage, heals for 4 HP"
		self.global_triggers[EventOnDamaged] = self.on_damaged

	def on_damaged(self, evt):
		if are_hostile(self.owner, evt.unit) and evt.damage_type == Tags.Dark:
			self.owner.deal_damage(-4, Tags.Heal, self)

def CountBat():
	unit = Bat()
	unit.asset_name = "bat_vampire_count"
	unit.is_coward = True
	unit.buffs.append(MatureInto(VampireCount, 20))
	return unit

def VampireCount():
	unit = Vampire()
	unit.name = "Vampire Count"
	unit.asset_name = "vampire_count"
	unit.max_hp = 93
	unit.spells[0].damage += 4

	unit.buffs.append(VampireCountBuff())
	unit.get_buff(RespawnAs).spawner = CountBat
	return unit

class Haunted(Buff):

	def on_init(self):
		self.name = "Haunted"
		self.buff_type = BUFF_TYPE_CURSE
		self.color = Tags.Dark.color
		self.description = "2 Hostile ghosts spawn near the cursed unit each turn.  The ghosts last 4 turns."

	def on_advance(self):
		for i in range(2):
			ghost = Ghost()
			ghost.team = self.caster.team
			ghost.turns_to_death = 4
			p = self.owner.level.get_summon_point(self.owner.x, self.owner.y, sort_dist=False, radius_limit=7)
			if p:
				self.owner.level.add_obj(ghost, p.x, p.y)
 
def Necrobat():
	bat = Bat()
	bat.asset_name = "bat_vampire_necromancer"
	bat.is_coward = True
	bat.buffs.append(MatureInto(VampireNecromancer, 20))
	return bat

def VampireNecromancer():
	unit = Vampire()
	unit.name = "Vampire Necromancer"
	unit.asset_name = "vampire_necromancer"

	unit.max_hp += 28

	haunt = SimpleCurse(Haunted, 7, effect=Tags.Dark)
	haunt.description = "Haunts the target, spawning 2 ghosts nearby each turn for 7 turns"
	haunt.cool_down = 13
	haunt.name = "Haunt"
	haunt.range = 4
	unit.spells.insert(0, haunt)
	
	freeze = SimpleCurse(FrozenBuff, 2, effect=Tags.Ice)
	freeze.description = "Freezes the target for 2 turns"
	freeze.name = "Freeze"
	freeze.cool_down = 9
	freeze.range = 7
	unit.spells.insert(0, freeze)
	unit.get_buff(RespawnAs).spawner = Necrobat
	return unit

def GnomeGiant():
	return Giant(Gnome())

def GnomeMicro():
	unit = Gnome()
	unit.name = "Micrognome"
	unit.asset_name = "gnome_micro"
	unit.shields += 2
	unit.max_hp = 1
	return unit

def IronThorn():
	unit = FaeThorn()
	unit.name = "Iron Fae Thorn"
	unit.asset_name = "fae_thorn_iron"
	unit.tags.append(Tags.Metallic)
	unit.spells[0].damage += 3
	return unit

def GnomeIron():
	unit = Gnome()
	unit.max_hp += 10

	unit.name = "Iron Gnome"
	unit.asset_name = "gnome_iron"

	def summon_thorn(caster, target):
		thorn = IronThorn()
		p = caster.level.get_summon_point(target.x, target.y, 1.5)
		if p:
			caster.level.add_obj(thorn, p.x, p.y)

	attack = SimpleRangedAttack(damage=2, range=4, damage_type=Tags.Physical, onhit=summon_thorn)
	attack.name = "Iron Thorn Bolt"
	attack.description = "Summons an iron fae thorn adjacent to the target"
	unit.spells = [attack]

	unit.tags.append(Tags.Metallic)
	return unit

def GnomeDruid():
	unit = Gnome()
	unit.name = "Gnome Druid"
	unit.asset_name = "gnome_druid"

	unit.max_hp += 8
	unit.shields += 2

	shield = ShieldAllySpell(shields=2, range=5, cool_down=4)
	frogs = SimpleSummon(GhostToad, num_summons=2, cool_down=14, duration=8)

	unit.spells.insert(0, shield)
	unit.spells.insert(0, frogs)

	return unit

def SpiderCopper():
	unit = SteelSpider()
	unit.name = "Copper Spider"
	unit.asset_name = "steel_spider_copper"

	unit.max_hp -= 3

	bolt = SimpleRangedAttack(damage=7, damage_type=Tags.Lightning, range=8, cool_down=4, beam=True)
	unit.spells.insert(0, bolt)

	return unit

def SpiderFurnace():
	unit = SteelSpider()
	unit.name = "Furnace Spider"
	unit.asset_name = "steel_spider_furnace"

	unit.max_hp += 3

	unit.buffs.append(DamageAuraBuff(damage=2, damage_type=Tags.Fire, radius=4))

	unit.resists[Tags.Fire] = 100
	unit.resists[Tags.Ice] = -50

	return unit

def SpiderMass():
	unit = GiantSpider()
	unit.name = "Arachnid Abombination"
	unit.asset_name = "darK_spider_mass"

	unit.max_hp *= 2
	unit.buffs.append(SpawnOnDeath(GiantSpider, 7))

	unit.spells[0].damage += 3

	return unit

def SteelSpiderMass():
	unit = SteelSpider()
	unit.name = "Steel Arachnid Abombination"
	unit.asset_name = "steel_spider_mass"

	unit.max_hp *= 2
	unit.buffs.append(SpawnOnDeath(SteelSpider, 7))

	unit.spells[0].damage += 3

	return unit

def PhaseSpiderMass():
	unit = PhaseSpider()
	unit.name = "Aether Arachnid Abombination"
	unit.asset_name = "aether_spider_mass"

	unit.max_hp *= 2
	unit.buffs.append(SpawnOnDeath(PhaseSpider, 7))

	unit.spells[0].damage += 3

	return unit

def MetalMantisGiant():
	unit = Giant(MetalMantis())
	unit.name = "Massive Metal Mantis"
	unit.asset_name = "mantis_alpha_metal"
	return unit

def MetalMantisCopper():
	unit = MetalMantis()
	unit.name = "Copper Mantis"
	unit.asset_name = "mantis_metal_copper"

	unit.max_hp -= 3

	bolt = SimpleRangedAttack(damage=7, damage_type=Tags.Lightning, range=8, cool_down=4, beam=True)
	unit.spells.insert(0, bolt)

	return unit

def MetalMantisFurnace():
	unit = MetalMantis()
	unit.name = "Furnace Mantis"
	unit.asset_name = "mantis_metal_furnace"

	unit.max_hp += 3
	unit.buffs.append(DamageAuraBuff(damage=2, damage_type=Tags.Fire, radius=4))

	unit.resists[Tags.Fire] = 100
	unit.resists[Tags.Ice] = -50
	return unit

class GrowSlimes(Spell):

	def on_init(self):
		self.name = "Grow Slimes"
		self.description = "All slimes gain 1 current and max hp"
		self.cool_down = 3
		self.range = 0

	def get_ai_target(self):
		for u in self.caster.level.units:
			if Tags.Slime in u.tags:
				return self.caster
		return None

	def cast_instant(self, x, y):
		for u in self.caster.level.units:
			if Tags.Slime in u.tags:
				u.max_hp += 1
				u.deal_damage(-1, Tags.Heal, self)

def SlimeMage():
	unit = Unit()
	unit.name = "Slime Brewer"
	unit.max_hp = 35

	unit.tags = [Tags.Arcane, Tags.Living]
	
	def summon_slime(caster, target):
		slime = GreenSlime()
		p = caster.level.get_summon_point(target.x, target.y, 1.5)
		if p:
			caster.level.add_obj(slime, p.x, p.y)

	attack = SimpleRangedAttack(damage=1, range=7, damage_type=Tags.Poison, onhit=summon_slime)
	attack.name = "Slime Shot"
	attack.cool_down = 2
	attack.description = "Summons a slime adjacent to the target"
	unit.spells.append(GrowSlimes())
	unit.spells.append(attack)

	return unit

def SlimeCube(spawner):
	# Slime cubes: stationary, regenerating, reproducing slime generators

	unit = spawner()
	unit.asset_name = "%s_cube" % unit.get_asset_name()
	unit.name = "%s Cube" % unit.name
	

	summon = SimpleSummon(spawner, cool_down=10)
	unit.spells.insert(0, summon)

	unit.max_hp *= 3
	unit.stationary = True
	unit.buffs[0].spawner = lambda : SlimeCube(spawner)
	
	return unit

def GreenSlimeCube():
	return SlimeCube(GreenSlime)

def GreenSlimeKing():
	return King(GreenSlime, "Shraggi")

def RedSlimeKing():
	return King(RedSlime, "Praggi")

def RedSlimeCube():
	return SlimeCube(RedSlime)

def IceSlimeKing():
	return King(IceSlime, "Xiaggi")


def IceSlimeCube():
	return SlimeCube(IceSlime)

def VoidSlimeCube():
	return SlimeCube(VoidSlime)

def VoidSlimeKing():
	return King(VoidSlime, "Eoggi")

def PolarBearArmored():
	return Armored(PolarBear())

def PolarBearAlpha():
	unit = Giant(PolarBear())
	unit.name = "Giant Polar Bear"
	unit.asset_name = "polar_bear_alpha"
	unit.buffs[0].heal = 20
	return unit

def PolarBearPossessed():
	unit = PolarBear()
	unit.name = "Possessed Polar Bear"
	unit.asset_name = "polar_bear_possessed"
	unit.buffs.append(SpawnOnDeath(FireImp, 3))
	unit.max_hp += 7
	unit.resists[Tags.Fire] = 50
	return unit

def PolarBearShaman():
	unit = PolarBear()
	unit.shields += 1
	unit.max_hp += 13

	unit.name = "Polar Bear Blizzard Shaman"
	unit.asset_name = "polar_bear_shaman"

	blizzard = WizardBlizzard()
	icehounds = SimpleSummon(IceHound, 2, cool_down=12, duration=8)
	heal = HealAlly(15, 4)
	heal.cool_down = 5
	melee = SimpleMeleeAttack(12)
	unit.spells = [blizzard, icehounds, heal, melee]

	return unit

def FurnaceHound():
	unit = HellHound()
	unit.name = "Furnace Hound"
	unit.asset_name = "hell_hound_furnace"
	unit.tags.append(Tags.Metallic)
	unit.max_hp += 7
	buff = DamageAuraBuff(damage=1, damage_type=Tags.Fire, radius=4)
	buff.name = "Furnace Aura"
	unit.buffs.append(buff)
	unit.spells[0].damage_type = Tags.Physical
	unit.spells[1].damage_type = Tags.Physical
	unit.resists[Tags.Ice] = -50
	return unit

def ChaosHound():
	unit = Unit()
	unit.max_hp = 23
	
	unit.resists[Tags.Fire] = 100
	unit.resists[Tags.Lightning] = 100
	unit.resists[Tags.Ice] = -50
	unit.resists[Tags.Dark] = 50

	bolt = SimpleRangedAttack(damage=6, damage_type=[Tags.Fire, Tags.Lightning], range=7, cool_down=9)
	bolt.name = "Chaos Bolt"

	melee = SimpleMeleeAttack(damage=6, damage_type=Tags.Fire)
	leap = LeapAttack(damage=6, damage_type=Tags.Lightning, range=4)

	unit.spells = [bolt, melee, leap]

	unit.buffs.append(Thorns(3, Tags.Fire))
	unit.buffs.append(Thorns(3, Tags.Lightning))
	unit.tags = [Tags.Demon, Tags.Fire, Tags.Lightning]
	
	unit.name = "Chaos Hound"
	unit.asset_name = "hell_hound_chaos"
	return unit

def InsanityHound():
	unit = Unit()

	unit.name = "Insanity Hound"
	unit.asset_name = "hell_hound_insanity"
	unit.max_hp = 13
	unit.shields = 1

	unit.resists[Tags.Arcane] = 100
	unit.resists[Tags.Dark] = 50

	swap = HagSwap()
	swap.cool_down = 3
	swap.range = 4
	unit.spells.append(swap)
	unit.spells.append(SimpleMeleeAttack(damage=6, damage_type=Tags.Arcane))

	unit.buffs.append(Thorns(4, Tags.Arcane))
	unit.tags = [Tags.Demon, Tags.Arcane]
	return unit

class LesserCultistAlterBuff(Buff):

	def on_init(self):
		self.description = "Whenever a cultist dies, randomly spawns 3 fire or spark imps"
		self.global_triggers[EventOnDeath] = self.on_death

	def on_death(self, evt):
		if evt.unit.name != "Cultist":
			return

		for i in range(3):
			imp = random.choice([FireImp(), SparkImp()])
			self.summon(imp)

def CultistAlterLesser():
	unit = Unit()
	unit.name = "Lesser Demonic Altar"
	unit.asset_name = "cultist_lesser_alter"
	unit.stationary = True
	unit.tags = [Tags.Dark, Tags.Construct]

	unit.max_hp = 35

	unit.buffs.append(LesserCultistAlterBuff())
	return unit

class GreaterCultistAlterBuff(Buff):

	def on_init(self):

		self.charges = 0
		self.global_triggers[EventOnDeath] = self.on_death

	def get_tooltip(self):
		return "Whenever a cultist dies, gains a charge.  At 3 charges, summons a dark or fiery tormentor.\n\nCurrent charges: %d" % self.charges

	def on_death(self, evt):
		if evt.unit.name != "Cultist":
			return

		self.charges += 1

		if self.charges == 3:
			tormentor = random.choice([DarkTormentor(), FieryTormentor()])
			self.summon(tormentor)
			self.charges = 0

def CultistAlterGreater():
	unit = Unit()
	unit.name = "Greater Demonic Altar"
	unit.asset_name = "cultist_greater_alter"
	unit.stationary = True
	unit.tags = [Tags.Dark, Tags.Construct]

	unit.max_hp = 50
	unit.buffs.append(GreaterCultistAlterBuff())
	return unit

def CultistChosen():
	unit = Cultist()
	unit.name = "Cultist Chosen"

	unit.max_hp *= 2

	unit.spells[0].range += 3
	unit.spells[0].damage += 1

	return unit

class CultNecromancyBuff(Buff):

	def on_applied(self, owner):
		self.global_triggers[EventOnDeath] = self.on_death

	def on_death(self, death_event):
		if death_event.unit.name == "Cultist": 
			self.owner.level.queue_spell(self.raise_skeleton(death_event.unit))

	def raise_skeleton(self, unit):
		raise_skeleton(self.owner, unit)
		yield

	def get_tooltip(self):
		return "Whenever a cultist dies, raises that unit as a skeleton."

def CultistLeader():
	unit = Cultist()
	unit.name = "Cultist Necromancer"
	unit.asset_name = "cultist_leader"
	unit.max_hp *= 3

	unit.spells[0].damage = 3

	unit.buffs.append(CultNecromancyBuff())

	return unit

def WildManAlpha():
	unit = WildMan()
	unit.max_hp += 10
	unit.asset_name = "werewolf_human_alpha"
	unit.buffs[0] = MatureInto(WerewolfAlpha, 20)
	return unit

def WerewolfAlpha():
	unit = Giant(Werewolf())
	unit.name = "Werewolf Alpha"
	unit.asset_name = "werewolf_alpha"
	unit.buffs[0] = RespawnAs(WildManAlpha)
	return unit

def WildManPossessed():
	unit = WildMan()
	unit.name = "Possessed Wild Man"
	unit.asset_name = "werewolf_human_possessed"
	unit.buffs[0] = MatureInto(WerewolfPossessed, 20)
	unit.buffs.append(SpawnOnDeath(FireImp, 3))
	unit.resists[Tags.Fire] = 50
	return unit

def WerewolfPossessed():
	unit = Werewolf()
	unit.name = "Possessed Werewolf"
	unit.asset_name = "werewolf_possessed"
	unit.buffs[0] = RespawnAs(WildManPossessed)
	unit.resists[Tags.Fire] = 50
	return unit

def WereWolfShamanMan():
	unit = WildMan()
	unit.asset_name = "werewolf_human_shaman"
	unit.buffs[0] = MatureInto(WerewolfShaman, 20)
	return unit

def WerewolfShaman():
	unit = Werewolf()
	unit.name = "Werewolf Shaman"
	unit.asset_name = "werewolf_shaman"

	unit.buffs[0] = RespawnAs(WereWolfShamanMan)

	bloodlust = WizardBloodlust()
	bloodlust.bonus = 3
	bloodlust.cool_down = 8

	heal = HealAlly(14, range=5)
	heal.cool_down = 4

	bolt = SimpleRangedAttack(damage=7, damage_type=Tags.Dark, cool_down=3, range=7)

	for s in [bolt, heal, bloodlust]:
		unit.spells.insert(0, s)

	return unit

def ChaosLionGiant():
	unit = Giant(RedLion())
	unit.name = "Giant Chaos Lion"
	unit.asset_name = "lion_giant_chaos"
	return unit

def ChaosSnakeGiant():
	unit = Giant(GoldenSnake())
	unit.name = "Giant Chaos Snake"
	unit.asset_name = "snake_giant_chaos"
	return unit

def ChaosChimeraGiant():
	unit = Giant(ChaosChimera())
	unit.asset_name = "chimera_giant"
	unit.buffs[0].spawner = ChaosLionGiant
	unit.buffs[1].spawner = ChaosSnakeGiant
	return unit

def StarfireLionGiant():
	unit = Giant(StarLion())
	unit.name = "Giant Star Lion"
	unit.asset_name = "lion_giant_starfire"
	return unit

def StarfireSnakeGiant():
	unit = Giant(FireSnake())
	unit.name = "Giant Fire Snake"
	unit.asset_name = "snake_giant_starfire"
	return unit

def StarfireChimeraGiant():
	unit = Giant(StarfireChimera())
	unit.asset_name = "chimera_giant_starfire"
	unit.buffs[0].spawner = StarfireLionGiant
	unit.buffs[1].spawner = StarfireSnakeGiant
	return unit

def DeathchillLionGiant():
	unit = Giant(IceLion())
	unit.name = "Giant Ice Lion"
	unit.asset_name = "lion_giant_deathchill"
	return unit

def DeathchillSnakeGiant():
	unit = Giant(DeathSnake())
	unit.name = "Giant Death Snake"
	unit.asset_name = "snake_giant_deathchill"
	return unit

def DeathchillChimeraGiant():
	unit = Giant(DeathchillChimera())
	unit.asset_name = "chimera_giant_deathchill"
	unit.buffs[0].spawner = DeathchillLionGiant
	unit.buffs[1].spawner = DeathchillSnakeGiant
	return unit

def BoneKnightChampion():
	unit = Giant(BoneKnight())
	unit.name = "Bone Champion"
	unit.asset_name = "bone_knight_champion"
	return unit

def BoneKnightKing():
	unit = King(BoneKnight)
	unit.name = "Ossuonobius, Bone King"
	unit.asset_name = "bone_knight_king"
	return unit

def BoneKnightArcher():
	unit = BoneKnight()
	unit.name = "Bone Archer"
	unit.asset_name = "bone_knight_archer"
	bow = SimpleRangedAttack(damage=9, damage_type=Tags.Dark, range=7, proj_name="dark_arrow")
	bow.name = "Wight Bow"

	def drain(caster, target):
		if Tags.Living in target.tags:
			target.max_hp -= 1
			target.max_hp = max(target.max_hp, 1)
			target.cur_hp = min(target.max_hp, target.cur_hp)

	bow.onhit = drain
	bow.description = "Living targets lose 1 max hp"
	unit.spells = [bow]
	return unit

def GolemGold():
	unit = Golem()
	unit.name = "Gold Golem"
	unit.asset_name = "golem_gilded"
	unit.max_hp *= 2
	unit.shields = 4
	unit.resists[Tags.Holy] = 50
	unit.resists[Tags.Arcane] = 50
	return unit

def GolemClay():
	unit = Golem()
	unit.name = "Clay Golem"
	unit.asset_name = "clay_golem"
	unit.max_hp += 15
	unit.buffs.append(RegenBuff(7))
	unit.tags = [Tags.Construct]
	return unit

def GolemBladed():
	unit = Golem()
	unit.name = "Spiked Golem"
	unit.asset_name = "golem_spike"
	unit.buffs.append(Thorns(6))
	unit.spells[0].damage += 9
	return unit

class LightningAura(DamageAuraBuff):
	def __init__(self):
		DamageAuraBuff.__init__(self, 1, Tags.Lightning, 4)
		self.name = "Charged Body"
		self.asset = ['status', 'charged_body']
		self.color = Tags.Lightning.color

def EarthTrollCopperstaff():
	unit = EarthTroll()
	unit.name = "Earth Troll Coppermancer"
	unit.asset_name = "earth_troll_coppermancer"

	unit.shields += 1
	unit.max_hp += 7

	chargebody = SimpleCurse(buff=LightningAura, buff_duration=30)
	chargebody.name = "Charge Body"
	chargebody.description = "Enemies within 4 tiles of target enemy take 1 damage each turn for 30 turns."
	chargebody.damage_type = Tags.Lightning
	chargebody.cool_down = 5

	copperimpswarm = Spells.ImpGateSpell()

	copperimpswarm.cool_down = 20
	copperimpswarm.duration = 7
	copperimpswarm.imp_choices = [CopperImp]
	copperimpswarm.num_summons = 2
	copperimpswarm.minion_duration = 7
	copperimpswarm.description = "For 7 turns, summon 2 copper imps near the caster each turn"
	copperimpswarm.name = "Copper Imp Swarm"
	copperimpswarm.damage_type = Tags.Chaos

	bolt = SimpleRangedAttack(damage=6, beam=True, range=7, damage_type=Tags.Lightning)
	bolt.name = "Lightning Bolt"
	bolt.cool_down = 3
	unit.spells = [chargebody, copperimpswarm, bolt, SimpleMeleeAttack(8)]

	return unit

class MagmaShellBuff(Buff):

	def on_init(self):
		self.resists[Tags.Physical] = 50
		self.resists[Tags.Fire] = 50
		self.buff_type = BUFF_TYPE_BLESS
		self.name = "Magma Shell"
		self.asset = ['status', 'magma_shell']

	def on_unapplied(self):
		for p in self.owner.level.get_points_in_ball(self.owner.x, self.owner.y, 1, diag=True):
			if (p.x, p.y) == (self.owner.x, self.owner.y):
				continue
			self.owner.level.deal_damage(p.x, p.y, 7, Tags.Fire, self)

class MagmaShellSpell(SimpleCurse):

	def __init__(self):
		SimpleCurse.__init__(self, MagmaShellBuff, 5)
		self.name = "Magma Shell"
		self.description = "Grant an ally 50% resistance to fire and physical damage for 5 turns.  Afterwards, deals 9 fire damage to adjacent units."
		self.cool_down = 3
		self.range = 12

	# Only cast if an enemy is within 3 squares
	def can_cast(self, x, y):
		units = self.caster.level.get_units_in_ball(Point(x, y), 1, diag=True)
		enemies = [u for u in units if are_hostile(u, self.caster)]
		if not enemies:
			return False
		return SimpleCurse.can_cast(self, x, y)


def EarthTrollMagmancer():
	unit = EarthTroll()
	unit.name = "Earth Troll Magmancer"
	unit.asset_name = "earth_troll_magmancer"

	unit.max_hp += 13

	fireres = FireProtection()

	magmashell = MagmaShellSpell()
	
	quakeport = WizardQuakeport()

	unit.spells = [quakeport, fireres, magmashell, SimpleMeleeAttack(8)]

	return unit

def HolyEarthElemental():
	unit = Unit()
	unit.stationary = True

	unit.name = "Hallowed Earth Elemental"
	unit.asset_name = "earth_elemental_holy"

	unit.max_hp = 25
	unit.resists[Tags.Physical] = 50
	unit.resists[Tags.Fire] = 50
	unit.resists[Tags.Lightning] = 50
	unit.resists[Tags.Holy] = 100


	unit.spells.append(SimpleMeleeAttack(12))
	unit.buffs.append(DamageAuraBuff(damage=1, damage_type=Tags.Holy, radius=3))
	unit.buffs.append(HealAuraBuff(heal=1, radius=3))

	return unit


def EarthTrollPriest():
	unit = EarthTroll()
	unit.name = "Earth Troll Priest"
	unit.asset_name = "earth_troll_priest"

	unit.max_hp += 8

	heal = HealAlly(15, 8)
	heal.cool_down = 6

	healrock = SimpleSummon(HolyEarthElemental)
	healrock.range = 6
	healrock.cool_down = 7
	healrock.duration = 16

	holybolt = SimpleRangedAttack(damage=6, damage_type=Tags.Holy, range=5)

	unit.spells = [heal, healrock, holybolt]
	unit.resists[Tags.Holy] = 75

	return unit

def SpikeBeastGiant():
	unit = Giant(SpikeBeast())
	unit.name = "Spike Beast Alpha"
	unit.asset_name = "spike_beast_alpha"
	return unit

def SpikeBeastPossessed():
	unit = SpikeBeast()
	unit.name = "Possessed Spike Beast"
	unit.asset_name = "spike_beast_possessed"
	unit.buffs.append(SpawnOnDeath(IronImp, 3))
	unit.resists[Tags.Lightning] = 50
	unit.resists[Tags.Fire] = 50
	return unit

def DwarfExecutioner():
	unit = Dwarf()
	unit.name = "Duergar Executioner"
	unit.max_hp += 9
	unit.spells = [SimpleMeleeAttack(27)]
	unit.spells[0].name = "Axe"
	return unit

def DwarfLizardLord():
	unit = Dwarf()
	unit.name = "Duergar Lizard Lord"
	unit.max_hp += 4
	lizards = SimpleSummon(IceLizard, 2, cool_down=18)
	unit.spells = [lizards, SimpleMeleeAttack(6)]
	return unit

def DwarfDarkPriest():
	unit = Dwarf()
	unit.name = "Duergar Dark Priest"
	unit.asset_name = "duergar_dark_priest"
	unit.shields = 1
	unit.max_hp += 2

	bats = SimpleSummon(Bat, 7, cool_down=9, duration=5)
	bats.range = 7
	heal = HealAlly(6, 8)

	bolt = SimpleRangedAttack(damage=4, damage_type=Tags.Dark, range=8)

	unit.spells = [bats, heal, bolt]
	return unit

def FieryTormentorGiant():
	unit = Giant(FieryTormentor())
	unit.asset_name = "tormentor_fiery_giant"
	return unit

def IcyTormentorGiant():
	unit = Giant(IcyTormentor())
	unit.asset_name = "tormentor_icy_giant"
	return unit

def DarkTormentorGiant():
	unit = Giant(DarkTormentor())
	unit.asset_name = "tormentor_dark_giant"
	return unit

def FieryTormentorMass():
	unit = FieryTormentor()
	unit.name = "Fiery Tormenting Mass"
	unit.asset_name = "tormentor_fiery_mass"
	unit.max_hp += 17
	unit.buffs.append(SpawnOnDeath(FieryTormentor, 3))
	return unit

def IcyTormentorMass():
	unit = IcyTormentor()
	unit.name = "Icy Tormenting Mass"
	unit.asset_name = "tormentor_icy_mass"
	unit.max_hp += 17
	unit.buffs.append(SpawnOnDeath(IcyTormentor, 3))
	return unit

def DarkTormentorMass():
	unit = DarkTormentor()
	unit.name = "Dark Tormenting Mass"
	unit.asset_name = "tormentor_dark_mass"
	unit.max_hp += 17
	unit.buffs.append(SpawnOnDeath(DarkTormentor, 3))
	return unit

def DeathchillTormentor():

	unit = Unit()
	unit.name = "Deathchill Tormentor"
	unit.asset_name = "tormentor_deathchill"
	unit.max_hp = 56

	def freeze(caster, target):
		target.apply_buff(FrozenBuff(), 1)

	burst = SimpleBurst(damage=7, damage_type=Tags.Ice, cool_down=5, radius=4, onhit=freeze, extra_desc="Applies 2 turns of freeze")
	burst.name = "Frosty Torment"

	unit.spells.append(burst)

	burst = SimpleBurst(damage=7, damage_type=Tags.Dark, cool_down=5, ignore_walls=True, radius=4)
	burst.name = "Dark Torment"

	unit.spells.append(burst)

	lifedrain = SimpleRangedAttack(damage=2, range=2, damage_type=Tags.Dark, drain=True)
	lifedrain.name = "Soul Suck"
	unit.spells.append(lifedrain)

	unit.tags = [Tags.Dark, Tags.Ice, Tags.Demon]
	unit.resists[Tags.Dark] = 100
	unit.resists[Tags.Fire] = -50
	unit.resists[Tags.Ice] = 100
	return unit

def SpikeBallToxic():
	unit = SpikeBall()
	unit.name = "Toxic Spike Ball"
	unit.asset_name = "rolling_spike_ball_poison"

	unit.buffs.append(DamageAuraBuff(damage_type=Tags.Poison, damage=1, radius=4))
	return unit

def SpikeBallTungsten():
	unit = SpikeBall()
	unit.name = "Tungsten Spike Ball"
	unit.asset_name = "rolling_spike_ball_tungsten"
	unit.max_hp *= 5
	unit.spells[0].damage *= 2
	return unit

def SpikeBallGhost():
	unit = SpikeBall()
	unit.name = "Ghostly Spike Ball"
	unit.asset_name = "rolling_spike_ball_ghost"
	unit.resists[Tags.Physical] = 100
	unit.resists[Tags.Dark] = 75
	unit.buffs.append(TeleportyBuff())
	return unit

def SpikeBallEye():
	unit = SpikeBall()
	unit.name = "Gazing Spike Ball"
	unit.asset_name = "rolling_spike_ball_ocular"
	unit.shields = 2

	beam = SimpleRangedAttack(damage=3, damage_type=Tags.Arcane, range=50, cool_down=3)
	beam.name = "Eye Beam"
	unit.spells.append(beam)

	unit.tags.append(Tags.Arcane)

	return unit

def FloatingEyeIce():
	unit = FloatingEye()
	unit.name = "Ice Eye"
	unit.asset_name = "floating_eyeball_ice"
	icebeam = SimpleRangedAttack(damage=2, damage_type=Tags.Ice, buff=FrozenBuff, buff_duration=1, range=99)
	unit.spells[0] = icebeam

	unit.tags.append(Tags.Ice)
	unit.resists[Tags.Ice] = 100
	return unit

def ChaosSpirit():
	spirit = Unit()
	spirit.max_hp = 36
	spirit.name = "Chaos Spirit"

	spirit.sprite.char = 'S'
	spirit.sprite.color = Color(255, 160, 60)

	spirit.buffs.append(SpiritBuff(Tags.Fire))
	spirit.buffs.append(SpiritBuff(Tags.Lightning))

	chaosball = SimpleRangedAttack(damage=11, radius=1, range=6, damage_type=[Tags.Fire, Tags.Lightning])
	chaosball.name = "Chaos Blast"

	spirit.spells.append(chaosball)

	spirit.resists[Tags.Fire] = 100
	spirit.resists[Tags.Lightning] = 100

	spirit.tags = [Tags.Fire, Tags.Lightning]
	
	return spirit

def StormSpirit():
	spirit = Unit()
	spirit.max_hp = 36
	spirit.name = "Storm Spirit"

	spirit.sprite.char = 'S'
	spirit.sprite.color = Color(255, 160, 60)

	spirit.buffs.append(SpiritBuff(Tags.Ice))
	spirit.buffs.append(SpiritBuff(Tags.Lightning))

	chaosball = SimpleRangedAttack(damage=11, radius=1, range=6, damage_type=[Tags.Ice, Tags.Lightning])
	chaosball.name = "Storm Blast"

	spirit.spells.append(chaosball)

	spirit.resists[Tags.Ice] = 100
	spirit.resists[Tags.Lightning] = 100

	spirit.tags = [Tags.Ice, Tags.Lightning]
	
	return spirit

def StarfireSpirit():
	spirit = Unit()
	spirit.max_hp = 20
	spirit.name = "Starfire Spirit"
	spirit.buffs.append(SpiritBuff(Tags.Fire))
	spirit.buffs.append(SpiritBuff(Tags.Arcane))

	chaosball = SimpleRangedAttack(damage=7, radius=1, range=6, damage_type=[Tags.Fire, Tags.Arcane])
	chaosball.name = "Starfire Blast"

	spirit.spells.append(chaosball)

	spirit.resists[Tags.Fire] = 100
	spirit.resists[Tags.Arcane] = 100

	spirit.tags = [Tags.Fire, Tags.Arcane]

	
	return spirit

def FireWyrmBroodmother():
	unit = FireWyrm()
	unit.name = "Fire Wyrm Broodmother"
	unit.asset_name = "wyrm_red_broodmother"
	unit.max_hp *= 3

	unit.buffs.append(GeneratorBuff(FireWyrm, .05))

	return unit

def FireWyrmArmored():
	unit = Armored(FireWyrm())
	unit.max_hp = 167
	return unit

def IceWyrmBroodmother():
	unit = IceWyrm()
	unit.name = "Ice Wyrm Broodmother"
	unit.asset_name = "wyrm_blue_broodmother"
	unit.max_hp *= 3

	unit.buffs.append(GeneratorBuff(IceWyrm, .05))

	return unit

def IceWyrmArmored():
	unit = Armored(IceWyrm())
	unit.max_hp = 167
	return unit

def BigDrake(unit):
	unit.max_hp *= 3

	unit.asset_name = unit.get_asset_name() + "_massive"
	unit.name = "Massive %s" % unit.name

	unit.spells[0].angle = math.pi / 4.0
	unit.spells[0].range += 2
	unit.spells[0].damage += 4
	unit.spells[1].damage *= 2

	return unit

def FireDrakeMassive():
	return BigDrake(FireDrake())

def FireDrakeArmored():
	unit = Armored(FireDrake())
	unit.max_hp = 89
	return unit

def StormDrakeMassive():
	return BigDrake(StormDrake())

def StormDrakeArmored():
	unit = Armored(StormDrake())
	unit.max_hp = 89
	unit.resists[Tags.Lightning] = 100
	return unit

def VoidDrakeMassive():
	return BigDrake(VoidDrake())

def VoidDrakeArmored():
	unit = Armored(VoidDrake())
	unit.max_hp = 89
	return unit

def GoldDrakeMassive():
	return BigDrake(GoldDrake())

def GoldDrakeArmored():
	unit = Armored(GoldDrake())
	unit.max_hp = 89
	return unit

class ToxicGazeBuff(Buff):

	def on_init(self):
		self.name = "Toxic Gaze"
		self.global_triggers[EventOnDamaged] = self.on_damaged
		self.description = "Whenever an enemy unit in line of sight takes poison damage, redeal that damage as dark damage."

	def on_damaged(self, evt):
		if not evt.damage_type == Tags.Poison:
			return

		if not are_hostile(self.owner, evt.unit):
			return

		if not self.owner.level.can_see(self.owner.x, self.owner.y, evt.unit.x, evt.unit.y):
			return

		for p in self.owner.level.get_points_in_line(self.owner, evt.unit, find_clear=True)[1:-1]:
			self.owner.level.show_effect(p.x, p.y, Tags.Dark, minor=True)
		
		evt.unit.deal_damage(evt.damage, Tags.Dark, self)



def SpiderAelf():
	unit = Unit()
	unit.name = "Aelf Arachnomancer"
	unit.asset_name = "aelf_dark_spider"
	unit.max_hp = 70
	unit.shields = 1

	bite = SimpleMeleeAttack(2, buff=Poison, buff_duration=10)
	bolt = SimpleRangedAttack(damage=3, range=12, damage_type=Tags.Lightning)

	unit.spells = [bite, bolt]

	unit.buffs.append(SpiderBuff())
	unit.buffs.append(ToxicGazeBuff())

	unit.resists[Tags.Dark] = 50
	unit.resists[Tags.Lightning] = 75

	unit.tags = [Tags.Spider, Tags.Living, Tags.Dark, Tags.Lightning, Tags.Poison]

	return unit

def ChaosKnightChampion():
	return Champion(ChaosKnight())

def ChaosKnightKing():
	unit = King(ChaosKnight)
	unit.name = "Vuldakot, Chaos King"
	return unit

def StormKnightChampion():
	return Champion(StormKnight())

def StormKnightKing():
	unit = King(StormKnight)
	unit.name = "Koseidius, Storm King"
	return unit

def VoidKnightChampion():
	return Champion(VoidKnight())

def VoidKnightKing():
	unit = King(VoidKnight)
	unit.name = "Zex Ku, Void King"
	return unit

def VoidHagElder():
	unit = VoidHag()
	unit.max_hp *= 4
	unit.name = "Elder Dream Hag"
	unit.asset_name = "dreamhag_elder"
	unit.spells[0].range = 20
	unit.spells[0].cool_down = 6
	return unit

def EfreetKing():
	return King(Efreet, "Pyrubo")

def EfreetJuggernaut():
	unit = Armored(Efreet())

	unit.name = "Efreet Juggernaut"
	unit.asset_name = "efreet_juggernaut"

	unit.spells[0] = SimpleMeleeAttack(17)

	return unit

def VoidToadGiant():
	return Giant(VoidToad())

def VoidToadArmored():
	return Armored(VoidToad())

def FlameToadGiant():
	return Giant(FlameToad())

def FlameToadArmored():
	return Armored(FlameToad())

def MinotaurIron():
	unit = Minotaur()
	unit.name = "Metal Minotaur"
	unit.asset_name = "minotaur_iron"
	unit.max_hp = 72
	unit.tags.append(Tags.Metallic)
	return unit

def MinotaurArmored():
	unit = Armored(Minotaur())
	unit.name = "Minotaur Juggernaut"
	unit.asset_name = "minotaur_juggernaut"
	for s in unit.spells:
		s.damage += 7
	return unit

class Cauterize(Spell):

	def on_init(self):
		self.name = "Cauterize"
		self.description = "Heal target ally for up to 15 hp.  Deals 10 fire damage to all enemies adjacent to that ally."
		self.target_allies = True
		self.heal = 15
		self.damage = 10
		self.damage_type = Tags.Fire
		self.cool_down = 4

	def can_cast(self, x, y):
		unit = self.caster.level.get_unit_at(x, y)
		if unit:
			if unit.cur_hp < unit.max_hp:
				return Spell.can_cast(self, x, y)
			else:
				return False

	def cast(self, x, y):
		unit = self.caster.level.get_unit_at(x, y)
		if unit:
			unit.deal_damage(-self.get_stat('heal'), Tags.Heal, self)
			yield
		for p in self.caster.level.get_points_in_ball(x, y, 1, diag=True):
			if (p.x, p.y) == (x, y):
				continue
			if not self.caster.level.tiles[p.x][p.y].can_see:
				continue

			unit = self.caster.level.get_unit_at(x, y)
			if not unit:
				continue
			if not are_hostile(self.caster, unit):
				continue

			unit.deal_damage(self.get_stat('damage'), Tags.Fire, self)

def MinotaurMagmaShaman():
	unit = Minotaur()
	heataura = WizardNightmare(damage_type=[Tags.Fire])
	heataura.name = "Flame Aura"

	unit.name = "Minotaur Magma Shaman"
	unit.asset_name = "minotaur_magma_shaman"

	firebolt = SimpleRangedAttack(damage=6, damage_type=Tags.Fire, range=6)
	unit.spells = [heataura, Cauterize(), MagmaShellSpell(), firebolt]

	unit.resists[Tags.Fire] = 75
	unit.tags.append(Tags.Fire)
	return unit

def LamasuGreater():
	unit = Lamasu()
	unit.max_hp *= 4
	unit.shields += 1
	unit.name = "Greater Lamasu"
	unit.asset_name = "lamasu_greater"
	unit.spells[0].damage *= 2
	return unit

def LamasuGold():
	unit = Lamasu()
	unit.max_hp *= 2
	unit.tags.append(Tags.Metallic)
	unit.name = "Gilded Lamasu"
	unit.asset_name = "lamasu_gilded"
	shieldspell = ShieldSightSpell(4, 3)
	unit.spells.insert(0, shieldspell)
	return unit

def LamasuGhost():
	unit = Lamasu()
	unit.name = "Ghostly Lamasu"
	unit.asset_name = "lamasu_ghostly"
	unit.tags.append(Tags.Undead)
	unit.resists[Tags.Physical] = 100
	unit.resists[Tags.Dark] = 100
	unit.resists[Tags.Holy] = 50
	unit.buffs.append(TeleportyBuff())
	return unit

def LamasuDark():
	unit = Lamasu()
	unit.buffs = [DamageAuraBuff(damage_type=Tags.Dark, damage=3, radius=6)]
	unit.asset_name = "lamasu_corrupted"
	unit.name = "Corrupted Lamasu"
	unit.resists[Tags.Holy] = -100
	unit.tags.append(Tags.Dark)
	return unit

def ElfAetherScion():
	unit = Elf()
	unit.name = "Aelf Aethermancer"
	unit.asset_name = "aelf_aether_scion"
	unit.max_hp += 8
	unit.shields += 1
	unit.resists[Tags.Arcane] = 75
	teleport = MonsterTeleport()
	teleport.cool_down = 20
	voidbeam = SimpleRangedAttack(damage=9, range=16, damage_type=Tags.Arcane, beam=True, melt=True)
	voidbeam.name = "Void Beam"
	voidbeam.cool_down = 10
	missile = SimpleRangedAttack(damage=7, range=6, damage_type=[Tags.Arcane, Tags.Lightning], radius=2)
	missile.name = "Crackleburn"
	unit.spells = [teleport, voidbeam, missile]
	return unit

def ElfPrism():
	unit = Unit()
	unit.tags = [Tags.Construct, Tags.Arcane]
	unit.max_hp = 20
	unit.shields = 1

	unit.name = "Aether Prism"
	unit.asset_name = "aelf_aether_prism"
	unit.stationary = True

	unit.resists[Tags.Arcane] = 50

	voidbeam = SimpleRangedAttack(damage=18, range=15, beam=True, melt=True, damage_type=Tags.Arcane)
	voidbeam.name = "Void Beam"
	
	unit.spells = [voidbeam]

	return unit

def ElfSiegeOperator():
	unit = SiegeOperator(ElfPrism)
	unit.name = "Aelf Siege Engineer"
	unit.asset_name = "aelf_siege_engineer"
	unit.max_hp = 18
	unit.shields = 1
	unit.resists[Tags.Dark] = 50
	unit.resists[Tags.Lightning] = 75
	unit.tags = [Tags.Living, Tags.Lightning, Tags.Dark]
	return unit

def ElfKing():
	return King(Elf, "Meilmanir")

def ElfElite():
	unit = Elf()
	unit.name = "Aelf Elite"
	unit.asset_name = 'aelf_elite'
	unit.max_hp += 10
	unit.shields += 1
	unit.spells[0].damage = 20
	unit.spells[1].damage = 7
	unit.spells[1].range += 2
	return unit

def IronHand():
	unit = Unit()
	unit.name = "Iron Hand"
	unit.asset_name = "giant_hand_iron"

	melee = SimpleMeleeAttack(19, damage_type=Tags.Physical)
	melee.onhit = lambda caster, target: randomly_teleport(target, 5, requires_los=True)
	melee.name = "Iron Flick"
	melee.description = "Randomly teleport the target up to 5 tiles away."

	unit.spells = [melee]

	unit.max_hp = 68
	unit.tags = [Tags.Arcane, Tags.Metallic]
	unit.resists[Tags.Arcane] = 75

	return unit

def JeweledHand():
	unit = PurpleHand()
	unit.name = "Jeweled Hand"
	unit.asset_name = "giant_hand_jeweled"

	unit.shields += 4

	return unit

def GoldHand():
	unit = PurpleHand()
	unit.name = "Gold Hand"
	unit.asset_name = "giant_hand_holy"

	unit.tags.append(Tags.Holy)
	unit.tags.append(Tags.Metallic)
	unit.resists[Tags.Holy] = 100
	unit.resists[Tags.Dark] = -100

	heal = HealAlly(21, 4)
	heal.cool_down = 7
	unit.max_hp = 44

	return unit

def StormTrollArmored():
	unit = Armored(StormTroll())
	unit.name = "Storm Troll Juggernaut"
	unit.asset_name = "storm_troll_juggernaut"
	unit.spells[0].damage += 5
	unit.resists[Tags.Lightning] = 100
	return unit

def StormTrollMystic():

	unit = StormTroll()
	unit.name = "Storm Troll Mystic"
	unit.shields += 1
	unit.max_hp += 11

	teleport = MonsterTeleport()
	teleport.cool_down = 20
	spirits = SimpleSummon(SparkSpirit, num_summons=2, duration=15, cool_down=10)
	bomb = SimpleRangedAttack(damage=7, damage_type=[Tags.Arcane, Tags.Lightning], range=7, radius=2)
	bomb.name = "Crackleball"
	bomb.cool_down = 2
	heal = HealAlly(16, range=7)
	heal.cool_down = 2

	unit.resists[Tags.Arcane] = 50

	unit.spells = [teleport, spirits, bomb, heal]
	unit.tags.append(Tags.Arcane)

	return unit

def ToadChaosSorcerer():

	unit = HornedToad()
	unit.max_hp = 99

	unit.name = "Toad Chaos Sorcerer"
	unit.asset_name = "horned_toad_mage_chaos"

	impswarm = Spells.ImpGateSpell()
	impswarm.description = "Summons %d imps each turn for %d turns" % (impswarm.num_summons, impswarm.duration)
	impswarm.num_summons = 2
	impswarm.max_charges = 0
	impswarm.cool_down = 20

	fball = SimpleRangedAttack(damage=5, radius=2, range=6, damage_type=Tags.Fire)
	fball.cool_down = 2
	lbolt = SimpleRangedAttack(damage=7, beam=True, range=8, damage_type=Tags.Lightning)
	lbolt.cool_down = 2

	unit.spells = [ToadHop(), impswarm, fball, lbolt]

	unit.resists[Tags.Fire] = 75
	unit.resists[Tags.Lightning] = 75

	unit.tags.append(Tags.Fire)
	unit.tags.append(Tags.Lightning)

	return unit

def ToadNightmareSorcerer():

	unit = HornedToad()
	unit.max_hp = 66
	unit.shields = 3
	unit.name = "Toad Nightmare Sorcerer"
	unit.asset_name = "horned_toad_mage_nightmare"

	nightmare = WizardNightmare()

	pnova = SimpleBurst(damage=5, damage_type=Tags.Poison, radius=6)
	
	pnova.cool_down = 8
	def poison(caster, target):
		target.apply_buff(Poison(), 7)

	pnova.onhit = poison
	pnova.extra_desc = "Applies 7 turns of poison"

	voidbolt = SimpleRangedAttack(damage=4, damage_type=Tags.Arcane, range=8)

	unit.spells = [MonsterTeleport(), ToadHop(), nightmare, pnova, voidbolt]

	unit.resists[Tags.Arcane] = 75
	unit.resists[Tags.Dark] = 75

	unit.tags.append(Tags.Arcane)
	unit.tags.append(Tags.Dark)
	return unit

def YetiGiant():
	return Giant(Yeti())

def YetiShaman():
	unit = Yeti()
	unit.name = "Yeti Shaman"
	unit.asset_name = "yeti_wizard"
	unit.max_hp += 9
	unit.shields = 2

	iceball = SimpleRangedAttack(damage=7, damage_type=Tags.Ice, buff=FrozenBuff, buff_duration=2, radius=2, range=6)
	iceball.cool_down = 11
	heal = HealAlly(33, 4)
	heal.cool_down = 8


	icebolt = SimpleRangedAttack(damage=3, damage_type=Tags.Ice, range=4)
	unit.spells = [iceball, heal, icebolt, SimpleMeleeAttack(10)]

	return unit

def GreenGorgonAlpha():
	unit = Giant(GreenGorgon())
	unit.asset_name = "gorgon_green_alpha"
	return unit

def GreenGorgonPosessed():
	unit = GreenGorgon()
	unit.name = "Possessed Green Gorgon"
	unit.asset_name = "green_gorgon_possossed"
	unit.buffs.append(SpawnOnDeath(RotImp, 3))
	return unit

def MindDevourerGiant():
	return Giant(MindDevourer())

def MegaGargoyleStatue():
	unit = GargoyleStatue()
	unit.max_hp *= 2
	unit.name = "Mega Gargoyle Statue"
	unit.asset_name = "gargoyle_statue_mega"
	unit.buffs[0].spawner = MegaGargoyle
	return unit

def MegaGargoyle():
	unit = Giant(Gargoyle())
	unit.name = "Mega Gargoyle"
	unit.asset_name = "gargoyle_mega"
	unit.buffs[0].spawner = MegaGargoyleStatue
	return unit

def IceGargoyleStatue():
	unit = GargoyleStatue()
	unit.name = "Ice Gargoyle Statue"
	unit.asset_name = "gargoyle_statue_ice"
	unit.tags.append(Tags.Ice)
	unit.resists[Tags.Ice] = 100
	unit.resists[Tags.Fire] = -50
	unit.buffs[0].spawner = IceGargoyle
	return unit

def IceGargoyle():
	unit = Gargoyle()
	unit.name = "Ice Gargoyle"
	unit.asset_name = "gargoyle_ice"
	icebolt = SimpleRangedAttack(damage=5, damage_type=Tags.Ice, range=6)
	unit.spells.append(icebolt)
	unit.tags.append(Tags.Ice)
	unit.resists[Tags.Ice] = 100
	unit.resists[Tags.Fire] = -50
	unit.buffs[0].spawner = IceGargoyleStatue
	return unit

def FireGargoyleStatue():
	unit = GargoyleStatue()
	unit.name = "Fire Gargoyle Statue"
	unit.asset_name = "gargoyle_statue_fire"
	unit.tags.append(Tags.Fire)
	unit.resists[Tags.Fire] = 100
	unit.resists[Tags.Ice] = -50
	unit.buffs[0].spawner = FireGargoyle
	return unit

def FireGargoyle():
	unit = Gargoyle()
	unit.name = "Fire Gargoyle"
	unit.asset_name = "gargoyle_fire"
	icebolt = SimpleRangedAttack(damage=5, damage_type=Tags.Fire, range=6)
	unit.spells.append(icebolt)
	unit.tags.append(Tags.Fire)
	unit.resists[Tags.Fire] = 100
	unit.resists[Tags.Ice] = -50
	unit.buffs[0].spawner = FireGargoyleStatue
	return unit


# Spawn -> VariantSpawn, min, max, weight
variants = {
	Bat: [
		(Vampire, 1, 3, WEIGHT_UNCOMMON),
		(BatGiant, 2, 3, WEIGHT_COMMON),
		(BatToxic, 2, 3, WEIGHT_UNCOMMON),
		(BatFlame, 3, 5, WEIGHT_UNCOMMON),
		(BatKing, 1, 1, WEIGHT_RARE),
	],
	Goblin: [
		(GoblinGiant, 2, 4, WEIGHT_RARE),
		(GoblinArmored, 4, 6, WEIGHT_COMMON),
		(GoblinRed, 2, 3, WEIGHT_UNCOMMON),
		(GoblinLanky, 4, 6, WEIGHT_RARE),
		(GoblinPsychic, 2, 3, WEIGHT_UNCOMMON),
		(GoblinVoidDemoman, 2, 4, WEIGHT_UNCOMMON),
		(GoblinFireDemoman, 2, 4, WEIGHT_UNCOMMON),
		(GoblinSiegeOperator, 2, 5, WEIGHT_UNCOMMON),
	],
	VoidBomber: [
		(GoblinVoidDemoman, 2, 4, WEIGHT_UNCOMMON),
		(VoidSpawner, 1, 1, WEIGHT_UNCOMMON),
		(VoidBomberGiant, 2, 4, WEIGHT_COMMON),
		(FireBomberGiant, 2, 4, WEIGHT_RARE),
		#(PrismBomb, 4, 6, WEIGHT_UNCOMMON),
		(VoidClusterBomb, 2, 4, WEIGHT_COMMON),
	],
	FireBomber: [
		(GoblinFireDemoman, 2, 4, WEIGHT_UNCOMMON),
		(FireSpawner, 1, 1, WEIGHT_UNCOMMON),
		(VoidBomberGiant, 2, 4, WEIGHT_RARE),
		(FireBomberGiant, 2, 4, WEIGHT_COMMON),
		(FireClusterBomb, 2, 4, WEIGHT_COMMON)
	],
	FireImp: [
		(FurnaceImp, 2, 4, WEIGHT_UNCOMMON),
		(ChaosImp, 2, 4, WEIGHT_UNCOMMON),
		(AshImp, 2, 4, WEIGHT_UNCOMMON),
		(FirestormImp, 2, 4, WEIGHT_UNCOMMON),
		(FireImpGiant, 1, 3, WEIGHT_COMMON),
		(FireImpKing, 1, 1, WEIGHT_RARE),
		(VoidImp, 2, 4, WEIGHT_RARE),
		(InsanityImp, 2, 4, WEIGHT_RARE),
		(RotImp, 2, 4, WEIGHT_RARE),
		(ImpTablet, 1, 1, WEIGHT_RARE)
	],
	SparkImp: [
		(ChaosImp, 2, 4, WEIGHT_UNCOMMON),
		(CopperImp, 3, 5, WEIGHT_UNCOMMON),
		(SparkImpGiant, 1, 3, WEIGHT_COMMON),
		(SparkImpKing, 1, 1, WEIGHT_RARE),
		(VoidImp, 2, 4, WEIGHT_RARE),
		(InsanityImp, 2, 4, WEIGHT_RARE),
		(RotImp, 2, 4, WEIGHT_RARE),
		(ImpTablet, 1, 1, WEIGHT_RARE)
	],
	Ghost: [
		(GhostVoid, 3, 5, WEIGHT_COMMON),
		(GhostGiant, 2, 4, WEIGHT_COMMON),
		(GhostFire, 3, 5, WEIGHT_COMMON),
		(GhostKing, 1, 1, WEIGHT_RARE),
		(GhostMass, 2, 3, WEIGHT_UNCOMMON),
		(Witch, 2, 3, WEIGHT_COMMON),
		(Haunter, 1, 1, WEIGHT_UNCOMMON)
	],
	MindMaggot: [
		(MindMaggotGiant, 2, 4, WEIGHT_COMMON),
		(MindMaggotWinged, 3, 7, WEIGHT_COMMON),
		(MindMaggotKing, 1, 1, WEIGHT_RARE),
		(MindDevourer, 1, 1, WEIGHT_UNCOMMON),
		(MindMaggotQueen, 1, 1, WEIGHT_RARE)
	],
	DisplacerBeast: [
		(DisplacerBeastMother, 2, 2, WEIGHT_UNCOMMON),
		(DisplacerBeastRazor, 3, 5, WEIGHT_COMMON),
		(DisplacerBeastGiant, 2, 4, WEIGHT_COMMON),
		(DisplacerBeastGhost, 3, 6, WEIGHT_COMMON),
		(DisplacerBeastBlood, 3, 6, WEIGHT_UNCOMMON),
		(NineTheCat, 1, 1, WEIGHT_UNCOMMON)
	],
	GreenMushboom: [
		(GreenMushboomGiant, 2, 4, WEIGHT_COMMON),
		(GreenMushboomKing, 1, 1, WEIGHT_RARE),
		(GlassMushboom, 3, 6, WEIGHT_RARE),
		(SwampQueen, 1, 1, WEIGHT_RARE),
	],
	GreyMushboom: [
		(GreyMushboomGiant, 2, 4, WEIGHT_COMMON),
		(GreyMushboomKing, 1, 1, WEIGHT_RARE),
		(GlassMushboom, 3, 6, WEIGHT_RARE),
		(SwampQueen, 1, 1, WEIGHT_RARE),
	],
	Mantis: [
		(MetalMantis, 1, 3, WEIGHT_COMMON),
		(MantisGiant, 2, 4, WEIGHT_COMMON),
		(MantisGhost, 3, 6, WEIGHT_COMMON),
		(MantisElectric, 3, 6, WEIGHT_COMMON),
		(MantisVoid, 3, 6, WEIGHT_COMMON),
	],
	Snake: [
		(SnakeGiant, 2, 4, WEIGHT_COMMON),
		(GoldenSnake, 2, 5, WEIGHT_UNCOMMON),
		(FireSnake, 2, 5, WEIGHT_UNCOMMON),
		(DeathSnake, 2, 4, WEIGHT_RARE),
		(SerpentPhilosopher, 1, 1, WEIGHT_RARE)
	],
	Boggart: [
		(BoggartToxic, 2, 3, WEIGHT_COMMON),
		(BoggartGiant, 2, 4, WEIGHT_COMMON),
		(BoggartAetherZealot, 3, 5, WEIGHT_COMMON),
		(BoggartKing, 1, 1, WEIGHT_RARE),
		(BoggartVoidMage, 1, 1, WEIGHT_UNCOMMON),
		(BoggartAssasin, 2, 3, WEIGHT_UNCOMMON),
	],
	Spriggan: [
		(ToxicSpriggan, 2, 3, WEIGHT_COMMON),
		(IcySpriggan, 3, 5, WEIGHT_COMMON),
		(Treant, 2, 3, WEIGHT_COMMON),
	],
	Kobold: [
		(KoboldKing, 1, 1, WEIGHT_RARE),
		(KoboldLongbow, 5, 8, WEIGHT_COMMON),
		(KoboldCrossbow, 4, 6, WEIGHT_UNCOMMON),
		(KoboldSiegeOperator, 2, 7, WEIGHT_UNCOMMON),
	],
	Satyr: [
		(SatyrKing, 1, 1, WEIGHT_RARE),
		(SatyrGiant, 2, 4, WEIGHT_COMMON),
		(SatyrWild, 3, 6, WEIGHT_UNCOMMON),
		(SatyrDark, 2, 5, WEIGHT_UNCOMMON),
		(SatyrArmored, 3, 7, WEIGHT_COMMON)
	],
	Witch: [
		(WitchFae, 2, 3, WEIGHT_COMMON),
		(WitchIce, 2, 4, WEIGHT_COMMON),
		(WitchFire, 2, 4, WEIGHT_COMMON),
		(OldWitch, 3, 5, WEIGHT_COMMON),
		(YoungBloodWitch, 4, 7, WEIGHT_UNCOMMON)
	],
	IronImp: [
		(IronImpGiant, 2, 3, WEIGHT_COMMON),
		(TungstenImp, 3, 5, WEIGHT_UNCOMMON),
		(IronImpKing, 1, 1, WEIGHT_RARE),
		(FurnaceImp, 2, 4, WEIGHT_UNCOMMON),
		(ChaosImp, 2, 4, WEIGHT_UNCOMMON),
		(CopperImp, 3, 5, WEIGHT_UNCOMMON),
		(VoidImp, 2, 4, WEIGHT_RARE),
		(InsanityImp, 2, 4, WEIGHT_RARE),
		(RotImp, 2, 4, WEIGHT_RARE),
	],
	FireLizard: [
		(FireLizardGiant, 2, 4, WEIGHT_COMMON),
		(FireLizardBelcher, 3, 6, WEIGHT_COMMON),
		(FireLizardArmored, 4, 6, WEIGHT_COMMON),
		# Two Header
	],
	IceLizard: [
		(IceLizardGiant, 2, 4, WEIGHT_COMMON),
		(IceLizardBelcher, 3, 6, WEIGHT_COMMON),
		(IceLizardArmored, 4, 6, WEIGHT_COMMON),
		# Two Header
	],
	GiantSpider: [
		(GiantSpiderQueen, 1, 1, WEIGHT_RARE),
		(SteelSpider, 3, 5, WEIGHT_UNCOMMON),
		(PhaseSpider, 3, 5, WEIGHT_UNCOMMON),
		(SpiderMass, 2, 4, WEIGHT_UNCOMMON),
		(SpiderAelf, 3, 5, WEIGHT_UNCOMMON)
	],
	PhaseSpider: [
		(PhaseSpiderQueen, 1, 1, WEIGHT_RARE),
		(PhaseSpiderMass, 2, 4, WEIGHT_UNCOMMON),
		(SpiderAelf, 3, 5, WEIGHT_UNCOMMON)
	],
	HornedToad: [
		(GhostToad, 3, 7, WEIGHT_UNCOMMON),
		(GiantToad, 2, 4, WEIGHT_COMMON),
		(VoidToad, 2, 4, WEIGHT_UNCOMMON),
		(FlameToad, 2, 4, WEIGHT_UNCOMMON),
		(HornedToadKing, 1, 1, WEIGHT_RARE),
		(ToadChaosSorcerer, 1, 1, WEIGHT_RARE),
		(ToadNightmareSorcerer, 1, 1, WEIGHT_RARE)
	],
	Orc: [
		(OrcBoarRider, 3, 6, WEIGHT_COMMON),
		(OrcPyroZealot, 2, 4, WEIGHT_UNCOMMON),
		(OrcFireShaman, 2, 4, WEIGHT_UNCOMMON),
		(OrcKing, 1, 1, WEIGHT_RARE),
		(OrcArmored, 3, 6, WEIGHT_COMMON),
		(OrcHoundlord, 2, 3, WEIGHT_UNCOMMON)
	],
	GoatHead: [
		(GoatHeadGiant, 2, 4, WEIGHT_COMMON),
		(GoatHeadSteel, 3, 6, WEIGHT_UNCOMMON),
		(GoatHeadGhost, 3, 6, WEIGHT_UNCOMMON),
		(GoatHeadTablet, 1, 1, WEIGHT_RARE)
	],
	Raven: [
		(RavenPossessed, 3, 5, WEIGHT_UNCOMMON),
		(RavenGiant, 2, 4, WEIGHT_COMMON),
		(RavenToxic, 2, 5, WEIGHT_UNCOMMON),
		(RavenWere, 3, 5, WEIGHT_UNCOMMON),
		(RavenMage, 1, 1, WEIGHT_RARE)
	],
	WormBall: [
		(WormShambler, 1, 3, WEIGHT_COMMON),
		(WormBallIron, 2, 4, WEIGHT_UNCOMMON),
		(WormBallToxic, 2, 3, WEIGHT_UNCOMMON),
		(WormBallGhostly, 3, 6, WEIGHT_UNCOMMON),
	],
	Ogre: [
		(OgreThunderbone, 2, 3, WEIGHT_UNCOMMON),
		(OgreArmored, 3, 5, WEIGHT_COMMON),
		(OgreBlackblaze, 1, 1, WEIGHT_UNCOMMON)
	],
	Centaur: [
		(CentaurDruid, 1, 2, WEIGHT_UNCOMMON),
		(CentaurArmored, 3, 5, WEIGHT_UNCOMMON),
		(Trolltaur, 2, 4, WEIGHT_UNCOMMON)
	],
	SporeBeast: [
		(SporeBeastToxic, 2, 3, WEIGHT_UNCOMMON),
		(SporeBeastAlpha, 2, 4, WEIGHT_COMMON),
		(SporeBeastPossessed, 3, 5, WEIGHT_UNCOMMON)
	],
	BagOfBugs: [
		(BagOfBugsFire, 2, 4, WEIGHT_COMMON),
		(BagOfBugsLightning, 2, 4, WEIGHT_COMMON),
		(BagOfBugsGiant, 2, 4, WEIGHT_COMMON),
		(BagOfBugsBrain, 2, 4, WEIGHT_UNCOMMON),
	],
	Troll: [
		(TrollKing, 1, 1, WEIGHT_RARE),
		(EarthTroll, 2, 4, WEIGHT_COMMON),
		(StormTroll, 2, 4, WEIGHT_UNCOMMON),
		(Trolltaur, 2, 4, WEIGHT_UNCOMMON)
	],
	Troubler: [
		(TroublerMass, 2, 2, WEIGHT_COMMON),
		(TroublerBig, 2, 4, WEIGHT_COMMON),
		(TroublerIron, 2, 3, WEIGHT_UNCOMMON),
		(TroublerGlass, 1, 1, WEIGHT_RARE),	
	],
	EvilFairy: [
		(WitchFae, 2, 3, WEIGHT_COMMON),
		(FaeArcanist, 2, 4, WEIGHT_COMMON),
		(ThornQueen, 1, 1, WEIGHT_RARE),
		(FairyIce, 2, 4, WEIGHT_COMMON),
		(FairyGlass, 2, 3, WEIGHT_UNCOMMON)
	],
	Vampire: [
		(VampireCount, 2, 4, WEIGHT_COMMON),
		(GreaterVampire, 3, 5, WEIGHT_COMMON),
		(MindVampire, 2, 4, WEIGHT_UNCOMMON),
		(VampireNecromancer, 1, 1, WEIGHT_RARE),
		(VampireArmored, 3, 5, WEIGHT_UNCOMMON)
	],
	Gnome: [
		(GnomeMicro, 3, 5, WEIGHT_COMMON),
		(GnomeIron, 3, 5, WEIGHT_COMMON),
		(GnomeDruid, 1, 1, WEIGHT_UNCOMMON),
		(GnomeKing, 1, 1, WEIGHT_RARE),
		(GnomeGiant, 2, 4, WEIGHT_COMMON)
	],
	SteelSpider: [
		(SpiderCopper, 3, 5, WEIGHT_UNCOMMON),
		(SpiderFurnace, 3, 5, WEIGHT_UNCOMMON),
		(SteelSpiderQueen, 2, 2, WEIGHT_RARE),
		(SteelSpiderMass, 2, 2, WEIGHT_UNCOMMON),
	],
	MetalMantis: [
		(MetalMantisGiant, 2, 4, WEIGHT_COMMON),
		(MetalMantisCopper, 3, 5, WEIGHT_UNCOMMON),
		(MetalMantisFurnace, 3, 5, WEIGHT_UNCOMMON),
	],
	GreenSlime: [
		(GreenSlimeCube, 2, 4, WEIGHT_COMMON),
		(GreenSlimeKing, 1, 1, WEIGHT_RARE),
		(VoidSlime, 3, 5, WEIGHT_UNCOMMON),
		(IceSlime, 3, 5, WEIGHT_UNCOMMON),
		(RedSlime, 3, 5, WEIGHT_UNCOMMON),
		(SlimeMage, 3, 4, WEIGHT_COMMON),
	],
	RedSlime: [
		(RedSlimeCube, 2, 4, WEIGHT_COMMON),
		(RedSlimeKing, 1, 1, WEIGHT_RARE),
		(SlimeMage, 3, 4, WEIGHT_UNCOMMON),
	],	
	IceSlime: [
		(IceSlimeCube, 2, 4, WEIGHT_COMMON),
		(IceSlimeKing, 1, 1, WEIGHT_RARE),
		(SlimeMage, 3, 4, WEIGHT_UNCOMMON),
	],	
	VoidSlime: [
		(VoidSlimeCube, 2, 4, WEIGHT_COMMON),
		(VoidSlimeKing, 1, 1, WEIGHT_RARE),
		(SlimeMage, 3, 4, WEIGHT_UNCOMMON),
	],
	Bloodghast: [
		(YoungBloodWitch, 4, 6, WEIGHT_UNCOMMON),
		(OldBloodWitch, 2, 3, WEIGHT_UNCOMMON),
		(BloodBear, 2, 4, WEIGHT_UNCOMMON),
		(Bloodhound, 5, 9, WEIGHT_UNCOMMON),
	],
	PolarBear: [
		(PolarBearAlpha, 2, 4, WEIGHT_COMMON),
		(PolarBearShaman, 1, 1, WEIGHT_UNCOMMON),
		(PolarBearPossessed, 3, 6, WEIGHT_UNCOMMON),
		(PolarBearArmored, 3, 5, WEIGHT_COMMON)
	],
	HellHound: [
		(IceHound, 2, 4, WEIGHT_RARE),
		(FurnaceHound, 3, 6, WEIGHT_COMMON),
		(ChaosHound, 2, 4, WEIGHT_COMMON),
		(InsanityHound, 2, 4, WEIGHT_RARE)
	],
	Cultist: [
		(CultistAlterLesser, 1, 3, WEIGHT_UNCOMMON),
		(CultistAlterGreater, 1, 1, WEIGHT_UNCOMMON),
		(CultistLeader, 2, 3, WEIGHT_UNCOMMON),
		(CultistChosen, 3, 5, WEIGHT_COMMON)
	],
	Werewolf: [
		(WerewolfShaman, 1, 3, WEIGHT_UNCOMMON),
		(WerewolfAlpha, 2, 4, WEIGHT_COMMON),
		(WerewolfPossessed, 3, 6, WEIGHT_UNCOMMON)
	],
	ChaosChimera: [
		(ChaosChimeraGiant, 2, 4, WEIGHT_UNCOMMON)
	],
	StarfireChimera: [
		(StarfireChimeraGiant, 2, 4, WEIGHT_UNCOMMON)
	],
	DeathchillChimera: [
		(DeathchillChimeraGiant, 2, 4, WEIGHT_UNCOMMON)
	],
	BoneKnight: [
		(BoneKnightArcher, 2, 4, WEIGHT_COMMON),
		(BoneKnightChampion, 2, 4, WEIGHT_COMMON),
		(BoneKnightKing, 1, 1, WEIGHT_RARE),
		(BoneWizard, 1, 1, WEIGHT_UNCOMMON)
	],
	Bloodhound: [
		(BloodBear, 3, 5, WEIGHT_UNCOMMON),
		(YoungBloodWitch, 5, 7, WEIGHT_UNCOMMON),
		(OldBloodWitch, 3, 4, WEIGHT_UNCOMMON),
	],
	Golem: [
		(GolemClay, 3, 5, WEIGHT_UNCOMMON),
		(GolemGold, 3, 5, WEIGHT_UNCOMMON),
		(GolemBladed, 3, 5, WEIGHT_UNCOMMON),
	],
	EarthTroll: [
		(EarthTrollCopperstaff, 1, 1, WEIGHT_UNCOMMON),
		(EarthTrollMagmancer, 1, 1, WEIGHT_UNCOMMON),
		(EarthTrollPriest, 1, 1, WEIGHT_UNCOMMON)
	],
	SpikeBeast: [
		(SpikeBeastGiant, 2, 4, WEIGHT_COMMON),
		(SpikeBeastPossessed, 2, 4, WEIGHT_UNCOMMON)
	],
	OldWitch: [
		(OldWitchFae, 2, 4, WEIGHT_UNCOMMON),
		(OldWitchFire, 2, 4, WEIGHT_COMMON),
		(OldWitchIce, 2, 4, WEIGHT_COMMON),
		(NightHag, 1, 3, WEIGHT_UNCOMMON),
		(VoidHag, 1, 1, WEIGHT_RARE)
	],
	Dwarf: [
		(DwarfExecutioner, 3, 6, WEIGHT_COMMON),
		(DwarfLizardLord, 2, 3, WEIGHT_COMMON),
		(DwarfDarkPriest, 2, 2, WEIGHT_UNCOMMON)
	],
	FieryTormentor: [
		(FieryTormentorGiant, 2, 4, WEIGHT_COMMON),
		(FieryTormentorMass, 2, 4, WEIGHT_UNCOMMON),
		(GhostfireTormentor, 2, 4, WEIGHT_UNCOMMON),
		(FrostfireTormentor, 2, 4, WEIGHT_UNCOMMON)
	],
	DarkTormentor: [
		(DarkTormentorGiant, 2, 4, WEIGHT_COMMON),
		(DarkTormentorMass, 2, 4, WEIGHT_UNCOMMON),
		(GhostfireTormentor, 2, 4, WEIGHT_UNCOMMON),
		(DeathchillTormentor, 2, 4, WEIGHT_UNCOMMON)
	],
	IcyTormentor: [
		(IcyTormentorGiant, 2, 4, WEIGHT_COMMON),
		# Art missing, todo, add
		#(IcyTormentorMass, 2, 4, WEIGHT_UNCOMMON),
		(DeathchillTormentor, 2, 4, WEIGHT_UNCOMMON),
		(FrostfireTormentor, 2, 4, WEIGHT_UNCOMMON)
	],
	SpikeBall: [
		(SpikeBallToxic, 3, 5, WEIGHT_UNCOMMON),
		(SpikeBallGhost, 3, 5, WEIGHT_UNCOMMON),
		(SpikeBallTungsten, 2, 4, WEIGHT_COMMON),
		(SpikeBallCopper, 3, 5, WEIGHT_UNCOMMON),
		(SpikeBallEye, 3, 5, WEIGHT_UNCOMMON)
	],
	FloatingEye: [
		(FloatingEyeIce, 2, 4, WEIGHT_COMMON),
		(FloatingEyeMass, 2, 4, WEIGHT_COMMON),
		(FlamingEye, 2, 4, WEIGHT_COMMON),
	],
	FireSpirit: [
		(StarfireSpirit, 3, 5, WEIGHT_COMMON),
		(ChaosSpirit, 3, 5, WEIGHT_COMMON),
	],
	SparkSpirit: [
		(ChaosSpirit, 3, 5, WEIGHT_COMMON),
		(StormSpirit, 3, 5, WEIGHT_COMMON)
	],
	FireWyrm: [
		(FireWyrmBroodmother, 2, 4, WEIGHT_COMMON),
		(FireWyrmArmored, 4, 6, WEIGHT_COMMON),
	],
	IceWyrm: [
		(IceWyrmBroodmother, 2, 4, WEIGHT_COMMON),
		(IceWyrmArmored, 4, 6, WEIGHT_COMMON),
	],
	FireDrake: [
		(FireDrakeMassive, 2, 4, WEIGHT_COMMON),
		(FireDrakeArmored, 4, 6, WEIGHT_COMMON),
	],
	StormDrake: [
		(StormDrakeMassive, 2, 4, WEIGHT_COMMON),
		(StormDrakeArmored, 4, 6, WEIGHT_COMMON),
	],
	VoidDrake: [
		(VoidDrakeMassive, 2, 4, WEIGHT_COMMON),
		(VoidDrakeArmored, 4, 6, WEIGHT_COMMON),
	],
	GoldDrake: [
		(GoldDrakeMassive, 2, 4, WEIGHT_COMMON),
		(GoldDrakeArmored, 4, 6, WEIGHT_COMMON),
	],
	ChaosKnight: [
		(ChaosKnightChampion, 2, 4, WEIGHT_COMMON),
		(ChaosKnightKing, 1, 1, WEIGHT_UNCOMMON),
	],
	StormKnight: [
		(StormKnightChampion, 2, 4, WEIGHT_COMMON),
		(StormKnightKing, 1, 1, WEIGHT_UNCOMMON),
	],
	VoidKnight: [
		(VoidKnightChampion, 2, 4, WEIGHT_COMMON),
		(VoidKnightKing, 1, 1, WEIGHT_UNCOMMON),
	],
	VoidHag: [
		(VoidHagElder, 2, 4, WEIGHT_COMMON)
	],
	Efreet: [
		(EfreetKing, 1, 1, WEIGHT_RARE),
		(EfreetJuggernaut, 4, 6, WEIGHT_COMMON)
	],
	VoidToad: [
		(VoidToadGiant, 2, 4, WEIGHT_COMMON),
		(VoidToadArmored, 3, 6, WEIGHT_UNCOMMON),
		(ToadNightmareSorcerer, 1, 1, WEIGHT_UNCOMMON)
	],
	FlameToad: [
		(FlameToadGiant, 2, 4, WEIGHT_COMMON),
		(FlameToadArmored, 3, 6, WEIGHT_UNCOMMON),
		(ToadChaosSorcerer, 1, 1, WEIGHT_UNCOMMON)
	],
	Minotaur: [
		(MinotaurIron, 2, 4, WEIGHT_UNCOMMON),
		#(MinotaurArmored, 3, 6, WEIGHT_UNCOMMON),
		(MinotaurKing, 1, 1, WEIGHT_RARE),
		(MinotaurMagmaShaman, 2, 3, WEIGHT_UNCOMMON)
	],
	Lamasu: [
		(LamasuGreater, 2, 4, WEIGHT_COMMON),
		(LamasuGold, 2, 4, WEIGHT_COMMON),
		(LamasuGhost, 2, 4, WEIGHT_UNCOMMON),
		(LamasuDark, 2, 4, WEIGHT_UNCOMMON)
	],
	Elf: [
		(ElfAetherScion, 2, 3, WEIGHT_UNCOMMON),
		(ElfLightningLord, 2, 3, WEIGHT_UNCOMMON),
		(ElfSiegeOperator, 2, 3, WEIGHT_UNCOMMON),
		(ElfKing, 1, 1, WEIGHT_RARE),
		(ElfElite, 3, 5, WEIGHT_COMMON),
	],
	PurpleHand: [
		(IronHand, 3, 5, WEIGHT_UNCOMMON),
		(JeweledHand, 3, 5, WEIGHT_UNCOMMON),
		(GoldHand, 2, 2, WEIGHT_UNCOMMON)
	],
	BoneShambler: [
		(ToweringBoneShambler, 2, 3, WEIGHT_UNCOMMON),
		(BoneShamblerMegalith, 1, 1, WEIGHT_RARE)
	],
	ToweringBoneShambler: [
		(BoneShamblerMegalith, 2, 3, WEIGHT_UNCOMMON)
	],
	StormTroll: [
		(StormTrollArmored, 3, 5, WEIGHT_COMMON),
		(StormTrollMystic, 1, 1, WEIGHT_COMMON)
	],
	GiantSkull: [
		(GoldSkull, 2, 4, WEIGHT_COMMON),
		(GiantFlamingSkull, 2, 3, WEIGHT_COMMON)
	],
	Yeti: [
		(YetiGiant, 2, 4, WEIGHT_COMMON),
		(YetiShaman, 1, 3, WEIGHT_UNCOMMON)
	],
	GreenGorgon: [
		(GreenGorgonAlpha, 2, 4, WEIGHT_COMMON),
		(GreenGorgonPosessed, 3, 5, WEIGHT_UNCOMMON)
	],
	MindDevourer: [
		(MindDevourerGiant, 2, 4, WEIGHT_COMMON)
	],
	Gargoyle: [
		(MegaGargoyle, 3, 5, WEIGHT_COMMON),
		(IceGargoyle, 3, 5, WEIGHT_UNCOMMON),
		(FireGargoyle, 3, 5, WEIGHT_UNCOMMON),
	]

}

def roll_variant(spawn, prng=None):

	if not prng:
		prng = random

	# forcevariant cheat- allways spawn a specific variant, even if that monster isnt present.  for debug.
	if 'forcevariant' in sys.argv:
		var_str = sys.argv[sys.argv.index('forcevariant') + 1]
		var_str = var_str.lower()
		var_str = var_str.replace(' ', '')
		var_str = var_str.replace('_', '')

		for spawn_list in variants.values():
			for spawn, lb, ub, w in spawn_list:
				spawn_str = spawn().name
				spawn_str = spawn_str.replace(' ', '')
				spawn_str = spawn_str.lower()
				if var_str in spawn_str:
					num = prng.randint(lb, ub)
					units = [spawn() for i in range(num)]
					return units

	if spawn in variants:
		options = variants[spawn]
		choice = prng.choices(population=options, weights=[o[3] for o in options])[0]
		variant_spawn, min_num, max_num, weight = choice 
		num = prng.randint(min_num, max_num)

		units = [variant_spawn() for i in range(num)]
#		if max_num == 1:
#			for u in units:
#				u.is_boss = True

		return units
	else:
		return None

def sanity_check():
	for k, v in variants.items():
		for w in v:
			w[0]()


sanity_check()
