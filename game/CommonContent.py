from Level import *

def get_spawn_min_max(difficulty):

	spawn_levels = [
		(1, 1), # 1
		(1, 2), # 2
		(2, 2), # 3 
		(2, 3), # 4
		(2, 3), # 5 
		(2, 4), # 6
		(3, 4), # 7
		(3, 4), # 8
		(3, 5), # 9
		(3, 5), # 10
		(4, 5), # 11
		(4, 5), # 12
		(5, 6), # 13
		(5, 6), # 14
		(6, 7), # 15
		(6, 7), # 16
		(7, 7), # 17
		(8, 8), # 18
		(8, 9), # 19
		(9, 9), # 20
	]


	# This formula is weird and appears to do very strange things but im not going to change it now because balance is good
	index = min(difficulty - 1, len(spawn_levels) - 1)

	min_level, max_level = spawn_levels[index]
	return min_level, max_level

class SimpleMeleeAttack(Spell):

	def __init__(self, damage=1, buff=None, buff_duration=0, damage_type=Tags.Physical, onhit=None, attacks=1, trample=False, drain=False):
		Spell.__init__(self)
		self.name = "Melee Attack"
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

			# Deal the damage
			dealt = self.caster.level.deal_damage(x, y, self.get_stat('damage'), self.damage_type, self)
			if self.drain:
				self.caster.deal_damage(-dealt, Tags.Heal, self)

			if unit and unit.is_alive():
				if self.buff:		
					unit.apply_buff(self.buff(), self.buff_duration)
				
			if unit:
				if self.trample and unit.can_teleport():

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
			desc += "Applies %s for %d turns.  " % (self.buff_name, self.buff_duration)
		if self.attacks > 1:
			desc += "Attacks %d times.  " % self.attacks
		if self.trample:
			desc += "Trample attack"
		if self.drain:
			desc += "Heals attacker for damage dealt"

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
					self.name = "%s Ball" % damage_type.name
				elif beam:
					self.name = "%s Beam" % damage_type.name
				else:
					self.name = "%s Bolt" % damage_type.name

		if not proj_name:
			if damage_type == Tags.Lightning:
				proj_name = 'lightning_bolt'
			if damage_type == Tags.Fire:
				proj_name = 'fire_bolt'
			if damage_type == Tags.Ice:
				proj_name = 'ice_bolt'
			if damage_type == Tags.Arcane:
				proj_name = 'arcane_bolt'
			if damage_type == Tags.Physical:
				proj_name = 'physical_bolt'

		if not self.name:
			name = "Ranged Attack"

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
			desc += "Beam attack\n"
		
		if self.melt:
			desc += "Melts through walls\n"
		elif not self.requires_los:
			desc += "Ignores walls\n"

		#if isinstance(self.damage_type, list):
		#	desc += "Randomly deals %s damage\n" % ' or '.join(t.name for t in self.damage_type)
		
		if self.cast_after_channel:
			desc += "Cast Time: %d turns\n" % self.max_channel
		elif self.max_channel:
			desc += "Can be channeled for up to %d turns\n" % self.max_channel

		if self.buff:
			desc += "Applies %s for %d turns\n" % (self.buff_name, self.buff_duration)

		if self.siege:
			desc += "Must be at full HP to fire.\nLoses half max HP on firing."

		if self.drain:
			desc += "Heals caster for damage dealt"

		if self.suicide:
			desc += "Kills the caster"

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
		self.description = "Applies %s for %d turns" % (buff().name, buff_duration)
		
	def can_threaten(self, x, y):
		if self.target_allies:
			return False
		return Spell.can_cast(self, x, y)

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

	def __init__(self, spawn_func, num_summons=1, cool_down=0, duration=0, max_channel=0, global_summon=False, path_effect=None, sort_dist=False, radius=3):
		Spell.__init__(self)
		
		self.duration = duration
		self.example_monster = spawn_func()

		self.num_summons = num_summons
		self.global_summon = global_summon
		self.cool_down = cool_down

		# How close to an enemy the ai needs to get the target
		self.ai_cast_radius = 2

		self.sort_dist = sort_dist

		self.path_effect = path_effect

		self.radius = radius
		self.spawn_func = spawn_func
		self.max_channel = max_channel

		self.calc_text()

	def calc_text(self):
		spawn_name = self.spawn_func().name

		self.name = "Summon %s" % spawn_name
		if self.num_summons > 1:
			self.name += 's'

		if self.duration:
			spawn_name = "temporary " + spawn_name

		if self.num_summons == 1:
			self.description = "Summons a %s" % spawn_name
		else:
			self.description = "Summons %d %ss" % (self.num_summons, spawn_name)

		if self.global_summon:
			self.description += " at a random location on the map"

		if self.max_channel:
			self.description += "\nCan be channeled for %d turns" % self.max_channel
		
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


		if self.max_channel and not channel_cast:
			self.caster.apply_buff(ChannelBuff(self.cast, Point(x, y)), self.max_channel)
			return

		for i in range(self.num_summons):
			unit = self.spawn_func()
			if self.duration:
				unit.turns_to_death = self.duration

			if self.global_summon:
				ex = self.spawn_func()

				targets = [t for t in self.caster.level.iter_tiles() if self.caster.level.can_stand(t.x, t.y, ex)]
				if targets:
					target = random.choice(targets)
					x = target.x
					y = target.y

			self.summon(unit, Point(x, y), sort_dist=self.sort_dist, radius=self.radius)
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
		self.name = "Pull Attack"
		self.color = color or Color(255, 255, 255)

	def get_description(self):
		return "Pulls the target %d tiles towards the caster" % self.pull_squares

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
		self.name = "Heal Ally"
		self.heal = heal
		self.range = range
		self.tag = tag

		self.description = "Heals an ally for %d" % self.heal
		if self.tag:
			self.description = "Heals one %s ally for %d" % (self.tag.name, self.heal)

		# For tooltips
		self.damage = heal
		self.damage_type = Tags.Heal

	def get_ai_target(self):
		units_in_range = self.caster.level.get_units_in_ball(Point(self.caster.x, self.caster.y), self.range)
		units_in_range = [u for u in units_in_range if not self.caster.level.are_hostile(self.caster, u)]
		units_in_range = [u for u in units_in_range if self.can_cast(u.x, u.y)]
		units_in_range = [u for u in units_in_range if u.resists[Tags.Heal] < 100]
		#units_in_range = [u for u in units_in_range if not u.is_player_controlled]

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
		self.name = "Storm Cloud"
		self.source = None
		self.asset_name = 'thunder_cloud'

	def get_description(self):
		return "Each turn, has a %d%% chance of dealing [%d_lightning:lightning] damage to any unit standing inside of it.\nExpires in %d turns." % (int(self.strikechance*100), self.damage, self.duration)

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
		self.name = "Blizzard"
		self.asset_name = 'ice_cloud'
		self.source = None
		self.spellcast = None

	def get_description(self):
		return "Each turn, deals [%d_ice:ice] damage and has a 50%% chance to freeze to any unit standing inside of it.\nExpires in %d turns." % (self.damage, self.duration)

	def on_advance(self):
		self.level.deal_damage(self.x, self.y, self.damage, Tags.Ice, self.source or self)
		if self.spellcast and random.random() < 0.25:
			if self.source:
				spell = self.source.caster.get_or_make_spell(self.spellcast)
				self.source.caster.level.act_cast(self.source.owner, spell, self.x, self.y, pay_costs=False)
			else:
				spell = self.spellcast()
				self.source.caster.level.act_cast(self.source.owner, spell, self.x, self.y, pay_costs=False)

		unit = self.level.get_unit_at(self.x, self.y)
		if unit:
			if random.random() > .5:
				unit.apply_buff(FrozenBuff(), 1)

	def on_damage(self, dtype):
		if dtype == Tags.Fire:
			self.kill()

