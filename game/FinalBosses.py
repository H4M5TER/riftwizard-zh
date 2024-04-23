from Monsters import *
from CommonContent import *
import BossSpawns
from RareMonsters import *
from Spells import *

# Corrupt the tile at x, y on cur_level using the same tile from new_level
def corrupt(x, y, cur_level, new_level):
	# Do not change tiles with units on them, too complex
	if cur_level.get_unit_at(x, y):
		return
	
	new_tile = new_level.tiles[x][y]

	calc_glyph = random.choice([True, True, False])

	if new_tile.is_chasm:
		cur_level.make_chasm(x, y, calc_glyph=calc_glyph)
	elif new_tile.is_floor():
		cur_level.make_floor(x, y, calc_glyph=calc_glyph)
	else:
		cur_level.make_wall(x, y, calc_glyph=calc_glyph)
	
	cur_tile = cur_level.tiles[x][y]				
	cur_tile.tileset = new_tile.tileset
	cur_tile.water = new_tile.water
	cur_tile.sprites = None

	unit = new_tile.unit

	if unit and cur_level.can_stand(x, y, unit):
		new_level.remove_obj(unit)
		cur_level.add_obj(unit, x, y)

	prop = new_tile.prop
	if prop:
		old_prop = cur_tile.prop
		if old_prop:
			cur_level.remove_prop(old_prop)
		cur_level.add_prop(prop, x, y)

	# Remove props from chasms and walls
	if cur_tile.prop and not cur_tile.is_floor():
		cur_level.remove_prop(cur_tile.prop)

	cur_level.show_effect(x, y, Tags.Translocation)

class ChaosBite(Spell):

	def on_init(self):
		self.name = "Chaos Bite"
		self.description = "Deals damage in an arc\nDeals fire and lightning and physical damage"
		self.range = 1.5
		self.melee = True
		self.can_target_self = False
		
		self.damage = 40 # to be overwritten

	def get_impacted_tiles(self, x, y):
		# return the point and the 2 adjacent points which are closest to the caster
		adj_points = [p for p in self.caster.level.get_points_in_ball(self.caster.x, self.caster.y, self.caster.radius + 1, diag=True) if distance(p, self.caster, diag=True) > self.caster.radius]
		aoe = sorted(adj_points, key=lambda p: distance(p, Point(x, y)))[:5]
		return aoe

	def cast(self, x, y):
		dtypes = [Tags.Fire, Tags.Lightning, Tags.Physical]
		for dtype in dtypes:
			for p in self.get_impacted_tiles(x, y):
				self.caster.level.deal_damage(p.x, p.y, self.get_stat('damage'), dtype, self)
			for i in range(3):
				yield

class ChaosBreath(Spell):

	def on_init(self):
		self.name = "Chaos Breath"
		self.damage = 13
		self.range = 32
		self.cool_down = 5
		self.angle = math.pi / 12.0
		self.requires_los = False
		self.description = "Corrupts space"

	def aoe(self, x, y):
		target = Point(x, y)
		return Burst(self.caster.level, 
				     self.caster,
				     self.get_stat('range'), 
				     burst_cone_params=BurstConeParams(target, self.angle), 
				     ignore_walls=True)


	# Always cast if possible, in general direction of the wizard
	def get_ai_target(self):
		wizards = [u for u in self.owner.level.units if u.is_player_controlled]

		# For unittests or other weird scenarios
		if not wizards:
			return Spell.get_ai_target(self)

		wizard = wizards[0]

		if distance(wizard, self.caster) >= self.get_stat('range'):
			return [p for p in self.owner.level.get_points_in_line(self.caster, wizard) if distance(p, self.caster) < self.get_stat('range')][-1]
		else:
			return wizard

	def cast(self, x, y):

		gen_params = self.caster.level.gen_params.make_child_generator(random.randint(15, 19))		
		gen_params.num_exits = 0
		gen_params.num_monsters = 50

		gen_params.bosses = [b for b in gen_params.bosses if b.radius == 0] 

		new_level = gen_params.make_level(check_terrain=False)

		points = 0

		for stage in self.aoe(x, y):
			for point in stage:
				points += 1
				# Do not impact self
				if self.caster.level.tiles[point.x][point.y].unit == self.caster:
					continue

				unit = self.owner.level.get_unit_at(point.x, point.y)
				dtype = random.choice([Tags.Fire, Tags.Lightning, Tags.Physical])
				
				if unit:
					self.owner.level.deal_damage(point.x, point.y, self.get_stat('damage'), dtype, self)
				elif random.random() < .5:
					self.owner.level.deal_damage(point.x, point.y, self.get_stat('damage'), dtype, self)
					corrupt(point.x, point.y, self.caster.level, new_level)

			yield

