from Level import *

class SimpleMeleeAttack(Spell):

	def __init__(self, damage=1, buff=None, buff_duration=0, damage_type=Tags.Physical, onhit=None, attacks=1, trample=False, drain=False):
		Spell.__init__(self)
		self.name = "近战"
		self.range = 1.5
		self.melee = True
		self.damage = damage
		self.damage_type = damage_type
		self.buff = buff
		self.buff_duration = buff_duration
		self.buff_name = buff().name if buff else None
		self.onhit = onhit
		self.attacks = attacks
		self.trample = trample
		self.drain = drain

	def cast_instant(self, x, y):

		for i in range(self.attacks):
			unit = self.caster.level.get_unit_at(x, y)

			if self.attacks > 1 and not unit:
				possible_targets = self.caster.level.get_units_in_ball(self.caster, 1.5)
				possible_targets = [t for t in possible_targets if self.caster.level.are_hostile(self.caster, t)]
				if possible_targets:
					target = random.choice(possible_targets)
					x = target.x
					y = target.y

			dealt = self.caster.level.deal_damage(x, y, self.get_stat('damage'), self.damage_type, self)
			if self.drain:
				self.caster.deal_damage(-dealt, Tags.Heal, self)

			if unit and unit.is_alive():
				if self.buff:		
					unit.apply_buff(self.buff(), self.buff_duration)
				if self.trample:
					
					trample_points = [p for p in self.caster.level.get_adjacent_points(Point(x, y ), check_unit=True, filter_walkable=True)] + [None]
					p = random.choice(trample_points)
					if p:
						self.caster.level.act_move(unit, p.x, p.y)
					
					if self.caster.level.can_move(self.caster, x, y, force_swap=True):
						self.caster.level.act_move(self.caster, x, y, force_swap=True)
					
			if self.onhit and unit:
				self.onhit(self.caster, unit)

	def get_description(self):
		if self.description:
			return self.description

		desc = ""
		if self.buff_name:
			desc += "施加 %d 回合的%s" % (self.buff_duration, self.buff_name)
		if self.attacks > 1:
			desc += "攻击 %d 次" % self.attacks
		if self.trample:
			desc += "Trample attack"
		if self.drain:
			desc += "根据造成的伤害治疗攻击者"

		return desc

class SimpleRangedAttack(Spell):

	def __init__(self, name=None, damage=1, damage_type=Tags.Physical, range=3, beam=False, onhit=None, radius=0, melt=False, 
				 max_channel=0, cool_down=0, proj_name=None, effect=None, buff=None, buff_duration=0, cast_after_channel=False,
				 drain=False):
		Spell.__init__(self)

		self.name = name

		# Auto name bolt, ball if only one damage type.  Multiple damage types is harder.
		if not self.name:
			if isinstance(damage_type, Tag):
				if radius:
					self.name = "%s球" % damage_type.name
				else:
					self.name = "%s箭" % damage_type.name

		if not self.name:
			name = "远程攻击"

		self.damage = damage
		self.damage_type = damage_type
		self.range = range
		if isinstance(damage_type, list):
			self.tags = damage_type
		else:
			self.tags = [damage_type]
		self.beam = beam
		self.onhit = onhit
		self.radius = radius
		self.melt = melt
		if self.melt:
			self.requires_los = False

		self.max_channel = max_channel
		self.cool_down = cool_down
		
		self.proj_name = proj_name
		self.effect = effect

		self.buff = buff
		self.buff_name = buff().name if buff else None
		self.buff_duration = buff_duration

		self.cast_after_channel = cast_after_channel
		self.siege = False

		self.drain = drain
		self.suicide = False

	def get_description(self):
		
		desc = self.description + '\n'
		if self.beam:
			desc += "射线攻击\n"
		
		if self.melt:
			desc += "融化经过的墙体\n"
		elif not self.requires_los:
			desc += "无视墙体\n"

		#if isinstance(self.damage_type, list):
		#	desc += "Randomly deals %s damage\n" % ' or '.join(t.name for t in self.damage_type)
		
		if self.cast_after_channel:
			desc += "施放时间: %d 回合\n" % self.max_channel
		elif self.max_channel:
			desc += "最多可以维持 %d 回合\n" % self.max_channel

		if self.buff:
			desc += "施加 %d 回合的%s\n" % (self.buff_duration, self.buff_name)

		if self.siege:
			desc += "满血时才能施放\n将扣除一半的血量"

		if self.drain:
			desc += "根据造成的伤害治疗施法者"

		if self.suicide:
			desc += "施法者将死亡"

		# Remove trailing \n
		desc = desc.strip()
		return desc

	def can_pay_costs(self):
		if self.siege and self.caster.cur_hp < self.caster.max_hp:
			return False
		return Spell.can_pay_costs(self)

	def cast(self, x, y, channel_cast=False):

		if self.siege:
			self.caster.cur_hp -= self.caster.max_hp // 2

		if self.suicide:
			self.caster.kill()

		if self.max_channel and not channel_cast:
			unit_target = self.caster.level.get_unit_at(x, y)
			target = unit_target if unit_target else Point(x, y)
			
			buff = ChannelBuff(self.cast, target, 
							   cast_after_channel=self.cast_after_channel,
							   channel_check=lambda t: self.can_cast(t.x, t.y))

			self.caster.apply_buff(buff, self.max_channel)
			return

		start = Point(self.caster.x, self.caster.y)
		target = Point(x, y)

		for point in Bolt(self.caster.level, start, target, find_clear=not self.melt):
			if not self.beam:
				dtype = self.effect or self.damage_type
				if isinstance(dtype, list):
					dtype = random.choice(dtype)
				
				if self.proj_name:
					self.caster.level.projectile_effect(point.x, point.y, proj_name=self.proj_name, proj_origin=self.caster, proj_dest=target)
				else:
					self.caster.level.deal_damage(point.x, point.y, 0, dtype, self)
				yield
			else:
				self.hit(point.x, point.y)
			if self.melt and self.caster.level.tiles[point.x][point.y].is_wall():
				self.caster.level.make_floor(point.x, point.y)

		if not self.beam:
			self.hit(x, y)

		stagenum = 0
		for stage in Burst(self.caster.level, target, self.get_stat('radius')):
			stagenum += 1

			# Skip the first point, its already been damaged
			if stagenum == 1:
				continue
			for point in stage:
				self.hit(point.x, point.y)
			for i in range(self.radius):
				yield

	def get_impacted_tiles(self, x, y):
		tiles = set()
		tiles.add(Point(x, y))

		target = Point(x, y)

		if self.beam:
			for p in Bolt(self.caster.level, self.caster, target):
				tiles.add(p)

		if self.get_stat('radius'):
			for stage in Burst(self.caster.level, target, self.get_stat('radius')):
				for point in stage:
					tiles.add(point)

		return tiles				

	def get_ai_target(self):

		if self.radius:
			return self.get_corner_target(self.radius)
		else:
			return Spell.get_ai_target(self)

	def can_threaten(self, x, y):
		if self.radius:
			return self.can_threaten_corner(x, y, self.radius)
		else:
			return Spell.can_threaten(self, x, y)

	def hit(self, x, y):
		unit = self.caster.level.get_unit_at(x, y)
		dtype = self.damage_type
		if isinstance(dtype, list):
			dtype = random.choice(dtype)
		dealt = self.caster.level.deal_damage(x, y, self.get_stat('damage'), dtype, self)
		if unit and self.onhit:
			self.onhit(self.caster, unit)
		if unit and self.buff:
			unit.apply_buff(self.buff(), self.buff_duration)
		if dealt and self.drain:
			self.caster.deal_damage(-dealt, Tags.Heal, self)