class FireCloud(Cloud):

	def __init__(self, owner, damage=6):
		Cloud.__init__(self)
		self.owner = owner
		self.duration = 4
		self.damage = damage
		self.color = Tags.Fire.color
		self.strikechance = .5
		self.name = "Firestorm"
		self.description = "Every turn, deals %d fire damage to any creature standing within." % self.damage
		self.asset_name = 'fire_cloud'

	def on_advance(self):
		self.level.deal_damage(self.x, self.y, self.damage, Tags.Fire, self)

class CloudGeneratorBuff(Buff):

	def __init__(self, cloud_func, radius, chance):
		Buff.__init__(self)
		self.cloud_func = cloud_func
		self.radius = radius
		self.chance = chance

		self.description = "Spawns %ss up to %d tiles away" % (cloud_func(None).name, radius)

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
		self.name = "Spider Web"
		self.color = Color(210, 210, 210)
		self.description = "Any non-spider unit entering the web is stunned for 1 turn.  This destroys the web.\n\nFire damage destroys webs."
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
		self.name = "Petrified"
		self.color = Color(180, 180, 180)
		self.resists[Tags.Physical] = 75
		self.resists[Tags.Fire] = 75
		self.resists[Tags.Ice] = 100
		self.resists[Tags.Lightning] = 100
		self.asset = ['status', 'stoned']
		self.stack_type = STACK_NONE

		self.description = "Cannot move or act."