class SnakeShedding(Buff):

	def on_init(self):
		self.description = "Each turn, summons 3 snakes"
		self.color = Tags.Chaos.color

	def advance(self):
		for i in range(3):
			unit = random.choice([Snake, TwoHeadedSnake])()

			modifier = random.choice([None, None,
									 BossSpawns.Chaostouched, BossSpawns.Stormtouched, BossSpawns.Flametouched,
									 BossSpawns.Metallic])

			if modifier:
				BossSpawns.apply_modifier(modifier, unit, apply_hp_bonus=True)

			self.summon(unit, radius=7, sort_dist=False)
		
class RotatingImmunity(Buff):

	def on_init(self):
		self.description = "Randomly gains 50 fire, lightning, or physical resist each turn."
		self.cur_element = None

	def advance(self):
		if self.cur_element:
			self.owner.resists[self.cur_element] -= 50

		self.cur_element = random.choice([Tags.Fire, Tags.Physical, Tags.Lightning])	
		self.owner.resists[self.cur_element] += 50

		for p in self.owner.iter_occupied_points():
			self.owner.level.show_effect(p.x, p.y, Tags.Buff_Apply, self.cur_element.color)


def Apep():
	unit = Unit()
	unit.name = "Jormungandr"
	unit.max_hp = 3666
	unit.radius = 2
	unit.asset_name = 'beast_of_chaos'
	
	chaos_word = WizardChaosWord()
	chaos_word.cool_down = 13

	unit.spells = [WizardChaosWord(), ChaosBreath(), ChaosBite()]

	unit.buffs = [SnakeShedding(), AdaptiveArmorBuff(10)]

	unit.burrowing = True


	unit.tags = [Tags.Chaos, Tags.Lightning, Tags.Fire, Tags.Living]

	unit.resists[Tags.Fire] = 50
	unit.resists[Tags.Lightning] = 50
	unit.resists[Tags.Physical] = 50

	return unit

class FrogPopeDefense(Buff):

	def on_init(self):
		self.name = "Pope Armor"
		self.description = "Cannot take more than 700 damage in one turn"
		self.owner_triggers[EventOnDamaged] = self.on_damaged
		self.damage_counter = 0

	def on_advance(self):
		self.damage_counter = 0

	def on_damaged(self, evt):

		# Total invincibility above 700
		if self.damage_counter > 700:
			self.owner.add_shields(1)
			return

		self.damage_counter += evt.damage

		# Heal remainder if overdamaged
		if self.damage_counter > 700:
			self.owner.heal(self.damage_counter - 700, self)
			self.damage_counter = 700

class FrogPopeSoulTax(Spell):

	def on_init(self):
		self.name = "Blood Tax"
		self.description = "Steals 30% of the target's current HP and redistributes equally amonst allies of the Frog Pope.  This does not count as damage, and this never kills the target."
		self.range = 99
		self.cool_down = 15

	def get_ai_target(self):
		wizards = [u for u in self.owner.level.units if u.is_player_controlled]
		if not wizards:
			return None
		wizard = wizards[0]
		if not self.can_cast(wizard.x, wizard.y):
			return None
		return wizard

	def cast(self, x, y):

		for p in self.owner.level.get_points_in_line(self.caster, Point(x, y))[1:-1]:
			self.owner.level.show_effect(p.x, p.y, Tags.Blood, minor=True)
			self.owner.level.show_effect(p.x, p.y, Tags.Holy, minor=True)
			yield

		target = self.owner.level.get_unit_at(x, y)

		stolen = (target.cur_hp * 3) // 10

		target.cur_hp -= stolen
		target.cur_hp = max(1, target.cur_hp)

		self.caster.level.show_effect(x, y, Tags.Blood)

		wounded = [u for u in self.owner.level.units if u.cur_hp < u.max_hp and not are_hostile(u, self.caster)]

		per_wounded = stolen // len(wounded)
		extra = stolen % len(wounded)

		random.shuffle(wounded)

		for u in wounded:
			heal = per_wounded
			if extra:
				extra -= 1
				heal += 1
	
			if heal <= 0:
				continue

			u.heal(heal, self)
			self.owner.level.show_path_effect(target, u, Tags.Blood, minor=True, inclusive=False)
			yield