class SimpleCurse(Spell):

	def __init__(self, buff, buff_duration, effect=None):
		self.buff = buff
		self.duration = buff_duration
		self.stackable = buff().stack_type == STACK_INTENSITY
		self.effect = effect
		Spell.__init__(self)
		if buff().buff_type == BUFF_TYPE_BLESS:
			self.target_allies = True
		self.description = "施加 %d 回合的%s" % (buff_duration, buff().name)
		

	def can_cast(self, x, y):
		unit = self.caster.level.get_unit_at(x, y)
		if not unit:
			return False
		if unit:
			if not self.stackable and unit.has_buff(self.buff):
				return False
		return Spell.can_cast(self, x, y)

	def cast_instant(self, x, y):
		unit = self.caster.level.get_unit_at(x, y)
		if unit:
			buff = self.buff()
			buff.caster = self.caster
			unit.apply_buff(buff, self.duration)
			if self.effect:
				for p in self.caster.level.get_points_in_line(self.caster, Point(x, y)):
					self.caster.level.show_effect(p.x, p.y, self.effect)

class SimpleSummon(Spell):

	def __init__(self, spawn_func, num_summons=1, cool_down=0, duration=0, max_channel=0, global_summon=False, path_effect=None):
		Spell.__init__(self)
		
		self.duration = duration

		spawn_name = spawn_func().name
		self.name = "召唤%s" % spawn_name
		self.num_summons = num_summons
		if num_summons > 1:
			self.name += '群'

		self.cool_down = cool_down

		if self.duration:
			spawn_name = "临时" + spawn_name

		if num_summons == 1:
			self.description = "召唤 1 个%s" % spawn_name
		else:
			self.description = "召唤 %d 个%s" % (self.num_summons, spawn_name)

		self.global_summon = global_summon
		if self.global_summon:
			self.description = " 于地图上的随机位置"

		self.spawn_func = spawn_func
		self.max_channel = max_channel
		if self.max_channel:
			self.description = "最多可以维持 %d 回合" % self.max_channel

		# How close to an enemy the ai needs to get the target
		self.ai_cast_radius = 2

		self.path_effect = path_effect

	def on_init(self):
		self.range = 0

	def get_ai_target(self):
		# Do not cast if there are no enemies
		if not any(are_hostile(self.caster, u) for u in self.caster.level.units):
			return None
		if self.range == 0:
			return Point(self.caster.x, self.caster.y)
		else:
			return self.get_corner_target(self.ai_cast_radius)

	def cast(self, x, y, channel_cast=False):
		if self.global_summon:
			ex = self.spawn_func()
			targets = [t for t in self.caster.level.iter_tiles() if self.caster.level.can_stand(t.x, t.y, ex)]
			if targets:
				target = random.choice(targets)
				x = target.x
				y = target.y

		if self.max_channel and not channel_cast:
			self.caster.apply_buff(ChannelBuff(self.cast, Point(x, y)), self.max_channel)
			return

		for i in range(self.num_summons):
			unit = self.spawn_func()
			if self.duration:
				unit.turns_to_death = self.duration
			self.summon(unit, Point(x, y), sort_dist=False)
			if self.path_effect:
				self.owner.level.show_path_effect(self.owner, unit, self.path_effect, minor=True)
			yield


class PullAttack(Spell):

	def __init__(self, damage=0, damage_type=Tags.Physical, range=3, pull_squares=1, color=None):
		Spell.__init__(self)
		self.damage = damage
		self.damage_type = damage_type
		self.range = range
		self.pull_squares = pull_squares
		self.name = "拉动攻击"
		self.color = color or Color(255, 255, 255)

	def get_description(self):
		return "将目标向施法者拉动  %d 格" % self.pull_squares

	def cast_instant(self, x, y):

		path = self.caster.level.get_points_in_line(self.caster, Point(x, y))
		for p in path[1:-1]:
			self.caster.level.flash(p.x, p.y, self.color)

		target_unit = self.caster.level.get_unit_at(x, y)

		if target_unit:
			pull(target_unit, self.caster, self.pull_squares)

			target_unit.deal_damage(self.damage, self.damage_type, self)


def pull(target, source, squares, find_clear=True):

	path = target.level.get_points_in_line(target, source, find_clear=find_clear, two_pass=find_clear)[1:-1][:squares]
	for p in path:
		if target.level.can_move(target, p.x, p.y, teleport=True):
			target.level.act_move(target, p.x, p.y, teleport=True)
		else:
			return False
	return True

# Push the target a certain number of square away from the source
# Return False if the target cannot be pushed to the location
def push(target, source, squares):
	dir_x = target.x - source.x
	dir_y = target.y - source.y

	mag_sq = dir_x * dir_x + dir_y * dir_y
	mag = math.sqrt(mag_sq)

	dir_x = dir_x / mag
	dir_y = dir_y / mag

	dest_x = round(target.x + 2*squares*dir_x)
	dest_y = round(target.y + 2*squares*dir_y)

	return pull(target, Point(dest_x, dest_y), squares, find_clear=False)
	
class HealAlly(Spell):

	def __init__(self, heal, range, tag=None):
		Spell.__init__(self)
		self.name = "治疗盟友"
		self.heal = heal
		self.range = range
		self.tag = tag

		self.description = "治疗友方 %d 点血量" % self.heal
		if self.tag:
			self.description = "治疗友方的%s %d 点血量" % (self.tag.name, self.heal)

		# For tooltips
		self.damage = heal
		self.damage_type = Tags.Heal

	def get_ai_target(self):
		units_in_range = self.caster.level.get_units_in_ball(Point(self.caster.x, self.caster.y), self.range)
		units_in_range = [u for u in units_in_range if not self.caster.level.are_hostile(self.caster, u)]
		units_in_range = [u for u in units_in_range if self.can_cast(u.x, u.y)]
		units_in_range = [u for u in units_in_range if not u.is_player_controlled]

		if self.tag:
			units_in_range = [u for u in units_in_range if self.tag in u.tags]

		wounded_units = [u for u in units_in_range if u.cur_hp < u.max_hp]
		if wounded_units:
			target = random.choice(wounded_units)
			return Point(target.x, target.y)
		else:
			return None

	def can_threaten(self, x, y):
		return False

	def cast_instant(self, x, y):
		unit = self.caster.level.get_unit_at(x, y)
		if unit:
			unit.deal_damage(-self.heal, Tags.Heal, self)

class StormCloud(Cloud):

	def __init__(self, owner, damage=10):
		Cloud.__init__(self)
		self.owner = owner
		self.duration = 5
		self.damage = damage
		self.color = Color(100, 100, 100)
		self.strikechance = .5
		self.name = "雷暴"
		self.source = None
		self.asset_name = 'thunder_cloud'

	def get_description(self):
		return "每回合有 %d%% 的几率对其中的单位造成 [%d_lightning:lightning] 点伤害\n%d 回合后消散" % (int(self.strikechance*100), self.damage, self.duration)

	def on_advance(self):
		if random.random() <= self.strikechance:
			self.level.deal_damage(self.x, self.y, self.damage, Tags.Lightning, self.source or self)

class BlizzardCloud(Cloud):

	def __init__(self, owner, damage=5):
		Cloud.__init__(self)
		self.owner = owner
		self.duration = 5
		self.damage = damage
		self.color = Color(100, 100, 100)
		self.name = "暴雪"
		self.asset_name = 'ice_cloud'
		self.source = None

	def get_description(self):
		return "每回合对其中的单位造成 [%d_ice:ice] 点伤害并有 50%% 的几率冻结\n%d 回合后消散" % (self.damage, self.duration)

	def on_advance(self):
		self.level.deal_damage(self.x, self.y, self.damage, Tags.Ice, self.source or self)
		unit = self.level.get_unit_at(self.x, self.y)
		if unit:
			if random.random() > .5:
				unit.apply_buff(FrozenBuff(), 1)