class GlassPetrifyBuff(PetrifyBuff):

	def __init__(self):
		PetrifyBuff.__init__(self)
		self.resists[Tags.Physical] = -100
		self.name = "Glassed"
		self.asset = ['status', 'glassed']
		self.color = Tags.Glass.color

	def on_applied(self, owner):
		if Tags.Glass in owner.tags:
			return ABORT_BUFF_APPLY
		return PetrifyBuff.on_applied(self, owner)

class ResistIce(Buff):

	def on_init(self):
		self.name = "Ice Protection"
		self.resists[Tags.Ice] = 50
		self.color = Tags.Ice.color
		self.asset = ['status', 'resist_ice']

class ResistFire(Buff):

	def on_init(self):
		self.name = "Fire Protection"
		self.resists[Tags.Fire] = 50
		self.color = Tags.Fire.color
		self.asset = ['status', 'resist_fire']

class ResistLightning(Buff):

	def on_init(self):
		self.name = "Lightning Protection"
		self.resists[Tags.Lightning] = 50
		self.color = Tags.Lightning.color
		self.asset = ['status', 'resist_lightning']

class ResistDark(Buff):

	def on_init(self):
		self.name = "Holy Protection"
		self.resists[Tags.Holy] = 50
		self.color = Tags.Holy.color
		self.asset = ['status', 'resist_holy']

class ResistHoly(Buff):

	def on_init(self):
		self.name = "Dark Protection"
		self.resists[Tags.Dark] = 50
		self.color = Tags.Dark.color
		self.asset = ['status', 'resist_dark']


class Stoneskin(Buff):

	def on_init(self):
		self.name = "Stoneskin"
		self.resists[Tags.Physical] = 50
		self.color = Tags.Physical.color
		self.asset = ['status', 'stoneskin']

# Raised when frozen is ended by damage
EventOnUnfrozen = namedtuple("EventOnUnfrozen", "unit dtype")
class FrozenBuff(Stun):

	def __init__(self):
		Stun.__init__(self)
		self.shatter_chance = 0
		self.name = "Frozen"
		self.color = Tags.Ice.color

		self.owner_triggers[EventOnDamaged] = self.on_damage

		self.break_dtype = None

		self.description = "Cannot move or use abilities.\n\nEnds on taking fire or physical damage."

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
		self.name = "Troll Regeneration"

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
		return "Regenerate 5 HP per turn.  Disabled on taking fire damage."

	def get_tooltip_color(self):
		return Color(0, 255, 0)