def FrogPopeRandomFrog():
	unit = HornedToad()

	if random.random() < .15:
		unit = ToadPriest()

	if random.random() < .5:
		modifier = random.choice(BossSpawns.modifiers)[0]
		BossSpawns.apply_modifier(modifier, unit, apply_hp_bonus=True)

	unit.cur_hp = random.randint(1, unit.max_hp)

	return unit


def ToadPriest():
	unit = HornedToad()
	unit.max_hp += 7

	unit.name = "Toad Priest"
	# Temp asset
	unit.asset_name = "horned_toad_mage"

	drain_spell = BloodTapSpell()
	drain_spell.max_charges = 0
	drain_spell.cool_down = 4
	drain_spell.bond = 1
	drain_spell.stacking = 1
	drain_spell.damage = 2
	drain_spell.duration = 9
	drain_spell.range = 7

	unit.spells.insert(0, drain_spell)
	return unit

class FrogPopeHop(Spell):

	def on_init(self):
		self.name = "Hop"
		self.description = "Hops up to 10 tiles away and deals 35 physical damage to adjacent enemies"
		self.damage = 35
		self.range = 10
		self.cool_down = 3

	def can_cast(self, x, y):
		return self.owner.level.can_stand(x, y, self.caster)

	def get_ai_target(self):
		options = [p for p in self.owner.level.get_points_in_ball(self.owner.x, self.owner.y, self.get_stat('range')) if self.owner.level.can_stand(p.x, p.y, self.caster)]
		if options:
			return random.choice(options)
		else:
			return None

	def cast(self, x, y):

		# TODO- make it squish things it hops on?  (Damage them and move them out of the way?)

		for p in self.owner.iter_occupied_points():
			self.owner.level.show_effect(p.x, p.y, Tags.Physical)
		
		yield

		self.owner.level.act_move(self.owner, x, y, teleport=True)

		yield

		for p in self.owner.level.get_points_in_ball(self.owner.x, self.owner.y, self.owner.radius+1, diag=True):
			if distance(p, self.owner, diag=True) > self.owner.radius:
				self.owner.level.deal_damage(p.x, p.y, self.get_stat('damage'), Tags.Physical, self)

		yield

def FrogPope():
	unit = Unit()
	unit.name = "Pope the Frog"
	unit.max_hp = 14000
	unit.radius = 2
	unit.asset_name = 'frog_prophet'
	unit.spells = [SimpleMeleeAttack(1)]

	frog_summon = SimpleSummon(FrogPopeRandomFrog, num_summons=7, radius=5, sort_dist=False, cool_down=6)
	frog_summon.name = "Toad Horde"
	frog_summon.description = "Summons a gang of hideous toad friends"

	fly_summon = SimpleSummon(FlyCloud, num_summons=16, radius=5, sort_dist=False, cool_down=12)

	tongue_attack = PullAttack(damage=17, range=7, color=Tags.Tongue.color)
	tongue_attack.name = "Tongue Lash"

	unit.spells = [frog_summon, fly_summon, FrogPopeSoulTax(), FrogPopeHop(), tongue_attack]

	unit.buffs = [FrogPopeDefense()]

	return unit