class FireCloud(Cloud):

	def __init__(self, owner, damage=6):
		Cloud.__init__(self)
		self.owner = owner
		self.duration = 4
		self.damage = damage
		self.color = Tags.Fire.color
		self.strikechance = .5
		self.name = "火风暴"
		self.description = "每回合对其中的生物造成 %d 火焰伤害" % self.damage
		self.asset_name = 'fire_cloud'

	def on_advance(self):
		self.level.deal_damage(self.x, self.y, self.damage, Tags.Fire, self)

class CloudGeneratorBuff(Buff):

	def __init__(self, cloud_func, radius, chance):
		Buff.__init__(self)
		self.cloud_func = cloud_func
		self.radius = radius
		self.chance = chance

		self.description = "在 %d 格的范围内召唤 %s" % (radius, cloud_func(None).name)

	def on_advance(self):
		for point in self.owner.level.get_points_in_ball(self.owner.x, self.owner.y, self.radius):
			unit = self.owner.level.get_unit_at(point.x, point.y)
			if unit and not are_hostile(unit, self.owner):
				continue
			if not self.owner.level.tiles[point.x][point.y].can_see:
				continue
			if random.random() < self.chance:
				self.owner.level.add_obj(self.cloud_func(owner=self.owner), point.x, point.y)

class SpiderWeb(Cloud):

	def __init__(self):
		Cloud.__init__(self)
		self.name = "蛛网"
		self.color = Color(210, 210, 210)
		self.description = "被踩踏时将非蜘蛛的单位眩晕 1 回合，之后消散\n\n火焰伤害会摧毁蛛网"
		self.duration = 12

		self.asset_name = 'web'

	def on_unit_enter(self, unit):
		if Tags.Spider not in unit.tags:
			unit.apply_buff(Stun(), 2)
			self.kill()

	def on_damage(self, dtype):
		if dtype == Tags.Fire:
			self.kill()

class PetrifyBuff(Stun):

	def __init__(self):
		Stun.__init__(self)
		self.name = "石化"
		self.color = Color(180, 180, 180)
		self.resists[Tags.Physical] = 75
		self.resists[Tags.Fire] = 75
		self.resists[Tags.Ice] = 100
		self.resists[Tags.Lightning] = 100
		self.asset = ['status', 'stoned']
		self.stack_type = STACK_NONE

		self.description = "行动不能"


class GlassPetrifyBuff(PetrifyBuff):

	def __init__(self):
		PetrifyBuff.__init__(self)
		self.resists[Tags.Physical] = -100
		self.name = "玻璃化"
		self.asset = ['status', 'glassed']
		self.color = Tags.Glass.color

	def on_applied(self, owner):
		if Tags.Glass in owner.tags:
			return ABORT_BUFF_APPLY
		return PetrifyBuff.on_applied(self, owner)

class ResistIce(Buff):

	def on_init(self):
		self.name = "抵抗冰"
		self.resists[Tags.Ice] = 50
		self.color = Tags.Ice.color
		self.asset = ['status', 'resist_ice']

class ResistFire(Buff):

	def on_init(self):
		self.name = "抵抗火"
		self.resists[Tags.Fire] = 50
		self.color = Tags.Fire.color
		self.asset = ['status', 'resist_fire']

class ResistLightning(Buff):

	def on_init(self):
		self.name = "抵抗雷"
		self.resists[Tags.Lightning] = 50
		self.color = Tags.Lightning.color
		self.asset = ['status', 'resist_lightning']

class ResistDark(Buff):

	def on_init(self):
		self.name = "抵抗神圣"
		self.resists[Tags.Holy] = 50
		self.color = Tags.Holy.color
		self.asset = ['status', 'resist_holy']

class ResistHoly(Buff):

	def on_init(self):
		self.name = "抵抗黑暗"
		self.resists[Tags.Dark] = 50
		self.color = Tags.Dark.color
		self.asset = ['status', 'resist_dark']


class Stoneskin(Buff):

	def on_init(self):
		self.name = "石肤"
		self.resists[Tags.Physical] = 50
		self.color = Tags.Physical.color
		self.asset = ['status', 'stoneskin']

# Raised when frozen is ended by damage
EventOnUnfrozen = namedtuple("EventOnUnfrozen", "unit dtype")
class FrozenBuff(Stun):

	def __init__(self):
		Stun.__init__(self)
		self.shatter_chance = 0
		self.name = "冻结"
		self.color = Tags.Ice.color

		self.owner_triggers[EventOnDamaged] = self.on_damage

		self.break_dtype = None

		self.description = "行动不能\n\n受到火焰或物理伤害时解冻"

		self.asset = ['status', 'frozen']

	def on_applied(self, owner):
		if owner.resists[Tags.Ice] >= 100:
			return ABORT_BUFF_APPLY
		return Stun.on_applied(self, owner)

	def on_damage(self, evt):
		if evt.damage_type in [Tags.Fire, Tags.Physical]:
			self.break_dtype = evt.damage_type
			self.owner.remove_buff(self)

	def on_unapplied(self):
		self.owner.level.event_manager.raise_event(EventOnUnfrozen(self.owner, self.break_dtype), self.owner)		
		Stun.on_unapplied(self)

class TrollRegenBuff(Buff):

	def on_init(self):
		self.name = "巨魔再生"

	def on_applied(self, owner):
		self.recently_burned = False
		self.owner_triggers[EventOnDamaged] = self.on_damage_taken

	def on_damage_taken(self, damage_event):
		if damage_event.damage_type == Tags.Fire:
			self.recently_burned = True

	def on_advance(self):
		if not self.recently_burned:
			if self.owner.cur_hp != self.owner.max_hp:
				self.owner.deal_damage(-5, Tags.Heal, self)
		self.recently_burned = False

	def get_tooltip(self):
		return "每回合回复 5 点血量，受到火焰伤害时无效"

	def get_tooltip_color(self):
		return Color(0, 255, 0)

class DamageAuraBuff(Buff):

	def __init__(self, damage, damage_type, radius, friendly_fire=False, melt_walls=False):
		Buff.__init__(self)
		self.damage = damage
		self.damage_type = damage_type
		self.radius = radius
		self.friendly_fire = friendly_fire
		self.source = None
		if isinstance(self.damage_type, Tag):
			self.name = "%s光环" % self.damage_type.name
		else:
			self.name = "伤害光环" 

		# Not used in base class, used in inherited classes
		self.damage_dealt = 0

		self.melt_walls = melt_walls

	def on_advance(self):

		effects_left = 7

		for unit in self.owner.level.get_units_in_ball(Point(self.owner.x, self.owner.y), self.radius):
			if unit == self.owner:
				continue

			if not self.friendly_fire and not self.owner.level.are_hostile(self.owner, unit):
				continue

			if isinstance(self.damage_type, list):
				damage_type = random.choice(self.damage_type)
			else:
				damage_type = self.damage_type
			self.damage_dealt += unit.deal_damage(self.damage, damage_type, self.source or self)
			effects_left -= 1

		# Show some graphical indication of this aura if it didnt hit much
		points = self.owner.level.get_points_in_ball(self.owner.x, self.owner.y, self.radius)
		points = [p for p in points if not self.owner.level.get_unit_at(p.x, p.y)]
		random.shuffle(points)
		for i in range(effects_left):
			if not points:
				break
			p = points.pop()
			if isinstance(self.damage_type, list):
				damage_type = random.choice(self.damage_type)
			else:
				damage_type = self.damage_type
			self.owner.level.deal_damage(p.x, p.y, 0, damage_type, source=self.source or self)

			# Wall melting
			if self.melt_walls and not self.owner.level.tiles[p.x][p.y].can_see:
				self.owner.level.make_floor(p.x, p.y)

	def can_threaten(self, x, y):
		return distance(self.owner, Point(x, y)) <= self.radius

	def get_tooltip(self):
		damage_type_str = '或'.join(t.name for t in self.damage_type) if isinstance(self.damage_type, list) else self.damage_type.name
		unit_type_str = '单位' if self.friendly_fire else '敌方单位'
		return "每回合对 %d 格的半径内的%s造成 %d 点%s伤害" % (self.radius, unit_type_str, self.damage, damage_type_str)