class DamageAuraBuff(Buff):

	def __init__(self, damage, damage_type, radius, custom_name=None, friendly_fire=False, melt_walls=False):
		
		self.damage = damage
		self.damage_type = damage_type
		self.radius = radius
		self.friendly_fire = friendly_fire
		self.source = None

		if custom_name:
			self.name = custom_name
		elif isinstance(self.damage_type, Tag):
			self.name = "%s Aura" % self.damage_type.name
		else:
			self.name = "Damage Aura" 

		# Not used in base class, used in inherited classes
		self.damage_dealt = 0

		self.melt_walls = melt_walls
		Buff.__init__(self)

	def on_hit(self, unit):
		# For derived to override
		pass

	def on_advance(self):

		for p in self.owner.level.get_points_in_ball(self.owner.x, self.owner.y, self.radius):

			unit = self.owner.level.get_unit_at(p.x, p.y)

			if isinstance(self.damage_type, list):
				damage_type = random.choice(self.damage_type)
			else:
				damage_type = self.damage_type

			if unit:
				if unit == self.owner:
					continue

				if not self.friendly_fire and not self.owner.level.are_hostile(self.owner, unit):
					continue


				self.damage_dealt += unit.deal_damage(self.damage, damage_type, self.source or self)
				
				self.on_hit(unit)
			else:
				if not self.owner.level.tiles[p.x][p.y].can_see:
					continue

				# Only show 50% of tiles?
				if random.random() < .5:
					continue

				self.owner.level.show_effect(p.x, p.y, damage_type, minor=True)

		
		# TODO- make wall melting work again

	def can_threaten(self, x, y):
		return distance(self.owner, Point(x, y)) <= self.radius

	def get_tooltip(self):
		damage_type_str = ' or '.join(t.name for t in self.damage_type) if isinstance(self.damage_type, list) else self.damage_type.name
		unit_type_str = 'units' if self.friendly_fire else 'enemy units'
		return "Each turn, deals %d %s damage to %s in a %d tile radius" % (self.damage, damage_type_str, unit_type_str, self.radius)

class HealAuraBuff(Buff):

	def __init__(self, heal, radius, whole_map=False, can_heal_player=True):
		Buff.__init__(self)
		self.name = "Healing Aura"
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
			return "Heals allies in a %d tile radius for %d each turn" % (self.radius, self.heal)
		else:
			return "Heals all allies for %d each turn" % self.heal

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

	def __init__(self, damage, range, damage_type=Tags.Physical, is_leap=True, charge_bonus=0, is_ghost=False, buff=None, buff_duration=0):
		Spell.__init__(self)
		self.damage = damage
		self.damage_type = damage_type
		self.range = range
		self.is_leap = is_leap and not is_ghost
		self.charge_bonus = charge_bonus
		self.is_ghost = is_ghost
		self.name = "Pounce" if self.is_leap else "Charge"
		self.requires_los = not self.is_ghost
		self.buff = buff
		self.buff_duration = buff_duration
		self.buff_name = buff().name if buff else None

	def get_leap_dest(self, x, y):
		potential_targets = []
		target_points = list(self.caster.level.get_adjacent_points(Point(x, y), check_unit=True))

		# Be willing to leap next to 3x3 or 5x5 monsters
		target_unit = self.owner.level.get_unit_at(x, y)
		if target_unit and target_unit.radius:
			for p in target_unit.iter_occupied_points():
				target_points.extend(self.caster.level.get_adjacent_points(p, check_unit=True))

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
			fmt = "Leap attack"
		elif self.is_ghost:
			fmt = "Teleport Attack"
		else:
			fmt = "Charge attack"
		if self.charge_bonus:
			fmt += ". %d extra damage per square travelled." % self.charge_bonus
		return fmt

	def can_cast(self, x, y):
		return Spell.can_cast(self, x, y) and (self.get_leap_dest(x, y) is not None)
			
	def cast(self, x, y):

		# Projectile
		leap_dest = self.get_leap_dest(x, y)
		if not leap_dest:
			return

		path = self.caster.level.get_points_in_line(Point(self.caster.x, self.caster.y), Point(leap_dest.x, leap_dest.y), find_clear=not self.is_ghost)
		for point in path:
			self.caster.level.leap_effect(point.x, point.y, self.damage_type.color, self.caster)
			yield
		
		unit = self.caster.level.get_unit_at(x, y)
		if self.buff and unit:
			unit.apply_buff(self.buff(), self.buff_duration)

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
		self.name = "Elemental Eye"

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
		self.name = "Petrify Armor"

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
		self.name = "Teleport"
		self.description = "Teleports to a random tile"
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

