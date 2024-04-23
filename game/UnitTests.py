from Game import *
from Level import *
from Spells import *
#from Encounters import *
from LevelGen import LevelGenerator
from Mutators import *


class TestBuff1(Buff):
	pass

class TestBuff2(Buff):
	pass

def test_buff_spells():
	level = Level(2, 2)

	test_spell = Spell()
	test_spell.name = "test spell"

	test_buff = TestBuff1()
	test_buff.spells = [test_spell]

	test_unit = Unit()
	test_unit.spells = [test_spell]


	level.add_obj(test_unit, 1, 1)
	test_unit.apply_buff(test_buff)
	assert(test_spell in test_unit.spells)

	# unit should still have spell since it had it before the buff
	test_unit.remove_buff(test_buff)
	assert(test_spell in test_unit.spells)

	level.remove_obj(test_unit)

	test_unit2 = Unit()
	level.add_obj(test_unit2, 1, 1)
	test_unit2.apply_buff(test_buff)
	test_unit2.remove_buff(test_buff)

	# This unit should have lost the buff spell since it did not have it to begin with
	assert(test_spell not in test_unit2.spells)

	test_buff2 = TestBuff2()
	test_buff2.spells = [test_spell]

	test_unit2.apply_buff(test_buff)
	test_unit2.apply_buff(test_buff2)

	assert(len(test_unit2.buffs) == 2)

	test_unit2.remove_buff(test_buff)
	assert(test_spell in test_unit2.spells)

	test_unit2.remove_buff(test_buff2)
	assert(test_spell not in test_unit2.spells)

def test_cast(spell, upg=False):
	level = Level(6, 6)
	player = Unit()
	player.max_hp = 6000
	player.team = TEAM_PLAYER
	# The 'player' will use this each turn instead of spell
	player.add_spell(SimpleMeleeAttack(1))
	player.add_spell(spell)

	# Add a spent flameburst for mystic memory or other 0 charge things
	fb = FlameBurstSpell()
	player.add_spell(fb)
	fb.cur_charges = 0

	level.add_obj(player, 1, 1)

	friend = Unit()
	friend.tags = [Tags.Living]
	friend.team = TEAM_PLAYER
	level.add_obj(friend, 1, 2)
	
	if upg:
		for upgrade in spell.spell_upgrades:
			player.apply_buff(upgrade)

	# Make a wall and a chasm for sblast and volcano and maybe other spells
	level.make_wall(1, 0)
	level.make_chasm(0, 1)

	# Checker the board with high hp low damage enemies with each tag
	for tile in level.iter_tiles():
		if tile.x == tile.y == 0:
			continue

		if tile.unit:
			continue

		if ((tile.x + tile.y) % 2 == 0):
			unit = Unit()
			unit.cur_hp = 39
			unit.max_hp	= 40
			unit.tags = [t for t in monster_tags]
			team_idx = ((tile.x + tile.y) % 4) // 2
			unit.team = [TEAM_PLAYER, TEAM_ENEMY][team_idx]

			# Always physical for now- make varied?
			unit.spells.append(SimpleMeleeAttack(1))
			level.add_obj(unit, tile.x, tile.y)

	spell.modify_test_level(level)

	target = None
	if spell.can_target_self:
		target = player
	else:
		targets = [Point(t.x, t.y) for t in level.iter_tiles() if spell.can_cast(t.x, t.y)]
		# IN full mode its ok to have no targets, but we expect them otherwise
		if not targets:
			assert(targets)
		target = targets[-1]
	
	level.act_cast(player, spell, target.x, target.y)
	for i in range(10):
		# This only channels for one turn- thats fine?
		level.advance(full_turn=True)


def test_each_player_spell():

	for upg in [False, True]:
		# To remake skills spells ect
		game = Game()
		for spell in game.all_player_spells:
			print(spell.name)
			test_cast(spell, upg)

class TestBuff3(Buff):

	def on_applied(self, owner):
		self.resists[Tags.Fire] = 1
		self.owner_triggers[EventOnDeath] = self.on_my_death
		self.global_triggers[EventOnSpellCast] = self.on_any_spell_cast

	def on_my_death(self, evt):
		pass

	def on_any_spell_cast(self, evt):
		pass

def test_stairs_with_buff():
	game = Game(generate_level=False)
	game.p1.apply_buff(TestBuff3())
	assert(game.p1.resists[Tags.Fire] == 1)

	#game.change_level()

	assert(game.p1.resists[Tags.Fire] == 1)

	event_manager = game.cur_level.event_manager
	assert(len(event_manager._handlers[EventOnDeath][game.p1]) == 1)
	assert(len(event_manager._handlers[EventOnSpellCast][None]) == 1)


