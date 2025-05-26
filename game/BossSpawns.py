from CommonContent import *
from Level import *
from Monsters import *



def apply_variant_hp_bonus(monster):
	monster.max_hp *= 4
	monster.max_hp += 15

	if monster.shields:
		monster.shields += 1

def Toxic(monster):
	toxic_aura = DamageAuraBuff(damage_type=Tags.Poison, damage=2, radius=5)

	if Tags.Poison not in monster.tags:
		monster.tags.append(Tags.Poison)
	monster.resists[Tags.Poison] += 100

	monster.recolor_primary = Color(43, 175, 43)

	monster.apply_buff(toxic_aura)

	monster.name = "Toxic %s" % monster.name
	return monster
	
def Icy(monster):
	iceball = SimpleRangedAttack(damage=6, damage_type=Tags.Ice, buff=FrozenBuff, buff_duration=2, radius=2, range=4, cool_down=4)
	monster.add_spell(iceball, prepend=True)

	if Tags.Ice not in monster.tags:
		monster.tags.append(Tags.Ice)

	monster.resists[Tags.Ice] = 100

	monster.name = "Frostspew %s" % monster.name
	monster.recolor_primary = Color(79, 195, 247)

	return monster

def Metallic(monster):
	if Tags.Metallic not in monster.tags:
		monster.tags.append(Tags.Metallic)

	if monster.resists[Tags.Lightning] < 75:
		monster.resists[Tags.Lightning] = 75
	
	if monster.resists[Tags.Ice] < 75:
		monster.resists[Tags.Ice] = 75

	if monster.resists[Tags.Fire] < 50:
		monster.resists[Tags.Fire] = 50


	# Metal ghosts lose physical resist, metal other stuff gain it
	monster.resists[Tags.Physical] = 50

	monster.name = "Metallic %s" % monster.name
	monster.recolor_primary = Color(189, 189, 189)  # not the same color as metallic, but this is what we use for idols and other metal things

	return monster

def Immortal(monster):

	buff = monster.get_buff(ReincarnationBuff)
	if not buff:
		monster.apply_buff(ReincarnationBuff(2))
	else:
		buff.lives += 2

	monster.name = "Immortal %s" % monster.name
	monster.recolor_primary = Tags.Holy.color

	if monster.resists[Tags.Holy] < 75:
		monster.resists[Tags.Holy] = 75
	if monster.resists[Tags.Dark] < 75:
		monster.resists[Tags.Dark] = 75

	return monster

def Lich(monster):

	monster.add_spell(LichSealSoulSpell(), prepend=True)

	monster.name = "%s Lich" % monster.name
	monster.recolor_primary = Color(156, 39, 176)

	if Tags.Undead not in monster.tags:
		monster.tags.append(Tags.Undead)

	if Tags.Living in monster.tags:
		monster.tags.remove(Tags.Living)

	return monster

def Ghostly(monster):
	monster.apply_buff(TeleportyBuff())

	if Tags.Undead not in monster.tags:
		monster.tags.append(Tags.Undead)
	
	monster.resists[Tags.Physical] = 100

	monster.name = "Ghostly %s" % monster.name
	monster.recolor_primary = Color(255, 255, 255)

	if Tags.Living in monster.tags:
		monster.tags.remove(Tags.Living)

	# Todo- darkinize melee attacks?

	return monster

def Lycanthrope(monster):
	original_sh = monster.shields
	def get_original():
		monster.shields = original_sh
		return monster

	removed_buffs = []
	removable_buff_types = [RespawnAs, SpawnOnDeath, ReincarnationBuff]
	for b in list(monster.buffs):
		for t in removable_buff_types:
			if isinstance(b, t):
				# Already in level- remove buff as normal
				if b.applied:
					monster.remove_buff(b)
				# Not yet in level- just remove from list
				else:
					monster.buffs.remove(b)
				removed_buffs.append(b)

	# TODO- Move all 'on death' buffs from the monster to its wolf- so a lycan bone shambler for instance would not split until its wolf was killed
	def animal_spawn_fn():
		unit = Unit()
		unit.name = "%s Wolf" % monster.name
		unit.asset_name = "wolf"
		unit.max_hp = monster.max_hp // 2

		unit.tags = [Tags.Living, Tags.Dark]
		unit.resists[Tags.Dark] = 50
		unit.is_coward = True

		unit.buffs.append(MatureInto(get_original, 20))
		unit.buffs.extend(removed_buffs)
		unit.recolor_primary = Color(11, 125, 7)
		return unit

	monster.apply_buff(RespawnAs(animal_spawn_fn, name='Wolf'))
	monster.apply_buff(RegenBuff(5))

	adjusted_monster_name = monster.name[0].lower() + monster.name[1:]
	monster.name = "Were%s" % adjusted_monster_name
	monster.recolor_primary =  Color(51, 105, 30)

	if Tags.Dark not in monster.tags:
		monster.tags.append(Tags.Dark)
	if monster.resists[Tags.Dark] <= 50:
		monster.resists[Tags.Dark] = 50

	return monster