class MonsterLeap(Spell):

	def on_init(self):
		self.name = "Leap"
		self.description = "Instantly moves to the target tile"
		self.range = 6
		self.requires_los = True
		self.cool_down = 5

	def get_ai_target(self):
		choices = [t for t in self.caster.level.get_tiles_in_ball(self.caster.x, self.caster.y, self.get_stat('range')) if self.caster.level.can_stand(t.x, t.y, self.caster)]
		choices = [t for t in choices if distance(self.caster, t) >= 2] # Do not leap one square
		if self.requires_los:
			choices = [t for t in choices if self.caster.level.can_see(self.caster.x, self.caster.y, t.x, t.y)]

		if not choices:
			return None

		return random.choice(choices)

	def can_threaten(self, x, y):
		return False

	def cast(self, x, y):

		if not self.caster.level.can_stand(x, y, self.caster):
			return

		path = self.caster.level.get_points_in_line(Point(self.caster.x, self.caster.y), Point(x, y), find_clear=True)

		for point in path:
			self.caster.level.leap_effect(point.x, point.y, Tags.Physical.color, self.caster)
			yield

		self.caster.level.act_move(self.caster, x, y, teleport=True)



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
		self.name = "Regeneration %d" % heal
		self.description = "Regenerates %d HP per turn" % self.heal
		self.buff_type = BUFF_TYPE_BLESS
		self.asset = ['status', 'heal']

	def on_advance(self):
		if self.owner.cur_hp < self.owner.max_hp:
			self.owner.deal_damage(-self.heal, Tags.Heal, self)


class ShieldRegenBuff(Buff):

	def __init__(self, shield_max, shield_freq=1):
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
		return "Gains 1 shield every %d turns up to a max of %d" % (self.shield_freq, self.shield_max)

class ReincarnationBuff(Buff):

	def __init__(self, lives=1):
		Buff.__init__(self)
		self.lives = lives
		self.owner_triggers[EventOnDeath] = self.on_death
		self.name = "Reincarnation %d" % self.lives
		self.buff_type = BUFF_TYPE_PASSIVE
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
		return "Reincarnates when killed (%d times)" % self.lives

	def on_death(self, evt):
		if self.lives >= 1:

			to_remove = [b for b in self.owner.buffs if b.buff_type != BUFF_TYPE_PASSIVE]
			for b in to_remove:
				self.owner.remove_buff(b)

			self.lives -= 1
			self.old_pos = Point(self.owner.x, self.owner.y)
			self.owner.level.queue_spell(self.respawn())
			self.name = "Reincarnation %d" % self.lives

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

			self.owner.level.leap_effect(self.old_pos.x, self.old_pos.y, Tags.Holy.color, self.owner)
			
			yield
			for p in self.owner.level.get_points_in_line(self.old_pos, dest)[1:-1]:
				self.owner.level.show_effect(p.x, p.y, Tags.Holy, minor=True)
			yield

			self.owner.level.leap_effect(dest.x, dest.y, Tags.Holy.color, self.owner)

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
		self.name = "Shield Allies"
		self.description = "Grant all allies in line of sight 1 shield, to a max of %d" % self.shields
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
		self.name = "Poison"
		self.buff_type = BUFF_TYPE_CURSE
		self.asset = ['status', 'poison']
		self.description = "Takes 1 poison damage each turn.  Cannot heal."
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

class Soulbound(Buff):

	def __init__(self, guardian):
		Buff.__init__(self)
		self.owner_triggers[EventOnDamaged] = self.on_self_damage
		self.global_triggers[EventOnDeath] = self.on_death
		self.guardian = guardian
		self.name = "Soul Jarred"
		self.asset = ['status', 'soulbound']
		self.color = Tags.Dark.color

	def get_buff_tooltip(self):
		return "Cannot die until it's jar %s is killed"

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


class BloodrageBuff(Buff):
	
	def __init__(self, bonus):
		self.bonus = bonus
		Buff.__init__(self)

	def on_init(self):
		self.name = 'Bloodrage'
		self.color = Tags.Demon.color
		self.asset = ['status', 'bloodlust']
		self.global_bonuses['damage'] = self.bonus
		self.stack_type	= STACK_INTENSITY	
		self.description = "Damage increased by %d" % self.bonus

def bloodrage(amount):
	def onhit(caster, target):
		caster.apply_buff(BloodrageBuff(amount), 10)
	return onhit