class DamageIncreaser(Buff):

	def modify_spell(self, spell):
		if hasattr(spell, 'damage'):
			spell.damage += 10

	def unmodify_spell(self, spell):
		if hasattr(spell, 'damage'):
			spell.damage -= 10

def test_spell_modifier_buffs():

	#Try adding and removing a modifier buff
	game = Game(generate_level=False)

	buff = DamageIncreaser()

	game.p1.add_spell(FireballSpell())
	game.p1.spells[0].damage = 5

	game.p1.apply_buff(buff)

	assert(game.p1.spells[0].damage == 15)

	game.p1.remove_buff(buff)

	assert(game.p1.spells[0].damage == 5)

	#Try a buff that adds and another that modifies
	game = Game(generate_level=False)

	buff1 = DamageIncreaser()

	spell = FireballSpell()
	spell.damage = 5

	buff2 = Buff()
	buff2.spells = [spell]
	buff2.stack_type = STACK_INTENSITY

	spell2 = LightningBoltSpell()
	spell2.damage = 5
	buff3 = Buff()
	buff3.stack_type = STACK_INTENSITY
	buff3.spells = [spell2]

	buff1.buff_type = BUFF_TYPE_PASSIVE
	buff2.buff_type = BUFF_TYPE_PASSIVE
	buff3.buff_type = BUFF_TYPE_PASSIVE

	game.p1.apply_buff(buff3)
	game.p1.apply_buff(buff1)
	game.p1.apply_buff(buff2)

	assert(game.p1.spells[0].damage == 15)
	assert(game.p1.spells[1].damage == 15)
	game.next_level = Level(5, 5)
	game.deploying = True
	game.try_deploy(0, 0)
	assert(game.p1.spells[0].damage == 15)
	assert(game.p1.spells[1].damage == 15)

	game.p1.remove_buff(buff1)

	assert(game.p1.spells[0].damage == 5)

	game = Game(generate_level=False)

	buff1 = DamageIncreaser()

	spell = FireballSpell()
	spell.damage = 5

	buff1.spells = [spell]
	buff1.buff_type = BUFF_TYPE_PASSIVE

	game.p1.apply_buff(buff1)
	assert(game.p1.spells[0].damage == 15)
	game.next_level = Level(5, 5)
	game.deploying = True
	game.try_deploy(0, 0)
	assert(game.p1.spells[0].damage == 15)

	game.p1.remove_buff(buff1)

	assert(spell.damage == 5)
	assert(game.p1.spells == [])


def test_battle_royale():
	# Add each monster to a level, perma berserk it, see what happens
	game = Game(generate_level=False)

	game.p1.cur_hp = 100000000
	game.p1.max_hp = 100000000

	# Do it 3 times since theres lots of randomness
	for _ in range(3):
		monsters = [s[0]() for s in spawn_options]
		i = 0
		for t in game.cur_level.iter_tiles():
			i += 1
			if not monsters:
				break
			if t.unit:
				continue
			cur_monster = monsters.pop()
			cur_monster.team = [TEAM_PLAYER, TEAM_ENEMY][i % 2]
			game.cur_level.add_obj(cur_monster, t.x, t.y)
			cur_monster.apply_buff(BerserkBuff())

		for i in range(2500):
		
			if game.is_awaiting_input():
				game.try_pass()
			game.advance()	

		for u in game.cur_level.units:
			print(u.name)

def test_cyclops():
	# Test some funny situations involving the red cyclops and his bat

	level = Level(5, 5)
	cyclops = RedCyclops()
	player = Unit()
	player.max_hp = 100
	player.team = TEAM_PLAYER
	player.stationary = True

	goblin = Goblin()

	level.add_obj(cyclops, 0, 0)
	level.add_obj(goblin, 0, 1)
	level.add_obj(player, 4, 4)

	for t in level.iter_tiles():
		if not t.unit:
			level.make_chasm(t.x, t.y)

	# Test 1: NOthing should happen, no room to hit goblin
	level.advance(full_turn=True)

	assert(goblin.cur_hp == goblin.max_hp)
	assert(player.cur_hp == player.max_hp)

	# Test 2: Put a place to hit the goblin to

	level.make_floor(3, 4)

	level.advance(full_turn=True)

	assert(goblin.x == 3)
	assert(goblin.y == 4)
	assert(player.cur_hp < player.max_hp)

	player.cur_hp = player.max_hp

	# Test 3: Put the player next to the cyclops
	level.act_move(player, 0, 1, teleport=True)
	level.make_chasm(3, 4)

	level.advance(full_turn=True)

	assert(player.x == player.y == 4)
	assert(player.cur_hp < player.max_hp)

	# Test 4: Put the player next to cyclops and remove bat point
	player.cur_hp = player.max_hp
	level.act_move(player, 0, 1, teleport=True)
	level.make_chasm(4, 4)

	level.advance(full_turn=True)

	assert(player.x == 0)
	assert(player.y == 1)
	assert(player.cur_hp < player.max_hp)