class BeatleVoidBeam(Spell):

	def on_init(self):
		self.name = "Wave of Corruption"
		self.damage = 17
		self.range = 99
		self.requires_los = False
		self.description = "Corrupt reality and deal 17 damage along a wide beam to the target."
		self.cool_down = 9

	def cast(self, x, y):
		
		gen_params = self.caster.level.gen_params.make_child_generator(random.randint(15 , 19))		
		gen_params.num_exits = 0
		gen_params.num_monsters = 50

		gen_params.bosses = [b for b in gen_params.bosses if b.radius == 0] 

		self.new_level = gen_params.make_level(check_terrain=False)

		points_hit = set(self.owner.iter_occupied_points())
		to_hit = []
		for p in self.owner.level.get_points_in_line(self.caster, Point(x, y)):
			if p in points_hit:
				continue

			self.hit_tile(p)

			points_hit.add(p)
			i = 0
			for q in self.owner.level.get_points_in_ball(p.x, p.y, 3):
				i += 1
				if q not in points_hit:
					
					self.hit_tile(q)
					if i % 5 == 0:
						yield

					points_hit.add(q)

	def hit_tile(self, q):
		self.caster.level.deal_damage(q.x, q.y, self.get_stat('damage'), Tags.Arcane, self)

		if self.caster.level.tiles[q.x][q.y].is_wall():
			self.caster.level.make_floor(q.x, q.y)

		if random.random() < .5:
			corrupt(q.x, q.y, self.caster.level, self.new_level)

class LayVoidEggs(Spell):

	def on_init(self):
		self.name = "Void Eggs"
		self.description = "Creates 6 void eggs which, if allowed to hatch, become horrible void creatures."
		self.num_summons = 6
		self.cool_down = 14
		self.range = 8

	def get_ai_target(self):
		opts = [p for p in self.owner.level.get_points_in_ball(self.owner.x, self.owner.y, self.get_stat('range')) if self.can_cast(p.x, p.y)]
		if opts:
			return random.choice(opts)


	def cast(self, x, y):

		spawner = random.choice([VoidDrake, MindDevourer, CorruptElephant, StarSwimmer, MindMaggotQueen, VoidToad])

		ex = spawner()

		for i in range(self.get_stat('num_summons')):
			unit = Unit()
			unit.stationary = True
			unit.max_hp = 120
			unit.tags = [Tags.Arcane]
			unit.resists[Tags.Arcane] = 75

			unit.name = "%s Egg" % ex.name
			unit.asset_name = 'void_egg'

			unit.buffs.append(MatureInto(spawner, 14))
			unit = self.summon(unit, target=Point(x, y), radius=4, sort_dist=False)

			if unit:
				self.owner.level.show_beam(self.caster, unit, Tags.Arcane, minor=True, inclusive=False)
	
			yield

class BeatleShields(Spell):

	def on_init(self):
		self.name = "Shield Tide"
		self.description = "All allies gain 1 SH, all enemies lose 1 SH."
		self.cool_down = 6
		self.range = 0

	def cast(self, x, y):
		targets = list(self.owner.level.units)
		random.shuffle(targets)

		for t in targets:
			if are_hostile(self.caster, t):
				t.remove_shields(1)
			else:
				t.add_shields(1)
			if random.random() < .25:
				yield

class BeatleBeams(Spell):

	def on_init(self):
		self.name = "Eye Beams"
		self.description = "Deals 2 arcane and 2 dark damage to all enemy units in line of sight"
		self.damage = 2
		self.range = 99
		self.cool_down = 2

	def cast(self, x, y):
		for u in self.owner.level.get_units_in_los(self.owner):
			if not are_hostile(self.owner, u):
				continue

			self.owner.level.show_beam(self.owner, u, Tags.Arcane, minor=True, inclusive=False)
			u.deal_damage(self.get_stat('damage'), Tags.Arcane, self)
			yield
			self.owner.level.show_beam(self.owner, u, Tags.Dark, minor=True, inclusive=False)
			u.deal_damage(self.get_stat('damage'), Tags.Dark, self)
			yield

			