class ClarityBuff(Buff):

	def on_init(self):
		self.description = "Cannot be stunned"

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
		self.name = "Thorns"
		self.description = "Deals %d %s damage to melee attackers" % (self.damage, self.dtype.name)
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

class RetaliationBuff(Buff):

	def __init__(self, damage, dtype):
		self.damage = damage
		self.dtype = dtype
		Buff.__init__(self)
		self.name = "%s Retaliation" % dtype.name
		self.description = "Deals %d %s damage to any unit that harms it" % (self.damage, self.dtype.name)

	def on_init(self):
		self.owner_triggers[EventOnDamaged] = self.on_damage

	def on_damage(self, evt):
		if not evt.source:
			return

		if not evt.source.owner:
			return

		if evt.source.owner == self.owner:
			return

		# Infinite loop prevention perhaps
		if not self.owner.is_alive():
			return

		if isinstance(evt.source, RetaliationBuff):
			return

		self.owner.level.queue_spell(self.do_damage(evt.source.owner))

	def do_damage(self, unit):
		if not unit.is_alive():
			return

		# Show path
		self.owner.level.show_path_effect(self.owner, unit, self.dtype, minor=True)

		unit.deal_damage(self.damage, self.dtype, self)
		yield




class ChanceToBecome(Buff):

	def __init__(self, spawner, chance, name=None):
		self.spawner = spawner
		self.chance = chance
		self.spawn_name = name
		Buff.__init__(self)

	def on_init(self):
		name = self.spawn_name if self.spawn_name else self.spawner().name
		self.description = "Each turn has a %d%% chance to become a %s" % (self.chance*100, name)

	def on_advance(self):
		if random.random() > self.chance:
			return

		self.owner.kill(trigger_death_event=False)
		new_unit = self.spawner()
		new_unit.team = self.owner.team
		new_unit.source = self.owner.source
		p = self.owner.level.get_summon_point(self.owner.x, self.owner.y, radius_limit=8, flying=new_unit.flying)
		if p:
			self.owner.level.add_obj(new_unit, p.x, p.y)

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
		return "Will become a %s in %d turns" % (self.spawn_name, self.mature_duration)

class SpawnOnDeath(Buff):

	def __init__(self, spawner, num_spawns):
		Buff.__init__(self)
		self.spawner = spawner
		self.num_spawns = num_spawns
		self.description = "On death, spawn %d %ss" % (self.num_spawns, self.spawner().name)
		self.owner_triggers[EventOnDeath] = self.on_death
		self.apply_bonuses = True

	def on_death(self, evt):
		self.owner.level.queue_spell(self.spawn())

	def spawn(self):
		for i in range(self.num_spawns):
			unit = self.spawner()
			# Inherit source- this propogates minion bonuses from shrines and skills
			if self.owner.source and self.apply_bonuses:
				unit.source = self.owner.source
				apply_minion_bonuses(self.owner.source, unit)
			self.summon(unit)
			yield

class RespawnAs(Buff):

	def __init__(self, spawner, name=None):
		Buff.__init__(self)
		self.spawner = spawner
		self.spawn_name = name
		if not self.spawn_name:
			self.spawn_name = self.spawner().name
			
		self.name = "Respawn As %s" % self.spawn_name

	def on_init(self):
		self.owner_triggers[EventOnDamaged] = self.on_damage

	def on_damage(self, evt):
		if self.owner.cur_hp <= 0:
			# Supress death events- this creature isn't really dying, its respawning
			self.owner.kill(trigger_death_event=False)

			self.owner.level.queue_spell(self.respawn())

	def respawn(self):
		new_unit = self.spawner()


		new_unit.team = self.owner.team
		new_unit.source = self.owner.source
		new_unit.parent = self.owner
		
		if self.owner.source:
			new_unit.source = self.owner.source
			apply_minion_bonuses(self.owner.source, new_unit)

		p = self.owner.level.get_summon_point(self.owner.x, self.owner.y, radius_limit=8, flying=new_unit.flying)
		if p:
			self.owner.level.add_obj(new_unit, p.x, p.y)
			
			# If the spawner is not a new monster, but an old monster that was removed from the map or something, it might need to be refreshed
			new_unit.refresh()

		yield
		

	def get_tooltip(self):
		if not self.spawn_name:
			self.spawn_name = self.spawner().name
		return "On reaching 0 hp, transforms into a %s" % self.spawn_name

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
		self.owner.level.queue_spell(self.split())

	def split(self):
		for i in range(self.children):
			unit = self.spawner()
			if unit.max_hp == 0:
				return

			self.summon(unit)
			yield
			
	def get_tooltip(self):
		return "On death, splits into %d smaller versions of itself" % self.children

