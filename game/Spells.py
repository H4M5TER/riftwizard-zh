from Level import *
from Monsters import *
from copy import copy
import math
import itertools
import text
import BossSpawns
import loc

ignore_los_upgrade = "施放这个法术不再需要视线"

# not in game
class FlameTongue(Spell):

	def on_init(self):
		self.name = "Flame Tongue"
		self.level = 1
		self.damage = 6
		self.max_charges = 28
		self.range = 5

		self.tags = [Tags.Fire, Tags.Sorcery]

		self.description = "Deal fire damage in a beam"

		self.upgrades['range'] = (3, 1)
		self.upgrades['damage'] = (5, 1)

	def get_impacted_tiles(self, x, y):
		start = Point(self.caster.x, self.caster.y)
		target = Point(x, y)

		for point in Bolt(self.caster.level, start, target):
			yield point

	def cast(self, x, y):
		start = Point(self.caster.x, self.caster.y)
		target = Point(x, y)

		for point in self.get_impacted_tiles(x, y):
			self.caster.level.deal_damage(point.x, point.y, self.get_stat('damage'), Tags.Fire, self)

		yield


class FireballSpell(Spell):

	def on_init(self):
		self.radius = 2
		self.damage = 9
		self.name = "Fireball"
		self.max_charges = 18
		self.range = 8
		self.element = Tags.Fire

		self.damage_type = Tags.Fire

		self.whiteflame_bonus = 0
		self.blueflame_bonus = 0

		self.tags = [Tags.Fire, Tags.Sorcery]
		self.level = 1

		self.upgrades['chaos'] = (1, 5, "Chaos Ball", "[Fireball:spell]随机造成[physical]、[lightning]或[fire]伤害。[Fireball:spell]会对目标造成其抗性最低类型的伤害。", "damage type")
		self.upgrades['ash'] = (1, 2, "Ash Ball", "[Fireball:spell]使目标[blind]和[poisoned] [4:duration]", "damage type")
		self.upgrades['meteor'] = (1, 3, "Meteor", "[Fireball:spell]中心的单位受到额外一份[physical]伤害并且被[stun] [3:duration]。")

	def get_description(self):
		return "对[{radius}:radius]内的单位造成 [{damage}:fire]。".format(**self.fmt_dict())

	def cast(self, x, y):
		dtypes = [Tags.Fire]
		if self.get_stat('chaos'):
			dtypes = [Tags.Fire, Tags.Lightning, Tags.Physical]

		damage = self.get_stat('damage')

		target = Point(x, y)

		if self.get_stat('meteor'):
			self.caster.level.deal_damage(target.x, target.y, damage, Tags.Physical, self)
			unit = self.caster.level.get_unit_at(target.x, target.y)
			if unit:
				unit.apply_buff(Stun(), self.get_stat('duration', base=2))

		for stage in Burst(self.caster.level, target, self.get_stat('radius')):
			for point in stage:

				random.shuffle(dtypes)
				unit = self.caster.level.get_unit_at(point.x, point.y)
				if unit:
					dtype = min(((unit.resists[t], t) for t in dtypes), key=lambda t : t[0])[1]
				else:
					dtype = random.choice(dtypes)

				self.caster.level.deal_damage(point.x, point.y, damage, dtype, self)

				if self.get_stat('ash') and unit:
					unit.apply_buff(BlindBuff(), self.get_stat('duration', base=5))
					unit.apply_buff(Poison(), self.get_stat('duration', base=5))

			yield

		return

	def get_impacted_tiles(self, x, y):
		return [p for stage in Burst(self.caster.level, Point(x, y), self.get_stat('radius')) for p in stage]

class MeteorShower(Spell):

	def on_init(self):
		self.name = "Rain of Fire"

		self.num_targets = 9
		self.storm_radius = 7
	
		self.radius = 2
		self.range = RANGE_GLOBAL

		self.max_charges = 1

		self.tags = [Tags.Fire, Tags.Sorcery]
		self.level = 8

		self.max_channel = 10

		self.upgrades['chaos'] = (1, 7, "Chaos Storm", "每颗陨石对[4:radius]内的 [3:num_targets]施放你的[Annihilate:spell]")
		self.upgrades['dragons'] = (1, 8, "Rain of Dragons", "每颗陨石有 50% 概率施放你的[Fire Drake:spell]")
		self.upgrades['pyrostatic'] = (1, 8, "Pyrostatic Storm", "每颗陨石对其目标地块视界内至多 [2:num_targets]敌人施放你的[Lightning Bolt:spell]")

		self.stats.append('storm_radius')


	def get_description(self):
		return ("每回合对[{storm_radius}:radius]内的随机格子砸下 [{num_targets} 颗陨石:num_targets]\n"
				"每颗陨石产生和你的火球术一样的效果\n"
				"陨石摧毁墙壁\n"
				+ loc.clauses['channel'] % "[{max_channel}:duration]").format(**self.fmt_dict())

	def get_impacted_tiles(self, x, y):
		return self.caster.level.get_points_in_ball(x, y, self.get_stat('storm_radius') + self.get_stat('radius'))

	def cast(self, x, y, channel_cast=False):

		if not channel_cast:
			self.caster.apply_buff(ChannelBuff(self.cast, Point(x, y)), self.get_stat('max_channel'))
			return

		points_in_ball = list(self.caster.level.get_points_in_ball(x, y, self.get_stat('storm_radius')))

		if self.owner.level.tiles[x][y].is_wall():
			self.owner.level.make_floor(x, y)

		fireball = self.owner.get_or_make_spell(FireballSpell)
		fire_drake = self.owner.get_or_make_spell(SummonFireDrakeSpell)
		annihilate = self.owner.get_or_make_spell(AnnihilateSpell)
		lbolt = self.owner.get_or_make_spell(LightningBoltSpell) 

		for _ in range(self.get_stat('num_targets')):
			target = random.choice(points_in_ball)
			for _ in self.owner.level.act_cast(self.owner, fireball, target.x, target.y, pay_costs=False, queue=False):
				yield

			if self.get_stat('chaos'):
				targets = self.owner.level.get_units_in_ball(target, self.get_stat('radius', base=4))
				targets = [t for t in targets if are_hostile(self.caster, t)]
				random.shuffle(targets)
				targets = targets[:self.get_stat('num_targets', base=3)]
				for t in targets:
					annihilate.origin_point = target
					for _ in self.owner.level.act_cast(self.owner, annihilate, t.x, t.y, pay_costs=False, queue=False):
						pass

			if self.get_stat('dragons'):
				if random.random() < .50:
					for _ in self.owner.level.act_cast(self.owner, fire_drake, target.x, target.y, pay_costs=False, queue=False):
						pass

			if self.get_stat('pyrostatic'):
				for _ in range(self.get_stat('num_targets', base=2)):
					targets = self.owner.level.get_units_in_los(target)
					targets = [t for t in targets if are_hostile(t, self.owner)]
					if not targets:
						continue

					t = random.choice(targets)
					lbolt.origin_point = target
					for _ in self.owner.level.act_cast(self.owner, lbolt, t.x, t.y, pay_costs=False, queue=False):
						pass

class LightningBoltSpell(Spell):
 
	def on_init(self):
		self.damage = 12
		self.range = 11
		self.name = "Lightning Bolt"
		self.max_charges = 18
		self.element = Tags.Lightning

		self.tags = [Tags.Lightning, Tags.Sorcery]
		self.level = 1

		self.upgrades['channel'] = (1, 2, "Channeling", loc.clauses["channel"] % "[10:duration]")
		self.upgrades['scrolls'] = (1, 7, "Electric Ink", "每当[Lightning Bolt:spell]击杀一个单位，生成一个可以再次施放你的[Lightning Bolt:spell]的[Living Scroll of Lightning:unit]")
		self.upgrades['energy'] = (1, 6, "Energy Bolt", "[Lightning Bolt:spell]额外造成一份[arcane]伤害")

		self.suicide = False
		self.damage_type = Tags.Lightning # For scroll AI

		# Generally shoot from the caster but not always
		self.origin_point = None

	def get_description(self):
		return "对一条直线造成 [{damage}:lightning]".format(**self.fmt_dict())

	def scroll(self):
		scroll = LivingLightningScroll()
		scroll.spells = []
		apply_minion_bonuses(self, scroll)

		# Make sure that the parent is the original wizard, not the current living spell scroll
		spell_parent = self.statholder if self.statholder else self.caster

		spell = grant_minion_spell(LightningBoltSpell, scroll, spell_parent, 0)
		spell.suicide = True
		return scroll

	def cast(self, x, y, channel_cast=False):

		if self.get_stat('channel') and not channel_cast:
			check_fn = self.should_ai_channel if not self.caster.is_player_controlled else None
			self.caster.apply_buff(ChannelBuff(self.cast, Point(x, y), channel_check=check_fn), 10)
			return

		start = self.origin_point or self.caster
		target = Point(x, y)

		dtypes = [Tags.Lightning]

		if self.get_stat('chaos'):
			dtypes = [Tags.Lightning, Tags.Fire]
		if self.get_stat('energy'):
			dtypes = [Tags.Lightning, Tags.Arcane]

		for dtype in dtypes:
			for point in Bolt(self.caster.level, start, target):

				unit = self.owner.level.get_unit_at(*point)
				self.caster.level.deal_damage(point.x, point.y, self.get_stat('damage'), dtype, self)

				if unit and self.get_stat('scrolls') and not unit.is_alive():
					scroll = self.scroll()
					self.summon(scroll, target=unit)

			for i in range(4):
				yield

		# For scrolls
		if self.suicide:
			self.caster.kill()

	def get_impacted_tiles(self, x, y):
		start = Point(self.caster.x, self.caster.y)
		target = Point(x, y)
		return list(Bolt(self.caster.level, start, target))

	def should_ai_channel(self, target):
		tiles = self.get_impacted_tiles(target.x, target.y)
		units = [self.owner.level.get_unit_at(t.x, t.y) for t in tiles]
		units = [u for u in units if u]
		return any(are_hostile(self.caster, u) and u.resists[Tags.Lightning] < 100 for u in units)

class AnnihilateSpell(Spell):

	def on_init(self):
		self.range = 6
		self.name = "Annihilate"
		self.max_charges = 10
		self.damage = 16
		self.tags = [Tags.Chaos, Tags.Sorcery]
		self.level = 2
		self.cascade_range = 0  # Should be cascade range
		self.arcane = 0
		self.dark = 0

		self.upgrades['cascade_range'] =  (3, 3, 'Cascade', '[Annihilate:spell]击杀主目标之后会选择周围的目标轰击')
		self.upgrades['extra'] =  (1, 2, 'Comprehensive Annihilation', '[Annihilate:spell]额外使用[dark]和[arcane]轰击')
		self.upgrades['doom_storm'] =  (1, 3, 'Doom Storm', '[Annihilate:spell]会对目标地块视界内至多 [5:num_targets]风暴地块连锁施放') # TODO

		self.origin_point = None

	def get_description(self):
		desc = "对目标造成 [{damage}:fire], [{damage}:lightning], [{damage}:physical]"
		return desc.format(**self.fmt_dict())

	def cast(self, x, y):

		for p in self.owner.level.get_points_in_line(self.origin_point or self.caster, Point(x, y))[1:-1]:
			self.owner.level.show_effect(p.x, p.y, Tags.Chaos, minor=True)

		dtypes = [Tags.Fire, Tags.Lightning, Tags.Physical]
		if self.get_stat('extra'):
			dtypes.append(Tags.Arcane)
			dtypes.append(Tags.Dark)
	

		targets = [Point(x, y)]
		if self.get_stat('doom_storm'):
			potential_targets = [t for t in self.owner.level.get_units_in_los(Point(x, y))]

			def is_storm(t):
				storm_types = [BlizzardCloud, StormCloud]
				return self.owner.level.tiles[t.x][t.y].cloud and type(self.owner.level.tiles[t.x][t.y].cloud) in storm_types

			potential_targets = [t for t in potential_targets if is_storm(t)]
			random.shuffle(potential_targets)

			targets.extend(potential_targets[:self.get_stat('num_targets', base=3)])

		for cur_target in targets:
			for dtype in dtypes:
				if self.get_stat('cascade_range') and not self.caster.level.get_unit_at(cur_target.x, cur_target.y):
					other_targets = self.caster.level.get_units_in_ball(cur_target, self.get_stat('cascade_range'))
					other_targets = [t for t in other_targets if self.caster.level.are_hostile(t, self.caster)]
					if other_targets:

						new_target = random.choice(other_targets)
						for p in self.owner.level.get_points_in_line(cur_target, new_target)[1:-1]:
							self.owner.level.show_effect(p.x, p.y, Tags.Chaos, minor=True)
						cur_target = random.choice(other_targets)

				self.caster.level.deal_damage(cur_target.x, cur_target.y, self.get_stat('damage'), dtype, self)
				for i in range(2):
					yield

class MegaAnnihilateSpell(AnnihilateSpell):

	def on_init(self):
		self.damage = 99
		self.max_charges = 3
		self.name = "Mega Annihilate"
		
		self.tags = [Tags.Chaos, Tags.Sorcery]
		self.level = 5

		self.cascade_range = 0
		self.arcane = 0
		self.dark = 0

		self.upgrades['cascade_range'] =  (4, 3, 'Cascade', '[Mega Annihilate:spell]击杀主目标之后会选择周围的目标轰击')
		self.upgrades['dark'] =  (1, 2, 'Dark Annihilation', '[Mega Annihilate:spell]额外使用[dark]伤害轰击')
		self.upgrades['arcane'] =  (1, 2, 'Arcane Annihilation', '[Mega Annihilate:spell]额外使用[arcane]伤害轰击')

		self.origin_point = None

class Teleport(Spell):

	def on_init(self):
		self.range = 16
		self.requires_los = False
		self.name = "Teleport"
		self.max_charges = 1

		self.tags = [Tags.Sorcery, Tags.Arcane, Tags.Translocation]
		self.level = 5

		self.upgrades['quick_cast'] = (1, 4, "Quickcast", "[Teleport:spell]不会结束你的回合")
		self.upgrades['group_teleport'] = (1, 4, "Group Teleport", "[Teleport:spell]会携带至多 [10:num_targets]友军单位")
		self.upgrades['void_teleport'] = (1, 5, "Void Teleport", "[Teleport:spell]对目标地块视界内的所有敌人造成和它的最大充能数相同的[arcane]伤害")

	def get_description(self):
		return "Teleport to target tile"

	def can_cast(self, x, y):
		return Spell.can_cast(self, x, y) and self.caster.level.can_move(self.caster, x, y, teleport=True)

	def cast(self, x, y):
		start_loc = Point(self.caster.x, self.caster.y)

		self.caster.level.show_effect(self.caster.x, self.caster.y, Tags.Translocation)
		p = self.caster.level.get_summon_point(x, y)
		if p:
			yield self.caster.level.act_move(self.caster, p.x, p.y, teleport=True)
			self.caster.level.show_effect(self.caster.x, self.caster.y, Tags.Translocation)
			if self.get_stat('group_teleport'):
				eligible_targets = [u for u in self.caster.level.units if not are_hostile(u, self.caster) and u != self.caster]
				if eligible_targets:
					random.shuffle(eligible_targets)
					for i in range(min(len(eligible_targets), self.get_stat('num_targets', base=10))):
						teleport_point = self.caster.level.get_summon_point(x, y)
						if teleport_point:
							yield self.caster.level.act_move(eligible_targets[i], teleport_point.x, teleport_point.y, teleport=True)
							self.caster.level.show_effect(eligible_targets[i].x, eligible_targets[i].y, Tags.Translocation)

		if self.get_stat('void_teleport'):
			for unit in self.owner.level.get_units_in_los(self.caster):
				if are_hostile(self.owner, unit):
					unit.deal_damage(self.get_stat('max_charges'), Tags.Arcane, self)

		if self.get_stat('lightning_blink') or self.get_stat('dark_blink'):
			dtype = Tags.Lightning if self.get_stat('lightning_blink') else Tags.Dark
			damage = math.ceil(2*distance(start_loc, Point(x, y)))
			for stage in Burst(self.caster.level, Point(x, y), 3):
				for point in stage:
					if point == Point(x, y):
						continue
					self.caster.level.deal_damage(point.x, point.y, damage, dtype, self)

		if self.get_stat('dispersal'):
			disperse = self.caster.get_or_make_spell(DispersalSpell)
			self.caster.level.act_cast(self.caster, disperse, p.x, p.y, pay_costs=False)

		if self.get_stat('thunder'):
			tstrike = self.caster.get_or_make_spell(ThunderStrike)
			targets = [u for u in self.owner.level.units if tstrike.can_cast(u.x, u.y) and are_hostile(u, self.caster)]
			random.shuffle(targets)
			targets.sort(key=lambda u: distance(u, self.caster))
			for t in targets[:self.get_stat('num_targets', base=2)]:
				self.caster.level.act_cast(self.caster, tstrike, t.x, t.y, pay_costs=False)

	def get_ai_target(self):
		points = [p for p in self.owner.level.get_points_in_ball(self.owner.x, self.owner.y, self.get_stat('range'))]
		points = [p for p in points if self.can_cast(p.x, p.y)]

		if not points:
			return None

		return random.choice(points)


class BlinkSpell(Teleport):

	def on_init(self):
		self.range = 6
		self.requires_los = True
		self.name = "Blink"
		self.max_charges = 6
		self.tags = [Tags.Arcane, Tags.Sorcery, Tags.Translocation]
		self.level = 3

		self.upgrades['requires_los'] = (-1, 2, "Blindcasting", ignore_los_upgrade)
		self.upgrades['dispersal'] = (1, 2, "Dissolution", "施放[Blink:spell]一同施放[Disperse:spell]")
		self.upgrades['thunder'] = (1, 2, "Thunderblink", "施放[Blink:spell]会对视线内最近的两个敌人施放[Thunder Strike:spell]")

class FlameGateBuff(Buff):

	def __init__(self, spell):
		Buff.__init__(self)
		self.name = "Flame Gate"
		self.spell = spell
		self.buff_type = BUFF_TYPE_BLESS
		self.asset = ['status', 'flame_gate']
		self.cast = True
		self.description = "每当你施放一个[fire]法术，在目标地块附近生成一个[Fire Elemental:unit]\n\n这个效果在你移动或施放[fire]之外的法术时结束"

	def on_applied(self, owner):
		self.owner_triggers[EventOnSpellCast] = self.on_spell_cast
		self.owner_triggers[EventOnPass] = self.on_pass
		self.color = Color(255, 0, 0)

	def on_advance(self):
		if self.cast == False:
			self.owner.remove_buff(self)
		self.cast = False

	def on_spell_cast(self, spell_cast_event):
		if Tags.Fire in spell_cast_event.spell.tags:
			self.owner.level.queue_spell(self.make_elemental(spell_cast_event))
			self.cast = True

	def on_pass(self, evt):
		if self.owner.has_buff(ChannelBuff):
			self.cast = True

	def make_elemental(self, spell_cast_event):
		if Tags.Fire in spell_cast_event.spell.tags:
			elemental = Unit()
			elemental.name = 'Fire Elemental'
			elemental.sprite.char = 'E'
			elemental.sprite.color = Color(255, 0, 0)
			# TODO
			elemental.spells.append(SimpleRangedAttack("Elemental Fire", self.spell.get_stat('minion_damage'), Tags.Fire, self.spell.get_stat('minion_range'), radius=self.spell.get_stat('radius')))
			if self.spell.get_stat('cast_eye'):
				grant_minion_spell(EyeOfFireSpell, elemental, self.spell.caster, cool_down=10)
			elemental.resists[Tags.Fire] = 100
			elemental.resists[Tags.Physical] = 50
			elemental.resists[Tags.Ice] = -100
			elemental.turns_to_death = self.spell.get_stat('minion_duration')
			elemental.max_hp = self.spell.get_stat('minion_health')
			elemental.team = self.owner.team
			elemental.tags = [Tags.Elemental, Tags.Fire]
			self.spell.summon(elemental, target=spell_cast_event)
		yield

class StarfireGateBuff(Buff): #I separated this into a separate buff so that I wasn't flooding FlameGateBuff with if statements and ternary operators

	def __init__(self, spell):
		Buff.__init__(self)
		self.name = "Starfire Gate"
		self.spell = spell
		self.buff_type = BUFF_TYPE_BLESS
		self.asset = ['status', 'flame_gate']
		self.cast = True
		self.description = "每当你施放一个[fire]或[arcane]法术，在目标地块附近生成一个[Starfire Elemental:unit]\n\n这个效果在你移动或施放[fire]或[arcane]之外的法术时失效"

	def on_applied(self, owner):
		self.owner_triggers[EventOnSpellCast] = self.on_spell_cast
		self.owner_triggers[EventOnPass] = self.on_pass
		self.color = Color(255, 0, 0)

	def on_advance(self):
		if self.cast == False:
			self.owner.remove_buff(self)
		self.cast = False

	def on_spell_cast(self, spell_cast_event):
		if Tags.Fire in spell_cast_event.spell.tags or Tags.Arcane in spell_cast_event.spell.tags:
			self.owner.level.queue_spell(self.make_elemental(spell_cast_event))
			self.cast = True

	def on_pass(self, evt):
		if self.owner.has_buff(ChannelBuff):
			self.cast = True

	def make_elemental(self, spell_cast_event):
		if Tags.Fire in spell_cast_event.spell.tags or Tags.Arcane in spell_cast_event.spell.tags:
			elemental = Unit()
			elemental.name = 'Starfire Elemental'
			elemental.sprite.char = 'E'
			elemental.sprite.color = Color(255, 0, 0)
			elemental.asset_name = 'starfire_elemental'
			# TODO
			elemental.spells.append(SimpleRangedAttack("Elemental Starfire", self.spell.get_stat('minion_damage'), [Tags.Fire, Tags.Arcane], self.spell.get_stat('minion_range'), radius=self.spell.get_stat('radius')))
			elemental.resists[Tags.Fire] = 100
			elemental.resists[Tags.Arcane] = 100
			elemental.resists[Tags.Physical] = 50
			elemental.resists[Tags.Ice] = -100
			elemental.turns_to_death = self.spell.get_stat('minion_duration')
			elemental.max_hp = self.spell.get_stat('minion_health')
			elemental.team = self.owner.team
			elemental.tags = [Tags.Elemental, Tags.Fire, Tags.Arcane]
			elemental.shields = 1
			self.spell.summon(elemental, target=spell_cast_event)
		yield

class FlameGateSpell(Spell):

	def on_init(self):
		self.range = 0
		self.max_charges = 4
		self.name = "Flame Gate"
		self.minion_duration = 9
		self.tags = [Tags.Fire, Tags.Enchantment, Tags.Conjuration]
		self.level = 3
		self.radius = 0 #This makes it have a radius in get_impacted_tiles but this way it will be affected by trinkets that effect Fire and Enchantment spells

		self.minion_damage = 7
		self.minion_health = 22
		self.minion_range = 4

		self.upgrades['radius'] = (1, 3, "Burst Fire", "[Fire Elemental:unit]的攻击获得[1:radius]")
		self.upgrades['cast_eye'] = (1, 5, "Eye Gate", "[Fire Elemental:unit]被召唤时施放你的[Eye of Fire:spell]")
		self.upgrades['starfire_summon'] = (1, 5, "Starfire Gate", "现在[Flame Gate:spell]会在你施放[fire]或[arcane]法术时召唤[Starfire Elemental:unit]\n不会在你施放[arcane]法术时结束")

	def get_description(self):
		return ("每当你施放一个[fire]法术，在目标地块附近生成一个[Fire Elemental:unit]\n"
				"[Fire Elemental:unit]有 [{minion_health}:minion_health], [100% 火焰抗性:fire], [50% 物理抗性:physical], [-50% 寒冰抗性:ice]\n"
				"[Fire Elemental:unit]的攻击造成 [{minion_damage}:fire]、射程 [{minion_range}:minion_range]\n"
				"[Fire Elemental:unit]在 [{minion_duration}:minion_duration]后消失\n"
				"这个效果在你移动或施放[fire]之外的法术时失效").format(**self.fmt_dict())

	def cast(self, x, y):
		if self.get_stat('starfire_summon'):
			self.caster.apply_buff(StarfireGateBuff(self), 0)
		else:
			self.caster.apply_buff(FlameGateBuff(self), 0)
		yield

	def get_fire_elemental(self):
		elemental = Unit()
		elemental.name = 'Fire Elemental'
		elemental.sprite.char = 'E'
		elemental.sprite.color = Color(255, 0, 0)
		elemental.spells.append(SimpleRangedAttack("Elemental Fire", self.get_stat('minion_damage'), Tags.Fire, self.get_stat('minion_range')))
		elemental.resists[Tags.Fire] = 100
		elemental.resists[Tags.Physical] = 50
		elemental.resists[Tags.Ice] = -100
		elemental.turns_to_death = self.get_stat('minion_duration')
		elemental.max_hp = self.get_stat('minion_health')
		elemental.team = self.owner.team
		elemental.tags = [Tags.Elemental, Tags.Fire]
		return elemental

	def get_starfire_elemental(self):
		elemental = Unit()
		elemental.name = 'Starfire Elemental'
		elemental.sprite.char = 'E'
		elemental.sprite.color = Color(255, 0, 0)
		elemental.asset_name = 'starfire_elemental'
		elemental.spells.append(SimpleRangedAttack("Elemental Starfire", self.get_stat('minion_damage'), [Tags.Fire, Tags.Arcane], self.get_stat('minion_range')))
		elemental.resists[Tags.Fire] = 100
		elemental.resists[Tags.Arcane] = 100
		elemental.resists[Tags.Physical] = 50
		elemental.resists[Tags.Ice] = -100
		elemental.turns_to_death = self.get_stat('minion_duration')
		elemental.max_hp = self.get_stat('minion_health')
		elemental.team = self.owner.team
		elemental.tags = [Tags.Elemental, Tags.Fire, Tags.Arcane]
		elemental.shields = 1
		return elemental

	def get_extra_examine_tooltips(self):
		return [self.get_fire_elemental(), self.spell_upgrades[0], self.spell_upgrades[1], self.spell_upgrades[2], self.get_starfire_elemental()]

class LightningFormBuff(Buff):

	def __init__(self, spell, phys_immune = False):
		Buff.__init__(self)
		self.spell = spell
		self.transform_asset_name = "player_lightning_form"
		self.phys_immune = phys_immune
		self.name = "Lightning Form"
		self.buff_type = BUFF_TYPE_BLESS
		self.asset = ['status', 'lightning_form']
		self.color = Tags.Lightning.color
		self.description = "你施放一个[lightning]法术时，如果目标地块是空的，传送到目标地块。\n\n这个效果在你移动或施放[lightning]之外的法术时失效"
		self.cast = True
		self.stack_type = STACK_TYPE_TRANSFORM
		
		self.check_tags = [Tags.Lightning]
		if self.spell.get_stat('fire_form'):
			self.check_tags = [Tags.Lightning, Tags.Fire]
		
		self.linger = 3
		

	def on_advance(self):
		if self.cast == False:
			if not self.spell.get_stat('lingering_form'):
				self.owner.remove_buff(self)
			else:
				self.linger -= 1
			if self.linger <= 0:
				self.owner.remove_buff(self)
		else:
			self.linger = 3
		self.cast = False
		
		if self.spell.get_stat('crackling_aura'):
			targets = self.owner.level.get_units_in_ball(self.owner, self.spell.get_stat('radius', base=5))
			random.shuffle(targets)
			
			for i in range(min(self.spell.get_stat('num_targets', base=4), len(targets))):
				if targets[i] and targets[i].is_alive():
					targets[i].deal_damage(5, Tags.Lightning, self.spell)

	def on_applied(self, caster):
		self.resists[Tags.Lightning] = 100
		self.resists[Tags.Physical] = 100
		if self.spell.get_stat('fire_form'):
			self.resists[Tags.Fire] = 100

		self.owner_triggers[EventOnSpellCast] = self.on_spell_cast
		self.owner_triggers[EventOnPass] = self.on_pass
		self.color = Color(122, 122, 200)

	def on_spell_cast(self, spell_cast_event):
		cast = False
		for tag in self.check_tags:
			if tag in spell_cast_event.spell.tags:
				cast = True
				if self.owner.level.can_move(self.owner, spell_cast_event.x, spell_cast_event.y, teleport=True):
					self.owner.level.queue_spell(self.do_teleport(spell_cast_event.x, spell_cast_event.y))
		self.cast = cast

	def on_pass(self, evt):
		if self.owner.has_buff(ChannelBuff):
			self.cast = True

	def do_teleport(self, x, y):
		if self.owner.level.can_move(self.owner, x, y, teleport=True):
			yield self.owner.level.act_move(self.owner, x, y, teleport=True)

class LightningFormSpell(Spell):

	def on_init(self):
		self.range = 0
		self.max_charges = 3
		self.name = "Lightning Form"
		self.physical_resistance = 0
		
		self.tags = [Tags.Lightning, Tags.Enchantment]
		self.level = 4

		self.upgrades['lingering_form'] = (1, 2, "Lingering Form", "[Lightning Form:spell]在你未施放[lightning]法术时持续 [3:duration] 而不是马上消失")
		self.upgrades['fire_form'] = (1, 3, "Fire Form", "同样对[fire]法术生效\n获得 [100% 火焰抗性:fire]")
		self.upgrades['crackling_aura'] = (1, 4, "Crackling Aura", "在[Lightning Form:spell]中，每回合对[5:radius]内的 [4:num_targets]敌人造成 [5:lightning]")

	def cast(self, x, y):
		self.caster.apply_buff(LightningFormBuff(self))
		yield

	def get_description(self):
		return ("你施放一个[lightning]法术时，如果目标地块是空的，传送到目标地块。\n"
				"获得 [100% 闪电抗性:lightning]\n"
				"获得 [100% 物理抗性:physical]\n"
				"这个效果在你移动或施放[lightning]之外的法术时失效").format(**self.fmt_dict())


class VoidBeamResistDebuff(Buff):

	def on_init(self):
		self.buff_type = BUFF_TYPE_CURSE
		self.color = Tags.Arcane.color
		self.name = "Arcane Vulnerability" # TODO
		self.stack_type = STACK_INTENSITY
		self.resists[Tags.Arcane] = -25

class VoidBeamSpell(Spell):

	def on_init(self):
		self.range = 15
		self.max_charges = 6
		self.name = "Void Beam"
		self.requires_los = False
		self.damage = 25
		
		self.tags = [Tags.Arcane, Tags.Sorcery]
		self.level = 4

		self.element = Tags.Arcane

		self.upgrades['voidbomber'] = (1, 2, "Void Binding", "[Void Beam:spell]击杀的敌人重生为[Void Bomber:unit]") # 我觉得不应该翻译成重生
		self.upgrades['starbeam'] = (1, 3, "Star Beam", "[Void Beam:spell]额外造成一份[fire]伤害")
		self.upgrades['voidcurse'] = (1, 3, "Voidcurse", "[Void Beam:spell]造成伤害前使敌人失去 [25% 奥术抗性:arcane]")
		# More void beam.... fork?  Combustion... but bigger?  Triple beam?

	def get_description(self):
		return "对一条直线造成 [{damage}:arcane]\n摧毁墙壁".format(**self.fmt_dict())

	def aoe(self, x, y):
		start = Point(self.caster.x, self.caster.y)
		target = Point(x, y)
		path = Bolt(self.caster.level, start, target, two_pass=False, find_clear=False)
		for point in path:
			yield point

	def cast(self, x, y):
		damage = self.get_stat('damage')
		for point in self.aoe(x, y):
			
			# Kill walls
			if not self.caster.level.tiles[point.x][point.y].can_see:
				self.caster.level.make_floor(point.x, point.y)
			
			cur_tile = self.caster.level.tiles[point.x][point.y]

			# Kill clouds
			if cur_tile.cloud:
				cur_tile.cloud.kill()

			# Deal damage
			unit = self.caster.level.get_unit_at(point.x, point.y)
			if unit and self.get_stat('voidcurse'):
				unit.apply_buff(VoidBeamResistDebuff())

			self.caster.level.deal_damage(point.x, point.y, self.get_stat('damage'), self.element, self)
			if self.get_stat('starbeam'):
				self.caster.level.deal_damage(point.x, point.y, self.get_stat('damage'), Tags.Fire, self)

			if unit and not unit.is_alive() and self.get_stat('voidbomber'):
				bomber = VoidBomber()
				apply_minion_bonuses(self, bomber)
				self.summon(bomber, target = unit)
		yield

	def get_impacted_tiles(self, x, y):
		return list(self.aoe(x, y))

class ThunderStrike(Spell):

	def on_init(self):
		self.range = 11
		self.max_charges = 9
		self.name = "Thunder Strike"
		self.damage = 24
		self.damage_type = Tags.Lightning
		self.radius = 2
		self.duration = 3
		
		self.tags = [Tags.Lightning, Tags.Sorcery]
		self.level = 2

		self.storm_power = 0
		self.upgrades['requires_los'] = (-1, 3, "Blindcasting", ignore_los_upgrade)
		self.upgrades['storm_power'] = (1, 3, "Storm Power", "如果目标地块存在雷云，返还充能") # TODO storm thunderstorm blizzard 译名
		self.upgrades['heaven_strike'] = (1, 3, "Heaven Strike", "[Thunder Strike:spell]造成额外的一份[holy]伤害")

	def get_description(self):
		return ("对目标造成 [{damage}:lightning]\n"
				"[stun][{radius}:radius]内的所有敌人").format(**self.fmt_dict())

	def cast(self, x, y):

		self.owner.level.show_beam(self.caster, Point(x, y), Tags.Lightning)

		in_cloud = isinstance(self.caster.level.tiles[x][y].cloud, StormCloud)
		duration = self.get_stat('duration')
		radius = self.get_stat('radius')
		damage = self.get_stat('damage')

		if in_cloud and self.get_stat('storm_power'):
			self.refund_charges(1)

		self.caster.level.deal_damage(x, y, damage, self.damage_type, self)
		yield

		if self.get_stat('heaven_strike'):
			for i in range(3):
				yield

			self.caster.level.deal_damage(x, y, damage, Tags.Holy, self)

		for stage in Burst(self.caster.level, Point(x, y), radius):
			for point in stage:

				self.caster.level.show_effect(point.x, point.y, Tags.Thunderstrike)
				cur_target = self.caster.level.get_unit_at(point.x, point.y)
				if cur_target and self.caster.level.are_hostile(cur_target, self.caster):
					cur_target.apply_buff(Stun(), self.get_stat('duration'))
			yield

	def get_impacted_tiles(self, x, y):
		radius = self.get_stat('radius')

		return [p for stage in Burst(self.caster.level, Point(x, y), radius) for p in stage]

class GiantStrengthBuff(Buff):

	def on_applied(self, owner):
		hurl_boulder = SimpleRangedAttack(name="Hurl Boulder", damage=self.damage, range=6, damage_type=Tags.Physical)
		hurl_boulder.max_charges = 50
		self.spells = [hurl_boulder]
		self.resists[Tags.Physical] = 50
		self.color = Tags.Enchantment.color
		self.name = "Giant Strength"
		self.buff_type = BUFF_TYPE_BLESS
		self.asset = ['status', 'giant_form']
# not in game
class GiantStrengthSpell(Spell):

	def on_init(self):
		self.name = "Stone Giant Form"
		self.duration = 15
		self.max_charges = 9
		self.damage = 25
		self.range = 0

		self.tags = [Tags.Nature, Tags.Enchantment]
		self.level = 2

		self.upgrades['damage'] = (15, 2)
		self.upgrades['duration'] = (15, 1)

	def get_description(self):
		return "Temporarily gain physical resistance and the ability to hurl boulders."

	def cast(self, x, y):
		buff = GiantStrengthBuff()
		buff.damage = self.get_stat('damage')
		self.caster.apply_buff(buff, self.get_stat('duration'))
		yield

class ChaosBarrage(Spell):

	def on_init(self):
		self.name = "Chaos Barrage"
		self.range = 7
		self.damage = 6
		self.num_targets = 9
		self.angle = math.pi / 6
		self.max_charges = 8
		self.tags = [Tags.Chaos, Tags.Sorcery]
		self.can_target_self = False

		self.level = 2

		self.upgrades['num_targets'] = (6, 4, "Mega Barrage")
		self.upgrades['shockwaves'] = (1, 3, "Shockwaves", "每发箭同样对相邻敌人造成伤害")
		self.upgrades['smart_targeting'] = (1, 3, "Smart Bolts", "[Chaos Barrage:spell]不会攻击盟友，会对目标造成其抗性最低类型的伤害")

	def get_description(self):
		return ("对锥形区域内的随机单位射出总共 [{num_targets} 发:num_targets]混沌能量箭\n"
				"每发箭随机造成 [{damage} 点:damage][fire][lightning]或[physical]伤害").format(**self.fmt_dict())

	def get_cone_burst(self, x, y):
		# TODO- this is very generous and frequently goes through walls, fix that
		target = Point(x, y)
		burst = Burst(self.caster.level, self.caster, self.get_stat('range'), expand_diagonals=True, burst_cone_params=BurstConeParams(target, self.angle))
		return [p for stage in burst for p in stage if self.caster.level.can_see(self.caster.x, self.caster.y, p.x, p.y)]

	def cast(self, x, y):

		for i in range(self.get_stat('num_targets')):
			cone_points = self.get_cone_burst(x, y)
			possible_targets = [self.caster.level.get_unit_at(p.x, p.y) for p in cone_points]
			possible_targets = [t for t in possible_targets if t and t != self.caster]
			possible_targets = [t for t in possible_targets if t.is_alive()]

			if self.get_stat('smart_targeting'):
				possible_targets = [t for t in possible_targets if are_hostile(self.caster, t)]

			if not possible_targets:
				possible_targets = cone_points

			cur_enemy = random.choice(possible_targets)

			dtypes = [Tags.Fire, Tags.Lightning, Tags.Physical]
			random.shuffle(dtypes)

			if self.get_stat('smart_targeting'):
				cur_element = min(dtypes, key=lambda t: cur_enemy.resists[t])
			else:
				# Already shuffled
				cur_element = dtypes[0]

			start = Point(self.caster.x, self.caster.y)
			target = Point(cur_enemy.x, cur_enemy.y)
			path = Bolt(self.caster.level, start, target)
			for p in path:
				self.caster.level.deal_damage(p.x, p.y, 0, cur_element, self)
				yield

			self.caster.level.deal_damage(target.x, target.y, self.get_stat('damage'), cur_element, self)

			if self.get_stat('shockwaves'):
				yield
				for p in self.caster.level.get_adjacent_points(target, filter_walkable=False):
					u = self.caster.level.get_unit_at(*p)
					if u and are_hostile(u, self.caster):
						self.caster.level.deal_damage(p.x, p.y, self.get_stat('damage'), cur_element, self)


	def get_impacted_tiles(self, x, y):
		return self.get_cone_burst(x, y)

class InfernoCloud(Cloud):

	def __init__(self, owner, damage):
		Cloud.__init__(self)
		self.damage = damage
		self.owner = owner
		self.color = Color(180, 0, 0)
		self.spread_chance = .7
		self.duration = 5
		self.name = "Inferno"
		self.description = "A spreading cloud of fire.  Deals %d damage to creatures caught within each turn."

	def on_advance(self):

		# Deal damage to units in the fire
		if self.level.get_unit_at(self.x, self.y):
			self.owner.level.deal_damage(self.x, self.y, self.get_stat('damage'), Tags.Fire, self)

		if random.random() < self.spread_chance:	
			expansion_points = self.owner.level.get_adjacent_points(Point(self.x, self.y))

			expansion_points = [p for p in expansion_points if self.owner.level.can_walk(p.x, p.y)]

			point = random.choice(expansion_points)
			if not self.level.tiles[point.x][point.y].cloud:
				self.owner.level.add_obj(InfernoCloud(self.owner, self.get_stat('damage')), point.x, point.y)
# not in game
class InfernoSpell(Spell):

	def on_init(self):
		self.range = 3
		self.max_charges = 1
		self.name = "Inferno"
		self.tags = [Tags.Fire]
		self.damage = 10

		self.level = 5

		self.requires_los = False
		self.range = 7

		self.upgrades['range'] = (5, 1)
		self.upgrades['max_charges'] = (2, 1)

	def get_description(self):
		return "Create a spreading inferno that deals damage each turn to units inside."

	def cast(self, x, y):
		self.caster.level.add_obj(InfernoCloud(self.caster, self.get_stat('damage')), x, y)
		yield

class DispersalSpell(Spell):

	def on_init(self):
		self.range = 6
		self.max_charges = 15
		self.name = "Disperse"
		self.tags = [Tags.Arcane, Tags.Sorcery, Tags.Translocation]
		self.can_target_self = False
		self.radius = 4
		self.level = 2

		self.upgrades['warpdagger'] = (1, 3, "Violent Warp", "对每个被传送的敌人施放[Magic Missile:spell]")
		self.upgrades['sheilds'] = (1, 2, "Protective Warp", "每个被传送的盟友获得 [3:shields]")

	def get_description(self):
		return ("把[{radius}_tile:radius]内的所有单位传送到随机位置\n"
				"不包括施法者本身").format(**self.fmt_dict())

	def get_impacted_tiles(self, x, y):
		return self.caster.level.get_points_in_ball(x, y, self.get_stat('radius'))

	def cast(self, x, y):
		for target in self.caster.level.get_units_in_ball(Point(x, y), self.get_stat('radius')):
			if not target:
				continue

			if target == self.caster:
				continue
			
			if not target.can_teleport:
				continue

			self.caster.level.show_effect(target.x, target.y, Tags.Translocation)
			yield 

			# Calc possible points directly before moving with no yields in between to gaurantee that the point remains valid when we teleport
			possible_points = []
			for i in range(len(self.caster.level.tiles)):
				for j in range(len(self.caster.level.tiles[i])):
					if self.caster.level.can_stand(i, j, target):
						possible_points.append(Point(i, j))

			if not possible_points:
				return

			target_point = random.choice(possible_points)

			self.caster.level.act_move(target, target_point.x, target_point.y, teleport=True)
			yield
			self.caster.level.show_effect(target.x, target.y, Tags.Translocation)

			if are_hostile(self.caster, target) and self.get_stat('warpdagger'):
				magic_missile = self.owner.get_spell(MagicMissile)
				if not magic_missile:
					magic_missile = MagicMissile()
					magic_missile.caster = self.caster
					magic_missile.owner = self.owner
				for _ in magic_missile.cast(target.x, target.y):
					yield

			if not are_hostile(self.caster, target) and self.get_stat('sheilds'):
				target.add_shields(3)

class PetrifySpell(Spell):

	def on_init(self):
		self.range = 8
		self.max_charges = 20
		self.name = "Petrify"
		self.requires_los = False

		self.duration = 10

		self.upgrades['glassify'] = (1, 3, 'Glassify', '把目标[glassify]而不是[petrify]\n[glassify]单位有 [-100% 物理抗性:physical]')
		self.upgrades['arcane_conductivity'] = (1, 3, "Arcane Conductivity", "目标失去 [100% 奥术抗性:arcane]")
		self.upgrades['petrified_animation'] = (1, 3, "Rocky Servitude", "目标死亡时将其复活为[Golem:unit]，继承生命值") #will add extra examine tooltip

		self.tags = [Tags.Arcane, Tags.Enchantment]
		self.level = 2

	def get_description(self):
		desc = "对目标施加 [{duration}:duration][petrify]\n"
		desc += text.petrify_desc
		return desc.format(**self.fmt_dict())

	def create_golem(self, evt):
		u = evt.unit
		golem = Golem()
		golem.max_hp = u.max_hp
		if u.flying:
			golem.name = "Flying Golem"
			golem.asset_name = "golem_flying"
			golem.flying = True
		self.summon(golem, u)

	def cast(self, x, y):

		target = self.caster.level.get_unit_at(x, y)
		if not target:
			return

		self.caster.level.deal_damage(x, y, 0, Tags.Physical, self)
		buff = PetrifyBuff() if not self.get_stat('glassify') else GlassPetrifyBuff()
		if self.get_stat('arcane_conductivity'):
			buff.resists[Tags.Arcane] = -100
		if self.get_stat('petrified_animation'):
			buff.owner_triggers[EventOnDeath] = self.create_golem
		target.apply_buff(buff, self.get_stat('duration'))
		yield

class StoneAuraBuff(Buff):

	def __init__(self, spell):
		self.spell = spell
		Buff.__init__(self)

	def on_init(self):
		self.name = "Petrification Aura" # TODO
		self.description = "每回合[Petrify]周围的敌人"

		self.global_triggers[EventOnDeath] = self.on_death

	def on_death(self, evt):
		if self.spell.get_stat('wormification') and distance(evt.unit, self.owner) <= self.spell.get_stat('radius') and (evt.unit.get_buff(PetrifyBuff) or evt.unit.get_buff(GlassPetrifyBuff)):
			unit = RockWurm()
			unit.max_hp = evt.unit.max_hp
			self.summon(unit, target=evt.unit)

	def on_advance(self):
		BuffClass = GlassPetrifyBuff if self.spell.get_stat('glassify') else PetrifyBuff
		units = [u for u in self.owner.level.get_units_in_ball(self.owner, self.spell.get_stat('radius'))]
		random.shuffle(units)
		stoned = 0
		for u in units:
			if not are_hostile(self.owner, u):
				continue
			if u.has_buff(BuffClass):
				if self.spell.get_stat('crumbling_aura') and u.cur_hp <= 16:
					u.kill()
				continue
			if stoned < self.spell.get_stat('num_targets'):
				u.apply_buff(BuffClass(), self.spell.get_stat('petrify_duration'))
				stoned += 1

			if stoned >= self.spell.get_stat('num_targets'):
				break


class StoneAuraSpell(Spell):

	def on_init(self):
		self.range = 0
		self.name = "Petrification Aura"
		self.tags = [Tags.Arcane, Tags.Enchantment]
		self.level = 4

		self.max_charges = 3
		self.num_targets = 3

		self.duration = 7

		self.petrify_duration = 2
		self.radius = 7

		self.upgrades['crumbling_aura'] = (1, 3, "Crumbling Aura", "每回合击杀光环范围内[小于 16 点血量:damage][petrify]的敌人")
		self.upgrades['wormification'] = (1, 4, "Wormification Aura", "光环范围内[petrify]的敌人死亡时，将其复活为[Rock Worm:unit]，继承生命值")
		self.upgrades['glassify'] = (1, 5, "Glassify", "将敌人[glassify]而不是[petrify]\n[glassify]单位有 [-100% 物理抗性:physical]")

	def get_description(self):
		return ("每回合对 [{radius}:radius]内最多 [{num_targets}:num_targets]未石化的敌人施加[petrify]\n" +
				text.petrify_desc + '\n'
				"持续 [{duration}:duration].").format(**self.fmt_dict())

	def cast_instant(self, x, y):
		self.caster.apply_buff(StoneAuraBuff(self), self.get_stat('duration'))

class SummonWolfSpell(Spell):

	def get_description(self): # 好拗口
		return ("召唤 [{num_summons}:num_summons]有跳跃攻击的[Wolf:unit]").format(**self.fmt_dict()) # 太拗口了

	def on_init(self):
		self.max_charges = 7
		self.name = "Wolf"
		self.minion_health = 15
		self.minion_damage = 5

		self.minion_range = 4

		self.num_summons = 1

		self.upgrades['num_summons'] = (2, 4, "Wolf Pack")
		self.upgrades['ice_hound'] = (1, 3, "Ice Hound", "召唤[Ice Hound:unit]而不是[Wolf:unit]")
		self.upgrades['clay_hound'] = (1, 5, "Clay Hound", "召唤[Clay Hound:unit]而不是[Wolf:unit]")

		self.tags = [Tags.Nature, Tags.Conjuration]
		self.level = 1

		self.must_target_walkable = True
		self.must_target_empty = True

		self.target_empty = True

	def get_extra_examine_tooltips(self):
		return [self.make_wolf(),
				self.spell_upgrades[0],
				self.spell_upgrades[1],
				self.make_ice_wolf(),
				self.spell_upgrades[2],
				self.make_clay_wolf()]

	def make_ice_wolf(self):
		wolf = self.make_wolf()

		ice_spit = SimpleRangedAttack(damage=self.get_stat('minion_damage'), range=self.get_stat('minion_range'), damage_type=Tags.Ice)
		ice_spit.cool_down = 2

		wolf.spells.insert(0, ice_spit)
		wolf.resists[Tags.Ice] = 100
		wolf.resists[Tags.Fire] = -50
		wolf.resists[Tags.Dark] = 50
		wolf.name = "Ice Hound"
		wolf.tags = [Tags.Demon, Tags.Ice]
		wolf.buffs.append(Thorns(4, Tags.Ice))

		return wolf

	def make_clay_wolf(self):
		wolf = self.make_wolf()
		wolf.name = "Clay Hound"
		wolf.asset_name = "earth_hound"

		wolf.resists[Tags.Physical] = 50
		wolf.resists[Tags.Fire] = 50
		wolf.resists[Tags.Lightning] = 50
		wolf.buffs.append(RegenBuff(3))
		return wolf

	def make_wolf(self):
		wolf = Unit()
		wolf.max_hp = self.get_stat('minion_health')
		
		wolf.sprite.char = 'w'
		wolf.sprite.color = Color(102, 77, 51)
		wolf.name = "Wolf"
		wolf.description = "中型野兽"
		wolf.spells.append(SimpleMeleeAttack(self.get_stat('minion_damage')))
		wolf.tags = [Tags.Living, Tags.Nature]

		wolf.spells.append(LeapAttack(damage=self.get_stat('minion_damage'), damage_type=Tags.Physical, range=self.get_stat('minion_range')))
		wolf.team = self.caster.team

		return wolf

	def cast(self, x, y):
		for i in range(self.get_stat('num_summons')):
			if self.get_stat('clay_hound'):
				wolf = self.make_clay_wolf()
			elif self.get_stat('ice_hound'):
				wolf = self.make_ice_wolf()
			else:
				wolf = self.make_wolf()
			self.summon(wolf, Point(x, y))
			yield

class SummonGiantBear(Spell):

	def get_description(self):
		return ("召唤一只[Giant Bear:unit].\n"
				"[Giant Bear:unit]有 [{minion_health}:minion_health]\n"
				"[Giant Bear:unit]的近战攻击造成 [{minion_damage}:physical]").format(**self.fmt_dict())

	def on_init(self):
		self.max_charges = 2
		self.name = "Giant Bear"
		self.minion_health = 75
		self.minion_damage = 10
		
		self.tags = [Tags.Nature, Tags.Conjuration]
		self.level = 3

		self.minion_attacks = 2

		self.upgrades['armored'] = (1, 3, "Metal Bear", "召唤[Metallic Giant Bear:unit]而不是[Giant Bear:unit]", "species")
		self.upgrades['venom'] = (1, 3, "Venom Bear", "召唤[Venom Bear:unit]而不是[Giant Bear:unit]\n[Venom Bear:unit]拥有[有毒啃咬:spell]，在敌人受到[poison]伤害时治疗自己", "species")
		self.upgrades['blood'] = (1, 3, "Blood Bear", "召唤[Blood Bear:unit]而不是[Giant Bear:unit]\[Blood Bear:unit]有[dark]伤害抗性，每次攻击造成更高的伤害", "species")

		self.must_target_walkable = True
		self.must_target_empty = True

	def get_extra_examine_tooltips(self):
		return [self.bear(), self.spell_upgrades[0], self.armored_bear(), self.spell_upgrades[1], self.venom_bear(), self.spell_upgrades[2], self.blood_bear()]

	def bear(self):

		bear = Unit()
		bear.max_hp = self.get_stat('minion_health')
		
		bear.name = "Giant Bear"
		bear.asset_name = "giant_bear"
		bear.spells.append(SimpleMeleeAttack(self.get_stat('minion_damage')))

		bear.tags = [Tags.Living, Tags.Nature]

		bear.spells[0].attacks = self.get_stat('minion_attacks')
		if self.get_stat('minion_attacks') > 1:
			bear.spells[0].description += "\nAttacks %d times." % self.get_stat('minion_attacks')
		
		return bear

	def venom_bear(self):
		bear = self.bear()
		bear.name = "Venom Bear" # 原本是 Beast，我觉得是写错了
		bear.asset_name = "giant_bear_venom"
		bear.resists[Tags.Poison] = 100
		bear.tags = [Tags.Living, Tags.Poison, Tags.Nature]

		bite = SimpleMeleeAttack(damage=self.get_stat('minion_damage'), buff=Poison, buff_duration=5)
		bite.name = "Poison Bite" # TODO
		bear.spells = [bite]

		bear.buffs = [VenomBeastHealing()]
		return bear

	def armored_bear(self):
		bear = BossSpawns.Metallic(self.bear())
		bear.max_hp = self.get_stat('minion_health')
		return bear

	def blood_bear(self):
		bear = BloodBear()

		bear.spells[0].attacks = self.get_stat('minion_attacks')
		bear.spells[0].description += "\nAttacks %d times." % self.get_stat('minion_attacks')

		apply_minion_bonuses(self, bear)
		return bear

	def cast(self, x, y):

		if self.get_stat('venom'):
			bear = self.venom_bear()

		elif self.get_stat('armored'):
			bear = self.armored_bear()

		elif self.get_stat('blood'):
			bear = self.blood_bear()

		else:
			bear = self.bear()

		self.summon(bear, Point(x, y))
		yield

class FeedingFrenzySpell(Spell):

	def on_init(self):
		self.max_charges = 5
		self.name = "Sight of Blood"
		self.duration = 4
		self.range = 10

		self.hp_cost = 20

		self.demon_units = 0
		self.upgrades['duration'] = (3, 3)
		self.upgrades['demon_units'] = (1, 2, "Demon Frenzy", "同样影响[demon]单位")
		self.upgrades['requires_los'] = (-1, 2, "Blindcasting", ignore_los_upgrade)
		
		self.tags = [Tags.Nature, Tags.Blood, Tags.Enchantment]
		self.level = 3

	def can_affect(self, unit):
		if Tags.Living not in unit.tags and not (self.get_stat('demon_units') and Tags.Demon in unit.tags):
			return False
		if unit == self.caster:
			return False
		if not are_hostile(self.caster, unit):
			return False
		return True

	def get_impacted_tiles(self, x, y):
		return [u for u in self.caster.level.get_units_in_los(Point(x, y)) if self.can_affect(u)]

	def cast(self, x, y):

		target = self.caster.level.get_unit_at(x, y)
		if not target:
			return

		self.caster.level.deal_damage(x, y, 0, Tags.Fire, self)
		target.apply_buff(Stun(), self.get_stat('duration'))

		for unit in self.caster.level.get_units_in_los(target):
			if unit == target:
				continue
			if not self.can_affect(unit):
				continue
			unit.apply_buff(BerserkBuff(), self.get_stat('duration'))

		yield

	def can_cast(self, x, y):
		unit = self.caster.level.get_unit_at(x, y)
		if not unit:
			return False
		if not self.can_affect(unit):
			return False
		if unit.cur_hp == unit.max_hp:
			return False
		return Spell.can_cast(self, x, y)

	def get_description(self):
		return ("只能以受伤的[living]单位为目标施放\n"
				"目标被[stunned] [{duration}:duration]\n"
				+ text.stun_desc + '\n'
				+ "目标视线内所有[living]敌人[berserk] [{duration}:duration]\n"
				+ text.berserk_desc).format(**self.fmt_dict())

class EternalDarknessUpgrade(Upgrade):

	def on_init(self):
		self.name = "Eternal Darkness"
		self.description = "每造成 [200:dark]，[Darkness:spell]获得 1 点充能"
		self.global_triggers[EventOnDamaged] = self.on_damage
		self.damage_counter = 0
		self.level = 3

	def on_damage(self, evt):
		if evt.damage_type == Tags.Dark:
			self.damage_counter += evt.damage
		if self.damage_counter >= 200:
			self.damage_counter -= 200
			darkness_spell = self.owner.get_spell(Darkness)
			darkness_spell.cur_charges = min(darkness_spell.cur_charges + 1, darkness_spell.get_stat('max_charges'))

class DarknessBuff(Buff):

	def on_init(self):
		self.name = "Darkness"
		self.color = Tags.Dark.color
		self.description = "致盲地图上的所有单位"
		self.asset = ['status', 'darkness']
		self.darkvision = False
		self.deal_clouds = False
		self.owner_triggers[EventOnUnitAdded] = self.on_unit_added

	def on_unit_added(self, evt):
		self.effect_unit(evt.unit)

	def on_applied(self, evt):
		units = list(self.owner.level.units)
		for unit in units:
			self.effect_unit(unit)

	def on_advance(self):
		units = list(self.owner.level.units)
		for unit in units:
			if not unit.get_buff(BlindBuff):
				self.effect_unit(unit)
			if self.deal_clouds and self.owner.level.tiles[x][y].cloud:
				unit.deal_damage(5, Tags.Dark, self)

	def on_unapplied(self):
		units = list(self.owner.level.units)
		for unit in units:
			buff = unit.get_buff(BlindBuff)
			if buff:
				unit.remove_buff(buff)

	def effect_unit(self, unit):
		if self.darkvision and unit.team == self.owner.team:
			return
		unit.apply_buff(BlindBuff())

class Darkness(Spell):

	def on_init(self):
		self.name = "Darkness"
		self.duration = 5
		self.max_charges = 3
		self.level = 3
		self.tags = [Tags.Dark, Tags.Enchantment]
		self.range = 0

		self.upgrades['darkvision'] = (1, 3, "Darkvision", "不会致盲你和你的盟友")
		self.upgrades['deal_clouds'] = (1, 5, "Dark Clouds", "每回合对所在地块有风暴云的敌人造成 [5:dark]")
		self.add_upgrade(EternalDarknessUpgrade())

	def cast_instant(self, x, y):
		buff = DarknessBuff()
		if self.get_stat('darkvision'):
			buff.darkvision = True
		self.caster.apply_buff(buff, self.get_stat('duration'))

	def get_description(self):
		return ("每回合[blind]所有单位 [1:duration].\n"
				+ text.blind_desc + '\n'
				#"[Demon] and [undead] units are unaffected.\n"
				"持续 [{duration}:duration]").format(**self.fmt_dict())


class SpiritHarvestUpgrade(Upgrade):

	def __init__(self, spell):
		Upgrade.__init__(self)
		self.spell = spell

	def on_init(self):
		self.name = "Spirit Harvest"
		self.description = "闪电风暴每造成 [75:damage]，召唤一个[Storm Spirit:unit]"
		self.global_triggers[EventOnDamaged] = self.on_damaged
		self.global_triggers[EventOnUnitAdded] = self.on_unit_added

		self.level = 4

		self.dmg_dealt = 0
		self.threshold = 1

	def on_unit_added(self, evt):
		if evt.unit.is_player_controlled:
			self.dmg_dealt = 0

	def on_damaged(self, evt):
		if evt.source == self.spell:
			self.dmg_dealt += 1
		
		while self.dmg_dealt >= self.threshold:
			self.dmg_dealt -= 1
			self.summon(StormSpirit(), target=self.spell.caster)

class LightningStarUpgrade(Upgrade):

	def __init__(self, spell):
		Upgrade.__init__(self)
		self.spell = spell

	def on_init(self):
		self.level = 3
		self.name = "Lightning Star"
		self.description = "每回合对随机三个雷云地块之间连成的直线造成伤害两次"
		
		self.cloud_groups = []

	def on_advance(self):
		for cloud_group in self.cloud_groups:
			if not self.owner.level.tiles[cloud_group[0].x][cloud_group[0].y].cloud:
				self.cloud_groups.remove(cloud_group)
				continue
			for i in range(2):
				random.shuffle(cloud_group)
				chosen_clouds = []
				for i in range(3):
					chosen_clouds.append(cloud_group[i])
				for i in range(3):
					for p in self.owner.level.get_points_in_line(chosen_clouds[i], chosen_clouds[(i + 1) % 3]):
						if self.owner.level.tiles[p.x][p.y].can_walk:
							self.owner.level.deal_damage(p.x, p.y, self.spell.get_stat('damage'), Tags.Lightning, self.spell)

class ParticleStormUpgrade(Upgrade):

	def __init__(self, spell):
		Upgrade.__init__(self)
		self.spell = spell

	def on_init(self):
		self.level = 3
		self.name = "Particle Storm"
		self.description = "[Lightning Storm:spell]召唤的雷云每回合对所在的地块造成 [3:arcane]"

		self.cloud_groups = []

	def on_advance(self):
		for cloud_group in self.cloud_groups:
			for c in cloud_group:
				if not self.owner.level.tiles[cloud_group[0].x][cloud_group[0].y].cloud:
					cloud_group.remove(c)
					continue
				self.owner.level.deal_damage(c.x, c.y, self.spell.get_stat('damage', base=3), Tags.Arcane, self.spell)

class StormSpell(Spell):

	def on_init(self):
		self.max_charges = 4
		self.name = "Lightning Storm"
		self.duration = 10
		self.range = 9
		self.radius = 4
		self.damage = 12
		self.strikechance = 50

		self.add_upgrade(ParticleStormUpgrade(self))
		self.add_upgrade(LightningStarUpgrade(self))
		self.add_upgrade(SpiritHarvestUpgrade(self))
		self.tags = [Tags.Lightning, Tags.Nature, Tags.Enchantment]
		self.level = 4

		self.stats.append('strikechance')

	def cast(self, x, y):

		cloud_group = []
		for stage in Burst(self.caster.level, Point(x, y), self.get_stat('radius')):
			for p in stage:
				cloud = StormCloud(self.caster)
				cloud.duration = self.get_stat('duration')
				cloud.damage = self.get_stat('damage')
				cloud.strikechance = self.get_stat('strikechance') / 100.0
				cloud.source = self
				cloud_group.append(cloud)
				yield self.caster.level.add_obj(cloud, p.x, p.y)

		if self.caster.has_buff(LightningStarUpgrade):
			self.caster.get_buff(LightningStarUpgrade).cloud_groups.append(cloud_group)
		if self.caster.has_buff(ParticleStormUpgrade):
			self.caster.get_buff(ParticleStormUpgrade).cloud_groups.append(cloud_group)

	def get_impacted_tiles(self, x, y):
		return [p for stage in Burst(self.caster.level, Point(x, y), self.get_stat('radius')) for p in stage]

	def get_description(self):
		return ("在[{radius}:radius]的范围里召唤雷暴\n"
				"每回合雷云有 [{strikechance}:strikechance]对其所在地块造成 [{damage}:lightning]\n"
				"雷暴持续 [{duration}:duration]").format(**self.fmt_dict())

class ThornyPrisonSpell(Spell):

	def on_init(self):
		self.max_charges = 6
		self.name = "Prison of Thorns"
		self.range = 10
		self.minion_damage = 3
		self.minion_health = 7
		
		self.upgrades['minion_damage'] = (3, 2)
		self.upgrades['minion_health'] = (7, 2)
		self.upgrades['iron'] = (1, 5, "Iron Prison", "生成[Iron Thorn:unit]而不是[Thorny Plant:unit]\n[Iron Thorn:unit]的攻击多造成 [3:damage]并且抵抗多种类型的伤害", 'prison')
		self.upgrades['icy'] = (1, 6, "Icy Prison", "生成[Icy Thorn:unit]而不是[Thorny Plant:unit]\n[Icy Thorn:unit]可以进行远程[ice]攻击", 'prison')
		
		self.minion_duration = 15

		self.tags = [Tags.Nature, Tags.Conjuration]
		self.level = 3

	def get_description(self):
		return ("在一组敌人周围生成一圈肉食植物\n"
		  		"植物有 [{minion_health}:minion_health] 且不能移动\n"
				"植物的近战攻击造成 [{minion_damage}:physical]\n"
				"植物在 [{minion_duration}:minion_duration] 后消失").format(**self.fmt_dict())

	def cast(self, x, y):
		target_points = self.get_impacted_tiles(x, y)

		random.shuffle(target_points)

		for p in target_points:
			
			unit = Unit()
			unit.name = "Thorny Plant"
			unit.max_hp = self.get_stat('minion_health')
			unit.spells.append(SimpleMeleeAttack(self.get_stat('minion_damage')))
			unit.stationary = True
			unit.turns_to_death = self.get_stat('minion_duration')
			unit.tags = [Tags.Nature]

			if self.get_stat('iron'):
				unit.name = "Iron Thorn"
				unit.asset_name = "fae_thorn_iron"
				unit.tags.append(Tags.Metallic)
				unit.spells[0].damage += 3
			if self.get_stat('icy'):
				unit.name = "Icy Thorn"
				unit.asset_name = "spriggan_bush_icy"
				unit.spells = [SimpleRangedAttack(damage=self.get_stat('minion_damage'), range=3 + self.get_stat('minion_range'), damage_type=Tags.Ice)]
				
			self.summon(unit, p, radius=0)

			yield


	def get_impacted_tiles(self, x, y):

		candidates = set([Point(x, y)])
		unit_group = set()

		while candidates:
			candidate = candidates.pop()
			unit = self.caster.level.get_unit_at(candidate.x, candidate.y)
			if unit and unit not in unit_group and are_hostile(unit, self.caster):
				unit_group.add(unit)

				for q in unit.iter_occupied_points():
					for p in self.caster.level.get_adjacent_points(Point(q.x, q.y), filter_walkable=False):
						if not self.caster.level.get_unit_at(p.x, p.y) == unit:
							candidates.add(p)

		outline = set()
		for unit in unit_group:
			for q in unit.iter_occupied_points():
				for p in self.caster.level.get_adjacent_points(Point(q.x, q.y)):
					if not self.caster.level.get_unit_at(p.x, p.y):
						outline.add(p)

		return list(outline)

class PillarDisruptionDebuff(Buff):

	def on_init(self):
		self.name = "Flammable"
		self.color = Tags.Fire.color
		self.resists[Tags.Fire] = -50
		self.stack_type = STACK_DURATION
		self.buff_type = BUFF_TYPE_CURSE
		self.asset = ['status', 'amplified_fire']

class FlameStrikeSpell(Spell):

	def on_init(self):
		self.max_charges = 2
		self.radius = 1
		self.damage = 50
		self.element = Tags.Fire
		self.range = 10
		self.name = "Pillar of Fire"
		self.requires_los = False

		self.tags = [Tags.Fire, Tags.Holy, Tags.Sorcery]
		self.level = 5

		self.num_targets = 4

		self.upgrades['channel'] = (1, 3, "Channeling", "[Pillar of Flame:spell]现在可以持续引导")
		self.upgrades['disruption'] = (1, 3, "Disrupting Flames", "移除中心目标的护盾并且使其减少 [50% 火焰抗性:fire] [10:duration]")
		self.upgrades['cast_annihilate'] = (1, 4, "Pillar of Annihilation", "击杀目标时，对目标地块视界内至多 [4:num_targets]敌人施放你的[Annihilate:spell]")

	def cast(self, x, y, channel_cast=False):
		
		if self.get_stat('channel') and not channel_cast:
			self.caster.apply_buff(ChannelBuff(self.cast, Point(x, y))) # 没有持续时间 seriously?
			return

		start = Point(self.caster.x, self.caster.y)
		target = Point(x, y)

		for stage in Burst(self.caster.level, target, self.get_stat('radius')):
			for point in stage:
				unit = self.caster.level.get_unit_at(point.x, point.y)
				damage = self.get_stat('damage')
				if point.x == x and point.y == y:
					damage = damage * 2
					if unit and self.get_stat('disruption'):
						unit.shields = 0
						unit.apply_buff(PillarDisruptionDebuff(), self.get_stat('duration', base=10))
				self.caster.level.deal_damage(point.x, point.y, damage, self.element, self)
				if unit and self.get_stat('num_targets') > 0 and not unit.is_alive():
					possible_targets = self.caster.level.get_units_in_los(point)
					possible_targets = [t for t in possible_targets if are_hostile(t, self.caster)]
					random.shuffle(possible_targets)
					annihilate = self.owner.get_or_make_spell(AnnihilateSpell)
					if self.get_stat('cast_annihilate'):
						for i in range(self.get_stat('num_targets')):
							if len(possible_targets) >= i:
								target = possible_targets[i]
								for _ in self.owner.level.act_cast(self.caster, annihilate, target.x, target.y, pay_costs=False, queue=False):
									pass
			yield

		return
 
	def get_impacted_tiles(self, x, y):
			return [p for stage in Burst(self.caster.level, Point(x, y), self.get_stat('radius')) for p in stage]

	def get_description(self):
		return ("对[{radius}:radius]内的单位造成 [{damage}:fire]\n"
			    "中心地块受到的伤害翻倍").format(**self.fmt_dict())

class CloudArmorBuff(Buff):

	def on_applied(self, owner): 
		self.resists[Tags.Lightning] = 100
		self.resists[Tags.Physical] = 50
		self.color = Color(215, 215, 255)
		self.buff_type = BUFF_TYPE_BLESS

	def on_advance(self):
		self.owner.deal_damage(-self.hp_regen, Tags.Heal, self)
# not in game
class CloudArmorSpell(Spell):

	def on_init(self):
		self.max_charges = 5
		self.duration = 8
		self.hp_regen = 5
		self.name = "Cloud Armor"
		self.range = 7

	def can_cast(self, x, y):
		if not Spell.can_cast(self, x, y):
			return False
		if not self.caster.level.is_point_in_bounds(Point(x, y)):
			return False
		if not self.caster.level.get_unit_at(x, y):
			return False
		return isinstance(self.caster.level.tiles[x][y].cloud, StormCloud)

	def get_description(self):
		return "Target unit standing in a lightning storm gains 100%% lighting resistance, 50%% physical resistance, and %d hp regeneration per turn for %d turns"

	def cast(self, x, y):
		self.caster.level.tiles[x][y].cloud.kill()
		buff = CloudArmorBuff()
		buff.hp_regen = self.hp_regen
		self.caster.level.get_unit_at(x, y).apply_buff(buff, self.get_stat('duration'))
		yield
		return

class BloodlustBuff(Buff):

	def __init__(self, spell):
		Buff.__init__(self)
		self.stack_type = STACK_INTENSITY
		self.name = "Blood Lust"
		self.buff_type = BUFF_TYPE_BLESS
		self.asset = ['status', 'bloodlust']
		self.color = Tags.Fire.color

		self.dtypes = [Tags.Fire, Tags.Physical]
		if spell.get_stat('holy_fury'):
			self.dtypes.append(Tags.Holy)
		if spell.get_stat('dark_fury'):
			self.dtypes.append(Tags.Dark)

	def qualifies(self, spell):
		if not hasattr(spell, 'damage'):
			return False
		if not hasattr(spell, 'damage_type'):
			return False
		if isinstance(spell.damage_type, list):
			for dtype in self.dtypes:
				if dtype in spell.damage_type:
					return True
			return False
		else:
			return spell.damage_type in self.dtypes

	def modify_spell(self, spell):
		if self.qualifies(spell):
			spell.damage += self.extra_damage

	def unmodify_spell(self, spell):
		if self.qualifies(spell):
			spell.damage -= self.extra_damage


class BloodlustSpell(Spell):

	def on_init(self):
		self.name = "Boiling Blood"
		self.max_charges = 11
		self.duration = 7
		self.extra_damage = 6
		self.range = 0
		self.hp_cost = 2

		self.tags = [Tags.Nature, Tags.Enchantment, Tags.Blood, Tags.Fire]
		self.level = 2

		self.upgrades['extra_damage'] = (6, 3)
		self.upgrades['duration'] = (7, 2)
		self.upgrades['holy_fury'] = (1, 3, "Holy Fury", "[Boiling Blood:spell]也影响[holy]能力")
		self.upgrades['dark_fury'] = (1, 3, "Dark Fury", "[Boiling Blood:spell]也影响[dark]能力")


	def get_description(self):
		return "所有盟友的[fire]和[physical]能力获得可堆叠的 [{extra_damage}:damage]加成\n持续 [{duration}:duration]".format(**self.fmt_dict())

	def cast(self, x, y):

		for unit in self.caster.level.units:
			if not self.caster.level.are_hostile(self.caster, unit) and unit != self.caster:
				buff = BloodlustBuff(self)
				buff.extra_damage = self.get_stat('extra_damage')
				unit.apply_buff(buff, self.get_stat('duration'))

				# For the graphic
				unit.deal_damage(0, Tags.Fire, self)
				yield

class HealMinionsSpell(Spell):

	def on_init(self):
		self.name = "Healing Light"
		self.heal = 25

		self.max_charges = 10
		self.range = 0

		self.upgrades['shields'] = (1, 2, "Shielding Light", "视线内的盟友获得 [1:shields]")
		self.upgrades['remove_debuffs'] = (1, 2, "Purifying Light", "净化视线内的盟友的负面状态")
		self.upgrades['heart_flame'] = (1, 4, "Heartflame", "每当[Healing Light:spell]治疗盟友时，对那个单位视线内最近的敌人造成和治疗量相同的[fire]和[holy]伤害")

		self.tags = [Tags.Holy, Tags.Sorcery]
		self.level = 2

	def get_description(self):
		return "治疗视线内的盟友 [{heal}:heal]".format(**self.fmt_dict())

	def cast(self, x, y):

		for unit in self.caster.level.get_units_in_los(self.caster):
			if not self.caster.level.are_hostile(self.caster, unit) and unit != self.caster:

				# Dont heal the player if a gold drake is casting
				if unit.is_player_controlled:
					continue

				health_dealt = 0
				if unit.cur_hp < unit.max_hp:
					health_dealt -= unit.deal_damage(-self.get_stat('heal'), Tags.Heal, self)
				
				if self.get_stat('shields'):
					unit.add_shields(self.get_stat('shields'))
				
				if self.get_stat('remove_debuffs'):
					for buff in unit.buffs:
						if buff.buff_type == BUFF_TYPE_CURSE:
							unit.remove_buff(buff)
				
				if self.get_stat('heart_flame') and health_dealt > 0:
					possible_targets = self.caster.level.get_units_in_los(unit)
					possible_targets = [t for t in possible_targets if are_hostile(self.caster, t)]
					
					if possible_targets:
						#find nearest target
						target = min(possible_targets, key=lambda t: distance(unit, t))
						
						path = self.caster.level.get_points_in_line(Point(unit.x, unit.y), Point(target.x, target.y), find_clear=True)
						
						for point in path:
							self.owner.level.deal_damage(point.x, point.y, 0, Tags.Fire, self)
							self.owner.level.deal_damage(point.x, point.y, 0, Tags.Holy, self)
						self.owner.level.deal_damage(target.x, target.y, health_dealt, Tags.Fire, self)
						self.owner.level.deal_damage(target.x, target.y, health_dealt, Tags.Holy, self)
				yield

class RegenAuraSpell(Spell):

	def on_init(self):
		self.name = "Regeneration Aura"
		self.heal = 4
		self.duration = 8
		self.range = 0
		self.radius = 10

		self.max_charges = 4
		self.level = 2

		self.tags = [Tags.Enchantment, Tags.Nature]

		self.whole_map = 0
		self.upgrades['heal'] = (4, 2)
		self.upgrades['duration'] = (8, 1)
		self.upgrades['whole_map'] = (1, 4, "Global", "光环治疗整个地图上所有盟友")

	def get_description(self):
		return ("每回合治疗[{radius}:radius]内所有盟友[{heal}:heal]\n持续 [{duration}:duration]").format(**self.fmt_dict())

	def cast_instant(self, x, y):
		self.caster.apply_buff(HealAuraBuff(self.get_stat('heal'), self.get_stat('radius'), whole_map=self.get_stat('whole_map')), self.get_stat('duration'))

class OrbBuff(Buff):

	def __init__(self, spell, dest):
		self.spell = spell
		self.dest = dest
		Buff.__init__(self)
		self.buff_type = BUFF_TYPE_PASSIVE

	def on_init(self):
		self.name = "Orb"
		self.description = "每回合向目标前进"
		if self.spell.get_stat('melt_walls'):
			self.description += "\n\n摧毁路径上的墙壁"
		self.first = False

		self.owner_triggers[EventOnDeath] = self.on_death

	def on_death(self, evt):
		self.owner.level.queue_spell(self.spell.on_orb_collide(self.owner, self.owner))

	def on_advance(self):
		# first advance: Radiate around self, do not move
		if self.first:
			self.first = False
			self.spell.on_orb_move(self.owner, self.owner)

		path = None
		if not self.spell.get_stat('melt_walls'):
			path = self.owner.level.find_path(self.owner, self.dest, self.owner, pythonize=True)
		else:
			path = self.owner.level.get_points_in_line(self.owner, self.dest)[1:]
		next_point = None
		if path:
			next_point = path[0]

		# Melt wall if needed
		if next_point and self.owner.level.tiles[next_point.x][next_point.y].is_wall() and self.spell.get_stat('melt_walls'):
			self.owner.level.make_floor(next_point.x, next_point.y)

		# otherwise- try to move one space foward
		if next_point and self.owner.level.can_move(self.owner, next_point.x, next_point.y, teleport=True):
			self.owner.level.act_move(self.owner, next_point.x, next_point.y, teleport=True)
			self.spell.on_orb_move(self.owner, next_point)
		else:
			self.spell.on_orb_move(self.owner, self.owner)

		if not next_point:
			self.owner.kill()

class OrbSpell(Spell):

	def __init__(self):
		self.melt_walls = False
		self.orb_walk = False
		Spell.__init__(self)
		# Do not require los, check points on the path instead
		self.requires_los = False

	def can_cast(self, x, y):
		if self.get_stat('orb_walk') and self.get_orb(x, y):
			return True

		path = self.caster.level.get_points_in_line(Point(self.caster.x, self.caster.y), Point(x, y))
		if len(path) < 2:
			return False

		start_point = path[1]
		blocker = self.caster.level.get_unit_at(start_point.x, start_point.y)
		if blocker:
			return False

		if not self.get_stat('melt_walls'):
			for p in path:
				if self.caster.level.tiles[p.x][p.y].is_wall():
					return False

		return Spell.can_cast(self, x, y)

	# Called before an orb is moved each turn
	def on_orb_move(self, orb, next_point):
		pass

	def on_orb_collide(self, orb, next_point):
		yield

	def on_orb_walk(self, existing):
		yield

	def on_make_orb(self, orb):
		return 

	def get_orb_impact_tiles(self, orb):
		return [Point(orb.x, orb.y)]

	def get_orb(self, x, y):
		existing = self.caster.level.get_unit_at(x, y)
		if existing and existing.name == self.name:
			return existing
		return None

	def cast(self, x, y):
		existing = self.get_orb(x, y)
		if self.get_stat('orb_walk') and existing:
			for r in self.on_orb_walk(existing):
				yield r
			return

		path = self.caster.level.get_points_in_line(Point(self.caster.x, self.caster.y), Point(x, y))
		if len(path) < 1:
			return

		start_point = path[1]

		# Clear a wall at the starting point if it exists so the unit can be placed
		if self.get_stat('melt_walls'):
			if self.caster.level.tiles[start_point.x][start_point.y].is_wall():
				self.caster.level.make_floor(start_point.x, start_point.y)

		unit = ProjectileUnit()
		unit.name = self.name
		unit.stationary = True
		unit.team = self.caster.team
		unit.turns_to_death = len(path) + 1

		unit.max_hp = self.get_stat('minion_health')
		
		# path[0] = caster, path[1] = start_point, path[2] = first point to move to
		buff = OrbBuff(spell=self, dest=Point(x, y))
		unit.buffs.append(buff)
		
		self.on_make_orb(unit)
		blocker = self.caster.level.get_unit_at(start_point.x, start_point.y)

		# Should be taken care of by can_cast- but weird situations could cause this
		if blocker:
			return

		self.summon(unit, start_point)

	def get_collide_tiles(self, x, y):
		return []

	def get_impacted_tiles(self, x, y):
		existing = self.get_orb(x, y)
		if existing and self.get_stat('orb_walk'):
			return self.get_orb_impact_tiles(existing)
		else:
			return self.caster.level.get_points_in_line(self.caster, Point(x, y))[1:] + self.get_collide_tiles(x, y)

class VoidOrbSpell(OrbSpell):

	def on_init(self):
		self.name = "Arcane Orb"
		self.fire_edge = 0
		self.range = 9
		self.max_charges = 4

		self.minion_health = 15

		self.element = Tags.Arcane
		
		self.tags = [Tags.Arcane, Tags.Orb, Tags.Conjuration]
		self.level = 3

		self.upgrades['cast_blazerip'] = (1, 4, "Blazerip Orb", "[Arcane Orb:unit]施放你的[Blazerip:spell]而不是[Magic Missile:spell]")
		self.upgrades['double_shot'] = (1, 5, "Double Shot", "[Arcane Orb:unit]每回合可以攻击两次")
		self.upgrades['orb_walk'] = (1, 5, "Orb Detonation", "瞄准现有的[Arcane Orb:unit]将其摧毁，摧毁时施放 [12 次:num_targets][Magic Missile:spell]")

	def on_orb_walk(self, existing):
		# Burst
		x = existing.x
		y = existing.y

		for i in range(self.get_stat('num_targets', base=12)):
			elligible_targets = [u for u in self.caster.level.get_units_in_ball(existing, existing.spells[0].range) if are_hostile(self.caster, u)]
			elligible_targets = [u for u in elligible_targets if u in self.caster.level.get_units_in_los(existing)]
			if elligible_targets:
				u = random.choice(elligible_targets)
				for _ in self.caster.level.act_cast(existing, existing.spells[0], u.x, u.y, pay_costs=False, queue=False):
					yield

		existing.kill()

	def on_orb_move(self, orb, next_point):
		if self.get_stat('double_shot'):
			elligible_targets = [u for u in self.caster.level.get_units_in_los(orb) if are_hostile(self.caster, u)]
			if elligible_targets:
				u = random.choice(elligible_targets)
				for _ in self.caster.level.act_cast(orb, orb.spells[0], u.x, u.y, pay_costs=False, queue=False):
					pass

	def on_make_orb(self, orb):
		orb.tags.append(Tags.Arcane) #append Arcane tag
		orb.resists[Tags.Arcane] = 0
		orb.shields = 3

		if self.get_stat('cast_blazerip'):
			grant_minion_spell(Blazerip, orb, self.caster)
		else:
			grant_minion_spell(MagicMissile, orb, self.caster)

	def on_orb_collide(self, orb, next_point):
		orb.level.show_effect(next_point.x, next_point.y, Tags.Arcane)
		yield

	def get_description(self):
		return ("在施法者旁生成一个[Arcane Orb:unit]\n"
				"法球会施放你的[Magic Missile:spell]\n"
				"法球没有意识，每回合向目标飘去\n" # 为什么要强调没有意识，另外是不是应该提一下消失的条件
				"法球只能被[arcane]伤害摧毁").format(**self.fmt_dict())


class FlameRiftSummonBuff(Buff):

	def __init__(self, spell):
		Buff.__init__(self)
		self.spell = spell

	def on_init(self):
		self.name = "Flame Rift"
		self.color = Tags.Fire.color
		self.dmg_dealt = 0
		self.summon_threshold = 20
		self.description = "造成 [%d:damage]后召唤下一个[Flame Rift:unit]" % (self.summon_threshold - self.dmg_dealt)

	def on_advance(self):
		while self.dmg_dealt >= self.summon_threshold:
			self.dmg_dealt -= self.summon_threshold
			unit = FireSpawner()
			unit.turns_to_death = self.spell.get_stat('minion_duration', base=10)
			self.summon(unit, target=self.owner)
		self.description = "造成 [%d:damage]后召唤下一个[Flame Rift:unit]" % (self.summon_threshold - self.dmg_dealt)

class SearingOrb(OrbSpell):

	def on_init(self):
		self.name = "Searing Orb"

		self.minion_damage = 3
		self.minion_health = 8
		self.max_charges = 3
		self.level = 6
		self.range = 9

		self.radius = 3

		self.tags = [Tags.Fire, Tags.Orb, Tags.Conjuration]

		self.upgrades['explosive'] = (1, 2, "Explosive Orb", "[Searing Orb:unit]消失时施放你的[Flameburst:spell]")
		self.upgrades['melt_walls'] = (1, 4, "Matter Melting", "[Searing Orb:unit]的轨迹可以经过和融化墙壁") # 太拗口了
		#changed the functionality of this upgrade a bit, it was pretty powerful so I tried making it more situational but also more rewarding. What do you think?
		self.upgrades['flame_rift'] = (1, 5, "Flame Rift", "[Searing Orb:unit]每造成 [20:damage]，在其附近召唤一个持续 [10:minion_duration]的[Flame Rift:unit]") 

	def get_description(self):
		return ("在施法者旁召唤一个[Searing Orb:unit]\n"
				"法球每回合对视线内的所有单位造成 [{minion_damage}:fire]\n"
				"施法者不受伤害\n"
				"法球没有意识，每回合向目标飘去\n"
				"法球只能被[ice]伤害摧毁").format(**self.fmt_dict())

	def on_make_orb(self, orb):
		orb.resists[Tags.Ice] = 0
		if self.get_stat('flame_rift'):
			orb.apply_buff(FlameRiftSummonBuff(self))

	def on_orb_move(self, orb, next_point):
		damage = self.get_stat('minion_damage')
		for u in orb.level.get_units_in_los(next_point):
			if u == self.caster:
				continue
			if u == orb:
				continue
			dmg_dealt = u.deal_damage(damage, Tags.Fire, self)
			if self.get_stat('flame_rift'):
				buff = orb.get_buff(FlameRiftSummonBuff)
				if buff:
					buff.dmg_dealt += dmg_dealt

	def on_orb_collide(self, orb, next_point):
		orb.level.show_effect(next_point.x, next_point.y, Tags.Fire)
		if self.get_stat('explosive'):
			flameburst_spell = self.caster.get_or_make_spell(FlameBurstSpell)
			for _ in self.caster.level.act_cast(orb, flameburst_spell, next_point.x, next_point.y, pay_costs=False, queue=False):
				yield
		yield
# 原来你丫也是法球？
class BallLightning(OrbSpell):

	def on_init(self):
		self.name = "Ball Lightning"

		self.num_targets = 3
		self.minion_damage = 6
		self.minion_health = 12

		self.level = 5
		self.range = 9
		self.max_charges = 4

		self.radius = 4

		self.tags = [Tags.Orb, Tags.Lightning, Tags.Conjuration]

		self.upgrades['final_burst'] = (1, 4, "Final Burst", "[Ball Lightning:unit]消失时施放你的[Arc Lightning:spell]")
		self.upgrades['drakebirth'] = (1, 4, "Drakebirth", "[Ball Lightning:unit]消失时施放你的[Storm Drake:spell]")
		self.upgrades['pyrostatics'] = (1, 7, "Pyrostatics", "[Ball Lightning:unit]每回合会施放你的[Pyrostatic Pulse:spell]")

	def get_description(self):
		return ("在施法者旁召唤一个[Ball Lightning:unit]\n"
		  		"法球每回合对视线内的 [{num_targets}:num_targets]随机单位发射闪电束，闪电束造成 [{minion_damage}:lightning]\n"
				"法球没有意识，每回合向目标飘去\n"
				"法球只能被[lightning]伤害摧毁").format(**self.fmt_dict())

	def on_make_orb(self, orb):
		orb.resists[Tags.Lightning] = 0

	def on_orb_walk(self, orb):
		targets = [u for u in orb.level.get_units_in_los(orb) if are_hostile(u, self.caster) and (Tags.Construct in u.tags or Tags.Lightning in u.tags)]

		for t in targets:
			pull(t, orb, 3)
			t.deal_damage(self.get_stat('minion_damage'), Tags.Physical, self)
			yield

	def on_orb_move(self, orb, next_point):
		targets = [u for u in orb.level.get_units_in_los(next_point) if are_hostile(u, self.caster)]
		random.shuffle(targets)
		for i in range(self.get_stat('num_targets')):
			if not targets:
				break
			target = targets.pop()
			
			if self.get_stat('pyrostatics'):
				pyrostatic_pulse = self.caster.get_or_make_spell(PyrostaticPulse)
				
				# Pull stats from wizard, but shoot the beam from the orb
				pyrostatic_pulse.statholder = self.caster
				pyrostatic_pulse.caster = orb
				pyrostatic_pulse.owner = orb

				self.caster.level.act_cast(orb, pyrostatic_pulse, target.x, target.y, pay_costs=False)
			for p in orb.level.get_points_in_line(next_point, target, find_clear=True)[1:]:
				if orb.level.get_unit_at(p.x, p.y) == orb:
					continue
				orb.level.deal_damage(p.x, p.y, self.get_stat('minion_damage'), Tags.Lightning, self)

	def on_orb_collide(self, orb, next_point):
		orb.level.show_effect(next_point.x, next_point.y, Tags.Lightning)
		if self.get_stat('final_burst'):
			arc_lightning = self.caster.get_or_make_spell(ArcLightning)
			self.caster.level.act_cast(orb, arc_lightning, next_point.x, next_point.y, pay_costs=False)
		if self.get_stat('drakebirth'):
			lightning_drake = self.caster.get_or_make_spell(SummonStormDrakeSpell)
			self.caster.level.act_cast(orb, lightning_drake, next_point.x, next_point.y, pay_costs=False)
		yield

class EnchantmentRefractionUpgrade(Upgrade):

	def __init__(self, spell):
		Upgrade.__init__(self)
		self.spell = spell

	def on_init(self):
		self.name = "Enchantment Refraction"
		self.description = "[Glass Orb:unit]会模仿所有你对自己施放的[enchantment]法术"
		self.owner_triggers[EventOnSpellCast] = self.on_spell_cast
		self.level = 4

	def on_spell_cast(self, evt):
		if self.owner.level.get_unit_at(evt.x, evt.y) == self.owner and Tags.Enchantment in evt.spell.tags:
			for u in self.owner.level.units:
				if self.spell.get_orb(u.x, u.y):
					enchantment_spell = type(evt.spell)()
					enchantment_spell.statholder = self.owner
					enchantment_spell.owner = u
					enchantment_spell.caster = u
					for _ in self.owner.level.act_cast(u, enchantment_spell, u.x, u.y, pay_costs=False, queue=False):
						pass

class GlassOrbSpell(OrbSpell):

	def on_init(self):
		self.name = "Glass Orb"
		
		self.minion_health = 8
		self.duration = 2
		self.level = 3
		self.max_charges = 5
		self.radius = 3
		self.range = 9

		self.tags = [Tags.Arcane, Tags.Orb, Tags.Conjuration]

		self.upgrades['petrification'] = (1, 3, "Petrification Orb", "[Glass Orb:unit]每回合施放你的[Petrify:spell]")
		self.upgrades['shards'] = (1, 3, "Orb Shards", "[Glass Orb:unit]每回合发射[两片:num_targets]玻璃碎片，分别对视线内的随机敌人造成 [16:physical]")
		self.add_upgrade(EnchantmentRefractionUpgrade(self))

	def get_description(self):
		return ("在施法者旁生成一个[Glass Orb:unit]\n"
				"法球每回合对[{radius}:radius]内的所有单位造成[glassify]\n"
				+ text.glassify_desc + "\n" + 
				"法球没有意识，每回合向目标飘去\n"
				"法球只能被[physical]伤害摧毁").format(**self.fmt_dict())

	def on_make_orb(self, orb):
		orb.resists[Tags.Physical] = -100
		orb.shields = 9

	def on_orb_move(self, orb, next_point):
		for p in orb.level.get_points_in_ball(next_point.x, next_point.y, self.get_stat('radius')):
			unit = orb.level.get_unit_at(p.x, p.y)
			if not unit:
				orb.level.show_effect(p.x, p.y, Tags.Glassification)
			
			if unit and unit != orb and unit != self.caster:
				if not are_hostile(orb, unit) and self.get_stat('shield'):
					if unit.shields < 3:
						unit.add_shields(1)
				elif are_hostile(orb, unit):
					unit.apply_buff(GlassPetrifyBuff(), self.get_stat('duration'))
					if self.get_stat('petrification') and unit:
						petrify_spell = self.caster.get_or_make_spell(PetrifySpell)
						for _ in self.caster.level.act_cast(self.caster, petrify_spell, unit.x, unit.y, pay_costs=False, queue=False):
							pass
		
		if self.get_stat('shards'):
			elligible_targets = [u for u in self.caster.level.get_units_in_los(Point(next_point.x, next_point.y)) if are_hostile(u, self.caster)]
			
			for i in range(min(2, len(elligible_targets))):
				unit = elligible_targets[i]
				for point in Bolt(self.caster.level, orb, elligible_targets[i]):
					self.caster.level.projectile_effect(point.x, point.y, proj_name="glassification", proj_origin=next_point, proj_dest=unit)
				unit.deal_damage(self.get_stat('damage', base=16), Tags.Physical, self)

	def on_orb_collide(self, orb, next_point):
		orb.level.show_effect(next_point.x, next_point.y, Tags.Physical)
		yield

	def on_orb_walk(self, orb):
		for stage in Burst(orb.level, orb, self.get_stat('radius') * 2):
			for point in stage:
				unit = orb.level.get_unit_at(point.x, point.y)
				
				if unit:
					if not are_hostile(orb, unit) and self.get_stat('shield'):
						if unit.shields < 3:
							unit.add_shields(1)
					else:
						unit.apply_buff(GlassPetrifyBuff(), self.get_stat('duration') * 2)
				# Todo- some glassier effect?
				orb.level.show_effect(point.x, point.y, Tags.Arcane)
			yield

class FrozenOrbSpell(OrbSpell):

	def on_init(self):
		self.name = "Ice Orb"

		self.minion_damage = 6
		self.radius = 4
		self.range = 9
		self.minion_health = 40
		self.level = 4

		self.max_charges = 5

		self.tags = [Tags.Orb, Tags.Conjuration, Tags.Ice]

		self.freeze_chance = 0
		self.dmg_dealt = 0
		self.upgrades['freeze_damage'] = (1, 4, "Frostgleam", "[Ice Orb:unit]额外对[frozen]的敌人造成一份[arcane]伤害")
		self.upgrades['summon_winter_faery'] = (1, 5, "Faebound Orb", "[Ice Orb:unit]每造成 [75:damage]，召唤一个[Ice Faery:unit]")
		self.upgrades['cast_blizzard'] = (1, 8, "Blizzard Orb", "[Ice Orb:unit] casts your Blizzard on an 8 turn cooldown.")

	def get_description(self):
		return ("在施法者旁生成一个[Ice Orb:unit]\n"
				"法球每回合对[{radius}:radius]内的所有单位造成 [{minion_damage}:ice]\n"
				+ text.frozen_desc + # 没有冻结效果啊，基本 freeze_chance 不是 0 吗
				"法球没有意识，每回合向目标飘去\n"
				"法球只能被[fire]伤害摧毁").format(**self.fmt_dict())

	def on_make_orb(self, orb):
		orb.resists[Tags.Fire] = 0
		if self.get_stat('cast_blizzard'):
			grant_minion_spell(BlizzardSpell, orb, self.caster, cool_down=8)

	def make_winter_fae(self):
		winter_fae = FairyIce()
		apply_minion_bonuses(self, winter_fae)
		return winter_fae

	def on_orb_move(self, orb, next_point):
		for p in orb.level.get_points_in_ball(next_point.x, next_point.y, self.get_stat('radius')):
			unit = orb.level.get_unit_at(p.x, p.y)
			if unit and are_hostile(orb, unit):
				dmg = unit.deal_damage(self.get_stat('minion_damage'), Tags.Ice, self)

				if self.get_stat('freeze_damage') and unit.get_buff(FrozenBuff):
					dmg += unit.deal_damage(self.get_stat('minion_damage'), Tags.Arcane, self)

				if self.get_stat('summon_winter_faery'):
					self.dmg_dealt += dmg
					while self.dmg_dealt >= 75:
						self.dmg_dealt -= 75
						winter_fae = self.make_winter_fae()
						self.summon(winter_fae, next_point)

				if random.randint(0, 100) < self.get_stat('freeze_chance'):
					unit.apply_buff(FrozenBuff(), self.get_stat('duration'))
			else:
				if random.random() < .5:
					orb.level.deal_damage(p.x, p.y, 0, Tags.Ice, self)

	def on_orb_collide(self, orb, next_point):
		orb.level.show_effect(next_point.x, next_point.y, Tags.Ice)
		yield

	def get_extra_examine_tooltips(self):
		return [self.spell_upgrades[0], self.spell_upgrades[1], self.make_winter_fae(), self.spell_upgrades[2]]
	
class OrbControlSpell(Spell):

	def on_init(self):
		self.name = "Orb Control"

		self.tags = [Tags.Sorcery, Tags.Orb]

		self.range = 9

		self.level = 4
		self.requires_los = False
		self.max_charges = 11

	def get_description(self): # 看起来这里是唯一用到 orb 这个 tag 的地方
		return ("使所有你控制的[orb]重新启程前往目标地块")

	def cast_instant(self, x, y, channel_cast=False):

		for u in self.caster.level.units:
			if u.team != self.caster.team:
				continue
			buff = u.get_buff(OrbBuff)
			if buff:
				path = self.caster.level.get_points_in_line(u, Point(x, y))[1:]
				u.turns_to_death = len(path) + 1
				buff.dest = Point(x, y)
				
	def get_impacted_tiles(self, x, y):
		tiles = set()
		for u in self.caster.level.units:
			if u.team != self.caster.team:
				continue
			buff = u.get_buff(OrbBuff)
			if buff:
				path = self.caster.level.get_points_in_line(u, Point(x, y))
				for p in path:
					tiles.add(p)
		return tiles

class DominateBuff(Buff):

	def __init__(self, caster, decay=False):
		Buff.__init__(self)
		self.caster = caster
		self.color = Color(255, 180, 180)
		self.stack_type = STACK_NONE
		self.buff_type = BUFF_TYPE_CURSE
		self.decay = decay

	def on_applied(self, owner):
		self.old_team = owner.team
		self.owner.team = self.caster.team

	def on_unapplied(self):
		self.owner.team = self.old_team
		if self.decay:
			self.owner.deal_damage(self.owner.cur_hp // 2, Tags.Physical, self)

class Dominate(Spell):

	def on_init(self):
		self.name = "Dominate"
		self.range = 5
		self.max_charges = 4
	
		self.tags = [Tags.Arcane, Tags.Enchantment]
		self.level = 3

		self.hp_threshold = 40
		self.check_cur_hp = 0

		self.upgrades['hp_threshold'] = (40, 3, 'HP Threshold', '增加可以[Dominate:spell]的最大生命值上限') # 到 40？
		self.upgrades['check_cur_hp'] = (1, 4, 'Brute Force', '根据当前生命值而不是最大生命值来决定是否可以[Dominate:spell]')
		self.upgrades['make_lich'] = (1, 4, "Undead Servitude", "使目标转化为巫妖")

	def can_cast(self, x, y):
		if not Spell.can_cast(self, x, y):
			return False
		unit = self.caster.level.get_unit_at(x, y)
		if unit is None:
			return False
		if not are_hostile(unit, self.caster):
			return False
		hp = unit.cur_hp if self.get_stat('check_cur_hp') else unit.max_hp
		return hp <= self.get_stat('hp_threshold')

	def cast(self, x, y):
		unit = self.caster.level.get_unit_at(x, y)
		if self.get_stat('make_lich'):
			BossSpawns.apply_modifier(BossSpawns.Lich, unit)
		unit.team = self.caster.team
		yield

	def get_description(self):
		return ("使不超过 [{hp_threshold} 点最大生命:heal]的敌人变成你的随从").format(**self.fmt_dict())

class ElementalEyeBuff(Buff):

	def __init__(self, element, damage, freq, spell):
		Buff.__init__(self)
		self.element = element
		self.damage = damage
		self.freq = max(1, freq)
		self.cooldown = freq
		self.color = element.color
		self.buff_type = BUFF_TYPE_BLESS

		freq_str = "每回合" if self.freq == 1 else ("每 %d 回合" % self.freq)
		self.description = "%s对视线内一个随机敌人造成 [%d:%s]" % (freq_str, self.damage, self.element.name)
		self.spell = spell

	def on_advance(self):

		self.cooldown -= 1
		if self.cooldown <= 0:
			self.cooldown = self.freq
			possible_targets = self.owner.level.units
			possible_targets = [t for t in possible_targets if self.owner.level.are_hostile(t, self.owner)]
			possible_targets = [t for t in possible_targets if self.owner.level.can_see(t.x, t.y, self.owner.x, self.owner.y)]

			if possible_targets:
				target = random.choice(possible_targets)
				self.owner.level.queue_spell(self.shoot(Point(target.x, target.y)))
				self.cooldown = self.freq

	def shoot(self, target):
		if not self.spell.get_stat('replace_cast'):
			self.owner.level.show_effect(0, 0, Tags.Sound_Effect, 'sorcery_ally')
			path = self.owner.level.get_points_in_line(Point(self.owner.x, self.owner.y), target, find_clear=True)

			for point in path:
				self.owner.level.deal_damage(point.x, point.y, 0, self.element, self.spell)
				u = self.owner.level.get_unit_at(point.x, point.y)

			unit = self.owner.level.get_unit_at(target.x, target.y)
			self.owner.level.deal_damage(target.x, target.y, self.damage, self.element, self.spell)
			
			if unit and self.spell.get_stat('cascade') and not unit.is_alive():
					possible_targets = self.owner.level.units
					possible_targets = [t for t in possible_targets if self.owner.level.are_hostile(t, self.owner)]
					possible_targets = [t for t in possible_targets if self.owner.level.can_see(t.x, t.y, self.owner.x, self.owner.y)]

					if possible_targets:
						target = random.choice(possible_targets)
						self.owner.level.queue_spell(self.shoot(target))
		else:
			path = self.owner.level.get_points_in_line(Point(self.owner.x, self.owner.y), target, find_clear=True)
			
			for point in path:
				self.owner.level.deal_damage(point.x, point.y, 0, self.element, self.spell)
			
			replacement_spell = self.owner.get_or_make_spell(self.replacement_spell)
			for _ in self.owner.level.act_cast(self.owner, replacement_spell, target.x, target.y, pay_costs=False, queue=False):
				pass
		
		self.on_shoot(target)
		yield

	def on_shoot(self, target):
		pass

class RageEyeBuff(ElementalEyeBuff):

	def __init__(self, freq, berserk_duration, spell):
		ElementalEyeBuff.__init__(self, Tags.Physical, 0, freq, spell)
		self.berserk_duration = berserk_duration
		self.name = "Eye of Rage"
		freq_str = "每回合" if self.freq == 1 else ("每 %d 回合" % self.freq)
		self.description = freq_str + "每回合使视线内一个随机敌人[berserk] [%d:duration]" % self.berserk_duration # 要不然是造成 0 点物理伤害，虽然真的有人看 buff 效果吗
		self.color = Tags.Nature.color
		self.asset = ['status', 'rage_eye']

	def on_shoot(self, target):
		units = [self.owner.level.get_unit_at(target.x, target.y)]
		if self.spell.get_stat('connected_group'):
			units = self.owner.level.get_connected_group_from_point(target.x, target.y, check_hostile=True)
		for unit in units:
			if unit:
				if self.spell.get_stat('lycanthrophy') and Tags.Living in unit.tags and unit.cur_hp <= 25:
					unit.kill()
					newunit = Werewolf()
					apply_minion_bonuses(self.spell, newunit)

					self.spell.summon(newunit, target=unit)
					newunit.apply_buff(BerserkBuff(), 14)
				
				else:
					unit.apply_buff(BerserkBuff(), self.berserk_duration)
					if self.spell.get_stat('fiery_aura'):
						fiery_aura_buff = DamageAuraBuff(2, Tags.Fire, self.spell.get_stat('radius', base=2), friendly_fire=True)
						fiery_aura_buff.name = "Burning Rage"
						unit.apply_buff(fiery_aura_buff, self.berserk_duration)


class PenetratingGazeBuff(Buff):

	def on_init(self):
		self.name = "Electrified"
		self.color = Tags.Lightning.color
		self.resists[Tags.Lightning] = -50
		self.stack_type = STACK_REPLACE
		self.asset = ['status', 'amplified_lightning']

# Split these into 2 classes so they stack properly
class LightningEyeBuff(ElementalEyeBuff):

	def __init__(self, damage, freq, spell):
		ElementalEyeBuff.__init__(self, Tags.Lightning, damage, freq, spell)
		self.name = "Eye of Lightning"
		self.color = Tags.Lightning.color
		self.asset = ['status', 'lightning_eye']
		self.replacement_spell = ThunderStrike

	def on_shoot(self, target):
		if self.spell.get_stat('applies_buff'):
			unit = self.owner.level.get_unit_at(target.x, target.y)
			if unit:
				unit.apply_buff(PenetratingGazeBuff())

		path = self.owner.level.get_points_in_line(Point(self.owner.x, self.owner.y), target, find_clear=True)
		for point in path[1:]:
			u = self.owner.level.get_unit_at(point.x, point.y)
			if u and self.spell.get_stat('healing') and not self.owner.level.are_hostile(u, self.owner):
				self.owner.level.deal_damage(point.x, point.y, -self.damage, Tags.Heal, self.spell)
				u.add_shields(1)

class FireEyeBuff(ElementalEyeBuff):

	def __init__(self, damage, freq, spell):
		ElementalEyeBuff.__init__(self, Tags.Fire, damage, freq, spell)
		self.name = "Eye of Fire"
		self.color = Tags.Fire.color
		self.asset = ['status', 'fire_eye']
		self.replacement_spell = FireballSpell

	def on_unapplied(self):
		for i in range(self.spell.get_stat('summon_eyeball')):
			unit = FlamingEye()
			self.spell.summon(unit, self.owner)

class IceEyeBuff(ElementalEyeBuff):

	def __init__(self, damage, freq, spell):
		ElementalEyeBuff.__init__(self, Tags.Ice, damage, freq, spell)
		self.name = "Eye of Ice"
		self.color = Tags.Ice.color
		self.asset = ['status', 'ice_eye']
		self.replacement_spell = Iceball

	def on_shoot(self, target):
		unit = self.owner.level.get_unit_at(target.x, target.y)
		if unit and self.spell.get_stat('freezing'):
			unit.apply_buff(FrozenBuff(), self.spell.get_stat('duration', base=3))

	def on_unapplied(self):
		for i in range(self.spell.get_stat('summon_eyeball')):
			unit = FrostEye()
			unit.spells[0].buff_duration = max([2 + self.spell.duration - 30, 2]) #buffs by diff between 30 and spell's duration, min of 2
			self.spell.summon(unit, self.owner)

class EyeOfFireSpell(Spell):

	def on_init(self):
		self.range = 0
		self.max_charges = 4
		self.name = "Eye of Fire"
		self.damage = 15
		self.element = Tags.Fire
		self.duration = 30
		self.shot_cooldown = 3
		
		self.stats.append('shot_cooldown')
		
		self.upgrades['replace_cast'] = (1, 5, "Eye of Fireballs", "[Eye of Fire:spell]改为施放你的[Fireball:spell]")
		self.upgrades['summon_eyeball'] = (1, 2, "Fiery Onlooker", "[Eye of Fire:spell]效果结束时召唤一个[Flaming Eyeball:unit]")
		self.upgrades['cascade'] = (1, 3, "Eye of Conflaguration", "[Eye of Fire:spell]击杀敌人时，再射击一次")

		self.tags = [Tags.Fire, Tags.Enchantment, Tags.Eye]
		self.level = 2

	def cast_instant(self, x, y):
		buff = FireEyeBuff(self.get_stat('damage'), self.get_stat('shot_cooldown'), self)
		buff.element = self.element
		self.caster.apply_buff(buff, self.get_stat('duration'))

	def get_extra_examine_tooltips(self):
		return [self.spell_upgrades[0], self.spell_upgrades[1], FlamingEye(), self.spell_upgrades[2]]

	def get_description(self):
		return ("每 [{shot_cooldown}:shot_cooldown]对视线一个随机敌人造成 [{damage}:fire]\n"
				"持续 [{duration}:duration]").format(**self.fmt_dict())

class EyeOfLightningSpell(Spell):

	def on_init(self):
		self.range = 0
		self.max_charges = 4
		self.name = "Eye of Lightning"
		self.damage = 15
		self.element = Tags.Lightning
		self.duration = 30
		self.shot_cooldown = 3

		self.stats.append('shot_cooldown')

		self.replacement_spell = ThunderStrike

		self.upgrades['healing'] = (1, 3, "Archon Eye", "[Eye of Lightning:spell]攻击的敌人与你之间的友军恢复 [15:heal]、获得 [1:shields]") # 天杀的拗口
		self.upgrades['replace_cast'] = (1, 4, "Eye of Thunderstrike", "[Eye of Lightning:spell]改为施放你的[Thunderstrike:spell]")
		self.upgrades['applies_buff'] = (1, 4, "Penetrating Gaze", "[Eye of Lightning:spell]对目标施加不叠加的 [-50% 闪电抗性:lightning]")

		self.tags = [Tags.Lightning, Tags.Enchantment, Tags.Eye]
		self.level = 2

	def cast_instant(self, x, y):
		buff = LightningEyeBuff(self.get_stat('damage'), self.get_stat('shot_cooldown'), self)
		buff.element = self.element
		self.caster.apply_buff(buff, self.get_stat('duration'))

	def get_description(self):
		return ("每 [{shot_cooldown}:shot_cooldown]对视线一个随机敌人造成 [{damage}:lightning]\n"
				"持续 [{duration}:duration]").format(**self.fmt_dict())

class EyeOfIceSpell(Spell):

	def on_init(self):
		self.range = 0
		self.max_charges = 4
		self.name = "Eye of Ice"
		self.damage = 15
		self.element = Tags.Ice
		self.duration = 30
		self.shot_cooldown = 3
		
		self.replacement_spell = Iceball

		self.stats.append('shot_cooldown')
		
		self.upgrades['summon_eyeball'] = (1, 2, "Frosty Onlooker", "[Eye of Ice:spell]效果结束时召唤一个[Frosty Eyeball:unit]")
		self.upgrades['freezing'] = (1, 3, "Eye of Freezing", "[Eye of Ice:spell]使目标[frozen] [3:duration]")
		self.upgrades['replace_cast'] = (1, 6, "Eye of Iceballs", "[Eye of Ice:spell]改为施放你的[Iceball:spell]")

		self.tags = [Tags.Ice, Tags.Enchantment, Tags.Eye]
		self.level = 2

	def cast_instant(self, x, y):
		buff = IceEyeBuff(self.get_stat('damage'), self.get_stat('shot_cooldown'), self)
		buff.element = self.element
		self.caster.apply_buff(buff, self.get_stat('duration'))

	def get_extra_examine_tooltips(self):
		return [self.spell_upgrades[0], FrostEye(), self.spell_upgrades[1], self.spell_upgrades[2]]

	def get_description(self):
		return ("每 [{shot_cooldown}:shot_cooldown]对视线一个随机敌人造成 [{damage}:ice]\n"
				"持续 [{duration}:duration]").format(**self.fmt_dict())

class EyeOfRageSpell(Spell):

	def on_init(self):
		self.range = 0
		self.max_charges = 4
		self.name = "Eye of Rage"
		self.duration = 20
		self.shot_cooldown = 3
		self.stats.append('shot_cooldown')

		self.berserk_duration = 2
		self.stats.append('berserk_duration')

		self.upgrades['lycanthrophy'] = (1, 5, "Lycanthropy", "[Eye of Rage:spell]使一个 [25:heal]以下的[living]单位陷入[berserk]时。杀死该单位，将其为复活[Werewolf:unit]，不继承生命值，[Werewolf:unit][berserk][14:duration]")
		self.upgrades['connected_group'] = (1, 5, "Infectious Rage", "[Eye of Rage:spell]影响相连的一组敌人")
		self.upgrades['fiery_aura'] = (1, 5, "Burning Rage", "目标单位获得伤害周围单位的火焰光环")

		self.tags = [Tags.Nature, Tags.Enchantment, Tags.Eye]
		self.level = 2

	def cast_instant(self, x, y):
		buff = RageEyeBuff(self.get_stat('shot_cooldown'), self.get_stat('berserk_duration'), self)
		self.caster.apply_buff(buff, self.get_stat('duration'))

	def get_description(self):
		return ("每 [{shot_cooldown}:shot_cooldown]使视线一个随机敌人[berserk] [{berserk_duration}:duration].\n"
				"持续 [{duration}:duration].").format(**self.fmt_dict())

class NightmareBuff(DamageAuraBuff):

	def __init__(self, spell):
		self.spell = spell
		DamageAuraBuff.__init__(self, damage=self.spell.aura_damage, radius=self.spell.get_stat('radius'), damage_type=[Tags.Arcane, Tags.Dark], friendly_fire=False)

	def get_description(self):
		return "%d damage dealt" % self.damage_dealt

	def on_unapplied(self):
		creatures = []

		if self.spell.get_stat("electric_dream"):
			creatures = [(Elf, 80), (Thunderbird, 35), (SparkSpirit, 25)]
		if self.spell.get_stat("dark_dream"):
			creatures = [(OldWitch, 80), (Werewolf, 35), (Raven, 25)]
		if self.spell.get_stat("fever_dream"):
			creatures = [(FireSpawner, 80), (FireSpirit, 35), (FireLizard, 25)]

		for spawner, cost in creatures:
			for i in range(self.damage_dealt // cost):
				unit = spawner()
				unit.turns_to_death = random.randint(4, 13)
				apply_minion_bonuses(self.spell, unit)
				self.summon(unit, sort_dist=False, radius=self.spell.get_stat('radius'))


class NightmareSpell(Spell):

	def on_init(self):

		self.range = 0
		self.max_charges = 2
		self.name = "Nightmare Aura"
		self.aura_damage = 2
		self.radius = 6
		self.duration = 20

		self.stats.append('aura_damage')

		self.upgrades['dark_dream'] = (1, 5, "Dark Dream", "效果结束时根据造成的伤害召唤一定数量的[Raven:unit]、[Werewolf:unit]、[Old Witch:unit]，分别持续 [4 到 13 回合:duration]", "dream")
		self.upgrades['electric_dream'] = (1, 5, "Electric Dream", "效果结束时根据造成的伤害召唤一定数量的[Spark Spirit:unit]、[Thunderbird:unit]、[Aelf:unit]，分别持续 [4 到 13 回合:duration]", "dream")
		self.upgrades['fever_dream'] = (1, 5, "Fever Dream", "效果结束时根据造成的伤害召唤一定数量的[Fire Lizard:unit]、[Fire Spirit:unit]、[Flame Rift:unit]，分别持续 [4 到 13 回合:duration]", "dream")

		self.tags = [Tags.Enchantment, Tags.Dark, Tags.Arcane]
		self.level = 3

	def cast_instant(self, x, y):
		buff = NightmareBuff(self)
		buff.stack_type = STACK_REPLACE
		buff.color = Tags.Arcane.color
		buff.name = "Nightmare Aura"
		buff.source = self
		self.caster.apply_buff(buff, self.get_stat('duration'))

	def get_description(self):
		return ("每回合对[{radius}:radius]内的所有敌人造成 [{aura_damage} 点:damage][arcane]或[dark]伤害\n"
				"伤害数值固定，不受能力或效果修正\n"
				"持续 [{duration}:duration]").format(**self.fmt_dict())

class CockatriceSkinSpell(Spell):

	def on_init(self):
		self.range = 0
		self.max_charges = 4
		self.name = "Basilisk Armor"
		self.duration = 10

		self.upgrades['max_charges'] = 4
		self.upgrades['duration'] = 5

		self.tags = [Tags.Enchantment, Tags.Nature, Tags.Arcane]
		self.level = 3

	def cast_instant(self, x, y):
		self.caster.apply_buff(cockatriceScaleArmorBuff(), self.get_stat('duration'))

	def get_description(self):
		return ("一个敌方单位把你作为法术或者攻击的目标时，那个单位被[petrified] [2:duration]\n"
				"持续 [{duration}:duration]").format(**self.fmt_dict())

class WatcherFormBuff(Stun):

	def __init__(self, spell):
		Stun.__init__(self)
		self.spell = spell

	def on_applied(self, owner):
		self.name = "Watcher Eye"
		self.color = Tags.Enchantment.color

	def on_advance(self):

		possible_targets = self.owner.level.units
		possible_targets = [t for t in possible_targets if self.owner.level.are_hostile(t, self.owner)]

		if not self.spell.get_stat('void_watcher'):
			possible_targets = [t for t in possible_targets if self.owner.level.can_see(t.x, t.y, self.owner.x, self.owner.y)]

		if possible_targets:
			random.shuffle(possible_targets)
			target = max(possible_targets, key=lambda t: distance(t, self.owner))
			self.owner.level.queue_spell(self.shoot(target))
		else:
			# Show the effect fizzling
			self.owner.deal_damage(0, Tags.Lightning, self)

	def shoot(self, target):
		spell_to_cast = self.owner.get_or_make_spell(LightningBoltSpell)
		if self.spell.get_stat('pyrostatic_watcher'):
			spell_to_cast = self.owner.get_or_make_spell(PyrostaticPulse)
		elif self.spell.get_stat('void_watcher'):
			spell_to_cast = self.owner.get_or_make_spell(VoidBeamSpell)
		elif self.spell.get_stat('chain_lightning_watcher'):
			spell_to_cast = self.owner.get_or_make_spell(ChainLightningSpell)

		for _ in self.owner.level.act_cast(self.owner, spell_to_cast, target.x, target.y, pay_costs=False, queue=False):
			yield

class WatcherFormDefenses(Buff):

	def __init__(self, spell):
		Buff.__init__(self)
		self.spell = spell
		self.transform_asset_name = "watcher"
		self.stack_type = STACK_TYPE_TRANSFORM
		self.resists[Tags.Physical] = 100
		self.resists[Tags.Lightning] = 100
		self.resists[Tags.Fire] = 75
		self.resists[Tags.Poison] = 100
		if self.spell.get_stat('void_watcher'):
			self.resists[Tags.Arcane] = 100
		elif self.spell.get_stat('pyrostatic_watcher'):
			self.resists[Tags.Fire] = 100
		self.color = Tags.Enchantment.color
		self.name = "Watcher Form"

class WatcherFormSpell(Spell):

	def on_init(self):
		self.name = "Watcher Form"
		self.range = 0
		self.max_charges = 5
		self.duration = 5
		self.element = Tags.Lightning
		self.tags = [Tags.Enchantment, Tags.Lightning, Tags.Arcane]
		self.level = 4

		self.upgrades['pyrostatic_watcher'] = (1, 3, "Pyrostatic Watcher Form", "改为施放你的[Pyrostatic Pulse:spell]\n获得[100% 火焰抗性:fire]")
		self.upgrades['void_watcher'] = (1, 4, "Void Watcher Form", "改为施放你的[Void Beam:spell]\n获得[100% 奥术抗性:arcane]\n可以对视线外的敌人施放")
		self.upgrades['chain_lightning_watcher'] = (1, 5, "Chain Watcher Form", "改为施放你的[Chain Lightning:spell]")

	def cast_instant(self, x, y):
		self.caster.apply_buff(WatcherFormBuff(self), self.get_stat('duration'))
		self.caster.apply_buff(WatcherFormDefenses(self), self.get_stat('duration') + 1)

	def get_description(self):
		return ("每回合对视线内最远的敌人施放你的[Lightning Bolt:spell]\n"
		  		"你不能移动和施法\n"
				"获得 [100% 物理抗性:physical]\n"
				"获得 [75% 火焰抗性:fire]\n"
				"获得 [100% 闪电抗性:lightning]\n"
				"获得 [100% 毒素抗性:poison]\n"
				"持续 [{duration}:duration]").format(**self.fmt_dict())

class ImpCallBuff(Buff):

	def __init__(self, spell):
		Buff.__init__(self)
		self.name = "Imp Call"
		self.description = "每回合召唤小鬼"
		self.spell = spell
		self.buff_type = BUFF_TYPE_BLESS
		self.asset = ['status', 'imp_call']


	def on_applied(self, owner):
		self.casts = 0
		self.cast_this_turn = False
		self.color = Tags.Conjuration.color

	def on_advance(self):
		self.owner.level.queue_spell(self.summon_imps())

	def summon_imps(self):
		self.owner.level.show_effect(0, 0, Tags.Sound_Effect, 'summon_3')
		for i in range(self.spell.get_stat('num_summons')):
			imp = random.choice(self.spell.get_imp_choices())()
			imp.turns_to_death = self.spell.get_stat('minion_duration')
			self.spell.summon(imp, self.owner)
			yield

class ChaosBuddiesNew(Upgrade):

	def on_init(self):
		self.name = "Endless Swarm"
		self.description = "每 [9:duration]再召唤一只小鬼"
		# 九回合只招一只？四费？seriously？
		self.counter = 10
		self.level = 4

	def on_advance(self):
		self.counter -= 1
		spells = [s for s in self.owner.spells if isinstance(s, ImpGateSpell)]
		
		if not spells:
			return

		spell = spells[0]

		if self.counter <= 0:
			imp = random.choice(spell.get_imp_choices())()
			self.summon(imp)
			self.counter = 10


class ImpGateSpell(Spell):

	def on_init(self):
		self.name = "Imp Swarm"
		self.range = 0
		self.max_charges = 3
		self.duration = 7
		self.tags = [Tags.Enchantment, Tags.Conjuration, Tags.Chaos]
		self.level = 4

		self.minion_health = 5
		self.minion_damage = 3
		self.minion_duration = 11
		self.minion_range = 3
		self.num_summons = 2

		self.add_upgrade(ChaosBuddiesNew())
		self.upgrades['metalswarm'] = (1, 4, "Metal Swarm", "[Imp Swarm:spell]召唤[Copper Imp:unit]和[Furnace Imp:unit]而不是[Fire Imp:unit]和[Spark Imp:unit]", "swarm")
		self.upgrades['darkswarm'] = (1, 3, "Dark Swarm", "[Imp Swarm:spell]召唤[Rot Imp:unit]、[Void Imp:unit]和[Insanity Imp:unit]而不是[Fire Imp:unit]、[Spark Imp:unit]和[Iron Imp:unit]", "swarm")

		self.imp_choices = [self.fire_imp, self.spark_imp, self.iron_imp]

	def get_description(self):
		return ("每回合在施法者旁召唤 [{num_summons}:num_summons]小鬼\n"
		  		"持续 [{duration}:duration]\n\n"
				"随机选择[Fire Imp:unit]、[Iron Imp:unit]、[Spark Imp:unit]中的一种\n"
				"小鬼有 [{minion_health}:minion_health]，会飞\n"
				"小鬼的远程攻击造成 [{minion_damage}:minion_damage]，范围 [{minion_range}:minion_range]\n"
				"小鬼在 [{minion_duration}:minion_duration]回合后消失\n").format(**self.fmt_dict())

	def fire_imp(self):
		unit = FireImp()
		apply_minion_bonuses(self, unit)
		return unit

	def spark_imp(self):
		unit = SparkImp()
		apply_minion_bonuses(self, unit)
		return unit

	def iron_imp(self):
		unit = IronImp()
		apply_minion_bonuses(self, unit)
		return unit

	def copper_imp(self):
		unit = CopperImp()
		apply_minion_bonuses(self, unit)
		return unit

	def furnace_imp(self):
		unit = FurnaceImp()
		apply_minion_bonuses(self, unit)
		return unit

	def tungsten_imp(self):
		unit = TungstenImp()
		apply_minion_bonuses(self, unit)
		return unit

	def rot_imp(self):
		unit = RotImp()
		apply_minion_bonuses(self, unit)
		return unit

	def void_imp(self):
		unit = VoidImp()
		apply_minion_bonuses(self, unit)
		return unit

	def insanity_imp(self):
		unit = InsanityImp()
		apply_minion_bonuses(self, unit)
		return unit

	def get_extra_examine_tooltips(self):
		return [self.fire_imp(), self.spark_imp(), self.iron_imp(), 
				self.spell_upgrades[2], 
				self.spell_upgrades[0], self.copper_imp(), self.furnace_imp(),
				self.spell_upgrades[1], self.rot_imp(), self.void_imp(), self.insanity_imp()]

	def get_imp_choices(self):
		if self.get_stat('metalswarm'):
			return [self.copper_imp, self.furnace_imp, self.tungsten_imp]
		elif self.get_stat('darkswarm'):
			return [self.rot_imp, self.void_imp, self.insanity_imp]
		else:
			return self.imp_choices

	def cast_instant(self, x, y):
		self.caster.apply_buff(ImpCallBuff(self), self.get_stat('duration'))

class LightningHaloBuff(Buff):
	
	def __init__(self, spell):
		Buff.__init__(self)
		self.spell = spell
		self.name = "Lightning Halo"
		self.description = "每回合对环状范围造成[lightning]伤害"
		self.buff_type = BUFF_TYPE_BLESS
		self.asset = ['status', 'lightning_halo']
		self.stack_type = STACK_REPLACE

	def on_init(self):
		self.radius = 1
		self.ring_of_fire = False

	def on_applied(self, owner):
		self.color = Tags.Lightning.color

	def on_advance(self):
		self.owner.level.show_effect(0, 0, Tags.Sound_Effect, 'sorcery_ally')
		points = self.owner.level.get_points_in_ball(self.owner.x, self.owner.y, self.radius)
		points = [p for p in points if p != Point(self.owner.x, self.owner.y) and distance(self.owner, p) >= self.radius - 1]

		for p in points:
			self.owner.level.deal_damage(p.x, p.y, self.spell.get_stat('damage'), self.spell.element, self.spell)
		
		if self.spell.get_stat('radioactivity'):
			targets = self.owner.level.get_units_in_ball(Point(self.owner.x, self.owner.y), self.radius - 1)
			targets = [u for u in targets if are_hostile(u, self.owner)]
			
			for t in targets:
				t.deal_damage(self.spell.get_stat('damage')//2, Tags.Poison, self.spell)
		
		if self.spell.get_stat('ring_of_fire'):
			points_fire = self.owner.level.get_points_in_ball(self.owner.x, self.owner.y, self.radius + 1)
			points_fire = [p for p in points_fire if p != Point(self.owner.x, self.owner.y) and distance(self.owner, p) >= self.radius]
			
			for p in points_fire:
				self.owner.level.deal_damage(p.x, p.y, self.spell.get_stat('damage'), Tags.Fire, self.spell)

		if self.spell.get_stat('expanding'):
			self.radius += 1


class LightningHaloSpell(Spell):

	def on_init(self):
		self.name = "Lightning Halo"
		self.range = 0
		self.max_charges = 5
		self.duration = 9
		self.tags = [Tags.Enchantment, Tags.Lightning]
		self.level = 3
		self.damage = 15
		self.element = Tags.Lightning

		self.radius = 3
		self.upgrades['ring_of_fire'] = (1, 3, "Ring of Fire", "[Lightning Halo:spell]在原本的光圈外添加一格造成[fire]伤害的光圈")
		self.upgrades['radioactivity'] = (1, 3, "Radioactive Field", "对光圈内的敌人造成一半的[poison]伤害") #made it 50% because dealing 100% damage to all units within radius is very powerful
		self.upgrades['expanding'] = (1, 3, "Lightning Nova", "每回合[Lightning Halo:spell] 获得[1:radius]") # 不是你半径变大宽度不变有个卵用
 
	def cast_instant(self, x, y):

		buff = LightningHaloBuff(self)
		buff.radius = self.get_stat('radius')
		self.caster.apply_buff(buff, self.get_stat('duration'))

	def get_impacted_tiles(self, x, y):
		points = self.caster.level.get_points_in_ball(self.caster.x, self.caster.y, self.get_stat('radius'))
		if not self.get_stat('radioactivity'):
			points = [p for p in points if p != Point(self.caster.x, self.caster.y) and distance(self.caster, p) >= self.get_stat('radius') - 1]

		if self.get_stat('ring_of_fire'):
			points_fire = self.owner.level.get_points_in_ball(self.owner.x, self.owner.y, self.radius + 1)
			points_fire = [p for p in points_fire if p != Point(self.owner.x, self.owner.y) and distance(self.owner, p) >= self.radius]
			points += points_fire
		return points

	def get_description(self):
		return ("每回合对[{radius}:radius]圆环范围内的所有敌人造成 [{damage}:lightning] 伤害\n"
		  		"持续 [{duration}:duration]").format(**self.fmt_dict())

class ArcaneVisionSpell(Spell):

	def on_init(self):
		self.name = "Mystic Vision"
		self.range = 0
		self.max_charges = 4
		self.duration = 8
		self.bonus = 5
		self.tags = [Tags.Enchantment, Tags.Arcane]
		self.level = 3

		self.upgrades['duration'] = (8, 2)
		self.upgrades['bonus'] = (5, 4)
		self.upgrades['aura'] = (1, 5, "Vision Aura", "[Mystic Vision:spell]对所有友军单位生效")

	def cast_instant(self, x, y):
		buff = GlobalAttrBonus('range', self.get_stat('bonus'))
		buff.name = "Mystic Vision"
		self.caster.apply_buff(buff, self.get_stat('duration'))

		if self.get_stat('aura'):
			for u in self.owner.level.units:
				if are_hostile(self.owner, u):
					continue
				buff = GlobalAttrBonus('range', self.get_stat('bonus'))
				buff.name = "Mystic Vision"
				u.apply_buff(buff, self.get_stat('duration'))

	def get_description(self):
		return ("所有其他法术获得 [{bonus}:range]范围\n"
		  		"持续 [{duration}:duration]").format(**self.fmt_dict())

class ArcaneDamageSpell(Spell):

	def on_init(self):
		self.name = "Mystic Power"
		self.range = 0
		self.max_charges = 7
		self.duration = 8
		self.bonus = 7
		self.tags = [Tags.Enchantment, Tags.Arcane]
		self.level = 3

		self.upgrades['duration'] = (8, 2)
		self.upgrades['bonus'] = (4, 4, "Damage Bonus")
		self.upgrades['stackable'] = (1, 4, "Intensity", "[Mystic Power:spell]叠加效果而不是持续时间")

	def cast_instant(self, x, y):
		buff = GlobalAttrBonus('damage', self.get_stat('bonus'))
		buff.name = "Mystic Power"
		buff.stack_type = STACK_DURATION if not self.get_stat('stackable') else STACK_INTENSITY
		self.caster.apply_buff(buff, self.get_stat('duration'))

	def get_description(self):
		return ("所有其他法术获得 [{bonus}:damage]\n"
		  		"持续 [{duration}:duration]").format(**self.fmt_dict())

class PainBuff(GlobalAttrBonus):

	def __init__(self, bonus, self_damage):
		GlobalAttrBonus.__init__('damage', bonus)
		self.self_damage = self_damage

	def on_applied(self, owner):
		self.owner_triggers[EventOnMoved] = self.on_moved

	def advance(self):
		owner.deal_damage(self_damage, Tags.Dark, self)

	def on_moved(self):
		self.owner.remove_buff(self)

class PainSpell(Spell):
# not in game
	def on_init(self):
		self.name = "Power of Pain"
		self.range = 0
		self.max_charges = 6
		self.bonus = 7
		self.tags = [Tags.Dark, Tags.Enchantment]
		self.level = 4

		self.self_damage = 4
		self.upgrades['max_charges'] = 6
		self.upgrades['bonus'] = (5, 2)
		self.upgrades['self_damage'] = (-2, 3)

	def cast_instant(self, x, y):
		self.caster.apply_buff(PainBuff(self.bonus))

	def get_description(self):
		return "你的法术造成额外 [%d:damage]。每回合你受到 [%d:dark]。移动时结束。"

class FlameBurstSpell(Spell):

	def on_init(self):
		self.name = "Flame Burst"
		self.range = 0
		self.max_charges = 6
		self.damage = 40
		self.tags = [Tags.Fire, Tags.Sorcery]
		self.level = 4
		self.radius = 8

		self.upgrades['meltflame'] = (1, 2, "Melting Flame", "融化周围一圈的墙", "flame")
		self.upgrades['dawnflame'] = (1, 5, "Bright Flame", "[Flame Burst:spell]造成[holy]而不是[fire]伤害，给予盟友护盾而不是造成伤害", "flame")
		self.upgrades['spreadflame'] = (1, 7, "Spreading Flame", "施放[Flame Burst:spell]消耗所有充能\n每点充能额外增加 [1:damage]、[1:radius]\n[Flame Burst:spell]杀死敌人后减半伤害和半径再次施放", "flame")

	def get_description(self):
		return ("对以施法者为中心[{radius}:radius]内的单位造成 [{damage}:fire]").format(**self.fmt_dict())

	def get_impacted_tiles(self, x, y):
		radius = self.get_stat('radius')
		if self.get_stat('spreadflame'):
			radius += self.cur_charges
		return [p for stage in Burst(self.caster.level, Point(x, y), radius) for p in stage]

	def cast(self, x, y, secondary=False, last_radius=None, last_damage=None):

		if secondary:
			radius = last_radius // 2
			damage = last_damage // 2

			if radius < 2:
				return
			if damage < 0:
				return

		else:
			radius = self.get_stat('radius')
			damage = self.get_stat('damage')

		if not secondary and self.get_stat('spreadflame'):
			radius += self.cur_charges
			damage += self.cur_charges
			self.cur_charges = 0

		to_melt = set([Point(self.caster.x, self.caster.y)])
		slain = []

		stagenum = 0
		for stage in Burst(self.caster.level, Point(x, y), radius):
			dtype = Tags.Holy if self.get_stat('dawnflame') else Tags.Fire
			stagenum += 1

			for p in stage:
				if p.x == self.caster.x and p.y == self.caster.y:
					continue

				friendly = None
				if self.get_stat('dawnflame'):
					friendly = self.caster.level.get_unit_at(p.x, p.y)
					if friendly and are_hostile(self.caster, friendly):
						friendly = None

					if friendly:
						friendly.add_shields(1)

				if not friendly:
					unit = self.caster.level.get_unit_at(p.x, p.y)
					self.caster.level.deal_damage(p.x, p.y, damage, dtype, self)
					if unit and not unit.is_alive():
						slain.append(unit)

				if self.get_stat('meltflame'):
					for q in self.caster.level.get_points_in_ball(p.x, p.y, 1):
						if self.caster.level.tiles[q.x][q.y].is_wall():
							to_melt.add(q)
					
			yield

		if self.get_stat('spreadflame'):
			for unit in slain:
				self.owner.level.queue_spell(self.cast(unit.x, unit.y, secondary=True, last_damage=damage, last_radius=radius))

		if self.get_stat('meltflame'):
			for p in to_melt:
				self.caster.level.make_floor(p.x, p.y)
				self.caster.level.show_effect(p.x, p.y, Tags.Fire)

class SummonFireDrakeSpell(Spell):

	def on_init(self):
		self.name = "Fire Drake"
		self.range = 4
		self.max_charges = 2
		self.tags = [Tags.Fire, Tags.Conjuration, Tags.Dragon]
		self.level = 4

		self.minion_health = 45
		self.minion_damage = 8
		self.breath_damage = FireDrake().spells[0].damage
		self.minion_range = 7

		self.upgrades['broodlings'] = (1, 5, "Broodlings", "[Fire Drake:unit]可以召唤两只[Fire Lizard:unit]，冷却时间 [9:duration]")
		self.upgrades['metal'] = (1, 3, "Metal Dragon", "给予[Fire Drake:unit][metallic]词条")
		self.upgrades['dragon_mage'] = (1, 5, "Dragon Mage", "[Fire Drake:unit]可以施放你的[Blazerip:spell]，冷却时间 [9:duration]")

		self.must_target_empty = True

	def get_description(self):
		return ("在选定地块召唤[Fire Drake:unit]\n"
				"[Fire Drake:unit]有 [{minion_health}:minion_health]，会飞，有 [100% 火焰抗性:fire]\n"
				"[Fire Drake:unit]的吐息造成 [{breath_damage}:fire]\n"
				"[Fire Drake:unit]的近战攻击造成 [{minion_damage}:physical]").format(**self.fmt_dict())

	def make_lizard(self):
		lizard = FireLizard()
		apply_minion_bonuses(self, lizard)
		return lizard

	def cast_instant(self, x, y):
		drake = FireDrake()
		drake.team = self.caster.team
		drake.max_hp = self.get_stat('minion_health')
		drake.spells[0].damage = self.get_stat('breath_damage')
		drake.spells[0].range = self.get_stat('minion_range')
		drake.spells[1].damage = self.get_stat('minion_damage')

		if self.get_stat('dragon_mage'):
			dragon_spell = Blazerip()
			dragon_spell.statholder = self.caster
			dragon_spell.max_charges = 0
			dragon_spell.cur_charges = 0
			dragon_spell.cool_down = 4
			drake.spells.insert(1, dragon_spell)

		if self.get_stat('metal'):
			BossSpawns.apply_modifier(BossSpawns.Metallic, drake)

		if self.get_stat('broodlings'):
			summon = SimpleSummon(self.make_lizard, num_summons=2, cool_down=8)
			drake.spells.insert(0, summon)

		self.summon(drake, Point(x, y))

	def get_extra_examine_tooltips(self):
		return [FireDrake(), self.spell_upgrades[0], self.make_lizard(), self.spell_upgrades[1], BossSpawns.apply_modifier(BossSpawns.Metallic, FireDrake()), self.spell_upgrades[2]]

class LightningSwapBuff(Buff):

	def __init__(self, spell):
		self.spell = spell
		Buff.__init__(self)

	def on_init(self):
		self.global_triggers[EventOnSpellCast] = self.on_spell_cast
		# 很难做到查看单位面板的时候快速滑到最右边查看 tooltip，不知道怎么优化下
		self.description = "被巫师选为[lightning]法术的目标时与巫师交换位置"

	def on_spell_cast(self, evt):
		if not self.spell.get_stat('drake_swap'):
			return
		if evt.caster != self.owner.source.owner:
			return
		if Tags.Lightning not in evt.spell.tags:
			return
		if evt.x != self.owner.x or evt.y != self.owner.y:
			return
		if not self.owner.level.can_stand(self.owner.x, self.owner.y, evt.caster, check_unit=False):
			return
		self.owner.level.act_move(self.owner, evt.caster.x, evt.caster.y, force_swap=True, teleport=True)

class SummonStormDrakeSpell(Spell):

	def on_init(self):
		self.name = "Storm Drake"
		self.range = 4
		self.max_charges = 2
		self.tags = [Tags.Lightning, Tags.Conjuration, Tags.Dragon]
		self.level = 4

		self.minion_health = 45
		self.minion_damage = 8
		self.breath_damage = StormDrake().spells[0].damage
		self.minion_range = 7
		
		self.upgrades['storm_legion'] = (1, 4, "Storm Summoning", "Whenever you cast Storm Drake, up to [2:num_summons] lightning storms in line of sight of the target are converted into drakes")
		self.upgrades['ghost_drake'] = (1, 3, "Ghost Drake", "Summoned Storm Drakes are ghostly.")
		self.upgrades['drake_swap'] = (1, 1, "Drake Swap", "Whenever you target a summoned Storm Drake with a lightning spell, swap places with it.") # 这升级有个卵用
		self.upgrades['dragon_mage'] = (1, 5, "Dragon Mage", "Summoned Storm Drakes can cast Chain Lightning with a 16 turn cooldown.\nThis Lightning Bolt gains all of your upgrades and bonuses.")
	
		self.must_target_empty = True

	def get_extra_examine_tooltips(self):
		return [self.drake(), self.spell_upgrades[0], self.spell_upgrades[1], BossSpawns.apply_modifier(BossSpawns.Ghostly, self.drake()), self.spell_upgrades[2], self.spell_upgrades[3]]

	def drake(self):
		drake = StormDrake()
		drake.max_hp = self.get_stat('minion_health')
		drake.spells[0].damage = self.get_stat('breath_damage')
		drake.spells[0].range = self.get_stat('minion_range')
		drake.spells[1].damage = self.get_stat('minion_damage')
		return drake

	def cast_instant(self, x, y):
		summon_targets = [Point(x, y)]

		if self.get_stat('storm_legion'):
			extra_targets = [t for t in self.caster.level.iter_tiles() if self.caster.level.can_see(x, y, t.x, t.y) and isinstance(t.cloud, StormCloud)]
			random.shuffle(extra_targets)
			extra_targets = extra_targets[:self.get_stat('num_summons', base=2)]
			for t in extra_targets:
				t.cloud.kill()
			summon_targets.extend(extra_targets)

		for t in summon_targets:
			drake = self.drake()

			if self.get_stat('drake_swap'):
				drake.buffs.append(LightningSwapBuff(self))

			if self.get_stat('dragon_mage'):
				dragon_spell = ChainLightningSpell()
				dragon_spell.statholder = self.caster
				dragon_spell.max_charges = 0
				dragon_spell.cur_charges = 0
				dragon_spell.cool_down = 16
				drake.spells.insert(1, dragon_spell)

			if self.get_stat('ghost_drake'):
				BossSpawns.apply_modifier(BossSpawns.Ghostly, drake)

			self.owner.level.show_beam(Point(x, y), t, Tags.Lightning, minor=True)
			self.summon(drake, t)

	def get_description(self):
		return ("Summon a storm drake at target square.\n"
				"Storm drakes have [{minion_health}_HP:minion_health], fly, and have [100_lightning:lightning] resist.\n"
				"Storm drakes have a breath weapon which creates storm clouds that deal [{breath_damage}_lightning:lightning] damage.\n"
				"Storm drakes have a melee attack which deals [{minion_damage}_physical:physical] damage.").format(**self.fmt_dict())
		
class EssenceDrakeBuff(Buff):

	def __init__(self, spell):
		self.spell = spell
		Buff.__init__(self)

	def on_init(self):
		self.global_triggers[EventOnDeath] = self.on_death

	def on_death(self, evt):
		if not self.spell.get_stat('essence_drake'):
			return
		if not evt.damage_event:
			return
		if not are_hostile(self.owner, evt.unit):
			return
		if not evt.damage_event.source.owner == self.owner:
			return

		candidates = [u for u in self.owner.level.units if not are_hostile(u, self.owner) and u.turns_to_death]
		if not candidates:
			return

		candidate = random.choice(candidates)
		candidate.turns_to_death += 5


class SummonVoidDrakeSpell(Spell):

	def on_init(self):
		self.name = "Void Drake"
		self.range = 4
		self.max_charges = 2
		self.tags = [Tags.Arcane, Tags.Conjuration, Tags.Dragon]
		self.level = 4

		self.minion_health = 45
		self.minion_damage = 8
		self.breath_damage = VoidDrake().spells[0].damage
		self.shields = 0
		self.minion_range = 7

		self.upgrades['shields'] = (3, 3)
		self.upgrades['dragon_mage'] = (1, 5, "Dragon Mage", "Summoned Void Drakes can cast Magic Missile with a 3 turn cooldown.\nThis Magic Missile gains all of your upgrades and bonuses.")
		self.upgrades['essence_drake'] = (1, 3, "Essence Drake", "Whenever a summoned Void Drake kills an enemy unit, a random temporary ally gains +5 turns to its duration.")

		self.must_target_empty = True

	def cast_instant(self, x, y):
		drake = VoidDrake()
		drake.team = self.caster.team
		drake.max_hp = self.get_stat('minion_health')
		drake.spells[0].damage = self.get_stat('breath_damage')
		drake.spells[0].range = self.get_stat('minion_range')
		drake.spells[1].damage = self.get_stat('minion_damage')
		drake.shields += self.get_stat('shields')
		drake.buffs.append(EssenceDrakeBuff(self))

		if self.get_stat('dragon_mage'):
			mmiss = MagicMissile()
			mmiss.statholder = self.caster
			mmiss.max_charges = 0
			mmiss.cur_charges = 0
			mmiss.cool_down = 3
			drake.spells.insert(1, mmiss)

		self.summon(drake, Point(x, y))

	def get_description(self):
		return ("Summon a Void Drake at target square.\n"		
				"Void Drakes have [{minion_health}_HP:minion_health], fly, and have [100_arcane:arcane] resist.\n"
				"Void Drakes have a breath weapon which deals [{minion_damage}_arcane:arcane] damage and melts walls.\n"
				"Void Drakes have a melee attack which deals [{minion_damage}_physical:physical] damage.").format(**self.fmt_dict())

class SummonIceDrakeSpell(Spell):

	def on_init(self):
		self.name = "Ice Drake"
		self.range = 4
		self.max_charges = 2
		self.tags = [Tags.Ice, Tags.Conjuration, Tags.Dragon]
		self.level = 4
		
		self.minion_range = 7
		self.minion_health = 45
		self.minion_damage = 8
		self.breath_damage = 7
		self.duration = 2


		self.upgrades['dracolich'] = (1, 4, "Dracolich", "Summoned Ice Drakes are Liches and can create a soul jars.")
		self.upgrades['broodlings'] = (1, 5, "Broodlings", "Summoned Ice Drakes can summon 2 Ice Lizards on a 9 turn cooldown.")
		self.upgrades['dragon_mage'] = (1, 5, "Dragon Mage", "Summoned Ice Drakes can cast Death Chill with an 8 turn cooldown.\nThis Death Chill gains all of your upgrades and bonuses.")

		self.must_target_empty = True

	def get_extra_examine_tooltips(self):
		return [IceDrake(), self.spell_upgrades[0], self.spell_upgrades[1], self.make_lizard(), self.spell_upgrades[2]]

	def make_lizard(self):
		lizard = IceLizard()
		apply_minion_bonuses(self, lizard)
		return lizard

	def cast_instant(self, x, y):
		drake = IceDrake()

		drake.max_hp = self.get_stat('minion_health')
		drake.spells[0].damage = self.get_stat('breath_damage')
		drake.spells[0].range = self.get_stat('minion_range')
		drake.spells[0].freeze_duration = self.get_stat('duration')
		drake.spells[1].damage = self.get_stat('minion_damage')

		if self.get_stat('dragon_mage'):
			dchill = DeathChill()
			dchill.statholder = self.caster
			dchill.max_charges = 0
			dchill.cur_charges = 0
			dchill.cool_down = 8
			drake.spells.insert(1, dchill)

		if self.get_stat('broodlings'):
			summon = SimpleSummon(self.make_lizard, num_summons=2, cool_down=8)
			drake.spells.insert(0, summon)

		if self.get_stat('dracolich'):
			BossSpawns.apply_modifier(BossSpawns.Lich, drake)

		self.summon(drake, Point(x, y))

	def get_description(self):
		return ("Summon an Ice Drake at target square.\n"		
				"Ice Drakes have [{minion_health}_HP:minion_health], fly, and have [100_ice:ice] resist.\n"
				"Ice Drakes have a breath weapon which deals [{minion_damage}_ice:ice] damage and [freezes] units.\n"
				"Ice Drakes have a melee attack which deals [{minion_damage}_physical:physical] damage.").format(**self.fmt_dict())


class SparkSpell(Spell):

	def on_init(self):
		self.name = "Spark"
		self.description = "Deal lightning damage to the target.  Chains to a limited number of nearby targets."
		self.range = 8
		self.max_charges = 26
		self.level = 1
		self.tags = [Tags.Lightning, Tags.Sorcery]
		self.damage = 6

		self.num_targets = 3
		self.cascade_range = 3
		self.upgrades['num_targets'] = (2, 2)
		self.upgrades['damage'] = (6, 2)

	def cast(self, x, y):
		prev = self.caster
		target = Point(x, y)
		targets_left = self.get_stat('num_targets')

		while targets_left > 0 and target:
			targets_left -= 1
			for p in self.caster.level.get_points_in_line(prev, target)[1:]:
				self.caster.level.show_effect(p.x, p.y, Tags.Lightning)
				yield

			self.caster.level.deal_damage(target.x, target.y, self.get_stat('damage'), Tags.Lightning, self)
			yield

			possible_targets = self.caster.level.get_units_in_ball(target, self.get_stat('cascade_range'))

			target_unit = self.caster.level.get_unit_at(target.x, target.y)
			if target_unit in possible_targets:
				possible_targets.remove(target_unit)
			if self.get_stat('no_friendly_fire'):
				possible_targets = [t for t in possible_targets if are_hostile(self.caster, t)]
			if not self.get_stat('wall_pen'):
				possible_targets = [t for t in possible_targets if self.caster.level.can_see(t.x, t.y, target.x, target.y)]

			prev = target
			if possible_targets:
				target = random.choice(possible_targets)
			else:
				target = None

class ChainLightningSpell(Spell):

	def on_init(self):
		self.name = "Chain Lightning"
		self.range = 9
		self.max_charges = 4
		self.tags = [Tags.Lightning, Tags.Sorcery]
		self.level = 3
		self.damage = 12
		self.element = Tags.Lightning

		self.cascade_range = 5
		self.no_friendly_fire = 0
		self.overlap = 1

		self.upgrades['chain_fireball'] = (1, 7, "Chain Fireball", "Cast Fireball for free on each target chain lightning bounces to")
		self.upgrades['weathercraft'] = (1, 3, "Cloud Conductance", "Chain Lightning can arc to blizzards and storm clouds")
		self.upgrades['shield'] = (1, 6, "Lightning Shield", "Chain Lightning can arc to friendly targets.\nFriendly units hit by Chain Lightning gain 1 SH, up to a max of 3, instead of damaged.")

	def get_description(self):
		return ("Fire an arcing bolt of electricity dealing [{damage}_lightning:lightning] damage.\n"
				"The bolt repeatably arcs to new targets within the cascade range.\n"
				"Each arc deals damage to all units along a beam.\n"
				"The bolt can arc up to [{cascade_range}_tiles:radius], and cannot pass through walls.\n"
				"The bolt terminates when it cannot arc to any new targets.").format(**self.fmt_dict())


	def cast(self, x, y):

		prev = self.caster
		target = self.caster.level.get_unit_at(x, y) or Point(x, y)
		already_hit = set()

		def hit_square(x, y):

			unit = self.caster.level.get_unit_at(x, y)
			if unit and not self.caster.level.are_hostile(unit, self.caster) and self.get_stat('shield'):
				if unit.shields < 3:
					unit.add_shields(1)
			else:
				self.caster.level.deal_damage(x, y, self.get_stat('damage'), self.element, self)

		fireball = self.caster.get_or_make_spell(FireballSpell)
		while target:

			# Overlap perk
			
			for p in self.caster.level.get_points_in_line(prev, target, find_clear=True)[1:]:
				if self.overlap:
					hit_square(p.x, p.y)
				else:
					self.caster.level.deal_damage(p.x, p.y, 0, self.element, self)
					yield

			if not self.overlap:
				hit_square(target.x, target.y)
				yield

			# Pause a bit after the bolts if overlap is on
			if self.overlap:
				for i in range(2):
					yield

			if self.get_stat('chain_fireball'):
				s = self.owner.level.act_cast(self.owner, fireball, target.x, target.y, pay_costs=False, queue=False)
				for _ in s:
					pass
				yield

			already_hit.add(Point(target.x, target.y))

			def can_arc(p, prev):
				if p in already_hit:
					return False
				if not self.caster.level.can_see(prev.x, prev.y, p.x, p.y):
					return False
				
				u = self.caster.level.get_unit_at(p.x, p.y)
				if u and are_hostile(self.caster, u):
					return True

				if u and not are_hostile(self.caster, u) and self.get_stat('shield'):
					return True

				c = self.caster.level.tiles[p.x][p.y].cloud
				if c and (type(c) in [StormCloud, BlizzardCloud]) and self.get_stat('weathercraft'):
					return True

				return False

			potential_targets = [p for p in self.caster.level.get_points_in_ball(target.x, target.y, self.get_stat('cascade_range')) if can_arc(p, target)]

			prev = target
			if potential_targets:
				target = random.choice(potential_targets)
			else:
				target = None			

class SoulCharge(Buff):

	def on_init(self):
		self.name = "Soulcharge"
		self.buff_type = BUFF_TYPE_BLESS
		self.color = Tags.Dark.color
		self.spell_bonuses[DeathBolt]['damage'] = 3
		self.stack_type = STACK_INTENSITY

class DeathBolt(Spell):

	def on_init(self):
		self.name = "Death Bolt"
		self.tags = [Tags.Dark, Tags.Sorcery, Tags.Conjuration]
		self.level = 1
		self.damage = 9
		self.element = Tags.Dark
		self.range = 8
		self.max_charges = 15

		self.upgrades['soulbattery'] = (1, 2, "Soul Battery", "Deathbolt gains 3 damage whenever it slays a target, lasts until next realm.")
		self.upgrades['winter'] = (1, 3, "Winter Bolt", "Deathbolt also deals ice damage")
		self.upgrades['chaos'] = (1, 5, "Chaos Skeletons", "Raised skeletons are Chaos skeletons, gaining resistances, a chaos ball attack, and spawning a number of imps on death proportional to their max hp.")

		self.can_target_empty = False
		self.minion_damage = 5

	def cast_instant(self, x, y):		
		unit = self.caster.level.get_unit_at(x, y)
		if unit and Tags.Living in unit.tags:
			# Queue the skeleton raise as the first spell to happen after the damage so that it will pre-empt stuff like ghostfire
			self.caster.level.queue_spell(self.try_raise(self.caster, unit))

		self.caster.level.show_beam(self.caster, Point(x, y), Tags.Dark)

		damage = self.caster.level.deal_damage(x, y, self.get_stat('damage'), Tags.Dark, self)
		if self.get_stat('winter'):
			self.caster.level.deal_damage(x, y, self.get_stat('damage'), Tags.Ice, self)

		if unit and not unit.is_alive() and self.get_stat('soulbattery'):
			self.caster.apply_buff(SoulCharge())
			
	def try_raise(self, caster, unit):
		if unit and unit.cur_hp <= 0 and not self.caster.level.get_unit_at(unit.x, unit.y):
			skeleton = raise_skeleton(caster, unit, source=self)
			if skeleton:
				if self.get_stat('chaos'):
					BossSpawns.apply_modifier(BossSpawns.Chaostouched, skeleton)

				apply_minion_bonuses(self, skeleton)

			yield

	def get_description(self):
		return ("Deals [{damage}_dark:dark] damage to one target.\n"
				"Slain living units are raised as skeletons.\n"
				"Raised skeletons have max HP equal to that of the slain unit, and deal [{minion_damage}_physical:physical] damage in melee.\n"
				"Skeletons of flying units can fly.").format(**self.fmt_dict())

class DeathrouletteStack(Buff):

	def on_init(self):
		self.name = "Roulette"
		self.stack_type = STACK_INTENSITY
		self.color = Tags.Dark.color

class WheelOfFate(Spell):

	def on_init(self):
		self.name = "Wheel of Death"
		self.damage = 200
		self.range = 0
		self.tags = [Tags.Dark, Tags.Sorcery]
		self.element = Tags.Dark
		self.level = 4
		self.max_charges = 12

		self.upgrades['max_charges'] = (3, 4)
		#self.upgrades['cascade'] = (1, 7, "Death Roulette", "On kill, gain a Roulette stack for 4 turns.\nWheel of death hits an additional enemy for each Roulette stack you have at cast time.")
		self.upgrades['cheater'] = (1, 4, "Cheat Fate", "Death Roulette avoids shielded and dark immune enemies, and weights its target selection by current resistance adjusted hitpoints instead of uniformly.")

	def cast(self, x, y):
		
		num_targets = 1 + len([b for b in self.owner.buffs if isinstance(b, DeathrouletteStack)])
		prev_hit = set()

		for i in range(num_targets):
			valid_targets = [u for u in self.caster.level.units if self.caster.level.are_hostile(self.caster, u) and u not in prev_hit]
			if not valid_targets:
				return

			if self.get_stat('cheater'):
				preferred_targets = [t for t in valid_targets if t.resists[Tags.Dark] < 100]
				more_preferred_targest = [t for t in preferred_targets if not t.shields]

				if more_preferred_targest:
					valid_targets = more_preferred_targest
				elif preferred_targets:
					valid_targets = preferred_targets

			if not self.get_stat('cheater'):
				target = random.choice(valid_targets)
			else:
				target = random.choices(valid_targets, weights=[t.cur_hp * (100 - t.resists[Tags.Dark]) for t in valid_targets], k=1)[0]

			prev_hit.add(target)
			target.deal_damage(self.get_stat('damage'), self.element, self)
			if self.get_stat('cascade') and not target.is_alive():
				self.owner.apply_buff(DeathrouletteStack(), self.get_stat('duration', 10))
			self.owner.level.show_path_effect(self.owner, target, Tags.Dark, minor=True)
			for i in range(3):
				yield

	def get_description(self):
		return "Deal [{damage}_dark:dark] damage to a random enemy unit.".format(**self.fmt_dict())

class TouchOfDeath(Spell):

	def on_init(self):
		self.damage = 200
		self.element = Tags.Dark
		self.range = 1
		self.melee = True
		self.can_target_self = False
		self.max_charges = 9
		self.name = "Touch of Death"
		self.tags = [Tags.Dark, Tags.Sorcery]
		self.level = 2

		self.can_target_empty = False

		self.fire_damage = 0
		self.arcane_damage = 0
		self.physical_damage = 0
		self.upgrades['fire_damage'] = (200, 2, "Flametouch")
		self.upgrades['raise_vampire'] = (1, 3, 'Touch of the Vampire', 'When a [living] target dies to touch of death, it is raised as a friendly Vampire.', 'raising')
		self.upgrades['raise_reaper'] = (1, 4, 'Touch of the Reaper', 'When a [living] target dies to touch of death, it is raise as a friendly Reaper for [6:minion_duration] turns', 'raising')
		self.upgrades['hand_of_death'] = (1, 3, 'Hand of Death', 'Touch of death hits up to [4:num_targets] more adjacent targets')

	def get_vamp(self):
		vamp = Vampire()
		apply_minion_bonuses(self, vamp)
		vamp.buffs[0].spawner = self.get_vamp_bat
		return vamp

	def get_vamp_bat(self):
		bat = VampireBat()
		apply_minion_bonuses(self, bat)
		bat.buffs[0].spawner = self.get_vamp
		return bat

	def cast_instant(self, x, y):
		unit = self.caster.level.get_unit_at(x, y)
		targets = [unit]

		if self.get_stat('hand_of_death'):
			potential_extra_targets = [u for u in self.owner.level.get_units_in_ball(self.caster, 1, diag=True)]
			potential_extra_targets = [u for u in potential_extra_targets if are_hostile(self.caster, u) and u != unit]
			random.shuffle(potential_extra_targets)
			targets.extend(potential_extra_targets[:self.get_stat('num_targets', base=4)])

		for unit in targets:
			if not unit:
				continue

			unit.deal_damage(self.get_stat('damage'), self.element, self)
			if self.get_stat('fire_damage'):
				unit.deal_damage(self.get_stat('damage'), Tags.Fire, self)

			if not unit.is_alive() and Tags.Living in unit.tags:
				if self.get_stat('raise_vampire'):
					vampire = self.get_vamp()
					self.summon(vampire, Point(unit.x, unit.y))
				elif self.get_stat('raise_reaper'):
					reaper = Reaper()
					reaper.turns_to_death = self.get_stat('minion_duration', base=6)
					self.summon(reaper, Point(unit.x, unit.y))



	def get_description(self):
		return "Deal [{damage}_dark:dark] damage to one unit in melee range.".format(**self.fmt_dict())

class SealedFateBuff(Buff):

	def __init__(self, spell):
		Buff.__init__(self)
		self.spell = spell
		self.name = "Sealed Fate"
		self.buff_type = BUFF_TYPE_CURSE
		self.asset = ['status', 'sealed_fate']

	def on_applied(self, owner):
		self.color = Tags.Dark.color

	def on_advance(self):
		if self.turns_left == 1:
			self.owner.deal_damage(self.spell.get_stat('damage'), Tags.Dark, self.spell)

			if self.spell.get_stat('spreads'):
				possible_targets = [u for u in self.owner.level.get_units_in_los(self.owner) if u != self.owner and are_hostile(u, self.spell.owner)]
				if possible_targets:
					target = random.choice(possible_targets)
					target.apply_buff(SealedFateBuff(self.spell), self.spell.get_stat('delay'))

class SealFate(Spell):

	def on_init(self):
		self.name = "Seal Fate"
		self.range = 8
		self.max_charges = 13
		self.tags = [Tags.Enchantment, Tags.Dark]
		self.level = 3
		self.delay = 4

		self.stats.append('delay')

		self.damage = 160
		self.upgrades['requires_los'] = (-1, 2, "Blindcasting", "Seal Fate can be cast without line of sight")
		self.upgrades['spreads'] = (1, 2, "Spreading Curse", "When Sealed Fate's duration expires, it jumps to a random enemy in line of sight.")
		self.upgrades['genocide'] = (1, 8, "Genocide", "Seal Fate effects all enemies with the same name as target.")

		self.can_target_empty = False

	def cast_instant(self, x, y):
		unit = self.caster.level.get_unit_at(x, y)
		if not unit:
			return

		if self.get_stat('genocide'):
			units = [u for u in self.caster.level.units if u.name == self.caster.level.get_unit_at(x, y).name]
		else:
			units = [unit]

		for unit in units:
			unit.apply_buff(SealedFateBuff(self), self.get_stat('delay'))

	def get_description(self):
		return "After [{delay}_turns:duration], deal [{damage}_dark:dark] damage to target unit.".format(**self.fmt_dict())

class Volcano(Spell):

	def on_init(self):
		self.name = "Volcanic Eruption"
		self.tags = [Tags.Fire]
		self.max_charges = 5
		self.radius = 6
		self.damage = 52
		self.element = Tags.Fire
		self.flow_range = 3

		self.cast_on_walls = True

		self.tags = [Tags.Fire, Tags.Sorcery]
		self.level = 4
		self.range = 10

		self.upgrades['flow_range'] = (2, 3)
		self.upgrades['requires_los'] = (-1, 2, "Blindcasting", "Volcano can be cast without line of sight")
		self.upgrades['wall_cast']= (1, 4, "Wallcano", "In addition to chasms, volcano may target walls.  Doing so turns the walls into chasms")

	def get_description(self):
		return ("Create a [{radius}_tile:radius] burst of lava in a chasm.\n"
				"The burst flows up to [{flow_range}_tiles:radius] out of the chasm.\n"
				"The lava deals [{damage}_fire:fire] damage").format(**self.fmt_dict())

	def get_chasm_points(self, caster, x, y):
		chasm_points = set([Point(x, y)])

		for i in range(self.radius):
			for point in list(chasm_points):
				for adj in self.caster.level.get_points_in_ball(point.x, point.y, 1):
					tile = self.caster.level.tiles[adj.x][adj.y]
					if tile.is_chasm or (tile.is_wall() and self.get_stat('wall_cast')):
						chasm_points.add(adj)

		return chasm_points

	def get_impacted_tiles(self, x, y):
		aoe = set(self.get_chasm_points(self.caster, x, y))
		for i in range(self.flow_range):
			for point in set(aoe):
				for adj in self.caster.level.get_points_in_ball(point.x, point.y, 1):
					if self.caster.level.tiles[adj.x][adj.y].can_see:
						aoe.add(adj)
		return aoe

	def cast(self, x, y):
		aoe = set(self.get_chasm_points(self.caster, x, y))

		for point in aoe:
			if self.get_stat('wall_cast') and self.caster.level.tiles[point.x][point.y].is_wall():
				self.caster.level.make_chasm(point.x, point.y)
			self.caster.level.deal_damage(point.x, point.y, self.get_stat('damage'), self.element, self)
		yield
		for i in range(self.get_stat('flow_range')):
			for point in set(aoe):
				for adj in self.caster.level.get_points_in_ball(point.x, point.y, 1):
					if self.caster.level.tiles[adj.x][adj.y].can_see and adj not in aoe:
						self.caster.level.deal_damage(adj.x, adj.y, self.get_stat('damage'), self.element, self)
						aoe.add(adj)
			yield

	def can_cast(self, x, y):
		tile = self.caster.level.tiles[x][y]
		if self.get_stat('wall_cast'):
			if not tile.is_chasm and not tile.is_wall():
				return False
		else:
			if not tile.is_chasm:
				return False

		return Spell.can_cast(self, x, y)

class SoulSwap(Spell):

	def on_init(self):
		self.requires_los = False
		self.range = RANGE_GLOBAL

		self.name = "Soul Swap"
		
		self.max_charges = 9

		self.level = 2
		self.tags = [Tags.Dark, Tags.Sorcery, Tags.Translocation]

		self.upgrades['forced_transfer'] = (1, 2, 'Forced Transfer', 'Soul Swap can target enemy undead units as well.')
		self.upgrades['max_charges'] = (9, 2)

	def can_cast(self, x, y):
		unit = self.caster.level.get_unit_at(x, y)
		if not unit:
			return False
		if Tags.Undead not in unit.tags:
			return False
		if are_hostile(self.caster, unit) and not self.get_stat('forced_transfer'):
			return False
		if not self.caster.level.can_move(self.caster, x, y, teleport=True, force_swap=True):
			return False
		return Spell.can_cast(self, x, y)

	def cast_instant(self, x, y):

		# Check again that the target is valid in case this is being cast from from cantrip cascade or something
		if not self.can_cast(x, y):
			return False

		if self.caster.level.can_move(self.caster, x, y, teleport=True, force_swap=True):
			self.caster.level.act_move(self.caster, x, y, teleport=True, force_swap=True)

	def get_description(self):
		return "Swap places with a friendly [undead] unit."

class UnderworldPortal(Spell):

	def on_init(self):
		self.requires_los = False
		self.range = 99
		self.name = "Underworld Passage"
		self.max_charges = 3
		self.tags = [Tags.Dark, Tags.Sorcery, Tags.Translocation]
		self.level = 3
		self.imps_summoned = 0

		self.upgrades['quick_cast'] = (1, 2, "Quickcast", "Casting underworld passage does not end your turn")
		self.upgrades['summon_rockworms'] = (1, 3, "Tremorsensitivity", "Summons 2 Rockworms on each end.")

	def get_description(self):
		return ("Teleport to any tile adjacent to a chasm.\n"
				"Can only be cast while adjacent to a chasm.")

	def can_cast(self, x, y):
		
		if not self.caster.level.can_stand(x, y, self.caster):
			return False

		for center in [self.caster, Point(x, y)]:
			next_to_chasm = False
			for p in self.caster.level.get_points_in_ball(center.x, center.y, 1.5, diag=True):
				if self.caster.level.tiles[p.x][p.y].is_chasm:
					next_to_chasm = True
					break
			if not next_to_chasm:
				return False
		return Spell.can_cast(self, x, y)

	def cast_instant(self, x, y):

		old_loc = Point(self.caster.x, self.caster.y)
		self.caster.level.act_move(self.caster, x, y, teleport=True)

		if self.get_stat('summon_rockworms'):
			for p in [old_loc, self.caster]:
				for i in range(2):
					self.summon(RockWurm(), target=p)

		for point in [old_loc, self.caster]:
			for i in range(self.get_stat('imps_summoned')):
				p = self.caster.level.get_summon_point(point.x, point.y, sort_dist=False)
				if p:
					imp = random.choice([FireImp(), SparkImp(), IronImp()])
					imp.max_hp += self.get_stat('minion_health')
					imp.spells[0].damage += self.get_stat('minion_damage')
					imp.team = self.caster.team
					self.summon(imp, p)

class VoidSpawn(Spell):

	def on_init(self):

		self.name = "Void Spawning"
		self.max_charges = 10
		self.tags = [Tags.Arcane, Tags.Conjuration]
		self.level = 2

		self.minion_duration = 10

		self.upgrades['minion_duration'] = 10
		self.upgrades['requires_los'] = -1

	def get_description(self):
		return "Summon a void spawner for 10 turns.  The void spawner is a stationary arcane creature that summons void bombers."

	def get_impacted_tiles(self, x, y):
		targets = self.caster.level.get_tiles_in_ball(x, y, 1.5)
		targets = set(t for t in targets if t.can_walk and not t.unit)
		return targets

	def cast_instant(self, x, y):

		voidspawner = VoidSpawner()
		voidspawner.team = self.caster.team
		voidspawner.turns_to_death = self.get_stat('minion_duration')
		self.summon(voidspawner, Point(x, y))


class SummonEarthElemental(Spell):

	def on_init(self):
		self.tags = [Tags.Nature, Tags.Conjuration]
		self.name = "Earthen Sentinel"
		self.max_charges = 5
		self.level = 3
		self.minion_damage = 20
		self.minion_health = 120
		self.minion_duration = 15
		self.minion_attacks = 1

		self.upgrades['earthquake_totem'] = (1, 6, "Earthquake Totem", "Earthen Sentinel gains your Earthquake spell on a 3 turn cool down.", "totem")
		self.upgrades['stinging_totem'] = (1, 5, "Stinging Totem", "Earthen Sentinel gains your Poison Sting spell.", "totem")
		self.upgrades['holy_totem'] = (1, 7, "Holy Totem", "Earthen Sentinel gains your Heavenly Blast spell on a 2 turn cool down.", "totem")

		self.must_target_empty = True

	def can_cast(self, x, y):
		tile = self.caster.level.tiles[x][y]
		return tile.unit is None and tile.can_walk and Spell.can_cast(self, x, y)

	def cast_instant(self, x, y):
		ele = Unit()
		ele.name = "Earth Elemental"
		ele.sprite.char = 'E'
		ele.sprite.color = Color(190, 170, 140)
		ele.spells.append(SimpleMeleeAttack(self.get_stat('minion_damage'), attacks=self.get_stat('minion_attacks')))
		ele.max_hp = self.get_stat('minion_health')
		ele.turns_to_death = self.get_stat('minion_duration')
		ele.stationary = True
		ele.resists[Tags.Physical] = 50
		ele.resists[Tags.Fire] = 50
		ele.resists[Tags.Lightning] = 50
		ele.tags = [Tags.Elemental]

		spell = None
		if self.get_stat('earthquake_totem'):
			spell = EarthquakeSpell()
			spell.cool_down = 3
		if self.get_stat('stinging_totem'):
			spell = PoisonSting()
		if self.get_stat('holy_totem'):
			spell = HolyBlast()
			spell.cool_down = 2

		if spell:
			spell.statholder = self.caster
			spell.max_charges = 0
			ele.spells.insert(0, spell)

		self.summon(ele, target=Point(x, y))

	def get_description(self):
		return ("Summon an Earth Elemental.\n"
				"Earth elementals have [{minion_health}_HP:minion_health], [50_physical:physical] resist, [50_fire:fire] resist, [50_lightning:lightning] resist, and cannot move.\n"
				"Earth elementals have a melee attack which deals [{minion_damage}_physical:physical]."
				"The elemental vanishes after [{minion_duration}_turns:minion_duration].").format(**self.fmt_dict())


class CallSpirits(Spell):

	def on_init(self):
		self.tags = [Tags.Dark, Tags.Conjuration, Tags.Sorcery]
		self.name = "Ghostball"
		self.radius = 1
		self.minion_damage = 1
		self.minion_health = 4
		self.minion_duration = 14
		self.max_charges = 6
		self.level = 3
		self.damage = 11

		self.upgrades['radius'] = (1, 3)

		self.upgrades['king'] = (1, 5, "Ghost King", "A Ghost King is summoned at the center of the ghost ball.", "center summon")
		self.upgrades['mass'] = (1, 4, "Ghost Mass", "A Ghostly Mass is summoned at the center of the ghost ball.", "center summon")

	def get_ai_target(self):
		# target random empty tile if possible
		targets = [p for p in self.owner.level.get_points_in_ball(self.owner.x, self.owner.y, self.get_stat('range')) if self.can_cast(p.x, p.y)]
		empty_targets = [p for p in targets if not self.owner.level.get_unit_at(p.x, p.y)]

		if empty_targets:
			return random.choice(empty_targets)
		else:
			return random.choice(targets)

	def cast_instant(self, x, y):

		points = self.caster.level.get_points_in_ball(x, y, self.get_stat('radius'))
		for point in points:
			unit = self.caster.level.tiles[point.x][point.y].unit
			if unit is None and self.caster.level.tiles[point.x][point.y].can_see:
				ghost = Ghost()
				if point.x == x and point.y == y:
					if self.get_stat('king'):
						ghost = GhostKing()
					elif self.get_stat('mass'):
						ghost = GhostMass()

				ghost.turns_to_death = self.get_stat('minion_duration')
				apply_minion_bonuses(self, ghost)
				self.summon(ghost, point)

			elif unit and are_hostile(unit, self.caster):
				unit.deal_damage(self.get_stat('damage'), Tags.Dark, self)

	def get_description(self):
		return ("Deal [{damage}_dark:dark] damage to enemy units in a [{radius}_tile:radius] radius.\n"
				"Summon ghosts at empty tiles in the radius.\n"
				"Ghosts have [{minion_health}_HP:minion_health], fly, [100_physical:physical] resist, [50_dark:dark] resist, and passively blink.\n"
				"Ghosts have a melee attack which deals [{minion_damage}_dark:dark] damage.\n"
				"The ghosts vanish after [{minion_duration}_turns:minion_duration].").format(**self.fmt_dict())

	def get_impacted_tiles(self, x, y):
		return [p for p in self.caster.level.get_points_in_ball(x, y, self.get_stat('radius'))]

class MysticMemory(Spell):

	def on_init(self):
		self.tags = [Tags.Arcane]
		self.name = "Mystic Memory"
		self.max_charges = 1
		self.level = 6
		self.range = 0
		self.max_channel = 5

		self.upgrades['distant_memory'] = (1, 2, "Distant Memory", "Prioritize regaining charges of depleted spells.")
		self.upgrades['max_channel'] = (5, 3, "Deep Reflection")
		self.upgrades['memory_shield'] = (1, 3, "Shield of Memories", "Gain 2 SH each time you gain charges from this spell.")

	def cast(self, x, y, channel_cast=False):
		if not channel_cast:
			self.caster.apply_buff(ChannelBuff(self.cast, Point(x, y)), self.get_stat('max_channel'))
			return
		
		spells = [s for s in self.caster.spells if s.cur_charges < s.get_stat('max_charges') and s != self]
		if self.get_stat('distant_memory'):
			for s in spells:
				if s != self and s.cur_charges == 0:
					#check if any spells are depleted before prioritizing them
					spells = [s for s in self.caster.spells if s != self and s.cur_charges == 0]
					break
		if spells:
			choice = random.choice(spells)
			choice.cur_charges = min(choice.cur_charges + 1, choice.get_stat('max_charges'))
			if self.get_stat('memory_shield'):
				self.caster.add_shields(2)

		yield

	def can_cast(self, x, y):
		if not [s for s in self.caster.spells if s != self and s.cur_charges < s.get_stat('max_charges')]:
			return False
		return Spell.can_cast(self, x, y)

	def get_description(self):
		return "While channeling, regain a charge of a random other spell. Channels for 5 turns."

class ConjureMemories(Spell):

	def on_init(self):
		self.tags = [Tags.Arcane, Tags.Conjuration]
		self.name = "Conjure Memories"
		self.max_charges = 1
		self.range = 0
		self.level = 4

		self.charges_regained = 1
		self.upgrades['charges_regained'] = (1, 2)
		self.upgrades['max_charges'] = (1, 2)

	def get_description(self):
		return "Regain a charge of each of your conjuration spells"

	def cast_instant(self, x, y):

		for s in self.caster.spells:

			if s == self:
				continue

			if Tags.Conjuration not in s.tags:
				continue

			s.cur_charges += self.get_stat('charges_regained')
			s.cur_charges = min(s.get_stat('max_charges'), s.cur_charges)


class WovenSorceryBuff(Buff):

	def on_applied(self, owner):
		self.name = "Woven"
		self.color = Tags.Sorcery.color
		self.tag_bonuses[Tags.Sorcery]['damage'] = 3*len([s for s in owner.spells if Tags.Enchantment in s.tags])
		self.tag_bonuses[Tags.Sorcery]['duration'] = len([s for s in owner.spells if Tags.Sorcery in s.tags])
		self.tag_bonuses[Tags.Enchantment]['damage'] = 3*len([s for s in owner.spells if Tags.Enchantment in s.tags])
		self.tag_bonuses[Tags.Enchantment]['duration'] = len([s for s in owner.spells if Tags.Sorcery in s.tags])
		self.buff_type = BUFF_TYPE_BLESS
		self.asset = ['status', 'woven']

class WovenSorcerySpell(Spell):

	def on_init(self):
		self.max_charges = 4
		self.duration = 20
		self.name = "Weave Sorcery"
		self.tags = [Tags.Sorcery, Tags.Enchantment]
		self.level = 4
		self.range = 0
		self.upgrades['duration'] = (20, 3)

	def get_description(self):
		return "Your sorcery and enchantment spells get +3 damage for each enchantment spell you know and +1 duration for each sorcery spell you know.  Lasts 20 turns."

	def cast_instant(self, x, y):
		self.caster.apply_buff(WovenSorceryBuff(), self.get_stat('duration'))

class PermenanceBuff(Buff):

	def on_init(self):
		' '
		self.global_bonuses['minion_duration'] = 5
		self.global_bonuses['duration'] = 5
		self.name = "Permanence"
		self.color = Tags.Enchantment.color
		self.buff_type = BUFF_TYPE_BLESS
		self.asset = ['status', 'permenance']

class Permenance(Spell):

	def on_init(self):
		self.max_charges = 4
		self.duration = 20
		self.name = "Permanence"
		self.tags = [Tags.Enchantment]
		self.level = 4
		self.range = 0
		self.upgrades['duration'] = (20, 3)

	def cast_instant(self, x, y):
		self.caster.apply_buff(PermenanceBuff(), self.get_stat('duration'))

	def get_description(self):
		return ("Your spells and temporary summons last an extra [5_turns:duration].\n"
				"This effect lasts [{duration}_turns:duration].").format(**self.fmt_dict())

class DeathGazeSpell(Spell):

	def on_init(self):
		self.name = "Vampiric Gaze"
		self.range = 0
		self.tags = [Tags.Dark, Tags.Blood, Tags.Sorcery]
		self.level = 4
		self.max_charges = 10
		self.damage = 6
		self.hp_cost = 5

		self.upgrades['toxic_gaze'] = (1, 3, "Toxic Gaze", "Vampiric Gaze also deals poison damage")
		self.upgrades['vampire_tax'] = (1, 4, "Vampiric Tax", "You heal for 100% of the damage dealt")
		self.upgrades['refract'] = (1, 6, "Refracting Gaze", "Each bolt bounces once to a random enemy in line of sight of the original target")
		
	def get_description(self):
		return ("Each allied unit deals [{damage}_dark:dark] damage to a random enemy in its line of sight."
				"Each allied unit heals for all damage dealt.").format(**self.fmt_dict())

	def cast(self, x, y):
		bolts = []
		for unit in self.caster.level.units:
			if unit == self.caster or self.caster.level.are_hostile(self.caster, unit):
				continue

			possible_targets = [u for u in self.caster.level.units if self.caster.level.are_hostile(unit, u) and self.caster.level.can_see(unit.x, unit.y, u.x, u.y)]
			if possible_targets:
				target = random.choice(possible_targets)
				bolts.append(self.bolt(unit, target))

		while bolts:
			bolts = [b for b in bolts if next(b)]
			yield
			
	def bolt(self, source, target, bounce_origin=None):

		disp_tag = Tags.Dark
		bolt_start = bounce_origin if bounce_origin else source
		for point in Bolt(self.caster.level, bolt_start, target):
			# TODO- make a flash using something other than deal_damage
			self.caster.level.deal_damage(point.x, point.y, 0, disp_tag, self)
			if self.get_stat('toxic_gaze'):
				if disp_tag == Tags.Dark:
					disp_tag = Tags.Poison
				else:
					disp_tag = Tags.Dark
			yield True

		damage = self.get_stat('damage')
		dealt = target.deal_damage(damage, Tags.Dark, self)

		if self.get_stat('toxic_gaze'):
			dealt += target.deal_damage(damage, Tags.Poison, self)

		if dealt:
			# Heal the unit
			source.heal(dealt, self)
			# Heal the caster if upgraded
			if self.get_stat('vampire_tax'):
				self.caster.heal(dealt, self)

		if (bounce_origin is None) and self.get_stat('refract'):
			possible_targets = [u for u in self.caster.level.units if self.caster.level.are_hostile(self.owner, u) and self.caster.level.can_see(target.x, target.y, u.x, u.y)]
			if possible_targets:
				new_target = random.choice(possible_targets)
				bolt = self.bolt(source, new_target, bounce_origin=target)
				while next(bolt):
					yield True

		yield False

class BoneBarrageSpell(Spell):

	def on_init(self):
		self.name = "Bone Barrage"
		self.range = 14
		self.tags = [Tags.Dark, Tags.Sorcery]
		self.level = 4
		self.max_charges = 7

		self.upgrades['beam'] = (1, 6, "Bone Spears", "Bone Barrage damages all targets in a beam from the minion to the target")
		self.upgrades['dark'] = (1, 5, "Cursed Bones", "Bone Barrage also deals dark damage")
		#self.upgrades['animation'] = (1, 6, "Shambler Assembly", "Bone Barrage can target empty tiles.\nIf it does, it creates a bone shambler at that tile with hp equal to the damage it would have dealt.")

	def can_cast(self, x, y):
		u = self.owner.level.get_unit_at(x, y)
		if not u and not self.get_stat('animation'):
			return False
		return Spell.can_cast(self, x, y)

	def get_description(self):
		return ("Your summoned allies in line of sight of the target take [physical] damage equal to half their health.\n"
				"Each affected ally deals that much [physical] damage to the target.")

	def get_impacted_tiles(self, x, y):
		start = Point(x, y)
		yield start
		for u in self.caster.level.get_units_in_los(start):
			if not are_hostile(u, self.caster) and u != self.caster:
				yield u
				if self.get_stat('beam'):
					for p in self.caster.level.get_points_in_line(u, Point(x, y), find_clear=True):
						yield p

	def cast(self, x, y):
		bolts = []
		target = self.caster.level.get_unit_at(x, y)

		total_damage = 0
		for u in self.caster.level.get_units_in_los(Point(x, y)):
			if u == self.caster:
				continue
			if are_hostile(u, self.caster):
				continue
			if u.resists[Tags.Physical] >= 100:
				continue

			half_hp = math.ceil(u.cur_hp / 2)
			damage = u.deal_damage(half_hp, Tags.Physical, self)
			total_damage += damage

			if damage > 0:
				bolts.append(self.bolt(u, Point(x, y), damage))

		while bolts:
			bolts = [b for b in bolts if next(b)]
			yield

		if not target and self.get_stat('animation') and total_damage:
			monster = BoneShambler(total_damage)
			self.summon(monster, target=Point(x, y))

	def hit(self, target, damage):
		target.deal_damage(damage, Tags.Physical, self)
		if self.get_stat('dark'):
			target.deal_damage(damage, Tags.Dark, self)

	def bolt(self, source, target, damage):

		for point in Bolt(self.caster.level, source, target):
			
			self.caster.level.projectile_effect(point.x, point.y, proj_name='bone_arrow', proj_origin=source, proj_dest=target)
			yield True

			unit = self.caster.level.get_unit_at(point.x, point.y)
			if self.get_stat('beam') and unit:
				self.hit(unit, damage)

		unit = self.caster.level.get_unit_at(target.x, target.y)
		if unit:
			self.hit(unit, damage)
		yield False

class InvokeSavagerySpell(Spell):

	def on_init(self):
		self.name = "Invoke Savagery"
		self.range = 0
		self.tags = [Tags.Nature, Tags.Sorcery]
		self.level = 2
		self.max_charges = 11
		self.damage = 14
		self.duration = 2

		self.kills = 0
		self.targets = []

		self.upgrades['poison'] = (10, 2, "Venomous Bite", "Poisons targets for 10 turns.")
		self.upgrades['leap_attack'] = (1, 4, "Savage Leap", "Instead of a melee attack, do a leap attack.")
		self.upgrades['recharge_wolf'] = (1, 4, "Scavengers", "Every 3 kills gain a wolf charge.")

	def get_impacted_tiles(self, x, y):
		return [u for u in self.caster.level.units if u != self.caster and not are_hostile(u, self.caster)]

	def cast(self, x, y):
		self.targets = []
		if self.get_stat('leap_attack'):
			attack = LeapAttack(damage=self.get_stat('damage'), range=3, buff=[Stun, Poison][self.get_stat('poison') > 0], buff_duration=[self.get_stat('duration'), self.get_stat('poison')][self.get_stat('poison') > 0])
		else:
			attack = SimpleMeleeAttack(damage=self.get_stat('damage'), buff=[Stun, Poison][self.get_stat('poison') > 0], buff_duration=[self.get_stat('duration'), self.get_stat('poison')][self.get_stat('poison') > 0])

		for unit in self.caster.level.units:
			if unit == self.caster or are_hostile(self.caster, unit):
				continue
			if Tags.Living not in unit.tags:
				continue

			possible_targets = [u for u in self.caster.level.get_units_in_ball(unit, radius=attack.range, diag=True) if are_hostile(u, self.caster)]
			if possible_targets:
				target = random.choice(possible_targets)
				attack.statholder = unit
				attack.caster = unit
				attack.owner = unit
				for _ in self.caster.level.act_cast(unit, attack, target.x, target.y, pay_costs=False, queue=False):
					pass
				if not target.is_alive() and self.get_stat('recharge_wolf'):
					self.kills += 1
				yield
			
			while self.kills >= 3:
				self.kills -= 3
				wolf_spell = self.caster.get_spell(SummonWolfSpell)
				if wolf_spell:
					wolf_spell.cur_charges = min(wolf_spell.cur_charges + 1, wolf_spell.get_stat('max_charges'))

	def get_description(self):
		return ("Each living ally attacks a random enemy unit in melee range.\n"
				"The attack deals [{damage}_physical:physical] damage and inflicts [{duration}_turns:duration] of [stun].").format(**self.fmt_dict())

class MagicMissile(Spell):

	def on_init(self):
		self.name = "Magic Missile"
		self.range = 12
		self.tags = [Tags.Arcane, Tags.Sorcery]
		self.level = 1

		self.damage = 11
		self.damage_type = Tags.Arcane

		self.max_charges = 25
		self.shield_burn = 0

		self.upgrades['shield_burn'] = (3, 2, "Shield Burn", "Magic Missile removes up to 3 SH from the target before dealing damage.")
		self.upgrades['disruption'] = (1, 3, "Disruption Bolt", "If Magic Missile targets an [arcane] unit, it deals [dark] and [holy] damage instead of [arcane].", 'bolt')
		self.upgrades['barrage'] = (1, 3, "Arcane Crossfire", "When you cast Magic Missile, up to [4:num_targets] additional missiles are fired from [arcane] allies in line of sight of the target.")
		self.upgrades['ricochet'] = (1, 5, "Ricochet", "Magic Missile bounces up to [2:num_targets] times to targets in range and line of sight of the target.")

	def cast(self, x, y):
		dtypes = [Tags.Arcane]

		bolts = [(self.caster, Point(x, y))]

		if self.get_stat('barrage'):
			candidates = [u for u in self.owner.level.get_units_in_los(Point(x, y))]
			candidates = [c for c in candidates if Tags.Arcane in c.tags and not are_hostile(self.caster, c)]
			random.shuffle(candidates)

			for c in candidates[:self.get_stat('num_targets', base=4)]:
				bolts.append((c, Point(x, y)))

		if self.get_stat('ricochet'):
			prev_target = Point(x, y)
			for _ in range(self.get_stat('num_targets', base=2)):
				candidates = [u for u in self.owner.level.get_units_in_los(Point(x, y))]
				candidates = [u for u in candidates if Point(u.x, u.y) != prev_target]
				candidates = [c for c in candidates if are_hostile(self.caster, c) and distance(c, prev_target) < self.get_stat('range')]
				if not candidates:
					break

				next_target = random.choice(candidates)
				bolts.append((prev_target, next_target))
				prev_target = next_target

		for origin, target in bolts:
			self.caster.level.show_beam(origin, target, Tags.Arcane)

			unit = self.caster.level.get_unit_at(target.x, target.y)
		
			if unit:
				if self.get_stat('shield_burn'):
					unit.shields -= self.get_stat('shield_burn')
					unit.shields = max(unit.shields, 0)
				if self.get_stat('disruption') and Tags.Arcane in unit.tags:
					dtypes = [Tags.Holy, Tags.Dark]

			for dtype in dtypes:
				self.caster.level.deal_damage(target.x, target.y, self.get_stat('damage'), dtype, self)
				if len(dtypes)> 1:
					for i in range(4):
						yield

			yield

	def get_description(self):
		return "Deal [{damage}_arcane:arcane] damage to the target.".format(**self.fmt_dict())

class MindDevour(Spell):

	def on_init(self):
		self.name = "Devour Mind"
		self.range = 5
		self.tags = [Tags.Arcane, Tags.Dark, Tags.Sorcery]
		self.max_charges = 11
		self.level = 2

		self.damage = 24
		self.threshold = .5

		self.requires_los = False

		self.upgrades['huskify'] = (1, 2, "Huskification", "Killed targets are raised as zombies")
		self.upgrades['spiriteater'] = (1, 1, "Spirit Eater", "Can target [demon] and [arcane] units")
		self.upgrades['gluttony'] = (1, 2, "Gluttony", "If Devour Mind kills the target, the charge cost is refunded")

		self.charges_gained = 1


	def get_description(self):
		return ("Deal [{damage}_arcane:arcane] to an enemy unit.\n"
				"Then, if the target is under 50% HP, deal it an additional [{damage}_dark:dark] damage.\n"
				"Can only target [living] units.").format(**self.fmt_dict())

	def can_cast(self, x, y):
		unit = self.caster.level.get_unit_at(x, y)
		if not unit:
			return False

		if not are_hostile(self.caster, unit):
			return False

		if Tags.Living in unit.tags:
			return Spell.can_cast(self, x, y)

		if self.get_stat('spiriteater') and (Tags.Demon in unit.tags or Tags.Arcane in unit.tags):
			return Spell.can_cast(self, x, y)
	
		return False

	def cast(self, x, y):
		unit = self.caster.level.get_unit_at(x, y)
		
		if not unit:
			return

		self.caster.level.deal_damage(x, y, self.get_stat('damage'), Tags.Arcane, self)
		
		if unit.cur_hp / unit.max_hp < .5:
			for i in range(3):
				yield

			self.caster.level.deal_damage(x, y, self.get_stat('damage'), Tags.Dark, self)

		if self.get_stat('gluttony') and not unit.is_alive():
			self.cur_charges += 1
			self.cur_charges = min(self.cur_charges, self.get_stat('max_charges'))
		if self.get_stat('huskify') and not unit.is_alive():
			zombie = Zombie()
			apply_minion_bonuses(self, zombie)
			zombie.max_hp = unit.max_hp
			self.summon(zombie, target=unit)



class DeathShock(Spell):

	def on_init(self):
		self.name = "Death Shock"
		self.range = 9
		self.tags = [Tags.Sorcery, Tags.Dark, Tags.Lightning]
		self.max_charges = 6
		self.level = 5
		self.damage = 17
		self.cascade_range = 5

		self.can_target_empty = False

		self.upgrades['fire'] = (1, 5, 'Fire Shock', "After dealing [dark] and [lightning] damage, deals [fire] damage as well")
		self.upgrades['shield_burn'] = (3, 4, 'Shield Burn', "Before dealing damage, removes 3 SH")
		self.upgrades['corpse'] = (1, 4, 'Corpse Construct', "If Death Shock kills one or more enemies, summon an electric zombie with hp equal to half the total hp of all slain enemies.")

	def get_description(self):
		return ("Deal [{damage}_lightning:lightning] damage and [{damage}_dark:dark] damage to the target.\n"
				"If the target is slain, this effect bounces to a random enemy in line of sight up to [{cascade_range}_tiles:range] away.\n").format(**self.fmt_dict())

	def zombie(self):
		unit = BossSpawns.Stormtouched(Zombie())
		apply_minion_bonuses(self, unit)
		unit.max_hp = 0 # for tt
		return unit

	def get_extra_examine_tooltips(self):
		return self.spell_upgrades + [self.zombie()]

	def cast(self, x, y):

		unit = self.caster.level.get_unit_at(x, y)
		first_time = True
		targets_hit = 0
		delay = 5
		dtypes = [Tags.Lightning, Tags.Dark]
		if self.get_stat('fire'):
			dtypes.append(Tags.Fire)

		killed_hp = 0

		while unit or first_time:
			if self.get_stat('shield_burn'):
				unit.remove_shields(self.get_stat('shield_burn'))
			for dtype in dtypes:
				target_point = Point(x, y) if first_time else unit
				self.caster.level.deal_damage(target_point.x, target_point.y, self.get_stat('damage'), dtype, self)
				for i in range(delay):
					yield
			if unit and unit.cur_hp <= 0:
				
				killed_hp += unit.max_hp

				candidates = self.caster.level.get_units_in_los(unit)
				candidates = [c for c in candidates if are_hostile(c, self.caster)]
				candidates = [c for c in candidates if distance(c, unit) <= self.get_stat('cascade_range')]
				if candidates:
					unit = random.choice(candidates)
				else:
					unit = None
			else:
				unit = None

			# Speed up near the end to prevent waiting
			targets_hit += 1
			if targets_hit > 3:
				delay = max(2, delay - targets_hit // 4)
			if targets_hit > 100:
				delay = 1
			first_time = False

		if self.get_stat('corpse') and killed_hp:
			unit = self.zombie()
			unit.max_hp = killed_hp // 2
			self.summon(unit)

class MeltBuff(Buff):

	def __init__(self, spell):
		self.spell = spell
		Buff.__init__(self)

	def on_init(self):
		self.resists[Tags.Physical] = -100
		if self.spell.get_stat('ice_resist'):
			self.resists[Tags.Ice] = -100
		self.stack_type = STACK_DURATION
		self.color = Color(255, 100, 100)
		self.name = "Armor Melted"
		self.buff_type = BUFF_TYPE_CURSE

class MeltFlame(Upgrade):

	def on_init(self):
		self.level = 4
		self.name = "White Flame"
		self.description = "Whenever you cast a [fire] or [chaos] spell other than Melt targeting an enemy unit, melt is also cast at that target."
		self.owner_triggers[EventOnSpellCast] = self.on_cast

	def on_cast(self, evt):
		if Tags.Fire not in evt.spell.tags and Tags.Chaos not in evt.spell.tags:
			return

		if isinstance(evt.spell, MeltSpell):
			return 
		
		unit = self.owner.level.get_unit_at(evt.x, evt.y)
		if not unit:
			return

		if not are_hostile(self.owner, unit):
			return

		spell = self.owner.get_spell(MeltSpell)
		if not spell:
			return # Impossible?

		self.owner.level.act_cast(self.owner, spell, evt.x, evt.y, pay_costs=False)

class MeltSpell(Spell):

	def on_init(self):
		self.tags = [Tags.Fire, Tags.Sorcery]
		self.level = 2
		self.max_charges = 15
		self.name = "Melt"
		self.damage = 22
		self.element = Tags.Fire
		self.range = 6
		self.duration = 3

		self.can_target_empty = False

		self.upgrades['num_targets'] = (2, 3, "Mass Melt", "Chains to up to [2:num_targets] adjacent enemies.")
		self.upgrades['ice_resist'] = (1, 3, "Ice Penetration", "Melt also reduces [ice] resist by 100")
		self.add_upgrade(MeltFlame())

	def get_impacted_tiles(self, x, y):
		targets = []

		if self.get_stat('num_targets'):
			connected_group = self.caster.level.get_connected_group_from_point(x, y, check_hostile=True, num_targets=self.get_stat('num_targets') + 1)
			i = 0
			for target in connected_group:
				targets.append(target)
		else:
			unit = self.caster.level.get_unit_at(x, y)
			if unit:
				targets.append(unit)

		return targets

	def cast_instant(self, x, y):

		targets = self.get_impacted_tiles(x, y)

		for target in targets:
			self.caster.level.deal_damage(target.x, target.y, self.get_stat('damage'), self.element, self)
			if target.is_alive():
					target.apply_buff(MeltBuff(self), self.get_stat('duration'))

	def get_description(self):
		return "Target unit takes [{damage}_fire:fire] damage and loses [100_physical:physical] resist.".format(**self.fmt_dict())

class DragonRoarBuff(Buff):

	def __init__(self, spell):
		self.spell = spell
		self.vigor = spell.get_stat('vigor')
		Buff.__init__(self)

	def on_init(self):
		self.name = "Dragon Roar"
		self.color = Tags.Dragon.color
		self.stack_type = STACK_INTENSITY
		self.buff_type = BUFF_TYPE_BLESS

	def on_advance(self):
		if self.spell.get_stat('vitality'):
			self.owner.cur_hp = min(self.owner.cur_hp + 6, self.owner.max_hp)

	def on_applied(self, owner):

		owner.cur_hp += self.spell.get_stat('hp_bonus')
		owner.max_hp += self.spell.get_stat('hp_bonus')

		for spell in owner.spells:
			
			if hasattr(spell, 'damage'):
				spell.damage += self.spell.get_stat('damage')

			if isinstance(spell, BreathWeapon):
				spell.cool_down -= 1
				spell.cool_down = max(0, spell.cool_down)
				if self.vigor:
					spell.range += 2

	def on_unapplied(self):

		self.owner.max_hp -= self.spell.get_stat('hp_bonus')
		self.owner.cur_hp = min(self.owner.max_hp, self.owner.cur_hp)

		for spell in self.owner.spells:
			
			if hasattr(spell, 'damage'):
				spell.damage -= self.spell.get_stat('damage')

			if isinstance(spell, BreathWeapon):
				spell.cool_down += 1
				spell.cool_down = max(0, spell.cool_down)
				if self.vigor:
					spell.range -= 2

class DragonRoarSpell(Spell):

	def on_init(self):
		self.name = "Dragon Roar"
		self.tags = [Tags.Dragon, Tags.Nature, Tags.Enchantment]
		self.max_charges = 2
		self.level = 6
		self.range = 0

		self.hp_bonus = 25
		self.stats.append('hp_bonus')
		self.damage = 12

		self.duration = 25

		self.upgrades['vitality'] = (1, 2, "Draconic Vitality", "You gain 6 HP regen for the duration.")
		self.upgrades['vigor'] = (1, 2, "Draconic Vigor", "Dragons gain +2 range to their breath attack")
		self.upgrades['majesty'] = (1, 3, "Draconic Majesty", "On cast, all enemy units adjacent to your dragon minions are stunned for [5_turns:duration].")

		self.cooldown_reduction = 1
		self.stats.append('cooldown_reduction')

	def cast_instant(self, x, y):
		for unit in self.caster.level.units:
			if Tags.Dragon not in unit.tags:
				continue

			if are_hostile(unit, self.caster):
				continue

			unit.apply_buff(DragonRoarBuff(self), self.get_stat('duration'))
			
			if self.get_stat('majesty'):
				for i in range(-1, 2): #-1 thru 1 inclusive
					for j in range(-1, 2):
						u = self.caster.level.get_unit_at(unit.x + i, unit.y + j)
						if u and are_hostile(u, self.caster):
							u.apply_buff(Stun(), self.get_stat('duration', base=5))


	def get_description(self):
		return "All allied dragons gain [{hp_bonus}_max_HP:minion_health], [{damage}:damage] attack damage, and [{cooldown_reduction}_turn:duration] cooldown reduction.\nLasts [{duration}_turns:duration].".format(**self.fmt_dict())

class IronSkinBuff(Buff):

	def __init__(self, spell):
		self.spell = spell
		Buff.__init__(self)
		self.name = "Ironized"
		self.buff_type = BUFF_TYPE_BLESS
		self.asset = ['status', 'protection']

	def on_init(self):
		for tag in [Tags.Physical, Tags.Fire, Tags.Lightning]:
			self.resists[tag] = self.spell.get_stat('resist')
		if self.spell.get_stat('resist_arcane'):
			self.resists[Tags.Arcane] = self.spell.get_stat('resist')

	def on_applied(self, owner):
		if Tags.Metallic not in self.owner.tags:
			self.nonmetal = True
			self.owner.tags.append(Tags.Metallic)
		else:
			self.nonmetal = False

	def on_unapplied(self):
		if self.nonmetal:
			self.owner.tags.remove(Tags.Metallic)

class ProtectMinions(Spell):

	def on_init(self):
		self.name = "Ironize"
		self.resist = 50
		self.stats.append('resist')
		self.duration = 10
		self.max_charges = 5
		self.level = 3
		
		self.tags = [Tags.Enchantment, Tags.Conjuration, Tags.Metallic]
		self.range = 0

		self.resist_arcane = 0
		self.upgrades['armor_plating'] = (1, 1, "Armor Plating", "Grants 1 SH to all minions.")
		self.upgrades['permanence'] = (1, 2, "Permanent Transmutation", "Permanent duration.")
		self.upgrades['resist_arcane'] = (1, 2, "Arcane Insulation")

	def cast_instant(self, x, y):
		for unit in self.caster.level.units:
			if unit == self.caster:
				continue
			if self.caster.level.are_hostile(unit, self.caster):
				continue
			if not self.get_stat('permanence'):
				unit.apply_buff(IronSkinBuff(self), self.get_stat('duration'))
			else:
				unit.apply_buff(IronSkinBuff(self))
			if self.get_stat('armor_plating'):
				unit.add_shields(1)
			unit.deal_damage(0, Tags.Physical, self)

	def get_description(self):
		return ("All allied units gain [{resist}_physical:physical] resist, [{resist}_fire:fire] resist, and [{resist}_lightning:lightning] resist and become metallic.\n"
				"Lasts [{duration}_turns:duration].").format(**self.fmt_dict())

class EchoCast(Buff):

	def __init__(self, spell):
		Buff.__init__(self)
		self.spell = spell
		self.name = "Echo Cast " + spell.name
		self.description = "Recast " + spell.name + (" in %d turns." % self.turns_left)
		self.color = spell.tags[0].color

	def on_advance(self):
		self.description = "Recast " + self.spell.name + (" in %d turns." % self.turns_left)

	def on_unapplied(self):
		self.owner.level.queue_spell(self.spell.cast(self.owner.x, self.owner.y, is_echo=True))

class WordOfUndeath(Spell):

	def on_init(self):
		self.name = "Word of Undeath"

		self.tags = [Tags.Dark, Tags.Word]
		self.element = Tags.Dark
		self.level = 7
		self.max_charges = 1
		self.range = 0

		self.upgrades['hatred_of_life'] = (1, 3, "Hatred of Life", "All [living:living] units take [36:poison] poison damage.")
		self.upgrades['spirit_gift'] = (1, 4, "Spirit Gift", "Up to [3:num_targets] non-[undead:undead] allies get the ghostly modifier.")
		self.upgrades['spirit_lich'] = (1, 5, "Spirit of Lichdom", "Up to [3:num_targets] random [living:living] allies get the lich modifier.")

	def get_impacted_tiles(self, x, y):
		return [u for u in self.caster.level.units if u != self.caster]

	def get_description(self):
		return ("All undead units have their current and maximum HP doubled.\n"
				"All other units except the caster lose half their current and maximum HP.").format(**self.fmt_dict())

	def cast(self, x, y):
		if self.get_stat('spirit_gift'):
			eligible_units = [u for u in self.caster.level.units if not are_hostile(self.caster, u) and not Tags.Undead in u.tags and not u.is_player_controlled]
			for i in range(min(self.get_stat('num_targets', base=3), len(eligible_units))):
				eligible_units[i].Anim = None
				BossSpawns.apply_modifier(BossSpawns.Ghostly, eligible_units[i])
		
		if self.get_stat('spirit_lich'):
			eligible_units = [u for u in self.caster.level.units if not are_hostile(self.caster, u) and Tags.Living in u.tags and not Tags.Undead in u.tags and not u.is_player_controlled]
			for i in range(min(self.get_stat('num_targets', base=3), len(eligible_units))):
				eligible_units[i].Anim = None
				BossSpawns.apply_modifier(BossSpawns.Lich, eligible_units[i])
		
		units = list(self.caster.level.units)
		random.shuffle(units)
		for unit in units:
			if unit.is_player_controlled:
				continue
			if Tags.Undead in unit.tags:
				unit.max_hp *= 2
				unit.deal_damage(-unit.cur_hp, Tags.Heal, self)
			else:
				unit.cur_hp //= 2
				unit.cur_hp = max(1, unit.cur_hp)
				unit.max_hp //= 2
				unit.max_hp = max(1, unit.max_hp)
				self.owner.level.show_effect(unit.x, unit.y, Tags.Dark, minor=False)
				if self.get_stat('hatred_of_life') and Tags.Living in unit.tags:
					unit.deal_damage(36, Tags.Poison, self)
				yield

class WordOfChaos(Spell):

	def on_init(self):
		self.name = "Word of Chaos"
		self.damage = 45
		self.duration = 6
		self.range = 0

		self.tags = [Tags.Chaos, Tags.Word]
		self.level = 7
		self.max_charges = 1

		self.upgrades['reanimation'] = (1, 4, "Animated Chaos", "Slain units are reanimated as Chaos Spirits.")
		self.upgrades['chaos_gifts'] = (1, 4, "Chaos Gifts", "Up to [3:num_targets] random non-chaos allies get the chaos boss modifier.")
		self.upgrades['echo'] = (1, 5, "Echoing Chaos", "Auto recasts in 10 turns.")

	def get_description(self):
		return ("[Stun] each enemy for [{duration}_turns:duration] and teleport them to random tiles."
				"\nDeal [{damage}_lightning:lightning] damage to all [fire] enemies."
				"\nDeal [{damage}_fire:fire] damage to all [lightning] enemies."
				"\nEach enemy construct loses all [physical] resist and takes [{damage}_physical:physical] damage.").format(**self.fmt_dict())

	def get_impacted_tiles(self, x, y):
		return [u for u in self.owner.level.units if u != self.caster]

	def cast(self, x, y, is_echo=False):
		if self.get_stat('echo') and not is_echo:
			self.caster.apply_buff(EchoCast(self), 10)
		
		if self.get_stat('chaos_gifts'):
			#had to have it apply to only non-chaos units, and make Chaostouched apply the chaos tag so that it doesn't repeat units
			eligible_units = [u for u in self.caster.level.units if not are_hostile(u, self.caster) and not Tags.Chaos in u.tags and not u.is_player_controlled]
			if eligible_units:
				random.shuffle(eligible_units)
				for i in range(min(self.get_stat('num_targets', base=3), len(eligible_units))):
					eligible_units[i].Anim = None
					BossSpawns.apply_modifier(BossSpawns.Chaostouched, eligible_units[i])
		
		units = list(self.caster.level.units)
		random.shuffle(units)
		for unit in units:
			if not self.caster.level.are_hostile(self.caster, unit):
				continue

			teleport_targets = [t for t in self.caster.level.iter_tiles() if self.caster.level.can_stand(t.x, t.y, unit)]
			if not teleport_targets:
				continue

			teleport_target = random.choice(teleport_targets)
			
			self.caster.level.show_path_effect(unit, teleport_target, Tags.Chaos)

			self.caster.level.act_move(unit, teleport_target.x, teleport_target.y, teleport=True)
			unit.apply_buff(Stun(), self.get_stat('duration'))

			if Tags.Construct in unit.tags:
				unit.resists[Tags.Physical] = 0
				unit.deal_damage(self.get_stat('damage'), Tags.Physical, self)
			if Tags.Lightning in unit.tags:
				unit.deal_damage(self.get_stat('damage'), Tags.Fire, self)
			if Tags.Fire in unit.tags:
				unit.deal_damage(self.get_stat('damage'), Tags.Lightning, self)
			
			if self.get_stat('reanimation') and not unit.is_alive():
				self.summon(ChaosSpirit(), target=unit)
			yield

class WordOfBeauty(Spell):

	def on_init(self):
		self.name = "Word of Beauty"
		self.damage = 25
		self.duration = 7
		self.range = 0
		self.tags = [Tags.Holy, Tags.Lightning, Tags.Word]
		self.level = 7
		self.max_charges = 1

		self.upgrades['beauty_steel'] = (1, 2, "Beauty of Steel", "Also heals allied [metallic:metallic] units.")
		self.upgrades['shield_strip'] = (1, 2, "Shield Strip", "Damaged units lose 1 SH before being damaged.") #assuming this is what you meant?
		self.upgrades['echo'] = (1, 4, "Echoing Beauty", "Auto recast in 10 turns.")

	def get_impacted_tiles(self, x, y):
		return [u for u in self.caster.level.units if u != self.caster]		

	def get_description(self):
		return ("Heal yourself and all living units fully."
				"\nDeal [{damage}_lightning:lightning] damage to [demon] and [undead] units."
				"\n[Stun] all [arcane] units for [{duration}_turns:duration].").format(**self.fmt_dict())

	def cast(self, x, y, is_echo=False):
		if self.get_stat('echo') and not is_echo:
			self.caster.apply_buff(EchoCast(self), 10)
		units = list(self.caster.level.units)
		random.shuffle(units)
		for unit in units:
			if unit.is_player_controlled or Tags.Living in unit.tags or (self.get_stat('beauty_steel') and Tags.Metallic in unit.tags):
				unit.deal_damage(-unit.max_hp, Tags.Heal, self)
			if Tags.Demon in unit.tags or Tags.Undead in unit.tags:
				if self.get_stat('shield_strip'):
					unit.remove_shields(1)
				unit.deal_damage(self.get_stat('damage'), Tags.Lightning, self)
			if Tags.Arcane in unit.tags:
				unit.deal_damage(0, Tags.Physical, self)
				unit.apply_buff(Stun(), self.get_stat('duration'))
			yield

class WordOfMadness(Spell):

	def on_init(self):
		self.name = "Word of Madness"
		self.duration = 5
		self.tags = [Tags.Word, Tags.Dark, Tags.Arcane]
		self.level = 7
		self.max_charges = 1

		self.duration = 5
		self.range = 0

		self.upgrades['selective_madness'] = (1, 1, "Selective Madness", "Only heals allies.")
		self.upgrades['echo'] = (1, 5, "Echoing Madness", "Auto recast in 10 turns.")
		self.upgrades['guardians'] = (1, 6, "Guardians of Madness", "Summon [3:num_summons] mind devourers, [5:num_summons] floating eyeballs, and [6:num_summons] troublers for 10 turns at random locations.")

	def get_description(self):
		return ("[Berserk] all units except the caster for [{duration}_turns:duration].\n"
				"Deal [dark] damage to all [construct] units equal to half their current HP.\n"
				"Fully heal all [demon] and [arcane] units.").format(**self.fmt_dict())

	def get_impacted_tiles(self, x, y):
		return [u for u in self.caster.level.units if u != self.caster]

	def cast(self, x, y, is_echo=False):
		if self.get_stat('echo') and not is_echo:
			self.caster.apply_buff(EchoCast(self), 10)
		
		if self.get_stat('guardians'):
			eligible_tiles = []
			for i in range(len(self.caster.level.tiles)):
				for j in range(len(self.caster.level.tiles[0])):
					if self.caster.level.tiles[i][j].can_walk:
						eligible_tiles.append(Point(i, j))
			amt_summons = [3, 5, 6]
			summons = [MindDevourer, FloatingEye, Troubler]
			for s in range(3):
				for i in range(self.get_stat('num_summons', base=amt_summons[s])):
					tile = random.choice(eligible_tiles)
					eligible_tiles.remove(tile)
					u = summons[s]()
					u.turns_to_death = 10
					self.summon(u, tile)
		
		units = list(self.caster.level.units)
		random.shuffle(units)
		for unit in units:
			if unit == self.caster:
				continue
			unit.apply_buff(BerserkBuff(), self.get_stat('duration'))
			if Tags.Construct in unit.tags:
				unit.deal_damage(unit.cur_hp // 2, Tags.Dark, self)
			if Tags.Demon in unit.tags or Tags.Arcane in unit.tags:
				if not self.get_stat('selective_madness') or not are_hostile(self.caster, unit):
					unit.deal_damage(-unit.max_hp, Tags.Heal, self)
			yield

class RegenShieldsBuff(Buff):

	def on_init(self):
		self.name = "Regenerating Shields"
		self.description = "Regenerate 2 SH per turn up to 4 SH."
		self.color = Tags.Arcane.color

	def on_advance(self):
		if self.owner.shields < 2:
			self.owner.add_shields(2 - self.owner.shields)

class SummonFloatingEye(Spell):

	def on_init(self):
		self.name = "Floating Eye"
		self.minion_duration = 4
		self.tags = [Tags.Eye, Tags.Arcane, Tags.Conjuration]
		self.level = 4
		self.max_charges = 6

		ex = FloatingEye()

		self.minion_health = ex.max_hp
		self.shields = ex.shields

		self.minion_duration = 16

		self.upgrades['stone_gaze'] = (1, 3, "Stone Gaze", "Floating Eye can cast your Petrify on a 3 turn cooldown.")
		self.upgrades['eyemage'] = (1, 4, "Eyemage", "Floating Eye can cast your [eye:eye] spells on 15 turn cooldowns.")
		self.upgrades['regen_shields'] = (1, 4, "Regenerating Shields", "Floating Eye gains 2 SH per turn up to 4 SH.")

		self.must_target_empty = True

	def cast_instant(self, x, y):
		eye = FloatingEye()
		eye.team = TEAM_PLAYER
		eye.max_hp += self.get_stat('minion_health')
		eye.turns_to_death = self.get_stat('minion_duration')

		p = self.caster.level.get_summon_point(x, y, flying=True)
		if p:
			if self.get_stat('eyemage'):
				for spell in self.caster.spells:
					if Tags.Eye in spell.tags and spell != self:
						grant_minion_spell(type(spell), eye, self.caster, cool_down=15)

			if self.get_stat('regen_shields'):
				eye.apply_buff(RegenShieldsBuff())

			if self.get_stat('stone_gaze'):
				grant_minion_spell(PetrifySpell, eye, self.caster, cool_down=3)

			self.summon(eye, p)

	def get_description(self):
		return ("Summon a floating eye.\n"
				"Floating eyes have [{minion_health}_HP:minion_health], [{shields}_SH:shields], fly, and passively blink.\n"
				#"Floating eyes have no attacks of their own, but will cast any other [eye] spells you know upon being summoned.\n"
				"Floating eyes vanish after [{minion_duration}_turns:minion_duration].").format(**self.fmt_dict())

class FarmiliarBuff(Buff):

	def __init__(self, summoner, tags):
		Buff.__init__(self)
		self.summoner = summoner
		self.tags = tags
		self.global_triggers[EventOnSpellCast] = self.on_spell_cast

	def on_spell_cast(self, evt):

		if evt.caster != self.summoner:
			return

		if Tags.Sorcery not in evt.spell.tags:
			return

		has_tag = False
		for tag in self.tags:
			if tag in evt.spell.tags:
				has_tag = True
		
		if not has_tag:
			return

		spell = type(evt.spell)()
		spell.cur_charges = 1
		spell.caster = self.owner
		spell.owner = self.owner
		spell.statholder = self.summoner

		if spell.can_cast(evt.x, evt.y):
			self.owner.level.act_cast(self.owner, spell, evt.x, evt.y)


class ChimeraFarmiliar(Spell):

	def on_init(self):
		self.name = "Chimera Familiar"
		self.tags = [Tags.Chaos, Tags.Conjuration]
		self.level = 3
		self.max_charges = 3
		self.minion_health = 20
		self.minion_damage = 6
		self.minion_range = 4
		self.minion_resists = 0
		self.dark_casting = 0
		self.arcane_casting = 0
		self.nature_casting = 0
		self.minion_resists = 50
		self.upgrades['minion_resists'] = (50, 2)
		self.upgrades['max_charges'] = (2, 3)
		self.upgrades['nature_casting'] = (1, 1, "Nature Mimicry", "The Chimera will mimic nature sorcery spells as well")
		self.upgrades['dark_casting'] = (1, 1, "Dark Mimicry", "The Chimera will mimic dark sorcery spells as well")
		self.upgrades['arcane_casting'] = (1, 1, "Arcane Mimicry", "The Chimera will mimic arcane sorcery spells as well")

		self.must_target_walkable = True
		self.must_target_empty = True

	def get_tags(self):
		tags = [Tags.Fire, Tags.Lightning, Tags.Chaos]
		if self.get_stat('dark_casting'):
			tags.append(Tags.Dark)
		if self.get_stat('nature_casting'):
			tags.append(Tags.Nature)
		if self.get_stat('arcane_casting'):
			tags.append(Tags.Arcane)
		return tags

	def get_description(self):
		tagstr = ' or '.join(t.name for t in self.get_tags())
		return ("Summon a Chimera Familiar.\n"
				"The chimera has [{minion_damage}_fire:fire] damage and [{minion_damage}_lightning:lightning] damage attacks with a range of [{minion_range}_tiles:minion_range].\n"
			    "The chimera mimics your casts of %s [sorcery] spells if the target is in range and line of sight."
			    % ' or '.join('[' + t.name.lower() + ']' for t in self.get_tags())).format(**self.fmt_dict())

	def cast_instant(self, x, y):
		chimera = Unit()
		chimera.name = "Chimera"
		chimera.sprite.char = 'C'
		chimera.sprite.color = Tags.Sorcery.color
		chimera.max_hp = self.get_stat('minion_health')
		b1 = SimpleRangedAttack(damage=self.get_stat('minion_damage'), range=self.get_stat('minion_range'), damage_type=Tags.Lightning)
		b1.cool_down = 2
		b2 = SimpleRangedAttack(damage=self.get_stat('minion_damage'), range=self.get_stat('minion_range'), damage_type=Tags.Fire)
		b2.cool_down = 2
		chimera.spells.append(b1)
		chimera.spells.append(b2)
		chimera.spells.append(SimpleMeleeAttack(self.get_stat('minion_damage')))
		chimera.resists[Tags.Fire] = self.get_stat('minion_resists')
		chimera.resists[Tags.Lightning] = self.get_stat('minion_resists')
		chimera.buffs.append(FarmiliarBuff(self.caster, self.get_tags()))
		chimera.team = TEAM_PLAYER
		chimera.tags = [Tags.Living, Tags.Arcane]

		self.summon(chimera, Point(x, y))


class ArcLightning(Spell):

	def on_init(self):
		self.name = "Arc Lightning"
		self.tags = [Tags.Lightning, Tags.Sorcery]
		self.max_charges = 1
		self.level = 6
		self.num_targets = 4
		self.friendly_fire = 1

		self.damage = 32
		self.element = Tags.Lightning
		self.range = 18

		self.upgrades['arcane_arcs'] = (1, 5, "Proton Storm", "Arc Lightning deals [4_arcane:arcane] damage to all units in line of sight of each arc target")
		self.upgrades['enervation'] = (1, 4, "Enervation", "Arc Lightning heals allies instead of damaging them")
		self.upgrades['num_targets'] = (4, 5, "Multi Flash")

	def get_description(self):
		return ("Lightning arcs to [{num_targets}_enemies:num_targets] visible from the target tile.\n"
				"Each arc deals [{damage}_lightning:lightning] damage to units in a beam.").format(**self.fmt_dict())

	def cast(self, x, y, is_echo=False):
		center_unit = self.caster.level.get_unit_at(x, y)

		if not center_unit or self.friendly_fire or self.caster.level.are_hostile(center_unit, self.caster):
			self.caster.level.deal_damage(x, y, self.get_stat('damage'), self.element, self)
			yield 1

		targets = set(t for t in self.caster.level.get_units_in_los(Point(x, y)) if self.caster.level.are_hostile(t, self.caster))
		chosen_targets = []
		for i in range(self.get_stat('num_targets')):
			if not targets:
				break

			target = targets.pop()
			chosen_targets.append(target)

			if self.get_stat('arcane_arcs'):
				for u in self.owner.level.get_units_in_los(target):
					u.deal_damage(self.get_stat('damage', base=4), Tags.Arcane, self)
				yield 1

			for p in self.caster.level.get_points_in_line(Point(x, y), target, find_clear=True)[1:]:

				damage = self.get_stat('damage')
				if is_echo:
					damage //= 2

				unit = self.caster.level.get_unit_at(p.x, p.y)

				if self.get_stat('enervation') and unit and not self.caster.level.are_hostile(unit, self.caster):
					unit.heal(damage, self)
				else:
					self.caster.level.deal_damage(p.x, p.y, damage, self.element, self)
			
			yield 1

		if not is_echo:
			recursions = [self.cast(t.x, t.y, is_echo=True) for t in chosen_targets]
			while recursions:
				recursions = [r for r in recursions if next(r)]
				yield 1

		yield 0

class PoisonSting(Spell):

	def on_init(self):
		self.name = "Poison Sting"
		self.tags = [Tags.Sorcery, Tags.Nature]
		self.max_charges = 20
		self.duration = 30
		self.damage = 9
		self.range = 12
		self.level = 1

		self.upgrades['antigen'] = (1, 2, "Acidity", "Damaged targets lose all poison resist")
		self.upgrades['webs'] = (1, 2, "Silk Shot", "Stuns target and spawns webs along a line to the target.  Webs stun enemy units that enter them for 2 turns.")
		self.upgrades['radius'] = (1, 4, "Stinger Barrage", "Hits every poisoned enemy in a radius of 3 of the main target.")

	def get_impacted_tiles(self, x, y):
		if self.get_stat('webs'):
			for p in self.caster.level.get_points_in_line(self.caster, Point(x, y), find_clear=True)[1:-1]:
				yield p
		yield Point(x, y)

	def cast_instant(self, x, y):
		unit = self.caster.level.get_unit_at(x, y)
		damage = self.caster.level.deal_damage(x, y, self.get_stat('damage'), Tags.Physical, self)

		for p in self.caster.level.get_points_in_line(self.caster, Point(x, y), find_clear=True)[1:-1]:
			self.caster.level.show_effect(p.x, p.y, Tags.Poison, minor=True)
			if self.get_stat('webs'):
				unit = self.caster.level.get_unit_at(p.x, p.y)
				if unit:
					unit.apply_buff(Stun(), 2)
				else:
					web = SpiderWeb()
					web.owner = self.caster
					self.owner.level.add_obj(web, p.x, p.y)

		unit = self.caster.level.get_unit_at(x, y)
		if unit and damage and self.get_stat('antigen'):
			unit.apply_buff(Acidified())
		if unit and unit.resists[Tags.Poison] < 100:
			unit.apply_buff(Poison(), self.get_stat('duration'))
		if unit and self.get_stat('webs'):
			unit.apply_buff(Stun(), self.get_stat('duration', base=2))

		if self.get_stat('radius'):
			elligible_units = [u for u in self.caster.level.get_units_in_ball(Point(x, y), self.get_stat('radius', base=3)) if u.has_buff(Poison)]
			for u in elligible_units:
				for point in self.caster.level.get_points_in_line(self.caster, u):
					self.caster.level.show_effect(point.x, point.y, Tags.Poison, minor=True)
				self.caster.level.deal_damage(x, y, self.get_stat('damage'), Tags.Physical, self)
				if u.is_alive() and u.resists[Tags.Poison] < 100:
					u.apply_buff(Poison(), self.get_stat('duration'))

	def get_description(self):
		return ("Deal [{damage}_physical:physical] damage to target unit.\n"
				"That unit is [poisoned] for [{duration}_turns:duration].\n"
				+ text.poison_desc).format(**self.fmt_dict())

class WildfireCharge(Buff):

	def on_init(self):
		self.name = "Wildfire"
		self.buff_type = BUFF_TYPE_BLESS
		self.color = Tags.Fire.color
		self.spell_bonuses[Flameblast]['range'] = 1
		self.stack_type = STACK_INTENSITY

class Flameblast(Spell):

	def on_init(self):
		self.name = "Fan of Flames"
		self.tags = [Tags.Sorcery, Tags.Fire]
		self.max_charges = 18
		self.damage = 9
		self.element = Tags.Fire
		self.range = 5
		self.angle = math.pi / 6.0
		self.level = 2
		self.can_target_self = False
		self.requires_los = False
		self.melt_walls = 0
		self.max_channel = 10

		self.upgrades['heal'] = (1, 3, "Healing Hearthfire", "Fan of Flames heals allies instead of damaging them.")
		self.upgrades['frostfire'] = (1, 4, "Fan of Frostfire", "Fan of flames also deals Ice damage.")
		self.upgrades['wildfire'] = (1, 5, "Wildfire", "Fan of Flames gains 1 range for the next turn for each enemy unit killed.")
		#self.upgrades['channel'] = (1, 2, "Channeling", "Fan of Flames can be channeled for up to 10 turns")
		self.channel = 1

	def get_description(self):
		return ("Deal [{damage}_fire:fire] damage to all units in a cone.\n"
				"This spell can be channeled for up to [{max_channel}_turns:duration].  The effect is repeated each turn the spell is channeled.").format(**self.fmt_dict())
 
	def aoe(self, x, y):
		origin = get_cast_point(self.caster.x, self.caster.y, x, y)
		target = Point(x, y)
		return Burst(self.caster.level, 
				     Point(self.caster.x, self.caster.y), 
				     self.get_stat('range'), 
				     burst_cone_params=BurstConeParams(target, self.angle), 
				     ignore_walls=self.get_stat('melt_walls'))
		
	def cast(self, x, y, channel_cast=False):

		if self.get_stat('channel') and not channel_cast:
			self.caster.apply_buff(ChannelBuff(self.cast, Point(x, y)), self.get_stat('max_channel'))
			return

		for stage in self.aoe(x, y):
			for point in stage:
				if self.get_stat('melt_walls') and self.caster.level.tiles[point.x][point.y].is_wall():
					self.caster.level.make_floor(point.x, point.y)
				if point.x == self.caster.x and point.y == self.caster.y:
					continue
				unit = self.caster.level.get_unit_at(point.x, point.y)
				if unit:
					if are_hostile(unit, self.caster) or not self.get_stat('heal'): #Always deal damage if FoF does not heal. If FoF heals, only deal damage to hostile enemies.
						self.caster.level.deal_damage(point.x, point.y, self.get_stat('damage'), self.element, self)
						if self.get_stat('frostfire'):
							self.caster.level.deal_damage(point.x, point.y, self.get_stat('damage'), Tags.Ice, self)
					else:
						self.caster.level.deal_damage(point.x, point.y, -self.get_stat('damage'), Tags.Heal, self)
					
					if not unit.is_alive() and self.get_stat('wildfire'):
						self.caster.apply_buff(WildfireCharge(), 2)
				else:
					self.caster.level.deal_damage(point.x, point.y, self.get_stat('damage'), self.element, self)
					if self.get_stat('frostfire'):
						self.caster.level.deal_damage(point.x, point.y, self.get_stat('damage'), Tags.Ice, self)
			yield

	def get_impacted_tiles(self, x, y):
		return [p for stage in self.aoe(x, y) for p in stage]

class SummonBlueLion(Spell):

	def on_init(self):
		self.name = "Blue Lion"
		self.tags = [Tags.Nature, Tags.Holy, Tags.Conjuration, Tags.Arcane]
		self.max_charges = 2
		self.level = 5
		self.minion_health = 28
		self.minion_damage = 7
		self.shield_max = 2
		self.shield_cooldown = 3
		
		self.upgrades['holy_bolt'] = (1, 3, "Holy Bolt", "The Blue Lion's melee attack is replaced by a range 6 holy bolt attack.")
		self.upgrades['healing_light_spell'] = (1, 4, "Shimmermane", "The Blue Lion gains your Healing Light spell on a 7 turn cooldown.")
		self.upgrades['burning_lion'] = (1, 5, "Burning Lion", "Summon a Burning Lion instead of a Blue Lion.")

		self.must_target_empty = True

	def cast_instant(self, x, y):
		lion = Unit()
		lion.name = "Blue Lion"
		lion.team = self.caster.team
		lion.sprite.char = 'L'
		lion.sprite.color = Color(100, 120, 255)
		lion.asset_name = "blue_lion"
		lion.max_hp = self.get_stat('minion_health')

		lion.flying = True

		sheen_spell = ShieldSightSpell(self.get_stat('shield_cooldown'), self.get_stat('shield_max'))
		sheen_spell.name = "Blue Lion Sheen"

		lion.spells.append(sheen_spell)
		
		if self.get_stat('holy_bolt'):
			bolt = SimpleRangedAttack(damage=self.get_stat('minion_damage'), damage_type=Tags.Holy, range=6 + self.get_stat('minion_range'))
			bolt.name = "Blue Lion Bolt"
			lion.spells.append(bolt)
		else:
			lion.spells.append(SimpleMeleeAttack(self.get_stat('minion_damage')))

		if self.get_stat('healing_light_spell'):
			grant_minion_spell(HealMinionsSpell, lion, self.caster, cool_down=7)
		
		if self.get_stat('burning_lion'):
			BossSpawns.apply_modifier(BossSpawns.Flametouched, lion)

		lion.tags = [Tags.Nature, Tags.Arcane, Tags.Holy]
		lion.resists[Tags.Arcane] = 50
		lion.resists[Tags.Physical] = 50
		
		self.summon(lion, Point(x, y))
		

	def get_description(self):
		return ("Summon a blue lion.\n"
				"Blue lions have [{minion_health}_HP:minion_health], fly, have [50_arcane:arcane] resist and [50_physical:physical] resist.\n"			
				"Blue lions have a spell that grants [1_SH:shield] to themselves and allies in their line of sight, up to a maximum of [2_SH:shield] with a cooldown of [3_turns:duration].\n"
				"Blue lions also have a melee attack which deals [{minion_damage}_physical:physical] damage.").format(**self.fmt_dict())


class DeathCleaveBuff(Buff):

	def __init__(self, spell):
		self.spell = spell
		Buff.__init__(self)
		self.stack_type = STACK_DURATION
		self.buff_type = BUFF_TYPE_BLESS
		self.asset = ['status', 'death_cleave']
		self.color = Tags.Dark.color

	def on_init(self):
		self.name = "Death Cleave"
		self.description = "Spells will cleave to nearby targets if they kill their main target"
		self.cur_target = None	
		self.owner_triggers[EventOnSpellCast] = self.on_spell_cast	

	def on_spell_cast(self, evt):
		self.cur_target = evt.caster.level.get_unit_at(evt.x, evt.y)
		self.owner.level.queue_spell(self.effect(evt))

	def show_fizzle(self, center):
		points = list(self.owner.level.get_adjacent_points(center, filter_walkable=False))
		random.shuffle(points)
		for p in points:
			if p == center:
				continue
			etype = random.choice([Tags.Arcane, Tags.Dark])
			self.owner.level.show_effect(p.x, p.y, etype, minor=True)
			if random.random() < .5:
				yield

	def effect(self, evt):
		if self.cur_target and not self.cur_target.is_alive():

			def can_cleave(t):
				if not evt.caster.level.are_hostile(t, evt.caster):
					return False
				if not evt.spell.can_cast(t.x, t.y):
					return False
				return True

			cleave_targets = [u for u in evt.caster.level.units if can_cleave(u)]

			if cleave_targets:
				target = random.choice(cleave_targets)
				yield

				# Draw chain
				for p in self.owner.level.get_points_in_line(self.cur_target, target)[:-1]:
					self.owner.level.show_effect(p.x, p.y, Tags.Dark, minor=True)

				evt.caster.level.act_cast(evt.caster, evt.spell, target.x, target.y, pay_costs=False)
			# If no cleavable targets exist, show a fizzling out effect on the last target
			else:
				evt.caster.level.queue_spell(self.show_fizzle(evt.caster))

		elif self.cur_target and self.cur_target.is_alive():
			evt.caster.level.queue_spell(self.show_fizzle(self.cur_target))




class DeathCleaveSpell(Spell):

	def on_init(self):
		self.name = "Death Cleave"
		self.duration = 2
		self.upgrades['duration'] = (3, 3)
		self.upgrades['max_charges'] = (4, 2)
		#self.upgrades['cascade_range'] = (3, 4)
		self.max_charges = 4
		self.cascade_range = 5
		self.range = 0
		self.level = 4
		self.tags = [Tags.Enchantment, Tags.Arcane, Tags.Dark]

	def cast_instant(self, x, y):
		self.caster.apply_buff(DeathCleaveBuff(self), self.get_stat('duration') + 1) # +1 so as to not count the current turn

	def get_description(self):
		return ("Whenever a spell you cast kills its primary target, that spell is recast on a randomly selected nearby valid enemy target.\n"
		  		"Lasts [{duration}_turns:duration].").format(**self.fmt_dict())

class CantripCascade(Spell):

	def on_init(self):
		self.name = "Cantrip Cascade"
		self.level = 5
		self.tags = [Tags.Arcane, Tags.Sorcery]
		self.max_charges = 3
		self.angle = math.pi / 6
		self.range = 7

		self.upgrades['cantrip_burst'] = (1, 3, "Cantrip Burst", "Instead of a cone, Cantrip Cascade casts in a [5_tile:radius] burst.")
		self.upgrades['orb_cantrips'] = (1, 4, "Orb Cascade", "In addition to casting in a cone, all of your orbs cast a random known cantrip on the nearest foe in line of sight.")
		self.upgrades['cast_twos'] = (1, 6, "Evocation Amalgamation", "Additionally cast one random level 2 [sorcery] spell from your spellbook on all targets.") #Do in addition? Or as a replacement?

	def get_impacted_tiles(self, x, y):
		target = Point(x, y)
		burst = None
		if self.get_stat('cantrip_burst'):
			burst = Burst(self.caster.level, Point(x, y), self.get_stat('radius', base=5))
			points = [p for stage in burst for p in stage]
		else: 
			burst = Burst(self.caster.level, self.caster, self.get_stat('range'), expand_diagonals=True, burst_cone_params=BurstConeParams(target, self.angle))
			points = [p for stage in burst for p in stage if (self.caster.level.can_see(self.caster.x, self.caster.y, p.x, p.y))]
		
		if self.get_stat('orb_cantrips'):
			points += [o for o in self.caster.level.units if (not are_hostile(o, self.caster)) and ("Orb" in o.name)] #add Orb tag to Orb summons? Or does this work fine?
		return points

	def cast_instant(self, x, y):
		spells = [s for s in self.caster.spells if s.level == 1 and Tags.Sorcery in s.tags]
		units = [self.caster.level.get_unit_at(p.x, p.y) for p in self.get_impacted_tiles(x, y)]
		enemies = set([u for u in units if u and are_hostile(u, self.caster)])

		pairs = list(itertools.product(enemies, spells))

		random.shuffle(pairs)

		for enemy, spell in pairs:
			self.caster.level.act_cast(self.caster, spell, enemy.x, enemy.y, pay_costs=False)
			
		if self.get_stat('cast_twos'):
			spells = [s for s in self.caster.spells if s.level == 2 if Tags.Sorcery in s.tags]
			for i in range(1): #if we ever want to change the amount, I'll leave the for loop in
				if spells:
					spell = random.choice(spells)
					spells.remove(spell)

					for enemy in enemies:
						if enemy.is_alive():
							self.caster.level.act_cast(self. caster, spell, enemy.x, enemy.y, pay_costs=False)

		if self.get_stat('orb_cantrips'):
			orbs = self.caster.level.units
			orbs = [o for o in orbs if (not are_hostile(o, self.caster)) and ("Orb" in o.name)] #Ditto above comment about Orb tag
			
			for orb in orbs:
				elligible_targets = self.caster.level.get_units_in_los(orb)
				elligible_targets = [u for u in elligible_targets if are_hostile(u, self.caster)]
				
				if elligible_targets:
					target = random.choice(elligible_targets)
					if spells:
						spell = random.choice(spells)
						self.caster.level.act_cast(orb, spell, target.x, target.y, pay_costs=False)

	def get_description(self):
		return ("Cast each of your level 1 sorcery spells on each enemy in a cone.")

class MulticastBuff(Buff):

	def __init__(self, spell):
		self.spell = spell
		Buff.__init__(self)
		self.stack_type = STACK_DURATION  # This may be OP but its also awesome
		self.color = Tags.Arcane.color
		self.buff_type = BUFF_TYPE_BLESS
		self.asset = ['status', 'multicast']


	def on_init(self):
		self.name = "Multicast"
		self.description = "Whenever you cast a sorcery spell, copy it."
		self.can_copy = True
		self.owner_triggers[EventOnSpellCast] = self.on_spell_cast

	def on_spell_cast(self, evt):
		if evt.spell.item:
			return
		if Tags.Sorcery not in evt.spell.tags:
			return

		if self.can_copy:
			self.can_copy = False
			for i in range(self.spell.get_stat('copies')):
				if evt.spell.can_cast(evt.x, evt.y) and evt.spell.can_pay_costs():
					evt.caster.level.act_cast(evt.caster, evt.spell, evt.x, evt.y, pay_costs=False)
			evt.caster.level.queue_spell(self.reset())

	def reset(self):
		self.can_copy = True
		yield

class MulticastSpell(Spell):

	def on_init(self):
		self.name = "Multicast"
		self.duration = 3
		self.copies = 1
		self.max_charges = 3
		self.multi_conjure = 0
		self.upgrades['copies'] = (1, 4)
		self.upgrades['duration'] = (4, 3)
		self.upgrades['max_charges'] = (4, 2)
		self.range = 0
		self.level = 7
		self.tags = [Tags.Enchantment, Tags.Arcane]

	def cast_instant(self, x, y):
		self.caster.apply_buff(MulticastBuff(self), self.get_stat('duration') + 1)

	def get_description(self):
		return ("Whenever you cast a [sorcery] spell, copy it.\n"
				"Lasts [{duration}_turns:duration]").format(**self.fmt_dict())

class FaeCourt(Spell):

	def on_init(self):
		self.name = "Fae Court"
		self.num_summons = 5
		self.max_charges = 2
		self.heal = 5
		self.minion_range = 4
		self.minion_duration = 15
		self.minion_health = 9
		self.shields = 1

		self.minion_damage = 4

		self.range = 0

		self.level = 5

		self.tags = [Tags.Nature, Tags.Arcane, Tags.Conjuration]

		self.upgrades['winter_fae'] = (1, 5, "Winter Faery", "Summon winter faeries instead of normal ones. Winter faeries resist ice and can cast your Freeze spell on a 5 turn cooldown.")
		self.upgrades['summon_queen'] = (1, 7, "Summon Queen", "A fae queen is summoned as well")
		self.upgrades['glass_fae'] = (1, 9, "Glass Faery", "Summon glass faeries instead of normal ones.")

	def get_description(self):
		return ("Summons a group of [{num_summons}:num_summons] faeries near the caster.\n"
				"The faeries fly, and have [{minion_health}_HP:minion_health], [{shields}_SH:shields], [75_arcane:arcane] resistance, and a passive blink.\n"
			    "The faeries can heal allies for [{heal}_HP:heal], with a range of [{minion_range}_tiles:minion_range].\n"
			    "The faeries have a [{minion_damage}_arcane:arcane] damage attack, with a range of [{minion_range}_tiles:minion_range].\n"
			    "The faeries vanish after [{minion_duration}_turns:minion_duration].").format(**self.fmt_dict())

	def get_extra_examine_tooltips(self):
		return [self.get_faery(), self.spell_upgrades[0], self.get_winter_faery(), self.spell_upgrades[1], self.get_faery_queen(), self.spell_upgrades[2], self.get_glass_faery()]

	def get_faery(self):
		unit = Unit()
		unit.sprite.char = 'f'
		unit.sprite.color = Color(252, 141, 249)

		unit.flying = True
		unit.max_hp = self.get_stat('minion_health')
		unit.shields = self.get_stat('shields')
		unit.buffs.append(TeleportyBuff(chance=.5))
		unit.spells.append(HealAlly(heal=self.get_stat('heal'), range=self.get_stat('minion_range') + 2))

		unit.turns_to_death = self.get_stat('minion_duration')
		unit.team = self.caster.team
		unit.tags = [Tags.Nature, Tags.Arcane, Tags.Living]
		unit.resists[Tags.Arcane] = 50

		unit.name = "Good Faery"
		unit.spells.append(SimpleRangedAttack(damage=self.get_stat('minion_damage'), range=self.get_stat('minion_range'), damage_type=Tags.Arcane))

		return unit

	def get_glass_faery(self):
		unit = self.get_faery()
		glassbolt = SimpleRangedAttack(damage=self.get_stat('minion_damage'), range=self.get_stat('minion_range'), damage_type=Tags.Arcane, effect=Tags.Glassification, buff=GlassPetrifyBuff, buff_duration=1)
		glassbolt.name = "Glassification Bolt"
		unit.spells[1] = glassbolt
		unit.name = "Glass Faery"
		unit.asset_name = "faery_glass"
		unit.tags.append(Tags.Glass)

		return unit

	def get_winter_faery(self):
		unit = self.get_faery()
		unit.name = "Winter Faery"
		unit.asset_name = "faery_ice"
		unit.tags.append(Tags.Ice)

		grant_minion_spell(Freeze, unit, self.caster, cool_down=5)

		unit.resists[Tags.Ice] = 100
		unit.resists[Tags.Fire] = -50

		return unit

	def get_faery_queen(self):
		unit = ThornQueen()
		unit.max_hp += self.minion_health - 9
		for s in unit.spells:
			if hasattr(s, 'damage'):
				s.damage += self.minion_damage - 4
		unit.turns_to_death = self.get_stat('minion_duration')

		return unit

	def cast(self, x, y):
		if self.get_stat('summon_queen'):
			p = self.caster.level.get_summon_point(self.caster.x, self.caster.y, sort_dist=False, flying=True, radius_limit=4)
			if p:	
				unit = self.get_faery_queen()
				self.summon(unit, p)

		for i in range(self.get_stat('num_summons')):

			unit = None
			if self.get_stat('glass_fae'):
				unit = self.get_glass_faery()
			elif self.get_stat('winter_fae'):
				unit = self.get_winter_faery()
			else:
				unit = self.get_faery()

			self.summon(unit, sort_dist=False)
			yield

class RingOfSpiders(Spell):

	def on_init(self):

		self.name = "Ring of Spiders"
		self.duration = 10
		self.range = 8

		self.level = 5
		self.max_charges = 2

		self.damage = 0
		self.aether_spiders = 0
		self.stun_duration = 1
		
		self.minion_health = 14
		self.minion_damage = 2

		self.upgrades['turbo_toxin'] = (1, 3, "Turbo Toxin", "Units blocking the spider ring instantly take 30 [poison_damage:poison].")
		self.upgrades['stun_duration'] = (4, 3, "Long Webs", "Units blocking the web ring are [stunned] for [5_turns:duration].")
		self.upgrades['aether_spiders'] = (1, 6)

		self.tags = [Tags.Nature, Tags.Conjuration]

	def get_description(self):
		return ("Summons a ring of giant spiders at the target, surrounded by a ring of webs.\n"
			 	"Units blocking the spider ring are [poisoned] for [{duration}_turns:duration], creatures blocking the web ring are [stunned] for [1_turn:duration].\n"
			 	"Giant spiders have [{minion_health}_HP:minion_health] and spin webs.\n"
			 	"Giant spiders have a melee attack which deals [{minion_damage}_physical:physical] and inflicts [5_turns:duration] of [poison].\n"
			 	"Webs [stun] non spider units which step on them for [1_turn:duration].\n"
			 	+ text.poison_desc + text.stun_desc).format(**self.fmt_dict())

	def get_impacted_tiles(self, x, y):
		return self.caster.level.get_points_in_rect(x-2, y-2, x+2, y+2)

	def cast(self, x, y):

		for p in self.get_impacted_tiles(x, y):
			unit = self.caster.level.get_unit_at(p.x, p.y)

			rank = max(abs(p.x - x), abs(p.y - y))

			if rank == 0:
				if self.get_stat('damage'):
					self.caster.level.deal_damage(x, y, self.get_stat('damage'), Tags.Poison, self)
			elif rank == 1:
				if not unit:
					if self.get_stat('aether_spiders'):
						spider = PhaseSpider()
					else:
						spider = GiantSpider()
					spider.team = self.caster.team
					
					spider.spells[0].damage = self.get_stat('minion_damage')
					spider.max_hp = self.get_stat('minion_health')

					self.summon(spider, p)

				if unit:
					if self.get_stat('turbo_toxin'):
						unit.deal_damage(self.get_stat('damage', base=30), Tags.Poison, self)
					unit.apply_buff(Poison(), self.get_stat('duration'))
			else:
				if not unit:
					cloud = SpiderWeb()
					cloud.owner = self.caster
					self.caster.level.add_obj(cloud, *p)
				if unit:
					unit.apply_buff(Stun(), self.get_stat('duration', base=self.get_stat('stun_duration')))
			yield

class HolyBlast(Spell):

	def on_init(self):

		self.name = "Heavenly Blast"
		self.range = 7
		self.radius = 1
		self.damage = 14

		self.damage_type = Tags.Holy
		
		self.max_charges = 12

		self.level = 2

		self.tags = [Tags.Holy, Tags.Sorcery] 

		self.upgrades['spiritbind'] = (1, 3, "Spirit Bind", "Slain enemies create temporary spirits.  Spirits are blinking holy undead with 4 hitpoints and a 2 damage ranged holy attack.")
		self.upgrades['shield'] = (1, 2, "Shield", "Affected ally units gain 2 SH, to a maximum of 5.")
		self.upgrades['echo_heal'] = (1, 2, "Echo Heal", "Affected ally units are re-healed for half the initial amount each turn for 5 turns.")

	def get_description(self):
		return "Deal [{damage}_holy:holy] damage to enemies and heal allies for [{damage}_hp:heal] along a beam and in a [{radius}_tile:radius] burst.".format(**self.fmt_dict())

	def get_impacted_tiles(self, x, y):
		burst = set(p for stage in Burst(self.caster.level, Point(x, y), self.get_stat('radius')) for p in stage)
		beam = set(Bolt(self.caster.level, self.caster, Point(x, y)))
		return burst.union(beam)

	def get_ai_target(self):
		enemy = self.get_corner_target(1)
		if enemy:
			return enemy
		else:
			allies = [u for u in self.caster.level.get_units_in_ball(self.caster, self.get_stat('range')) if u != self.caster and not are_hostile(self.caster, u) and not u.is_player_controlled]
			allies = [u for u in allies if self.caster.level.can_see(self.caster.x, self.caster.y, u.x, u.y)]
			allies = [u for u in allies if u.cur_hp < u.max_hp]
			if allies:
				return random.choice(allies)
		return None

	def cast(self, x, y):
		target = Point(x, y)

		def deal_damage(point):
			unit = self.caster.level.get_unit_at(point.x, point.y)
			if unit and not are_hostile(unit, self.caster) and not unit == self.caster and unit != self.statholder:
				unit.deal_damage(-self.get_stat('damage'), Tags.Heal, self)
				if self.get_stat('shield'):
					if unit.shields < 4:
						unit.add_shields(2)
					elif unit.shields == 4:
						unit.add_shields(1)
				if self.get_stat('echo_heal'):
					unit.apply_buff(RegenBuff(self.get_stat('damage') // 2), 5)
			elif unit == self.caster:
				pass
			elif unit and unit.is_player_controlled and not are_hostile(self.caster, unit):
				pass
			else:
				self.caster.level.deal_damage(point.x, point.y, self.get_stat('damage'), Tags.Holy, self)
				if unit and not unit.is_alive() and self.get_stat('spiritbind'):
					spirit = Unit()
					spirit.name = "Spirit"
					spirit.asset_name = "holy_ghost" # temp
					spirit.max_hp = 4
					spirit.spells.append(SimpleRangedAttack(damage=2, damage_type=Tags.Holy, range=3))
					spirit.turns_to_death = 7
					spirit.tags = [Tags.Holy, Tags.Undead]
					spirit.buffs.append(TeleportyBuff())
					apply_minion_bonuses(self, spirit)
					spirit.resists[Tags.Holy] = 100
					spirit.resists[Tags.Dark] = -100
					spirit.resists[Tags.Physical] = 100
					spirit.flying = True
					self.summon(spirit, target=unit)

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
			yield

class HolyFlame(Spell):

	def on_init(self):
		self.name = "Holy Fire"

		self.tags = [Tags.Fire, Tags.Holy, Tags.Sorcery]

		self.max_charges = 7

		self.damage = 22
		self.duration = 3
		self.lightning = 0
		self.cascade_range = 0
		self.radius = 2

		self.range = 7

		self.upgrades['holy_smite'] = (1, 2, "Holy Smite", "Holy Fire deals additional lightning damage on the center tile.")
		self.upgrades['divine_blaze'] = (1, 4, "Divine Blaze", "Holy Fire casts your Blazerip spell.")
		self.upgrades['heaven_call'] = (1, 4, "Heaven Call", "If Holy Fire kills a unit, gain a charge of Call Seraph.") #Changed to max of one recharge / turn for balance purposes

		self.level = 3

	def get_description(self):
		return ("Deal [{damage}_fire:fire] damage in a vertical line and [{damage}_holy:holy] damage in a horizontal line.\n"
				"[Stun] [demon] and [undead] units in the affected area.").format(**self.fmt_dict())

	def get_impacted_tiles(self, x, y):
		rad = self.get_stat('radius')
		for i in range(-rad, rad + 1):
			yield Point(x+i, y)
			if i != 0:
				yield Point(x, y+i)
		if self.get_stat('divine_blaze'):
			blazerip_spell = self.caster.get_or_make_spell(Blazerip)
			for p in blazerip_spell.get_impacted_tiles(x, y):
				yield p

	def cast(self, x, y):
		killed = False
		cur_target = Point(x, y)
		dtypes = [Tags.Holy, Tags.Fire]
		if self.get_stat('lightning'):
			dtypes.append(Tags.Lightning)

		rad = self.get_stat('radius')
		for i in range(y - rad, y + rad + 1):
			if not self.caster.level.is_point_in_bounds(Point(x, i)):
				continue

			unit = self.caster.level.get_unit_at(x, i)
			self.caster.level.deal_damage(x, i, self.get_stat('damage'), Tags.Fire, self)
			if unit and unit.is_alive() and (Tags.Demon in unit.tags or Tags.Undead in unit.tags):
				unit.apply_buff(Stun(), self.get_stat('duration'))
			elif self.get_stat('heaven_call') and unit and not unit.is_alive():
				killed = True

			yield

		for i in range(2):
			yield

		for i in range(x - rad, x + rad + 1):
			if not self.caster.level.is_point_in_bounds(Point(i, y)):
				continue

			unit = self.caster.level.get_unit_at(i, y)
			self.caster.level.deal_damage(i, y, self.get_stat('damage'), Tags.Holy, self)
			if unit and (Tags.Demon in unit.tags or Tags.Undead in unit.tags):
				unit.apply_buff(Stun(), self.get_stat('duration'))
			elif self.get_stat('heaven_call') and unit and not unit.is_alive():
				killed = True
			yield

		for i in range(2):
			yield

		#Max recharge once per cast instead of every kill, for balance purposes
		if killed: 
			seraph_spell = self.caster.get_spell(SummonSeraphim)
			if seraph_spell:
				seraph_spell.cur_charges += 1
				seraph_spell.cur_charges = min(seraph_spell.cur_charges, seraph_spell.get_stat('max_charges'))
				

		if self.get_stat('divine_blaze'):
			blazerip_spell = self.caster.get_or_make_spell(Blazerip)
			for _ in self.caster.level.act_cast(self.caster, blazerip_spell, x, y, pay_costs=False, queue=False):
				yield

		if self.get_stat('holy_smite'):
			self.caster.level.deal_damage(x, y, self.damage, Tags.Lightning, self)
			yield

class ConversionBuff(Buff):

	def on_init(self):
		self.name = "Mercy"
		self.color = Tags.Holy.color
		self.stacks = 0

	def on_advance(self):
		if self.stacks >= self.owner.max_hp and self.owner.team != self.spell.caster.team:
			self.owner.team = self.spell.caster.team

class AngelSong(Spell):

	def on_init(self):
		self.name = "Sing"
		self.description = "Living and holy units are healed, undead, demons, and dark units take holy and fire damage."
		self.radius = 5
		self.damage = 2
		self.heal = 1
		self.range = 0
		self.conversion = 0
		self.damage_type = [Tags.Fire, Tags.Holy]

	def cast_instant(self, x, y):
		for unit in self.caster.level.get_units_in_ball(Point(x, y), self.get_stat('radius')):
			if (Tags.Living in unit.tags or Tags.Holy in unit.tags) and unit.cur_hp < unit.max_hp:
				dmg = unit.deal_damage(-self.get_stat('heal'), Tags.Heal, self)
				if self.conversion:
					if not unit.get_buff(ConversionBuff):
						conversion_buff = ConversionBuff()
						conversion_buff.spell = self
						unit.apply_buff(conversion_buff)
					unit.get_buff(ConversionBuff).stacks += abs(dmg)
			if Tags.Dark in unit.tags or Tags.Undead in unit.tags or Tags.Demon in unit.tags:
				unit.deal_damage(self.get_stat('damage'), Tags.Fire, self)
				unit.deal_damage(self.get_stat('damage'), Tags.Holy, self)

	def get_ai_target(self):
		units = self.caster.level.get_units_in_ball(self.caster, self.get_stat('radius'))

		for unit in units:
			if unit.is_player_controlled:
				continue
			if (Tags.Living in unit.tags or Tags.Holy in unit.tags) and unit.cur_hp < unit.max_hp:
				return self.caster
			if Tags.Undead in unit.tags or Tags.Demon in unit.tags or Tags.Dark in unit.tags:
				return self.caster
		return None

class AngelicChorus(Spell):

	def on_init(self):
		self.name = "Choir of Angels"

		self.minion_health = 10
		self.shields = 1
		self.minion_duration = 10
		self.num_summons = 4
		self.heal = 1
		self.minion_damage = 2
		self.radius = 5

		self.range = 7

		self.tags = [Tags.Holy, Tags.Conjuration]
		self.level = 3

		self.max_charges = 3

		self.upgrades['cast_deathbolt'] = (1, 4, "Dual Angels", "Angels can cast your Death Bolt on a 4 turn cooldown.") #minor, silly issue: the angel's Sing kills the undead lol
		self.upgrades['conversion'] = (1, 5, "Mercy", "When an enemy is healed for a cumulative total more than its max health, it becomes an ally.")
		self.upgrades['num_summons'] = (4, 5, "Massive Chorus")

	def get_description(self):
		return ("Summons a choir of [{num_summons}:num_summons] angelic singers.\n"
				"The singers have [{minion_health}_HP:minion_health], [{shields}_SH:shields], 50% resistance to [fire] and [holy] damage, and 100% resistance to [dark] damage.\n"
				"The angels can sing, dealing [{minion_damage}_fire:fire] and [{minion_damage}_holy:holy] damage to all [undead], [demon], and [dark] units in a [{radius}_tile:radius] radius. "
				"[Living] and [holy] units in the song's radius are healed for [{heal}_HP:heal].\n"
				"The angels vanish after [{minion_duration}:minion_duration] turns.").format(**self.fmt_dict())

	def get_impacted_tiles(self, x, y):
		return [Point(x, y)]

	def cast(self, x, y):

		for i in range(self.get_stat('num_summons')):
			angel = Unit()
			angel.name = "Angelic Singer"
			angel.max_hp = self.get_stat('minion_health')
			angel.shields = self.get_stat('shields')
			
			song = AngelSong()
			song.damage = self.get_stat('minion_damage')
			song.heal = self.get_stat('heal')
			song.radius = self.get_stat('radius')
			song.conversion = self.get_stat('conversion')
			
			angel.spells.append(song)

			angel.flying = True
			angel.tags = [Tags.Holy]
			angel.resists[Tags.Holy] = 50
			angel.resists[Tags.Fire] = 50
			angel.resists[Tags.Dark] = 100

			angel.sprite.char = 'a'
			angel.sprite.color = Tags.Holy.color

			angel.turns_to_death = self.get_stat('minion_duration')
			
			if self.get_stat('cast_deathbolt'):
				grant_minion_spell(DeathBolt, angel, self.caster, cool_down=4)

			self.summon(angel, Point(x, y))
			yield

class HeavensWrath(Spell):

	def on_init(self):

		self.name = "Heaven's Wrath"

		self.num_targets = 3

		self.damage = 22

		self.level = 6
		self.max_charges = 2

		self.stun_duration = 0

		self.upgrades['culling'] = (1, 3, "Culling" ,"Heaven's Wrath also damages the units with the lowest current HP.")
		self.upgrades['stun_duration'] = (3, 3, "Halt Heretics", "Heaven's Wrath also applies Stun for [3_turns:duration].")
		self.upgrades['deal_fire'] = (1, 3, "Fiery Wrath", "Heaven's Wrath also deals fire damage.")

		self.tags = [Tags.Holy, Tags.Lightning, Tags.Sorcery]
		self.range = 0

	def get_description(self):
		return ("Deal [{damage}_lightning:lightning] damage and [{damage}_holy:holy] damage to [{num_targets}_units:num_targets] with the highest current HP.\n"
				"Does not target friendly units or gates.").format(**self.fmt_dict())

	def cast(self, x, y):

		orders = [-1]
		if self.get_stat('culling'):
			orders.append(1)

		for order in orders:
			units = [u for u in self.caster.level.units if are_hostile(u, self.caster) and not u.is_lair]
			random.shuffle(units)
			units = sorted(units,  key=lambda u: order * u.cur_hp)
			units = units[:self.get_stat('num_targets')]

			for unit in units:
				unit.deal_damage(self.get_stat('damage'), Tags.Lightning, self)
				for i in range(3):
					yield
				unit.deal_damage(self.get_stat('damage'), Tags.Holy, self)
				for i in range(3):
					yield
				if self.get_stat('deal_fire'):
					unit.deal_damage(self.get_stat('damage'), Tags.Fire, self)
				
				if self.get_stat('stun_duration'):
					stun_duration = self.get_stat('duration', base=self.get_stat('stun_duration')) #reworked to gain bonuses from duration -- yay or nay?
					unit.apply_buff(Stun(), stun_duration)

class BestowImmortality(Spell):

	def on_init(self):

		self.name = "Suspend Mortality"
		self.tags = [Tags.Dark, Tags.Holy, Tags.Enchantment]

		self.lives = 1
		self.level = 3

		self.max_charges = 8

		self.requires_los = False
		self.range = 8

		self.upgrades['lives'] = (2, 2, "Endlessness", "The target gains 3 reincarnations instead of just 1.")
		self.upgrades['mass'] = (1, 3, "Mass Immortaity", "All allies with the same name as the target are also affected.")
		self.upgrades['essence'] = (1, 2, "Twilight Essence", "Targeted unit gains the [holy] and [undead] tags and 25 [holy] and [dark] resist.")

	def get_description(self):
		return "Target allied unit gains the ability to reincarnate on death."

	def can_cast(self, x, y):
		unit = self.caster.level.get_unit_at(x, y)
		return unit and unit != self.caster and not unit.is_player_controlled

	def get_impacted_tiles(self, x, y):
		unit = self.caster.level.get_unit_at(x, y)
		units = [unit]
		if self.get_stat('mass'):
			units = [u for u in self.owner.level.units if not are_hostile(self.caster, u) and u.name == unit.name]
		
		return [Point(u.x, u.y) for u in units]

	def cast(self, x, y):
		unit = self.caster.level.get_unit_at(x, y)
		units = [unit]
		if self.get_stat('mass'):
			units = [u for u in self.owner.level.units if not are_hostile(self.caster, u) and u.name == unit.name]

		for u in units:
			buff = u.get_buff(ReincarnationBuff)
			if not buff:
				u.apply_buff(ReincarnationBuff(self.get_stat('lives')))
			if buff:
				buff.lives += self.get_stat('lives')

			if self.get_stat('essence'):
				u.resists[Tags.Dark] += 25
				u.resists[Tags.Holy] += 25
				if Tags.Undead not in u.tags:
					u.tags.append(Tags.Undead)
				if Tags.Holy not in u.tags:
					u.tags.append(Tags.Holy)

			self.owner.level.show_path_effect(self.caster, u, [Tags.Holy, Tags.Dark], minor=True, inclusive=False)
			yield
			self.owner.level.show_effect(u.x, u.y, Tags.Buff_Apply, Tags.Holy.color)
			yield

	def get_ai_target(self):
		elligible_targets = [u for u in self.caster.level.get_units_in_ball(self.caster, self.range) if not are_hostile(u, self.caster) and self.can_cast(u.x, u.y)]
		if elligible_targets:
			random.shuffle(elligible_targets)
			
			def return_reincarnations(unit):
				buff = unit.get_buff(ReincarnationBuff)
				if buff:
					return buff.lives
				else:
					return -1
			
			return min(elligible_targets, key=lambda u: return_reincarnations(u))
		else:
			return None


class SoulTax(Spell):

	def on_init(self):

		self.name = "Soul Tax"

		self.level = 5
		self.range = 4

		self.tags = [Tags.Sorcery, Tags.Dark, Tags.Holy]
		self.max_charges = 4
		self.arcane = 0

		self.upgrades['arcane'] = (1, 2, "Arcane Taxation", "Soul tax deals an additional third of the target's remaining HP as arcane damage.")
		self.upgrades['quick_cast'] = (1, 2, "Insta Tax", "Casting Soul Tax does not end your turn")
		self.upgrades['target_group'] = (1, 6, "Mass Taxation", "Targets a connected group of enemies.")

	def get_description(self):
		return ("Deal damage to target unit equal to one third of its health as [holy] damage, and then one third of its remaining health as [dark] damage.\n"
				"Heal the caster for the total amount of damage dealt.").format(**self.fmt_dict())		

	def can_cast(self, x, y):
		unit = self.caster.level.get_unit_at(x, y)
		if not unit:
			return False
		if not are_hostile(self.caster, unit):
			return False
		return Spell.can_cast(self, x, y)

	def get_impacted_tiles(self, x, y):
		if not self.get_stat('target_group'):
			return [Point(x, y)]
		else:
			return self.caster.level.get_connected_group_from_point(x, y, check_hostile=True)

	def cast(self, x, y):
		units = [self.caster.level.get_unit_at(x, y)]
		if self.get_stat('target_group'):
			units = self.caster.level.get_connected_group_from_point(x, y, check_hostile=True)
		for unit in units:
			if not unit:
				break
			dtypes = [Tags.Holy, Tags.Dark]
			if self.get_stat('arcane'):
				dtypes.append(Tags.Arcane)
			for dtype in dtypes:
				damage = unit.cur_hp // 3
				dealt = unit.deal_damage(damage, dtype, self)
				self.caster.deal_damage(-dealt, Tags.Heal, self)
				for i in range(4):
					yield
					
				# if the units dead, stop
				if not unit.is_alive():
					break
		yield


class HolyShieldBuff(Buff):

	def __init__(self, resist, resist_tags, thorns=False):
		Buff.__init__(self)
		self.name = "Holy Armor"
		self.buff_type = BUFF_TYPE_BLESS
		self.resist_tags = resist_tags
		self.thorns = thorns
		self.owner_triggers[EventOnDamaged] = self.on_damaged
		
		for tag in self.resist_tags:
			self.resists[tag] = resist

	def on_damaged(self, evt):
		if self.thorns:
			if evt.source.owner:
				evt.source.owner.deal_damage(7, Tags.Lightning, self)


class HolyShieldSpell(Spell):

	def on_init(self):
		self.name = "Holy Armor"

		self.tags = [Tags.Holy, Tags.Enchantment]
		self.level = 3
		self.duration = 9
		self.resist = 50
		self.max_charges = 6

		self.upgrades['resist'] = (25, 1, "Greater Armor")
		self.upgrades['crystal_armor'] = (1, 2, "Crystal Armor", "Also provides resistance to [arcane:arcane], [holy:holy], and [ice:ice].")
		self.upgrades['smiting_thorns'] = (1, 3, "Smiting Thorns", "Whenever you take damage, deal [7_lightning:lightning] damage to the source.")

		self.range = 0

	def cast_instant(self, x, y):
		tags = [Tags.Fire, Tags.Lightning, Tags.Dark, Tags.Physical]
		if self.get_stat('crystal_armor'):
			tags.append(Tags.Arcane)
			tags.append(Tags.Holy)
			tags.append(Tags.Ice)
		buff = HolyShieldBuff(self.get_stat('resist'), tags, thorns=self.get_stat('smiting_thorns'))
		self.caster.apply_buff(buff, self.get_stat('duration'))

	def get_description(self):
		return ("Gain [{resist}_physical:physical] resist.\n"
				"Gain [{resist}_fire:fire] resist.\n"
				"Gain [{resist}_lightning:lightning] resist.\n"
				"Gain [{resist}_dark:dark] resist.\n"
				"Lasts [{duration}_turns:duration].").format(**self.fmt_dict())

class BlindingLightSpell(Spell):

	def on_init(self):
		self.name = "Blinding Light"

		self.range = 0
		self.max_charges = 4
		self.duration = 4
		self.damage = 5

		self.tags = [Tags.Holy, Tags.Sorcery]
		self.level = 3
		self.dark_units = 0
		self.upgrades['inflict_stun'] = (1, 2, "Halting Light", "Deals [1_turn:duration] of stun to all enemy units.")
		self.upgrades['deal_fire'] = (1, 3, "Searing Light", "Deals [5_fire:fire] damage to all enemy units in LOS.") #restricting it to enemy units for now, maybe the cost could be lowered if it's all units?
		self.upgrades['quick_cast'] = (1, 2, "Quickcast", "Casting Blinding Light does not end your turn")


	def get_description(self):
		return ("[Blind] all units in line of sight of the caster for [{duration}_turns:duration].\n"
				+ text.blind_desc +
				"Deals [{damage}_holy:holy] damage to affected undead and demon units.").format(**self.fmt_dict())

	def cast(self, x, y):
		targets = [u for u in self.caster.level.get_units_in_los(self.caster) if u != self.caster]
		targets = sorted(targets, key=lambda u: distance(u, self.caster))

		for target in targets:
			target.apply_buff(BlindBuff(), self.get_stat('duration'))

			if self.get_stat('deal_fire') and are_hostile(self.caster, target):
				target.deal_damage(self.get_stat('damage'), Tags.Fire, self)

			if self.get_stat('inflict_stun'):
				target.apply_buff(Stun(), self.get_stat('duration', base=1))

			if not (Tags.Undead in target.tags or Tags.Demon in target.tags or (self.get_stat('dark_units') and Tags.Dark in target.tags)):
				continue
			target.deal_damage(self.get_stat('damage'), Tags.Holy, self)
			

			yield

class FlockOfEaglesSpell(Spell):

	def on_init(self):

		self.name = "Flock of Eagles"

		self.minion_health = 18
		self.minion_damage = 6
		self.minion_range = 5
		self.num_summons = 3
		self.shields = 0

		self.max_charges = 3

		self.upgrades['num_summons'] = (4, 6, "Army of Eagles")
		self.upgrades['shields'] = (3, 3, "Shielded Eagles")
		self.upgrades['thunderbirds'] = (1, 5, "Thunder Claw", "Eagles gain your Thunder Strike spell on a 15 turn cool down.")
		self.upgrades['awe'] = (1, 3, "Untouchable Majesty", "Eagles deal 1 [holy] damage to anyone dealing them damage.")

		self.range = 0

		self.level = 6
		self.tags = [Tags.Conjuration, Tags.Nature, Tags.Holy]

	def get_extra_examine_tooltips(self):
		return [self.make_eagle()] + self.spell_upgrades

	def get_description(self):
		return ("Summons [{num_summons}_eagles:num_summons] near the caster.\n"
				"Eagles have [{minion_health}_HP:minion_health] and can fly.\n"
				"Eagles have a melee attack which deals [{minion_damage}_physical:physical] damage.").format(**self.fmt_dict())

	def make_eagle(self):
			eagle = Unit()
			eagle.name = "Eagle"

			dive = LeapAttack(damage=self.get_stat('minion_damage'), range=self.get_stat('minion_range'), is_leap=True)
			peck = SimpleMeleeAttack(damage=self.get_stat('minion_damage'))

			dive.name = 'Dive'
			peck.name = 'Claw'

			eagle.spells.append(peck)
			eagle.spells.append(dive)
			eagle.max_hp = self.get_stat('minion_health')
			eagle.team = self.caster.team

			eagle.flying = True
			eagle.tags = [Tags.Living, Tags.Holy, Tags.Nature]

			eagle.shields = self.get_stat('shields')

			if self.get_stat('thunderbirds'):
				grant_minion_spell(ThunderStrike, eagle, self.caster, cool_down=15)

			if self.get_stat('awe'):
				eagle.buffs.append(RetaliationBuff(damage=1, dtype=Tags.Holy))

			return eagle

	def cast_instant(self, x, y):
		for i in range(self.get_stat('num_summons')):
			eagle = self.make_eagle()
			self.summon(eagle, Point(x, y))

class FlamingSwordSwing(Spell):

	def __init__(self, parent_spell):
		self.parent_spell = parent_spell
		Spell.__init__(self)

	def on_init(self):
		self.name = "Flaming Arc"
		self.description = "Swing your flaming sword"
		self.range = 1.5
		self.melee = True
		self.can_target_self = False
		self.max_charges = 50

	def get_impacted_tiles(self, x, y):
		ball = self.caster.level.get_points_in_ball(x, y, 1)
		aoe = [p for p in ball if 1 <= distance(p, self.caster, diag=True) < 2]
		return aoe

	def cast(self, x, y):
		for p in self.get_impacted_tiles(x, y):
			for dtype in [Tags.Fire, Tags.Holy]:
				self.caster.level.deal_damage(p.x, p.y, self.parent_spell.get_stat('damage'), dtype, self)
				yield

class FlamingSwordBuff(Buff):

	def __init__(self, spell):
		self.spell = spell
		Buff.__init__(self)
		self.color = Tags.Holy.color
		self.name = "Flaming Sword"

	def on_applied(self, owner):
		self.spell_slot = self.owner.spells.index(self.spell)
		self.owner.spells[self.spell_slot] = FlamingSwordSwing(self.spell)
		
		# Hack
		self.owner.spells[self.spell_slot].caster = self.owner

	def on_unapplied(self):
		self.owner.spells[self.spell_slot] = self.spell

class FlamingSwordSpell(Spell):

	def on_init(self):

		self.name = "Flaming Sword"
		self.description = "Wield a flaming sword.  The sword can be swung at adjacent enemies dealing fire and holy damage."
		self.duration = 15
		self.max_charges = 4

		self.tags = [Tags.Holy, Tags.Fire, Tags.Enchantment]
		self.level = 2
		self.range = 0

		self.damage = 14

		self.upgrades['damage'] = (14, 4)
		self.upgrades['duration'] = (30, 3)

	def cast_instant(self, x, y):
		self.caster.apply_buff(FlamingSwordBuff(self), self.get_stat('duration'))

class BeautyIdolBuff(Buff):

	def __init__(self, spell):
		self.spell = spell
		Buff.__init__(self)

	def on_applied(self, owner):
		self.name = "Beauty"

	def on_advance(self):
		units = self.owner.level.get_units_in_los(self.owner)
		for u in units:
			if u == self.owner:
				continue
			
			if are_hostile(u, self.owner):
				u.deal_damage(1, Tags.Holy, self)
				if Tags.Undead in u.tags or Tags.Demon in u.tags:
					u.deal_damage(1, Tags.Lightning, self)

			else:
				u.deal_damage(-self.spell.get_stat('heal'), Tags.Heal, self)

class HeavenlyIdolShieldGazeSpell(Spell):

	def on_init(self):
		self.name = "Shield Gaze"
		self.tags = [Tags.Holy]
		self.can_target_self = True

	def get_description(self):
		return ("Set the SH of a unit with less than 4 SH to 4 SH.").format(**self.fmt_dict())

	def cast(self, x, y):
		unit = self.caster.level.get_unit_at(x, y)
		if unit:
			unit.shields = 4
			for p in self.caster.level.get_points_in_line(self.caster, unit):
				self.caster.level.deal_damage(p.x, p.y, 0, Tags.Holy, self)
		yield

	def get_ai_target(self):
		elligible_targets = [u for u in self.caster.level.units if not are_hostile(u, self.caster) and u.shields < 4]
		elligible_targets = [u for u in elligible_targets if u != self.caster]
		if elligible_targets:
			random.shuffle(elligible_targets)
			unit = min(elligible_targets, key=lambda u: u.shields)
			return unit
		else:
			return None


class HeavenlyIdol(Spell):

	def on_init(self):

		self.name = "Heavenly Idol"
		
		self.level = 5
		self.tags = [Tags.Holy, Tags.Lightning, Tags.Conjuration]
		self.max_charges = 4

		self.minion_health = 35
		self.shields = 2
		self.fire_gaze = 0
		self.heal = 1
		self.minion_duration = 15

		self.upgrades['fire_gaze'] = (1, 4, "Fire Gaze", "The Idol gains a fire beam attack")
		self.upgrades['shield_gaze'] = (1, 4, "Shield Gaze", "The Idol gains a single-target +4 SH ability, which sets the SH of a unit with less than 4 SH to 4 SH.")
		self.upgrades['immortality'] = (1, 6, "Bastion of Immortality", "Casts your Suspend Mortality on summoned ally units with a 5 turn cooldown")

		self.must_target_walkable = True
		self.must_target_empty = True

	def get_description(self):
		return ("Summon an Idol of Beauty.\n"
				"The idol has [{minion_health}_HP:minion_health], [{shields}_SH:shields], and is stationary.\n"
				"The idol has a passive aura which affects all units in line of sight of the idol each turn.\n"
				"Affected allies are healed for [{heal}_HP:heal].\n"
				"Affected enemies take [1_holy:holy] damage.\n"
				"Affected [undead] and [demon] units take an additional [1_lightning:lightning] damage.\n"
				"The idol vanishes after [{minion_duration}_turns:minion_duration].").format(**self.fmt_dict())

	def cast_instant(self, x, y):

		idol = Unit()
		idol.sprite.char = 'I'
		idol.sprite.color = Tags.Construct.color
		idol.asset_name = "idol"
		idol.name = "Idol of Beauty"
		idol.asset_name = "heavenly_idol"

		idol.max_hp = self.get_stat('minion_health')
		idol.shields = self.get_stat('shields')
		idol.stationary = True

		idol.resists[Tags.Physical] = 75
		
		idol.tags = [Tags.Construct, Tags.Holy]

		idol.buffs.append(BeautyIdolBuff(self))
		idol.turns_to_death = self.get_stat('minion_duration')

		if self.get_stat('immortality'):
			grant_minion_spell(BestowImmortality, idol, self.caster, cool_down=5)
		if self.get_stat('shield_gaze'):
			gaze = HeavenlyIdolShieldGazeSpell()
			idol.spells.append(gaze)
		if self.get_stat("fire_gaze"):
			gaze = SimpleRangedAttack(damage=8, range=10, beam=True, damage_type=Tags.Fire)
			gaze.name = "Fiery Gaze"
			idol.spells.append(gaze)

		self.summon(idol, Point(x, y))

class GoldGuardian(Upgrade):

	def on_init(self):
		self.prereq = SummonGoldDrakeSpell
		self.name = "Golden Crusade"
		self.level = 2
		self.description = "Gain a free charge of Gold Drake whenever you enter a rift containing atleast 1 [undead] or [demon] unit."
		self.owner_triggers[EventOnUnitAdded] = self.on_unit_add

	def on_unit_add(self, evt):
		for u in self.owner.level.units:
			if Tags.Undead in u.tags or Tags.Demon in u.tags:
				if self.prereq.cur_charges < self.prereq.get_stat('max_charges'):
					self.prereq.cur_charges += 1
					return

class DragonSaintThornsBuff(Buff):

	def __init__(self, spell):
		self.spell = spell
		Buff.__init__(self)

	def on_init(self):
		self.name = "Dragon Saint"
		self.color = Tags.Holy.color
		self.description = "Deal 14 [holy_damage:holy] to anything that deals damage to the unit."
		self.owner_triggers[EventOnDamaged] = self.on_damaged

	def on_damaged(self, evt):
		if evt.source.owner:
			evt.source.owner.deal_damage(self.spell.get_stat('damage', base=14), Tags.Holy, self)

class SummonGoldDrakeSpell(Spell):

	def on_init(self):
		self.name = "Gold Drake"
		self.range = 4
		self.max_charges = 2
		self.tags = [Tags.Holy, Tags.Conjuration, Tags.Dragon]
		self.level = 6

		self.minion_health = 45
		self.minion_damage = 8
		self.breath_damage = 9
		self.minion_range = 7
		self.shields = 0

		self.upgrades['dragon_saint'] = (1, 3, "Dragon Saint", "Deals 14 [holy_damage:holy] to anything that deals damage to the Gold Drake.")
		self.upgrades['immortal_dragon'] = (1, 3, "Immortal Dragon", "Gold Drake gains the Immortal modifier.")
		self.upgrades['dragon_mage'] = (1, 4, "Dragon Mage", "Summoned Gold Drakes can cast Healing Light with a 8 turn cooldown.\nThis Healing Light gains all of your upgrades and bonuses.")
		#self.add_upgrade(GoldGuardian())

		self.must_target_empty = True

	def cast_instant(self, x, y):
		drake = GoldDrake()
		drake.team = self.caster.team
		drake.max_hp = self.get_stat('minion_health')
		drake.spells[0].damage = self.get_stat('breath_damage')
		drake.spells[0].range = self.get_stat('minion_range')
		drake.spells[1].damage = self.get_stat('minion_damage')
		drake.shields += self.get_stat('shields')
		
		if self.get_stat('dragon_mage'):
			hlight = HealMinionsSpell()
			hlight.statholder = self.caster
			hlight.max_charges = 0
			hlight.cur_charges = 0
			hlight.cool_down = 8
			drake.spells.insert(1, hlight)

		if self.get_stat('dragon_saint'):
			drake.apply_buff(DragonSaintThornsBuff(self))

		if self.get_stat('immortal_dragon'):
			BossSpawns.apply_modifier(BossSpawns.Immortal, drake)

		self.summon(drake, Point(x, y))

	def get_description(self):
		return ("Summon a Gold Drake.\n"
				"Gold drakes have [{minion_health}_HP:minion_health], [100_holy:holy] resist, and can fly.\n"
				"Gold drakes have a breath weapon which deals [{breath_damage}_holy:holy] damage to enemies and heals allies for [{breath_damage}_HP:heal].\n"
				"Gold drakes have a melee attack which deals [{minion_damage}_physical:physical] damage").format(**self.fmt_dict())

class SeraphimSwordSwing(Spell):

	def on_init(self):
		self.name = "Flaming Sword"
		self.description = "Deals damage in an arc\nDeals fire and holy damage"
		self.range = 1.5
		self.melee = True
		self.can_target_self = False
		
		self.damage = 0 # to be overwritten
		self.damage_type = [Tags.Fire, Tags.Holy] # for bloodlust

	def get_impacted_tiles(self, x, y):
		ball = self.caster.level.get_points_in_ball(x, y, 1, diag=True)
		aoe = [p for p in ball if 1 <= distance(p, self.caster, diag=True) < 2]
		return aoe

	def cast(self, x, y):
		dtypes = [Tags.Fire, Tags.Holy]
		if self.arcane:
			dtypes += [Tags.Arcane]
		for p in self.get_impacted_tiles(x, y):
			for dtype in dtypes:
				# Never hit friendly units, is angel
				unit = self.caster.level.get_unit_at(p.x, p.y)
				if unit and not are_hostile(self.caster, unit):
					continue
				self.caster.level.deal_damage(p.x, p.y, self.get_stat('damage'), dtype, self)
				yield

class SummonSeraphim(Spell):

	def on_init(self):
		self.name = "Call Seraph"
		self.range = 4
		self.max_charges = 4
		self.tags = [Tags.Holy, Tags.Fire, Tags.Conjuration]

		self.minion_health = 33
		self.shields = 3
		self.minion_damage = 14

		self.minion_duration = 14
		self.heal = 0

		self.upgrades['moonblade'] = (1, 3, "Moonblade", "The Seraph deals arcane damage in addition to fire and holy damage with its cleave attack.")
		self.upgrades['heal'] = (4, 4, "Heal Aura", "The Seraph heals all allies within 4 tiles for 4 HP each turn.", "aura")
		self.upgrades['holy_fire'] = (1, 5, "Holy Fire Aura", "The Seraph gains a damage aura, randomly dealing either [2_fire:fire] or [2_holy:holy] damage to enemies within 5 tiles each turn.", "aura")
		self.level = 4

		self.must_target_empty = True

	def get_description(self):
		return ("Summon a seraph.\n"
				"Seraphim have [{minion_health}_HP:minion_health], [{shields}_SH:shields], and can fly.\n"
				"Seraphim have a cleaving melee attack which deals [{minion_damage}_fire:fire] and [{minion_damage}_holy:holy] damage.\n"
				"The seraph vanishes after [{minion_duration}_turns:minion_duration].").format(**self.fmt_dict())

	def cast_instant(self, x, y):

		angel = Unit()
		angel.name = "Seraph"
		angel.asset_name = "seraphim"
		angel.tags = [Tags.Holy]

		angel.sprite.char ='S'
		angel.sprite.color = Tags.Holy.color

		angel.max_hp = self.get_stat('minion_health')
		angel.shields = self.get_stat('shields')

		angel.resists[Tags.Holy] = 100
		angel.resists[Tags.Dark] = 75
		angel.resists[Tags.Fire] = 75

		sword = SeraphimSwordSwing()
		sword.damage = self.get_stat('minion_damage')
		sword.arcane = self.get_stat('moonblade')
		angel.spells.append(sword)
		angel.flying = True
		if self.get_stat('heal'):
			angel.buffs.append(HealAuraBuff(self.get_stat('heal'), 5))

		if self.get_stat('essence'):
			aura = EssenceAuraBuff()
			aura.radius = 5
			angel.buffs.append(aura)

		if self.get_stat('holy_fire'):
			aura = DamageAuraBuff(damage=2, damage_type=[Tags.Fire, Tags.Holy], radius=5)
			angel.buffs.append(aura)

		angel.turns_to_death = self.get_stat('minion_duration')

		self.summon(angel, Point(x, y))
		
class ArchonLightning(Spell):

	def on_init(self):
		self.name = "Archon Lightning"
		self.description = "Beam attack\nShields allies in the Aoe"
		self.damage_type = Tags.Lightning

	def handle_point(self, x, y):
		unit = self.caster.level.get_unit_at(x, y)
		if unit and not are_hostile(unit, self.caster):
			unit.add_shields(1)
			if self.get_stat('healing'):
				self.caster.level.deal_damage(unit.x, unit.y, -self.get_stat('damage'), Tags.Heal, self)
		else:
			self.caster.level.deal_damage(x, y, self.get_stat('damage'), Tags.Lightning, self)
			if self.get_stat('storm_archon'):
				self.caster.level.deal_damage(x, y, self.get_stat('damage'), Tags.Ice, self)

	def cast_instant(self, x, y):
		for p in self.caster.level.get_points_in_line(self.caster, Point(x, y), find_clear=True)[1:]:
			self.handle_point(p.x, p.y)
		
		if self.get_stat('cascade'):
			eligible_units = self.caster.level.get_units_in_ball(Point(x, y), self.get_stat('range')) #Assumed cascade range is same as range, lmk if you want me to change this
			eligible_units = [u for u in eligible_units if are_hostile(u, self.caster)]
			
			if eligible_units:
				unit = random.choice(eligible_units)
				for p in self.caster.level.get_points_in_line(Point(x, y), unit, find_clear=True)[1:]:
					self.handle_point(p.x, p.y)

class SummonArchon(Spell):

	def on_init(self):

		self.name = "Call Archon"
		self.tags = [Tags.Lightning, Tags.Holy, Tags.Conjuration]

		self.max_charges = 4

		self.minion_health = 77
		self.shields = 3
		self.minion_damage = 14

		self.minion_duration = 17
		self.minion_range = 8

		self.upgrades['healing'] = (1, 3, "Heal Beam", "Archon's attack heals allies it passes through.")
		self.upgrades['cascade'] = (1, 4, "Beam Arc", "Archon's attack arcs a maximum of one time to a nearby enemy.")
		self.upgrades['storm_archon'] = (1, 4, "Storm Archon", "Archon gains 50 Ice resist and its attack also deals Ice damage.")

		self.level = 5

		self.must_target_empty = True

	def get_description(self):
		return ("Summon an Archon.\n"
				"Archons have [{minion_health}_HP:minion_health], [{shields}_SH:shields], and can fly.\n"
				"Archons have beam attacks which deal [{minion_damage}_lightning:lightning] damage to enemies and shield allies.\n"
				"The Archon vanishes after [{minion_duration}_turns:minion_duration].").format(**self.fmt_dict())

	def cast_instant(self, x, y):

		angel = Unit()
		angel.name = "Archon"
		angel.tags = [Tags.Holy]
		
		angel.sprite.char ='A'
		angel.sprite.color = Tags.Holy.color

		angel.max_hp = self.get_stat('minion_health')
		angel.shields = self.get_stat('shields')

		angel.resists[Tags.Holy] = 100
		angel.resists[Tags.Dark] = 75
		angel.resists[Tags.Lightning] = 75

		lightning = ArchonLightning()
		lightning.damage = self.get_stat('minion_damage')
		lightning.range = self.get_stat('minion_range')
		lightning.healing = self.get_stat('healing')
		lightning.cascade = self.get_stat('cascade')
		lightning.storm_archon = self.get_stat('storm_archon')

		if self.get_stat('storm_archon'):
			lightning.damage_type = [Tags.Ice, Tags.Lightning]

		angel.spells.append(lightning)
		angel.flying = True

		angel.turns_to_death = self.get_stat('minion_duration')

		if self.get_stat('storm_archon'):
			angel.name = "Storm Archon"
			angel.asset_name = "archon_storm"
			angel.tags.append(Tags.Ice)
			angel.resists[Tags.Ice] = 50

		self.summon(angel, Point(x, y))


class PainMirror(Buff):

	def __init__(self, source=None):
		Buff.__init__(self)
		self.source = source

	def on_init(self):
		self.name = "Pain Mirror"
		self.owner_triggers[EventOnDamaged] = self.on_damage
		self.color = Tags.Dark.color
		self.dmg_tags = [Tags.Dark]
		self.dmg_taken = 0

	def on_damage(self, event):
		if self.source.get_stat('flesh_harvest'):
			self.dmg_taken += event.damage
			while self.dmg_taken >= 100:
				self.dmg_taken -= 100
				flesh_fiend_spell = self.source.caster.get_spell(FleshFiendSpell)
				if flesh_fiend_spell:
					flesh_fiend_spell.cur_charges = min(flesh_fiend_spell.cur_charges + 1, flesh_fiend_spell.get_stat('max_charges'))

		self.owner.level.queue_spell(self.reflect(event.damage))

	def reflect(self, damage):
		for u in self.owner.level.get_units_in_los(self.owner):
			if are_hostile(self.owner, u):
				for tag in self.dmg_tags:
					u.deal_damage(damage, tag, self.source or self)
					yield


class PainMirrorSpell(Spell):

	def on_init(self):
		self.name = "Pain Mirror"
		self.range = 0
		self.duration = 14
		self.hp_cost = 11

		self.level = 4

		self.max_charges = 1

		self.upgrades['flesh_harvest'] = (1, 3, "Flesh Harvest", "For every 100 damage taken during Pain Mirror, gain a charge of Summon Flesh Fiend.")
		self.upgrades['gain_resists'] = (1, 5, "Dulled Pain", "Gain 25% resist to [dark:dark], [arcane:arcane], [fire:fire], [lightning:lightning], and [physical:physical] damage during pain mirror.")
		self.upgrades['deal_fire'] = (1, 6, "Burning Pain", "Additionally deal [fire:fire] damage.")

		self.tags = [Tags.Blood, Tags.Enchantment]

	def cast_instant(self, x, y):
		buff = PainMirror(self)
		buff.asset = ["status", "pain_mirror"]
		if self.get_stat('deal_fire'):
			buff.dmg_tags.append(Tags.Fire)
		if self.get_stat('gain_resists'):
			tags = [Tags.Dark, Tags.Arcane, Tags.Fire, Tags.Lightning, Tags.Physical]
			for tag in tags:
				buff.resists[tag] = 25
		self.caster.apply_buff(buff, self.get_stat('duration'))

	def get_description(self):
		return ("Whenever you take damage, deal that much [dark] damage to all enemies in line of sight.\n"
				"Lasts [{duration}_turns:duration].").format(**self.fmt_dict())

class PyrostaticPulse(Spell):

	def on_init(self):
		self.name = "Pyrostatic Pulse"
		self.level = 2

		self.damage = 16

		self.max_charges = 9
		self.range = 6
		self.tags = [Tags.Fire, Tags.Lightning, Tags.Sorcery]

		self.upgrades['chaos'] = (1, 3, "Chaos Pulse", "Add a physical damage layer.")
		self.upgrades['lesser_cascade'] = (1, 5, "Lesser Cascade", "[Lightning:lightning] damage arcs to [2:num_targets] enemy units in line of sight.")
		self.upgrades['greater_cascade'] = (1, 7, "Greater Cascade", "On kill, jump to a new target")

	def get_description(self):
		return ("Deal [{damage}_fire:fire] damage in a beam.\n"
				"Deal [{damage}_lightning:lightning] damage to tiles adjacent to the beam.").format(**self.fmt_dict())

	def get_impacted_tiles(self, x, y):
		center_beam = self.caster.level.get_points_in_line(self.caster, Point(x, y), find_clear=True)[1:]
		side_beam = []
		physical_beam = []
		for p in center_beam:
			for q in self.caster.level.get_points_in_ball(p.x, p.y, 1.5):
				if q.x == self.caster.x and q.y == self.caster.y:
					continue
				if q not in center_beam and q not in side_beam:
					side_beam.append(q)
		
		for p in side_beam:
			for q in self.caster.level.get_points_in_ball(p.x, p.y, 1.5):
				if q.x == self.caster.x and q.y == self.caster.y:
					continue
				if self.get_stat('chaos') and q not in center_beam and q not in side_beam and q not in physical_beam:
					physical_beam.append(q)
		return center_beam + side_beam + physical_beam

	def do_spell(self, start, end): #will think of a better name for this function lol
		center_beam = self.caster.level.get_points_in_line(start, end, find_clear=True)[1:]
		side_beam = []
		physical_beam = []
		for p in center_beam:
			for q in self.caster.level.get_points_in_ball(p.x, p.y, 1.5):
				if q.x == self.caster.x and q.y == self.caster.y:
					continue
				if q not in center_beam and q not in side_beam:
					side_beam.append(q)

		for p in side_beam:
			for q in self.caster.level.get_points_in_ball(p.x, p.y, 1.5):
				if q.x == self.caster.x and q.y == self.caster.y:
					continue
				if self.get_stat('chaos') and q not in center_beam and q not in side_beam and q not in physical_beam:
					physical_beam.append(q)

		lightning_cascades = []

		for p in center_beam:
			unit = self.caster.level.get_unit_at(p.x, p.y)
			self.caster.level.deal_damage(p.x, p.y, self.get_stat('damage'), Tags.Fire, self)
			if self.get_stat('greater_cascade') and unit and not unit.is_alive():
				elligible_targets = [u for u in self.caster.level.get_units_in_los(p) if are_hostile(u, self.caster)]
				if elligible_targets:
					t = random.choice(elligible_targets)
					self.do_spell(p, t)

		for p in side_beam:
			unit = self.caster.level.get_unit_at(p.x, p.y)
			if unit:
				lightning_cascades.append(unit)
			self.caster.level.deal_damage(p.x, p.y, self.get_stat('damage'), Tags.Lightning, self)
			if self.get_stat('greater_cascade') and unit and not unit.is_alive():
				elligible_targets = [u for u in self.caster.level.get_units_in_los(p) if are_hostile(u, self.caster)]
				if elligible_targets:
					t = random.choice(elligible_targets)
					self.do_spell(p, t)

		for p in physical_beam:
			unit = self.caster.level.get_unit_at(p.x, p.y)
			self.caster.level.deal_damage(p.x, p.y, self.get_stat('damage'), Tags.Physical, self)
			if self.get_stat('greater_cascade') and unit and not unit.is_alive():
				elligible_targets = [u for u in self.caster.level.get_units_in_los(p) if are_hostile(u, self.caster)]
				if elligible_targets:
					t = random.choice(elligible_targets)
					self.do_spell(p, t)

		if self.get_stat('lesser_cascade'):
			for p in lightning_cascades:
				elligible_targets = [u for u in self.caster.level.get_units_in_los(p) if are_hostile(u, self.caster)]
				cascades = []
				if elligible_targets:
					for i in range(min(self.get_stat('num_targets', base=2), len(elligible_targets))):
						targ = random.choice(elligible_targets)
						cascades.append(targ)
						line = self.caster.level.get_points_in_line(p, targ)
						for q in line:
							self.caster.level.deal_damage(q.x, q.y, 0, Tags.Lightning, self)
						self.caster.level.deal_damage(q.x, q.y, self.get_stat('damage'), Tags.Lightning, self)

	def cast_instant(self, x, y):
		self.do_spell(self.caster, Point(x, y))

class ThunderStone(Prop):

	def __init__(self):
		self.name = "Thunder Stone"
		self.asset = ['tiles', 'thunderstone']
		self.damage = 0

	def on_unit_enter(self, player):
		candidates = self.level.get_units_in_los(self)
		candidates = [u for u in candidates if are_hostile(player, u)]
		candidates = sorted(candidates, key=lambda u: -distance(u, player))
		if candidates:
			target = candidates[0]
		else:
			target = player
		self.level.queue_spell(self.arc(target))
		self.level.remove_obj(self)

	def arc(self, target):

		self.level.deal_damage(self.x, self.y, 0, Tags.Lightning), self	
		for p in self.level.get_points_in_line(self, target)[1:]:
			unit = self.level.get_unit_at(point.x, point.y)
			if unit and unit.team == TEAM_PLAYER:
				continuenue
			self.level.deal_damage(p.x, p.y, self.damage, Tags.Lightning, self)
		yield

class ThunderStones(Spell):

	def on_init(self):
		self.name = "Thunder Stones"
		self.description = "Create several thunderstones nearby on the ground.  When a unit step on a stone, lightning arcs to the farthest visible enemy, dealing damage to enemies in a beam."
		self.level = 2
		self.tags = [Tags.Lightning, Tags.Sorcery]

		self.damage = 14
		self.num_stones = 4
		self.max_charges = 12
		self.range = 0

		self.upgrades['damage'] = (9, 3)
		self.upgrades['num_stones'] = (2, 3)

	def cast_instant(self, x, y):

		candidate_points = self.caster.level.get_points_in_ball(x, y, 3)

		def can_target(p):
			tile = self.caster.level.tiles[p.x][p.y]
			if tile.prop:
				return False
			if not tile.can_walk:
				return False
			return True

		candidate_points = [p for p in candidate_points if can_target(p)]

		random.shuffle(candidate_points)

		for i in range(self.get_stat('num_stones')):
			if not candidate_points:
				break
			p = candidate_points.pop()
			prop = ThunderStone()
			prop.damage = self.get_stat('damage')
			self.caster.level.add_obj(prop, p.x, p.y)

class FireStone(Prop):

	def __init__(self):
		self.name = "Fire Stone"
		self.asset = ['tiles', 'firestone']
		self.damage = 0
		self.radius = 0

	def on_unit_enter(self, player):
		candidates = self.level.get_units_in_los(self)
		candidates = [u for u in candidates if are_hostile(player, u)]
		candidates = sorted(candidates, key=lambda u: -distance(u, player))
		if candidates:
			target = candidates[0]
		else:
			target = player
		self.level.queue_spell(self.explode())
		self.level.remove_obj(self)

	def explode(self):
		for stage in Burst(self.level, self, self.radius):
			for point in stage:
				unit = self.level.get_unit_at(point.x, point.y)
				if unit and unit.team == TEAM_PLAYER:
					continue
				self.level.deal_damage(point.x, point.y, self.damage, Tags.Fire, self)

			for i in range(3):
				yield

class FireStones(Spell):

	def on_init(self):
		self.name = "Fire Stones"
		self.description = "Create several firestones nearby on the ground.  When a unit step on a stone, it bursts into flames, dealing damage to enemies in an area."
		self.level = 2
		self.tags = [Tags.Fire, Tags.Sorcery]

		self.damage = 16
		self.num_stones = 4
		self.radius = 3
		self.max_charges = 12
		self.range = 0

		self.upgrades['damage'] = (11, 3)
		self.upgrades['num_stones'] = (2, 2)
		self.upgrades['radius'] = (2, 3)

	def cast_instant(self, x, y):

		candidate_points = self.caster.level.get_points_in_ball(x, y, 3)

		def can_target(p):
			tile = self.caster.level.tiles[p.x][p.y]
			if tile.prop:
				return False
			if not tile.can_walk:
				return False
			return True

		candidate_points = [p for p in candidate_points if can_target(p)]

		random.shuffle(candidate_points)

		for i in range(self.get_stat('num_stones')):
			if not candidate_points:
				break
			p = candidate_points.pop()
			prop = FireStone()
			prop.damage = self.get_stat('damage')
			prop.radius = self.get_stat('radius')
			self.caster.level.add_obj(prop, p.x, p.y)

class VoidRip(Spell):

	def on_init(self):
		self.name = "Aether Swap"
		self.range = 7

		self.max_charges = 8
		self.damage = 16
		self.level = 3

		self.upgrades['petrify'] = (1, 3, "Petrification", "Casts your Petrify on the target.")
		self.upgrades['requires_los'] = (-1, 4, "Blindcasting", "Aether Swap can be cast without line of sight")
		self.upgrades['quick_cast'] = (1, 3, "Quickcast", "Casting Aether Swap does not end your turn")

		self.tags = [Tags.Arcane, Tags.Translocation, Tags.Sorcery]

	def get_description(self):
		return ("Swap places with target unit.\n"
				"That unit takes [{damage}_arcane:arcane] damage.\n"
				"Cannot target [arcane] immune units.").format(**self.fmt_dict())

	def can_cast(self, x, y):
		unit = self.caster.level.get_unit_at(x, y)
		if not unit:
			return False

		if unit == self.caster:
			return False
		
		if unit.resists[Tags.Arcane] >= 100:
			return False
		
		if not unit.can_teleport():
			return False

		# Ensure the caster can go where he is trying to go
		if not self.caster.level.can_stand(x, y, self.caster, check_unit=False):
			return False

		# Ensure that the target can stand where its getting swapped to (prevent flying crash)
		if not self.owner.level.can_stand(self.caster.x, self.caster.y, unit, check_unit=False):
			return False
		return Spell.can_cast(self, x, y)

	def cast_instant(self, x, y):
		target = self.caster.level.get_unit_at(x, y)
		
		# Fizzle if attempting to cast on non walkable tile
		if self.caster.level.can_move(self.caster, x, y, teleport=True, force_swap=True):
			self.caster.level.act_move(self.caster, x, y, teleport=True, force_swap=True)	
			
		if target:
			target.deal_damage(self.get_stat('damage'), Tags.Arcane, self)
			if self.get_stat('petrify') and target:
				petrify_spell = self.caster.get_or_make_spell(PetrifySpell)
				for _ in self.caster.level.act_cast(self.caster, petrify_spell, target.x, target.y, pay_costs=False, queue=False):
					pass

class ShieldSiphon(Spell):

	def on_init(self):
		self.name = "Siphon Shields"

		self.max_charges = 3
		self.level = 4

		self.tags = [Tags.Arcane, Tags.Enchantment]
		self.range = 0

		self.shield_burn = 0
		self.shield_steal = 1

		self.upgrades['shield_burn'] = (5, 2, "Shield Burn", "Deal 5 fire damage per shield stolen")
		self.upgrades['shield_steal'] = (4, 1)

	def get_impacted_tiles(self, x, y):
		return [u for u in self.caster.level.get_units_in_los(self.caster) if are_hostile(u, self.caster) and u.shields]

	def get_description(self):
		return ("Steal up to [{shield_steal}_SH:shields] from all enemy units in line of sight.").format(**self.fmt_dict())

	def cast(self, x, y):

		total = 0
		targets = [u for u in self.caster.level.get_units_in_los(self.caster) if are_hostile(u, self.caster)]
		for u in targets:

			if not u.shields:
				continue

			stolen = min(self.get_stat('shield_steal'), u.shields)

			self.caster.level.show_effect(u.x, u.y, Tags.Shield_Expire)			
			u.shields -= stolen

			if self.get_stat('shield_burn'):
				u.deal_damage(stolen * self.get_stat('shield_burn'), Tags.Fire, self)

			total += stolen

			yield

		if total:
			self.caster.add_shields(total)

		yield


class VoidMaw(Spell):

	def on_init(self):
		self.name = "Hungry Maw"

		self.max_charges = 6
		self.level = 2
		self.tags = [Tags.Arcane, Tags.Conjuration]
		self.range = 7

		self.minion_range = 7
		self.minion_damage = 9
		self.minion_health = 8
		self.minion_duration = 15
		self.shields = 2

		self.upgrades['devour'] = (1, 3, "Gnashing Teeth", "Hungry Maw gains a [physical] melee attack which attacks four times")
		self.upgrades['shields'] = (5, 3, "Invincible Maw")
		self.upgrades['void'] = (1, 5, "Void Maw", "Hungry Maw gains a wall melting arcane beam attack")
		
		self.must_target_empty = True

	def get_description(self):
		return ("Summons a hungry maw.\n"
				"The maw is shielded, floats, and is stationary.\n"
				"The maw has a ranged [physical] attack, which pulls enemies towards it.\n"
				"The maw vanishes after [{minion_duration}_turns:minion_duration].").format(**self.fmt_dict())
	
	def get_extra_examine_tooltips(self):
		return [self.make_maw()] + self.spell_upgrades

	def make_maw(self):
		u = Unit()
		u.tags = [Tags.Arcane, Tags.Demon]
		u.name = "Hungry Maw"
		u.max_hp = self.get_stat('minion_health')
		u.shields = self.get_stat('shields')
		u.asset_name = 'floating_mouth'


		if self.get_stat('devour'):
			devour = SimpleMeleeAttack(damage=self.get_stat('minion_damage'), attacks=4)
			devour.name = "Gnashing Teeth"
			u.spells.append(devour)

		u.spells.append(PullAttack(damage=self.get_stat('minion_damage'), range=self.get_stat('minion_range'), color=Tags.Tongue.color))

		if self.get_stat('void'):
			beam = SimpleRangedAttack(damage=self.get_stat('minion_damage'), range=self.get_stat('minion_range')+3, melt=True,
			 						  damage_type=Tags.Arcane, beam=True)
			beam.cool_down = 3
			u.spells.insert(0, beam)

		u.flying = True
		u.stationary = True

		u.turns_to_death = self.get_stat('minion_duration')

		u.resists[Tags.Arcane] = 75
		u.resists[Tags.Dark] = 50
		u.resists[Tags.Lightning] = -50
		return u

	def cast_instant(self, x, y):
		u = self.make_maw()
		self.summon(u, Point(x, y))


class RotBuff(Buff):

	def __init__(self, spell):
		self.spell = spell
		Buff.__init__(self)

	def on_init(self):
		self.color = Tags.Dark.color
		self.name = "Hollow Flesh"
		self.asset = ['status', 'rot']
		if self.spell.get_stat('raise_zombie'):
			self.owner_triggers[EventOnDeath] = self.on_death

	def on_death(self, evt):
		zombie = Zombie()
		zombie.max_hp = self.owner.max_hp
		self.spell.summon(zombie, self.owner)

	def on_applied(self, owner):
		self.owner.resists[Tags.Dark] += 100
		self.owner.resists[Tags.Fire] -= self.spell.get_stat('fire_vulnerability')
		self.owner.resists[Tags.Holy] -= 100
		self.owner.resists[Tags.Heal] = 100

		frac = self.spell.get_stat('max_health_loss') / 100

		self.owner.max_hp -= math.floor(self.owner.max_hp * frac)
		self.owner.max_hp = max(self.owner.max_hp, 1)
		if self.owner.cur_hp > self.owner.max_hp:
			self.owner.cur_hp = self.owner.max_hp

		self.owner.tags.append(Tags.Undead) 
		if Tags.Living in self.owner.tags:
			self.owner.tags.remove(Tags.Living)

class HallowFlesh(Spell):

	def on_init(self):
		self.name = "Plague of Undeath"
		self.tags = [Tags.Dark, Tags.Enchantment]
		self.level = 2
		self.max_charges = 9
		self.range = 8

		self.holy_vulnerability = 100
		self.fire_vulnerability = 0
		self.max_health_loss = 25

		self.damage = 6

		self.upgrades['max_health_loss'] = (25, 2) 
		self.upgrades['fire_vulnerability'] = (50, 2, "Fire Vulnerability")
		self.upgrades['raise_zombie'] = (1, 4, "Plague of Undead", "Raise killed units as zombies.")

	def get_description(self):
		return ("Curse a group of [living] units with the essence of undeath.\n"
				"Affected units become [undead] and lose [living].\n"
				"Affected units lose [{max_health_loss}%:damage] of their max HP.\n"
				"Affected units then take [{damage}_poison:poison] damage.\n"
				"Affected units lose [100_holy:holy] resist.\n"
				"Affected units gain [100_dark:dark] resist.\n"
				"Affected units cannot be healed.").format(**self.fmt_dict())

	def get_impacted_tiles(self, x, y):

		return self.caster.level.get_connected_group_from_point(x, y, required_tags=[Tags.Living], check_hostile=True)

	def cast(self, x, y):
		points = self.get_impacted_tiles(x, y)

		for p in points:
			unit = self.caster.level.get_unit_at(p.x, p.y)
			if unit:
				unit.apply_buff(RotBuff(self))
				unit.deal_damage(self.get_stat('damage'), Tags.Poison, self)
				yield

	def get_ai_target(self):
		targets = [u for u in self.owner.level.units if self.can_cast(u.x, u.y)]
		targets = [u for u in targets if are_hostile(self.caster, u)]
		targets = [u for u in targets if Tags.Living in u.tags]

		if targets:
			return random.choice(targets)

class ConductanceBuff(Buff):
	
	def on_init(self):
		self.name = "Conductance"
		self.color = Tags.Lightning.color
		self.can_copy = True
		self.global_triggers[EventOnSpellCast] = self.on_spell_cast
		self.resists[Tags.Lightning] = -50
		self.buff_type = BUFF_TYPE_CURSE
		self.copies = 1
		self.asset = ['status', 'conductance']

	def on_spell_cast(self, evt):
		if not (evt.x == self.owner.x and evt.y == self.owner.y):
			return
		if not self.can_copy:
			return
		if not Tags.Lightning in evt.spell.tags:
			return
		
		self.can_copy = False
		for i in range(self.copies):
			if evt.spell.can_cast(evt.x, evt.y):
				evt.caster.level.act_cast(evt.caster, evt.spell, evt.x, evt.y, pay_costs=False)
		evt.caster.level.queue_spell(self.reset())

	def reset(self):
		self.can_copy = True
		yield

class ConductanceSpell(Spell):

	def on_init(self):
		self.name = "Conductance"
		self.tags = [Tags.Lightning, Tags.Enchantment]
		self.level = 4
		self.max_charges = 12

		self.resistance_debuff = 50

		self.duration = 10
		self.copies = 1
		self.upgrades['copies'] = (1, 2, "Multicopy", "Make 1 extra copy of lightning spells cast on the target")
		self.upgrades['resistance_debuff'] = (50, 2)
		self.upgrades['max_charges'] = (6, 2)

	def can_cast(self, x, y):
		return self.caster.level.get_unit_at(x, y) and Spell.can_cast(self, x, y)

	def cast_instant(self, x, y):
		unit = self.caster.level.get_unit_at(x, y)
		if unit:
			buff = ConductanceBuff()
			buff.copies = self.get_stat('copies')
			buff.resists[Tags.Lightning] = -self.get_stat('resistance_debuff')
			unit.apply_buff(buff, self.get_stat('duration'))

	def get_description(self):
		return ("Curse an enemy with the essence of conductivity.\n"
				"That enemy loses [50_lightning:lightning] resist.\n"
				"Whenever you cast a [lightning] spell targeting that enemy, copy that spell.\n"
				"Lasts [{duration}_turns:duration].").format(**self.fmt_dict())

class ShrapnelBlast(Spell):

	def on_init(self):
		self.name = "Shrapnel Blast"

		self.tags = [Tags.Fire, Tags.Metallic, Tags.Sorcery]
		self.level = 3
		self.max_charges = 6
		self.radius = 4
		self.range = 7
		self.damage = 12
		self.requires_los = False
		self.num_targets = 16

		self.upgrades['num_targets'] = (12, 6, "More Shrapnel", "12 more shrapnel shards are shot")
		self.upgrades['puncture'] = (1, 2, "Puncturing Blast", "The shrapnel can penetrate or destroy walls")
		self.upgrades['homing'] = (1, 7, "Magnetized Shards", "The shrapnel shards always target enemies if possible.")

	def get_description(self):
		return ("Detonate target wall tile.\n" 
				"Enemies adjacent to the wall tile take [{damage}_fire:fire] damage.\n"
				"The explosion fires [{num_targets}_shards:num_targets] at random tiles in a [{radius}_tile:radius] burst.\n"
				"Each shard deals [{damage}_physical:physical] damage.").format(**self.fmt_dict())


	def can_cast(self, x, y):
		return self.caster.level.tiles[x][y].is_wall() and Spell.can_cast(self, x, y)

	def cast(self, x, y):
		target = Point(x, y)
	
		damage = self.get_stat('damage')

		for stage in Burst(self.caster.level, target, 1):
			for point in stage:
				self.caster.level.deal_damage(point.x, point.y, damage, Tags.Fire, self)

			for i in range(2):
				yield

		for i in range(self.get_stat('num_targets')):
			possible_targets = list(self.caster.level.get_points_in_ball(x, y, self.get_stat('radius')))
			
			if not self.get_stat('puncture'):
				possible_targets = [t for t in possible_targets if self.caster.level.can_see(x, y, t.x, t.y, light_walls=True)]

			if self.get_stat('homing'):

				def can_home(t):
					u = self.caster.level.get_unit_at(t.x, t.y)
					if not u:
						return False
					return are_hostile(self.caster, u)

				enemy_targets = [t for t in possible_targets if can_home(t)]
				if enemy_targets:
					possible_targets = enemy_targets

			if possible_targets:
				target = random.choice(possible_targets)
				self.caster.level.deal_damage(target.x, target.y, damage, Tags.Physical, self)
				for i in range(2):
					yield

		self.caster.level.make_floor(x, y)
		return

	def get_impacted_tiles(self, x, y):
		fire_targets = [p for stage in Burst(self.caster.level, Point(x, y), 1) for p in stage]
		
		possible_targets = list(self.caster.level.get_points_in_ball(x, y, self.get_stat('radius')))
		if not self.get_stat('puncture'):
			possible_targets = [t for t in possible_targets if self.caster.level.can_see(x, y, t.x, t.y, light_walls=True)]

		return set(fire_targets + possible_targets)


class PlagueOfFilth(Spell):

	def on_init(self):

		self.tags = [Tags.Nature, Tags.Dark, Tags.Conjuration]
		self.name = "Plague of Filth"
		self.minion_health = 12
		self.minion_damage = 2
		self.minion_range = 4

		self.minion_duration = 7
		self.num_summons = 2
		self.radius = 2

		self.max_channel = 15

		self.level = 3
		self.max_charges = 5

		self.upgrades['num_summons'] = (2, 4)
		self.upgrades['minion_duration'] = (6, 2)
		self.upgrades['snakes'] = (1, 2, "Serpent Plague", "Plague of Filth has a 50% chance of summoning a snake instead of a fly swarm or frog.  Snakes have 3/4 the health of toads, deal 1 more damage.  Snakes apply 5 stacks of poison on hit.")

	def fmt_dict(self):
		d = Spell.fmt_dict(self)
		d['fly_health'] = d['minion_health'] // 2
		d['fly_damage'] = d['minion_damage'] // 2
		return d

	def get_description(self):
		return ("Summon a group of [{num_summons}:num_summons] toads and fly swarms.\n"
				"Toads have [{minion_health}_HP:minion_health].\n"
				"Toads have a ranged tongue attack which deals [{minion_damage}_physical:physical] damage and pulls enemies towards it.\n"
				"Toads can hop up to [4_tiles:range] away.\n"
				"Fly swarms have [{fly_health}_HP:minion_health], [75_dark:dark] resist, [75_physical:physical] resist, [-50_ice:ice] resist, and can fly.\n"
				"Fly swarms have a melee attack which deals [{fly_damage}_physical:physical] damage.\n"
				"The summons vanish after [{minion_duration}_turns:minion_duration].\n"
				"This spell can be channeled for up to [{max_channel}_turns:duration].").format(**self.fmt_dict())

	def cast(self, x, y, channel_cast=False):

		if not channel_cast:
			self.caster.apply_buff(ChannelBuff(self.cast, Point(x, y)), self.get_stat('max_channel'))
			return

		for i in range(self.get_stat('num_summons')):

			if self.get_stat('snakes') and random.random() < .5:
				unit = Snake()
				unit.max_hp = (self.get_stat('minion_health') * 3) // 4
				for s in unit.spells:
					if hasattr(s, 'damage'):
						s.damage = self.get_stat('minion_damage') + 1

			elif random.random() < .5:
				unit = HornedToad()
				unit.max_hp = self.get_stat('minion_health')
				for s in unit.spells:
					if hasattr(s, 'damage'):
						s.damage = self.get_stat('minion_damage')
			else:
				unit = FlyCloud()
				unit.max_hp = self.get_stat('minion_health') // 2
				for s in unit.spells:
					if hasattr(s, 'damage'):
						s.damage = self.get_stat('minion_damage') // 2
			
			unit.turns_to_death = self.get_stat('minion_duration')
			self.summon(unit, Point(x, y), radius=self.get_stat('radius'), sort_dist=False)
			yield

class SummonFieryTormentor(Spell):

	def on_init(self):
		self.name = "Fiery Tormentor"

		self.minion_health = 34
		self.minion_damage = 7
		self.minion_duration = 40
		self.minion_range = 2

		self.radius = 4

		self.max_charges = 7
		self.level = 4

		self.requires_los = False
		self.range = 8

		self.upgrades['frostfire'] = (1, 3, "Frostfire Tormentor", "Summons a frostfire tormentor instead.")
		self.upgrades['metallic'] = (1, 3, "Metallic Tormentor", "Summons a metallic fiery tormentor instead.")
		self.upgrades['mass'] = (1, 6, "Tormenting Mass", "Summons a Fiery Tormenting Mass instead.")

		self.tags = [Tags.Dark, Tags.Fire, Tags.Conjuration]

		self.must_target_walkable = True
		self.must_target_empty = True

	def fmt_dict(self):
		d = Spell.fmt_dict(self)
		d['minion_leech_damage'] = d['minion_damage'] - 5
		return d

	def get_description(self):
		return ("Summon a fiery tormentor.\n"
				"The tormentor has [{minion_health}_HP:minion_health].\n"
				"The tormentor has a burst attack dealing [{minion_damage}_fire:fire] damage with a [{radius}_tile:radius] radius.\n"
				"The tormentor has a lifesteal attack dealing [{minion_leech_damage}_dark:dark] damage with a [{minion_range}_tile:minion_range] range.\n"
				"The tormentor vanishes after [{minion_duration}_turns:minion_duration].").format(**self.fmt_dict())

	def get_impacted_tiles(self, x, y):
		for stage in Burst(self.caster.level, Point(x, y), self.get_stat('radius')):
			for p in stage:
				yield p

	def cast_instant(self, x, y):

		if self.get_stat('frostfire'):
			unit = FrostfireTormentor()
		elif self.get_stat('metallic'):
			unit = BossSpawns.Metallic(FieryTormentor())
		elif self.get_stat('mass'):
			unit = FieryTormentorMass()
		else:
			unit = FieryTormentor()

		apply_minion_bonuses(self, unit)
		unit.max_hp = self.get_stat('minion_health')

		for s in unit.spells:
			if hasattr(s, 'radius') and s.radius > 0:
				s.radius = self.get_stat('radius')

		unit.turns_to_death = self.get_stat('minion_duration')
		
		self.summon(unit, Point(x, y))

class DispersionFieldBuff(Buff):

	def __init__(self, spell):
		self.spell = spell
		Buff.__init__(self)

	def on_init(self):
		self.name = "Dispersion Field"
		self.description = "Teleport nearby enemies away each turn"

	def on_advance(self):
		tped = 0
		units = self.owner.level.get_units_in_ball(self.owner, self.spell.get_stat('radius'))
		random.shuffle(units)
		for u in units:
			if not are_hostile(self.owner, u):
				continue

			possible_points = []
			for i in range(len(self.owner.level.tiles)):
				for j in range(len(self.owner.level.tiles[i])):
					if self.owner.level.can_stand(i, j, u):
						possible_points.append(Point(i, j))

			if not possible_points:
				continue

			target_point = random.choice(possible_points)

			self.owner.level.show_effect(u.x, u.y, Tags.Translocation)
			self.owner.level.act_move(u, target_point.x, target_point.y, teleport=True)
			self.owner.level.show_effect(u.x, u.y, Tags.Translocation)

			tped += 1
			if tped > self.spell.get_stat('num_targets'):
				break

class DispersionFieldSpell(Spell):

	def on_init(self):
		self.name = "Dispersion Field"
		self.level = 4
		self.tags = [Tags.Enchantment, Tags.Arcane, Tags.Translocation]

		self.max_charges = 3
		self.duration = 7
		self.num_targets = 3

		self.range = 0
		self.radius = 6

		self.upgrades['num_targets'] = (2, 2)
		self.upgrades['duration'] = (5, 1)
		self.upgrades['max_charges'] = (5, 4)

	def get_description(self):
		return ("Each turn, teleport [{num_targets}_enemies:num_targets] in a [{radius}_tile:radius] radius to random locations on the map.\n"
				"Lasts [{duration}_turns:duration].").format(**self.fmt_dict())

	def cast_instant(self, x, y):
		self.caster.apply_buff(DispersionFieldBuff(self), self.get_stat('duration'))
		
class KnightBuff(Buff):

	def __init__(self, summoner):
		Buff.__init__(self)
		self.summoner = summoner

	def on_init(self):
		self.name = "Bound Knight"
		self.owner_triggers[EventOnDeath] = self.on_death

	def on_death(self, evt):
		self.summoner.deal_damage(40, Tags.Holy, self)

class SummonKnights(Spell):

	def on_init(self):
		self.name = "Knightly Oath"
		self.level = 6
		self.tags = [Tags.Conjuration, Tags.Holy]

		self.minion_health = 90

		self.max_charges = 2
		self.minion_damage = 7
		
		self.range = 0
		
		# Purely for shrine bonuses
		self.minion_range = 3

		self.upgrades['void_court'] = (1, 4, "Void Court", "Summon only void knights.  Summon a void champion as well.", "court")
		self.upgrades['storm_court'] = (1, 4, "Storm Court","Summon only storm knights.  Summon a storm champion as well.", "court")
		self.upgrades['chaos_court'] = (1, 4, "Chaos Court", "Summon only chaos knights.  Summon a chaos champion as well.", "court")

	def get_description(self):
		return ("Summon a void knight, a chaos knight, and a storm knight.\n"
				"Each knight has [{minion_health}_HP:minion_health], various resistances, and an arsenal of unique magical abilities.\n"
				"The caster takes [40_holy:holy] damage whenever a knight dies.").format(**self.fmt_dict())

	def cast(self, x, y):

		knights = [VoidKnight(), ChaosKnight(), StormKnight()]
		if self.get_stat('void_court'):
			knights = [VoidKnight(), VoidKnight(), VoidKnight(), Champion(VoidKnight())]
		if self.get_stat('storm_court'):
			knights = [StormKnight(), StormKnight(), StormKnight(), Champion(StormKnight())]
		if self.get_stat('chaos_court'):
			knights = [ChaosKnight(), ChaosKnight(), ChaosKnight(), Champion(ChaosKnight())]

		for u in knights:
			apply_minion_bonuses(self, u)
			u.buffs.append(KnightBuff(self.caster))
			self.summon(u)
			yield

class ToxinBurst(Spell):

	def on_init(self):

		self.name = "Toxin Burst"
		self.level = 2

		self.tags = [Tags.Sorcery, Tags.Nature, Tags.Dark]

		self.damage = 1
		self.radius = 4
		self.duration = 20
		self.requires_los = False
		self.range = 12

		self.damage_type = Tags.Poison

		self.max_charges = 10

		self.upgrades['chemical_remedy'] = (4, 1, "Herbal Remedy", "All allies in the radius are healed instead of damaged and poisoned.")
		self.upgrades['deal_dark'] = (1, 3, "Withertoxin", "Toxin Burst also deals [15_dark:dark] damage.")
		self.upgrades['summon_bomber'] = (1, 3, "Toxin Bomber", "Summons a Poison Bomber in the center of the burst that deals [15_poison:poison] damage.")

	def get_bomber(self):
		unit = PoisonBomber()
		unit.spells[0].range = self.radius
		unit.buffs[0].radius = self.radius

		unit.name = "Toxin Bomber"
		return unit

	def cast(self, x, y):
		points = list(self.caster.level.get_points_in_ball(x, y, self.get_stat('radius')))
		random.shuffle(points)
		for p in points:

			if self.get_stat('chemical_remedy'):
				unit = self.owner.level.get_unit_at(p.x, p.y)
				if unit and not are_hostile(self.caster, unit):
					unit.deal_damage(-self.get_stat('damage'), Tags.Heal, self)
					continue	

			self.caster.level.deal_damage(p.x, p.y, self.get_stat('damage'), Tags.Poison, self)
			if self.get_stat('deal_dark'):
				self.caster.level.deal_damage(p.x, p.y, self.get_stat('damage', base=15), Tags.Dark, self)
			
			unit = self.caster.level.get_unit_at(p.x, p.y)
			if unit:
				unit.apply_buff(Poison(), self.get_stat('duration'))

			if random.random() < .3:
				yield
		
		if self.get_stat('summon_bomber'):
			self.summon(self.get_bomber(), target=Point(x, y))

	def get_description(self):
		return ("Deal [{damage}_poison:poison] damage and inflict [poison] on all units in a [{radius}_tile:radius] radius for [{duration}_turns:duration].\n"
				+ text.poison_desc).format(**self.fmt_dict())

	def get_extra_examine_tooltips(self):
		return [self.spell_upgrades[0], self.spell_upgrades[1], self.spell_upgrades[2], self.get_bomber()]

class ToxicSpore(Spell):

	def on_init(self):
		self.name = "Toxic Spores"

		self.level = 2
		self.tags = [Tags.Conjuration, Tags.Nature]
		self.range = 8
		self.max_charges = 16	

		example = GreenMushboom()
		self.minion_health = example.max_hp
		self.minion_damage = example.spells[0].damage

		self.num_summons = 2
		self.minion_range = 2
		self.upgrades['num_summons'] = (2, 3)
		self.upgrades['grey_mushboom'] = (1, 2, "Grey Mushbooms", "Summon grey mushbooms instead, which apply stun instead of poison.", "color")
		self.upgrades['red_mushboom'] = (1, 5, "Red Mushbooms", "Summon red mushbooms instead, which do not apply poison but deal fire damage", "color")
		self.upgrades['glass_mushboom'] = (1, 6, "Glass Mushbooms", "Summon glass mushbooms instead, which apply glassify instead of poison", "color")


	def get_description(self):
		return ("Summons [{num_summons}:num_summons] Mushbooms.\n"
				"Mushbooms have [{minion_health}_HP:minion_health].\n"
				"Mushbooms have a ranged attack dealing [{minion_damage}_poison:poison] damage and inflicting [4_turns:duration] of [poison].\n"
				"Mushbooms inflict [12_turns:duration] of [poison] on units in melee range when they die.").format(**self.fmt_dict())

	def cast(self, x, y):
		for i in range(self.get_stat('num_summons')):
			mushboom = GreenMushboom()
			if self.get_stat('grey_mushboom'):
				mushboom = GreyMushboom()
			if self.get_stat('red_mushboom'):
				mushboom = RedMushboom()
			if self.get_stat('glass_mushboom'):
				mushboom = GlassMushboom()
			apply_minion_bonuses(self, mushboom)
			self.summon(mushboom, target=Point(x, y))
			yield

class AmplifyPoisonBuff(Buff):

	def __init__(self, spell):
		self.spell = spell
		Buff.__init__(self)

	def on_init(self):
		self.name = "Amplified Poison"
		self.asset = ['status', 'amplified_poison']
		self.stack_type = STACK_DURATION
		self.buff_type = BUFF_TYPE_CURSE
		self.color = Tags.Poison.color
		self.resists[Tags.Poison] = -self.spell.get_stat('resistance_debuff')

class AmplifyPoisonSpell(Spell):

	def on_init(self):
		self.name = "Amplify Venom"

		self.duration = 10
		self.tags = [Tags.Enchantment, Tags.Nature]
		self.level = 3

		self.range = 0

		self.max_charges = 8

		self.resistance_debuff = 100
		self.upgrades['resistance_debuff'] = (100, 3)
		self.upgrades['duration'] = (10, 1)
		self.upgrades['max_charges'] = (12, 2)
		self.upgrades['spread'] = (1, 2, "Spread Poison", "Amplify Poison spreads poison to nearby enemies (radius 2)")

	def get_description(self):
		return ("All [poisoned] enemies lose [100_poison:poison] resist for [{duration}_turns:duration].").format(**self.fmt_dict())

	def cast(self, x, y):

		units = [u for u in self.caster.level.units if are_hostile(u, self.caster) and u.has_buff(Poison)]
		random.shuffle(units)
		for u in units:
					
			# Unit died, or some crazy buff removed poison
			if not u.has_buff(Poison):
				continue

			if self.get_stat('spread'):
				for p in self.caster.level.get_points_in_ball(u.x, u.y, 2):
					unit = self.caster.level.get_unit_at(p.x, p.y)
					if unit and are_hostile(self.caster, unit):
						unit.apply_buff(Poison(), u.get_buff(Poison).turns_left)

			u.apply_buff(AmplifyPoisonBuff(self), self.get_stat('duration'))
			yield

class IgnitePoison(Spell):

	def on_init(self):
		self.name = "Combust Poison"
		self.level = 4
		self.tags = [Tags.Sorcery, Tags.Fire, Tags.Nature]		

		self.max_charges = 3

		self.multiplier = 1
		self.radius = 2

		self.stats.append('multiplier')

		self.upgrades['stun'] = (1, 3, "Paralyzing Combustion", "Stuns targets for 3 turns.")
		self.upgrades['healing'] = (1, 3, "Flame Rave", "Heal allies instead of hurt them.")
		self.upgrades['deal_poison'] = (1, 4, "Toxic Embers", "The explosion applies poison to damaged targets for one half of the [fire] damage taken.")

		self.range = 0

	def get_impacted_tiles(self, x, y):
		tiles = set()
		for u in self.owner.level.units:
			if not u.has_buff(Poison):
				continue
			if not are_hostile(u, self.caster):
				continue
			points = [p for stage in Burst(self.caster.level, u, self.get_stat('radius')) for p in stage]
			for p in points:
				tiles.add(p)
		return tiles

	def get_description(self):
		return ("Consume all [poison] on enemy units.\n"
				"Deal [fire] damage in an [{radius}_tile:radius] burst around each affected enemy equal to [{multiplier}x:damage] the amount of poison consumed.").format(**self.fmt_dict())		

	def burst(self, damage, u):
		damage_dealt = 0
		for stage in Burst(self.caster.level, u, self.get_stat('radius')):
			for point in stage:
				unit = self.caster.level.get_unit_at(point.x, point.y)
				if unit:
					if self.get_stat('stun'):
						unit.apply_buff(Stun(), 3)
					if are_hostile(self.caster, unit) or not self.get_stat('healing'):
						damage_dealt = self.caster.level.deal_damage(point.x, point.y, damage, Tags.Fire, self)
					elif self.get_stat('healing'):
						damage_dealt = 0
						self.caster.level.deal_damage(point.x, point.y, damage, Tags.Heal, self)
					if self.get_stat('deal_poison'):
						if damage_dealt >= 2:
							unit.apply_buff(Poison(), damage_dealt // 2)
				else:
					self.caster.level.deal_damage(point.x, point.y, damage, Tags.Fire, self)

	def cast(self, x, y):

		units = [u for u in self.caster.level.units if are_hostile(u, self.caster) and u.has_buff(Poison)]
		random.shuffle(units)
		
		bursts = []
		
		for u in units:
			# Unit died, or some crazy buff removed poison
			if not u.has_buff(Poison):
				continue

			buff = u.get_buff(Poison)
			damage = buff.turns_left * self.get_stat('multiplier')				
			
			u.remove_buff(buff)
			bursts.append([damage, u])
		
		for b in bursts:
			self.burst(b[0], b[1])
			yield

class VenomBeastThorns(Buff):

	def on_init(self):
		self.name = "Poison Skin"
		self.global_triggers[EventOnSpellCast] = self.on_spell
		self.description = "Poisons melee attackers for 5 turns"
		self.color = Tags.Poison.color

	def on_spell(self, evt):
		if evt.x != self.owner.x or evt.y != self.owner.y:
			return
		# Distance is implied to be 1 if its a leap or a melee
		if not (isinstance(evt.spell, LeapAttack) or evt.spell.melee):
			return
		self.owner.level.queue_spell(self.do_thorns(evt.caster))

	def do_thorns(self, unit):
		unit.apply_buff(Poison(), 5)
		yield

class VenomBeastHealing(Buff):

	def on_init(self):
		self.name = "Venom Drinker"
		self.description = "Heals whenever a unit takes poison damage"
		self.global_triggers[EventOnDamaged] = self.on_damage

	def on_damage(self, evt):
		if evt.damage_type != Tags.Poison:
			return
		self.owner.deal_damage(-evt.damage, Tags.Heal, self)

class VenomBeast(Spell):

	def on_init(self):
		self.name = "Venom Beast"

		self.level = 4
		self.tags = [Tags.Nature, Tags.Conjuration]
		self.minion_health = 70
		self.minion_damage = 12

		self.max_charges = 3

		self.upgrades['venom_skin'] = (1, 3, "Poison Skin", "The venom beast's skin poison's melee attackers for 5 turns.")
		self.upgrades['resists'] = (50, 2, "Resistances", "The venom beast gains resistance to fire and lightning damage.")
		self.upgrades['minion_health'] = (30, 3)
		self.upgrades['trample'] = (1, 2, "Trample Attack", "The venom beast gains a trample attack on a 2 turn cooldown.")

		self.must_target_walkable = True
		self.must_target_empty = True

	def get_description(self):
		return ("Summon a venom best.\n"
				"The venom beast has [{minion_health}_HP:minion_health], and heals whenever any unit takes poison damage.\n"
				"The venom beast has a melee attack which deals [{minion_damage}_physical:physical] damage and inflicts [5_turns:duration] of [poison].").format(**self.fmt_dict())

	def cast_instant(self, x, y):
		beast = Unit()
		beast.name = "Venom Beast"
		beast.resists[Tags.Poison] = 100
		beast.tags = [Tags.Living, Tags.Poison, Tags.Nature]

		if self.get_stat('trample'):
			trample = SimpleMeleeAttack(damage=self.get_stat('minion_damage'), trample=True)
			trample.cool_down = 2
			trample.name = "Trample"
			beast.spells.append(trample)

		bite = SimpleMeleeAttack(damage=self.get_stat('minion_damage'), buff=Poison, buff_duration=5)
		bite.name = "Poison Bite"
		beast.spells.append(bite)

		beast.buffs = [VenomBeastHealing()]

		if self.get_stat('venom_skin'):
			beast.buffs.append(VenomBeastThorns())

		beast.max_hp = self.get_stat('minion_health')

		beast.resists[Tags.Fire] = self.get_stat('resists')
		beast.resists[Tags.Lightning] = self.get_stat('resists')

		self.summon(beast, target=Point(x, y))

class SummonSpiderQueen(Spell):

	def on_init(self):
		self.name = "Spider Queen"
		self.tags = [Tags.Nature, Tags.Conjuration]

		self.max_charges = 2
		self.level = 5

		self.upgrades["aether"] = (1, 3, "Aether Queen", "Summon an aether spider queen instead.", "species")
		self.upgrades["steel"] = (1, 3, "Steel Queen", "Summon a steel spider queen instead.", "species")
		self.upgrades['vampire'] = (1, 7, "Vampire Queen", "The Spider Queen and its babies can cast your Life Drain on a 4 turn cooldown.")

		self.must_target_walkable = True
		self.must_target_empty = True

		self.minion_damage = GiantSpider().spells[0].damage
		self.minion_health = 10

		self.num_summons = 4


	def fmt_dict(self):
		d = Spell.fmt_dict(self)
		d['queen_hp'] = 96 + self.get_stat('minion_health', base=0)
		d['spider_hp'] = 14 + self.get_stat('minion_health', base=0)
		return d

	def get_description(self):
		return ("Summon a spider queen.\n"
				"The spider queen has [{queen_hp}_HP:minion_health].\n"
				"The spider queen hatches [{num_summons}:num_summons] baby spiders every [12_turns:duration].\n"
				"Baby spiders have [3_HP:minion_health] and prefer to flee than attack, but they mature into giant spiders after [8_turns:duration] which have [{spider_hp}_HP:minion_health].\n"
				"Giant spiders and the spider queen have melee attacks which deal [{minion_damage}_physical:physical] physical damage and inflicts 10 turns of [poison].").format(**self.fmt_dict())

	def spawn_with_bonuses(self, base_spawner):
		unit = base_spawner()
		if self.get_stat('vampire'):
			grant_minion_spell(BloodTapSpell, unit, self.caster, cool_down=4)
		apply_minion_bonuses(self, unit)
		return unit

	def cast_instant(self, x, y):

		spawner = GiantSpider

		if self.get_stat('aether'):
			spawner = PhaseSpider
		if self.get_stat('steel'):
			spawner = SteelSpider

		unit = spawner()
		unit.max_hp = 96
		apply_minion_bonuses(self, unit)

		unit.name = "%s Queen" % unit.name
		unit.asset_name += '_mother'

		def babyspider():
			unit = spawner()
			unit.max_hp = 3
			apply_minion_bonuses(self, unit)
			unit.name = "Baby %s" % unit.name
			unit.asset_name += '_child'
			
			if self.get_stat('vampire'):
				#put the granting spell before the damage-setting since it's a baby, lmk if you want me to move it to after
				grant_minion_spell(BloodTapSpell, unit, self.caster, cool_down=4)
			
			for s in unit.spells:
				if hasattr(s, 'damage'):
					s.damage = 1

			unit.is_coward = True
			unit.buffs = [b for b in unit.buffs if not isinstance(b, SpiderBuff)]
			unit.buffs.append(MatureInto(lambda: self.spawn_with_bonuses(spawner), 8))
			unit.source = self
			return unit

		unit.spells.insert(0, SimpleSummon(babyspider, num_summons=self.get_stat('num_summons'), cool_down=12))
		if self.get_stat('vampire'):
			grant_minion_spell(BloodTapSpell, unit, self.caster, cool_down=4)

		self.summon(unit, target=Point(x, y))

class RefreezeBuff(Buff):

	def on_init(self):
		self.name = "Refreezing"
		self.color = Tags.Ice.color
		self.buff_type = BUFF_TYPE_CURSE

	def on_advance(self):
		self.has_buff = False
		if self.owner.get_buff(FrozenBuff):
			buff = self.owner.get_buff(FrozenBuff)
			buff.turns_left += 1
		else:
			self.owner.apply_buff(FrozenBuff(), 1)

class Freeze(Spell):

	def on_init(self):
		self.tags = [Tags.Enchantment, Tags.Ice]
		self.level = 2
		self.name = "Freeze"
	
		self.duration = 5
		
		self.max_charges = 20

		self.range = 8

		self.upgrades['refreezing'] = (1, 4, "Refreezing", "The target is refrozen every turn for the duration.")
		self.upgrades['freeze_group'] = (1, 4, "Mass Freeze", "Freeze a connected group.")
		self.upgrades['quick_cast'] = (1, 2, "Quickcast", "Casting freeze does not end your turn")

	def get_impacted_tiles(self, x, y):
		tiles = [Point(x, y)]
		if self.get_stat('freeze_group'):
			tiles = self.caster.level.get_connected_group_from_point(x, y, ignored_units=[self.caster])

		return tiles

	def can_cast(self, x, y):
		return self.caster.level.get_unit_at(x, y) and Spell.can_cast(self, x, y)

	def cast(self, x, y):
		targets = [self.caster.level.get_unit_at(x, y)]
		if self.get_stat('freeze_group'):
			targets = self.caster.level.get_connected_group_from_point(x, y, ignored_units=[self.caster]) #Currently it's going to freeze allies (including the player) as well, let me know if you want this to change

		for target in targets:
			if target:
				target.apply_buff(FrozenBuff(), self.get_stat('duration')-self.get_stat('refreezing')) #subtracting refreezing because that adds a stack due to the logic
				if self.get_stat('refreezing'):
					target.apply_buff(RefreezeBuff(), self.get_stat('duration'))
				self.owner.level.show_beam(self.caster, target, Tags.Ice, minor=True, inclusive=False)
			yield
		yield #2 yields just in case no targets

	def get_description(self):
		return ("Target unit is [frozen] for [{duration}_turns:duration].\n"
			    + text.frozen_desc).format(**self.fmt_dict())

class Iceball(Spell):

	def on_init(self):
		self.tags = [Tags.Sorcery, Tags.Ice]
		self.level = 2
		self.name = "Iceball"

		self.damage = 14
		self.duration = 3
		self.radius = 2

		self.range = 7

		self.max_charges = 8

		self.upgrades['cloud_combustion'] = (1, 3, "Cloud Combustion", "Gains +2 radius and x2 damage if cast on a Blizzard tile. The Blizzard tile is consumed.")
		self.upgrades['icecrush'] = (1, 4, "Ice Crush", "Units inside of the area of effect which are already frozen take physical damage before being refrozen.")
		self.upgrades['summon_faery'] = (4, 4, "Fae Ball", "Whenever you cast Iceball, summon 1 ice faery for every 4 enemies it freezes.")


	def get_description(self):
		return ("Deals [{damage}_ice:ice] damage in a [{radius}_tile:radius] burst.\n"
				"Affected units in the area are [frozen] for [{duration}_turns:duration].").format(**self.fmt_dict())

	def cast(self, x, y):
		target = Point(x, y)

		enemies_frozen = 0

		bonus_radius = 0
		damage_multiplier = 1
		c = self.caster.level.tiles[x][y].cloud
		if c and (type(c) == BlizzardCloud) and self.get_stat('cloud_combustion'):
			bonus_radius = 2
			damage_multiplier = 2
			c.kill()

		for stage in Burst(self.caster.level, target, self.get_stat('radius') + bonus_radius):
			for point in stage:
				unit = self.caster.level.get_unit_at(point.x, point.y)
				damage = self.get_stat('damage')*damage_multiplier

				if self.get_stat('icecrush'):
					if unit and unit.has_buff(FrozenBuff):
						unit.deal_damage(damage, Tags.Physical, self)

				self.caster.level.deal_damage(point.x, point.y, damage, Tags.Ice, self)

				if unit:
					frozen_debuff = FrozenBuff()
					unit.apply_buff(frozen_debuff, self.get_stat('duration'))
					if frozen_debuff in unit.buffs and self.get_stat('summon_faery'):
						enemies_frozen += 1
						if enemies_frozen == 4:
							enemies_frozen = 0
							ice_faery = FairyIce()
							self.summon(ice_faery, Point(x, y))
			for i in range(3):
				yield

		return

	def get_impacted_tiles(self, x, y):
		return [p for stage in Burst(self.caster.level, Point(x, y), self.get_stat('radius')) for p in stage]

class IcePhoenixRecharge(Upgrade):

	def on_init(self):
		self.name = "Snow Feathers"
		self.description = "Every 150 damage, return a charge of your Ice Phoenix spell."
		self.owner_triggers[EventOnUnitAdded] = self.on_unit_added
		self.global_triggers[EventOnDamaged] = self.on_damage
		self.level = 4
		self.damage_dealt = 0

	def on_unit_added(self, evt):
		self.damage_dealt = 0

	def on_damage(self, evt):
		if isinstance(evt.source, BlizzardSpell):
			self.damage_dealt += evt.damage
			while self.damage_dealt >= 150:
				self.damage_dealt -= 150
				for s in self.owner.spells:
					if isinstance(s, SummonIcePhoenix):
						s.cur_charges += 1
						s.cur_charges = min(s.cur_charges, s.max_charges)

class BlizzardSpell(Spell):

	def on_init(self):

		self.name = "Blizzard"

		self.tags = [Tags.Enchantment, Tags.Ice, Tags.Nature]
		self.level = 4
		self.max_charges = 4

		self.range = 9
		self.radius = 4

		self.damage = 5
		self.duration = 5

		self.upgrades['freezing'] = (1, 3, "Flash Freeze", "Freeze all units in affected tiles for 2 turns.")
		self.add_upgrade(IcePhoenixRecharge())
		self.upgrades['cast_icicle'] = (1, 4, "Hailstorm", "Each Blizzard has a 25% chance to cast your Icicle spell each turn.")

	def get_description(self):
		return ("Create a blizzard with a [{radius}_tile:radius] radius.\n" +
				"Each turn, units in the blizzard take [{damage}_ice:ice] damage, and have a 50% chance to be [frozen].\n" +
				text.frozen_desc +
				"The blizzard lasts [{duration}_turns:duration].").format(**self.fmt_dict())

	def cast(self, x, y):

		for stage in Burst(self.caster.level, Point(x, y), self.get_stat('radius')):
			for p in stage:

				if self.get_stat('stormshaping'):
					unit = self.owner.level.get_unit_at(p.x, p.y)
					if unit and not are_hostile(unit, self.caster):
						continue

				unit = self.caster.level.get_unit_at(p.x, p.y)
				if unit and self.get_stat('freezing'):
					unit.apply_buff(FrozenBuff(), 2)

				cloud = BlizzardCloud(self.caster)
				cloud.duration = self.get_stat('duration')
				cloud.damage = self.get_stat('damage')
				cloud.source = self
				if self.get_stat('cast_icicle'):
					cloud.spellcast = Icicle

				yield self.caster.level.add_obj(cloud, p.x, p.y)

	def get_impacted_tiles(self, x, y):
		return [p for stage in Burst(self.caster.level, Point(x, y), self.get_stat('radius')) for p in stage]

class HydraReclamationUpgrade(Upgrade):

	def on_init(self):
		self.name = "Hydra Reclamation"
		self.description = "Whenever a Frostfire Hydra expires, regain a charge of Frostfire Hydra."
		self.global_triggers[EventOnDeath] = self.on_death
		self.level = 2

	def on_death(self, evt):
		if evt.unit.source == self.owner.get_spell(SummonFrostfireHydra) and evt.unit.turns_to_death == 0:
			self.owner.get_spell(SummonFrostfireHydra).cur_charges = min(self.owner.get_spell(SummonFrostfireHydra).cur_charges+1, self.owner.get_spell(SummonFrostfireHydra).max_charges)

class CrystalEyesBuff(Buff):

	def on_init(self):
		self.name = "Crystal Eyes"
		self.description = "Deal additional 50% Arcane damage"
		self.color = Tags.Arcane.color
		self.global_triggers[EventOnDamaged] = self.on_damaged

	def on_damaged(self, evt):
		if evt.source.owner == self.owner and evt.source != self:
			self.owner.level.deal_damage(evt.unit.x, evt.unit.y, evt.damage//2, Tags.Arcane, self)

class SummonFrostfireHydra(Spell):

	def on_init(self):
		self.name = "Frostfire Hydra"
		
		self.tags = [Tags.Ice, Tags.Fire, Tags.Dragon, Tags.Conjuration]
		self.level = 3
		self.max_charges = 7

		self.minion_range = 9
		self.minion_damage = 7
		self.minion_health = 16
		self.minion_duration = 15

		self.add_upgrade(HydraReclamationUpgrade())
		self.upgrades['crystal_eyes'] = (1, 4, "Crystal Eyes Hydra", "50% of damage dealt by Frostfire Hydra is redealt as Arcane damage.")
		self.upgrades['freezing'] = (1, 6, "Freezing Ice", "Frostfire Hydra's Ice beam freezes units for 2 turns.")

		self.must_target_walkable = True
		self.must_target_empty = True

	def get_description(self):
		return ("Summon a frostfire hydra.\n"
				"The hydra has [{minion_health}_HP:minion_health], and is stationary.\n"
				"The hydra has a beam attack which deals [{minion_damage}_fire:fire] damage with a [{minion_range}_tile:minion_range] range.\n"
				"The hydra has a beam attack which deals [{minion_damage}_ice:ice] damage with a [{minion_range}_tile:minion_range] range.\n"
				"The hydra vanishes after [{minion_duration}_turns:minion_duration].").format(**self.fmt_dict())

	def cast_instant(self, x, y):

		unit = Unit()
		unit.max_hp = self.get_stat('minion_health')

		unit.name = "Frostfire Hydra"
		unit.asset_name = 'fire_and_ice_hydra'

		fire = SimpleRangedAttack(damage=self.get_stat('minion_damage'), range=self.get_stat('minion_range'), damage_type=Tags.Fire, beam=True)
		fire.name = "Fire"
		fire.cool_down = 2

		ice = SimpleRangedAttack(damage=self.get_stat('minion_damage'), range=self.get_stat('minion_range'), damage_type=Tags.Ice, beam=True)
		ice.name = "Ice"
		ice.cool_down = 2
		if self.get_stat('freezing'):
			ice.buff = FrozenBuff
			ice.buff_duration = 2

		unit.stationary = True
		unit.spells = [ice, fire]

		unit.resists[Tags.Fire] = 100
		unit.resists[Tags.Ice] = 100

		unit.turns_to_death = self.get_stat('minion_duration')

		unit.tags = [Tags.Fire, Tags.Ice, Tags.Dragon]
		if self.get_stat('crystal_eyes'):
			unit.name = "Crystal Eyes Frostfire Hydra"
			unit.asset_name = "fire_and_ice_hydra_crystal_eyes"
			unit.apply_buff(CrystalEyesBuff())
			unit.tags.append(Tags.Arcane) #If this is too much I can axe it

		self.summon(unit, Point(x, y))

class StormNova(Spell):

	def on_init(self):
		self.name = "Storm Burst"
		self.level = 4
		self.tags = [Tags.Ice, Tags.Lightning, Tags.Sorcery]

		self.max_charges = 4

		self.damage = 20
		self.duration = 4
		self.radius = 8
		self.range = 0

		self.upgrades['grants_immunity'] = (100, 2, "Stormshield", "Allies in radius are not affected, and instead gain [ice:ice] and [lightning:lightning] immunity for [4_turns:duration].")
		self.upgrades['dual_burst'] = (1, 4, "Dual Nova", "Enemies take both lightning and ice damage instead of just one, and are both frozen and stunned.")
		self.upgrades['summon_threshold'] = (40, 5, "Spirit Nova", "Summons a Storm Spirit for every 40 damage dealt")

	def get_description(self):
		return ("Unleashes a [{radius}_tile:radius] burst of storm energy.\n"
				"Each tile in the burst takes either [{damage}_ice:ice] damage or [{damage}_lightning:lightning] damage.\n"
				"Units dealt ice damage are [frozen] for [{duration}_turns:duration].\n"
				"Units dealt lightning damage are [stunned] for [{duration}_turns:duration].").format(**self.fmt_dict())

	def cast(self, x, y):
		dmg_dealt = 0
		for stage in Burst(self.caster.level, self.caster, self.get_stat('radius')):
			for p in stage:
				if (p.x, p.y) == (self.caster.x, self.caster.y):
					continue
				dtype = random.choice([Tags.Ice, Tags.Lightning])

				
				unit = self.caster.level.get_unit_at(p.x, p.y)
				if unit:
					if not self.get_stat('grants_immunity') or (self.get_stat('grants_immunity') and are_hostile(self.caster, unit)):

						if dtype == Tags.Ice or self.get_stat('dual_burst'):
							unit.apply_buff(FrozenBuff(), self.get_stat('duration'))
							dmg_dealt += self.caster.level.deal_damage(p.x, p.y, self.get_stat('damage'), Tags.Ice, self)

						if dtype == Tags.Lightning or self.get_stat('dual_burst'):
							unit.apply_buff(Stun(), self.get_stat('duration'))
							dmg_dealt += self.caster.level.deal_damage(p.x, p.y, self.get_stat('damage'), Tags.Lightning, self)

					elif self.get_stat('grants_immunity') and not are_hostile(self.caster, unit):

						buff = Buff()
						buff.resists[Tags.Ice] = self.get_stat('grants_immunity')
						buff.color = Tags.Ice.color
						buff.name = "Ice Immunity"
						unit.apply_buff(buff, self.get_stat('duration'))

						buff = Buff()
						buff.resists[Tags.Lightning] = self.get_stat('grants_immunity')
						buff.color = Tags.Lightning.color
						buff.name = "Lightning Immunity"
						unit.apply_buff(buff, self.get_stat('duration'))
				else:
					self.caster.level.show_effect(p.x, p.y, dtype)

				if self.get_stat('summon_threshold'):
					while dmg_dealt >= self.get_stat('summon_threshold'):
						self.summon(StormSpirit(), self.caster)
						dmg_dealt -= self.get_stat('summon_threshold')
				
				if self.get_stat('clouds'):
					if dtype == Tags.Ice:
						cloud = BlizzardCloud(self.caster)
					if dtype == Tags.Lightning:
						cloud = StormCloud(self.caster)
					self.caster.level.add_obj(cloud, p.x, p.y)

			yield

	def get_impacted_tiles(self, x, y):
		return [p for stage in Burst(self.caster.level, Point(x, y), self.get_stat('radius')) for p in stage]

class DeathChillDebuff(Buff):

	def __init__(self, spell):
		self.spell = spell
		Buff.__init__(self)

	def on_init(self):
		self.name = "Death Chill"
		self.color = Tags.Dark.color
		self.buff_type = BUFF_TYPE_CURSE
		self.owner_triggers[EventOnDeath] = self.on_death
		self.asset = ['status', 'deathchill']

	def on_advance(self):
		self.owner.deal_damage(self.spell.get_stat('damage'), Tags.Dark, self.spell)
		if self.spell.get_stat('deal_poison'):
			self.owner.deal_damage(self.spell.get_stat('damage'), Tags.Poison, self.spell)

	def on_death(self, evt):
		self.owner.level.queue_spell(self.burst())

		if self.spell.get_stat('raise_skeleton'):
			skeleton = raise_skeleton(self.spell.caster, self.owner, source=self.spell)
			if skeleton:
				BossSpawns.apply_modifier(BossSpawns.Icy, skeleton)	
				apply_minion_bonuses(self.spell, skeleton)

	def burst(self):
		for unit in self.owner.level.get_units_in_ball(self.owner, self.spell.get_stat('radius')):
			if are_hostile(self.spell.owner, unit):

				for p in self.owner.level.get_points_in_line(self.owner, unit)[1:-1]:
					self.owner.level.show_effect(p.x, p.y, Tags.Ice, minor=True)
				
				damage = unit.deal_damage(self.spell.get_stat('damage'), Tags.Ice, self.spell)
				if damage:
					unit.apply_buff(FrozenBuff(), self.spell.get_stat('duration'))
				yield

class DeathChill(Spell):

	def on_init(self):

		self.name = "Death Chill"
		
		self.level = 3
		self.tags = [Tags.Enchantment, Tags.Dark, Tags.Ice]

		self.duration = 5
		self.radius = 3
		self.damage = 11

		self.range = 9

		self.max_charges = 12

		self.can_target_empty = False

		self.upgrades['raise_skeleton'] = (1, 3, "Icy Necromancy", "Raise slain [living] units as Icy Skeletons.")
		self.upgrades['deal_poison'] = (1, 3, "Slaughter Chill", "Also deals poison damage to main target.")
		self.upgrades['mass_deathchill'] = (1, 6, "Mass Death Chill", "Applies Death Chill to a connected group of enemies.")

	def get_impacted_tiles(self, x, y):
		tiles = [Point(x, y)]
		if self.get_stat('mass_deathchill'):
			tiles = self.caster.level.get_connected_group_from_point(x, y, ignored_units=[self.caster])
		return tiles

	def get_description(self):
		return ("Deal [{damage}_dark:dark] damage to the target each turn for [{duration}_turns:duration].\n"
				"If the target dies during this time, deals [{damage}_ice:ice] damage and inflicts [frozen] for [{duration}_turns:duration] on all enemies within a [{radius}_tiles:radius] radius.\n"
				+ text.frozen_desc).format(**self.fmt_dict())

	def cast_instant(self, x, y):
		targets = [self.caster.level.get_unit_at(x, y)]
		if self.get_stat('mass_deathchill'):
			targets = self.caster.level.get_connected_group_from_point(x, y, ignored_units=[self.caster]) #Currently it's going to apply death chill to allies as well, let me know if you want this to change

		for target in targets:
			if target:
				target.apply_buff(DeathChillDebuff(self), self.get_stat('duration'))

class IcePhoenixBuff(Buff):
	
	def __init__(self, radius):
		Buff.__init__(self)
		self.radius = radius

	def on_init(self):
		self.color = Tags.Ice.color
		self.owner_triggers[EventOnDeath] = self.on_death
		self.name = "Phoenix Freeze"

	def get_tooltip(self):
		return "On death, create an icy blast which freezes for 4 turns and deals 25 ice damage to enemies and applies 2 shields to allies."

	def on_death(self, evt):
		for p in self.owner.level.get_points_in_ball(self.owner.x, self.owner.y, self.radius):
			unit = self.owner.level.get_unit_at(*p)
			if unit and not are_hostile(unit, self.owner):
				unit.add_shields(2)
			else:
				self.owner.level.deal_damage(p.x, p.y, 25, Tags.Ice, self)
				u = self.owner.level.get_unit_at(p.x, p.y)
				if u:
					u.apply_buff(FrozenBuff(), 4)

class SummonIcePhoenix(Spell):

	def on_init(self):
		self.name = "Ice Phoenix"
		self.level = 5
		self.max_charges = 3
		self.tags = [Tags.Conjuration, Tags.Ice, Tags.Holy]

		self.minion_health = 74
		self.minion_damage = 9
		self.minion_range = 4
		self.lives = 1

		self.radius = 6

		self.upgrades['lives'] = (2, 3, "Reincarnations", "The phoenix will reincarnate 2 more times")
		self.upgrades['ice_aura'] = (1, 4, "Ice Aura", "The phoenix gains 2 damage ice aura with a 6 tile radius")
		self.upgrades['heal_aura'] = (1, 3, "Heal Aura", "The phoenix gains a 1 hp regen aura with a 6 tile radius")

		self.must_target_empty = True

	def get_description(self):
		return ("Summon an ice phoenix.\n"
				"The phoenix has [{minion_health}_HP:minion_health], flies, and reincarnates once upon death.\n"
				"The phoenix has a ranged attack which deals [{minion_damage}_ice:ice] damage with a [{minion_range}_tile:minion_range] range.\n"
				"When the phoenix dies, it explodes in a [{radius}_tile:radius] burst, freezing enemies for 4 turns and dealing them [25_ice:ice] damage, and granting [2_SH:shields] to allies."
			).format(**self.fmt_dict())

	def cast_instant(self, x, y):
		phoenix = Unit()
		phoenix.max_hp = self.get_stat('minion_health')
		phoenix.name = "Ice Phoenix"

		phoenix.tags = [Tags.Ice, Tags.Holy]

		phoenix.sprite.char = 'P'
		phoenix.sprite.color = Tags.Ice.color

		phoenix.buffs.append(IcePhoenixBuff(self.get_stat('radius')))
		phoenix.buffs.append(ReincarnationBuff(self.get_stat('lives')))

		if self.get_stat('ice_aura'):
			phoenix.buffs.append(DamageAuraBuff(damage=2, damage_type=Tags.Ice, radius=self.get_stat('radius')))
		if self.get_stat('heal_aura'):
			phoenix.buffs.append(HealAuraBuff(heal=1, radius=self.get_stat('radius')))

		phoenix.flying = True

		phoenix.resists[Tags.Ice] = 100
		phoenix.resists[Tags.Dark] = -50

		phoenix.spells.append(SimpleRangedAttack(damage=self.get_stat('minion_damage'), range=self.get_stat('minion_range'), damage_type=Tags.Ice))
		self.summon(phoenix, target=Point(x, y))

class WordOfIce(Spell):

	def on_init(self):
		self.name = "Word of Ice"
		self.level = 7
		self.tags = [Tags.Ice, Tags.Word]
		self.max_charges = 1
		self.duration = 5
		self.damage = 50
		self.range = 0

		self.upgrades['echo'] = (1, 5, "Echoing Ice", "Auto recast in 10 turns.")
		self.upgrades['endless_ice'] = (1, 5, "Endless Ice", "Gain a charge of all other ice spells on cast.")
		self.upgrades['word_of_wind'] = (1, 7, "Word of Wind", "Casts your Chill Wind on up to [3:num_targets] enemies.")

	def cast(self, x, y, is_echo=False):
		if self.get_stat('echo') and not is_echo:
			self.caster.apply_buff(EchoCast(self), 10)
		
		if self.get_stat('endless_ice'):
			eligible_spells = [s for s in self.caster.spells if Tags.Ice in s.tags and s != self]
			for s in eligible_spells:
				s.cur_charges = min(s.cur_charges + 1, s.get_stat('max_charges'))
		
		if self.get_stat('word_of_wind'):
			eligible_targets = [u for u in self.caster.level.units if are_hostile(self.caster, u)]
			if eligible_targets:
				random.shuffle(eligible_targets)
				for i in range(min(self.get_stat('num_targets', base=3), len(eligible_targets))):
					chill_wind = self.caster.get_or_make_spell(IceWind)
					for _ in self.caster.level.act_cast(self.caster, chill_wind, eligible_targets[i].x, eligible_targets[i].y,  pay_costs=False, queue=False):
						pass #passing for animation speed, lmk if you want to yield instead
		
		units = [u for u in self.caster.level.units if are_hostile(u, self.caster)]
		random.shuffle(units)
		for u in units:
			u.apply_buff(FrozenBuff(), self.get_stat('duration'))
			if Tags.Fire in u.tags:
				u.deal_damage(self.get_stat('damage'), Tags.Ice, self)
			if random.random() < .3:
				yield

	def get_impacted_tiles(self, x, y):
		return [u for u in self.caster.level.units if are_hostile(u, self.caster) and (u.resists[Tags.Ice] < 100 or Tags.Fire in u.tags)]

	def get_description(self):
		return ("All non [ice] immune enemies are [frozen] for [{duration}_turns:duration].\n"
				"Deals [{damage}_ice:ice] damage to all fire units.").format(**self.fmt_dict())

class IceWeave(Spell):

	def on_init(self):
		self.name = "Ice Weave"
		self.level = 3
		self.tags = [Tags.Enchantment, Tags.Ice]
		self.max_charges = 4
		self.range = 0

		self.duration = 4

		self.upgrades['duration'] = (2, 3)
		self.upgrades['max_charges'] = (4, 3)

	def get_description(self):
		return ("All [frozen] enemies are [frozen] for an additional [{duration}_turns:duration].").format(**self.fmt_dict())

	def cast_instant(self, x, y):
		for u in self.caster.level.units:
			if not are_hostile(self.caster, u):
				continue

			buff = u.get_buff(FrozenBuff)
			if not buff:
				continue

			buff.turns_left += 4
			u.deal_damage(0, Tags.Ice, self)

class IcicleHarvest(Upgrade):

	def on_init(self):
		self.name = "Icicle Harvest"
		self.description = "Whenever a frozen enemy dies to [ice] damage, regain a charge of Icicle."
		self.global_triggers[EventOnDeath] = self.on_death
		self.level = 2

	def on_death(self, evt):
		if not are_hostile(self.owner, evt.unit):
			return

		if not evt.unit.has_buff(FrozenBuff):
			return

		if self.prereq.cur_charges >= self.prereq.get_stat('max_charges'):
			return

		if not evt.damage_event or evt.damage_event.damage_type != Tags.Ice:
			return

		self.prereq.cur_charges += 1

class Icicle(Spell):

	def on_init(self):

		self.name = "Icicle"

		self.tags = [Tags.Ice, Tags.Sorcery]

		self.radius = 1
		self.damage = 6
		self.level = 1

		self.range = 9

		self.max_charges = 22

		self.upgrades['freezing'] = (1, 2, "Freezing", "Freeze the main target for 2 turns")
		self.upgrades['ice_spear'] = (1, 2, "Ice Spear", "Deals physical damage to all units in a beam to the main target")
		self.add_upgrade(IcicleHarvest())

	def get_description(self):
		return ("Deal [{damage}_physical:physical] damage to the target.\n"
				"Then, deal [{damage}_ice:ice] to the target and a [{radius}_tile:radius] area around it.\n"
				"If cast on a chasm tile, creates a floor tile.").format(**self.fmt_dict())

	def cast(self, x, y):

		if self.get_stat('ice_spear'):
			for p in self.caster.level.get_points_in_line(self.caster, Point(x, y), find_clear=True)[1:-1]:
				self.caster.level.projectile_effect(p.x, p.y, proj_name='ice_bolt', proj_origin=self.caster, proj_dest=Point(x, y))
				yield

				u = self.caster.level.get_unit_at(p.x, p.y)
				if u:
					u.deal_damage(self.get_stat('damage'), Tags.Physical, self)

		else:
			for p in self.caster.level.get_points_in_line(self.caster, Point(x, y), find_clear=True)[1:-1]:
				self.caster.level.show_effect(p.x, p.y, Tags.Physical, minor=True)

		self.caster.level.deal_damage(x, y, self.get_stat('damage'), Tags.Physical, self)
		unit = self.caster.level.get_unit_at(x, y)

		if unit and self.get_stat('freezing'):
			unit.apply_buff(FrozenBuff(), 2 + self.get_stat('duration'))

		yield

		for stage in Burst(self.caster.level, Point(x, y), self.get_stat('radius')):
			for p in stage:
				self.caster.level.deal_damage(p.x, p.y, self.get_stat('damage'), Tags.Ice, self)
			yield

		if self.owner.level.tiles[x][y].is_chasm:
			self.owner.level.make_floor(x, y)

	def get_impacted_tiles(self, x, y):

		points = [p for stage in Burst(self.caster.level, Point(x, y), self.get_stat('radius')) for p in stage]
		if self.get_stat('ice_spear'):
			beam = [p for p in self.caster.level.get_points_in_line(self.caster, Point(x, y))[1:-1]]
			points.extend(beam)

		return points

class IceWind(Spell):

	def on_init(self):
		self.name = "Chill Wind"

		self.level = 5
		self.tags = [Tags.Ice, Tags.Sorcery]

		self.max_charges = 2

		self.damage = 21
		self.duration = 6

		self.range = RANGE_GLOBAL
		self.requires_los = False

		self.damage_dealt = 0

		self.upgrades['refresh_conjuration'] = (1, 3, "Ice Guardians", "For each 100 damage dealt by a single cast, gain a charge of a random ice conjuration spell.")
		self.upgrades['mirror'] = (1, 4, "Dual Wind", "Chill Wind also casts behind the caster.")
		self.upgrades['cast_blazerip'] = (1, 7, "Arcane Storm", "On kill, Chill Wind casts your Blazerip spell.")

	def get_description(self):
		return ("Deals [{damage}_ice:ice] damage and inflicts [{duration}_turns:duration] of [frozen] on units in a [3_tile:radius] wide line perpendicular to the caster.").format(**self.fmt_dict())

	def cast(self, x, y):
		for p in self.get_impacted_tiles(x, y):
			unit = self.caster.level.get_unit_at(p.x, p.y)
			self.damage_dealt += self.caster.level.deal_damage(p.x, p.y, self.get_stat('damage'), Tags.Ice, self)
			if unit:
				if unit.is_alive():
					unit.apply_buff(FrozenBuff(), self.get_stat('duration'))
				elif self.get_stat('cast_blazerip'):
					blazerip_spell = self.caster.get_or_make_spell(Blazerip)
					for _ in self.caster.level.act_cast(self.caster, blazerip_spell, p.x, p.y, pay_costs=False, queue=False):
						pass
			if random.random() < .4:
				yield

		if self.get_stat('refresh_conjuration'):
			while self.damage_dealt >= 100:

				self.damage_dealt -= 100
				eligible_spells = self.caster.spells
				eligible_spells = [s for s in eligible_spells if Tags.Ice in s.tags and Tags.Conjuration in s.tags]
				eligible_spells = [s for s in eligible_spells if s.cur_charges < s.get_stat('max_charges')]

				if eligible_spells:
					s = random.choice(eligible_spells)
					s.cur_charges += 1

	def get_impacted_tiles(self, x, y):
		line = self.caster.level.get_perpendicular_line(self.caster, Point(x, y))
		result = set()
		for p in line:
			for q in self.caster.level.get_points_in_rect(p.x-1, p.y-1, p.x+1, p.y+1):
				result.add(q)
		if self.get_stat('mirror'):
			mirrored_line = self.caster.level.get_perpendicular_line(self.caster, Point(2*self.caster.x-x, 2*self.caster.y-y))
			for p in mirrored_line:
				for q in self.caster.level.get_points_in_rect(p.x-1, p.y-1, p.x+1, p.y+1):
					result.add(q)
		return result

class HungryIceWallBuff(Buff):

	def on_init(self):
		self.name = "Hungry Wall"
		self.description = "+1 minion duration whenever an enemy dies of ice damage"
		self.global_triggers[EventOnDeath] = self.on_death

	def on_death(self, evt):
		if not evt.damage_event:
			return

		if evt.damage_event.damage_type == Tags.Ice and are_hostile(self.owner, evt.unit):
			self.owner.turns_to_death += 1

class IceWall(Spell):
	
	def on_init(self):
		self.name = "Wall of Ice"
		self.minion_health = 36
		self.minion_duration = 15
		self.minion_range = 3
		self.minion_damage = 5

		self.level = 4
		self.max_charges = 3

		self.tags = [Tags.Conjuration, Tags.Ice]

		self.range = 7
		self.radius = 3

		self.upgrades['hungry_wall'] = (1, 3, "Hungry Wall", "+1 minion duration whenever an enemy dies of ice damage")
		self.upgrades['fae_wall'] = (1, 5, "Fae Wall", "Ice Walls gain fae modifier.")
		self.upgrades['endless_wall'] = (99, 7, "Endless Wall", "Infinite radius, make floors out of tiles in AoE.")

		# Permafrost
		# Cast your Freeze spell
		# Summon random one offs?
		# infinite radiius????

	def fmt_dict(self):
		d = Spell.fmt_dict(self)
		d['width'] = 1 + 2*d['radius']
		return d

	def get_description(self):
		return ("Summons a line of ice elementals with a length of [{width}_tiles:num_summons].\n"
				"Ice elementals have [{minion_health}_HP:minion_health], [50_physical:physical] resist, [100_ice:ice] resist, [-100_fire:fire] resist, and cannot move.\n"
				"Ice elementals have a ranged attack which deals [{minion_damage}_ice:ice] damage at a range of up to [{minion_range}_tiles:minion_range].\n"
				"The elementals vanish after [{minion_duration}_turns:minion_duration].").format(**self.fmt_dict())

	def cast(self, x, y):
		for p in self.get_impacted_tiles(x, y):
			elemental = Unit()
			elemental.name = "Ice Elemental"
			snowball = SimpleRangedAttack(damage=self.get_stat('minion_damage'), damage_type=Tags.Ice, range=self.get_stat('minion_range'))
			snowball.name = "Snowball"
			elemental.spells.append(snowball)
			elemental.max_hp = self.get_stat('minion_health')
			elemental.stationary = True
			
			elemental.tags = [Tags.Elemental, Tags.Ice]
			
			elemental.resists[Tags.Physical] = 50
			elemental.resists[Tags.Fire] = -100
			elemental.resists[Tags.Ice] = 100
			
			elemental.turns_to_death = self.get_stat('minion_duration')

			if self.get_stat('hungry_wall'):
				elemental.apply_buff(HungryIceWallBuff())
			if self.get_stat('fae_wall'):
				BossSpawns.apply_modifier(BossSpawns.Faetouched, elemental)

			if self.get_stat('endless_wall') and (self.owner.level.tiles[p.x][p.y].is_wall() or self.owner.level.tiles[p.x][p.y].is_chasm):
				self.owner.level.make_floor(p.x, p.y)

			self.summon(elemental, target=p, radius=0)
			yield

	def get_impacted_tiles(self, x, y): 
		points = self.caster.level.get_perpendicular_line(self.caster, Point(x, y), length=self.get_stat('radius') + self.get_stat('endless_wall'))
		if not self.get_stat('endless_wall'):
			points = [p for p in points if self.caster.level.can_walk(p.x, p.y, check_unit=True)]
		else:
			points = [p for p in points if not self.caster.level.get_unit_at(p.x, p.y)]
		return points

class AftershocksBuff(Buff):

	def on_init(self):
		self.name = "Aftershocks"
		self.buff_type = BUFF_TYPE_BLESS
		self.color = Tags.Nature.color
		self.spell_bonuses[EarthquakeSpell]['radius'] = 2
		self.stack_type = STACK_INTENSITY

class EarthquakeSpell(Spell):

	def on_init(self):
		self.name = "Earthquake"

		self.radius = 7
		self.max_charges = 4
		self.range = 0

		self.damage = 21
		self.level = 3
		self.tags = [Tags.Sorcery, Tags.Nature]

		self.upgrades['safety'] = (1, 2, "Safety", "Earthquake will not damage friendly units.")
		self.upgrades['radius_buff'] = (1, 2, "Aftershocks", "Whenever you cast Earthquake, Earthquake gains +2 radius for 2 turns.") #Changed to 2 turns for same reason as Wildfire
		self.upgrades['stun'] = (1, 4, "Magnitude 8.0", "Stuns for 7 turns.") #change to duration for scaling?

	def get_description(self):
		return ("Invoke an earthquake with a [{radius}_tile:radius] radius.\n"
				"Each tile in the area has a 50% chance to be affected.\n"
				"Units on affected tiles take [{damage}_physical:physical] physical damage.\n"
				"Walls on affected tiles are destroyed.").format(**self.fmt_dict())

	def cast(self, x, y):
		points = list(self.caster.level.get_points_in_ball(self.caster.x, self.caster.y, radius=self.get_stat('radius')))
		random.shuffle(points)
		for p in points:

			unit = self.caster.level.get_unit_at(p.x, p.y)
			if unit == self.caster:
				continue

			if self.get_stat('safety') and unit and not are_hostile(self.caster, unit):
				continue

			if random.random() < .5:
				continue

			self.caster.level.show_effect(p.x, p.y, Tags.Physical)

			if random.random() < .3:
				yield

			if unit:
				if self.get_stat('stun'):
					unit.apply_buff(Stun(), 7)
				unit.deal_damage(self.get_stat('damage'), Tags.Physical, self)
				continue

			tile = self.caster.level.tiles[p.x][p.y]
			if not tile.can_walk:
				self.caster.level.make_floor(p.x, p.y)

		if self.get_stat('radius_buff'):
			self.caster.apply_buff(AftershocksBuff(), 2)

class SearingSealBuff(Buff):

	def __init__(self, spell, dmg_mod=1):
		self.spell = spell
		self.dmg_mod = dmg_mod
		Buff.__init__(self)

	def on_init(self):
		self.name = "Seal of Searing"
		self.dtypes = [Tags.Fire]
		self.charges = [0]
		if self.spell.get_stat('chaos_seal'):
			self.dtypes = [Tags.Fire, Tags.Lightning, Tags.Physical]
			self.charges = [0, 0, 0]
		self.stack_type = STACK_REPLACE
		self.buff_type = BUFF_TYPE_BLESS
		self.global_triggers[EventOnDamaged] = self.on_damage

	def get_description(self):
		num_charges = 0
		for i in range(len(self.charges)):
			num_charges += self.charges[i]
		return "Gains 1 charge each time an enemy unit takes fire damage.\nOn expiration, deals 1 damage to each enemy in LOS for every 4 charges.\n\nCurrent charges: %d" % num_charges

	def on_damage(self, evt):
		for i in range(len(self.dtypes)):
			if evt.damage_type == self.dtypes[i]:
				self.charges[i] += evt.damage

	def on_unapplied(self):
		self.owner.level.queue_spell(self.sear())

	def sear(self):
		enemies = [u for u in self.owner.level.get_units_in_los(self.owner) if are_hostile(self.owner, u)]
		for i in range(len(self.dtypes)):
			damage = self.charges[i] // 5
			for u in enemies:
				u.deal_damage(damage // self.dmg_mod, self.dtypes[i], self.spell)
				yield
		
		if self.spell.get_stat('slow_burn') and self.dmg_mod != 3:
			self.owner.apply_buff(SearingSealBuff(self.spell, dmg_mod=self.dmg_mod + 1), self.spell.get_stat('duration'))
		if self.spell.get_stat('fire_harvest'):
			while self.charges[0] > 100:
				self.charges[0] -= 100
				self.summon(FireSpirit())

class SearingSealSpell(Spell):

	def on_init(self):
		self.name = "Searing Seal"
		
		self.tags = [Tags.Fire, Tags.Enchantment]
		self.level = 4
		self.max_charges = 6
		self.range = 0
		self.duration = 6

		self.upgrades['slow_burn'] = (1, 4, "Slow Burn", "On expiring and dealing damage, gain a buff that redeals half the damage, then, finally, one that deals a third of it.")
		self.upgrades['chaos_seal'] = (1, 4, "Chaos Seal", "Gains charges separately from [fire:fire], [lightning:lightning], and [physical:physical] damage, and redeals each on expiration.")
		self.upgrades['fire_harvest'] = (1, 5, "Fire Harvest", "For every 100 damage dealt, summon a flame spirit.")

	def get_description(self):
		return ("Gain Seal of Searing.\n"
				"Whenever a unit takes [fire] damage, the seal gains that many charges.\n"
				"When the seal expires, it deals [1_fire:fire] damage to all enemies in line of sight for every 5 charges it has.\n"
				"The seal lasts [{duration}_turns:duration].\n"
				"Recasting the spell will expire the current seal and create a new one.").format(**self.fmt_dict())

	def cast_instant(self, x, y):
		self.caster.apply_buff(SearingSealBuff(self), self.get_stat('duration'))

class PurityBuff(Buff):

	def on_init(self):
		self.name = "Purity"
		self.description = "Immune to debuffs."
		self.color = Tags.Holy.color
		self.asset = ['status', 'purity']

	def on_applied(self, owner):
		self.owner.debuff_immune = True

	def on_unapplied(self):
		self.owner.debuff_immune = False

class PuritySpell(Spell):

	def on_init(self):
		self.name = "Purity"

		self.duration = 6
		self.level = 4
		self.max_charges = 4

		self.upgrades['duration'] = (6, 3)
		self.upgrades['max_charges'] = (4, 3)
		self.range = 0

		self.tags = [Tags.Holy, Tags.Enchantment]

	def get_description(self):
		return ("Lose all debuffs.\n"
				"You cannot gain new debuffs.\n"
				"Lasts [{duration}_turns:duration].").format(**self.fmt_dict())

	def cast_instant(self, x, y):
		buffs = list(self.caster.buffs)
		for b in buffs:
			if b.buff_type == BUFF_TYPE_CURSE:
				self.caster.remove_buff(b)
		self.caster.apply_buff(PurityBuff(), self.get_stat('duration'))

class TwilightGazeBuff(Buff):

	def __init__(self, spell):
		self.spell = spell
		Buff.__init__(self)

	def on_init(self):
		self.name = "Twilight"
		self.buff_type = BUFF_TYPE_CURSE
		self.resists[Tags.Dark] = -self.spell.get_stat('resistance_debuff')
		self.resists[Tags.Holy] = -self.spell.get_stat('resistance_debuff')
		if self.spell.get_stat('arcane'):
			self.resists[Tags.Arcane] = -self.spell.get_stat('resistance_debuff')
		self.color = Tags.Dark.color
		self.stack_type = STACK_DURATION


class TwilightGazeSpell(Spell):

	def on_init(self):
		self.name = "Twilight Gaze"

		self.level = 6
		self.max_charges = 4
		
		self.resistance_debuff = 50
		self.duration = 10

		self.upgrades['resistance_debuff'] = (50, 3)
		self.upgrades['duration'] = (10, 2)
		self.upgrades['arcane'] = (1, 3, "Arcane Gaze", "Twilight Gaze also reduces [arcane] resist.")

		self.tags = [Tags.Holy, Tags.Dark, Tags.Enchantment]
		self.range = 0

	def get_description(self):
		return ("All enemies in line of sight lose [{resistance_debuff}_dark:dark] resist and [{resistance_debuff}_holy:holy] resist.\n"
				"Lasts [{duration}_turns:duration].").format(**self.fmt_dict())

	def cast(self, x, y):
		units = [u for u in self.caster.level.get_units_in_los(self.caster) if are_hostile(u, self.caster)]
		units.sort(key=lambda u: distance(self.caster, u)) 
		for u in units:
			u.apply_buff(TwilightGazeBuff(self), self.get_stat('duration'))
			yield

class SlimeformBuff(Buff):

	def __init__(self, spell):
		self.spell = spell
		Buff.__init__(self)

	def on_init(self):
		self.name = "Slime Form"
		self.transform_asset_name = "slime_form"
		self.stack_type = STACK_TYPE_TRANSFORM
		self.resists[Tags.Poison] = 100
		self.resists[Tags.Physical] = 50

	def make_summon(self, base):
		unit = base()
		unit.max_hp = self.spell.get_stat('minion_health')
		unit.spells[0].damage = self.spell.get_stat('minion_damage')
		if not unit.spells[0].melee:
			unit.spells[0].range = self.spell.get_stat('minion_range')
		# Make sure bonuses propogate
		unit.buffs[0].spawner = lambda : self.make_summon(base)
		unit.source = self.spell
		return unit

	def on_advance(self):
		spawn_funcs = [GreenSlime]
		if self.spell.get_stat('fire_slimes'):
			spawn_funcs.append(RedSlime)
		if self.spell.get_stat('ice_slimes'):
			spawn_funcs.append(IceSlime)
		if self.spell.get_stat('void_slimes'):
			spawn_funcs.append(VoidSlime)
		
		spawn_func = random.choice(spawn_funcs)
		unit = self.make_summon(spawn_func)
		self.spell.summon(unit)

class SlimeformSpell(Spell):

	def on_init(self):
		self.name = "Slime Form"
		self.tags = [Tags.Arcane, Tags.Enchantment, Tags.Conjuration]
		self.level = 5
		self.max_charges = 2
		self.range = 0
		self.duration = 8

		self.upgrades['fire_slimes'] = (1, 1, "Fire Slime", "Gain a chance to summon fire slime.")
		self.upgrades['ice_slimes'] = (1, 2, "Ice Slime", "Gain a chance to summon ice slime.")
		self.upgrades['void_slimes'] = (1, 3, "Void Slime", "Gain a chance to summon void slime.")

		ex = GreenSlime()

		self.minion_health = ex.max_hp
		self.minion_damage = ex.spells[0].damage
		self.minion_range = 3

	def get_description(self):
		return ("Assume slime form for [{duration}_turns:duration].\n"
				"Gain [50_physical:physical] resist while in slime form.\n"
				"Gain [100_poison:poison] resist while in slime form.\n"
				"Summon a friendly slime each turn while in slime form.\n"
				"Slimes have [{minion_health}_HP:minion_health], have a 50% chance each turn to gain 1 max HP, and split into two slimes upon reaching twice their starting HP.\n"
				"Slimes have a melee attack which deals [{minion_damage}_poison:poison] damage.").format(**self.fmt_dict())

	def cast_instant(self, x, y):
		self.caster.apply_buff(SlimeformBuff(self), self.get_stat('duration'))

class AetherSicknessBuff(Buff):

	def on_init(self):
		self.name = "Aether Poison"
		self.buff_type = BUFF_TYPE_CURSE
		self.color = Tags.Arcane.color
		self.damage = 1
		self.resists[Tags.Arcane] = -50

	def on_advance(self):
		self.owner.deal_damage(self.damage, Tags.Arcane, self)

class Blazerip(Spell):

	def on_init(self):
		self.name = "Blazerip"
		self.tags = [Tags.Arcane, Tags.Fire, Tags.Sorcery]
		self.level = 3
		self.max_charges = 8
		self.damage = 12
		self.range = 6
		self.requires_los = False
		self.radius = 3

		self.upgrades['mirror'] = (1, 3, "Dual Blazerip", "Blazerip also casts behind the player.")
		self.upgrades['aether_poison'] = (1, 3, "Aether Poison", "Inflicts Aether Poison on units it hits. Aether Poison lasts [4:duration] turns, and deals [1_arcane:damage] damage per turn, and causes the enemy to lose 50 [arcane] resistance during the duration.")
		self.upgrades['blazebugs'] = (1, 5, "Blazebugs", "On kill, summon a swarm of either Fae Flies or Burning Flies.")

	def get_fae_flies(self):
		flies = FlyCloud()
		BossSpawns.apply_modifier(BossSpawns.Faetouched, flies)
		return flies

	def get_fire_flies(self):
		flies = FlyCloud()
		BossSpawns.apply_modifier(BossSpawns.Flametouched, flies)
		return flies

	def summon_flies(self, x, y):
		flies = None
		if random.random() > .5:
			flies = self.get_fae_flies()
		else:
			flies = self.get_fire_flies()
		self.summon(flies, target=Point(x, y))
		yield

	def cast(self, x, y):
		points = self.get_impacted_tiles(x, y)
		for p in points:
			unit = self.caster.level.get_unit_at(p.x, p.y)
			if unit:
				if self.get_stat('aether_poison'):
					unit.apply_buff(AetherSicknessBuff(), self.get_stat('duration', base=4)) #currently applies debuff BEFORE dealing damage. Let me know if you want this to change to after.
			
			self.owner.level.deal_damage(p.x, p.y, self.get_stat('damage'), Tags.Arcane, self)
			
			if self.get_stat('blazebugs') and unit and not unit.is_alive():
				self.caster.level.queue_spell(self.summon_flies(p.x, p.y))
			
			if self.owner.level.tiles[p.x][p.y].is_wall():
				self.owner.level.make_floor(p.x, p.y)
			yield

		for p in reversed(points):
			unit = self.caster.level.get_unit_at(p.x, p.y)
			self.owner.level.deal_damage(p.x, p.y, self.get_stat('damage'), Tags.Fire, self)
			if self.get_stat('blazebugs') and unit and not unit.is_alive():
				self.caster.level.queue_spell(self.summon_flies(p.x, p.y))
			yield
	
	def fmt_dict(self):
		d = Spell.fmt_dict(self)
		d['width'] = 1 + 2*d['radius']
		return d

	def get_extra_examine_tooltips(self):
		return [self.spell_upgrades[0], self.spell_upgrades[1], self.spell_upgrades[2], self.get_fae_flies(), self.get_fire_flies()]

	def get_description(self):
		return ("Deals [{damage}_arcane:arcane] and [{damage}_fire:fire] damage in a [{width}_tile:radius] line perpendicular to the caster.\n"
				"Melts walls in the affected area.").format(**self.fmt_dict())

	def get_impacted_tiles(self, x, y): 
		points = self.caster.level.get_perpendicular_line(self.caster, Point(x, y), length=self.get_stat('radius'))
		if self.get_stat('mirror'):
			mirrored_points = self.caster.level.get_perpendicular_line(self.caster, Point(2*self.caster.x-x, 2*self.caster.y-y), length=self.get_stat('radius'))
			for p in mirrored_points:
				points.append(p)
		return points

class IceVortex(Spell):

	def on_init(self):
		self.name = "Ice Vortex"
		self.damage = 11
		self.tags = [Tags.Ice, Tags.Arcane, Tags.Sorcery]
		self.level = 4
		self.max_charges = 6
		self.duration = 2
		self.range = 10
		self.requires_los = False

		self.radius = 5

		self.upgrades['damage'] = (11, 3)
		self.upgrades['duration'] = (2, 2)
		self.upgrades['radius'] = (3, 2)

	def can_cast(self, x, y):
		u = self.caster.level.get_unit_at(x, y)
		if not u:
			return False
		if not u.has_buff(FrozenBuff):
			return False
		return Spell.can_cast(self, x, y)

	def get_description(self):
		return ("Must target a frozen unit.\n"
				"All enemy units in a [{radius}_tile:radius] radius are pulled towards that unit, [frozen] for [{duration}_turns:duration], and dealt [{damage}_arcane:arcane] and [{damage}_ice:ice] damage.").format(**self.fmt_dict())

	def modify_test_level(self, level):
		first_enemy = [u for u in level.units if u.team != TEAM_PLAYER][0]
		first_enemy.apply_buff(FrozenBuff(), 5)

	def cast(self, x, y):
		main_target = self.caster.level.get_unit_at(x, y)
		units = [u for u in self.caster.level.get_units_in_ball(Point(x, y), self.get_stat('radius')) if u != main_target]
		random.shuffle(units)
		units.sort(key=lambda u: distance(u, Point(x, y)))
		for u in units:

			if not are_hostile(u, self.caster):
				continue

			for p in self.caster.level.get_points_in_line(Point(x, y), u):
				dtype = random.choice([Tags.Ice, Tags.Arcane])
				self.caster.level.show_effect(p.x, p.y, dtype, minor=True)

			pull(u, Point(x, y), self.get_stat('radius'))
			yield
			u.apply_buff(FrozenBuff(), self.get_stat('duration'))
			yield
			u.deal_damage(self.get_stat('damage'), Tags.Arcane, self)
			yield
			u.deal_damage(self.get_stat('damage'), Tags.Ice, self)
			yield


class RestlessDeadBuff(Buff):

	def __init__(self, spell):
		self.spell = spell
		Buff.__init__(self)

	def on_init(self):
		self.global_triggers[EventOnDamaged] = self.on_damaged
		self.name = "Restless Dead"
		self.color = Tags.Dark.color	

	def on_damaged(self, damage_event):
		if damage_event.unit.cur_hp > 0:
			return

		if not self.owner.level.are_hostile(self.owner, damage_event.unit) and not self.spell.get_stat('friendly'):
			return

		if Tags.Living in damage_event.unit.tags:
			self.owner.level.queue_spell(self.raise_skeleton(damage_event.unit))
		elif Tags.Construct in damage_event.unit.tags and self.spell.get_stat('salvage'):
			self.owner.level.queue_spell(self.raise_golem(damage_event.unit))
		if (Tags.Fire in damage_event.unit.tags or Tags.Lightning in damage_event.unit.tags) and self.spell.get_stat('spirit_catcher'):
			self.owner.level.queue_spell(self.grant_sorcery(damage_event.unit))


	def raise_skeleton(self, unit):
		if unit and unit.cur_hp <= 0:
			skeleton = raise_skeleton(self.owner, unit, source=self.spell)
			if skeleton:
				skeleton.spells[0].damage += self.spell.get_stat('minion_damage') - 5
			yield

	def raise_golem(self, unit):
		if unit and unit.cur_hp <= 0 and not self.owner.level.get_unit_at(unit.x, unit.y):
			g = Golem()
			g.asset_name = 'golem_junk'
			g.name = "Junk Golem"
			g.spells = [SimpleMeleeAttack(self.spell.get_stat('minion_damage'))]
			g.tags.append(Tags.Undead)
			g.max_hp = unit.max_hp
			self.summon(g, target=unit)
		yield

	def grant_sorcery(self, unit):
		grantables = []
		if Tags.Fire in unit.tags:
			grantables.append(Tags.Fire)
		if Tags.Lightning in unit.tags:
			grantables.append(Tags.Lightning)
		if Tags.Ice in unit.tags:
			grantables.append(Tags.Ice)

		if not grantables:
			return

		candidates = [u for u in self.owner.level.units if not u.has_buff(TouchedBySorcery) and not are_hostile(u, self.owner) and u != self.owner]

		if not candidates:
			return

		candidate = random.choice(candidates)
		chosen_tag = random.choice(grantables)
		buff = TouchedBySorcery(chosen_tag)

		candidate.apply_buff(buff)
		self.owner.level.show_path_effect(unit, candidate, chosen_tag, minor=True)
		yield

	def get_description(self):
		return ("Whenever a living enemy dies, raise it as a skeleton.")

class RestlessDead(Spell):

	def on_init(self):
		self.name = "The Restless Dead"
		self.level = 4
		self.tags = [Tags.Dark, Tags.Enchantment, Tags.Conjuration]
		self.duration = 20
		self.range = 0
		self.max_charges = 3
		self.minion_damage = 5

		self.upgrades['salvage'] = (1, 2, "Junk Golems", "Whenever an enemy constructs dies, raise it as a junk golem.")
		self.upgrades['spirit_catcher'] = (1, 3, "Elemental Spirits", "Whenever an enemy fire, ice or lightning unit dies, a random summoned ally gains 100 resistance to that element and a ranged attack of that type.  Each ally can gain only 1 such buff.")
		self.upgrades['friendly'] = (1, 2, "Restless Minions", "Allies can also be raised by Restless Dead")

	def get_description(self):
		return ("Whenever a living enemy dies, raise it as a skeleton.\n"
				"Raised skeletons have max HP equal to that of the slain unit, and deal [{minion_damage}_physical:physical] damage in melee.\n"
				"Skeletons of flying units can fly.\n"
				"This effect lasts [{duration}_turns:duration].").format(**self.fmt_dict())

	def cast_instant(self, x, y):
		self.caster.apply_buff(RestlessDeadBuff(self), self.get_stat('duration'))

class GustOfWind(Spell):

	def on_init(self):
		self.name = "Gust of Wind"
		self.level = 2
		self.tags = [Tags.Nature, Tags.Sorcery]
		self.range = 7
		self.max_charges = 10
		self.angle = math.pi / 6
		self.damage = 14
		self.force = 3
		self.stats.append('force')
		self.duration = 3

		self.upgrades['duration'] = (2, 2, "Stun Duration")
		self.upgrades['range'] = (4, 4)
		self.upgrades['damage'] = (10, 3)
		self.upgrades['force'] = (3, 3)

	def get_description(self):
		return ("Push back units in a cone [{force}:range] tiles.\n"
				"If a unit collides with a wall, chasm, or another unit, it is [stunned] for [{duration}_turns:duration] and takes [{damage}_physical:physical] damage.\n"
				"Stationary enemise are unaffected.\n"
				"Stormclouds and webs in the area are destroyed.\n").format(**self.fmt_dict())
		

	def get_impacted_tiles(self, x, y):
		target = Point(x, y)
		burst = Burst(self.caster.level, self.caster, self.get_stat('range'), expand_diagonals=True, burst_cone_params=BurstConeParams(target, self.angle))
		return [p for stage in burst for p in stage if self.caster.level.can_see(self.caster.x, self.caster.y, p.x, p.y)]

	def blow(self, unit, start_loc):
		for p in self.caster.level.get_points_in_line(start_loc, unit, find_clear=True):
			self.caster.level.leap_effect(p.x, p.y, Tags.Nature.color, unit)
			yield

	def cast_instant(self, x, y):
		to_push = []
		for p in self.get_impacted_tiles(x, y):

			cloud = self.caster.level.tiles[p.x][p.y].cloud
			if cloud:
				cloud.kill()

			unit = self.caster.level.get_unit_at(p.x, p.y)
			if not unit:
				continue
			if unit == self.caster:
				continue
			if unit.stationary:
				continue
			
			to_push.append(unit)
		
		to_push.sort(key=lambda u: -distance(u, self.caster))
		for unit in to_push:
			start_loc = Point(unit.x, unit.y)
			self.owner.level.queue_spell(self.blow(unit, start_loc))
			result = push(unit, self.caster, self.get_stat('force'))
			if not result:
				unit.apply_buff(Stun(), self.get_stat('duration'))
				unit.deal_damage(self.get_stat('damage'), Tags.Physical, self)

class ChaosCast(Upgrade):

	def on_init(self):
		self.level = 4
		self.name = "Pyrostatic Chaos"
		self.description = "Whenever you cast a [chaos] spell, cast Pyrostatic Curse at that position."
		self.owner_triggers[EventOnSpellCast] = self.on_cast

	def on_cast(self, evt):
		if (not Tags.Chaos in evt.spell.tags) or (isinstance(evt.spell, PyrostaticHexSpell)):
			return

		spell = self.owner.get_or_make_spell(PyrostaticHexSpell)
		self.owner.level.act_cast(self.owner, spell, evt.x, evt.y, pay_costs=False)

class PyroStaticHexBuff(Buff):

	def __init__(self, spell):
		self.spell = spell
		Buff.__init__(self)

	def on_init(self):
		self.name = "Pyrostatic Hex"
		self.beam = False
		self.buff_type = BUFF_TYPE_CURSE
		self.color = Tags.Fire.color
		self.owner_triggers[EventOnDamaged] = self.on_damage
		self.asset = ['status', 'pyrostatic_hex']

		if self.spell.get_stat('remove_resistance'):
			self.resists[Tags.Fire] = -25

	def on_damage(self, evt):
		if evt.damage_type != Tags.Fire:
			return

		self.owner.level.queue_spell(self.deal_damage(evt))

	def return_dist(self, unit):
		return distance(self.owner, unit)

	def deal_damage(self, evt):

		redeal_targets = [u for u in self.owner.level.get_units_in_los(self.owner) if are_hostile(u, self.spell.owner) and u != self.owner]
		if not self.beam:
			random.shuffle(redeal_targets)
		else:
			sort(redeal_targets, key=lambda u: distance(u, self.owner))

		for t in redeal_targets[:self.spell.get_stat('num_targets')]:
			if not self.beam:
				for p in self.owner.level.get_points_in_line(self.owner, t)[1:-1]:
					self.owner.level.show_effect(p.x, p.y, Tags.Lightning)
				t.deal_damage(evt.damage, Tags.Lightning, self.spell)
			else:	
				for p in self.owner.level.get_points_in_line(self.owner, t)[1:]:
					self.owner.level.deal_damage(evt.damage // 2, Tags.Lightning, self.spell)
		yield

class PyrostaticHexSpell(Spell):

	def on_init(self):
		self.name = "Pyrostatic Curse"

		self.tags = [Tags.Fire, Tags.Lightning, Tags.Enchantment]
		self.level = 4
		self.max_charges = 10

		self.radius = 5
		self.range = 9
		self.duration = 4

		self.num_targets = 2

		self.upgrades['remove_resistance'] = (1, 2, "Resistance Melting", "Removes 25 Fire resist from targets.")
		self.add_upgrade(ChaosCast())
		self.upgrades['beam'] = (1, 5, "Linear Conductance", "Redealt lightning damage is dealt along a beam instead of just to one target.")

	def get_description(self):
		return ("Curses targets in a [{radius}_tile:radius] radius for [{duration}_turns:duration].\n"
				"Whenever a cursed target takes fire damage, [{num_targets}:num_targets] random enemy units in line of sight of that unit are dealt that much [lightning] damage.\n").format(**self.fmt_dict())

	def cast_instant(self, x, y):
		for p in self.owner.level.get_points_in_ball(x, y, self.get_stat('radius')):
			u = self.owner.level.get_unit_at(p.x, p.y)
			if u and are_hostile(u, self.caster):
				u.apply_buff(PyroStaticHexBuff(self), self.get_stat('duration'))

class SpikeballFactory(Spell):

	def on_init(self):
		self.name = "Spikeball Factory"
		self.tags = [Tags.Metallic, Tags.Conjuration]

		self.level = 7

		self.max_charges = 1

		self.minion_health = 40
		self.range = 0

		#upgrades
		# 2 layers of factories
		# 1 more charge
		# minion hp
		# copper spikeballs
		self.upgrades['defense'] = (1, 3, "Defense System", "The summoned lairs gain a projectile attack with 10 range that deals [5_physical:physical] damage.")
		self.upgrades['manufactory'] = (1, 6, "Manufactory", "Surrounds the initially summoned gates with another layer of gates")
		self.upgrades['copper'] = (1, 7, "Copper Spikeballs", "Summons copper spikeballs instead of normal ones")

	def get_description(self):
		return "Surrounds the caster with spikeball gates, which will spawn spikeballs."


	def spikeball(self):
		if self.get_stat('copper'):
			spikeball = SpikeBallCopper()
		else:
			spikeball = SpikeBall()
		apply_minion_bonuses(self, spikeball)
		return spikeball

	def cast(self, x, y):
		for p in self.get_impacted_tiles(x, y):

			gate = MonsterSpawner(self.spikeball)
			apply_minion_bonuses(self, gate)
			if self.get_stat('defense'):
				spell = SimpleRangedAttack(damage=self.get_stat('minion_damage', base=5), range=self.get_stat('minion_rage', base=10))
				gate.spells.insert(0, spell)
			self.summon(gate, p)
			yield

	def get_impacted_tiles(self, x, y):
		points = set()
		for p in self.owner.level.get_adjacent_points(self.caster, filter_walkable=True, check_unit=True):
			points.add(p)
			yield p
		if self.get_stat('manufactory'):
			for p in points:
				for q in self.owner.level.get_adjacent_points(p, filter_walkable=True, check_unit=True):
					yield q

class MercurizeBuff(Buff):

	def __init__(self, spell):
		self.spell = spell
		Buff.__init__(self)
		if self.spell.get_stat('corrosion'):
			self.resists[Tags.Physical] = -50

	def on_init(self):
		self.buff_type = BUFF_TYPE_CURSE
		self.name = "Mercurized"
		self.asset = ['status', 'mercurized']
		self.owner_triggers[EventOnDeath] = self.on_death

	def on_advance(self):
		dtypes = [Tags.Physical, Tags.Poison]

		if self.spell.get_stat('dark'):
			dtypes.append(Tags.Dark)

		for dtype in dtypes:
			self.owner.deal_damage(self.spell.get_stat('damage'), dtype, self.spell)
			if not self.owner.is_alive():
				break

	def on_death(self, evt):
		geist = Ghost()
		geist.name = "Mercurial %s" % self.owner.name
		geist.asset_name = "mercurial_geist"
		geist.max_hp = self.owner.max_hp
		geist.tags.append(Tags.Metallic)
		trample = SimpleMeleeAttack(damage=self.spell.get_stat('minion_damage'))
		geist.spells = [trample]

		geist.turns_to_death = self.spell.get_stat('minion_duration')

		self.spell.summon(geist, target=self.owner)

		if self.spell.get_stat('noxious_aura'):
			geist.apply_buff(DamageAuraBuff(damage=1, damage_type=Tags.Poison, radius=2))

		if self.spell.get_stat('vengeance'):
			geist.apply_buff(MercurialVengeance(self.spell))


class MercurialVengeance(Buff):

	def __init__(self, spell):
		self.spell = spell
		Buff.__init__(self)

	def on_init(self):
		self.name = "Mercurial Vengeance"
		self.owner_triggers[EventOnDeath] = self.on_death

	def on_death(self, evt):
		# cast a Mercurize with the summoner's buffs
		if evt.damage_event:
			spell = MercurizeSpell()
			spell.owner = self.owner
			spell.caster = self.owner
			spell.statholder = self.spell.statholder or self.spell.caster
			self.owner.level.act_cast(self.owner, spell, evt.damage_event.source.owner.x, evt.damage_event.source.owner.y, pay_costs=False)

class MercurizeSpell(Spell):

	def on_init(self):
		self.name = "Mercurize"

		self.level = 2
		self.tags = [Tags.Dark, Tags.Metallic, Tags.Enchantment, Tags.Conjuration]

		self.damage = 2

		self.max_charges = 6
		self.duration = 6

		self.range = 8

		self.minion_damage = 10

		self.minion_duration = 32

		self.upgrades['dark'] = (1, 4, "Morbidity", "Mercurized targets also take dark damage")
		self.upgrades['corrosion'] = (1, 2, "Corrosion", "Mercurized targets lose 50 physical resist")
		self.upgrades['noxious_aura'] = (1, 4, "Toxic Fumes", "Quicksilver Geists have a noxious aura that deals 1 poison damage to enemy units within [2_tiles:radius] each turn.")
		self.upgrades['vengeance'] = (1, 3, "Mercurial Vengeance", "When a Quicksilver Geist is killed, its killer is affliected with Mercurize.")

	def get_description(self):
		return("Afflict the target with Mercurize.  The target takes [{damage}_poison:poison] and [{damage}_physical:physical] damage each turn for [{duration}_turns:duration].\n"
			   "If the target dies while cursed, it is raised as a Quicksilver Geist.\n"
			   "Geists are flying undead metallic units with many resistances and immunities.\n"
			   "The Geist has max HP equal to the cursed unit, and a trample attack dealing [{minion_damage}_physical:physical] damage.\n"
			   "Geist dissapear after [{minion_duration}_turns:minion_duration]".format(**self.fmt_dict()))

	def can_cast(self, x, y):
		return self.caster.level.get_unit_at(x, y) is not None and Spell.can_cast(self, x, y)

	def cast_instant(self, x, y):
		for p in self.owner.level.get_points_in_line(self.caster, Point(x, y))[1:-1]:
			self.owner.level.show_effect(p.x, p.y, Tags.Dark, minor=True)
		unit = self.caster.level.get_unit_at(x, y)
		if unit:
			unit.apply_buff(MercurizeBuff(self), self.get_stat('duration'))

class MagnetizeBuff(Buff):

	def __init__(self, spell):
		self.spell = spell
		Buff.__init__(self)

	def on_init(self):
		self.name = "Magnetized"
		self.asset = ['status', 'magnetized']

	def on_applied(self, owner):
		self.buff_type = BUFF_TYPE_CURSE if are_hostile(self.owner, self.spell.owner) else BUFF_TYPE_BLESS

	def on_advance(self):
		# pull stuff towards self
		units = [u for u in self.owner.level.get_units_in_ball(self.owner, self.spell.get_stat('radius')) if u != self.owner]
		random.shuffle(units)
		units.sort(key=lambda u: distance(u, self.owner))
		for u in units:
			# Only hit targets hostile to the caster
			if not are_hostile(u, self.spell.owner):
				continue
			for p in self.owner.level.get_points_in_line(self.owner, u):
				self.owner.level.show_effect(p.x, p.y, Tags.Lightning, minor=True)

			pull(u, self.owner, self.spell.get_stat('pull_strength'))

			if distance(self.owner, u) < 2:
				u.apply_buff(Stun(), 1)
				if self.spell.get_stat('cast_mercurize'):
					mercurize_buff = MercurizeBuff(self.spell.caster.get_or_make_spell(MercurizeSpell))
					u.apply_buff(mercurize_buff, self.spell.get_stat('duration', base=1)) #change to 2? since buffs act weird w/ 1 duration
				u.deal_damage(self.spell.get_stat('damage'), Tags.Lightning, self)
			elif self.spell.get_stat('electromagnetism'):
				u.deal_damage(self.spell.get_stat('damage'), Tags.Lightning, self)


class MagnetizeSpell(Spell):

	def on_init(self):
		self.name = "Magnetize"
		self.tags = [Tags.Lightning, Tags.Metallic, Tags.Enchantment]

		self.level = 2
		self.max_charges = 10

		self.radius = 4
		self.pull_strength = 1
		self.stats.append('pull_strength')
		self.damage = 3

		self.range = 9
		self.requires_los = False

		self.duration = 5

		self.upgrades['radioactivity'] = (1, 4, "Radioactivity", "Lowers target's [lightning:lightning] and [arcane:arcane] resist by 75.")
		self.upgrades['electromagnetism'] = (1, 4, "Electromagnetism", "Deals [lightning:lightning] damage to all units in range rather than just adjacent units.")
		self.upgrades['cast_mercurize'] = (1, 7, "Liquid Magnetism", "Casts your Mercurize with 1 duration on adjacent enemy units.")


	def can_cast(self, x, y):
		unit = self.owner.level.get_unit_at(x, y)
		
		if not unit:
			return False

		if not ((Tags.Metallic in unit.tags) or (self.get_stat('universal'))):
			#keeping self.get_stat('universal') for now just in case we wanna keep that later
			return False

		return Spell.can_cast(self, x, y)

	def cast_instant(self, x, y):

		unit = self.owner.level.get_unit_at(x, y)
		if unit:
			if self.get_stat('radioactivity'):
				unit.resists[Tags.Lightning] -= 75
				unit.resists[Tags.Arcane] -= 75
			unit.apply_buff(MagnetizeBuff(self), self.get_stat('duration'))

	def get_description(self):
		return ("Magnetize target metallic unit.\n"
				"Enemy units within a [{radius}_tile:radius] radius of the magnetized unit are pulled [1_tiles:range] towards the unit each turn.\n" #appending 'pull_strength' doesn't seem to work for some reason?
				"Afterwards, adjecent enemy units are stunned for 1 turn. and take [{damage}_lightning:lightning] damage.\n"
				"Lasts [{duration}_turns:duration].").format(**self.fmt_dict())

class SilverSpearSpell(Spell):

	def on_init(self):
		self.name = "Silver Spear"
		self.level = 3
		self.max_charges = 25
		self.tags = [Tags.Holy, Tags.Metallic, Tags.Sorcery]

		self.damage = 27

		self.range = 11
		self.radius = 1

		self.upgrades['deal_lightning'] = (1, 3, "Copper Shaft", "Deals Lightning damage to all enemies adjacent to the spear.")
		self.upgrades['cast_holyblast'] = (1, 4, "Consecration", "Cast your Heavenly Blast on slain targets.")
		#self.upgrades['barrage'] = (1, 4, "Spear Barrage", "Shoots 3 parallel spears.")

	def get_description(self):
		return ("Deals [{damage}_physical:physical] damage to the target.\n"
				"Deals [{damage}_holy:holy] damage to [dark] and [arcane] units within a [{radius}_tile:radius] away from the projectiles path.".format(**self.fmt_dict()))

	def get_impacted_tiles(self, x, y):
		spear_offsets = [Point(0, 0)]
		if self.get_stat('barrage'):
			pass
		points = set()
		for spear in spear_offsets:
			for p in self.caster.level.get_points_in_line(Point(self.caster.x + spear.x, self.caster.y + spear.y), Point(x + spear.x, y + spear.y))[1:]:
				for q in self.caster.level.get_points_in_ball(p.x, p.y, self.get_stat('radius')):
					if q not in points:
						yield q
						points.add(q)

	def cast(self, x, y):
		spear_offsets = [Point(0, 0)]
		#trigonometry fun for parallel spears
		if self.get_stat('barrage'):
			pass #couldn't get the trigonometry fun to work :(
		hits = set()
		# todo- holy sparkles randomly around projectile?
		for spear_offset in spear_offsets:
			
			start_x = self.caster.x + spear_offset.x
			start_y = self.caster.y + spear_offset.y

			start = Point(start_x, start_y)

			end = Point(0, 0)
			
			end_x = x + spear_offset.x
			end_y = y + spear_offset.y

			end = Point(end_x, end_y)

			for p in self.caster.level.get_points_in_line(start, end)[1:]:
				self.caster.level.projectile_effect(p.x, p.y, proj_name='silver_spear', proj_origin=start, proj_dest=end)
				units = self.owner.level.get_units_in_ball(p, self.get_stat('radius'))
				for unit in units:
					if unit in hits:
						continue
					hits.add(unit)
					if Tags.Arcane in unit.tags or Tags.Dark in unit.tags:
						unit.deal_damage(self.get_stat('damage'), Tags.Holy, self)
					if self.get_stat('deal_lightning') and unit != self.caster:
						unit.deal_damage(self.get_stat('damage'), Tags.Lightning, self)
					if self.get_stat('cast_holyblast') and not unit.is_alive():
						holy_blast_spell = self.caster.get_or_make_spell(HolyBlast)
						for _ in self.caster.level.act_cast(self.caster, holy_blast_spell, unit.x, unit.y, pay_costs=False, queue=False):
							yield
				yield

		unit = self.caster.level.get_unit_at(x, y)
		if unit:
			unit.deal_damage(self.get_stat('damage'), Tags.Physical, self)
			if self.get_stat('cast_holyblast') and not unit.is_alive():
				holy_blast_spell = self.caster.get_or_make_spell(HolyBlast)
				for _ in self.caster.level.act_cast(self.caster, holy_blast_spell, unit.x, unit.y, queue=False, pay_costs=False):
					yield

def InfernoCannon():
	unit = Unit()
	unit.tags = [Tags.Construct, Tags.Metallic, Tags.Fire]
	unit.max_hp = 24
	unit.name = "Inferno Cannon"
	unit.asset_name = "goblin_cannon"
	unit.stationary = True

	unit.resists[Tags.Physical] = 50
	unit.resists[Tags.Fire] = -100

	cannonball = SimpleRangedAttack(damage=11, range=12, radius=2, damage_type=[Tags.Physical, Tags.Fire])
	cannonball.name = "Cannon Blast"
	unit.spells = [cannonball]

	unit.buffs.append(DeathExplosion(damage=11, damage_type=Tags.Fire, radius=1))
	return unit

def SiegeGolem():
	unit = SiegeOperator(InfernoCannon)
	unit.name = "Golem Siege Mechanic"
	unit.asset_name = "golem"

	unit.max_hp = 25
	unit.tags = [Tags.Metallic, Tags.Construct]
	return unit

class ChaosCannonball(Spell):

	def on_init(self):
		self.name = "Chaos Cannonball"
		self.tags = [Tags.Chaos]
		self.dtypes = [Tags.Fire, Tags.Lightning, Tags.Physical]
		self.retarget = True
		self.radius = 1

	def cast(self, x, y):
		for dtype in self.dtypes:
			possible_targets = self.caster.level.get_units_in_ball(self.caster, self.range)
			possible_targets = [u for u in possible_targets if self.caster.level.can_see(u.x, u.y, self.caster.x, self.caster.y)]
			possible_targets = [u for u in possible_targets if are_hostile(self.caster, u)]
			if possible_targets:
				target = random.choice(possible_targets)
				x = target.x
				y = target.y

			for point in self.caster.level.get_points_in_line(self.caster, Point(x, y)):
				self.caster.level.deal_damage(point.x, point.y, 0, dtype, self)

			for stage in Burst(self.caster.level, Point(x, y), self.get_stat('radius')):
				for point in stage:
					self.caster.level.deal_damage(point.x, point.y, self.get_stat('damage'), dtype, self)

			yield
		yield

	def get_description(self):
		return ("Shoots a Fire, Lightning, and Physical Cannonball.\n") #Placeholder description, let me know what you want to put here

class SummonSiegeGolemsSpell(Spell):

	def on_init(self):
		self.name = "Siege Golems"
		self.tags = [Tags.Fire, Tags.Conjuration, Tags.Metallic]
		self.level = 4
		self.max_charges = 3
		self.range = 5

		self.minion_damage = 30
		self.minion_range = 15
		self.radius = 3

		self.minion_health = InfernoCannon().max_hp
		self.num_summons = 3

		self.upgrades['assistant_cannoneers'] = (1, 3, "Assistant Cannoneers", "In addition to Siege Golems, summon 5 Goblin Assistants that can repair and operate inferno cannons.")
		self.upgrades['recycling'] = (1, 5, "Recycling", "Constructs and Metallic units killed by Inferno Cannons are summoned as Siege Golems.")
		self.upgrades['chaos_cannon'] = (1, 7, "Chaos Cannon", "Instead of summoning Siege Golems, summon Chaos Siege Golems. Chaos Siege Golems make a Chaos Cannon that shoots a Fire projectile, a Lightning projectile, and a Physical projectile with lowered radiuses.")

		#Upgrade- fires cluster firebombs instead of just explosions?

	def get_description(self):
		return ("Summons a crew of [{num_summons}:num_summons] siege golems.\n"
				"The siege golems will assemble an inferno cannon, or operate one if it is within [3_tiles:range].\n"
				"The inferno cannon deals [{minion_damage}_fire:fire] damage to units in a [{radius}_tile:radius] radius.\n"
				"The cannon will explode when destroyed, dealing [{minion_damage}_fire:fire] damage equal to one quarter its maximum hp to units in a [3_tile:radius].\n".format(**self.fmt_dict()))


	def cannon(self):
		unit = Unit()
		unit.tags = [Tags.Construct, Tags.Metallic, Tags.Fire]
		
		unit.max_hp = 24
		unit.name = "Inferno Cannon"
		unit.stationary = True

		unit.resists[Tags.Physical] = 50
		unit.resists[Tags.Fire] = -100

		cannonball = None
		if not self.get_stat('chaos_cannon'):
			cannonball = SimpleRangedAttack(damage=self.get_stat('minion_damage'), range=self.get_stat('minion_range'), radius=self.get_stat('radius'), damage_type=Tags.Fire)
			cannonball.name = "Fire Blast"
			if self.get_stat('recycling'):
				def try_raise(caster, unit):
					if (not unit.is_alive()) and ((Tags.Metallic in unit.tags) or (Tags.Construct in unit.tags)):
						g = self.golem()
						g.max_hp = unit.max_hp
						if unit.flying:
							g.flying = True
							g.asset_name = "golem_siege_flying"
							g.name = "Flying Siege Golem"
						self.summon(g, unit)

				cannonball.onhit = try_raise
		else:
			cannonball = ChaosCannonball()
			cannonball.range = self.get_stat('minion_range')
			cannonball.damage = self.get_stat('minion_damage')
			unit.asset_name = "inferno_cannon_chaos"
		unit.spells = [cannonball]

		unit.buffs.append(DeathExplosion(damage=self.get_stat('minion_damage'), damage_type=Tags.Fire, radius=1))

		unit.max_hp = 18
		return unit

	def golem(self):
		golem = SiegeOperator(self.cannon)
		golem.spells[2].range = 3
		golem.spells[1].heal = 2
		golem.name = "Golem Siege Mechanic"
		golem.asset_name = "golem_siege"
		golem.max_hp = 25
		golem.tags = [Tags.Metallic, Tags.Construct]
		apply_minion_bonuses(self, golem)

		if self.get_stat('chaos_cannon'):
			golem.asset_name = "golem_siege_chaos"
			golem.name = "Chaos Golem Siege Mechanic"

		return golem

	def get_assistant(self):
		assistant = SiegeOperator(self.cannon)
		assistant.spells.remove(assistant.spells[3])
		assistant.name = "Goblin Siege Assistant"
		assistant.max_hp = 6
		assistant.asset_name = "goblin_cannon_crew"
		assistant.tags = [Tags.Living]
		apply_minion_bonuses(self, assistant)

		return assistant

	def cast(self, x, y):
		for i in range(self.get_stat('num_summons')):
			golem = self.golem()
			self.summon(golem, target=Point(x, y))
			yield
		if self.get_stat('assistant_cannoneers'):
			for i in range(self.get_stat('num_summons')+2):
				assistant = self.get_assistant()
				self.summon(assistant, target=Point(x, y))
				yield

# Lightning Spire
# Each turn fires lightning bolts a random X units in the aoe

class LightningSpireArc(Spell):

	def on_init(self):
		self.name = "Zap"

		self.damage = 5
		self.num_targets = 2
		self.range = 0
		self.radius = 4
		self.requires_los = True

	def get_ai_target(self):
		if self.get_targets():
			return self.owner
		else:
			return None

	def can_target(self, t):
		if t.resists[Tags.Lightning] >= 100:
			return False
		if not are_hostile(self.owner, t):
			return False
		if not self.owner.level.can_see(self.owner.x, self.owner.y, t.x, t.y):
			return self.get_stat('requires_los')
		return True

	def get_targets(self):
		potential_targets = self.owner.level.get_units_in_ball(self.owner, self.get_stat('radius'))
		potential_targets = [t for t in potential_targets if self.can_target(t)]
		random.shuffle(potential_targets)
		return potential_targets[:self.get_stat('num_targets')]

	def can_cast(self, x, y):
		return self.get_targets()

	def cast(self, x, y):
		targets = self.get_targets()
		for t in targets:
			for p in self.owner.level.get_points_in_line(self.owner, t)[1:-1]:
				self.owner.level.show_effect(p.x, p.y, Tags.Lightning, minor=True)
			self.owner.level.deal_damage(t.x, t.y, self.get_stat('damage'), Tags.Lightning, self)
			if self.get_stat('resistance_debuff'):
				t.apply_buff(Electrified())
			yield

class LightningSpire(Spell):

	def on_init(self):

		self.name = "Lightning Spire"
		self.minion_health = 25
		self.minion_damage = 8
		self.radius = 5
		self.max_charges = 5
		self.level = 3
		self.range = 6

		self.num_targets = 4

		self.tags = [Tags.Lightning, Tags.Metallic, Tags.Conjuration]

		self.upgrades['num_targets'] = (4, 4, "Mass Blasting")
		self.upgrades['blindcasting'] = (1, 5, "Wall Penetration", "The spires can zap enemies through walls.")
		self.upgrades['resistance_debuff'] = (1, 5, "Resistance Penetration", "Zapped units permenantly lose 10 [lightning] resistance.")


		self.must_target_empty = True

	def get_description(self):
		return ("Summon a Lightning Spire.\n"
				"Lightning Spires are stationary [metallic] constructs with [{minion_health}:minion_health] max hp.\n"
				"Each turn, the spire will zap up to [{num_targets}:num_targets] enemy units up to [{radius}:minion_range] tiles away, dealing [{minion_damage}_lightning:lightning] damage.").format(**self.fmt_dict())


	def get_impacted_tiles(self, x, y):
		for p in self.owner.level.get_points_in_ball(x, y, self.get_stat('radius')):
			if self.get_stat('blindcasting'):
				yield p
			elif self.owner.level.can_see(x, y, p.x, p.y):
				yield p

	def cast_instant(self, x, y):
		unit = Unit()
		unit.name = "Lightning Spire"

		unit.max_hp = self.get_stat('minion_health')
		unit.tags = [Tags.Metallic, Tags.Construct, Tags.Lightning]

		arc = LightningSpireArc()
		arc.damage = self.get_stat('minion_damage')
		arc.num_targets = self.get_stat('num_targets')
		arc.radius = self.get_stat('radius')
		arc.requires_los = self.get_stat('blindcasting')
		arc.resistance_debuff = self.get_stat('resistance_debuff')
		
		unit.spells = [arc]

		unit.stationary = True

		self.summon(unit, target=Point(x, y))

class EssenceFlux(Spell):

	def on_init(self):
		self.name = "Essence Flux"
		self.tags = [Tags.Arcane, Tags.Chaos, Tags.Enchantment]

		self.max_charges = 12
		self.level = 4
		self.range = 7
		self.radius = 4

		self.upgrades['radius'] = (2, 2)
		self.upgrades['max_charges'] = (6, 2)

	def get_description(self):
		return ("Swap the polarity of the resistances of all other units in a [{radius}_tile:radius] area.\n"
				"[Fire] resistance is swapped with [ice].\n"
				"[Lightning] resistance is swapped with [physical].\n"
				"[Dark] resistance is swapped with [holy].\n"
				"[Poison] resistance is swapped with [arcane].\n").format(**self.fmt_dict())

	def cast(self, x, y):

		points = list(self.caster.level.get_points_in_ball(x, y, self.get_stat('radius')))
		random.shuffle(points)
		for p in points:

			unit = self.caster.level.get_unit_at(p.x, p.y)

			if unit == self.caster:
				continue

			if unit:
				old_resists = unit.resists.copy()
				for e1, e2 in [
					(Tags.Fire, Tags.Ice),
					(Tags.Lightning, Tags.Physical),
					(Tags.Dark, Tags.Holy),
					(Tags.Poison, Tags.Arcane)]:

					if old_resists[e1] == 0 and old_resists[e2] == 0:
						continue

					if old_resists[e1] == old_resists[e2]:
						continue

					unit.resists[e1] = old_resists[e2]
					unit.resists[e2] = old_resists[e1]

					color = e1.color if old_resists[e1] > old_resists[e2] else e2.color
					self.caster.level.show_effect(unit.x, unit.y, Tags.Debuff_Apply, fill_color=color)
			else:
				self.owner.level.show_effect(p.x, p.y, Tags.Chaos)
			if random.random() < .25:
				yield


class FaehauntGardenBuff(Buff):

	def __init__(self, spell):
		Buff.__init__(self)
		self.name = "Faehaunt Gardener"
		self.buff_type = BUFF_TYPE_BLESS
		self.color = Tags.Arcane.color
		self.counter = 0
		self.counter_max = 50
		self.global_triggers[EventOnDamaged] = self.on_damaged
		self.spell = spell

		self.fly_counter = 0
		self.fly_counter_max = 15

	def on_damaged(self, evt):

		if evt.damage_type not in [Tags.Arcane, Tags.Lightning]:
			return

		if not evt.source or not evt.source.owner == self.owner:
			return

		self.counter += evt.damage
		while self.counter > self.counter_max:
			self.counter -= self.counter_max

			if self.spell.get_stat('glass'):
				butterfly = GlassButterfly()
			else:
				butterfly = ButterflyDemon()

			apply_minion_bonuses(self.spell, butterfly)
			bfly = self.summon(butterfly, target=evt.unit, sort_dist=False)
			if bfly:
				self.owner.level.show_path_effect(self.owner, bfly, [Tags.Arcane, Tags.Lightning], minor=True, inclusive=False)

		if self.spell.get_stat('flies'):
			self.fly_counter += evt.damage
			while self.fly_counter > self.fly_counter_max:
				self.fly_counter -= self.fly_counter_max
				flies = self.spell.get_fae_flies()
				apply_minion_bonuses(self.spell, flies)
				flies.turns_to_death = None
				flies = self.summon(flies)
				if flies:
					self.owner.level.show_path_effect(self.owner, flies, [Tags.Arcane], minor=True, inclusive=False)



class FaehauntGardenSpell(Spell):

	def on_init(self):
		self.name = "Faehaunt Garden"
		self.tags = [Tags.Enchantment, Tags.Arcane, Tags.Nature, Tags.Lightning, Tags.Conjuration]
		self.level = 6
		self.duration = 30
		self.max_charges = 3
		self.duration = 10
		self.minion_duration = 8
		self.range = 0

		example = ButterflyDemon()
		self.minion_health = example.max_hp
		self.minion_range = example.spells[0].range
		self.minion_damage = example.spells[0].damage

		self.upgrades['gnomes'] = (1, 4, "Guardian Gnomes", "Summon 6 electric gnomes on casting faehaunt garden.")
		self.upgrades['flies'] = (1, 4, "Fae Flies", "Summon a Fae Fly Swarm every 15 damage.")
		self.upgrades['glass'] = (1, 4, "Glass Garden", "Summon Glass Butterflies instead of Butterfly Demons.")

	def get_fae_flies(self):
		flies = FlyCloud()
		BossSpawns.apply_modifier(BossSpawns.Faetouched, flies)
		return flies

	def get_gnome(self):
		gnome = Gnome()
		BossSpawns.apply_modifier(BossSpawns.Stormtouched, gnome)
		return gnome

	def fmt_dict(self):
		result = Spell.fmt_dict(self)
		result['lightning_damage'] = result['minion_damage']
		result['arcane_damage'] = self.get_stat('minion_damage', base=9)
		return result

	def get_extra_examine_tooltips(self):
		return [self.spell_upgrades[0], self.get_gnome(), self.spell_upgrades[1], self.get_fae_flies(), self.spell_upgrades[2], GlassButterfly()]

	def get_description(self):
		return ("For [{duration}:duration] turns, whenever you deal 50 or more [lightning] or [arcane] damage, summon a butterfly demon.\n"
				"Butterfly demons fly and have [{minion_health}_HP:minion_health] and [3_SH:shields].\n"
				"Butterfly demons have [lightning] and [arcane] beam attacks which deal [{lightning_damage}_lightning:lightning] and [{arcane_damage}_arcane:damage], both with a range of [{minion_range}_tiles:minion_range]."
				" The arcane beam can melt through walls.\n"
				"Butterfly demons are immune to [lightning], [arcane] and [dark] damage, but take 50% extra damage from [ice] and double damage from [holy].\n"
				"Butterfly demons last [{minion_duration}_turns:minion_duration].").format(**self.fmt_dict())

	def cast_instant(self, x, y):
		self.caster.apply_buff(FaehauntGardenBuff(self), self.get_stat('duration'))

		if self.get_stat('gnomes'):
			for _ in range(self.get_stat('num_summons', base=6)):
				gnome = self.get_gnome()
				apply_minion_bonuses(self, gnome)
				self.summon(gnome)

class DisintegrationCascadeBuff(Buff):

	def __init__(self, spell):
		Buff.__init__(self)
		self.name = "Disintegrator"
		self.buff_type = BUFF_TYPE_BLESS
		self.color = Tags.Arcane.color
		self.counter = 0
		self.counter_max = 30
		self.global_triggers[EventOnDamaged] = self.on_damaged
		self.spell = spell

	def on_damaged(self, evt):

		if evt.damage_type not in [Tags.Arcane, Tags.Dark]:
			return

		self.counter += evt.damage
		while self.counter > self.counter_max:
			self.counter -= self.counter_max
			enemies = [u for u in self.owner.level.units if are_hostile(u, self.owner)]
			for e in enemies:
				e.deal_damage(1, Tags.Physical, self)

class DisintegrationCascadeSpell(Spell):

	def on_init(self):
		self.name = "Disintegration Cascade"
		self.tags = [Tags.Dark, Tags.Arcane, Tags.Enchantment]
		self.duration = 30
		self.max_charges = 3
		self.level = 5
		self.range = 0

	def get_description(self):
		return "For [{duration}_turns:duration], whenever 30 [dark] or [arcane] damage is dealt to an enemy, all enemies take 1 [physical] damage.".format(**self.fmt_dict())

	def cast_instant(self, x, y):
		self.caster.apply_buff(DisintegrationCascadeBuff(self), self.get_stat('duration'))		

class FurnaceOfSorceryBuff(Buff):

	def __init__(self, spell):
		self.spell = spell
		Buff.__init__(self)

	def on_init(self):

		self.global_triggers[EventOnDamaged] = self.on_damage
		self.counter = 0
		self.counter_max = 100
		self.description = "Spawn a furnace hound for every 100 damage you deal with [sorcery]."

		self.imp_counter = 0
		self.imp_counter_max = 30

	def on_damage(self, evt):
		if not evt.source:
			return

		if not hasattr(evt.source, 'tags'):
			return

		if Tags.Sorcery not in evt.source.tags:
			return

		self.counter += evt.damage
		self.owner.level.show_effect(self.owner.x, self.owner.y, Tags.Fire)

		while self.counter >= self.counter_max:
			self.counter -= self.counter_max
			hound = FurnaceHound()
			apply_minion_bonuses(self.spell, hound)
			hound.buffs[1].radius = self.spell.get_stat('radius')

			if self.spell.get_stat('lasers'):
				grant_minion_spell(MagicMissile, hound, self.spell.caster, cool_down=4)

			hound = self.summon(hound, sort_dist=False)
			if hound:
				self.owner.level.show_path_effect(self.owner, hound, [Tags.Dark, Tags.Fire], minor=True)

		if self.spell.get_stat('smithy'):
			self.imp_counter += evt.damage

			while self.imp_counter >= self.imp_counter_max:
				self.imp_counter -= self.imp_counter_max
				imp = CopperImp()
				apply_minion_bonuses(self.spell, imp)

				imp = self.summon(imp, sort_dist=False)
				if imp:
					self.owner.level.show_path_effect(self.owner, imp, [Tags.Dark, Tags.Lightning], minor=True)



class FurnaceOfSorcerySpell(Spell):

	def on_init(self):
		self.name = "Furnace of Sorcery"
		self.tags = [Tags.Sorcery, Tags.Metallic, Tags.Conjuration]
		self.level = 6

		self.must_target_empty = True
		self.must_target_walkable = True
		self.max_charges = 1

		example = FurnaceHound()

		self.minion_damage = example.spells[0].damage
		self.minion_range = example.spells[1].range
		self.minion_health = example.max_hp
		self.radius = 4

		self.upgrades['flames'] = (1, 5, "Flames of Sorcery", "The furnace can cast your Flame Burst spell on a 5 turn coodlown.")
		self.upgrades['smithy'] = (1, 4, "Imp Smithy", "The furnace also produces an Copper Imp every 30 damage.")
		self.upgrades['lasers'] = (1, 6, "Arcane Eyebolts", "The hounds can cast your magic missile spell on a 4 turn cooldown.")

	# Do not show radius on targeting
	def get_impacted_tiles(self, x, y):
		if self.get_stat('flames'):
			fake_spell = FlameBurstSpell()
			return [p for stage in Burst(self.caster.level, Point(x, y), fake_spell.get_stat('radius')) for p in stage]

		return [Point(x, y)]

	def get_extra_examine_tooltips(self):
		return [FurnaceHound(), self.spell_upgrades[0], self.spell_upgrades[1], CopperImp(), self.spell_upgrades[2]]

	def get_description(self):
		return ("Summons a crucible of pain which summons furnace hounds whenever you deal 100 damage with [sorcery].\n"
				"Furnace hounds have a [{minion_damage}_damage:damage] leap attack with a [{minion_range}_tile:minion_range] range, a [1_fire:fire] damage aura with a [{radius}_tile:radius] radius, and deal [4_fire:fire] damage to enemies that attack them in melee.\n"
				"Furnace hounds are immune to [fire] and [lightning] damage, and take half damage from [physical] and [dark].\n"
				"Furnace hounds take double damage from [holy] and 50% extra damage from [ice].\n").format(**self.fmt_dict())

	def cast_instant(self, x, y):
		crucible = Idol()
		crucible.tags.append(Tags.Metallic)
		crucible.name = "Furnace of Sorcery"
		crucible.asset_name = "crucible_of_pain_idol"
		crucible.buffs.append(FurnaceOfSorceryBuff(self))

		apply_minion_bonuses(self, crucible)

		if self.get_stat('flames'):
			burst = grant_minion_spell(FlameBurstSpell, crucible, self.caster, cool_down=5)

		self.summon(crucible, target=Point(x, y))

class GoldSkullSummonSpell(Spell):

	def on_init(self):
		self.name = "Golden Skull"
		self.tags = [Tags.Dark, Tags.Holy, Tags.Metallic, Tags.Conjuration]
		self.level = 5
		self.max_charges = 2

		example = GoldSkull()

		self.minion_damage = example.spells[0].damage
		self.minion_range = example.spells[0].range
		self.minion_health = example.max_hp
		self.heal = example.spells[1].heal

		self.upgrades['ghost_ball'] = (1, 6, "Ghost Caller", "The Golden Skull gains your Ghostball spell with a 6 turn cooldown")
		self.upgrades['wheel'] = (1, 5, "Bone Wheel", "The Golden Skull gains your Wheel of Death spell with a 12 turn cooldown")
		self.upgrades['bloodshift'] = (1, 4, "Blood Skull", "The Golden Skull gians your Bloodshift spell with a 3 turn cooldown")

	def get_extra_examine_tooltips(self):
		return [self.skull()] + self.spell_upgrades

	def skull(self):
		skull = GoldSkull()
		apply_minion_bonuses(self, skull)

		if self.get_stat('ghost_ball'):
			grant_minion_spell(CallSpirits, skull, self.caster, cool_down=6)
		if self.get_stat('wheel'):
			grant_minion_spell(WheelOfFate, skull, self.caster, cool_down=12)
		if self.get_stat('bloodshift'):
			grant_minion_spell(Bloodshift, skull, self.caster, cool_down=3)		

		return skull

	def get_description(self):
		return ("Summons a golden skull.\n"
				"Golden skulls are teleporting, floating, shielded stationary units.\n"
				"Golden skulls have a [holy] beam attack and a single target healing spell.\n").format(**self.fmt_dict())

	def cast_instant(self, x, y):
		skull = self.skull()

		self.summon(skull, target=Point(x, y))

class ScaleHarvestUpgrade(Upgrade):

	def on_init(self):
		self.name = "Scale Harvest"
		self.description = "For every 6 allied dragons that die, gain a charge of Wyrm Eggs."
		self.level = 4
		self.global_triggers[EventOnDeath] = self.on_death
		self.global_triggers[EventOnUnitAdded] = self.on_unit_added
		self.deaths = 0
		self.threshold = 6

	def on_unit_added(self, evt):
		if evt.unit.is_player_controlled:
			self.deaths = 0

	def on_death(self, evt):
		if Tags.Dragon in evt.unit.tags and not are_hostile(evt.unit, self.owner):
			self.deaths += 1
		while self.deaths >= self.threshold:
			self.deaths -= self.threshold
			wyrm_eggs = self.owner.get_spell(WyrmEggs)
			wyrm_eggs.cur_charges = min(wyrm_eggs.cur_charges + 1, wyrm_eggs.get_stat('max_charges'))

class WyrmEggs(Spell):

	def on_init(self):
		self.name = "Wyrm Eggs"
		self.tags = [Tags.Fire, Tags.Ice, Tags.Dragon, Tags.Conjuration]
		self.level = 7
		self.max_charges = 1
		
		self.range = 5
		self.requires_los = False

		self.num_summons = 4

		example = IceWyrm()
		
		self.breath_damage = 7

		self.minion_health = example.max_hp

		self.minion_damage = example.spells[1].damage
		self.duration = example.spells[0].duration
		self.minion_range = example.spells[0].range

		self.upgrades['magic_eggs'] = (1, 4, "Magic Eggs", "Fire eggs cast your Fireball on a 3 turn cooldown, and Ice eggs cast your Icicle on a 3 turn cooldown.")
		self.add_upgrade(ScaleHarvestUpgrade())
		self.upgrades['radiant_eggs'] = (1, 5, "Radiant Eggs", "Wyrm Eggs gain a 1 damage [3_radius:radius] aura of their element type.")

	def get_description(self):
		return ("Summons [{num_summons}:num_summons] Wyrm eggs near the caster.\n"
				"Upon death, these eggs hatch into Wyrms.\n"
				"Wyrms have [{minion_health}_HP:minion_health], and regenerate 8 HP per turn.\n"
				"Each wyrm is either a [fire] or an [ice] wyrm, being immune to its own element, but taking 50% extra damage from the other.\n"
				"The wyrms have melee trample attacks dealing [{minion_damage}_physical:physical] damage and breath attacks that deal [{breath_damage}_damage:damage] of the appropriate type.\n"
				"The ice wyrm breath weapon freeze units in the affected area for [{duration}_turns:duration].\n").format(**self.fmt_dict())

	def fmt_dict(self):
		result = Spell.fmt_dict(self)
		result['breath_damage'] = result['minion_damage'] - 7
		return result


	def cast(self, x, y):
		for i in range(self.get_stat('num_summons')):
			rand_type = random.choice([FireWyrmEgg, IceWyrmEgg])
			egg = rand_type()
			if self.get_stat('magic_eggs'):
				if rand_type == FireWyrmEgg:
					grant_minion_spell(FireballSpell, egg, self.caster, cool_down=3)
				else:
					grant_minion_spell(Icicle, egg, self.caster, cool_down=3)
			
			if self.get_stat('radiant_eggs'):
				buff = DamageAuraBuff(damage=1, damage_type=Tags.Fire, radius=self.get_stat('radius', base=3))
				if rand_type == IceWyrmEgg:
					buff.damage_type = Tags.Ice
				egg.apply_buff(buff)
			
			apply_minion_bonuses(self, egg)
			self.summon(egg, radius=4, sort_dist=False)
			yield

class DeathchillConjuringBuff(Buff):

	def __init__(self, spell):
		Buff.__init__(self)
		self.spell = spell

	def on_init(self):
		self.name = "Deathchill Gate"
		self.buff_type = BUFF_TYPE_BLESS
		self.color = Tags.Dark.color
		self.global_triggers[EventOnDamaged] = self.on_damage

		self.ice = 0
		self.dark = 0
		self.threshold = 50

	def get_description(self):
		return "%d ice damage dealt, %d dark damage dealt" % (self.ice, self.dark)

	def on_damage(self, evt):
		if not are_hostile(evt.unit, self.owner):
			return

		if evt.damage_type == Tags.Ice:
			self.ice += evt.damage

		if evt.damage_type == Tags.Dark:
			self.dark += evt.damage

		while self.ice > 25 and self.dark > 25:
			chimera = DeathchillChimera()

			apply_minion_bonuses(self.spell, chimera)
			self.summon(chimera, radius=4, sort_dist=False)

			self.ice -= 25
			self.dark -= 25

class DeathchillConjuringSpell(Spell):

	def on_init(self):
		self.name = "Deathchill Gate"
		self.tags = [Tags.Dark, Tags.Ice, Tags.Conjuration, Tags.Enchantment]
		self.level = 4
		self.max_charges = 2
		self.duration = 15
		self.range = 0


		example = DeathchillChimera()
		
		self.minion_damage = example.spells[0].damage
		self.minion_health = example.max_hp
		self.minion_range = example.spells[0].range

		self.upgrades['duration'] = (3, 2)
		self.upgrades['max_charges'] = (2, 3)

	def get_description(self):
		return ("For [{duration}_turns:duration], whenever you deal 25 [dark] and 25 [ice] damage, summon a deathchill chimera.\n"
				"Deathchill chimera have [{minion_health}_HP:minion_health].\n"
				"Deathchill chimera have ranged [dark] and [ice] attacks, each dealing [{minion_damage}_damage:damage] with a range of [{minion_range}_tiles:range].\n"
				"Deathchill chimera are 75% resistant to [ice] and [dark] damage, can fly, and split into a Death Snake and an Ice Lion on death."
			).format(**self.fmt_dict())

	def cast_instant(self, x, y):
		self.owner.apply_buff(DeathchillConjuringBuff(self), self.get_stat('duration'))

class AetherBlade(Upgrade):

	def on_init(self):
		self.name = "Aether Blade"
		self.description = "Whenever you cast a [Translocation] spell, gain a charge of Moon Glaive."
		self.global_triggers[EventOnSpellCast] = self.on_cast
		self.level = 3

	def on_cast(self, evt):
		if not evt.spell.caster == self.owner:
			return

		if not Tags.Translocation in evt.spell.tags:
			return

		if self.prereq.cur_charges >= self.prereq.get_stat('max_charges'):
			return

		self.prereq.cur_charges += 1


class MoonGlaiveBuff(Buff):

	def __init__(self, spell, unit):
		self.spell = spell
		self.unit = unit
		Buff.__init__(self)

	def on_init(self):
		self.buff_type = BUFF_TYPE_BLESS
		self.stack_type = STACK_INTENSITY
		self.name = "Moon Glaive"
		self.color = Tags.Arcane.color

	def on_unapplied(self):
		
		if not self.owner.is_alive():
			return

		origin = Point(self.unit.x, self.unit.y)
		self.unit.kill()
		# deal damage along the beam and show proj effect
		for p in self.spell.caster.level.get_points_in_line(origin, self.owner)[:-1]:
			self.spell.caster.level.projectile_effect(p.x, p.y, proj_name='moon_glaive', proj_dest=self.spell.caster, proj_origin=origin)
	
			if self.spell.caster.level.get_unit_at(p.x, p.y):
				self.spell.caster.level.deal_damage(p.x, p.y, self.spell.get_stat('damage'), Tags.Arcane, self)
				self.spell.caster.level.deal_damage(p.x, p.y, self.spell.get_stat('damage'), Tags.Physical, self)
			else:
				self.spell.caster.level.show_effect(p.x, p.y, Tags.Arcane, minor=True)
				
		self.owner.remove_buff(self)


class MoonGlaive(Spell):

	def on_init(self):
		self.name = "Moon Glaive"

		self.tags = [Tags.Metallic, Tags.Arcane, Tags.Sorcery]
		self.level = 2

		self.max_charges = 12
		self.range = 9
		self.damage = 7

		self.upgrades['los_damage'] = (1, 4, "Glimmerblade", "Deals [1_arcane:arcane] damage to all enemies in LOS of the target.  This damage is fixed and cannot be buffed.")
		self.upgrades['lightning_damage'] = (1, 4, "Electroblade", "Deals [7_lightning:lightning] damage to up to 3 enemies near the blade's destination.")
		self.upgrades['recharge'] = (1, 3, "Steelshaping", "Regain a charge of another random Metallic spell.")
		#self.add_upgrade(AetherBlade())

		self.must_target_empty = True

	def get_impacted_tiles(self, x, y):
		for p in self.caster.level.get_points_in_line(self.caster, Point(x, y))[1:]: 
			yield p

	def cast(self, x, y, returning=False):

		# deal damage along the beam and show proj effect
		damaged_units = set()
		for p in self.caster.level.get_points_in_line(self.caster, Point(x, y))[1:]:
			self.caster.level.projectile_effect(p.x, p.y, proj_name='moon_glaive', proj_origin=self.caster, proj_dest=Point(x, y))
			yield
			if self.caster.level.get_unit_at(p.x, p.y):
				damaged_units.add(self.caster.level.get_unit_at(p.x, p.y))
				self.caster.level.deal_damage(p.x, p.y, self.get_stat('damage'), Tags.Arcane, self)
				yield
				self.caster.level.deal_damage(p.x, p.y, self.get_stat('damage'), Tags.Physical, self)
			else:
				self.caster.level.show_effect(p.x, p.y, Tags.Arcane, minor=True)
			if self.get_stat('los_damage'):
				possible_targets = self.caster.level.get_units_in_los(p)
				possible_targets = [t for t in possible_targets if are_hostile(t, self.caster)]
				#prevent Glimmerblade from damaging the same enemy multiple times
				possible_targets = [t for t in possible_targets if not t in damaged_units]
				
				for target in possible_targets:
					damaged_units.add(self.caster.level.get_unit_at(target.x, target.y))
					self.caster.level.deal_damage(target.x, target.y, self.get_stat('los_damage'), Tags.Arcane, self)

		if self.get_stat('lightning_damage'):
			possible_targets = self.caster.level.get_units_in_ball(Point(x, y), 2)
			possible_targets = [t for t in possible_targets if are_hostile(t, self.caster)]
			for i in range(3):
				if possible_targets:
					target = random.choice(possible_targets)
					possible_targets.remove(target)
					self.caster.level.deal_damage(target.x, target.y, self.get_stat('damage'), Tags.Lightning, self)

		if self.get_stat('recharge'):
			valid_spells = [s for s in self.caster.spells if Tags.Metallic in s.tags and s != self]
			valid_spells = [s for s in valid_spells if s.cur_charges < s.get_stat('max_charges')]
			
			if valid_spells:
				affected_spell = random.choice(valid_spells)
				affected_spell.cur_charges += self.get_stat('recharge') #in case we want to change it to more than 1, we can just change the upgrade amt
				affected_spell.cur_charges = min([affected_spell.get_stat('max_charges'), affected_spell.cur_charges])

		# Make unit
		unit = Unit()
		unit.tags = [Tags.Metallic, Tags.Arcane, Tags.Construct]
		unit.name = "Moon Glaive"
		unit.asset_name = "glaive_placeholder"
		unit.max_hp = 16
		for dtype in [Tags.Physical, Tags.Fire, Tags.Ice, Tags.Poison, Tags.Dark, Tags.Holy, Tags.Lightning, Tags.Arcane]:
			unit.resists[dtype] = 100


		unit.stationary = True
		unit.flying = True

		summoned_unit = self.summon(unit, target=(Point(x, y)))
		if not summoned_unit:
			return

		# apply buff
		self.caster.apply_buff(MoonGlaiveBuff(self, unit), duration=2)

	def get_description(self):
		return ("Deals [{damage}_arcane:arcane] and [{damage}_physical:physical] damage in a line to target empty tile."
				"The glaive will linger on the target tile for 1 turn, and return at the end of your next turn, dealing damage again.").format(**self.fmt_dict())


class CarnivalOfPainBuff(Buff):

	def __init__(self, spell):
		self.spell = spell
		Buff.__init__(self)

	def on_init(self):
		self.name = "Carnival of Pain"
		self.global_triggers[EventOnDamaged] = self.on_damage

		self.kills = 0

		self.buff_type = BUFF_TYPE_BLESS
		self.color = Tags.Chaos.color

	def get_description(self):
		self.description = self.spell.get_description()
		
	def on_damage(self, evt):
		if not are_hostile(self.owner, evt.unit):
			return

		if evt.damage_type not in [Tags.Fire, Tags.Physical, Tags.Lightning]:
			return

		self.owner.level.queue_spell(self.do_damage(evt))

	def do_damage(self, evt):
		modifier = 1
		if self.spell.get_stat('death_power') and not evt.unit.is_alive():
			modifier = 2
		targets = [u for u in self.owner.level.units if are_hostile(u, self.owner) and u != evt.unit]

		random.shuffle(targets)
		targets.sort(key=lambda u: distance(u, evt.unit))

		damage_dealt = 0

		for u in targets[:self.spell.get_stat('num_targets')]:
			self.owner.level.show_beam(evt.unit, u, Tags.Dark)
			damage_dealt += u.deal_damage(evt.damage * modifier, Tags.Dark, self.spell)
			if self.spell.get_stat('summon_tormentor') and not u.is_alive():
				self.kills += 1
				if self.kills >= 3:
					self.kills -= 3
					tormentor_spell = self.owner.get_or_make_spell(SummonFieryTormentor)
					for _ in self.owner.level.act_cast(self.spell.caster, tormentor_spell, u.x, u.y, pay_costs=False, queue=False):
						yield
			yield
		
		if self.spell.get_stat('lifesteal'):
			self.spell.caster.deal_damage(-damage_dealt//2, Tags.Heal, self)

class CarnivalOfPain(Spell):

	def on_init(self):

		self.name = "Carnival of Pain"
		self.tags = [Tags.Dark, Tags.Chaos, Tags.Enchantment]
		self.level = 4
		self.max_charges = 2
		self.duration = 4
		self.num_targets = 3

		self.range = 0

		self.kills = 0

		self.upgrades['lifesteal'] = (1, 5, "Lifesteal", "You heal for 50% of all damage dealt by this spell.")
		self.upgrades['death_power'] = (1, 5, "Death Power", "If the damage killed the enemy, the bolt coming out of that enemy deals 2x damage.")
		self.upgrades['summon_tormentor'] = (1, 8, "Torment", "Every 3 kills casts your Fiery Tormentor spell where the slain enemy was.")

	def get_description(self):
		return ("Whenever an enemy takes [physical], [fire], or [lightning] damage, the [{num_targets}:num_targets] nearest enemies take that much dark damage.\n"
				"Lasts [{duration}_turns:duration].").format(**self.fmt_dict())

	def cast_instant(self, x, y):
		self.caster.apply_buff(CarnivalOfPainBuff(self), self.get_stat('duration'))

class DreamwalkBuff(Buff):

	def __init__(self, spell):
		self.spell = spell
		Buff.__init__(self)

	def on_init(self):
		self.name = "Dreamwalking"
		self.buff_type = BUFF_TYPE_BLESS
		self.stack_type = STACK_REPLACE

		if self.spell.get_stat('dream_form'):
			self.resists[Tags.Dark] = 75
			self.resists[Tags.Physical] = 75
			self.resists[Tags.Arcane] = 75
			self.resists[Tags.Holy] = 75

	def on_applied(self, owner):
		self.hp = self.owner.cur_hp
		self.charges = {s: s.cur_charges for s in self.owner.spells}
		self.location = Point(self.owner.x, self.owner.y)

	def on_unapplied(self):

		self.owner.cur_hp = self.hp
		
		if self.spell.get_stat('memory_walk'):
			for s in self.charges:
				if s in self.owner.spells:
					s.cur_charges = self.charges[s]

		if self.location != Point(self.owner.x, self.owner.y):
			tp_point = self.owner.level.get_summon_point(self.location.x, self.location.y, radius_limit=7)
			if tp_point:
				self.owner.level.act_move(self.owner, tp_point.x, tp_point.y, teleport=True)
		else:
			self.owner.level.show_effect(self.owner.x, self.owner.y, Tags.Translocation)

class DreamwalkSpell(Spell):

	def on_init(self):
		self.name = "Dreamwalk"
		self.tags = [Tags.Arcane, Tags.Enchantment, Tags.Translocation]
		self.level = 2
		self.max_charges = 2
		self.range = 0
		self.duration = 5

	def get_description(self):
		return ("Dreamwalk for 5 turns.  Afterwards, you are returned to the location you cast it at, restored to the HP you cast it at.\n"
			    "Casting Dreamwalk while dreamwalk is already active will simply end the current walk.")

		# 3SP upgrade: Memory walk: refund all SP used during dream walk?
		# 2SP upgrade: resist arcane, dark, holy, and physical damage while dreamwalking ('dreamform')

		#self.upgrades['memory_walk'] = (1, 7, "Memory Walk", "When dreamwalk ends, reset all spell charge counts to what they were at the beginning of the walk.")
		self.upgrades['dream_form'] = (1, 3, "Dream Form", "While dreamwalking, gain 75% resistance to [arcane], [dark], [physical], and [holy] damage.")
		self.upgrades['max_charges'] = (2, 4)

	def cast_instant(self, x, y):
		if self.owner.has_buff(DreamwalkBuff):
			self.owner.remove_buffs(DreamwalkBuff)
		else:
			self.owner.apply_buff(DreamwalkBuff(self), self.get_stat('duration'))

class MassCalcification(Spell):

	def on_init(self):
		self.name = "Mass Calcification"
		self.tags = [Tags.Dark, Tags.Enchantment]
		self.level = 4
		self.range = 0
		self.max_charges = 3

		self.upgrades['fae_bones'] = (1, 4, "Fae Bones", "Arcane Allies are raised as fae bone shamblers instead of normal ones.")
		self.upgrades['burning_bones'] = (1, 4, "Burning Bones", "Fire allies are raised as burning bone shamblers instead of normal ones.")
		self.upgrades['bone_shards'] = (1, 5, "Bone Shards", "Each slain ally deals [7_physical:physical] damage to up to [3:num_targets] enemies in line of sight.")

	def get_description(self):
		return "All non undead allies are instantly killed and raised as bone shamblers.\nBone Shamblers have the same HP as the raised units, a quarter that much melee damage, and split into smaller shamblers on death."

	def make_shambler(self, u):
		shambler = BoneShambler(u.max_hp)
		if self.get_stat('fae_bones') and Tags.Arcane in u.tags:
			BossSpawns.apply_modifier(BossSpawns.Faetouched, shambler)
		if self.get_stat('burning_bones') and Tags.Fire in u.tags:
			BossSpawns.apply_modifier(BossSpawns.Flametouched, shambler)
		apply_minion_bonuses(self, shambler)
		return shambler

	def cast(self, x, y):
		units = [u for u in self.owner.level.units if u != self.owner and not are_hostile(u, self.owner) and Tags.Undead not in u.tags]
		random.shuffle(units)
		for u in units:
			self.caster.level.show_path_effect(self.caster, u, Tags.Dark, minor=True, inclusive=False)
			yield
			if self.get_stat('bone_shards'):
				targets = [unit for unit in self.caster.level.get_units_in_los(u) if are_hostile(u, unit)]
				if targets:
					random.shuffle(targets)
					for i in range(min(self.get_stat('num_targets', base=3), len(targets))):
						self.caster.level.show_path_effect(u, targets[i], Tags.Physical, minor=True, inclusive=False)
						targets[i].deal_damage(self.get_stat('damage', base=7), Tags.Physical, self)
					yield
			self.caster.level.show_effect(u.x, u.y, Tags.Dark)
			u.kill()
			shambler = self.make_shambler(u)
			self.summon(shambler, target=u)
			yield

class ScourgeBuff(Stun):

	def __init__(self, spell):
		self.spell = spell
		Stun.__init__(self)

	def on_init(self):		
		self.buff_type = BUFF_TYPE_CURSE
		self.stack_type	= STACK_NONE
		self.name = "Scourged"
		self.color = Tags.Holy.color
		self.asset = ['status', 'stun']  # TODO- own asset
		self.description = "Cannot move or cast spells.  [Holy] damage dealt to all nearby units each turn."
		
		if self.spell.get_stat('refresh_conjuration') or self.spell.get_stat('refresh_dominate'):
			self.owner_triggers[EventOnDeath] = self.on_death

	def on_advance(self):
		for t in self.owner.level.get_tiles_in_ball(self.owner.x, self.owner.y, self.spell.get_stat('radius')):
			self.owner.level.deal_damage(t.x, t.y, self.spell.get_stat('damage'), Tags.Holy, self.spell)

	def on_death(self, evt):
		spell = None
		if self.spell.get_stat('refresh_conjuration'):
			spells = [s for s in self.spell.owner.spells if Tags.Holy in s.tags and Tags.Conjuration in s.tags]
			if spells:
				spell = random.choice(spells)
		elif self.spell.get_stat('refresh_dominate'):
			spell = self.spell.owner.get_spell(Dominate)

		if spell:
			spell.cur_charges += 1
			spell.cur_charges = min(spell.cur_charges, spell.get_stat('max_charges'))

class ScourgeSpell(Spell):

	def on_init(self):
		self.name = "Scourge"
		self.level = 2
		self.max_charges = 9
		self.tags = [Tags.Holy, Tags.Enchantment]
		self.damage = 5
		self.duration = 5
		self.radius = 1

		self.upgrades['refresh_conjuration'] = (1, 3, "Redemption", "When a Scourged enemy dies, gain a charge of a random Holy conjuration.")
		self.upgrades['refresh_dominate'] = (1, 3, "Conversion", "When a Scourged enemy dies, gain a charge of Dominate.")
		self.upgrades['mass_scourge'] = (1, 4, "Mass Scourge", "Scourge is applied to a connected group of enemies.")

		self.range = 6

		self.can_target_empty = False

	def get_impacted_tiles(self, x, y):
		tiles = [Point(x, y)]
		if self.get_stat('mass_scourge'):
			tiles = self.caster.level.get_connected_group_from_point(x, y, ignored_units=[self.caster])
		return tiles

	def get_description(self):
		return ("The target is stunned for [{duration}_turns:duration].\n"
				"Each turn, the target and all units within [{radius}_tiles:radius] take [{damage}_holy:holy] damage.").format(**self.fmt_dict())

	def cast_instant(self, x, y):
		targets = [self.caster.level.get_unit_at(x, y)]
		if self.get_stat('mass_scourge'):
			targets = self.caster.level.get_connected_group_from_point(x, y, ignored_units=[self.caster]) #Currently it's going to scourge allies as well, let me know if you want this to change

		for target in targets:
			if target:
				target.apply_buff(ScourgeBuff(self), self.get_stat('duration'))

class ImmolateBuff(Buff):

	def __init__(self, spell):
		self.spell = spell
		Buff.__init__(self)

	def on_init(self):
		self.name = "Immolated"
		self.buff_type = BUFF_TYPE_CURSE
		self.stack_type = STACK_REPLACE
		self.color = Tags.Fire.color
		self.damage = self.spell.get_stat('damage')
		self.damage_growth = self.spell.get_stat('damage_growth')
		self.asset = ['status', 'burning']

		self.show_effect = False

		if self.spell.get_stat('dragon_soul'):
			self.owner_triggers[EventOnDeath] = self.on_death

	def on_advance(self):
		self.owner.deal_damage(self.damage, Tags.Fire, self.spell)

		if self.spell.get_stat('radiant_heat'):
			for t in self.owner.level.get_tiles_in_ball(self.owner.x, self.owner.y, self.spell.get_stat('radius')):
				u = self.owner.level.get_unit_at(t.x, t.y)

				if not u:
					if random.random() > .7:
						self.owner.level.show_effect(t.x, t.y, Tags.Fire, minor=True)
					continue

				if u == self.owner:
					continue

				if not are_hostile(u, self.spell.caster):
					continue
				
				u.deal_damage(self.damage // 2, Tags.Fire, self.spell)

		self.damage += self.damage_growth

	def on_death(self, evt):
		spells = [s for s in self.spell.caster.spells if Tags.Dragon in s.tags if s.cur_charges < s.get_stat('max_charges') and s.level <= 4]
		if spells:
			spell = random.choice(spells)
			spell.cur_charges += 1


class ImmolateSpell(Spell):

	def on_init(self):
		self.name = "Immolate"
		self.tags = [Tags.Fire, Tags.Enchantment]
		self.level = 2
		self.must_target_empty = False

		self.damage = 3
		self.damage_growth = 3
		self.duration = 8
		self.max_charges = 10

		self.range = 8
		self.radius = 3

		self.stats.append('damage_growth')

		self.upgrades['mass_immolate'] = (1, 3, "Conflaguration", "Immolate also affects a connected group of enemies.")
		self.upgrades['radiant_heat'] = (1, 4, "Radiant Heat", "Immolate deals half damage to units in a [3_tile:radius] radius around the target each turn.")
		self.upgrades['dragon_soul'] = (1, 2, "Dragon Soul", "When an immolated enemy dies, regain a charge of a random level 4 or lower [dragon] spell you know.")

		self.can_target_empty = False

	def get_description(self):
		return ("Target enemy takes [{damage}_fire:fire] damage each turn for [{duration}_turns:duration].\n"
				"This damage increases by [{damage_growth}_damage:damage] each turn.").format(**self.fmt_dict())

	def get_impacted_tiles(self, x, y):

		if self.get_stat('mass_immolate'):

			candidates = set([Point(x, y)])
			unit_group = set()

			while candidates:
				candidate = candidates.pop()
				unit = self.caster.level.get_unit_at(candidate.x, candidate.y)
				if unit and unit not in unit_group:

					if not are_hostile(unit, self.caster):
						continue
					if unit == self.caster:
						continue
					unit_group.add(unit)

					for p in self.caster.level.get_adjacent_points(Point(unit.x, unit.y), filter_walkable=False):
						candidates.add(p)

			return unit_group
		else:
			return [Point(x, y)]

	def cast(self, x, y):

		for p in self.owner.level.get_points_in_line(self.owner, Point(x, y))[1:-1]:
			self.owner.level.show_effect(p.x, p.y, Tags.Fire, minor=True)

		if self.get_stat('mass_immolate'):
			for t in self.get_impacted_tiles(x, y):
				u = self.owner.level.get_unit_at(t.x, t.y)
				if u:
					self.owner.level.show_effect(t.x, t.y, Tags.Immolate)
					u.apply_buff(ImmolateBuff(self), self.get_stat('duration'))
					yield

		else:
			u = self.owner.level.get_unit_at(x, y)
			if not u:
				return

			self.owner.level.show_effect(u.x, u.y, Tags.Immolate)
			u.apply_buff(ImmolateBuff(self), self.get_stat('duration'))
			yield

class ArmageddonArmorBuff(Buff):

	def __init__(self, spell):
		Buff.__init__(self)
		self.spell = spell

	def on_init(self):
		self.name = "Armor of Armageddon"
		self.color = Tags.Chaos.color
		self.description = "25 chaos resist. Damages enemies that damage buffed unit 2 damage per chaos type."

		self.resists[Tags.Fire] = 25
		self.resists[Tags.Lightning] = 25
		self.resists[Tags.Physical] = 25

		self.owner_triggers[EventOnDamaged] = self.on_damaged

	def on_damaged(self, evt):
		if evt.source.owner != self.owner: #self-damaging spells would kill units
			for tag in [Tags.Fire, Tags.Lightning, Tags.Chaos]:
				evt.source.owner.deal_damage(2, tag, self.spell)

class ArmeggedonBlade(Spell):

	def on_init(self):
		self.name = "Armageddon Blade"
		self.tags = [Tags.Chaos, Tags.Metallic, Tags.Enchantment]
		self.level = 4
		self.max_charges = 6

		self.can_target_empty = False

		# Armor of Armeggedon upgrade to give resists?
		armor_upgrade_text = "Grants 25 resist to [fire:fire], [lightning:lightning], and [physical:physical] damage and provides thorns buff that deals 2 damage for each chaos type to enemies that attack buffed units."
		self.upgrades['armor'] = (1, 2, "Armor of Armageddon", armor_upgrade_text)
		self.upgrades['connected_group'] = (1, 5, "Mass Armaments", "Cast on a connected group.")
		self.upgrades['mega'] = (1, 8, "Mega Armageddon", "Provides unit with a melee version of Mega Annihilate instead of Annihilate.")

	def get_description(self):
		return ("Grants target ally a melee version of Annihilate, gaining any bonuses you have to that spell.")

	def cast_instant(self, x, y):

		units = [self.owner.level.get_unit_at(x, y)]
		if self.get_stat('connected_group'):
			units = self.caster.level.get_connected_group_from_point(x, y)
		for unit in units:
			if unit and unit is not self.caster and not are_hostile(unit, self.caster):
				blade = AnnihilateSpell()
				if self.get_stat('mega'):
					blade = MegaAnnihilateSpell()
				blade.statholder = self.owner
				blade.melee = True
				blade.range = 1
				blade.max_charges = 0
				unit.add_spell(blade, prepend=True)
				
				if self.get_stat('armor'):
					buff = ArmageddonArmorBuff(self)
					unit.apply_buff(buff)
				
				self.owner.level.show_effect(unit.x, unit.y, Tags.ArmageddonBlade, speed=2)

class Bonespear(Spell):

	def on_init(self):

		self.name = "Bone Spear"
		self.tags = [Tags.Sorcery, Tags.Blood]
		self.hp_cost = 5

		self.range = 8
		self.damage = 16

		self.level = 2

		self.duration = 3

		self.radius = 3

		self.upgrades['fire'] = (1, 4, "Infernal Spear", "Bone Spear also deals [fire] damage.")
		self.upgrades['toxic'] = (1, 4, "Toxic Spear", "Whenever the spear kills a unit, up to 3 enemy units within a [3_tile:radius] radius take [16_poison:poison] damage.")
		self.upgrades['stun'] = (1, 3, "Stun Spear", "Bone Spear applies stun for 3 turns")

		self.cast_on_walls = True

	def get_impacted_tiles(self, x, y):
		return self.owner.level.get_points_in_line(self.caster, Point(x, y))

	def get_description(self):
		return ("Deals [{damage}_physical:physical] damage to all units in a line.\nThis spell can target and destroy a wall tile.").format(**self.fmt_dict())

	def cast(self, x, y):

		for p in self.caster.level.get_points_in_line(self.caster, Point(x, y))[1:]:
			self.caster.level.projectile_effect(p.x, p.y, proj_name='silver_spear', proj_origin=self.caster, proj_dest=Point(x, y))
			unit = self.caster.level.get_unit_at(p.x, p.y)
			if unit:
				unit.deal_damage(self.get_stat('damage'), Tags.Physical, self)
				if self.get_stat('fire'):
					unit.deal_damage(self.get_stat('damage'), Tags.Fire, self)
				if self.get_stat('stun'):
					unit.apply_buff(Stun(), self.get_stat('duration'))
				if self.get_stat('toxic') and not unit.is_alive():
					candidates = [u for u in self.owner.level.get_units_in_ball(unit, self.get_stat('radius')) if are_hostile(u, self.caster)]
					random.shuffle(candidates)
					for c in candidates[:3]:
						for p in self.owner.level.get_points_in_line(unit, c)[1:-1]:
							self.owner.level.show_effect(p.x, p.y, Tags.Poison, minor=True)
						c.deal_damage(self.get_stat('damage'), Tags.Poison, self)
			
			yield

		if self.owner.level.tiles[x][y].is_wall():
			self.owner.level.make_floor(x, y)
			self.owner.level.show_effect(x, y, Tags.Physical)

class WormOffering(Spell):

	def on_init(self):
		self.name = "Lumbriogenesis"
		self.level = 3
		self.tags = [Tags.Blood, Tags.Nature, Tags.Conjuration]
		self.max_charges = 2
		self.range = 1
		self.melee = True

		self.must_target_empty = True
		self.must_target_walkable = True

		self.target_empty = True

		# TODO:
		# Basic upgrades
		# charges?
		# regen amount?
		# also summon num_summons little wormballs around main worm ball?

		# Ultimate Upgrades
		self.upgrades['toxic'] = (1, 6, "Toxogenesis", "Summons a toxic worm ball instead.  Toxic wormballs have a poison aura.", 'ultimate')
		self.upgrades['iron'] = (1, 5, "Mechanogenesis", "Summons an iron worm ball instead.  Iron wormballs have many resistances.", 'ultimate')
		self.upgrades['ghostly'] = (1, 5, "Ectogenesis", "Summons a ghost worm ball instead.  Ghost wormballs have many resistances, are undead, and teleport.", 'ultimate')

	def get_description(self):
		return ("Sacrifice half your HP rounded up and summon a wormball with that much hp.\n"
				"Wormballs regenerate 3 HP per turn and have a melee attack dealing damage equal to half their max HP.\n"
				"If you sacrificed 50 or more hp, summon a worm shambler instead of a worm ball.\n")

	def cast_instant(self, x, y):
		hp = self.caster.cur_hp // 2

		if not hp:
			return

		self.caster.cur_hp -= hp
		self.caster.level.event_manager.raise_event(EventOnSpendHP(self.caster, hp), self.caster)

		if self.get_stat('toxic'):
			unit = WormBallToxic(hp)
		elif self.get_stat('iron'):
			unit = WormBallIron(hp)
		elif self.get_stat('ghostly'):
			unit = WormBallGhostly(hp)
		else:
			unit = WormBall(hp)

		apply_minion_bonuses(self, unit)
		self.summon(unit, target=Point(x, y))

		self.owner.level.show_effect(self.caster.x, self.caster.y, Tags.Blood)

class HagSummon(Spell):

	def on_init(self):

		self.name = "Night Hag"
		self.level = 5
		self.hp_cost = 30
		self.max_charges = 3
		self.requires_los = False
		self.range = 5
		self.tags = [Tags.Blood, Tags.Dark, Tags.Conjuration]

		# Todo- drain not getting minion dmg bonus

		self.upgrades["bone_spear"] = (1, 5, "Spear Hag", "The Night Hag gains your Bone Spear spell on a 4 turn cooldown")
		self.upgrades["nightmare"] = (1, 4, "Nightmare Hag", "The Night hag can cast your Nightmare Aura spell")
		self.upgrades["bone_lady"] = (1, 6, "Bone Queen", "The Night Hag gains the ability to summon small bone shamblers")

	def bone_shambler(self):
		shambler = BoneShambler(8)
		apply_minion_bonuses(self, shambler)
		return shambler

	def hag(self):
		hag = NightHag()
		apply_minion_bonuses(self, hag)

		if self.get_stat('bone_spear'):
			grant_minion_spell(Bonespear, hag, self.caster, 4)

		if self.get_stat('nightmare'):
			grant_minion_spell(NightmareSpell, hag, self.caster, 30)

		if self.get_stat('bone_lady'):
			summon = SimpleSummon(self.bone_shambler, cool_down=4, num_summons=2 + self.get_stat('num_summons'))
			hag.spells.insert(0, summon)

		return hag

	def get_description(self):
		return ("Summon a Night Hag.\n"
				"Night Hags can summon ghosts and drain HP from all living units in line of sight when they are wounded.\n")

	def get_extra_examine_tooltips(self):
		return [self.hag()] + self.spell_upgrades

	def cast_instant(self, x, y):
		hag = self.hag()
		apply_minion_bonuses(self, hag)
		self.summon(hag, Point(x, y))

class BloodGolemVampirism(Buff):

	def on_init(self):
		self.name = "Blood Golem Vampirism"
		self.description = "Half of all damage dealt is converted to healing, and then redirected and redistributed to all [living] allies"
		self.global_triggers[EventOnDamaged] = self.on_damage

	def on_damage(self, evt):
		if not evt.source:
			return

		if evt.source.owner != self.owner:
			return

		if evt.damage_type == Tags.Heal:
			return

		# Should redistribute via the other golem buff, and even use the weird remainder math
		self.owner.deal_damage(-evt.damage // 2, Tags.Heal, self)

class BloodGolemBuff(Buff):

	def on_init(self):
		self.name = "Blood Bond"
		self.description = "All damage taken is redirected and redistributed to all [living] allies"
		self.owner_triggers[EventOnPreDamaged] = self.pre_damage

	def pre_damage(self, evt):
		# Block the damage
		self.owner.shields += 1

		# ..but redeal it to all allies
		allies = [u for u in self.owner.level.units if Tags.Living in u.tags and not are_hostile(self.owner, u)]
		
		divisor = max(1, len(allies))
		to_dist = evt.damage // divisor
		remainder = evt.damage % divisor

		# Makes sure every point is distributed- for instance distributing 3 damage amongst 5 enemies should deal 1 damage to 3 random allies
		remainder_recievers = list(allies)
		random.shuffle(remainder_recievers)
		remainder_recievers = set(remainder_recievers[:remainder])

		for a in allies:
			dmg = to_dist
			if a in remainder_recievers:
				dmg += 1
			if not dmg:
				continue

			a.deal_damage(dmg, evt.damage_type, evt.source)
			for p in self.owner.level.get_points_in_line(a, self.owner)[1:]:
				self.owner.level.show_effect(p.x, p.y, Tags.Dark, minor=True)

class BloodGolemSpell(Spell):

	def on_init(self):
		self.name = "Blood Golem"
		self.minion_damage = 25
		self.tags = [Tags.Metallic, Tags.Blood, Tags.Conjuration]
		self.level = 4
		self.max_charges = 1
		self.hp_cost = 9
		self.color = Tags.Blood.color

		self.upgrades['pain_aura'] = (1, 4, "Pain Aura", "The Blood Golem gains a [5_tile:radius] [poison] and [fire] damage aura.")
		self.upgrades['super_thorns'] = (1, 3, "Greater Thorns", "The Blood Golems thorns damage is increased by its minion damage stat.")
		self.upgrades['vampirism'] = (1, 5, "Vampire Golem", "Whenever the Blood Golem deals damage, half that much healing is distributed amongst its [living] allies.")

	def get_description(self):
		return 	("Summon a Blood Golem.\n"
				 "The golem never takes damage, instead redistributing damage to its master and any [living] allies.\n"
				 "The Golem has a [25_physical:physical] damage melee attack, and thorns which deal 7 [physical] damage to units that attack the golem in melee.")

	def get_extra_examine_tooltips(self):
		return [self.BloodGolem()] + self.spell_upgrades

	def BloodGolem(self):

		unit = Unit()
		unit.tags = [Tags.Construct, Tags.Metallic, Tags.Blood]
		unit.max_hp = 50

		for t in damage_tags:
			unit.resists[t] = 0

		unit.name = 'Blood Golem'
		unit.asset_name = 'golem_blood'

		unit.buffs.append(BloodGolemBuff())
		
		thorns_damage = 7
		if self.get_stat('super_thorns'):
			thorns_damage += self.get_stat('minion_damage')
		
		unit.buffs.append(Thorns(thorns_damage))

		if self.get_stat('pain_aura'):
			radius = 5 + self.get_stat('radius')
			aura = DamageAuraBuff(damage=2, damage_type=[Tags.Poison, Tags.Fire], radius=radius)
			unit.buffs.append(aura)

		unit.spells.append(SimpleMeleeAttack(self.get_stat('minion_damage')))

		if self.get_stat('vampirism'):
			unit.buffs.append(BloodGolemVampirism())

		return unit

	def cast_instant(self, x, y):
		golem = self.BloodGolem()
		apply_minion_bonuses(self, golem)
		self.summon(golem, target=Point(x, y))

class BloodTapDebuff(Buff):

	def __init__(self, spell):
		self.spell = spell
		Buff.__init__(self)

	def on_init(self):
		self.buff_type = BUFF_TYPE_CURSE
		self.name = "Lifedrain"
		self.color = Tags.Blood.color
		self.asset = ["status", "blood_tap"]

	def on_advance(self):
		for p in self.owner.level.get_points_in_line(self.owner, self.spell.caster)[1:-1]:
			self.owner.level.show_effect(p.x, p.y, Tags.Blood, minor=True)
		
		dmg = self.owner.deal_damage(self.spell.get_stat('damage'), Tags.Dark, self.spell)
		if dmg:
			self.spell.caster.deal_damage(-dmg, Tags.Heal, self.spell)

			# Blood bond healing
			if self.spell.get_stat('bond'):
				potential_targets = [u for u in self.owner.level.units if Tags.Living in u.tags and not are_hostile(self.spell.caster, u)]
				random.shuffle(potential_targets)
				for u in potential_targets[:self.spell.get_stat('num_targets')]:
					u.deal_damage(-dmg, Tags.Heal, self.spell)

		# Chain targets
		if self.spell.get_stat('chain'):
			potential_targets = self.owner.level.get_units_in_ball(self.owner, self.spell.get_stat('radius'))
			potential_targets = [t for t in potential_targets if are_hostile(self.spell.caster, t) and t != self.owner]
			random.shuffle(potential_targets)

			for u in potential_targets[:self.spell.get_stat('num_targets')]:
				for p in self.owner.level.get_points_in_line(self.owner, u)[1:-1]:
					self.owner.level.show_effect(p.x, p.y, Tags.Blood, minor=True)

				dmg = u.deal_damage(self.spell.get_stat('damage'), Tags.Dark, self)
				if dmg:
					self.spell.caster.deal_damage(-dmg, Tags.Heal, self.spell)
		
		

class BloodTapSpell(Spell):

	def on_init(self):
		self.name = "Lifedrain"
		self.tags = [Tags.Blood, Tags.Dark, Tags.Enchantment]
		self.level = 1
		self.hp_cost = 1

		self.max_charges = 20

		self.duration = 15
		self.damage = 3

		self.range = 6

		# Only for Chain Drain and Blood Bond, but used for those
		self.num_targets = 2
		self.radius = 3

		self.upgrades['bond'] = (1, 4, "Blood Bond", "Lifedrain also heals 2 random [living] allies.", "ultimate")
		self.upgrades['chain'] = (1, 4, "Life Funnel", "Lifedrain also drains life from 2 random enemy units up to 3 tiles away from the target.", "ultimate")
		self.upgrades['requires_los'] = (-1, 2, "Blindcasting", "Lifedrain can be cast without line of sight")
		
		self.stacking = 0

		# Mass Lifedrain: Apply in a 3x3 area
		# Soul Drain: If a unit dies under the effect of lifedrain, regain a charge of life drain
		self.can_target_empty = False

	def get_impacted_tiles(self, x, y):
		if not self.get_stat('chain'):
			return [Point(x, y)]
		else:
			return Spell.get_impacted_tiles(self, x, y)

	def get_description(self):
		return ("Deals [{damage}_dark:dark] damage to target unit each turn for [{duration}_turns:duration], healing the caster for the same amount.").format(**self.fmt_dict())

	def cast_instant(self, x, y):
		for p in self.owner.level.get_points_in_line(self.caster, Point(x, y)):
			self.owner.level.show_effect(p.x, p.y, Tags.Blood, minor=True)
		u = self.owner.level.get_unit_at(x, y)
		if u:
			debuff = BloodTapDebuff(self)
			if self.stacking:
				debuff.stack_type = STACK_INTENSITY
			u.apply_buff(debuff, self.get_stat('duration'))  

	def get_ai_target(self):
		potentials = [u for u in self.owner.level.units if self.can_cast(u.x, u.y) and are_hostile(u, self.caster)]
		if potentials:
			return random.choice(potentials)

	def can_threaten(self, x, y):
		return distance(self.caster, Point(x, y)) < self.get_stat('range') and self.caster.level.can_see(self.caster.x, self.caster.y, x, y)

class RitualOfRevelation(Spell):

	def on_init(self):
		self.name = "Ritual of Revelation"
		self.tags = [Tags.Holy, Tags.Blood]
		self.level = 8
		self.max_charges = 1
		self.hp_cost = 77

		self.max_channel = 7

		self.range = 0

		self.num_summons = 7
		self.num_targets = 3

		# Mechanic - summon ever increasing numbers of false prophets, then holy blast all enemies in LOS after duration finishes

		# upgrades:
		#  Start by summoning 2 seraphs?
		#  Each turn shoot holy blast at nearest enemy?
		#  num summons?

		self.upgrades['num_summons'] = (4, 7, "Holy Horde")
		self.upgrades['blasphemy'] = (1, 5, "Blasphemy", "Summoned Prophets are liches.")
		self.upgrades['arcane_revelation'] = (1, 8, "Arcane Revelation", "Also casts your Blazerip on [3:num_targets] enemies.")


	def get_description(self):
		return ("Channel the Ritual of Revelation for [{max_channel}_turns:duration].\n"
				"Each turn while you channel the ritual, Holy Fire will be cast for free on [{num_targets}:num_targets] enemy units in line of sight.\n"
				"If not enough enemy units are in line of sight, allies will be targeted as well.\n"
				"Units will never be targeted more than once."
				"When the channel is complete, [{num_summons}:num_summons] False Prophets will be summoned.").format(**self.fmt_dict())

	def cast(self, x, y, channel_cast=False):
		if not channel_cast:
			self.owner.apply_buff(ChannelBuff(self.cast, Point(x, y)), self.get_stat('max_channel'))
			return

		holy_fire = self.owner.get_spell(HolyFlame)
		if not holy_fire:
			holy_fire = HolyFlame()
			holy_fire.caster = self.caster
			holy_fire.owner = self.caster

		targets = [u for u in self.caster.level.units if are_hostile(self.caster, u) and self.caster.level.can_see(self.caster.x, self.caster.y, u.x, u.y)]
		random.shuffle(targets)
		targets = targets[:self.get_stat('num_targets')]

		missing_targets = self.get_stat('num_targets') - len(targets)
		if len(targets) < self.get_stat('num_targets'):
			extra_targets = [u for u in self.caster.level.units if not are_hostile(self.caster, u) and self.caster.level.can_see(self.caster.x, self.caster.y, u.x, u.y)]
			random.shuffle(extra_targets)
			extra_targets = extra_targets[:missing_targets]
			targets.extend(extra_targets)

		for u in targets:
			for p in self.owner.level.get_points_in_line(self.owner, u)[1:-1]:
				self.owner.level.show_effect(p.x, p.y, Tags.Holy, minor=True)
			self.owner.level.act_cast(self.caster, holy_fire, u.x, u.y, pay_costs=False)
			yield

		if self.get_stat('arcane_revelation'):
			targets = [u for u in self.caster.level.get_units_in_los(self.caster) if are_hostile(u, self.caster)]
			if targets:
				random.shuffle(targets)
				for i in range(min(self.get_stat('num_targets'), len(targets))):
					for _ in self.caster.level.act_cast(self.caster, self.caster.get_or_make_spell(Blazerip), targets[i].x, targets[i].y, pay_costs=False, queue=False):
						yield
		
		# Final turn
		if not self.owner.has_buff(ChannelBuff):

			for i in range(self.get_stat('num_summons')):
				unit = FalseProphet()
				if self.get_stat('blasphemy'):
					BossSpawns.apply_modifier(BossSpawns.Lich, unit)
				apply_minion_bonuses(self, unit)
				self.summon(unit, radius=7)
				yield



class DevourFlesh(Spell):

	def on_init(self):
		self.tags = [Tags.Blood]
		self.name = "Devour Flesh"
		self.max_charges = 4
		self.level = 3
		self.range = 1
		self.melee = True

		self.upgrades['control'] = (1, 1, "Controlled Appetite", "Instead of killing the target, only steal as much HP as you are missing.")
		self.upgrades['heal_allies'] = (1, 2, "Mass Feeding", "Also heal allies in a 2 tile radius.") #same value?
		self.upgrades['charred_flesh'] = (1, 5, "Charred Flesh", "Slain Living units are raised as Burning Skeletons.") #Added Living requirement due to raise_skeleton(), can change to normal summon to remove req

	def get_description(self):
		return "Devour an allied [living] unit to heal yourself for its current hp."

	def can_cast(self, x, y):
		unit = self.owner.level.get_unit_at(x, y)
		if not unit:
			return False
		if are_hostile(unit, self.caster):
			return False
		if not Tags.Living in unit.tags:
			return False
		return Spell.can_cast(self, x, y)

	def cast_instant(self, x, y):
		unit = self.owner.level.get_unit_at(x, y)
		if not unit:
			return False

		healing_dealt = 0
		max_steal = self.caster.max_hp - self.caster.cur_hp
		if max_steal < unit.cur_hp and self.get_stat('control'):
			unit.cur_hp -= max_steal
			healing_dealt = self.owner.deal_damage(-max_steal, Tags.Heal, self)

		else:
			healing_dealt = self.owner.deal_damage(-unit.cur_hp, Tags.Heal, self)

			self.owner.level.show_effect(unit.x, unit.y, Tags.Physical)

			unit.kill()

		if self.get_stat('heal_allies'):
			elligible_units = [u for u in self.caster.level.get_units_in_ball(Point(x, y), 2) if u != self.caster and not are_hostile(self.caster, u)]
			for u in elligible_units:
				self.caster.level.deal_damage(u.x, u.y, healing_dealt, Tags.Heal, self)
		
		if unit and not unit.is_alive() and self.get_stat('charred_flesh'):
			s = raise_skeleton(self.caster, unit, source=self)
			if s:
				BossSpawns.apply_modifier(BossSpawns.Flametouched, s)

class Bloodshift(Spell):

	def on_init(self):
		self.name = "Bloodshift"
		
		self.tags = [Tags.Blood, Tags.Dark, Tags.Sorcery]
		
		self.range = 6
		self.radius = 4
		
		self.max_charges = 9
		self.hp_cost = 8

		self.level = 3

		self.damage = 18

		self.upgrades['radius'] = (2, 4)
		self.upgrades['damage'] = (13, 3)
		self.upgrades['max_charges'] = (5, 2)
		self.upgrades['range'] = (3, 2)
		self.upgrades['toxicity'] = (1, 4, "Toxic Shift", "Bloodshift also deals [poison] damage, though this damage does not cause healing.")

	def get_description(self):
		return ("Enemies in a [{radius}_tile:radius] burst take [{damage}_dark:dark] damage.\n"
				"Whenever an enemy is dealt damage this way, you or a random wounded ally in the targeted area is healed for half that amount.\n").format(**self.fmt_dict())

	def cast(self, x, y):
		target = Point(x, y)

		ally_candidates = []
		# First gather heal candidaes
		for stage in Burst(self.caster.level, target, self.get_stat('radius')):
			for point in stage:

				unit = self.owner.level.get_unit_at(point.x, point.y)
				if not unit:
					continue

				if not are_hostile(unit, self.caster) and unit.cur_hp <= unit.max_hp:
					ally_candidates.append(unit)

		for stage in Burst(self.caster.level, target, self.get_stat('radius')):
			for point in stage:

				unit = self.caster.level.get_unit_at(point.x, point.y)
				
				if not unit:
					self.caster.level.show_effect(point.x, point.y, Tags.Blood, minor=True)
					if self.get_stat('toxicity'):
						self.caster.level.show_effect(point.x, point.y, Tags.Poison, minor=True)
					continue

				if not are_hostile(self.caster, unit):
					continue

				dmg = unit.deal_damage(self.get_stat('damage'),  Tags.Dark, self)
				if self.get_stat('toxicity'):
					self.caster.level.deal_damage(point.x, point.y, self.get_stat('damage'), Tags.Poison, self)

				heal = dmg // 2
				if heal:
					if ally_candidates:
						candidate = random.choice(ally_candidates)
						candidate.deal_damage(-heal, Tags.Heal, self)
						if candidate.cur_hp >= candidate.max_hp:
							ally_candidates.remove(candidate)

			yield

		return

	def get_impacted_tiles(self, x, y):
		return [p for stage in Burst(self.caster.level, Point(x, y), self.get_stat('radius')) for p in stage]

class FleshFiendSpell(Spell):

	def on_init(self):
		self.name = "Flesh Fiend"
		self.tags = [Tags.Blood, Tags.Conjuration]
		self.hp_cost = 80
		self.max_charges = 3
		self.level = 5

		self.must_target_walkable = True
		self.must_target_empty = True

		ex = FleshFiend()
		self.minion_health = ex.max_hp
		self.minion_damage = ex.spells[0].damage

		self.upgrades['belly_flop'] = (1, 3, "Belly Flop", "Gains a [25:damage] damage leap attack with a 7 turn cooldown.")
		self.upgrades['char_fiend'] = (1, 5, "Barbeque Fiends", "Summons burning flesh fiends instead of normal ones.")
		self.upgrades['worm_lord'] = (1, 8, "Worm Lord", "Flesh Fiends can cast your Lumbriogenesis spell on a 13 turn cooldown.")


	def get_description(self):
		return ("Summons a Fleshy Mass.\n"
				"Fleshy Masses have [{minion_health}_HP:minion_health] and regenerate 21 HP per turn.\n"
				"Fleshy Masses have a melee attack which deals [{minion_damage}_physical:physical] damage.\n").format(**self.fmt_dict())

	def cast_instant(self, x, y):
		fiend = FleshFiend()

		if self.get_stat('belly_flop'):
			flop = LeapAttack(damage=24, range=5)
			fiend.spells.insert(0, flop)

		apply_minion_bonuses(self, fiend)

		if self.get_stat('worm_lord'):
			grant_minion_spell(WormOffering, fiend, self.caster, cool_down=13)

		if self.get_stat('char_fiend'):
			BossSpawns.apply_modifier(BossSpawns.Flametouched, fiend)

		self.summon(fiend, target=Point(x, y))

class WitchCoven(Spell):

	def on_init(self):
		self.name = "Witch Coven"
		self.tags = [Tags.Dark, Tags.Conjuration]
		self.level = 4
		self.max_charges = 1
		self.range = 3

	def can_cast(self, x, y):
		if self.owner.level.tiles[x][y].prop:
			return False
		return Spell.can_cast(self, x, y)

	def cast(self, x, y):
		prop = PlaceOfPower(Tags.Dark)
		self.owner.level.show_effect(x, y, Tags.Dark)
		self.owner.level.add_obj(prop, x, y)
		yield

		adj = list(self.owner.level.get_adjacent_points(Point(x, y)))
		random.shuffle(adj)
		for p in adj:
			witch = Witch()
			apply_minion_bonuses(self, witch)
			self.summon(witch, target=p)
			yield

	def get_impacted_tiles(self, x, y):
		adj = list(self.owner.level.get_adjacent_points(Point(x, y)))
		return [Point(x, y)] + adj

	def get_description(self):
		return ("Summons a Dark Circle surrounded by Witches.")

class SatyrCoven(Spell):

	def on_init(self):
		self.name = "Satyr Circle"
		self.tags = [Tags.Nature, Tags.Conjuration]
		self.level = 4
		self.max_charges = 1
		self.range = 3

	def can_cast(self, x, y):
		if self.owner.level.tiles[x][y].prop:
			return False
		return Spell.can_cast(self, x, y)

	def cast(self, x, y):
		prop = PlaceOfPower(Tags.Nature)
		self.owner.level.show_effect(x, y, Tags.Poison)
		self.owner.level.add_obj(prop, x, y)
		yield

		adj = list(self.owner.level.get_adjacent_points(Point(x, y)))
		random.shuffle(adj)
		for p in adj:
			satyr = Satyr()
			apply_minion_bonuses(self, satyr)
			self.summon(satyr, target=p)
			yield

	def get_impacted_tiles(self, x, y):
		adj = list(self.owner.level.get_adjacent_points(Point(x, y)))
		return [Point(x, y)] + adj

	def get_description(self):
		return ("Summons a Nature Circle surrounded by Satyrs.")

class HelgateSpell(Spell):

	def on_init(self):
		self.name = "Gates of Helheim"
		self.tags = [Tags.Dark, Tags.Lightning, Tags.Conjuration]
		self.level = 8

		self.max_charges = 13

		self.range = 0

		example = Elf()

		self.minion_health = example.max_hp
		self.minion_damage = example.spells[0].damage
		self.minion_range = example.spells[0].range

		self.upgrades['aelf_horde'] = (1, 5, "Aelf Horde", "刷怪笼生成时间缩短至4到5回合。")
		self.upgrades['fae_aelves'] = (1, 6, "Fae Aelves", "刷怪笼生成仙灵词条的精灵而非普通精灵。")
		self.upgrades['elite_aelves'] = (1, 8, "Elite Aelves", "刷怪笼生成精灵雷术师而非普通精灵。")

	def get_description(self):
		return "在随机位置召唤一个精灵刷怪笼。".format(**self.fmt_dict())

	def elf(self):
		unit = Elf()
		apply_minion_bonuses(self, unit)
		return unit

	def fae_elf(self):
		unit = Elf()
		BossSpawns.apply_modifier(BossSpawns.Faetouched, unit)
		apply_minion_bonuses(self, unit)
		return unit

	def elite_elf(self):
		unit = ElfLightningLord()
		apply_minion_bonuses(self, unit)
		return unit

	def cast(self, x, y):
		elf = self.elf
		if self.get_stat('fae_aelves'):
			elf = self.fae_elf
		if self.get_stat('elite_aelves'):
			elf = self.elite_elf
		gate = MonsterSpawner(elf)
		if self.get_stat('aelf_horde'):
			gate.get_spell(SimpleSummon).cool_down = random.randint(4, 5)
			gate.cool_downs[gate.get_spell(SimpleSummon)] = gate.get_spell(SimpleSummon).cool_down
		apply_minion_bonuses(self, gate)
		result = self.summon(gate, radius=99, sort_dist=False)
		if result:
			self.owner.level.show_path_effect(self.caster, result, [Tags.Dark, Tags.Lightning], minor=True)
		yield

	def get_extra_examine_tooltips(self):
		return [self.elf(), self.spell_upgrades[0], self.spell_upgrades[1], self.fae_elf(), self.spell_upgrades[2], self.elite_elf()]

class HordeOfHalfmen(Spell):

	def on_init(self):
		self.name = "Horde of Halfmen"
		
		self.tags = [Tags.Nature, Tags.Blood, Tags.Conjuration]
		self.level = 8

		self.hp_cost = 99

		self.num_summons = 5

		# Bases for %age bonuses
		self.minion_health = 20
		self.minion_damage = 9

		self.range = 9

		self.upgrades['trollblooded'] = (1, 5, "Trollblooded Halfmen", "召唤物带有[巨魔血:nature]词条")
		self.upgrades['metallic'] = (1, 6, "Metallic Halfmen", "召唤物带有[金属:metallic]词条")
		self.upgrades['burning'] = (1, 7, "Burning Halfmen", "召唤物带有[燃烧:fire]词条")

	def tooltip_monster(self, modifier, unit):
		unit = unit()
		BossSpawns.apply_modifier(modifier, unit)
		apply_minion_bonuses(self, unit)
		return unit

	def get_description(self):
		return "召唤[{num_summons}:num_summons]萨堤尔和[{num_summons}:num_summons]牛头人。".format(**self.fmt_dict())

	def get_extra_examine_tooltips(self):
		return [Satyr(), Minotaur(),
                self.spell_upgrades[0], self.tooltip_monster(BossSpawns.Trollblooded, Satyr), self.tooltip_monster(BossSpawns.Trollblooded, Minotaur),
				self.spell_upgrades[1], self.tooltip_monster(BossSpawns.Metallic, Satyr), self.tooltip_monster(BossSpawns.Metallic, Minotaur),
				self.spell_upgrades[2], self.tooltip_monster(BossSpawns.Flametouched, Satyr), self.tooltip_monster(BossSpawns.Flametouched, Minotaur)]

	def cast(self, x, y):
		for i in range(self.get_stat('num_summons')):
			for unit in [Satyr(), Minotaur()]:
			
				if self.get_stat('trollblooded'):
					BossSpawns.apply_modifier(BossSpawns.Trollblooded, unit)
				if self.get_stat('metallic'):
					BossSpawns.apply_modifier(BossSpawns.Metallic, unit)
				if self.get_stat('burning'):
					BossSpawns.apply_modifier(BossSpawns.Flametouched, unit)
			
				apply_minion_bonuses(self, unit)
				monster = self.summon(unit, target=Point(x, y), radius=7)

				# Todo: use "Nature" effect instead of poison
				if monster:
					self.owner.level.show_path_effect(self.caster, monster, [Tags.Blood, Tags.Poison], minor=True)

				yield

class GoatOffering(Spell):

	def on_init(self):
		self.name = "Goatia Offering"
		self.tags = [Tags.Blood, Tags.Dark, Tags.Nature, Tags.Conjuration]
		self.level = 2
		self.hp_cost = 5

		self.upgrades['reincarnation'] = (1, 3, "Reincarnation", "羊头恶魔死亡时可重生一次")
		self.upgrades['pain'] = (1, 3, "Pain Aura", "羊头恶魔对任何对其造成伤害的单位造成[5:dark]。")
		self.upgrades['maggot_host'] = (1, 3, "Maggot Host", "羊头恶魔死亡时，生成[2:num_summons]心灵蛆虫。")

		example = GoatHead()

		self.minion_health = example.max_hp
		self.minion_damage = example.spells[0].damage
		self.minion_range = example.spells[0].range

	def maggot(self):
		maggot = MindMaggot()
		return maggot

	def gotia(self):
		unit = GoatHead()
		apply_minion_bonuses(self, unit)

		if self.get_stat('reincarnation'):
			unit.buffs.append(ReincarnationBuff(1))
		if self.get_stat('pain'):
			unit.buffs.append(RetaliationBuff(self.get_stat('minion_damage'), Tags.Dark))
		if self.get_stat('maggot_host'):
			# Gets flat numsummons buffs... but not %age ones?  hmm.....  dont want to show num_summons on the unupgraded spell tho
			unit.buffs.append(SpawnOnDeath(self.maggot, 2 + self.get_stat('num_summons')))

		return unit

	def cast_instant(self, x, y):
		unit = self.gotia()
		self.summon(unit, target=Point(x, y))

	def get_extra_examine_tooltips(self):
		return [self.gotia()] + self.spell_upgrades

	def get_description(self):
		return "召唤一只羊头恶魔."

class BurningHungerBuff(Buff):

	def __init__(self, spell):
		self.spell = spell
		Buff.__init__(self)

	def on_init(self):
		self.description = "每回合吞噬生命值最低的友军，对该单位附近敌人造成火焰伤害。"

	def on_advance(self):
		allies = [u for u in self.owner.level.units if not are_hostile(u, self.owner)]

		# WTF
		if not allies:
			return

		# Shuffle to make min random
		random.shuffle(allies)

		ally = min(allies, key=lambda a: a.cur_hp)

		self.owner.level.show_path_effect(self.owner, ally, Tags.Dark, minor=True)
		
		if self.spell.get_stat('archon_beam'):
			for p in self.owner.level.get_points_in_line(self.owner, ally):
				u = self.owner.level.get_unit_at(p.x, p.y)
				if u and not are_hostile(u, self.owner):
					self.owner.level.deal_damage(p.x, p.y, 0, Tags.Lightning, self.spell)
					u.add_shields(1)
				else:
					self.owner.level.deal_damage(p.x, p.y, self.spell.get_stat('damage'), Tags.Lightning, self.spell)

		ally.kill()
		self.owner.level.show_effect(ally.x, ally.y, Tags.Fire)

		for u in self.owner.level.get_units_in_ball(ally, self.spell.get_stat('radius')):
			if self.spell.get_stat('bone_explosion'):
				self.owner.level.show_beam(ally, u, Tags.Physical, minor=True)
				u.deal_damage(self.spell.get_stat('damage'), Tags.Physical, self.spell)
			if not are_hostile(self.owner, u):
				continue
			self.owner.level.show_beam(ally, u, Tags.Fire, minor=True)
			u.deal_damage(self.spell.get_stat('damage'), Tags.Fire, self.spell)

class IdolOfBurningHunger(Spell):

	def on_init(self):
		self.name = "Burning Idol"
		self.tags = [Tags.Fire, Tags.Conjuration, Tags.Metallic, Tags.Dark]
		self.level = 4
		self.max_charges = 2
		self.radius = 4

		titan = Idol()
		self.damage = 20
		self.must_target_empty = True
		
		self.upgrades['bone_explosion'] = (1, 3, "Bone Explosion", "额外对被牺牲单位4格距离内所有单位造成被牺牲单位一半生命值的[physical:physical]伤害。")
		self.upgrades['archon_beam'] = (1, 3, "Archon Beam", "在与被牺牲单位连接的路径上发射闪电，对敌人造成伤害，对友方提供护盾。")

	def get_impacted_tiles(self, x, y):
		# dont show radius
		return [Point(x, y)]

	def get_description(self):
		return ("召唤一座焚烬造像。\n"
			    "每回合雕像会吞噬其生命值最低的友军，对临近被牺牲单位的敌人造成火焰伤害。\n"
			    "巫师与雕像本身都是合法的牺牲对象。\n")

	def make_idol(self):
		unit = Idol()
		unit.asset_name = 'fiery_vengeance_idol'
		unit.buffs.append(BurningHungerBuff(self))
		return unit

	def cast_instant(self, x, y):
		unit = self.make_idol()
		apply_minion_bonuses(self, unit)
		self.summon(unit, target=Point(x, y))

class DrainPulse(Spell):

	def on_init(self):
		self.tags = [Tags.Dark, Tags.Blood, Tags.Sorcery]
		self.damage = 13
		self.max_charges = 3
		self.level = 4
		self.radius = 8
		self.range = 0
		self.hp_cost = 4
		self.name = "Drain Pulse"

		#Upgrade ideas:
		# Summon a horde of snakes per damage dealt.. or flies... or... something?
		# Overhealing converted to lightning and arcane energy
		# Raise kills as bloodghasts
		# +3 radius
		# Repeat pulse
		# Redeal dealt damage as holy (arcane?) 4SP

		self.upgrades['felomancy'] = (1, 4, "Felomancy", "被杀死的目标重生为被诅咒的猫。")
		self.upgrades['ursomancy'] = (1, 4, "Ursomancy", "超出巫师最大生命值的治疗会召唤鲜血巨熊。")
		self.upgrades['radius'] = (3, 4)

	def get_description(self):
		return ("对[{radius}_tile:radius]范围内的单位造成[{damage}:dark]与[{damage}:poison]。\n" #不改变占位符的话，“伤害”字样会重复
				"造成伤害的一半会治疗你。").format(**self.fmt_dict())

	def get_impacted_tiles(self, x, y):
		radius = self.get_stat('radius')
		return [p for stage in Burst(self.caster.level, Point(x, y), radius) for p in stage]

	def cast(self, x, y):
		dmg = 0

		kills = []

		for stage in Burst(self.caster.level, Point(x, y), self.get_stat('radius')):
			for point in stage:
				if point == Point(x, y):
					continue
				unit = self.owner.level.get_unit_at(*point)
				dmg += self.owner.level.deal_damage(point.x, point.y, self.get_stat('damage'), Tags.Dark, self)
				if unit and not unit.is_alive():
					kills.append(unit)
			yield

		back_burst_stages = reversed([s for s in Burst(self.caster.level, Point(x, y), self.get_stat('radius'))])

		for stage in back_burst_stages:
			for point in stage:
				if point == Point(x, y):
					continue

				unit = self.owner.level.get_unit_at(*point)
				dmg += self.owner.level.deal_damage(point.x, point.y, self.get_stat('damage'), Tags.Poison, self)
				if unit and not unit.is_alive():
					kills.append(unit)
			yield

		if dmg > 1:
			heal = (dmg // 2)
			max_heal = self.caster.max_hp - self.caster.cur_hp
			overheal = heal - max_heal
			self.caster.heal(heal, self)

			if self.get_stat('ursomancy') and overheal > 0:
				num_bears = (overheal // 75) + 1
				bear_hp = overheal / num_bears

				for _ in range(int(num_bears)):
					bear = BloodBear()
					apply_minion_bonuses(self, bear)
					bear.max_hp = bear_hp
					self.summon(bear)

		if self.get_stat('felomancy'):
			for u in kills:
				cat = BlackCat()
				apply_minion_bonuses(self, cat)
				self.summon(cat, target=u)

class SummonWizard(Spell):

	def on_init(self):
		self.name = "Summon Wizard"
		self.tags = [Tags.Conjuration, Tags.Arcane]
		self.level = 8
		self.max_charges = 1

		# Upgrades
		#  Clay Wizard - 5 SP CLAY
		#  Ghost Wizard - 5 SP GHOST
		#  Wizard Council - 8 SP SUMMON 3NUMSMMONS

		self.upgrades['clay_wizard'] = (1, 6, "Clay Wizard", "被召唤的巫师具有黏土制品词条。")
		self.upgrades['ghost_wizard'] = (1, 5, "Ghost Wizard", "被召唤的巫师具有幽灵词条。")
		self.upgrades['wizard_army'] = (1, 9, "Wizard Gang", "召唤[3:num_summons]巫师。")

		#  Affinity - always summon a wizard with a tag matching your most common spell (skill?) tag

	def get_description(self):
		return "召唤一名随机巫师。"

	def cast_instant(self, x, y):
		import RareMonsters  # GROSS.  But neccecary.

		number_summoned = 1 if not self.get_stat('wizard_army') else self.get_stat('num_summons', base=3)

		for i in range(number_summoned):
			wizard = random.choice(RareMonsters.all_wizards)[0]()  

			if self.get_stat('clay_wizard'):
				BossSpawns.apply_modifier(BossSpawns.Claytouched, wizard)

			if self.get_stat('ghost_wizard'):
				BossSpawns.apply_modifier(BossSpawns.Ghostly, wizard)

			self.summon(wizard, target=Point(x, y))

class BrainSeedParasiteBuff(Buff):

	def __init__(self, spell):
		self.spell = spell
		Buff.__init__(self)
		self.asset = ['status', 'brain_seed']
		self.color = Tags.Arcane.color
		self.name = "Psychic Parasite"
		self.buff_type = BUFF_TYPE_CURSE
		self.owner_triggers[EventOnDeath] = self.on_death

	def on_advance(self):
		self.owner.deal_damage(self.spell.get_stat('damage', base=1), Tags.Arcane, self.spell)

	def on_death(self, evt):
		if self.owner.max_hp < 40:
			return
		self.owner.level.queue_spell(self.do_summon())

	def do_summon(self):
		unit = BrainBush()
		apply_minion_bonuses(self.spell, unit)
		self.spell.summon(unit, target=self.owner)
		yield

class BrainSeedSpell(Spell):

	def on_init(self):
		self.name = "Psychic Seedling"
		self.level = 3
		self.max_charges = 5
		self.tags = [Tags.Conjuration, Tags.Arcane, Tags.Nature]

		# upgrade: 5 seeds instead of 1.  4SP.
		# upgrade: Parasitic Growth: can cast on an enemy, deals 1 arcane damage until that enemy dies and then sprouds as a tree with hp = enemy max hp. 1SP.
		# upgrade: Eternal Forest: summon an immortal bush.  7SP.

		self.upgrades['psychic_forest'] = (1, 6, "Psychic Fields", "种下5棵幼苗，而非1棵。")
		self.upgrades['eternal_forest'] = (1, 8, "Immortal Forest", "种下一棵不朽（复活一次）幼苗，而非普通幼苗。")
		self.upgrades['parasite'] = (1, 4, "Parasitic Growth", "除空地格外还可指定敌人为目标。目标敌人每回合受到[1_arcane:arcane]伤害，持续10回合。若期间该敌人死亡，且其具有至少40点最大生命值，则在其死亡地格处生成一棵脑树。") 

	def get_description(self):
		return "种下一丛脑树幼苗，它最终会成长为一片脑树森林。"
		#考虑到brain tree这个单位翻译成脑树，这里先叫脑树丛
	def can_cast(self, x, y):
		unit = self.owner.level.get_unit_at(x, y)
		if unit:
			return self.get_stat('parasite')

		return Spell.can_cast(self, x, y)

	def cast_instant(self, x, y):

		target = self.owner.level.get_unit_at(x, y)
		if target and self.get_stat('parasite'):
			target.apply_buff(BrainSeedParasiteBuff(self))
			return


		num_units = 1
		if self.get_stat('psychic_forest'):
			num_units = self.get_stat('num_summons', base=5)

		for i in range(num_units):
			unit = BrainSapling()

			if self.get_stat('eternal_forest'):
				BossSpawns.apply_modifier(BossSpawns.Immortal, unit)

			apply_minion_bonuses(self, unit)

			self.summon(unit, target=(Point(x, y)))


	def get_extra_examine_tooltips(self):
		return [BrainSapling(), BrainBush()] + self.spell_upgrades

class SoulWindSpell(Spell):

	def on_init(self):
		self.tags = [Tags.Blood, Tags.Holy, Tags.Dark, Tags.Sorcery]
		self.hp_cost = 54
		self.requires_los = False
		self.range = RANGE_GLOBAL
		self.max_charges = 3
		self.level = 7
		self.damage = 37
		self.name = "Soul Wind"

		# Upgrade 1: All souls ripped
		# Upgrade 2: Mirror
		# Upgrade 3: All units additionally take arcane damage

		self.upgrades['ensoulment'] = (1, 4, "Ensoulment", "非[living]单位也可生成灵体。")
		self.upgrades['arcane_wind'] = (1, 5, "Arcane Wind", "对范围内所有单位再造成一次奥术伤害。")
		self.upgrades['mirror'] = (1, 4, "Dual Wind", "额外在施法者身后施放灵魂之风。")

	def get_description(self):
		return ("引发一阵灵魂之风。范围内的所有单位受到[{damage}:dark]。\n"
			   "范围内所有[undead]，[dark]，与[demon]单位改为受到[{damage}:holy]。\n"
			   "范围内的[Living]单位的灵魂会被从肉体剥离，生成灵体。\n"
			   "灵体可能因生成该灵体的原本单位的词缀而拥有额外的能力与抗性。").format(**self.fmt_dict())

	def get_impacted_tiles(self, x, y):
		line = self.caster.level.get_perpendicular_line(self.caster, Point(x, y))
		result = set()
		for p in line:
			for q in self.caster.level.get_points_in_rect(p.x-1, p.y-1, p.x+1, p.y+1):
				result.add(q)
		if self.get_stat('mirror'):
			mirrored_line = self.caster.level.get_perpendicular_line(self.caster, Point(2*self.caster.x-x, 2*self.caster.y-y))
			for p in mirrored_line:
				for q in self.caster.level.get_points_in_rect(p.x-1, p.y-1, p.x+1, p.y+1):
					result.add(q)
		return result

	def cast(self, x, y):
		for p in self.get_impacted_tiles(x, y):

			unit = self.owner.level.get_unit_at(p.x, p.y)
			if not unit:
				
				if self.get_stat('arcane_wind'):
					dtype = random.choice([Tags.Dark, Tags.Holy, Tags.Arcane])
				else:
					dtype = random.choice([Tags.Dark, Tags.Holy])	
				self.owner.level.show_effect(p.x, p.y, dtype, minor=True)

			if unit:
				dtype = Tags.Dark
				for t in [Tags.Undead, Tags.Demon, Tags.Dark]:
					if t in unit.tags:
						dtype = Tags.Holy
						break

				unit.deal_damage(self.get_stat('damage'), dtype, self)

				if self.get_stat('arcane_wind'):
					unit.deal_damage(self.get_stat('damage'), Tags.Arcane, self)

				if Tags.Living in unit.tags or self.get_stat('ensoulment'):
					ghost = Ghost()
					apply_minion_bonuses(self, ghost)

					opts = [(Tags.Fire, BossSpawns.Flametouched),
							 (Tags.Ice, BossSpawns.Icy),
							 (Tags.Arcane, BossSpawns.Faetouched),
							 (Tags.Lightning, BossSpawns.Stormtouched),
							 (Tags.Chaos, BossSpawns.Chaostouched),
							 (Tags.Metallic, BossSpawns.Metallic)]

					modifier = None
					for t, m in opts:
						if t in unit.tags:
							modifier = m
							break

					if modifier:
						BossSpawns.apply_modifier(m, ghost)

					self.summon(ghost, target=unit)


			if random.random() < .4:
				yield

class ElephantFormBuff(Buff):

	def __init__(self, spell):
		self.spell = spell
		Buff.__init__(self)

	def on_init(self):
		self.name = "Elephant Form"

		self.resists[Tags.Physical] = 50

		if self.spell.get_stat('fae'):
			self.resists[Tags.Arcane] = 50
		if self.spell.get_stat('burning'):
			self.resists[Tags.Fire] = 50
		if self.spell.get_stat('metallic'):
			self.resists[Tags.Fire] = 25
			self.resists[Tags.Lightning] = 50

		self.transform_asset_name = "player_elephant"
		self.buff_type = BUFF_TYPE_BLESS
		self.stack_type = STACK_TYPE_TRANSFORM
		self.owner_triggers[EventOnSpellCast] = self.on_spell_cast
		self.elephants = []

	def on_spell_cast(self, evt):
		if evt.spell == self.owner.melee_spell:
			return

		if self.spell.get_stat('fae') and Tags.Arcane in evt.spell.tags:
			return
		if self.spell.get_stat('burning') and Tags.Fire in evt.spell.tags:
			return
		if self.spell.get_stat('metallic') and Tags.Metallic in evt.spell.tags:
			return

		self.owner.remove_buff(self)

	def on_applied(self, owner):
		trample = SimpleMeleeAttack(damage=self.spell.get_stat('damage'), trample=True)
		trample.owner = self.owner
		trample.caster = self.owner
		self.owner.melee_spell = trample

	def on_unapplied(self):
		self.owner.melee_spell = None
		for e in self.elephants:
			if e.is_alive():
				e.kill(trigger_death_event=False)
				self.owner.level.show_effect(e.x, e.y, Tags.Translocation)


class StampedeFormSpell(Spell):

	def on_init(self):
		self.name = "Stampede Form"
		self.tags = [Tags.Nature, Tags.Conjuration, Tags.Enchantment]
		self.level = 4
		self.max_charges = 3
		self.duration = 12
		self.minion_duration = 12
		self.range = 0
		self.damage = 14
		self.num_summons = 10

		# Fae Stampede - gain arcane resist, faephants, can cast arcane spells and not end 
		# Burning Stampede - gain fire reists, burning elephants, can cast fire spells and not end
		# Metal Stampede - gain phys, fire, light resist, metal elephants, can cast metal spells and not end

		self.upgrades['fae'] = (1, 6, "Fae Stampede", "召唤仙灵大象而不是普通大象。获得50奥术抗性，施放奥术法术不会结束大象形态。")#faetouched在loc.py里没见过
		self.upgrades['burning'] = (1, 7, "Burning Stampede", "召唤燃烧大象而不是普通大象。获得50火焰抗性，施放火焰法术不会结束大象形态。")
		self.upgrades['metallic'] = (1, 7, "Metal Stampede", "召唤金属大象而不是普通大象。获得25火焰抗性和50闪电抗性，施放金属法术不会结束大象形态。")
	
	def get_description(self):
		return ("变形为大象，并同时在你周围召唤[{num_summons}:num_summons]大象。\n"
				"处于大象形态时，你可以从敌人头上走过，击退它们并对它们造成[{damage}:physical]。\n"
				"处于大象形态时获得50[physical]抗性。\n"
				"当你施放一个法术时，结束大象形态并解除召唤所有大象。").format(**self.fmt_dict())

	def get_elephant(self):
		elephant = Elephant()

		if self.get_stat('fae'):
			BossSpawns.apply_modifier(BossSpawns.Faetouched, elephant)

		if self.get_stat('burning'):
			BossSpawns.apply_modifier(BossSpawns.Flametouched, elephant)

		if self.get_stat('metallic'):
			BossSpawns.apply_modifier(BossSpawns.Metallic, elephant)

		apply_minion_bonuses(self, elephant)
		return elephant

	def cast(self, x, y):
		buff = ElephantFormBuff(self)
		self.owner.apply_buff(buff, self.get_stat('duration'))
		
		for i in range(self.get_stat('num_summons')):
			elephant = self.get_elephant()
			self.summon(elephant)
			buff.elephants.append(elephant)
			yield

class ChannelMalevolence(Spell):

	def on_init(self):
		self.tags = [Tags.Fire, Tags.Dark, Tags.Sorcery]
		self.level = 7
		self.max_charges = 1
		self.num_targets = 4
		self.max_channel = 5
		self.damage = 14
		self.name = "Hatebolts"
		self.range = 0
		self.requires_los = False

		# Upgrades
		#  Radius
		#  extra DType
		#  tormentor charges

		self.upgrades['return'] = (1, 3, "Boomerang", "箭在抵达目标后会返回，对路径中间的单位造成二次伤害")
		self.upgrades['toxic'] = (1, 3, "Toxic Hatred", "箭也会对敌人造成 [poison]，持续 [13_turns:duration]")
		self.upgrades['harvest'] = (1, 3, "Torment Harvest", "如果该法术击杀一名敌人，炽火狱卒法术获得一点充能。")


	def get_description(self):
		return ("每回合对[{num_targets}:num_targets]随机敌人发射能量箭，交替对路径上所有单位造成[{damage}:fire]或[{damage}:dark]。\n"
				"可持续引导至多5回合。").format(**self.fmt_dict())


	def cast(self, x, y, channel_cast=False):

		if not channel_cast:
			self.caster.apply_buff(ChannelBuff(self.cast, Point(x, y)), self.get_stat('max_channel'))
			return

		targets = [u for u in self.owner.level.units if are_hostile(self.caster, u)]
		random.shuffle(targets)

		wisps_left = self.get_stat('num_targets')
		target_idx = 0

		wisps = []

		is_fire_bolt = True
		while wisps_left and targets:
			target = targets.pop()
			pather = Unit()
			pather.flying = True

			path = self.owner.level.find_path(self.owner, target, pather, pythonize=True, unit_penalty=0)
			if not path:
				continue

			if self.get_stat('return'):
				ret_path = path[:-1]
				ret_path.reverse()
				path = path + ret_path
			else:
				path.reverse()

			if is_fire_bolt:
				dtype = Tags.Fire
			else:
				dtype = Tags.Dark
			is_fire_bolt = not is_fire_bolt

			wisps.append((path, dtype))
			wisps_left -= 1

		is_fire_bolt = True
		while any(wisp[0] for wisp in wisps):
			for path, dtype in wisps:
				if not path:
					continue

				p = path.pop()
				unit = self.owner.level.get_unit_at(p.x, p.y)


				self.owner.level.deal_damage(p.x, p.y, self.get_stat('damage'), dtype, self)
				
				if unit and self.get_stat('toxic'):
					unit.apply_buff(Poison(), self.get_stat('duration', base=13))

				if unit and not unit.is_alive() and self.get_stat('harvest'):
					spell = self.owner.get_spell(SummonFieryTormentor)
					if spell and spell.cur_charges < spell.get_stat('max_charges'):
						spell.cur_charges += 1


			yield


class GiftOfLycanthropy(Spell):

	def on_init(self):
		self.name = "Gift of Lycanthropy"
		self.tags = [Tags.Enchantment, Tags.Blood, Tags.Nature]

		self.can_target_empty = False

		self.hp_cost = 6
		self.max_charges = 7
		self.level = 3

		self.upgrades['hp_bonus'] = (1, 3, "Greater Werewolf", "The targeted unit gains 80 max HP")
		self.upgrades['shaman'] = (1, 5, "Werewolf Shaman", "The targeted unit gains your lifetap spell on a 7 turn cooldown")
		self.upgrades['howler'] = (1, 8, "Werewolf Howler", "The targeted unit gains your summon wolf spell on a 7 turn cooldown")

	def get_description(self):
		return ("Target unit becomes a Lycanthrope, regenerating 5 hp per turn and turning into a wolf on death.  If the wolf survives, it returns to its original form.\n"
			   "Cannot target units that already respawn or split.\n")

	def can_cast(self, x, y):
		unit = self.owner.level.get_unit_at(x, y)
		
		if not unit:
			return False

		if not BossSpawns.check_death_buffs(unit):
			return False

		if are_hostile(self.caster, unit):
			return False

		return Spell.can_cast(self, x, y)


	def cast_instant(self, x, y):
		unit = self.owner.level.get_unit_at(x, y)
		if not unit:
			return

		unit.Anim = None

		BossSpawns.apply_modifier(BossSpawns.Lycanthrope, unit)

		if self.get_stat('hp_bonus'):
			unit.max_hp += 80
			unit.cur_hp += 80

		if self.get_stat('shaman'):
			grant_minion_spell(BloodTapSpell, unit, self.caster, cool_down=7)

		if self.get_stat('howler'):
			grant_minion_spell(SummonWolfSpell, unit, self.caster, cool_down=7)



class BloodflameBuff(Buff):

	def on_init(self):
		self.name = "Bloodfire"
		self.color = Tags.Fire.color
		self.buff_type = BUFF_TYPE_BLESS
		self.tag_bonuses[Tags.Fire]['quick_cast'] = 1
		self.owner_triggers[EventOnSpellCast] = self.on_cast
		self.charges = 4

	def on_cast(self, evt):
		self.charges -= 1

		if self.charges == 0:
			self.owner.remove_buff(self)
	

class BloodflameSpell(Spell):

	def on_init(self):
		self.name = "Bloodflame"
		self.tags = [Tags.Blood, Tags.Fire, Tags.Enchantment]
		self.duration = 1
		self.hp_cost = 30
		self.max_charges = 1
		self.level = 5
		self.quick_cast = True
		self.range = 0


	def get_description(self):
		return ("接下来4个 [Fire] 法术可立即施法，无需结束回合。\n"
				"持续1回合。\n")

	def cast_instant(self, x, y):
		self.owner.apply_buff(BloodflameBuff(), 1)
		self.owner.level.show_effect(self.owner.x, self.owner.y, Tags.Blood)


all_player_spell_constructors = [
	#FlameTongue,
	#SparkSpell,
	FireballSpell, 
	LightningBoltSpell,
	AnnihilateSpell,
	LightningFormSpell,
	MegaAnnihilateSpell,
	Teleport,
	BlinkSpell,
	VoidBeamSpell,
	ThunderStrike,
	#GiantStrengthSpell,
	ChaosBarrage,
	DispersalSpell,
	PetrifySpell,
	SummonWolfSpell,
	#SummonDireWolfSpell,
	SummonGiantBear,
	FeedingFrenzySpell,
	StormSpell,
	ThornyPrisonSpell,
	FlameStrikeSpell,
	BloodlustSpell,
	HealMinionsSpell,
	RegenAuraSpell,
	VoidOrbSpell,
	Dominate,
	FlameGateSpell,
	EyeOfFireSpell,
	EyeOfLightningSpell,
	EyeOfIceSpell,
	NightmareSpell,
	CockatriceSkinSpell,
	WatcherFormSpell,
	ImpGateSpell,
	LightningHaloSpell,
	ArcaneVisionSpell,
	ArcaneDamageSpell,
	FlameBurstSpell,
	SummonFireDrakeSpell,
	SummonStormDrakeSpell,
	SummonVoidDrakeSpell,
	SummonIceDrakeSpell,
	ChainLightningSpell,
	DeathBolt,
	TouchOfDeath,
	SealFate,
	WheelOfFate,
	Volcano,
	UnderworldPortal,
	SummonEarthElemental,
	CallSpirits,
	MysticMemory,
	#ConjureMemories,
	Permenance,
	DeathGazeSpell,
	MagicMissile,
	MindDevour,
	DeathShock,
	MeltSpell,
	DragonRoarSpell,
	ProtectMinions,
	WordOfChaos,
	WordOfUndeath,
	WordOfBeauty,
	SummonFloatingEye,
	EyeOfRageSpell,
	#ChimeraFarmiliar,
	ArcLightning,
	Flameblast,
	PoisonSting,
	SummonBlueLion,
	DeathCleaveSpell,
	MulticastSpell,
	FaeCourt,
	RingOfSpiders,
	WordOfMadness,
	HolyBlast,
	HolyFlame,
	AngelicChorus,
	HeavensWrath,
	BestowImmortality,
	SoulTax,
	HolyShieldSpell,
	BlindingLightSpell,
	FlockOfEaglesSpell,
	#FlamingSwordSpell,
	HeavenlyIdol,
	SummonGoldDrakeSpell,
	SummonSeraphim,
	SummonArchon,
	PainMirrorSpell,
	PyrostaticPulse,
	#ThunderStones,
	#FireStones,  
	VoidRip,
	ShieldSiphon,
	VoidMaw,
	Darkness,
	HallowFlesh,
	CantripCascade,
	ConductanceSpell,
	InvokeSavagerySpell,
	MeteorShower,
	ShrapnelBlast,
	PlagueOfFilth,
	SearingOrb,
	BallLightning,
	OrbControlSpell,
	GlassOrbSpell,
	SummonFieryTormentor,
	StoneAuraSpell,
	DispersionFieldSpell,
	SummonKnights,
	ToxinBurst,
	ToxicSpore,
	#AmplifyPoisonSpell,
	IgnitePoison,
	#VenomBeast,
	SummonSpiderQueen,
	Freeze,
	Iceball,
	BlizzardSpell,
	SummonFrostfireHydra,
	StormNova,
	DeathChill,
	SummonIcePhoenix,
	WordOfIce,
	FrozenOrbSpell,
	#IceWeave,
	#ShatterShards,
	Icicle,
	IceWind,
	IceWall,
	BoneBarrageSpell,
	EarthquakeSpell,
	SearingSealSpell,
	SoulSwap,
	PuritySpell,
	TwilightGazeSpell,
	SlimeformSpell,
	Blazerip,
	IceVortex,
	RestlessDead,
	#GustOfWind,
	PyrostaticHexSpell,
	SpikeballFactory,
	MercurizeSpell,
	MagnetizeSpell,
	SilverSpearSpell,
	SummonSiegeGolemsSpell,
	LightningSpire,
	EssenceFlux,
	FaehauntGardenSpell,
	#DisintegrationCascadeSpell,
	FurnaceOfSorcerySpell,
	GoldSkullSummonSpell,
	WyrmEggs,
	#DeathchillConjuringSpell,
	MoonGlaive,
	CarnivalOfPain,
	DreamwalkSpell,
	MassCalcification,
	ScourgeSpell,
	ImmolateSpell,
	ArmeggedonBlade,
	Bonespear,
	WormOffering,
	HagSummon,
	BloodGolemSpell,
	BloodTapSpell,
	RitualOfRevelation,
	DevourFlesh,
	Bloodshift,
	FleshFiendSpell,
	HelgateSpell,
	HordeOfHalfmen,
	#WitchCoven,
	#SatyrCoven,
	IdolOfBurningHunger,
	GoatOffering,
	DrainPulse,
	SummonWizard,
	BrainSeedSpell,
	SoulWindSpell,
	StampedeFormSpell,
	ChannelMalevolence,
	#GiftOfLycanthropy,
	BloodflameSpell
]

def make_player_spells():
	all_player_spells = []

	for c in all_player_spell_constructors:
		s = c()
	#	if Tags.Chaos not in s.tags and Tags.Holy not in s.tags and Tags.Word not in s.tags:
		all_player_spells.append(s)

	unit = Unit()
	for spell in all_player_spells:
		unit.add_spell(spell)

	# Insist that all spells are spells (to catch mod bugs mostly)
	for spell in all_player_spells:
		if not isinstance(spell, Spell):
			print(spell.name)
			assert(isinstance(spell, Spell))

	# Insist that no spells have none descs, a common bug
	for spell in all_player_spells:
		if not spell.get_description():
			print(spell.name)
			assert(spell.get_description())

	# Insist that no spells have no tags
	for spell in all_player_spells:
		if not spell.level or not len(spell.tags):
			print(spell.name)
			assert(spell.level)
			assert(len(spell.tags))

	# Insist that the spell has consistant desc
	for spell in all_player_spells:
		if spell.description:
			print(spell.name)
			assert(spell.description == spell.get_description())

	# Insist that all extra tooltips exist
	for spell in all_player_spells:
		for tt_obj in spell.get_extra_examine_tooltips():
			if not tt_obj:
				print(spell)
				assert(tt_obj)

	# sort by total req levels
	all_player_spells.sort(key=lambda s: (s.level, s.name))

	return all_player_spells

if __name__ == '__main__':
	spells = make_player_spells()


	num_bads = 0
	for s in spells:
		bad = False
		if len(s.upgrades) != 3:
			bad = True

		for u in s.spell_upgrades:
			if u.name in attr_colors.keys():
				bad = True

		if bad:
			print(s.name)
			for u in s.upgrades:
				print('   ' + u)
			num_bads += 1

	print("Bads: %d" % num_bads)