def ApocalypseBeatle():
	unit = Unit()
	unit.name = "Insanity Queen"
	unit.max_hp = 9009
	unit.radius = 2
	unit.asset_name = 'insanity_queen'
	
	unit.tags = [Tags.Living, Tags.Arcane, Tags.Dark]

	# Spell 1: five wide void beam with corruption
	# Spell 2: Lay eggs that hatch into void creatures
	# Spell 3: Aetherwind.  Shield Allies unshield enemies.
	# Spell 4: Teleport. 
	# Spell 5: Void bolts.  Shoot 7 void bolts at random enemies in LOS

	teleport = MonsterTeleport()
	teleport.range = 99
	teleport.requires_los = False
	teleport.cool_down = 15

	unit.spells = [BeatleVoidBeam(), LayVoidEggs(), BeatleShields(), MonsterTeleport(), BeatleBeams()]
	unit.buffs.append(AdaptiveArmorBuff(10))

	return unit


class OphanDefense(Buff):

	def on_init(self):
		self.description = "Redirect all damage to allies"
		self.owner_triggers[EventOnPreDamaged] = self.on_damaged

	def on_damaged(self, evt):
		allies = [u for u in self.owner.level.units if not are_hostile(self.owner, u) and u != self.owner]
		if not allies:
			return

		self.owner.add_shields(1)

		scapegoat = random.choice(allies)

		scapegoat.deal_damage(evt.damage, evt.damage_type, evt.source)

class SummonImmortals(Spell):

	def on_init(self):
		self.name = "Summon Immortals"
		self.description = "Summons 4 immortals"
		self.cool_down = 10
		self.range = 0

	def cast(self, x, y):
		spawner = random.choice([BlackCat, Minotaur, Witch, DarkTormentor, FireDrake, Elf, Troll, Elephant, Dwarf, TwoHeadedSnake])
		for i in range(3):
			unit = spawner()
			BossSpawns.apply_modifier(BossSpawns.Immortal, unit)
			self.summon(unit, radius=6, sort_dist=False)
			yield

class OphanBlast(Spell):

	def on_init(self):
		self.name = "Ophan Blast"
		self.description = "Deal [dark] and [holy] damage and corrupt space in an 8 tile burst around the target."
		self.range = 99
		self.requires_los = False
		self.radius = 8
		self.cool_down = 6
		self.damage = 14

	def get_ai_target(self):
		# just any random point is fine
		return Point(random.randint(0, self.owner.level.width),
					 random.randint(0, self.owner.level.height))

	def cast(self, x, y):
		gen_params = self.caster.level.gen_params.make_child_generator(random.randint(15 , 19))		
		gen_params.num_exits = 0
		gen_params.num_monsters = 50

		gen_params.bosses = [b for b in gen_params.bosses if b.radius == 0] 

		new_level = gen_params.make_level(check_terrain=False)

		for stage in Burst(self.owner.level, Point(x, y), self.radius, ignore_walls=True):
			for p in stage:
				if not self.owner.level.is_point_in_bounds(p):
					continue

				if self.owner.level.tiles[p.x][p.y].unit == self.caster:
					continue

				self.owner.level.deal_damage(p.x, p.y, self.get_stat('damage'), Tags.Dark, self)
				self.owner.level.deal_damage(p.x, p.y, self.get_stat('damage'), Tags.Holy, self)
				corrupt(p.x, p.y, self.owner.level, new_level)
			yield

def Ophan():
	unit = Unit()
	unit.name = "Ophan"
	unit.shields = 7
	unit.max_hp = 7

	unit.flying = True
	unit.stationary = True

	unit.radius = 2
	unit.asset_name = 'the_messenger'

	teleport = MonsterTeleport()
	teleport.range = 99
	teleport.cool_down = 3
	teleport.requires_los = False

	unit.spells = [OphanBlast(), SummonImmortals(), teleport]
	
	unit.buffs = [OphanDefense(), ReincarnationBuff(1), ShieldRegenBuff(7)]
	return unit

def roll_final_boss():
	unit = random.choice([Apep(), Ophan(), FrogPope(), ApocalypseBeatle()])
	unit.is_boss = True
	return unit


if __name__ == '__main__':
	Apep()
	Ophan()
	FrogPope()
	ApocalypseBeatle()