class SimpleBurst(Spell):

	def __init__(self, damage, radius, damage_type=Tags.Physical, cool_down=0, ignore_walls=False, onhit=None, extra_desc=None):
		Spell.__init__(self)
		self.damage = damage
		self.damage_type = damage_type
		self.name = "%s Burst" % self.damage_type.name
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
		desc = "Deals damage in a burst around the caster."
		if self.ignore_walls:
			desc += "\nThe burst ignores walls."
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

	if Tags.Living not in unit.tags:
		return

	skeleton = Unit()
	skeleton.name = "Skeletal %s" % unit.name
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
		self.description = "On death, deals %d %s damage to all tiles in a radius of %d" % (damage, damage_type.name, radius)
		self.damage = damage
		self.damage_type = damage_type
		self.radius = radius
		self.name = "Death Explosion"

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
		self.name = "Call Kingdom"
		self.range = 0
		self.cool_down = 10
		self.max_charges = 0

	def get_description(self):
		return "Summon 2 %s gates" % self.spawner().name

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
		return "Spawns a %s every %d to %d turns.\n\nNext spawn: %d turns" % (self.example_monster.name, self.min_turns, self.max_turns, self.turns)

def MonsterSpawner(spawn_func):
	unit = Unit()
	example_monster = spawn_func()
	unit.sprite = example_monster.sprite
	unit.sprite.color = Color(0, 0, 0)

	unit.name = "%s Spawner" % example_monster.name
	unit.max_hp = 40

	unit.sprite.bg_color = Color(255, 255, 255)
	summon = SimpleSummon(spawn_func, cool_down=random.randint(7, 10), sort_dist=True)
	summon.cool_down
	unit.spells.append(summon)
	unit.cool_downs[summon] = random.randint(5, 10)
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
		self.name = "Nightmare Aura"
		self.cool_down = 16
		self.duration = 8
		self.radius = 7
		self.range = 0
		dtype_str = self.damage_type.name if isinstance(self.damage_type, str) else ' or '.join([t.name for t in self.damage_type])
		self.description = "Deals 2 %s damage to all enemies in the radius each turn" % dtype_str

	def get_ai_target(self):
		for u in self.caster.level.get_units_in_ball(self.caster, radius=self.radius):
			if are_hostile(u, self.caster):
				return self.caster
		return None


	def cast_instant(self, x, y):
		buff = DamageAuraBuff(damage=2, damage_type=self.damage_type, radius=self.get_stat('radius'))
		buff.name = buff.name or "Nightmare Aura"
		self.caster.apply_buff(buff, self.get_stat('duration'))

class WizardSelfBuff(Spell):

	def __init__(self, buff, duration, cool_down=0):
		self.buff = buff
		self.duration = duration
		Spell.__init__(self)
		self.cool_down = cool_down
		self.description = "Applies %s for %d turns." % (self.buff().name, duration)
		
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
		self.description = "Heals allies within a [%d_tile:radius] radius for [%d_HP:heal] each turn for [%d_turns:duration]." % (self.radius, self.heal, self.duration)
		

	def get_ai_target(self):
		for u in self.caster.level.get_units_in_ball(self.caster, radius=self.radius):
			if not are_hostile(u, self.caster) and u.cur_hp < u.max_hp:
				return self.caster
		return None

	def on_init(self):
		self.name = "Heal Aura"
		self.range = 0

	def cast_instant(self, x, y):
		self.caster.apply_buff(HealAuraBuff(heal=self.get_stat('heal'), radius=self.get_stat('radius')), self.get_stat('duration'))