class HealAuraBuff(Buff):

	def __init__(self, heal, radius, whole_map=False, can_heal_player=False):
		Buff.__init__(self)
		self.name = "治疗光环"
		self.color = Tags.Heal.color
		self.heal = heal
		self.radius = radius
		self.whole_map = whole_map
		self.can_heal_player = can_heal_player

	def on_advance(self):
		if self.whole_map:
			units = list(self.owner.level.units)
		else:
			units = list(self.owner.level.get_units_in_ball(Point(self.owner.x, self.owner.y), self.radius))

		for unit in units:
			if unit.is_player_controlled and not self.can_heal_player:
				continue

			if unit == self.owner:
				continue

			if self.owner.level.are_hostile(self.owner, unit):
				continue

			if unit.cur_hp == unit.max_hp:
				continue

			unit.deal_damage(-self.heal, Tags.Heal, self)

	def get_tooltip(self):
		if not self.whole_map:
			return "每回合治疗 %d 格的半径内的友方 %d 点血量" % (self.radius, self.heal)
		else:
			return "每回合治疗所有友方 %d 点血量" % self.heal

class EssenceAuraBuff(Buff):

	def on_init(self):
		self.radius = 5

	def on_advance(self):
		for unit in self.owner.level.get_units_in_ball(Point(self.owner.x, self.owner.y), self.radius):
			if are_hostile(self.owner, unit):
				continue
			if unit ==  self.owner:
				continue
			if unit.turns_to_death:
				unit.turns_to_death += 1

class LeapAttack(Spell):

	def __init__(self, damage, range, damage_type=Tags.Physical, is_leap=True, charge_bonus=0, is_ghost=False):
		Spell.__init__(self)
		self.damage = damage
		self.damage_type = damage_type
		self.range = range
		self.is_leap = is_leap and not is_ghost
		self.charge_bonus = charge_bonus
		self.is_ghost = is_ghost
		self.name = "猛扑" if self.is_leap else "冲刺"
		self.requires_los = not self.is_ghost

	def get_leap_dest(self, x, y):
		target_points = list(self.caster.level.get_adjacent_points(Point(x, y), check_unit=True))
		random.shuffle(target_points)
		for point in target_points:
			if point == Point(x, y):
				continue

			path = self.caster.level.get_points_in_line(Point(x, y), Point(self.caster.x, self.caster.y), find_clear=not self.is_ghost)[1:-1]

			# Charge: check for path
			if not self.is_leap and not self.is_ghost:
				if not all(self.caster.level.can_stand(p.x, p.y, self.caster) for p in path):
					continue
			# Leap: check for LOS
			elif not self.is_ghost:
				if not self.caster.level.can_see(point.x, point.y, self.caster.x, self.caster.y):
					continue
			# Ghost: just check destination
			if not self.caster.level.can_move(self.caster, point.x, point.y, teleport=True):
				continue

			return point
		return None		

	def get_description(self):
		if self.is_leap:
			fmt = "飞跃攻击"
		elif self.is_ghost:
			fmt = "传送攻击"
		else:
			fmt = "冲刺攻击"
		if self.charge_bonus:
			fmt += "，每位移 1 格造成 %d 点额外伤害" % self.charge_bonus
		return fmt

	def can_cast(self, x, y):
		return Spell.can_cast(self, x, y) and (self.get_leap_dest(x, y) is not None)
			
	def cast(self, x, y):

		# Projectile

		leap_dest = self.get_leap_dest(x, y)
		path = self.caster.level.get_points_in_line(Point(self.caster.x, self.caster.y), Point(leap_dest.x, leap_dest.y), find_clear=not self.is_ghost)
		for point in path:
			self.caster.level.leap_effect(point.x, point.y, self.damage_type.color, self.caster)
			yield
		
		self.caster.level.act_move(self.caster, leap_dest.x, leap_dest.y, teleport=True)

		charge_bonus = self.charge_bonus * (len(path) - 2)
		self.caster.level.deal_damage(x, y, self.damage + charge_bonus, self.damage_type, self)


class ElementalEyeBuff(Buff):

	def __init__(self, damage_type, damage, freq):
		Buff.__init__(self)
		self.damage_type = damage_type
		self.damage = damage
		self.freq = freq
		self.cooldown = freq
		self.name = "元素之眼"

	def on_advance(self):

		self.cooldown -= 1
		if self.cooldown == 0:
			self.cooldown = self.freq


			possible_targets = self.owner.level.units
			possible_targets = [t for t in possible_targets if self.owner.level.are_hostile(t, self.owner)]
			possible_targets = [t for t in possible_targets if self.owner.level.can_see(t.x, t.y, self.owner.x, self.owner.y)]

			if possible_targets:
				target = random.choice(possible_targets)
				self.owner.level.queue_spell(self.shoot(Point(target.x, target.y)))
				self.cooldown = self.freq
			else:
				self.cooldown = 1


	def shoot(self, target):
		path = self.owner.level.get_points_in_line(Point(self.owner.x, self.owner.y), target, find_clear=True)

		for point in path:
			self.owner.level.deal_damage(point.x, point.y, 0, self.damage_type, self)
			yield

		self.owner.level.deal_damage(target.x, target.y, self.damage, self.damage_type, self)

class cockatriceScaleArmorBuff(Buff):

	def on_init(self):
		self.name = "石化护甲"

	def on_applied(self, owner):
		self.global_triggers[EventOnSpellCast] = self.on_spell_cast

	def on_spell_cast(self, evt):
		if evt.caster == self.owner:
			return
		if evt.x != self.owner.x:
			return
		if evt.y != self.owner.y:
			return
		evt.caster.apply_buff(PetrifyBuff(), 2)