def test_cat():
	level = Level(5, 5)
	cat = NineTheCat()

	level.add_obj(cat, 0, 0)
	
	for t in level.iter_tiles():
		if not t.unit:
			level.make_chasm(t.x, t.y)

	cat.kill()
	level.advance(full_turn=True)
	assert(cat.cur_hp > 0)
	assert(cat.is_alive())

	cat.kill()
	level.make_floor(4, 4)
	level.make_chasm(0, 0)
	level.advance(full_turn=True)
	assert(cat.cur_hp > 0)
	assert(cat.is_alive())
	assert(cat.x == cat.y == 4)

	level.make_floor(0, 0)
	level.make_floor(0, 1)

	for _ in range(8):
		assert(cat.cur_hp > 0)
		assert(cat.is_alive())
		cat.kill()
		level.advance(full_turn=True)

	assert(cat.cur_hp == 0)
	assert(not cat.is_alive())

	# Make sure nothin funny with the unit list ect
	assert(len(level.units) == 0)
	for t in level.iter_tiles():
		assert(not t.unit)

def test_rare_monsters():
	batch_size = 8
	i = 0
	monsters = list(rare_monsters)
	random.shuffle(monsters)
	while i * batch_size < len(rare_monsters):

		p1 = Unit()

		dtypes = [Tags.Dark, Tags.Physical, Tags.Arcane, Tags.Fire, Tags.Ice, Tags.Lightning]
		for tag in dtypes:
			zap = SimpleRangedAttack(damage=25, range=16, damage_type=tag)
			zap.radius = 3
			zap.cool_down = len(dtypes)
			p1.spells.append(zap)
			zap.beam = True

		p1.max_hp = 100000

		p1.team = TEAM_PLAYER

		p1.buffs.append(TeleportyBuff(radius=15, chance=.1))

		difficulty = 2
		gen = LevelGenerator(difficulty)
		
		gen.num_monsters = 7
		gen.num_generators = 2
		gen.num_open_spaces = 8
		gen.bosses = []

		for e in rare_monsters[i*batch_size:(i+1)*batch_size]:
			print(e[0]().name)
			gen.bosses.append(e[0]())

		gen.num_elites = 0

		level = gen.make_level()
		level.start_pos = gen.empty_spawn_points.pop()
		
		level.spawn_player(p1)

		for _ in range(80):
			level.advance(full_turn=True)

		i += 1


def test_variant_monsters():

	monsters = list(rare_monsters)
	random.shuffle(monsters)
	for monster, var_list in variants.items(): 

		p1 = Unit()

		dtypes = [Tags.Dark, Tags.Physical, Tags.Arcane, Tags.Fire, Tags.Ice, Tags.Lightning]
		for tag in dtypes:
			zap = SimpleRangedAttack(damage=25, range=16, damage_type=tag)
			zap.radius = 3
			zap.cool_down = len(dtypes)
			p1.spells.append(zap)
			zap.beam = True

		p1.max_hp = 100000

		p1.team = TEAM_PLAYER

		p1.buffs.append(TeleportyBuff(radius=15, chance=.99))

		difficulty = 2
		gen = LevelGenerator(difficulty, None)
		
		gen.num_monsters = 7
		gen.num_generators = 2
		gen.num_open_spaces = 8
		gen.bosses = []

		for v in var_list:
			print(v[0]().name)
			gen.bosses.append(v[0]())

		gen.num_elites = 0

		level = gen.make_level()
		level.start_pos = gen.empty_spawn_points.pop()
		
		level.spawn_player(p1)

		for _ in range(35):
			level.advance(full_turn=True)