def Faetouched(monster):
	monster.shields += 2

	monster.apply_buff(ShieldRegenBuff(2, 5))
	monster.apply_buff(TeleportyBuff(chance=.5))

	monster.resists[Tags.Arcane] += 50
	if Tags.Arcane not in monster.tags:
		monster.tags.append(Tags.Arcane)

	monster.name = "Fae %s" % monster.name
	monster.recolor_primary = Tags.Arcane.color

	return monster

def Flametouched(monster):
	monster.apply_buff(DamageAuraBuff(2, Tags.Fire, 4))

	dmg = monster.max_hp // 10
	dmg = max(dmg, 5)
	monster.apply_buff(DeathExplosion(dmg, 4, Tags.Fire))

	if Tags.Fire not in monster.tags:
		monster.tags.append(Tags.Fire)

	monster.resists[Tags.Fire] += 100

	monster.name = "Burning %s" % monster.name

	monster.recolor_primary = Tags.Fire.color

	return monster

def Trollblooded(monster):
	monster.apply_buff(TrollRegenBuff())

	if Tags.Living not in monster.tags:
		monster.tags.append(Tags.Living)

	monster.name = "Trollblooded %s" % monster.name
	monster.recolor_primary = Color(156, 204, 101)

	return monster

def Slimy(monster):
	candidates = [GreenSlime] # can always spawn greens

	# Can spawn other color slimes based on matching creature tags
	if Tags.Fire in monster.tags:
		candidates.append(RedSlime)
	if Tags.Ice in monster.tags:
		candidates.append(IceSlime)
	if Tags.Arcane in monster.tags:
		candidates.append(VoidSlime)

	monster.apply_buff(SlimyBuff(spawner=candidates))

	if Tags.Slime not in monster.tags: # make it a slime if it isn't one already
		monster.tags.append(Tags.Slime)

	# if SlimeBuff in monster.buffs: # get rid of base slime buff, since this one is stronger, makes propagation of this buff
	# 	monster.remove_buff(SlimeBuff)

	monster.name = "Slimy %s" % monster.name
	monster.recolor_primary = Tags.Slime.color

	#give it proper slime resists
	monster.resists[Tags.Poison] = 100
	if monster.resists[Tags.Physical] < 50:
		monster.resists[Tags.Physical] = 50

	return monster