class WizardBloodlust(Spell):

	def on_init(self):
		self.name = "Bloodlust"
		self.bonus = 3
		self.radius = 5
		self.range = 0
		self.duration = 5
		self.cool_down = 10
		self.damage_type = Tags.Fire

	def get_description(self):
		return "Increases damage by %d for all allied units within %d tiles for %d turns" % (self.bonus, self.radius, self.duration)

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
		self.name = "Sorcery Mirror"
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
		return "Whenever a sorcery spell is cast targeting this unit, this unit casts a copy of that spell targeting the original caster"

class ShieldAllySpell(Spell):

	def __init__(self, shields=1, range=5, cool_down=0):
		self.shields = shields
		Spell.__init__(self)
		self.range = range
		self.cool_down = cool_down

	def on_init(self):
		self.name = "Shield Ally"
		self.description = "Grant an ally %d shields, to a maximum of %d" % (self.shields, self.shields)
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
		self.name = "Blizzard"
		self.description = "Creates blizzard clouds in an area of radius 3"
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
		self.name = "Quakeport"
		self.description = "Teleports to the target and creates a local earthquake"
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
		self.name = "Fire Protection"
		self.duration = 8
		self.description = "Grants caster and allies 50%% resistance to Fire and Ice for %d turns" % self.duration
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
		self.name = "Passive Teleportation"

	def on_advance(self):
		if random.random() > self.chance:
			return

		if self.owner.is_stunned():
			return

		# Dont interupt channels, its dumb
		if self.owner.has_buff(ChannelBuff):
			return

		old = Point(self.owner.x, self.owner.y)
		randomly_teleport(self.owner, self.radius, requires_los=self.hop)

		for p in self.owner.level.get_points_in_line(old, self.owner)[:-1]:
			self.owner.level.show_effect(p.x, p.y, Tags.Translocation, minor=True)

	def get_tooltip(self):
		moveword = "hop" if self.hop else "blink"
		return "Each turn, %d%% chance to %s to a random tile up to %d tiles away" % (int(self.chance * 100), moveword, self.radius)

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
		self.name = "Acidified"
		self.resists[Tags.Poison] = -100
		self.buff_type = BUFF_TYPE_CURSE
		self.asset = ['status', 'amplified_poison']
		self.color = Tags.Poison.color

class Electrified(Buff):

	def on_init(self):
		self.name = "Electrified"
		self.resists[Tags.Lightning] = -10
		self.buff_type = BUFF_TYPE_CURSE
		self.stack_type	= STACK_INTENSITY
		self.asset = ['status', 'amplified_lightning']
		self.color = Tags.Lightning.color

def drain_spell_charges(caster, target):
	possible_spells = [s for s in target.spells if s.cur_charges > 0]
	if possible_spells:
		spell = random.choice(possible_spells)
		spell.cur_charges = spell.cur_charges - 1
	

def grant_minion_spell(spell_class, unit, master, cool_down=1, pre_insert=True):
	spell = spell_class()
	spell.statholder = master
	spell.caster = unit
	spell.owner = unit

	# Erase charges and add cooldown 
	spell.max_charges = 0
	spell.cur_charges = 0
	spell.cool_down = cool_down

	if pre_insert:
		unit.spells.insert(0, spell)

	# Return spell so further modifications can be made (range twiddling ect)
	return spell


class AdaptiveArmorResistBuff(Buff):

	def __init__(self, tag, resist):
		Buff.__init__(self)
		self.buff_type = BUFF_TYPE_BLESS
		self.stack_type = STACK_INTENSITY
		self.name = "%s Armor" % tag.name
		self.color = tag.color
		self.resists[tag] = resist


class AdaptiveArmorBuff(Buff):

	def __init__(self, resist):
		self.res_amt = resist
		Buff.__init__(self)

	def on_init(self):
		self.name = "Adaptive Armor"
		self.description = "On taking damage, gains %d%% resistance to that damage type for 1 turn." % self.res_amt
		self.owner_triggers[EventOnDamaged] = self.on_damage

	def on_damage(self, evt):
		
		# do not resist heals or whatever
		if evt.damage <= 0:
			return

		self.owner.apply_buff(AdaptiveArmorResistBuff(evt.damage_type, self.res_amt), 1)