def test_predictable_fight():

	level = Level(5, 5)
	u1 = Unit()
	u1.max_hp = 10
	u1.spells = [SimpleRangedAttack(damage=5, range=5)]
	u1.team = TEAM_PLAYER

	u2 = Unit()
	u2.max_hp = 10
	u2.spells = [SimpleRangedAttack(damage=5, range=5)]
	u2.team = TEAM_ENEMY

	level.add_obj(u1, 0, 0)
	level.add_obj(u2, 3, 3)

	level.advance(full_turn=True)
	assert(u1.cur_hp == u2.cur_hp == 5)

def test_long_mordred():
	print("Running test")
	level = Level(33, 33)
	u1 = Unit()
	level.gen_params = LevelGenerator(19)
	u1.max_hp = 100000
	u1.team = TEAM_PLAYER
	level.player_unit = u1

	u2 = Apep()
	u2.team = TEAM_ENEMY

	level.add_obj(u1, 0, 0)
	level.add_obj(u2, 25, 25)

	turns = 35
	for i in range(turns):
		level.advance(full_turn=True)
		print("Mordred turn: %d" % i)

def test_levelgen():
	p1 = Unit()
	for i in range(50):
		print("Generating level %d" % i)
		difficulty = (i % 25) + 1
		level = LevelGenerator(difficulty=i).make_level()

def test_seeded_levelgen():

	for diff, seed in [(10, .5234), (1, 3), (1, 5), (20, .123123), (25, .135599)]:

		generator = LevelGenerator(difficulty=diff, seed=seed)
		l1 = generator.make_level()

		generator = LevelGenerator(difficulty=diff, seed=seed)
		l2 = generator.make_level()
		print("Comparing levelgen for difficutly %d seed %f" % (diff, seed))

		for i in range(LEVEL_SIZE-1):
			for j in range(LEVEL_SIZE-1):
				t1 = l1.tiles[i][j]
				t2 = l2.tiles[i][j]

				if t1.can_walk != t2.can_walk or t1.can_see != t2.can_see:
					print("Tile discrepency at %d, %d" % (i, j))
					assert(False)
				
				if t1.prop:
					if not t2.prop:
						print("Map 1 has a %s at %d, %d, Map 2 has nothing" % (t1.prop.name, i, j))
						assert(t2.prop)
					if not (t1.prop.name == t2.prop.name):
						print("Map 1 has a %s at %d, %d, Map 2 has %s" % (t1.prop.name, i, j, t2.prop.name))
						assert(t1.prop.name == t2.prop.name)

				if t1.unit:
					if not t2.unit:
						print("Map 1 has a %s at %d, %d, Map 2 has nothing" % (t1.unit.name, i, j))
						assert(t2.unit)
					if not (t1.unit.name == t2.unit.name):
						print("Map 1 has a %s at %d, %d, Map 2 has %s" % (t1.unit.name, i, j, t2.unit.name))
						assert(t1.unit.name == t2.unit.name)

def test_trials():
	for trial in all_trials:
		print("Testing trial: %s" % trial.name)
		game = Game(save_enabled=True, mutators=trial.mutators, trial_name=trial.name)
		game.p1.is_player_controlled = False
		game.p1.add_spell(SimpleRangedAttack(damage=10, damage_type=Tags.Physical, range=5))

		for i in range(25):
			game.cur_level.advance(full_turn=True)

def test_weekly_mods():
	for mod in weekly_mods:
		print("Testing mutator: %s" % mod.description)
		game = Game(mutators=[mod])
		game.p1.is_player_controlled = False

		game.p1.add_spell(SimpleRangedAttack(damage=10, damage_type=Tags.Physical, range=5))

		for i in range(25):
			game.cur_level.advance(full_turn=True)

def test_sprites():
	to_check = []
	for m, _ in spawn_options:
		to_check.append(m())

	for monster, var_list in variants.items():
		for v in var_list:
			to_check.append(v[0]())

	for m, _, _, _, _ in rare_monsters:
		to_check.append(m())

	print(len(to_check))
	for m in to_check:
		path = os.path.join('rl_data', 'char', m.get_asset_name() + '.png')
		assert(os.path.exists(path))


def run_tests():
	test_sprites()

	# Seeded levels are currently broken, trials are temp, fix this later
	#test_weekly_mods()
	#test_trials()
	#test_seeded_levelgen()

	test_each_player_spell()
	test_rare_monsters()

	#test_variant_monsters() 

	test_spell_modifier_buffs()
	test_cyclops()
	test_cat()
	test_buff_spells()
	test_stairs_with_buff()
	test_battle_royale()
	test_long_mordred()
	test_predictable_fight()
	test_levelgen()

if __name__ == "__main__":
	run_tests()