class SlimyBuff(Buff):

	def __init__(self, spawner, name='slimes'):
		Buff.__init__(self)
		self.name = "Slimy"
		self.color = Tags.Slime.color
		self.spawner = spawner
		self.spawner_name = name
		self.spawns = 1
		self.stack_type = STACK_REPLACE
		self.description = ("50% chance to gain 10% of base hp as current and max hp per turn. Upon reaching double its base HP, splits, releasing 5 slimes.\n"
							"When this creature is damaged, a slime is spawned nearby.")

	def on_applied(self, owner):
		self.start_hp = self.owner.max_hp # return to this on split
		self.spawns = 5 # num of spawns
		self.to_split = self.start_hp * 2 # split when hp reaches this
		self.growth = max(1, self.start_hp // 10) # how much to grow by per tick, little slimes need to grow too so min of 1
		self.description = ("50%% chance to gain %d hp and max hp per turn.  Upon reaching %d HP, splits, releasing %d %s.\n"
							"When this creature is damaged, a slime is spawned nearby.") % (self.growth, self.to_split, self.spawns, self.spawner_name)
		self.owner_triggers[EventOnDamaged] = self.on_damaged

	def on_advance(self):
		if random.random() < 0.5: # 50% chance to activate growth
			return

		if self.owner.cur_hp == self.owner.max_hp: # only grow if they're at max hp
			self.owner.max_hp += self.growth
		self.owner.deal_damage(-self.growth, Tags.Heal, self) # always heal either up to new max, or if already damaged
		if self.owner.cur_hp >= self.to_split: # if they've reached the split threshold
			self.owner.max_hp = self.start_hp # set their hp back to original
			self.owner.cur_hp = self.start_hp
			for i in range(self.spawns): # for how many spawns they will spit out
				p = self.owner.level.get_summon_point(self.owner.x, self.owner.y) # grab a spawn point
				if p:
					unit = random.choice(self.spawner)() # spawn the unit based on the spawner fxn
					unit.team = self.owner.team

					unit.max_hp = max(10, self.owner.max_hp // (self.spawns * 2)) # units hp should be proportionate to how much hp it siphoned off the monster

					self.owner.level.add_obj(unit, p.x, p.y) # spawn it in

	def on_damaged(self, evt):
		p = self.owner.level.get_summon_point(self.owner.x, self.owner.y)  # grab a spawn point
		if p:
			unit = random.choice(self.spawner)()  # spawn the unit based on the spawner fxn
			unit.team = self.owner.team
			self.owner.level.add_obj(unit, p.x, p.y)  # spawn it in

def Stormtouched(monster):
	monster.apply_buff(Thorns(damage=2, dtype=Tags.Lightning))

	lightning_leap = LeapAttack(damage=7, damage_type=Tags.Lightning, range=6)
	lightning_leap.cool_down = 5

	lightning_leap.name = "Lightning Leap"

	monster.spells.insert(0, lightning_leap)

	monster.recolor_primary = Tags.Lightning.color

	if Tags.Lightning not in monster.tags:
		monster.tags.append(Tags.Lightning)
		
	monster.resists[Tags.Lightning] = 100

	monster.name = "Electric %s" % monster.name
	monster.shields += 1

	return monster

def Chaostouched(monster):
	# Throw chaos balls
	# Spawn a cloud of imps on death
	# Resist chaos damage

	if not Tags.Chaos in monster.tags:
		monster.tags.append(Tags.Chaos)

	num_imps = (monster.max_hp // 15) + 1
	num_imps = max(1, num_imps)
	num_imps = min(num_imps, 10)

	death_spawn = SpawnOnDeath(RandomImp, num_imps)
	death_spawn.description = "On death, spawns %d imps" % num_imps

	monster.apply_buff(death_spawn)

	for dtype in [Tags.Dark, Tags.Fire, Tags.Lightning]:
		if monster.resists[dtype] < 50:
			monster.resists[dtype] = 50

	chaos_ball = SimpleRangedAttack(damage=7, range=7, radius=2, damage_type=[Tags.Fire, Tags.Physical, Tags.Lightning])
	chaos_ball.cool_down = 5
	chaos_ball.name = "Chaos Ball"

	monster.add_spell(chaos_ball, prepend=True)
	
	monster.recolor_primary = Tags.Chaos.color

	monster.name = "Infernal %s" % monster.name

	return monster

def Claytouched(monster):

	for dtype in (Tags.Fire, Tags.Lightning, Tags.Physical):
		if monster.resists[dtype] < 50:
			monster.resists[dtype] = 50

	monster.apply_buff(RegenBuff(3))

	monster.name = "Clay %s" % monster.name
	monster.recolor_primary = Color(160, 135, 126)

	return monster

# damage taken is evenly divided amongst all monsters with same name
class HivemindBuff(Buff):

	def on_init(self):
		self.owner_triggers[EventOnPreDamaged] = self.on_damaged
		self.color = Tags.Blood.color
		self.description = "All damage taken is shared evenly amongst all monsters with the same name"
		self.name = "Fleshbound"

	def on_damaged(self, evt):
		# Do not trigger on 0 damage, do not trigger on damage which is 100% resisted
		if evt.unresisted_damage <= 0:
			return

		# Do not redist hivemind damage
		if isinstance(evt.source, HivemindBuff):
			return

		# Shield self to prevent damage
		self.owner.add_shields(1)


		# But then queue new damage afterwards
		self.owner.level.queue_spell(self.dist_damage(evt))

		# Also queue a fake damage event to trigger spells ect
		self.owner.level.event_manager.raise_event(EventOnDamaged(self.owner, evt.damage, evt.damage_type, evt.source))

		
	def dist_damage(self, evt):
		old_damage = evt.damage

		units = [u for u in self.owner.level.units if u.name == self.owner.name]
		if not units:
			return

		new_damage = math.ceil(old_damage / (len(units)))

		for u in units:
			u.deal_damage(new_damage, evt.damage_type, self)
			if u != self.owner:
				self.owner.level.show_path_effect(self.owner, u, Tags.Blood, minor=True, inclusive=False)
		yield
		

def Hivemind(monster):
	monster.apply_buff(HivemindBuff())
	monster.apply_buff(RegenBuff(1))
	monster.recolor_primary = Tags.Blood.color
	monster.name = "Fleshbound %s" % monster.name

	monster.tags.append(Tags.Blood)

	return monster


def get_boss_mod_name(boss_mod):
	example = boss_mod(Unit())
	return example.name.replace("Unnamed", "").strip()

def check_tag(tag, m):
	return tag not in m.tags

def check_ghost(m):
	# Ghostly skeletons ghostly zombies ect is ok but ghostly ghosts is too much and ghostly anything physical immune is kind of pointless
	return m.resists[Tags.Physical] <= 100

def check_troll(m):
	return not m.has_buff(TrollRegenBuff)

# For variants that change how the monster behaves on death, do not apply them to monsters that already do something on death.  Aka no lycanspriggans.
# Do this because 1) its weird and 2) its often way too strong
def check_death_buffs(m):
	death_buffs = [RespawnAs, SpawnOnDeath, SplittingBuff, ReincarnationBuff]
	for b in death_buffs:
		if m.has_buff(b):
			return False
	return True

def check_lich(m):
	return not any([isinstance(s, LichSealSoulSpell) for s in m.spells])

def check_fae(m):
	# Dont make fae out of already teleporty monsters
	return not m.has_buff(TeleportyBuff)

# (spawn modifier function, minimum spawned, weight)

modifiers = [
	(Icy, 4, 2, lambda m: check_tag(Tags.Ice, m)),
	(Lich, 3, 2, check_lich),
	(Ghostly, 6, 2, lambda m: check_tag(Tags.Dark, m)),
	(Faetouched, 4, 2, check_fae),
	(Flametouched, 4, 2, lambda m: check_tag(Tags.Fire, m)),
	(Trollblooded, 4, 2, check_troll),
	(Stormtouched, 4, 2, lambda m: check_tag(Tags.Lightning, m)),
	#(Lycanthrope, 4, 2, check_death_buffs),
	(Metallic, 4, 2, lambda m: check_tag(Tags.Metallic, m)),
	(Immortal, 2, 2, check_death_buffs),
	(Chaostouched, 4, 2, lambda m: check_tag(Tags.Chaos, m)),
	(Claytouched, 5, 2),
	(Hivemind, 5, 2),
	(Slimy, 2, 2)
]

def apply_modifier(modifier, unit, propogate=True, apply_hp_bonus=False):
	# Make sure asset name is implicit since name will be changed
	unit.asset_name = unit.get_asset_name()
	
	# Early out, for instance in recursive case, if already recolored
	if unit.recolor_primary:
		return unit

	if apply_hp_bonus:
		apply_variant_hp_bonus(unit)
	
	if propogate:
		for b_type in [MatureInto, RespawnAs, SpawnOnDeath, ChanceToBecome, GeneratorBuff, Generator2Buff, SplittingBuff, SlimeBuff]:
			buffs = [b for b in unit.buffs if isinstance(b, b_type)]
			for buff in buffs:
				# Capture spawner fn so we dont infinitely recurse
				def make_child(spawner=buff.spawner, modifier=modifier):
					# Special case
					unit = spawner()

					# Apply hp bonus except for splitting buff (since that results in exponentially higher hp values) 
					#  or for SpawnOnDeaths > 2 (stuff llike burning bag of bugs shouldnt spawn enourmous fly swarms, but it should spawn burning ones)
					should_apply_hp_bonus = b_type == SplittingBuff or b_type == SpawnOnDeath and b_type.num_spawns > 2
					apply_modifier(modifier, unit, apply_hp_bonus=should_apply_hp_bonus)

					return unit

				buff.spawner = make_child

		for s in unit.spells:
			if not isinstance(s, SimpleSummon):
				continue

			# Capture spawner fn so we dont infinitely recurse
			# Do not apply hp bonus to all summons as that is just ridiculous
			def make_child(spawner=s.spawn_func, modifier=modifier):
				return apply_modifier(modifier, spawner())

			s.spawn_func = make_child
			s.calc_text()

	modifier(unit)

	return unit

def roll_modifiers(difficulty, spawner, prng=random):
	eligible_modifiers = [t for t in modifiers if len(t) < 4 or t[3](spawner())]

	choices = [m[0] for m in eligible_modifiers]

	weights = [m[2] for m in eligible_modifiers]
	choice = prng.choices(eligible_modifiers, weights=weights)[0]
	return choice

def roll_bosses(difficulty, spawner, prng=random):
	choice = roll_modifiers(difficulty, spawner, prng)
	result = []

	min_extras = 0
	if difficulty > 9:
		min_extras = 1
	if difficulty > 17:
		min_extras = 2
	if difficulty > 21:
		min_extras = 3

	max_extras = 0
	if difficulty > 5:
		max_extras = 1
	if difficulty > 10:
		max_extras = 2
	if difficulty > 13:
		max_extras = 3
	if difficulty > 17:
		max_extras = 4
	if difficulty > 20:
		max_extras = 5

	num_extras = prng.randint(min_extras, max_extras)

	for i in range(choice[1] + num_extras):
		result.append(apply_modifier(choice[0], spawner(), apply_hp_bonus=True))

	return result

if __name__ == "__main__":
	# Test that all modifiers work on all monsters without crashing
	import Monsters
	for s, l in Monsters.spawn_options:
		for m in modifiers:
			unit = s()
			allowed = m[3](unit) if len(m) > 3 else True
			apply_modifier(m[0], unit)
			print("%s, %s" % (unit.name, allowed))