class ElementalReincarnationBuff(Buff):

	def on_applied(self, owner):
		self.global_triggers[EventOnDamaged] = self.on_damage
		self.buff_type = BUFF_TYPE_BLESS

	def on_damage(self, damage_event):
		if damage_event.unit.cur_hp > 0:
			return

		if self.owner.level.are_hostile(self.owner, damage_event.unit):
			return

		if self.owner == damage_event.unit:
			return

		if Tags.Elemental in damage_event.unit.tags:
			return

		if damage_event.damage_type in [Tags.Lightning, Tags.Fire]:
			self.owner.level.queue_spell(self.raise_elemental(damage_event))

	def raise_elemental(self, damage_event):
		if self.owner.level.get_unit_at(damage_event.unit.x, damage_event.unit.y):
			return

		elemental = Unit()
		elemental.name = "Elemental %s Revenant" % damage_event.unit.name
		elemental.sprite.char = damage_event.unit.sprite.char
		elemental.sprite.color = damage_event.damage_type.color
		elemental.max_hp = max(1, damage_event.unit.max_hp // 2)

		elemental.spells = list(damage_event.unit.spells)
		
		for spell in elemental.spells:
			if hasattr(spell, 'damage_type'):
				spell.damage_type = damage_event.damage_type

		elemental.tags.append(Tags.Elemental)

		elemental.resists[damage_event.damage_type] = 100
		elemental.description = "An elemental reincarnation of a %s" % damage_event.unit.name
		elemental.team = self.owner.team
		elemental.stationary = damage_event.unit.stationary
		elemental.flying = damage_event.unit.flying
		elemental.turns_to_death = 7
		
		self.owner.level.add_obj(elemental, damage_event.unit.x, damage_event.unit.y)
		yield

class GlobalAttrBonus(Buff):

	def __init__(self, attr, bonus):
		Buff.__init__(self)
		self.attr = attr
		self.bonus = bonus
		self.global_bonuses[attr] = bonus
		self.buff_type = BUFF_TYPE_BLESS

class MonsterTeleport(Spell):

	def on_init(self):
		self.name = "传送"
		self.description = "传送到随机的格子"
		self.range = 10
		self.can_target_self = True
		self.cool_down = 4
		self.requires_los = False

	def get_ai_target(self):
		return self.caster

	def can_threaten(self, x, y):
		return False

	def cast_instant(self, x, y):
		randomly_teleport(self.caster, self.range, flash=True, requires_los=self.requires_los)

def randomly_teleport(unit, radius, flash=True, requires_los=False):
		blink_targets = [p for p in unit.level.get_points_in_ball(unit.x, unit.y, radius) if unit.level.can_stand(p.x, p.y, unit)]
		if not blink_targets:
			return

		if requires_los:
			blink_targets = [p for p in blink_targets if unit.level.can_see(unit.x, unit.y, p.x, p.y)]

		if not blink_targets:
			return

		target = random.choice(blink_targets)
		if flash:
			unit.level.flash(unit.x, unit.y, Tags.Translocation.color)
		
		unit.level.act_move(unit, target.x, target.y, teleport=True)
		
		if flash:
			unit.level.flash(unit.x, unit.y, Tags.Translocation.color)

def drain_max_hp(unit, hp):
	unit.max_hp -= hp
	unit.max_hp = max(1, unit.max_hp)
	unit.cur_hp = min(unit.cur_hp, unit.max_hp)

class RegenBuff(Buff):

	def __init__(self, heal):
		Buff.__init__(self)
		self.heal = heal
		self.stack_type = STACK_INTENSITY
		self.name = "再生 %d" % heal
		self.description = "每回合回复 %d 点血量" % self.heal
		self.buff_type = BUFF_TYPE_BLESS
		self.asset = ['status', 'heal']

	def on_advance(self):
		if self.owner.cur_hp < self.owner.max_hp:
			self.owner.deal_damage(-self.heal, Tags.Heal, self)


class ShieldRegenBuff(Buff):

	def __init__(self, shield_max, shield_freq):
		Buff.__init__(self)
		self.shield_max = shield_max
		self.shield_freq = shield_freq
		self.turns = 0
		self.buff_type = BUFF_TYPE_BLESS

	def on_advance(self):
		if self.owner.shields >= self.shield_max:
			self.turns = 0
		else:
			self.turns += 1
			if self.turns == self.shield_freq:
				self.owner.add_shields(1)
				self.turns = 0

	def get_tooltip(self):
		return "每 %d 回合获得 1 点护盾，最多 %d 点" % (self.shield_freq, self.shield_max)

class ReincarnationBuff(Buff):

	def __init__(self, lives=1):
		Buff.__init__(self)
		self.lives = lives
		self.owner_triggers[EventOnDeath] = self.on_death
		self.name = "复生 %d" % self.lives
		self.buff_type = BUFF_TYPE_BLESS
		self.duration = 0
		self.turns_to_death = None
		self.shields = 0
		self.max_hp = 0

	def on_attempt_apply(self, owner):
		# Do not allow a unit to gain multiple reincarnation buffs
		if owner.has_buff(ReincarnationBuff):
			return False
		return True

	def on_applied(self, owner):
		# Cache the initial turns to death value
		if owner.turns_to_death is not None:
			if owner.source and isinstance(owner.source, Spell) and owner.source.get_stat('minion_duration'):
				self.turns_to_death = owner.source.get_stat('minion_duration')
			else:
				self.turns_to_death = owner.turns_to_death
		# Cache initial shields
		self.shields = self.owner.shields
		# Cache max hp in case it gets reduced
		self.max_hp = self.owner.max_hp


	def get_tooltip(self):
		return "死亡时复生 (%d 次)" % self.lives

	def on_death(self, evt):
		if self.lives >= 1:

			to_remove = [b for b in self.owner.buffs if b.buff_type != BUFF_TYPE_PASSIVE]
			for b in to_remove:
				self.owner.remove_buff(b)

			self.lives -= 1
			self.owner.level.queue_spell(self.respawn())
			self.name = "复生 %d" % self.lives

	def respawn(self):
		self.owner.killed = False

		respawn_points = [p for p in self.owner.level.iter_tiles() if self.owner.level.can_stand(p.x, p.y, self.owner)]
		if respawn_points:

			# Restore original shields
			self.owner.shields = self.shields

			# Heal any max hp damage
			self.owner.max_hp = max(self.owner.max_hp, self.max_hp)

			dest = random.choice(respawn_points)
			self.owner.cur_hp = self.owner.max_hp
			self.owner.turns_to_death = self.turns_to_death
			self.owner.level.add_obj(self.owner, dest.x, dest.y)

		if self.lives == 0:
			self.owner.remove_buff(self)
		# Reapply self if removed- happens if reincarnation was granted as a non passive buff
		elif self not in self.owner.buffs:
			self.owner.apply_buff(self, self.turns_left)

		# Stun for 1 turn so units dont teleport next to stuff and kill them while they reincarnate
		self.owner.apply_buff(Stun(), 1)
		yield

class ShieldSightSpell(Spell):

	def __init__(self, cool_down, shields):
		Spell.__init__(self)
		self.shields = shields
		self.name = "群体保护盟友"
		self.description = "给予视线里的友方 1 点护盾，最多 %d 点" % self.shields
		self.cool_down = cool_down
		self.buff_type = BUFF_TYPE_BLESS
		
	def on_init(self):
		self.range = 0

	def cast_instant(self, x, y):
		units = [u for u in self.caster.level.get_units_in_los(Point(x, y)) if not self.caster.level.are_hostile(u, self.caster)]
		for unit in units:
			if unit.shields < self.shields:
				unit.add_shields(1)

class Poison(Buff):

	def on_init(self):
		self.stack_type = STACK_NONE
		self.damage = 1
		self.color = Tags.Poison.color
		self.name = "中毒"
		self.buff_type = BUFF_TYPE_CURSE
		self.asset = ['status', 'poison']
		self.description = "每回合受到 1 点毒素伤害，无法回复血量"
		self.resists[Tags.Heal] = 100

	def on_applied(self, owner):
		if owner.resists[Tags.Poison] >= 100:
			return ABORT_BUFF_APPLY

	def on_advance(self):
		self.owner.deal_damage(self.damage, Tags.Poison, self)

def remove_buff(caster, target):
	buffs = [b for b in target.buffs if b.buff_type == BUFF_TYPE_BLESS]
	if not buffs:
		return
	to_remove = random.choice(buffs)
	if target.is_alive():
		target.remove_buff(to_remove)

class Soulbound(Buff):

	def __init__(self, guardian):
		Buff.__init__(self)
		self.owner_triggers[EventOnDamaged] = self.on_self_damage
		self.global_triggers[EventOnDeath] = self.on_death
		self.guardian = guardian
		self.name = "命匣"
		self.asset = ['status', 'soulbound']
		self.color = Tags.Dark.color

	def get_buff_tooltip(self):
		return "在它的命匣 %s 被破坏之前无法死亡"

	def on_advance(self):
		if not self.guardian.is_alive():
			self.owner.remove_buff(self)

	def on_self_damage(self, damage):
		# Do not protect if guardian is gone.  This can happen if the guardian is banished by mordred.
		if not self.guardian.is_alive():
			self.owner.remove_buff(self)
			return

		if self.owner.cur_hp <= 0:
			self.owner.cur_hp = 1

	def on_death(self, evt):
		if evt.unit == self.guardian:
			self.owner.remove_buff(self)


class PainMirror(Buff):

	def __init__(self, source=None):
		Buff.__init__(self)
		self.source = source

	def on_init(self):
		self.name = "伤害反射"
		self.owner_triggers[EventOnDamaged] = self.on_damage
		self.color = Tags.Dark.color

	def on_damage(self, event):
		self.owner.level.queue_spell(self.reflect(event.damage))

	def reflect(self, damage):
		for u in self.owner.level.get_units_in_los(self.owner):
			if are_hostile(self.owner, u):
				u.deal_damage(damage, Tags.Dark, self.source or self)
				yield

class BloodrageBuff(Buff):
	
	def __init__(self, bonus):
		self.bonus = bonus
		Buff.__init__(self)

	def on_init(self):
		self.name = '血怒'
		self.color = Tags.Demon.color
		self.asset = ['status', 'bloodlust']
		self.global_bonuses['damage'] = self.bonus
		self.stack_type	= STACK_INTENSITY	
		self.description = "伤害增加 %d 点" % self.bonus

def bloodrage(amount):
	def onhit(caster, target):
		caster.apply_buff(BloodrageBuff(amount), 10)
	return onhit

class ClarityBuff(Buff):

	def on_init(self):
		self.description = "无法眩晕"

	def on_pre_advance(self):
		buffs = [b for b in self.owner.buffs if isinstance(b, Stun)]
		for b in buffs:
			self.owner.remove_buff(b)

def ProjectileUnit():

	unit = Unit()
	unit.max_hp = 8

	unit.resists[Tags.Physical] = 100
	unit.resists[Tags.Dark] = 100
	unit.resists[Tags.Holy] = 100
	unit.resists[Tags.Fire] = 100
	unit.resists[Tags.Lightning] = 100
	unit.resists[Tags.Arcane] = 100
	unit.resists[Tags.Ice] = 100

	#unit.debuff_immune = True
	#unit.buff_immune = True

	unit.flying = True

	return unit

class Thorns(Buff):

	def __init__(self, damage, dtype=Tags.Physical):
		self.damage = damage
		self.dtype = dtype
		Buff.__init__(self)
		self.name = "荆棘"
		self.description = "受到近战攻击时反弹 %d 点%s伤害" % (self.damage, self.dtype.name)
		self.color = dtype.color

	def on_init(self):
		self.global_triggers[EventOnSpellCast] = self.on_spell

	def on_spell(self, evt):
		if evt.x != self.owner.x or evt.y != self.owner.y:
			return
		# Distance is implied to be 1 if its a leap or a melee
		if not (isinstance(evt.spell, LeapAttack) or evt.spell.melee):
			return
		self.owner.level.queue_spell(self.do_thorns(evt.caster))

	def do_thorns(self, unit):
		unit.deal_damage(self.damage, self.dtype, self)
		yield

class MatureInto(Buff):

	def __init__(self, spawner, duration):
		Buff.__init__(self)
		self.spawner = spawner
		self.spawn_name = None
		self.mature_duration = duration

	def on_advance(self):
		self.mature_duration -= 1
		if self.mature_duration <= 0:
			self.owner.kill(trigger_death_event=False)
			new_unit = self.spawner()
			new_unit.team = self.owner.team
			new_unit.source = self.owner.source
			p = self.owner.level.get_summon_point(self.owner.x, self.owner.y, radius_limit=8, flying=new_unit.flying)
			if p:
				self.owner.level.add_obj(new_unit, p.x, p.y)


	def get_tooltip(self):
		if not self.spawn_name:
			self.spawn_name = self.spawner().name
		return "%d 回合后成长为 %s" % (self.mature_duration, self.spawn_name)

class SpawnOnDeath(Buff):

	def __init__(self, spawner, num_spawns):
		Buff.__init__(self)
		self.spawner = spawner
		self.num_spawns = num_spawns
		self.description = "死亡时生成 %d 个%s" % (self.num_spawns, self.spawner().name)
		self.owner_triggers[EventOnDeath] = self.on_death
		self.apply_bonuses = True

	def on_death(self, evt):
		for i in range(self.num_spawns):
			unit = self.spawner()
			# Inherit source- this propogates minion bonuses from shrines and skills
			if self.owner.source and self.apply_bonuses:
				unit.source = self.owner.source
				apply_minion_bonuses(self.owner.source, unit)
			self.summon(unit)

class RespawnAs(Buff):

	def __init__(self, spawner):
		Buff.__init__(self)
		self.spawner = spawner
		self.spawn_name = None
		self.get_tooltip() # populate name
		self.name = "重生为 %s" % self.spawn_name

	def on_init(self):
		self.owner_triggers[EventOnDamaged] = self.on_damage

	def on_damage(self, evt):
		if self.owner.cur_hp <= 0:
			# Supress death events- this creature isn't really dying, its respawning
			self.owner.kill(trigger_death_event=False)
			self.respawn()

	def respawn(self):
		new_unit = self.spawner()
		new_unit.team = self.owner.team
		new_unit.source = self.owner.source
		new_unit.parent = self.owner
		p = self.owner.level.get_summon_point(self.owner.x, self.owner.y, radius_limit=8, flying=new_unit.flying)
		if p:
			self.owner.level.add_obj(new_unit, p.x, p.y)
		

	def get_tooltip(self):
		if not self.spawn_name:
			self.spawn_name = self.spawner().name
		return "血量降低到 0 时变换为 %s" % self.spawn_name

class SimpleBurst(Spell):

	def __init__(self, damage, radius, damage_type=Tags.Physical, cool_down=0, ignore_walls=False, onhit=None, extra_desc=None):
		Spell.__init__(self)
		self.damage = damage
		self.damage_type = damage_type
		self.name = "%s爆破" % self.damage_type.name
		self.cool_down = cool_down
		self.radius = radius
		self.friendly_fire = True
		self.ignore_walls = ignore_walls
		self.onhit = onhit
		self.extra_desc = extra_desc

	def on_init(self):
		self.range = 0
		
	def get_ai_target(self):
		for p in self.get_impacted_tiles(self.caster.x, self.caster.y):
			u = self.caster.level.get_unit_at(p.x, p.y)
			if u and are_hostile(u, self.caster):
				return self.caster

		return None

	def get_description(self):
		desc = "在施法者周围爆裂造成伤害"
		if self.ignore_walls:
			desc += "\n爆破无视墙壁"
		if self.extra_desc:
			desc += '\n'
			desc += self.extra_desc
		return desc

	def get_impacted_tiles(self, x, y):
		for stage in Burst(self.caster.level, Point(x, y), self.get_stat('radius'), ignore_walls=self.ignore_walls):
			for p in stage:
				yield p

	def can_threaten(self, x, y):
		if distance(self.caster, Point(x, y)) > self.radius:
			return False

		# Potential optimization- only make the aoe once per frame
		return Point(x, y) in list(self.get_impacted_tiles(self.caster.x, self.caster.y))

	def cast_instant(self, x, y):
		for p in self.get_impacted_tiles(x, y):
			if p.x == self.caster.x and p.y == self.caster.y:
				continue
			self.caster.level.deal_damage(p.x, p.y, self.damage, self.damage_type, self)
			if self.onhit:
				unit = self.caster.level.get_unit_at(p.x, p.y)
				if unit:
					self.onhit(self.caster, unit)


def spawn_webs(unit):

	adj = unit.level.get_points_in_ball(unit.x, unit.y, 1.5)
	candidates = [p for p in adj if unit.level.get_unit_at(p.x, p.y) is None and unit.level.tiles[p.x][p.y].can_see]

	if candidates:
		p = random.choice(candidates)
		web = SpiderWeb()
		web.owner = unit
		unit.level.add_obj(web, p.x, p.y)


def raise_skeleton(owner, unit, source=None):
	if unit.has_been_raised:
		return

	if Tags.Living not in unit.tags:
		return

	unit.has_been_raised = True

	skeleton = Unit()
	skeleton.name = "骷髅%s" % unit.name
	skeleton.sprite.char = 's'
	if unit.max_hp >= 40:
		skeleton.sprite.char = 'S'
	skeleton.sprite.color = Color(201, 213, 214)
	skeleton.max_hp = unit.max_hp
	skeleton.spells.append(SimpleMeleeAttack(5))
	skeleton.tags.append(Tags.Undead)
	skeleton.stationary = unit.stationary
	skeleton.team = owner.team
	skeleton.flying = unit.flying
	skeleton.source = source

	p = unit.level.get_summon_point(unit.x, unit.y, flying=unit.flying)
	if p:
		owner.level.summon(owner=owner, unit=skeleton, target=p)
		return skeleton
	else:
		return None

class DeathExplosion(Buff):

	def __init__(self, damage, radius, damage_type):
		Buff.__init__(self)
		self.description = "死亡时自爆，在 %d 格范围内造成 %d 点%s伤害" % (radius, damage, damage_type.name)
		self.damage = damage
		self.damage_type = damage_type
		self.radius = radius
		self.name = "自爆"

	def on_applied(self, owner):
		self.owner_triggers[EventOnDeath] = self.on_death

	def on_death(self, death_event):
		self.owner.level.queue_spell(self.explode(self.owner.level, self.owner.x, self.owner.y))

	def explode(self, level, x, y):
		for stage in Burst(self.owner.level, self.owner, self.radius):
			for point in stage:
				self.owner.level.deal_damage(point.x, point.y, self.damage, self.damage_type, self)
			yield

class KingSpell(Spell):

	def __init__(self, spawner):
		Spell.__init__(self)
		self.spawner = spawner

	def on_init(self):
		self.name = "呼唤王国"
		self.range = 0
		self.cool_down = 10
		self.max_charges = 0

	def get_description(self):
		return "生成 2 个%s刷怪笼" % self.spawner().name

	def cast_instant(self, x, y):
		for i in range(2):
			p = self.caster.level.get_summon_point(x, y, radius_limit=5, sort_dist=False)
			if not p:
				return
			lair = MonsterSpawner(self.spawner)
			lair.team = self.caster.team
			
			if self.owner.source:
				lair.source = self.owner.source
				apply_minion_bonuses(lair.source, lair)

			self.summon(lair, p)

class Generator2Buff(Buff):

	def __init__(self, spawner):
		self.spawner = spawner
		self.example_monster = self.spawner()
		Buff.__init__(self)

	def on_init(self):
		self.min_turns = 7
		self.max_turns = 10
		self.turns = random.randint(self.min_turns, self.max_turns)

	def on_advance(self):
		# Dont spawn while stunned
		if self.owner.is_stunned():
			return
		self.turns -= 1
		if self.turns == 0:
			unit = self.spawner()
			if self.owner.source:
				unit.source = self.owner.source
				apply_minion_bonuses(self.owner.source, unit)
			
			self.summon(unit)
			self.turns = random.randint(self.min_turns, self.max_turns)

	def get_tooltip(self):
		return "每 %d to %d 回合生成 1 个%s\n\n距离下次: %d 回合" % (self.min_turns, self.max_turns, self.example_monster.name, self.turns)

def MonsterSpawner(spawn_func):
	unit = Unit()
	example_monster = spawn_func()
	unit.sprite = example_monster.sprite
	unit.sprite.color = Color(0, 0, 0)
	unit.name = "%s刷怪笼" % example_monster.name
	unit.max_hp = 20
	unit.sprite.bg_color = Color(255, 255, 255)
	unit.buffs.append(Generator2Buff(spawn_func))
	unit.stationary = True
	unit.is_lair = True
	return unit

class WizardNightmare(Spell):

	def __init__(self, damage_type=None):
		if not damage_type:
			damage_type = [Tags.Dark, Tags.Arcane]
		self.damage_type = damage_type
		Spell.__init__(self)

	def on_init(self):
		self.name = "梦魇光环"
		self.cool_down = 16
		self.duration = 8
		self.radius = 7
		self.range = 0
		dtype_str = self.damage_type.name if isinstance(self.damage_type, str) else '或'.join([t.name for t in self.damage_type])
		self.description = "每回合对范围内的敌人造成 2 点%s伤害" % dtype_str

	def get_ai_target(self):
		for u in self.caster.level.get_units_in_ball(self.caster, radius=self.radius):
			if are_hostile(u, self.caster):
				return self.caster
		return None


	def cast_instant(self, x, y):
		buff = DamageAuraBuff(damage=2, damage_type=self.damage_type, radius=self.get_stat('radius'))
		buff.name = buff.name or "梦魇光环"
		self.caster.apply_buff(buff, self.get_stat('duration'))

class WizardSelfBuff(Spell):

	def __init__(self, buff, duration, cool_down=0):
		self.buff = buff
		self.duration = duration
		Spell.__init__(self)
		self.cool_down = cool_down
		self.description = "施加 %d 回合的%s\n" % (duration, self.buff().name)
		
	def on_init(self):
		self.range = 0
		self.name = self.buff().name

	def get_ai_target(self):
		if not self.caster.has_buff(self.buff):
			return self.caster
		return None

	def cast_instant(self, x, y):
		self.caster.apply_buff(self.buff(), self.get_stat('duration'))

class WizardHealAura(Spell):

	def __init__(self, heal=2, duration=8, cool_down=16, radius=7):
		Spell.__init__(self)
		self.heal = heal
		self.duration = duration
		self.cool_down = 16
		self.radius = radius
		self.description = "每回合治疗 [%d_tile:radius] 格半径内的友方 [%d_HP:heal] 点血量，持续 [%d_turns:duration] 回合" % (self.radius, self.heal, self.duration)
		

	def get_ai_target(self):
		for u in self.caster.level.get_units_in_ball(self.caster, radius=self.radius):
			if not are_hostile(u, self.caster) and u.cur_hp < u.max_hp:
				return self.caster
		return None

	def on_init(self):
		self.name = "治疗光环"
		self.range = 0

	def cast_instant(self, x, y):
		self.caster.apply_buff(HealAuraBuff(heal=self.get_stat('heal'), radius=self.get_stat('radius')), self.get_stat('duration'))

class WizardBloodlust(Spell):

	def on_init(self):
		self.name = "渴血"
		self.bonus = 3
		self.radius = 5
		self.range = 0
		self.duration = 5
		self.cool_down = 10
		self.damage_type = Tags.Fire

	def get_description(self):
		return "给 [%d_tile:radius] 格范围内的友方增加 %d 点伤害，持续 [%d_turns:duration] 回合" % (self.bonus, self.radius, self.duration)

	def cast_instant(self, x, y):
		for p in self.caster.level.get_points_in_ball(self.caster.x, self.caster.y, self.radius):
			unit = self.caster.level.get_unit_at(p.x, p.y)
			if unit and not are_hostile(unit, self.caster):
				bloodlust = BloodrageBuff(self.bonus)
				unit.apply_buff(bloodlust, self.duration)

def drain_frenzy(caster, target, spell, bonus):
	caster.deal_damage(-spell.damage, Tags.Heal, spell)
	caster.apply_buff(BloodrageBuff(bonus), 10)	

class GlassReflection(Buff):

	def on_init(self):
		self.name = "咒术反射"
		self.global_triggers[EventOnSpellCast] = self.on_spell_cast

	def on_spell_cast(self, evt):
		if evt.x == self.owner.x and evt.y == self.owner.y and Tags.Sorcery in evt.spell.tags:
			self.owner.level.queue_spell(self.reflect(evt))

	def reflect(self, evt):
		spell = type(evt.spell)()
		spell.cur_charges = 1
		spell.caster = self.owner
		spell.owner = self.owner
		spell.statholder = evt.caster

		if spell.can_cast(evt.caster.x, evt.caster.y):
			self.owner.level.act_cast(self.owner, spell, evt.caster.x, evt.caster.y)

		yield

	def get_tooltip(self):
		return "当这个单位被作为巫术法术的目标时，这个单位对施法者施放一个一样的法术"

class ShieldAllySpell(Spell):

	def __init__(self, shields=1, range=5, cool_down=0):
		self.shields = shields
		Spell.__init__(self)
		self.range = range
		self.cool_down = cool_down

	def on_init(self):
		self.name = "单体保护盟友"
		self.description = "给予单体友方 %d 点护盾，最多 %d 点" % (self.shields, self.shields)
		self.target_allies = True

	def cast_instant(self, x, y):
		unit = self.caster.level.get_unit_at(x, y)
		if unit and unit.shields < self.shields:
			unit.add_shields(self.shields - unit.shields)

	def can_cast(self, x, y):
		unit = self.caster.level.get_unit_at(x, y)
		if unit and unit.shields < self.shields:
			return Spell.can_cast(self, x, y)
		else:
			return False

class WizardBlizzard(Spell):

	def on_init(self):
		self.name = "暴风雪"
		self.description = "生成一个半径 3 格的暴风雪"
		self.radius = 4
		self.cool_down = 10
		self.range = 8
		# For tooltip color
		self.damage_type = Tags.Ice

	def get_ai_target(self):
		return self.get_corner_target(self.radius)

	def cast(self, x, y):
		for stage in Burst(self.caster.level, Point(x, y), self.get_stat('radius')):
			for p in stage:
				cloud = BlizzardCloud(self.caster)
				self.caster.level.add_obj(cloud, p.x, p.y)
			yield

class WizardQuakeport(Spell):

	def on_init(self):
		self.name = "空间震"
		self.description = "传送到目标点并制造地震"
		self.range = 12
		self.cool_down = 19
		self.can_target_self = True

	def get_ai_target(self):
		return self.caster

	def cast(self, x, y):
		randomly_teleport(self.caster, radius=self.range)
		yield

		points = list(self.caster.level.get_points_in_ball(self.caster.x, self.caster.y, 4))
		random.shuffle(points)

		def is_important_floor(p):
			# Not a floor = certainly not an IMPORTANT floor
			if not self.caster.level.tiles[p.x][p.y].can_walk:
				return False
			# If floor, and all adjacent tiles are floor, unimportant
			return all(self.caster.level.tiles[q.x][q.y].can_walk for q in self.caster.level.get_adjacent_points(p, filter_walkable=False))

		for p in points:
			# Dont mess with floors, as this could make the level unpathable, and we dont want this spell to do that.
			if is_important_floor(p):
				continue

			unit = self.caster.level.get_unit_at(p.x, p.y)
			prop = self.caster.level.tiles[p.x][p.y].prop
			if random.random() < .65:
				self.caster.level.deal_damage(p.x, p.y, self.get_stat('damage'), Tags.Physical, self)
				if random.random() < .7:
					self.caster.level.make_floor(p.x, p.y)
				elif not unit and not prop:
					if random.random() < .5:
						self.caster.level.make_wall(p.x, p.y)
					else:
						self.caster.level.make_chasm(p.x, p.y)
			if random.random() < .25:
				yield

class FireProtection(Spell):
	
	def on_init(self):
		self.name = "防护火焰"
		self.duration = 8
		self.description = "给予施法者与盟友 50%% 的火焰抗性，持续 %d 回合" % self.duration
		self.cool_down = 12
		self.range = 0

	def cast(self, x, y):
		for u in self.caster.level.units:
			if not are_hostile(u, self.caster):
				u.apply_buff(ResistFire(), self.get_stat('duration'))
				yield

class TeleportyBuff(Buff):

	def __init__(self, radius=3.5, chance=.25, flash = None, hop=False):
		Buff.__init__(self)
		self.flash = flash
		self.radius = radius
		self.chance = chance
		self.hop = hop
		self.buff_type = BUFF_TYPE_PASSIVE
		self.name = "被动传送"

	def on_advance(self):
		if random.random() > self.chance:
			return

		if self.owner.is_stunned():
			return

		# Dont interupt channels, its dumb
		if self.owner.has_buff(ChannelBuff):
			return

		randomly_teleport(self.owner, self.radius, requires_los=self.hop)

	def get_tooltip(self):
		moveword = "hop" if self.hop else "blink"
		return "每回合有 %d%% 的几率%s到距离 %d 格的随机位置" % (int(self.chance * 100), moveword, self.radius)

	def get_tooltip_color(self):
		return Tags.Sorcery.color

# Apply bonuses to a summoned unit
def apply_minion_bonuses(obj, unit):
	if not hasattr(obj, 'get_stat'):
		return
	unit.max_hp = obj.get_stat('minion_health', base=unit.max_hp)
	for s in unit.spells:
		if hasattr(s, 'damage'):
			s.damage = obj.get_stat('minion_damage', base=s.damage)
		if hasattr(s, 'range') and s.range >= 2:
			s.range = obj.get_stat('minion_range', base=s.range)

	# Make the unit temporary iff the obj has minion duration bonus or it is already temporary.  Give it all applicable bonuses if it does.
	if hasattr(obj, 'minion_duration'):
		unit.turns_to_death = obj.get_stat('minion_duration')
	elif unit.turns_to_death:
		unit.turns_to_death = obj.get_stat('minion_duration', unit.turns_to_death)


class TouchedBySorcery(Buff):

	def __init__(self, element):
		self.element = element
		Buff.__init__(self)

	def on_init(self):
		self.resists[self.element] = 100
		self.name = "Touched by %s" % self.element.name
		self.color = self.element.color
		spell = SimpleRangedAttack(damage=5, range=7, damage_type=self.element)
		spell.name = "Sorcery"
		self.spells = [spell]
		self.asset = ['status', '%s_eye' % self.element.name.lower()]

def Champion(unit):
	unit.asset_name = unit.get_asset_name() + "_champion"
	unit.name = unit.name.replace('Knight', 'Champion')
	unit.max_hp *= 4
	for s in unit.spells:
		s.damage += s.damage // 2

	return unit

class Acidified(Buff):

	def on_init(self):
		self.name = "酸化"
		self.resists[Tags.Poison] = -100
		self.buff_type = BUFF_TYPE_CURSE
		self.asset = ['status', 'amplified_poison']
		self.color = Tags.Poison.color

class Electrified(Buff):

	def on_init(self):
		self.name = "磁化"
		self.resists[Tags.Lightning] = -10
		self.buff_type = BUFF_TYPE_CURSE
		self.stack_type	= STACK_INTENSITY
		self.asset = ['status', 'amplified_lightning']
		self.color = Tags.Lightning.color