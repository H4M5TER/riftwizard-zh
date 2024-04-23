from collections import defaultdict, namedtuple, OrderedDict
import math
import logging
import random
import bisect
import tcod as libtcod
import time
import os

logger = None

Point = namedtuple("Point", "x y")

import heapq

TEAM_PLAYER = 0
TEAM_ENEMY = 1
TEAM_PREY = 2

LAST_LEVEL = 21

RANGE_GLOBAL = 50

# Special value for on_apply
ABORT_BUFF_APPLY = 99

# Max advance time = 20 milliseconds
MAX_ADVANCE_TIME = .02

ITEM_SLOT_STAFF = 0
ITEM_SLOT_ROBE = 1
ITEM_SLOT_HEAD = 2
ITEM_SLOT_GLOVES = 3
ITEM_SLOT_BOOTS = 4
ITEM_SLOT_AMULET = 5

TILE_TYPE_FLOOR = 0
TILE_TYPE_WALL = 1
TILE_TYPE_CHASM = 2

visual_mode = False
def set_visual_mode(val):
	global visual_mode
	visual_mode = val

class PriorityQueue:
	def __init__(self):
		self.elements = []
	
	def empty(self):
		return len(self.elements) == 0
	
	def put(self, item, priority):
		heapq.heappush(self.elements, (priority, item))
	
	def get(self):
		return heapq.heappop(self.elements)[1]

def distance(p1, p2, diag=False, euclidean=True):
	if diag:
		return max(abs(p1.x - p2.x), abs(p1.y - p2.y))
	if euclidean:
		return math.sqrt(math.pow((p1.x - p2.x), 2) + math.pow((p1.y - p2.y), 2))
	
	return abs(p1.x - p2.x) + abs(p1.y - p2.y)


def are_hostile(unit1, unit2):
	if unit1 == unit2:
		return False

	if unit1.team != unit2.team:
		return True

	# Player cannot be berserked- and we can save a trip through the buff list by short circuiting out on the player
	# (The player is a very common arg for unit1 or unit2)
	if (not unit1.is_player_controlled and unit1.has_buff(BerserkBuff)) or (not unit2.is_player_controlled and unit2.has_buff(BerserkBuff)):
		return True

	return False

def format_attr(attr):

	if is_stat_pct(attr):
		attr = "% " + attr

	attr = ' '.join(w.capitalize() for w in attr.replace('_', ' ').split())

	return attr


attr_explanations = {
	'minion_damage': 'damage dealt by primary attack skills'


}
def explain_attr(attr):

	if attr in attr_explanations:
		return attr_explanations[attr]
	else:
		return format_attr(attr)

def dot_product(x1, y1, x2, y2):
	return x1 * x2 + y1 * y2

# Returns the minimum angle between the lines AB and AC
def get_min_angle(A_x, A_y, B_x, B_y, C_x, C_y):
	AB_x = B_x - A_x
	AB_y = B_y - A_y
	AC_x = C_x - A_x
	AC_y = C_y - A_y

	len_AB = math.sqrt(dot_product(AB_x, AB_y, AB_x, AB_y))
	len_AC = math.sqrt(dot_product(AC_x, AC_y, AC_x, AC_y))

	# return 0 if 2 of the points are the same
	if len_AB == 0 or len_AC == 0:
		return 0

	cos_theta = dot_product(AB_x, AB_y, AC_x, AC_y) / (len_AB * len_AC)
	cos_theta = min(1.0, cos_theta)
	cos_theta = max(-1.0, cos_theta)
	
	theta = math.acos(cos_theta)
	return theta;

# Return the point adjacent to point 1 closest to point 2 
def get_cast_point(x1, y1, x2, y2):
	adjacents = []
	for xmod in [-1, 0, 1]:
		for ymod in [-1, 0, 1]:
			if xmod == ymod == 0:
				continue
			adjacents.append(Point(x1 + xmod, y1 + ymod))
	return min(adjacents, key=lambda p: distance(p, Point(x2, y2)))

EventOnSpellCast = namedtuple("EventOnSpellCast", "spell caster x y")
EventOnDeath = namedtuple("EventOnDeath", "unit damage_event")
EventOnPropEnter = namedtuple("EventOnPropEnter", "unit prop")
EventOnPreDamaged = namedtuple("EventOnPreDamaged", "unit damage damage_type source")
EventOnDamaged = namedtuple("EventOnDamaged", "unit damage damage_type source")
EventOnHealed = namedtuple("EventOnHealed", "unit heal source")
EventOnItemPickup = namedtuple("EventOnItemPickup", "item")
EventOnBuffApply = namedtuple("EventOnBuffApply", "buff unit")
EventOnBuffRemove = namedtuple("EventOnBuffRemove", "buff unit")
EventOnMoved = namedtuple("EventOnMoved", "unit x y teleport")
EventOnUnitAdded = namedtuple("EventOnUnitAdded", "unit")
EventOnUnitPreAdded = namedtuple("EventOnUnitPreAdded", "unit")
EventOnPass = namedtuple("EventOnPass", "unit")
EventOnSpendHP = namedtuple("EventOnSpendHP", "unit hp")

class EventHandler():
	# A system for dynamically registering and unregistering from global or entity scoped events
	# This is meant for flexible content like spells and buffs
	# Global game rules should not use dynamic subscriptions, they should be static in code.
	# We only need this because iterating over every buff on every character every time anything happened would be impractical

	def __init__(self):
		self._queue = []
		self._handlers = defaultdict(lambda : defaultdict(list))

	def register_global_trigger(self, event_type, handler):
		assert(isinstance(event_type, type))
		self._handlers[event_type][None].append(handler)

	def unregister_global_trigger(self, event_type, handler):
		assert(isinstance(event_type, type))
		self._handlers[event_type][None].remove(handler)

	def register_entity_trigger(self, event_type, entity, handler):
		assert(isinstance(event_type, type))
		self._handlers[event_type][entity].append(handler)

	def unregister_entity_trigger(self, event_type, entity, handler):
		assert(isinstance(event_type, type))
		self._handlers[event_type][entity].remove(handler)

	def raise_event(self, event, entity=None):
		# Record state of list once to ignore changes to the list caused by subscriptions
		if entity:
			for handler in list(self._handlers[type(event)][entity]):
				handler(event)

		global_handlers = list(self._handlers[type(event)][None])
		for handler in global_handlers:
			handler(event)


class Bolt():
	# A sequencing tool for projectiles and projectile like phenomena
	def __init__(self, level, start, end, two_pass=True, find_clear=True):
		self.start = start
		self.end = end
		self.level = level
		self.two_pass = two_pass
		self.find_clear = find_clear

	def __iter__(self):
		path = self.level.get_points_in_line(self.start, self.end, two_pass=self.two_pass, find_clear=self.find_clear)

		# Skip first point
		path = path[1:]

		for point in path:
			yield point

BurstConeParams = namedtuple("BurstConeParams", "target angle")
class Burst():
	# A sequencing tool for explosions and explosion like phenomena
	def __init__(self, level, origin, radius, burst_cone_params=None, expand_diagonals=False, ignore_walls=False):
		self.level = level
		self.origin = origin
		self.radius = radius
		self.burst_cone_params = burst_cone_params

		# Auto expand diagonals in cones, they dont work otherwise.
		self.expand_diagonals = expand_diagonals if not burst_cone_params else True
		self.ignore_walls = ignore_walls


	def is_in_burst(self, p):

		dist = distance(p, self.origin)
		if dist > self.radius:
			return False



		if isinstance(self.origin, Unit):
			# Take minimum of angle with each of the occupied points of the origin monster
			angle = min(get_min_angle(o.x, 
									  o.y, 
									  self.burst_cone_params.target.x, 
									  self.burst_cone_params.target.y, 
									  p.x, 
									  p.y) for o in self.origin.iter_occupied_points())

		else:
			angle = abs(get_min_angle(self.origin.x, 
								  self.origin.y, 
								  self.burst_cone_params.target.x, 
								  self.burst_cone_params.target.y, 
								  p.x, 
								  p.y)) 

		return angle <= self.burst_cone_params.angle

	def __iter__(self):

		# Start with the origin point, or, with all the points of the origin unit
		last_stage = set([self.origin])

		if isinstance(self.origin, Unit):
			last_stage = [u for u in self.origin.iter_occupied_points()]

		already_exploded = set(last_stage)

		if not self.burst_cone_params:
			yield last_stage

		for i in range(self.radius):
			next_stage = set()

			for point in last_stage:
				ball_radius = 1.5 if self.expand_diagonals else 1.1
				next_stage.update(self.level.get_points_in_ball(point.x, point.y, ball_radius, diag=self.expand_diagonals))

			# Remove already explored points from the next stage
			next_stage.difference_update(already_exploded)

			# Remove walls in non wall ignoring bursts
			if not self.ignore_walls:
				next_stage = [p for p in next_stage if self.level.tiles[p.x][p.y].can_see]

			if self.burst_cone_params is not None:
				next_stage = [p for p in next_stage if self.is_in_burst(p)]

			already_exploded.update(next_stage)
			yield next_stage
			last_stage = next_stage

def tween(start, end, t):
	return (1 - t) * start + t * end

class Color:
	def __init__(self, r=255, g=255, b=255):
		self.r = int(r)
		self.g = int(g)
		self.b = int(b)

	def __hash__(self):
		return hash((self.r, self.b, self.g))

	def __eq__(self, other):
		return self.r == other.r and self.g == other.g and self.b == other.b

	def __str__(self):
		return "<Color %d %d %d>" % (self.r, self.g, self.b)

	def to_tup(self):
		return (self.r, self.g, self.b)

def random_color(min=0, max=255):
	return Color(random.randint(min, max), random.randint(min, max), random.randint(min, max))

def tween_color(start, end, t):
	return Color(
			tween(start.r, end.r, t),
			tween(start.g, end.g, t),
			tween(start.b, end.b, t)
		)
COLOR_BLACK = Color(0, 0, 0)
COLOR_ARTIFACT = Color(252, 186, 3)
COLOR_CONSUMABLE = Color(31, 255, 75)
COLOR_MANA = Color(125, 125, 255)
COLOR_OMEGA = Color(255, 217, 102)

COLOR_DAMAGE = Color(215, 0, 0)
COLOR_CHARGES = Color(255, 128, 0)
COLOR_RANGE = Color(180, 100, 255)

COLOR_SHIELD = Color(77, 253, 252)

class Sprite:
	def __init__(self, char, color=Color()):
		self.char = char
		self.color = color
		self.bg_color = None
		self.face_left = False


class Effect(object):
	def __init__(self, x, y, start_color, end_color, frames):
		self.x = x
		self.y = y
		self.start_color = start_color
		self.end_color = end_color
		self.color = start_color
		self.frames = frames
		self.frames_left = frames
		self.minor = False
		self.speed = 1

	def advance(self):
		t = (self.frames - self.frames_left) / float(self.frames)
		self.color = tween_color(self.start_color, self.end_color, t)
		self.frames_left = self.frames_left - 1

	def __reduce__(self):
		assert(False)


class Cloud():
	def __init__(self):
		self.is_player_controlled = False
		self.is_alive = True
		self.asset_name = None
		pass

	def advance(self):
		self.duration -= 1
		self.on_advance()
		if self.duration <= 0 and self.is_alive:
			self.kill()
		return True

	def kill(self):
		assert(self.is_alive)
		self.on_expire()
		self.level.remove_obj(self)
		self.is_alive = False

	def can_be_replaced_by(self, new_cloud):
		return True

	def on_advance(self):
		pass

	def on_expire(self):
		pass

	def on_unit_enter(self, unit):
		pass

	def on_damage(self, dtype):
		pass

def is_stat_pct(stat):
	return False

	#return stat in [
	#	'damage', 
	#	'minion_damage', 
	#	'minion_health', 
	#	'heal', 
	#	'duration', 
	#	'minion_duration'
	#]

stat_names = [
			'range',
			'max_charges',
			'damage', 
			'radius',
			'duration',
			'minion_duration',
			'minion_damage',
			'breath_damage',
			'minion_health',
			'minion_range',
			'heal',
			'num_targets',
			'cascade_range',
			'shields',
			'max_channel',
			'num_summons',
		]

class Spell(object):

	def __init__(self):
		# By default any of these attributes can be modified by shrines buffs ect.
		# Spells can delete or add values from this list in on_init.
		self.stats = list(stat_names)

		self.spell_upgrades = []

		self.name = "Unnamed spell"
		self.mana_cost = 0
		self.cool_down = 0
		self.hp_cost = 0
		self.requires_los = True
		self.tags = []
		self.added_by_buff = False
		self.item = None

		self.asset = None

		self.prereqs = []
		self.level = 0
		self.description = ""
		self.caster = None
		self.owner = None
		self.statholder = None

		self.melee = False

		self.show_tt = True
		self.quick_cast = False

		self.cast_on_walls = False

		self.range = 5
		self.max_charges = 0
		self.can_target_self = False
		self.can_target_empty = True
		self.must_target_walkable = False
		self.must_target_empty = False

		# AI targest allies instead of enemies if true
		self.target_allies = False

		# AI targets random valid empty targets
		self.target_empty = False

		self.diag_range = False

		self.animate = True

		# attr, amount, max stacks, rarity
		self.upgrades = OrderedDict()
		self.on_init() # This must happen last or else defaults will be overwritten

		if self.range == 0:
			self.can_target_self = True

		# Record what stats actually exist on this spell
		self.stats = [s for s in self.stats if hasattr(self, s)]

		self.self_target = (self.range == 0)

		for attr, val in reversed(self.upgrades.items()):
			name = None
			desc = None
			exc_class = None
			if attr not in self.stats:
				self.stats.append(attr)
			
			# Create the upgrade
			if isinstance(val, tuple):
				amt = val[0]
				level = val[1]

				if len(val) > 2:
					name = val[2]
				if len(val) > 3:
					desc = val[3]
				if len(val) > 4:
					exc_class = val[4]
			else:
				amt = val
				level = 1
			self.spell_upgrades.insert(0, SpellUpgrade(spell=self, attribute=attr, amount=amt, level=level, name=name, desc=desc, exc_class=exc_class))

		self.cur_charges = self.get_stat('max_charges')

	# For very complex upgrades
	def add_upgrade(self, upgrade):
		assert(isinstance(upgrade, Upgrade))
		upgrade.prereq = self
		upgrade.tags = list(self.tags)
		self.spell_upgrades.append(upgrade)

	def modify_test_level(self, level):
		pass

	# Override with objects that will appear in the tooltip when the mouse wheel is scrolled (Summons, buffs)
	def get_extra_examine_tooltips(self):
		return self.spell_upgrades

	def fmt_dict(self):
		return {s: self.get_stat(s) for s in self.stats}

	def iter_stats(self):
		for stat in self.stats:
			yield (stat, getattr(self, stat, 0), self.get_stat(stat))


	def get_color(self):
		return self.tags[0].color if self.tags else Color(255, 255, 255)

	def get_stat(self, attr, base=None):
		statholder = self.statholder or self.caster
		
		if base is None:
			base = getattr(self, attr, 0)

		if not statholder or not statholder.buffs:
			return base

		return statholder.get_stat(base, self, attr)

	def on_init(self):
		pass

	# Returns a list of tiles that can be targeted
	def get_targetable_tiles(self):

		if self.get_stat('range') == RANGE_GLOBAL:
			return [Point(t.x, t.y) for t in self.caster.level.iter_tiles() if self.can_cast(t.x, t.y)]

		candidates = self.caster.level.get_points_in_ball(self.caster.x, self.caster.y, self.get_stat('range'))
		if self.melee:
			candidates = self.caster.level.get_points_in_ball(self.caster.x, self.caster.y, 1.5, diag=True)

		return [p for p in candidates if self.can_cast(p.x, p.y)]

	# Returns a list of points that will be impacted if the spell is cast here
	def get_impacted_tiles(self, x, y):
		
		# If there is a radius, default to using it
		if hasattr(self, 'radius'):
			radius = self.get_stat('radius')
		else:
			radius = 0

		if radius:
			return self.caster.level.get_points_in_ball(x, y, radius)

		else:
			return [Point(x, y)]

	def cast(self, x, y):
		yield self.cast_instant(x, y)

	# Can override this instead of cast if you want to not put yield at the end
	def cast_instant(self, x, y):
		# Assert on unimplemented spells
		assert(False)

	# Return true if we shuold shade the tile red when alt is held
	def can_threaten(self, x, y):
		# By default can cast on xy <=> can threaten, but for some fancy aoes it might not be the same
		return self.can_cast(x, y)

	def can_threaten_corner(self, x, y, radius):
		# Immediately disqualify points out of range
		if distance(Point(x, y), self.caster) > radius + self.range:
			return False

		# Immediately qualify targetable points
		if self.can_cast(x, y):
			return True

		nearby_points = self.caster.level.get_points_in_ball(x, y, radius)

		for p in nearby_points:
			# Todo- should also check path length
			if self.can_cast(p.x, p.y) and Point(x, y) in self.get_impacted_tiles(p.x, p.y):
				return True

		return False

	
	# By default, target a random targetable enemy unit
	def get_ai_target(self):
		if self.self_target:
			return self.caster if self.can_cast(self.caster.x, self.caster.y) else None

		if self.target_empty:
			candidates = [p for p in self.owner.level.get_points_in_ball(self.caster.x, self.caster.y, self.get_stat('range')) if self.can_cast(p.x, p.y)]
			if candidates:
				return random.choice(candidates)
			else:
				return None

		def is_good_target(p):
			u = self.owner.level.get_unit_at(p.x, p.y)
			if not u:
				return False
			if bool(self.target_allies) == bool(self.caster.level.are_hostile(u, self.caster)):
				return False
			if hasattr(self, 'damage_type'):
				if isinstance(self.damage_type, list):
					if all(u.resists[dtype] >= 100 for dtype in self.damage_type):
						return False
				else:
					if u.resists[self.damage_type] >= 100:
						return False
			if not self.can_cast(p.x, p.y):
				return False
			return True

		targets = []
		for u in self.caster.level.units:
			for p in u.iter_occupied_points():
				if is_good_target(p):
					targets.append(p)

		if not targets:
			return None
		else:
			target = random.choice(targets)
			return Point(target.x, target.y)

	def get_corner_target(self, radius, requires_los=True):
		# Find targets possibly around corners
		# Returns the first randomly found target which will hit atleast one enemy with a splash of the given radius

		dtypes = []
		if hasattr(self, 'damage_type'):
			if isinstance(self.damage_type, Tag):
				dtypes = [self.damage_type]
			else:
				dtypes = self.damage_type
		
		def is_target(v):
			if not are_hostile(self.caster, v):
				return False
			# if no damage type is specified, take any hostile target
			if not dtypes:
				return True
			for dtype in dtypes:
				if v.resists[dtype] < 100:
					return True

		nearby_enemies = self.caster.level.get_units_in_ball(self.caster, self.range + radius)
		nearby_enemies = [u for u in nearby_enemies if is_target(u)]

		possible_cast_points = list(self.caster.level.get_points_in_ball(self.caster.x, self.caster.y, self.range))

		# Filter points that are not close to any enemies
		potentials = []
		for p in possible_cast_points:
			for e in nearby_enemies:
				if distance(p, e, diag=False, euclidean=False) < radius:
					potentials.append(p)
					break

		possible_cast_points = potentials

		# Filter points that the spell cannot target
		potentials = []
		for p in possible_cast_points:
			if self.can_cast(p.x, p.y):
				potentials.append(p)

		possible_cast_points = potentials
		random.shuffle(possible_cast_points)

		def can_hit(p, u):
			return distance(p, u, diag=False, euclidean=False) <= radius and (not self.requires_los or self.caster.level.can_see(p.x, p.y, u.x, u.y))

		for p in possible_cast_points:
			if not any(is_target(u) and can_hit(p, u) for u in self.owner.level.get_units_in_ball(p, radius)):
				continue
			return p
		return None

	def can_pay_costs(self):
		
		if self.caster.is_stunned():
			return False

		# Can always cast items
		if self.item:
			return True

		if self.caster.cool_downs.get(self, 0) > 0:
			return False

		if self.max_charges:
			if self.cur_charges <= 0:
				return False

		if self.hp_cost:
			if self.get_stat('hp_cost') >= self.caster.cur_hp:
				return False

		return True

	def can_copy(self, x, y):
		old_req_los = self.requires_los
		old_range = self.range

		self.requires_los = False
		self.range = RANGE_GLOBAL

		retval = self.can_cast(x, y)

		self.range = old_range
		self.requires_los = old_req_los

		return retval

	def can_cast(self, x, y):

		if (not self.can_target_self) and (self.caster.x == x and self.caster.y == y):
			return False

		if (not self.can_target_empty) and (not self.caster.level.get_unit_at(x, y)):
			return False

		if self.must_target_walkable and not self.caster.level.can_walk(x, y):
			return False

		if self.must_target_empty and self.caster.level.get_unit_at(x, y):
			return False

		if self.caster.is_blind() and distance(Point(x, y), self.caster, diag=True) > 1:
			return False

		if not distance(Point(x, y), Point(self.caster.x, self.caster.y), diag=self.melee or self.diag_range) <= self.get_stat('range') + self.owner.radius:
			return False

		if self.get_stat('requires_los'):
			if not self.caster.level.can_see(self.caster.x, self.caster.y, x, y, light_walls=self.cast_on_walls):
				return False

		return True

	def pay_costs(self):

		if self.item:
			self.caster.remove_item(self.item)
			return

		self.caster.mana = self.caster.mana - self.get_mana_cost()
		if self.cool_down > 0:
			self.caster.cool_downs[self] = self.cool_down

		if self.max_charges:
			self.cur_charges -= 1

		if self.hp_cost:
			self.caster.cur_hp -= self.get_stat('hp_cost')
			self.caster.level.combat_log.debug("%s pays %d HP to cast %s" % (self.caster.name, self.hp_cost, self.name))
			self.caster.level.event_manager.raise_event(EventOnSpendHP(self.caster, self.get_stat('hp_cost')), self.caster)
			self.caster.level.show_effect(self.caster.x, self.caster.y, Tags.Blood, minor = self.get_stat('hp_cost') < 11)

	def get_description(self):
		return self.description

	def get_mana_cost(self):
		# allow negative mana costs for buff book keeping, 
		#  but never actually pay or print negative numbers
		return max(0, self.mana_cost)

	def summon(self, unit, target=None, radius=4, team=None, sort_dist=True):
		if not unit.source:
			unit.source = self
		if not target:
			target = Point(self.caster.x, self.caster.y)
		return self.caster.level.summon(self.caster, unit, target, radius, team, sort_dist)

	def refund_charges(self, charges):
		self.cur_charges += charges
		self.cur_charges = min(self.cur_charges, self.get_stat('max_charges'))


MoveAction = namedtuple("MoveAction", "x y")
CastAction = namedtuple("CastAction", "spell x y")
PassAction = namedtuple("PassAction", "")
StunnedAction = namedtuple("StunnedAction", "buff duration")

class Item(object):

	def __init__(self):
		self.sprite = Sprite("!", Color(255, 255, 255))
		self.buff = None
		self.name = "Unnamed Item"
		self.description = "Undescribed Item"
		self.cost = 1
		self.visible = True
		self.spell = None
		self.quantity = 1
		self.asset = None

	def set_spell(self, spell):
		spell.range = 0
		spell.on_init()
		if spell.range == 0:
			spell.self_cast = True
		self.spell = spell
		spell.item = self
		spell.name = self.name

		if not spell.description:
			spell.description = self.description

	def get_asset(self):
		asset = ['tiles', 'items', 'animated', self.name.lower().replace(' ', '_')]
		# use generic trinket asset if specific asset is not present
		if not os.path.exists(os.path.join('rl_data', *asset) + '.png'):
			asset = ['tiles', 'items', 'animated', 'trinket']
		
		return asset

STACK_NONE = 0
STACK_DURATION = 1
STACK_INTENSITY = 2
STACK_REPLACE = 3
STACK_TYPE_TRANSFORM = 4

class Buff(object):

	def __init__(self):
		self.description = None
		self.owner_triggers = {}
		self.global_triggers = {}

		self.turns_left = 0
		self.color = None
		self.asset = None
		self.resists = defaultdict(lambda : 0)

		# source dtype -> dest dtype
		self.conversions = defaultdict(lambda : {})
		
		# Spell -> source dtype -> dest dtype
		self.spell_conversions = defaultdict(lambda : defaultdict (lambda : {}))

		self.spells = []
		self.stack_type = STACK_NONE

		self.owner = None

		self.applied = False
		self.name = "Unnamed buff"

		# self.spell_bonuses[spell][attr]
		self.spell_bonuses = defaultdict(lambda : defaultdict(lambda: 0))
		self.global_bonuses = defaultdict(lambda: 0)
		self.tag_bonuses = defaultdict(lambda : defaultdict(lambda: 0))

		self.spell_bonuses_pct = defaultdict(lambda : defaultdict(lambda: 0))
		self.global_bonuses_pct = defaultdict(lambda: 0)
		self.tag_bonuses_pct = defaultdict(lambda : defaultdict(lambda: 0))


		self.buff_type = BUFF_TYPE_BLESS
		self.show_effect = True

		self.transform_asset_name = None

		self.on_init()
		if self.conversions or self.spell_conversions:
			# For now- do not allow conversion AND global damage subscription
			# Perhaps later allow this by chaining the two functions together with functools or something
			assert EventOnPreDamaged not in self.global_triggers
			self.global_triggers[EventOnDamaged] = self.process_conversions

		# Do not allow setting of turns_left in on_init, since usually its an accidental overload of the term
		assert(self.turns_left == 0)

		self.prereq = None

	def can_threaten(self, x, y):
		return False

	def on_init(self):
		pass

	def on_applied(self, owner):
		pass

	def on_unapplied(self):
		pass

	# Rarely... but sometimes needed
	def on_pre_advance(self):
		pass

	def on_advance(self):
		pass

	def get_description(self):
		return self.description

	# Override to prevent the owner from advancing- ie for stun, or conditional stun
	def on_attempt_advance(self):
		return True

	# Override to prevent application in some circumstances- ie, not letting stun refresh on the player
	def on_attempt_apply(self, owner):
		return True

	def advance(self):
		
		self.on_advance()

		# Guard with if self.applied because advance might unapply (by for instance killing the owner)
		if self.applied:
			if self.turns_left > 0:
				self.turns_left -= 1
				if self.turns_left == 0:
					self.owner.remove_buff(self)

	def apply(self, owner):
		assert(not self.applied)
		self.owner = owner
		if self.on_applied(owner) == ABORT_BUFF_APPLY:
			return ABORT_BUFF_APPLY

		self.applied = True

		prev_max_charges = {spell: spell.get_stat('max_charges') for spell in self.owner.spells}

		event_manager = self.owner.level.event_manager

		if self.owner.level:
			self.subscribe()

		# Accumulate resists
		for dtype, resist in self.resists.items():
			self.owner.resists[dtype] += resist

		# Accumulate spell bonuses
		for attr, amt in self.global_bonuses.items():
			owner.global_bonuses[attr] += amt

		for attr, amt in self.global_bonuses_pct.items():
			owner.global_bonuses_pct[attr] += amt

		for spell_class, bonuses in self.spell_bonuses.items():
			for attr, amt in bonuses.items():
				owner.spell_bonuses[spell_class][attr] += amt

		for spell_class, bonuses in self.spell_bonuses_pct.items():
			for attr, amt in bonuses.items():
				owner.spell_bonuses_pct[spell_class][attr] += amt

		for tag, bonuses in self.tag_bonuses.items():
			for attr, amt in bonuses.items():
				owner.tag_bonuses[tag][attr] += amt

		for tag, bonuses in self.tag_bonuses_pct.items():
			for attr, amt in bonuses.items():
				owner.tag_bonuses_pct[tag][attr] += amt

		# Modify spells
		for spell in self.owner.spells:
			self.modify_spell(spell)

		# Add all new spells from this buff
		if self.spells:
			for spell in self.spells:
				if spell.name not in [s.name for s in self.owner.spells]:
					spell.added_by_buff = True
					self.owner.add_spell(spell)

		# Modify sprite on transforms
		if self.transform_asset_name:
			assert(self.stack_type == STACK_TYPE_TRANSFORM)
			self.owner.transform_asset_name = self.transform_asset_name

		# Update spells whos max charges have changed
		for spell in self.owner.spells:
			if spell not in prev_max_charges:
				continue

			charge_diff = spell.get_stat('max_charges') - prev_max_charges[spell]
			spell.cur_charges += charge_diff

	def unapply(self):

		assert(self.applied)
		self.applied = False

		prev_max_charges = {spell: spell.get_stat('max_charges') for spell in self.owner.spells}

		self.on_unapplied()

		# TODO- put passive effect stuff aka resistances here

		for dtype, resist in self.resists.items():
			self.owner.resists[dtype] -= resist

		# Unaccumulate spell bonuses
		for attr, amt in self.global_bonuses.items():
			self.owner.global_bonuses[attr] -= amt

		# Unaccumulate spell bonuses
		for attr, amt in self.global_bonuses_pct.items():
			self.owner.global_bonuses_pct[attr] -= amt

		for spell_class, bonuses in self.spell_bonuses.items():
			for attr, amt in bonuses.items():
				self.owner.spell_bonuses[spell_class][attr] -= amt

		for spell_class, bonuses in self.spell_bonuses_pct.items():
			for attr, amt in bonuses.items():
				self.owner.spell_bonuses_pct[spell_class][attr] -= amt

		for tag, bonuses in self.tag_bonuses.items():
			for attr, amt in bonuses.items():
				self.owner.tag_bonuses[tag][attr] -= amt

		for tag, bonuses in self.tag_bonuses_pct.items():
			for attr, amt in bonuses.items():
				self.owner.tag_bonuses_pct[tag][attr] -= amt


		# This is an intersting idea but it causes lots of race conditions when writing death triggers
		#self.owner = None

		spells_from_other_buffs = [s.name for b in self.owner.buffs for s in b.spells if b != self]
		for spell in self.owner.spells:

			# Remove all spells granted only by this buff
			if spell.added_by_buff and spell.name not in spells_from_other_buffs:
				self.owner.remove_spell(spell)

			self.unmodify_spell(spell)

		# Modify sprite on transforms
		if self.transform_asset_name:
			assert(self.stack_type == STACK_TYPE_TRANSFORM)
			assert(self.transform_asset_name == self.owner.transform_asset_name)
			self.owner.transform_asset_name = None
			self.owner.Transform_Anim = None

		self.unsubscribe()

		# Update spells whos max charges have changed
		for spell in self.owner.spells:
			if spell not in prev_max_charges:
				continue

			charge_diff = spell.get_stat('max_charges') - prev_max_charges[spell]
			spell.cur_charges += charge_diff

	def on_add_spell(self, spell):
		self.modify_spell(spell)

	def on_remove_spell(self, spell):
		self.unmodify_spell(spell)

	def subscribe(self):
		event_manager = self.owner.level.event_manager

		for event_type, trigger in self.owner_triggers.items():
			event_manager.register_entity_trigger(event_type, self.owner, trigger)
		for event_type, trigger in self.global_triggers.items():
			event_manager.register_global_trigger(event_type, trigger)

	def unsubscribe(self):
		event_manager = self.owner.level.event_manager
		
		for event_type, trigger in self.owner_triggers.items():
			event_manager.unregister_entity_trigger(event_type, self.owner, trigger)
		for event_type, trigger in self.global_triggers.items():
			event_manager.unregister_global_trigger(event_type, trigger)


	def process_conversions(self, evt): 
		# Do not deal damage to dead units
		if not evt.unit.is_alive():
			return

		# Global conversions: whenever an enemy takes any damage of the given type, redeal it as another type
		if evt.damage_type in self.conversions and are_hostile(self.owner, evt.unit):
			for dest_dtype, mult in self.conversions[evt.damage_type].items():
				self.owner.level.queue_spell(self.deal_conversion_damage(evt, mult, dest_dtype))


		# Check for conversions of 1) the spell which dealt the damage and 2) the spell which summoned the creature that cast the spell (if applicable)
		sources = [evt.source]
		if evt.source.owner:
			if type(evt.source.owner.source) in self.spell_conversions:
				sources.append(evt.source.owner.source)

		for source in sources:
			# Spell conversions only convert damage from the owner's spells (or minions)
			if source.owner != self.owner:
				continue

			if type(source) in self.spell_conversions:
				if evt.damage_type in self.spell_conversions[type(source)]:
					for dest_dtype, mult in self.spell_conversions[type(source)][evt.damage_type].items():
						self.owner.level.queue_spell(self.deal_conversion_damage(evt, mult, dest_dtype))
				
	def deal_conversion_damage(self, evt, mult, dest_dtype):
		if not evt.unit.is_alive():
			return
		for i in range(6):
			yield
		damage = round(mult * evt.damage)
		if damage > 0:
			evt.unit.deal_damage(damage, dest_dtype, self)
		
		# Todo- change up timings?

	# Called on each spell the owner has once
	def modify_spell(self, spell):
		pass

	def unmodify_spell(self, spell):
		pass

	# For examine
	def get_tooltip(self):
		return self.description

	def get_tooltip_color(self):
		return self.color if self.color else Color(255, 255, 255)

	def get_extra_examine_tooltips(self):
		return []

	def summon(self, unit, target=None, radius=3, team=None, sort_dist=True):
		unit.source = self
		if not target:
			target = Point(self.owner.x, self.owner.y)
		return self.owner.level.summon(self.owner, unit, target, radius, team, sort_dist)



class Upgrade(Buff):

	def __init__(self):
		Buff.__init__(self)
		self.level = 0
		self.tags = []
		self.description = ""
		self.prereq = None
		self.on_init()
		self.keystone = False
		self.stack_type = STACK_INTENSITY
		self.max_stacks = 1
		self.buff_type = BUFF_TYPE_PASSIVE
		self.shrine_name = None

	def fmt_dict(self):
		d = {}
		for stat in stat_names:
			if hasattr(self, stat):
				d[stat] = self.get_stat(stat)
		return d

	def get_stat(self, attr, base=None):
		if base is None:
			base = getattr(self, attr, 0)
		if self.owner:
			return self.owner.get_stat(base, self, attr)
		else:
			return base

class Equipment(Buff):

	def __init__(self):

		self.slot = -1
		self.level = 0
		self.asset_name = None
		self.recolor_primary = False
		self.recolor_secondary = False

		Buff.__init__(self)
		
		self.buff_type = BUFF_TYPE_ITEM
		self.stack_type = STACK_INTENSITY  # Allow multiples of same item to stack

	def __str__(self):
		return "Equipment: %s" % self.name

	def get_asset(self):
		asset = ['tiles', 'items', 'equipment', self.name.lower().replace(' ', '_') if not self.asset_name else self.asset_name]
		# use generic trinket asset if specific asset is not present
		if not os.path.exists(os.path.join('rl_data', *asset) + '.png'):

			if self.slot == ITEM_SLOT_AMULET:
				asset = ['tiles', 'items', 'equipment', 'generic_amulet']
			if self.slot == ITEM_SLOT_STAFF:
				asset = ['tiles', 'items', 'equipment', 'generic_staff']
			if self.slot == ITEM_SLOT_BOOTS:
				asset = ['tiles', 'items', 'equipment', 'generic_boots']
			if self.slot == ITEM_SLOT_ROBE:
				asset = ['tiles', 'items', 'equipment', 'generic_robe']
			if self.slot == ITEM_SLOT_HEAD:
				asset = ['tiles', 'items', 'equipment', 'generic_hat']
			
		return asset

	def get_extra_examine_tooltips(self):
		return None

ABORT_CHANNEL = 99
class ChannelBuff(Buff):

	def __init__(self, spell, target, cast_after_channel=False, channel_check=None, on_stop=None):
		Buff.__init__(self)
		self.spell = spell
		self.name = "Channeling"
		self.spell_target = target
		self.turns = 0
		self.passed = True
		self.owner_triggers[EventOnPass] = self.on_pass
		self.stack_type = STACK_INTENSITY

		self.buff_type = BUFF_TYPE_BLESS

		self.cast_after_channel = cast_after_channel
		self.channel_check = channel_check

		self.on_stop=on_stop

	def on_applied(self, owner):
		self.channel_turns = 0
		self.max_channel = self.turns_left

		buffs = [b for b in owner.buffs if isinstance(b, ChannelBuff)]
		for b in buffs:
			if b.spell != self.spell:
				owner.remove_buff(b)

	def on_unapplied(self):
		if self.on_stop:
			self.on_stop()
		
	def on_advance(self):

		self.channel_turns += 1

		if not self.passed:
			self.owner.remove_buff(self)
			return

		cast = False
		if not self.cast_after_channel:
			cast = True
			self.owner.level.queue_spell(self.spell(self.spell_target.x, self.spell_target.y, channel_cast=True))

		if self.cast_after_channel and self.channel_turns == self.max_channel:
			cast = True
			self.owner.level.queue_spell(self.spell(self.spell_target.x, self.spell_target.y, channel_cast=True))

		if cast and self.owner.is_player_controlled:
			self.owner.level.show_effect(0, 0, Tags.Sound_Effect, 'sorcery_ally')

		self.passed = False

	def on_pass(self, evt):
		self.passed = True

class SpellUpgrade(Upgrade):

	def __init__(self, spell, attribute, amount, level=1, tags=None, name=None, desc=None, exc_class=None):
		Upgrade.__init__(self)
		self.spell = type(spell)
		self.attribute = attribute.replace('_', ' ')
		self.spell_bonuses[type(spell)][attribute] = amount
		self.name = name if name else format_attr(attribute)
		self.tags = tags if tags else list(spell.tags)
		self.description = desc
		self.prereq = spell
		self.level = level
		self.amount = amount
		self.exc_class = exc_class

class Immobilize(Buff):

	def on_init(self):
		self.buff_type = BUFF_TYPE_CURSE
		self.stack_type = STACK_NONE
		self.name = "Immobilized"

class SiegeWeaponBuff(Buff):

	def __init__(self, operator_name):
		self.operator_name = operator_name
		Buff.__init__(self)

	def on_attempt_advance(self):
		return False

	def on_init(self):
		self.name = "Siege Machine"
		self.buff_type = BUFF_TYPE_PASSIVE
		self.description = "Must be operated by an adjacent %s." % self.operator_name

class BlindBuff(Buff):

	def on_init(self):
		self.name = "Blind"
		self.stack_type	= STACK_REPLACE
		self.buff_type = BUFF_TYPE_CURSE
		self.asset = ['status', 'blind']
		self.description = "All spells reduced to melee range"


class BerserkBuff(Buff):

	def __init__(self):
		Buff.__init__(self)
		self.name = "Berserk"
		self.buff_type = BUFF_TYPE_CURSE
		self.stack_type	= STACK_NONE
		self.asset = ['status', 'berserk']
		self.color = Color(255, 0, 0)

class Stun(Buff):

	def on_init(self):
		self.buff_type = BUFF_TYPE_CURSE
		self.stack_type	= STACK_NONE
		self.name = "Stunned"
		self.color = Color(220, 220, 220)
		self.asset = ['status', 'stun']
		self.description = "Cannot move or cast spells."

	def on_attempt_advance(self):
		return False

	def on_attempt_apply(self, owner):
		if owner.gets_clarity and owner.has_buff(Stun):
			return False
		return True

	def on_unapplied(self):
		if self.owner.gets_clarity:
			self.owner.apply_buff(StunImmune(), 1)

	def on_applied(self, owner):
		if owner.has_buff(StunImmune):
			return ABORT_BUFF_APPLY

class StunImmune(Buff):

	def on_init(self):
		self.buff_type = BUFF_TYPE_BLESS
		self.stack_type = STACK_NONE
		self.name = "Clarity"

	def get_tooltip(self):
		return "Cannot be stunned, frozen, or petrified."

class CowardBuff(Buff):

	def on_init(self):
		self.name = "Running Away"

	def on_applied(self, owner):
		self.owner.is_coward = True

	def on_unapplied(self):
		self.owner.is_coward = False


class Unit(object):

	def __init__(self):
		self.sprite = Sprite('?', Color(255, 0, 125))
		self.is_player_controlled = False
		self.max_hp = 1
		self.cur_hp = 0
		self.shields = 0
		self.clarity = 0
		self.spells = []
		self.name = "Unnamed"
		self.description = "Undescribed"
		self.mana = 0
		self.resists = defaultdict(lambda : 0)
		self.cool_downs = {}
		self.buffs = []
		self.tags = []
		self.items = []
		self.team = TEAM_ENEMY
		self.stationary = False
		self.bg_color = None
		self.flying = False

		self.glow = self.iter_buff_glow()
		self.turns_to_death = None
		self.gold = 0

		self.moves_per_turn = 1
		self.moves_left = 0

		self.spell_bonuses = defaultdict(lambda : defaultdict(lambda: 0))
		self.global_bonuses = defaultdict(lambda: 0)
		self.tag_bonuses = defaultdict(lambda : defaultdict(lambda: 0))
		
		self.spell_bonuses_pct = defaultdict(lambda : defaultdict(lambda: 0))
		self.global_bonuses_pct = defaultdict(lambda: 0)
		self.tag_bonuses_pct = defaultdict(lambda : defaultdict(lambda: 0))

		self.Anim = None
		self.Transform_Anim = None

		self.is_boss = False
		self.is_lair = False
		self.asset_name = None
		self.transform_asset_name = None

		self.killed = False

		self.debuff_immune = False
		self.buff_immune = False

		self.is_coward = False

		# The spell or buff which summoned this unit
		self.source = None

		self.stack_max = None

		# Does this unit get clarity after being stunned
		self.gets_clarity = False

		# Track whether the unit has been spawned yet- useful for making mutators only apply onces
		self.ever_spawned = False

		# The unit this unit spawned from- for bestiary completion
		self.parent = None

		self.asset = None

		# for 3x3, 5x5, 7x7 units
		# Use radius so that unit.x and unit.y give the unit's center
		self.radius = 0

		self.outline_color = None
		self.recolor_primary = None

		self.equipment = {}
		self.trinkets = []

		self.last_action = None

		self.burrowing = False

		self.boss_modifier = None

		self.melee_spell = None # Autospell to cast when the player melees something.  Only used by elephant form but could bring back flaming sword or something.

	def iter_occupied_points(self):
		for i in range(-self.radius, self.radius+1):
			for j in range(-self.radius, self.radius+1):
				yield Point(self.x + i, self.y + j)

	def get_asset_name(self):
		if self.asset_name:
			name = self.asset_name
		else:
			name = self.name.lower().replace(' ', '_')
		return name

	def get_stat(self, base, spell, attr):
		# Range for self targeted or melee spells does not change
		if attr == 'range' and spell.range < 2:
			return spell.range

		bonus_total = 0
		pct_total = 100.0

		# Accumulate spell specific bonus
		bonus_total += self.spell_bonuses[type(spell)].get(attr, 0)
		pct_total += self.spell_bonuses_pct[type(spell)].get(attr, 0)

		# Accumulate tag bonuses
		for tag in spell.tags:
			bonus_total += self.tag_bonuses[tag].get(attr, 0)
			pct_total += self.tag_bonuses_pct[tag].get(attr, 0)

		# Accumulate global bonus
		bonus_total += self.global_bonuses.get(attr, 0)
		pct_total += self.global_bonuses_pct.get(attr, 0)

		isint = type(base) == int

		value = (base + bonus_total) * (pct_total / 100.0)
		if isint:
			value = int(math.ceil(value))

		# Cap things at 0- or at 1, in the case of range or duration, as those function poorly when zeroed	
		value = max(value, 0)
		if attr in ['range', 'duration']:
			value = max(value, 1)

		return value

	def __reduce__(self):
		if self.Anim:
			self.Anim.unregister()
			self.Anim = None
		self.glow = None
		return object.__reduce__(self)

	def equip(self, item):
		assert(item.slot >= 0)

		# TEMP: all items stack.  Lets try it out.
		if item.slot != ITEM_SLOT_AMULET:
			to_replace = self.equipment.get(item.slot)
			if to_replace:
				self.unequip(to_replace)

			self.equipment[item.slot] = item
		else:
			self.trinkets.append(item)

		self.apply_buff(item)

		# Instantly proc on unit added self triggers
		if EventOnUnitAdded in item.owner_triggers:
			evt = EventOnUnitAdded(self)
			item.owner_triggers[EventOnUnitAdded](None)


	def unequip(self, item):
		if item.slot != ITEM_SLOT_AMULET:
			self.equipment[item.slot] = None
		else:
			self.trinkets.remove(item)
			
		self.remove_buff(item)

		# TODO- Find a tile without a prop?  Generally unequip comes after a prop is destroyed anyways so its generally ok?
		self.level.add_prop(EquipPickup(item), self.x, self.y)


	def add_item(self, item):
		existing = [i for i in self.items if i.name == item.name]
		if existing:
			existing[0].quantity += 1
		else:
			if item.spell:
				item.spell.caster = self
				item.spell.owner = self
			self.items.append(item)

	def remove_item(self, item):
		item = [i for i in self.items if i.name == item.name][0]
		item.quantity -= 1
		if item.quantity == 0:
			self.items.remove(item)

	def get_skills(self):
		return sorted((b for b in self.buffs if b.buff_type == BUFF_TYPE_PASSIVE and b.prereq == None), key=lambda b: b.name)

	def try_enter(self, other):
		return False

	def pre_advance(self):
		# Pre turn effects
		self.cool_downs = { spell : (cooldown - 1) for (spell, cooldown) in self.cool_downs.items() if cooldown > 1}

		for b in self.buffs:
			b.on_pre_advance()

	def advance(self, orders=None):
	
		can_act = True
		for b in self.buffs:
			if not b.on_attempt_advance():
				can_act = False
				if self.is_player_controlled:
					stun_duration = 1 if not isinstance(self.last_action, StunnedAction) else self.last_action.duration + 1
					self.last_action = StunnedAction(b, stun_duration)
					self.level.requested_action = None

		if can_act:
			# Take an action
			if not self.is_player_controlled:
				action = self.get_ai_action()
			else:
				action = self.level.requested_action
				self.level.requested_action = None
				self.last_action = action
				
			logging.debug("%s will %s" % (self, action))
			assert(action is not None)

			if isinstance(action, MoveAction):
				self.level.act_move(self, action.x, action.y)
			elif isinstance(action, CastAction):
				self.level.act_cast(self, action.spell, action.x, action.y)
				if action.spell.get_stat('quick_cast'):
					return False
			elif isinstance(action, PassAction):
				self.level.event_manager.raise_event(EventOnPass(self), self)


		self.try_dismiss_ally()

		# TODO- post turn effects
		# TODO- return False if a non turn consuming action was taken
		return True

	def try_dismiss_ally(self):
		# dont dismiss in tests ect
		if not self.level.player_unit:
			return

		if not any(are_hostile(self.level.player_unit, u) for u in self.level.units):
			if not self.is_player_controlled:
				if random.random() < .2:
					self.kill(trigger_death_event=False)
					self.level.show_effect(self.x, self.y, Tags.Translocation)

	def advance_buffs(self):
		# Advance buffs after the character.
		# This way poison burning ect can be cured before they kill you, and lightning form doesnt glow when you cant actually use it.
		# Copy the list before iteration since we advance could modify the list
		for buff in list(self.buffs):
			buff.advance()

		# Do this here so that buffs advance N turns on creatures meant to live N turns
		if self.turns_to_death is not None:
			self.turns_to_death -= 1
			if self.turns_to_death <= 0 and self.is_alive():
				self.kill()
				self.level.show_effect(self.x, self.y, Tags.Translocation)

	def is_blind(self):
		return self.has_buff(BlindBuff)

	def is_stunned(self):
		# Skip action if stunned, but advance buffs first.
		for b in self.buffs:
			if isinstance(b, Stun):
				return True
		
		return False

	def can_harm(self, other):
		for s in self.spells:
			if not hasattr(s, 'damage_type'):
				return True
			if isinstance(s.damage_type, list):
				for d in s.damage_type:
					if other.resists[d] < 100:
						return True
			else:
				if other.resists[s.damage_type] < 100:
					return True
		return False

	def get_ai_action(self):
		
		assert(not self.is_player_controlled)
		assert(self.is_alive())
		assert(not self.killed)

		# For now always channel if you can
		if self.has_buff(ChannelBuff):
			b = self.get_buff(ChannelBuff)

			if b.channel_check:
				if b.channel_check(b.spell_target):
					return PassAction()
				else:
					# If should not channel, keep going to decide on action
					pass
			else:
				# If no channel check exists, default to continue channeling
				return PassAction()

		for spell in self.spells:
			if not spell.can_pay_costs():
				continue

			spell_target = spell.get_ai_target()
			if spell_target and not spell.can_cast(spell_target.x, spell_target.y):
				# Should not happen ever but sadly it does alot
				target_unit = self.level.get_unit_at(spell_target.x, spell_target.y)
				if target_unit:
					target_str = target_unit.name
					if target_unit == self:
						target_str = 'self'
				else:
					target_str = "empty tile"
				print("%s wants to cast %s on invalid target (%s)" % (self.name, spell.name, target_str))
				continue
			if spell_target:
				return CastAction(spell, spell_target.x, spell_target.y)

		# Stationary monsters pass if they cant cast
		if self.stationary:
			return PassAction()

		# Currently select targets via controller
		if not self.is_coward:
			possible_movement_targets = [u for u in self.level.units if self.level.are_hostile(self, u) and u.turns_to_death is None and self.can_harm(u)]

			# Non flying monsters will not move towards flyers over chasms
			if not self.flying:
				possible_movement_targets = [u for u in possible_movement_targets if self.level.tiles[u.x][u.y].can_walk]

			# The player is always prioritized if possible
			if any(u.is_player_controlled for u in possible_movement_targets):
				possible_movement_targets = [u for u in possible_movement_targets if u.is_player_controlled]

		# Cowards move away from closest enemy, swapping if neccecary
		else:
			enemies = [u for u in self.level.units if self.level.are_hostile(self, u)]
			if enemies:
				enemies.sort(key = lambda u: distance(self, u))
				closest = enemies[0]

				def can_flee_to(p):
					unit = self.level.get_unit_at(p.x, p.y)
					if unit and are_hostile(self, unit):
						return False
					# Don't let cowards continually swap with each other- looks like no one is moving at all when that happens
					if unit and unit.is_coward:
						return False
					# Don't flee through a player, its confusing
					if unit and unit.is_player_controlled:
						return False
					# Don't swap with stationary units
					if unit and unit.stationary:
						return False
					# Must be able to walk on the tile
					if not self.level.can_stand(p.x, p.y, self, check_unit=False):
						return False
					# Cannot swap with 3x3s
					if unit and unit.radius:
						return False
					# If there is a unit, *it* must be able to walk on the tile I am currently on
					if unit and not self.level.can_stand(self.x, self.y, unit, check_unit=False):
						return False
					return True

				best_flee_points = [p for p in self.level.get_adjacent_points(self, filter_walkable=False) if can_flee_to(p)]
				choices = [(p, distance(p, closest)) for p in best_flee_points]
				if best_flee_points:
					best_flee_points.sort(key = lambda p: distance(p, closest), reverse=True)

					best_dist = distance(best_flee_points[0], closest)
					best_flee_points = [p for p in best_flee_points if distance(p, closest) >= best_dist]

					p = random.choice(best_flee_points)
					return MoveAction(p.x, p.y)
				else:
					possible_movement_targets = None
			else:
				possible_movement_targets = None

		if not possible_movement_targets:

			# Move randomly if there are no enemies in the level
			possible_movement_targets = [p for p in self.level.get_adjacent_points(Point(self.x, self.y), check_unit=True, filter_walkable=False) if self.level.can_stand(p.x, p.y, self)]
			if not possible_movement_targets:
				return PassAction()
			else:
				p = random.choice(possible_movement_targets)
				return MoveAction(p.x, p.y)

		target = min(possible_movement_targets, key = lambda t: distance(Point(self.x, self.y), Point(t.x, t.y)))

		if distance(Point(target.x, target.y), Point(self.x, self.y)) >= 2:
			path = self.level.find_path(Point(self.x, self.y), Point(target.x, target.y), self)

			if path:
				if libtcod.path_size(path) > 0:
					x, y = libtcod.path_get(path, 0)
					if self.level.can_move(self, x, y):
						return MoveAction(x, y)

				libtcod.path_delete(path)

		# If you cant do anything then pass
		return PassAction()

	def is_alive(self):
		return self.cur_hp > 0 and not self.killed

	def add_spell(self, spell, prepend=False):

		# Avoid having two duplicately named spells since they basically count as the same spell
		existing = [s for s in self.spells if s.name == spell.name]
		if existing:
			return

		for buff in self.buffs:
			if buff.applied:
				buff.on_add_spell(spell)

		spell.caster = self
		spell.owner = self
		spell.cur_charges = spell.get_stat('max_charges')
		
		if not prepend:
			self.spells.append(spell)
		else:
			self.spells.insert(0, spell)

	def remove_spell(self, spell):
		# Remove spell by name, dont worry about pointer address
		self.spells = [s for s in self.spells if s.name != spell.name]

		# Do not None the caster because the spell might be currently queued
		#spell.caster = None
		
		for buff in self.buffs:
			if buff.applied:
				buff.on_remove_spell(spell)

	def apply_buff(self, buff, duration=0):
		assert(isinstance(buff, Buff))

		# If we call this method before adding the monster to the level just add the buff to the list and we will call this again later
		if not hasattr(self, 'level'):
			self.buffs.append(buff)
			return
		
		# Do not apply buffs to dead units
		if not self.is_alive():
			return

		if self.clarity > 0 and buff.buff_type == BUFF_TYPE_CURSE:
			self.clarity -= 1
			return

		if not buff.on_attempt_apply(self):
			return	

		if buff.buff_type == BUFF_TYPE_CURSE and self.debuff_immune:
			return
		if buff.buff_type == BUFF_TYPE_BLESS and self.buff_immune:
			return

		#assert(self.level)
		# For now unstackable = stack_type stack duration

		# Do not refresh stuns on clarity havers
		# Otherwise they can get stunlocked by anything with 2 or more duration
		# Which defeats the purpose of clarity
		if self.gets_clarity and isinstance(buff, Stun) and self.is_stunned():
			return

		def same_buff(b1, b2):
			return b1.name == b2.name and type(b1) == type(b2)

		existing = [b for b in self.buffs if same_buff(b, buff)]
		if existing:

			if buff.stack_type == STACK_NONE:
				existing[0].turns_left = max(duration, existing[0].turns_left)
				return
			elif buff.stack_type == STACK_DURATION:
				existing[0].turns_left += duration
				return
			elif buff.stack_type == STACK_REPLACE:
				self.remove_buff(existing[0])
				# And continue to add this one

		if buff.stack_type == STACK_TYPE_TRANSFORM:
			existing = [b for b in self.buffs if b != buff and b.stack_type == STACK_TYPE_TRANSFORM]
			if existing:
				self.remove_buff(existing[0])

		assert(isinstance(buff, Buff))
		buff.turns_left = duration
		
		self.buffs.append(buff)
		result = buff.apply(self)
		if result == ABORT_BUFF_APPLY:
			self.buffs.remove(buff)
			return

		if buff.show_effect:
			if buff.buff_type == BUFF_TYPE_BLESS:
				if self.buff_immune:
					return
				self.level.show_effect(self.x, self.y, Tags.Buff_Apply, buff.color)
			if buff.buff_type == BUFF_TYPE_CURSE:
				if self.debuff_immune:
					return
				self.level.show_effect(self.x, self.y, Tags.Debuff_Apply, buff.color)
		

		self.level.event_manager.raise_event(EventOnBuffApply(buff, self), self)

	def remove_buff(self, buff):

		if buff not in self.buffs:
			return
		if not buff.applied:
			return

		self.buffs.remove(buff)
		buff.unapply()

		self.level.event_manager.raise_event(EventOnBuffRemove(buff, self), self)

	def remove_buffs(self, buff_class):
		to_remove = [b for b in self.buffs if isinstance(b, buff_class)]
		for b in to_remove:
			self.remove_buff(b)

	def has_buff(self, buff_class):
		for b in self.buffs:
			if isinstance(b, buff_class):
				return True
		return False

	def get_buff(self, buff_class):
		candidates = [b for b in self.buffs if isinstance(b, buff_class)]
		if candidates:
			return candidates[0]
		else:
			return None

	def get_buff_stacks(self, buff_class):
		return len([b for b in self.buffs if isinstance(b, buff_class)])

	def iter_buff_glow(self):
		glow_frames = 15
		wait_frames = 15
		while True:
			# TODO- cut glow short if buff is removed?
			buffs = list(self.buffs)

			for buff in buffs:
				if not buff.color:
					continue

				for color1, color2 in [(self.sprite.color, buff.color),
									   (buff.color, self.sprite.color)]:
					for i in range(glow_frames):
						glow_tween = i / float(glow_frames)
						yield tween_color(color1, color2, glow_tween)

			for i in range(wait_frames):
				yield self.sprite.color

	def steal_hp(self, amount, source):

		amount = min(self.cur_hp, amount)
		self.cur_hp -= amount
		
		self.event_manager.raise_event()

		if self.cur_hp <= 0:
			self.kill()

		self.level.show_effect(self.x, self.y, Tags.Blood)

		source_name = "%s's %s" % (source.owner.name, source.name) if source.owner else source.name
		self.level.combat_log.debug("%s lost %d life from %s" % (self.name, amount, source_name))

		return amount

	def heal(self, amount, spell):
		if not self.is_alive():
			return 0

		return self.level.deal_damage(self.x, self.y, -amount, Tags.Heal, spell)

	def deal_damage(self, amount, damage_type, spell):
		if not self.is_alive():
			return 0
		return self.level.deal_damage(self.x, self.y, amount, damage_type, spell)

	def add_shields(self, shields):
		self.level.show_effect(self.x, self.y, Tags.Shield_Apply)
		self.shields += shields

		# Max 20 shields
		self.shields = min(self.shields, 20)

	def remove_shields(self, shields):
		if not self.shields:
			return

		self.level.show_effect(self.x, self.y, Tags.Shield_Expire)
		
		self.shields -= shields
		if self.shields < 0:
			self.shields = 0


	def can_teleport(self):
		return self.radius == 0

	def refresh(self):
		
		# Remove all temporary buffs and debuffs
		temp_buffs = [b for b in self.buffs if b.buff_type in [BUFF_TYPE_CURSE, BUFF_TYPE_BLESS]]
		for d in temp_buffs:
			self.remove_buff(d)

		self.cur_hp = self.max_hp

		for s in self.spells:
			s.cur_charges = s.get_stat('max_charges')

		self.shields = 0

		self.killed = False

	# Used by things other than the unit to make the unit cast a spell
	def get_spell(self, spell_class):
		spells = [s for s in self.spells if isinstance(s, spell_class)]
		if not spells:
			return None

		return spells[0]
		
	# Get the spell if it exists in the units spell list, make it up if it doesnt
	def get_or_make_spell(self, spell_class):
		spell = self.get_spell(spell_class)
		if spell:
			return spell

		spell = spell_class()
		spell.owner = self
		spell.caster = self
		return spell

	def kill(self, damage_event=None, trigger_death_event=True):
		# Sometimes you kill something twice, whatever.
		if self.killed:
			return

		# TODO- trigger on death events and such?
		if trigger_death_event:
			self.level.event_manager.raise_event(EventOnDeath(self, damage_event), self)
			if self.level.player_unit and self.level.player_unit != self:
				if are_hostile(self.level.player_unit, self):
					self.level.turn_summary.enemy_kill_counts[self.name] += 1
				else:
					self.level.turn_summary.ally_kill_counts[self.name] += 1
		self.level.remove_obj(self)
		self.cur_hp = 0
		self.killed = True


BUFF_TYPE_PASSIVE = 0
BUFF_TYPE_BLESS = 1
BUFF_TYPE_CURSE = 2
BUFF_TYPE_ITEM = 3
BUFF_TYPE_NONE = -1

TILE_FLOOR = 0
TILE_WALL = 1
TILE_CHASM = 2

CHAR_FLOOR_CROSS = 197
CHAR_FLOOR_HORIZONTAL = 196
CHAR_FLOOR_VERTICAL = 179

CHAR_FLOOR_T_RIGHT = 195
CHAR_FLOOR_T_DOWN = 194
CHAR_FLOOR_T_UP = 193
CHAR_FLOOR_T_LEFT = 180

CHAR_FLOOR_UR = 192 
CHAR_FLOOR_LL = 191 
CHAR_FLOOR_LR = 218 
CHAR_FLOOR_UL = 217

CHAR_SMALL_DOT = 250

CHAR_WALL_CROSS = 206
CHAR_WALL_HORIZONTAL = 205
CHAR_WALL_VERTICAL = 186

CHAR_WALL_T_RIGHT = 204
CHAR_WALL_T_DOWN = 203
CHAR_WALL_T_LEFT = 185
CHAR_WALL_T_UP = 202

CHAR_WALL_UL = 188
CHAR_WALL_LL = 187
CHAR_WALL_UR = 200
CHAR_WALL_LR = 201 

class Tile(object):
	def __init__(self, char='*', color=Color(255, 0, 125), can_walk=True, x=0, y=0, level=None):
		self.sprite = Sprite(char, color)
		self.sprite_override = None
		self.can_walk = can_walk
		self.can_see = True
		self.can_fly = True
		self.unit = None
		self.prop = None
		self.cloud = None
		self.name = "Tile"
		self.description = "Tile"
		self.x = x
		self.y = y
		self.is_chasm = False
		self.level = level
		self.sprites = None
		self.star = None
		self.tileset = 'glass'
		self.water = None

	def __reduce__(self):
		self.star = None
		self.sprites = None
		return object.__reduce__(self)

	def is_floor(self):
		return self.can_walk

	def is_wall(self):
		return not self.can_see

	def is_outer_wall(self):
		return self.is_wall() and not self.is_inner_wall()

	def is_inner_wall(self):
		if not self.is_wall():
			return False

		neighbors = list(self.level.get_points_in_rect(self.x-1, self.y-1, self.x+1, self.y+1))
		# Edge tiles are not inner walls
		if len(neighbors) != 9:
			return False
		return all(self.level.tiles[p.x][p.y].is_wall() for p in neighbors)

	def is_inner_floor(self):
		return self.is_floor() and not self.is_outer_floor()

	def is_outer_floor(self):
		if not self.is_floor():
			return False
		neighbors = self.level.get_points_in_ball(self.x, self.y, 1.5)
		# Edge tiles are not inner floors
		return any(self.level.tiles[p.x][p.y].is_chasm for p in neighbors)

	def calc_glyph(self, cascade=True):
		return

		level = self.level
		global visual_mode
		if visual_mode:
			self.sprites = None
			if cascade:
				for p in [Point(self.x, self.y + 1),
						  Point(self.x, self.y - 1),
						  Point(self.x - 1, self.y),
						  Point(self.x + 1, self.y)]:
					if not level.is_point_in_bounds(p):
						continue
					level.tiles[p.x][p.y].sprites = None
			return False

		if self.is_floor():
			self.sprite.char = chr(0)

			above = level.tiles[self.x][self.y - 1].is_outer_floor() if level.is_point_in_bounds(Point(self.x, self.y - 1)) else False
			below = level.tiles[self.x][self.y + 1].is_outer_floor() if level.is_point_in_bounds(Point(self.x, self.y + 1)) else False
			right = level.tiles[self.x + 1][self.y].is_outer_floor() if level.is_point_in_bounds(Point(self.x + 1, self.y)) else False
			left = level.tiles[self.x - 1][self.y].is_outer_floor() if level.is_point_in_bounds(Point(self.x - 1, self.y)) else False

			# If only one floor neighbor use wall neighbors
			if len([x for x in [above, below, right, left] if x]) == 1:
				above |= not level.is_point_in_bounds(Point(self.x, self.y - 1)) or level.tiles[self.x][self.y - 1].is_wall()
				below |= not level.is_point_in_bounds(Point(self.x, self.y + 1)) or level.tiles[self.x][self.y + 1].is_wall()
				right |= not level.is_point_in_bounds(Point(self.x + 1, self.y)) or level.tiles[self.x + 1][self.y].is_wall()
				left |= not level.is_point_in_bounds(Point(self.x - 1, self.y)) or level.tiles[self.x - 1][self.y].is_wall()


			# No neighbors: use a dot
			if self.is_inner_floor():
				self.sprite.char = CHAR_SMALL_DOT
			# All neighbors: Use a cross
			elif above and below and left and right:
				self.sprite.char = CHAR_FLOOR_CROSS
			# Left or right neighbor but no top or bottom neighbor: horizontal line
			elif not above and not below and (left or right):
				self.sprite.char = CHAR_FLOOR_HORIZONTAL
			# Above orbelow neighbor but no left or right: vertical line
			elif not left and not right and (above or below):
				self.sprite.char = CHAR_FLOOR_VERTICAL
			# 4 corners
			elif above and right and not left and not below:
				self.sprite.char = CHAR_FLOOR_UR
			elif right and below and not above and not left:
				self.sprite.char = CHAR_FLOOR_LR
			elif below and left and not above and not right:
				self.sprite.char = CHAR_FLOOR_LL
			elif left and above and not below and not right:
				self.sprite.char = CHAR_FLOOR_UL
			# T connectors
			elif above and right and left and not below:
				self.sprite.char = CHAR_FLOOR_T_UP
			elif above and right and below and not left:
				self.sprite.char = CHAR_FLOOR_T_RIGHT
			elif right and below and left and not above:
				self.sprite.char = CHAR_FLOOR_T_DOWN
			elif below and above and left and not right:
				self.sprite.char = CHAR_FLOOR_T_LEFT

			if self.is_inner_floor():
				self.sprite.char = CHAR_SMALL_DOT
			
			self.sprite.color = Color(190, 190, 190)

		elif self.is_wall():
			above = level.tiles[self.x][self.y - 1].is_outer_wall() if level.is_point_in_bounds(Point(self.x, self.y - 1)) else False
			below = level.tiles[self.x][self.y + 1].is_outer_wall() if level.is_point_in_bounds(Point(self.x, self.y + 1)) else False
			right = level.tiles[self.x + 1][self.y].is_outer_wall() if level.is_point_in_bounds(Point(self.x + 1, self.y)) else False
			left = level.tiles[self.x - 1][self.y].is_outer_wall() if level.is_point_in_bounds(Point(self.x - 1, self.y)) else False
			self.sprite.color = Color(135, 135, 135)
			# No neighbors: use a cross
			if self.is_inner_wall():
				self.sprite.char = (chr(176))				
			elif not above and not below and not right and not left:
				self.sprite.char = CHAR_WALL_CROSS
			# All neighbors: Use a cross
			elif above and below and left and right:
				self.sprite.char = CHAR_WALL_CROSS
			# Left or right neighbor but no top or bottom neighbor: horizontal line
			elif not above and not below and (left or right):
				self.sprite.char = CHAR_WALL_HORIZONTAL
			# Above orbelow neighbor but no left or right: vertical line
			elif not left and not right and (above or below):
				self.sprite.char = CHAR_WALL_VERTICAL
			# 4 corners
			elif above and right and not left and not below:
				self.sprite.char = CHAR_WALL_UR
			elif right and below and not above and not left:
				self.sprite.char = CHAR_WALL_LR
			elif below and left and not above and not right:
				self.sprite.char = CHAR_WALL_LL
			elif left and above and not below and not right:
				self.sprite.char = CHAR_WALL_UL
			# T connectors
			elif above and right and left and not below:
				self.sprite.char = CHAR_WALL_T_UP
			elif above and right and below and not left:
				self.sprite.char = CHAR_WALL_T_RIGHT
			elif right and below and left and not above:
				self.sprite.char = CHAR_WALL_T_DOWN
			elif below and above and left and not right:
				self.sprite.char = CHAR_WALL_T_LEFT

			self.sprite.char = chr(219)
			shade = random.randint(80, 160)
			self.sprite.color = Color(shade, shade, shade)

		elif self.is_chasm:
			self.sprite.char = chr(0)

		if cascade:
			for p in [Point(self.x, self.y + 1),
					  Point(self.x, self.y - 1),
					  Point(self.x - 1, self.y),
					  Point(self.x + 1, self.y)]:
				if not level.is_point_in_bounds(p):
					continue
				level.tiles[p.x][p.y].calc_glyph(cascade=False)

class Prop(object):

	def on_player_enter(self, player):
		pass

	def on_unit_enter(self, unit):
		pass

	def on_player_exit(self, player):
		pass

	def advance(self):
		pass

	def __reduce__(self):
		self.Sprite = None
		return object.__reduce__(self)

class Portal(Prop):
	def __init__(self, level_gen_params, reroll=False):
		self.sprite = Sprite(chr(25), Color(160, 160, 160))
		self.name = "Rift"
		self.level_gen_params = level_gen_params
		self.description = level_gen_params.get_description()
		self.next_level = None
		self.locked = True
		self.reroll = reroll

		self.asset = ['tiles', 'portal', 'dormant_portal']

	def on_player_enter(self, player):
		if self.reroll:
			self.next_level = None
			
		if not self.locked:
			self.level.cur_portal = self

	def advance(self):
		if self.level.gen_params.difficulty == LAST_LEVEL:
			self.level.show_effect(self.x, self.y, Tags.Arcane)
			self.level.remove_prop(self)

		if all(u.team == TEAM_PLAYER for u in self.level.units):
			self.unlock()

	def unlock(self):
		self.locked = False
		self.sprite.color = Color(255, 50, 255)

		self.asset = ['tiles', 'portal', 'active_portal']

	
EventOnHealDotConsumed = namedtuple("EventOnHealDotConsumed", "consumer")
class HealDot(Prop):

	def __init__(self):
		self.sprite = Sprite(chr(7), color=Color(255, 100, 100))
		self.name = "Heal Dot"
		self.description = "Restores max health"

	def on_player_enter(self, player):

		self.level.event_manager.raise_event(EventOnHealDotConsumed(player), player)
		player.cur_hp += player.max_hp
		player.cur_hp = min(player.cur_hp, player.max_hp)
		self.level.remove_prop(self)

class ManaDot(Prop):
	def __init__(self):
		self.name = "Memory Orb"
		self.sprite = Sprite(chr(249), color=COLOR_MANA)
		self.description = "Grants 1 SP"
		self.asset = ['tiles', 'items', 'animated', 'mana_orb']

	def on_player_enter(self, player):
		player.xp = player.xp + 1
		self.level.remove_prop(self)
		self.level.event_manager.raise_event(EventOnItemPickup(self), player)


class ChargeDot(Prop):
	def __init__(self):
		self.name = "Spell Recharge"
		self.sprite = Sprite(chr(7), color=COLOR_MANA)
		self.mana = 100
		self.description = "Restores all spell charges"

	def on_player_enter(self, player):
		for spell in player.spells:
			spell.cur_charges = spell.max_charges
		self.level.remove_prop(self)

class SpellScroll(Prop):

	def __init__(self, spell):
		self.spell = spell
		self.name = 'Scroll: %s' % spell.name
		self.description = 'Learn %s for free' % spell.name
		self.asset = ['tiles', 'library', 'library_white']

	def on_player_enter(self, player):
		if self.spell not in player.spells:
			player.add_spell(self.spell)
			self.level.remove_prop(self)
			self.level.event_manager.raise_event(EventOnItemPickup(self), player)

class HeartDot(Prop):
	def __init__(self, bonus=10):
		self.name = "Ruby Heart"
		self.bonus = bonus
		self.description = "Increase max hp by %d" % self.bonus
		self.sprite = Sprite(chr(3), Color(255, 0, 0))
		self.asset = ['tiles', 'items', 'animated', 'ruby_heart']

	def on_player_enter(self, player):
		player.max_hp += self.bonus
		player.cur_hp += self.bonus
		self.level.remove_prop(self)
		self.level.event_manager.raise_event(EventOnItemPickup(self), player)

class GoldDot(Prop):
	def __init__(self):
		self.name = "Gold"
		self.sprite = Sprite(chr(249), color=Color(252, 186, 3))
		self.gold = 1
		self.description = "%d gold seeking a worthy owner" % self.gold

	def on_player_enter(self, player):
		player.gold += self.gold
		self.level.remove_prop(self)

CURRENCY_GOLD = 0
CURRENCY_PICK = 2
CURRENCY_MAX_HP = 3

class PlaceOfPower(Prop):

	def __init__(self, tag=None):
		if not tag:
			tag = random.choice(Knowledges)
		self.tag = tag
		self.name = "%s Circle" % self.tag.name
		self.sprite = Sprite(chr(247), self.tag.color)
		self.description = '%s spells, spell upgrades, and passive skills are 1SP cheaper here' % self.tag.name
		self.asset = ['tiles', 'circleofpower', 'circleofpower']

	def on_player_enter(self, player):
		player.discount_tag = self.tag

	def on_player_exit(self, player):
		player.discount_tag = None

class NPC(Prop):

	def __init__(self, name, description, dialogue, color):
		self.name = name
		self.description = description
		self.dialogue = dialogue
		self.sprite = Sprite(chr(2), color)

	def on_player_enter(self, player):
		self.level.cur_chatter = self

	def advance(self):

		if random.random() < .75:
			return

		move_points = list(self.level.get_adjacent_points(Point(self.x, self.y)))
		random.shuffle(move_points)
		for p in move_points:
			if self.level.tiles[p.x][p.y].prop == None:
				self.level.remove_obj(self)
				self.level.add_obj(self, p.x, p.y)
				return

class Shop(Prop):

	def __init__(self):
		self.sprite = Sprite('$')
		self.items = []

		self.name = "Shop"
		self.description = "What wonders could be contained for sale within?"
		self.currency = CURRENCY_PICK

		# For now...
		self.asset = ['tiles', 'shrine', 'shrine_white']

	def buy(self, shopper, item):

		assert(isinstance(shopper, Unit))
		assert(item in self.items)

		self.on_buy(shopper, item)

		if isinstance(item, Item):
			shopper.add_item(item)
		elif isinstance(item, Equipment):
			shopper.equip(item)
		elif isinstance(item, Buff):
			shopper.apply_buff(item)
		elif isinstance(item, Spell):
			shopper.add_spell(item)
		else:
			assert(False)

		if self.currency == CURRENCY_PICK:
			self.level.cur_shop = None
			self.level.remove_prop(self)
			self.items = []
		elif self.currency == CURRENCY_MAX_HP:
			self.items.remove(item)
			shopper.max_hp -= item.cost
			if shopper.max_hp < shopper.cur_hp:
				shopper.cur_hp = shopper.max_hp
		else:
			self.items.remove(item)


	def on_buy(self, shopper, item):
		pass

	def can_shop(self, shopper, item):
		if item is None:
			return True
	
		if item not in self.items:
			return False

		assert(isinstance(shopper, Unit))

		if self.currency == CURRENCY_GOLD:
			return shopper.gold >= item.cost
		if self.currency == CURRENCY_PICK:
			return True
		if self.currency == CURRENCY_MAX_HP:
			return shopper.max_hp > item.cost

	def on_player_enter(self, player):
		player.level.cur_shop = self

class ShiftingShop(Shop):

	def __init__(self, get_items_func):
		self.get_items_func = get_items_func
		Shop.__init__(self)

	def on_player_enter(self, player):
		self.items = self.get_items_func()
		Shop.on_player_enter(self, player)

class ShrineShop(ShiftingShop):

	def on_buy(self, shopper, item):
		# remove any other shrine buffs on the same spell
		pre_existing = [b for b in shopper.buffs if isinstance(b, Upgrade) and b.prereq == item.prereq and b.shrine_name and b != item]
		for b in pre_existing:
			shopper.remove_buff(b)

		# TODO- summon guardian here?

class EquipPickup(Prop):

	def __init__(self, item):
		self.item = item
		self.description = item.description
		self.name = item.name
		self.asset = item.get_asset()

	def on_player_enter(self, player):
		self.level.remove_prop(self)
		self.level.event_manager.raise_event(EventOnItemPickup(self.item), player)

		# Todo- by default do not swap with held item
		player.equip(self.item)
		
class ItemPickup(Prop):

	def __init__(self, item):
		self.item = item
		self.name = item.name
		self.description = item.description
		self.cost = 1

		self.asset = item.get_asset()
		

	def on_player_enter(self, player):
		if len(player.items) >= 10 and self.item.name not in [i.name for i in player.items]:
			return
		
		existing = [i for i in player.items if i.name == self.name]
		if existing:
			if player.stack_max is not None and existing[0].quantity >= player.stack_max:
				return

		player.add_item(self.item)
		self.level.remove_prop(self)
		self.level.event_manager.raise_event(EventOnItemPickup(self.item), player)

class LiquidChasms(object):

	class LiquidTile(object):

		def __init__(self, tile, environment):
			self.environment = environment
			self.sprite = Sprite(247, self.environment.wave_color)

			tile.sprite_override = self.sprite

			self.sprite.bg_color = tween_color(self.environment.bg_min_color, self.environment.bg_max_color, random.random())
			self.pick_water_color()

		def advance(self):
			if random.random() < self.environment.shift_chance:
				self.pick_water_color()

		def pick_water_color(self):
			t = random.random()
			dest_color = tween_color(self.environment.bg_min_color, self.environment.bg_max_color, t)
			self.sprite.bg_color = tween_color(self.sprite.bg_color, dest_color, self.environment.shift_amount)

	# Liquid- put a wave tile in each chasm
	# Each frame, shift each tiles bg color by its color velocity
	# Each frame, chance to change  bg color velocity

	def __init__(self, level):

		self.wave_color = Color(0, 0, 64)

		self.bg_min_color = Color(0, 0, 80)
		self.bg_max_color = Color(0, 0, 150)

		self.shift_amount = .15

		self.shift_chance = .05
		self.tiles = None
		self.level = level

	def advance(self):
		if self.tiles is None:
			self.tiles = [self.LiquidTile(tile, self) for tile in self.level.iter_tiles() if tile.is_chasm]

		for tile in self.tiles:
			tile.advance()



class StarrySkyChasms(object):

	class Star(object):

		def __init__(self, tile, color, lifetime):
			self.tile = tile
			self.sprite = Sprite(CHAR_SMALL_DOT, Color(0, 0, 0) )
			self.lifetime = lifetime
			self.frame = 0
			self.finished = False
			self.tile.sprite_override = self.sprite

			self.color = color

		def advance(self):
			self.frame += 1
			glow = 1

			t = 1.0 - (abs(self.frame - (self.lifetime / 2)) / (self.lifetime / 2.0))
			t = t * t

			self.sprite.color = tween_color(Color(0, 0, 0), self.color, t)

			if self.frame >= self.lifetime:
				self.tile.sprite_override = None
				self.finished = True


	def __init__(self, level):
		self.level = level
		self.star_freq = .00125   # each frame's chance of idle chasms showing glimmering star
		self.stars = {}

		self.star_lifetime = 400
		self.star_lifetime_var = 200

		self.colors = [
			Color(100, 180, 255),
			Color(100, 100, 155),
			Color(50,  150, 255),
			Color(100, 255, 255),
			Color(100, 120, 250)
		]

		self.has_advanced = False


	def advance(self):
		if not self.has_advanced:
			self.has_advanced = True
			for i in range(120):
				self.advance()

		for tile in self.level.iter_tiles():
			
			if tile in self.stars and not tile.is_chasm:
				del(self.stars[tile])

			if tile in self.stars and tile.is_chasm:

				self.stars[tile].advance()
				if self.stars[tile].finished:
					del(self.stars[tile])

			if tile not in self.stars and tile.is_chasm:
				if random.random() < self.star_freq:
					self.stars[tile] = self.Star(tile, random.choice(self.colors), random.randint(self.star_lifetime, self.star_lifetime + self.star_lifetime_var))

class Level(object):
	def __init__(self, w, h):
		self.width = w
		self.height = h

		self.size = self.width
		
		self.tiles = [[Tile(char='A', color=Color(50, 128, 50), x=j, y=i, level=self) for i in range(h)] for j in range(w)]
		self.effects = []
		self.units = []
		self.props = []
		self.active_spells = []
		self.clouds = []

		self.cur_obj = None
		self.turns = self.iter_frame()

		self.cur_portal = None

		self.is_awaiting_input = False
		self.requested_action = None

		self.player_unit = None
		self.event_manager = EventHandler()

		self.cur_shop = None
		self.cur_chatter = None
		self.gen_params = None

		self.chasm_anims = StarrySkyChasms(self)
		self.tcod_map = None

		self.frame_start_time = time.time()

		self.level_id = random.randint(0, 100000)

		self.spell_counts = defaultdict(lambda: 0)
		self.item_counts = defaultdict(lambda: 0)

		self.damage_taken_sources = defaultdict(lambda: 0)
		self.damage_dealt_sources = defaultdict(lambda: 0)

		self.turn_no = 0

		self.fov = libtcod.FOV_PERMISSIVE(8)
		self.turn_log_handler = None

		self.combat_log = logging.getLogger("damage")
		self.combat_log.setLevel(logging.DEBUG)
		self.combat_log.propagate = False

		self.logdir = None
		self.level_no = 0

		self.turn_summary = TurnSummary()
		self.brush_tileset = None

	def __getstate__(self):
		state = self.__dict__.copy()
		state["effects"] = []
		state["active_spells"] = []
		state["turns"] = None
		state["tcod_map"] = None
		state["combat_log"] = None
		state["turn_log_handler"] = None
		return state

	def setup_logging(self, logdir, level_num):

		self.combat_log = logging.getLogger("damage")
		self.combat_log.setLevel(logging.DEBUG)
		self.combat_log.propagate = False

		self.logdir = logdir
		self.level_no = level_num
		# Clear handlers if they exist
		for h in list(self.combat_log.handlers):
			self.combat_log.removeHandler(h)

		self.combat_log.addHandler(logging.FileHandler(os.path.join(self.logdir if self.logdir else '.', 'combat_log.txt'), mode='a'))
		#print(self.turn_no)
		#if self.turn_no:
		#	self.next_log_turn()


	def next_log_turn(self):
		if self.turn_log_handler:
			self.combat_log.removeHandler(self.turn_log_handler)

		# Do not make split logs for levels that do not have a log dir- ie, unit tests
		if self.logdir and self.logdir != ".":

			turn_file = os.path.join(self.logdir, str(self.level_no), 'combat_log.%d.txt' % self.turn_no)
			dirname = os.path.dirname(turn_file)
			if not os.path.exists(dirname):
				os.makedirs(dirname)

			self.turn_log_handler = logging.FileHandler(turn_file)
			self.combat_log.addHandler(self.turn_log_handler)

	def calc_glyphs(self):
		for t in self.iter_tiles():
			t.calc_glyph(cascade=False)

	def can_move(self, unit, x, y, teleport=False, force_swap=False):
		if not teleport and distance(Point(unit.x, unit.y), Point(x, y), diag=True) > 1.5:
			return False

		if not self.is_point_in_bounds(Point(x, y)):
			return False

		if not self.can_stand(x, y, unit, check_unit=False):
			return False

		# Big units can only move to completely clear tiles- they have no chance of swapping units
		if unit.radius:
			if not self.can_stand(x, y, unit, check_unit=True):
				return False

		# Blockers can be swapped unless they are large or stationary or cannot stand on the tile they are being swapped to
		blocker = self.tiles[x][y].unit
		
		# Big units should not block themselves of course
		if blocker == unit:
			blocker = None

		if blocker is not None:

			# big units cannot swap or be swapped
			if unit.radius > 0 or blocker.radius > 0:
				return False

			# Do not non flying units onto chasms
			if not self.can_stand(unit.x, unit.y, blocker, check_unit=False):
				return False

			# Do not force walkers onto chasms
			if not blocker.flying and not self.tiles[x][y].can_walk:
				return False

			# Check additional conditions if the swap is not forced, aka is from a move command not a spell:
			if not force_swap:

				# Only coward units and players can do non forced swap movement
				if not unit.is_coward and not unit.is_player_controlled:
					return False

				# Enemies can only swap via spells
				if are_hostile(unit, blocker):
					return False

				# Nothing can swap the player except magic
				if blocker.is_player_controlled:
					return False

				# Nothing can swap stationary units except magic
				if blocker.stationary:
					return False

		return True

	def set_order_move(self, x, y):
		self.requested_action = MoveAction(x, y)
		self.is_awaiting_input = False
		self.cur_chatter = None

	def set_order_cast(self, spell, x, y):
		self.requested_action = CastAction(spell, x, y)
		self.is_awaiting_input = False
		self.cur_chatter = None

	def set_order_pass(self):
		self.requested_action = PassAction()
		self.is_awaiting_input = False
		self.cur_chatter = None

	def act_move(self, unit, x, y, teleport=False, leap=False, force_swap=False):
		# Do nothing if something tries to move a dead unit- a spell or buff for instance
		if not unit.is_alive():
			return

		assert(isinstance(unit, Unit))
		
		if not leap:
			assert(self.can_move(unit, x, y, teleport=teleport, force_swap=force_swap))

		assert(unit.is_alive())

		if unit.is_player_controlled:
			prop = self.tiles[unit.x][unit.y].prop
			if prop:
				prop.on_player_exit(unit)

		# flip sprite if needed
		if x < unit.x:
			unit.sprite.face_left = True
		if x > unit.x:
			unit.sprite.face_left = False

		# allow swaps
		swapper = self.tiles[x][y].unit
		if swapper == unit:
			swapper = None

		oldx = unit.x
		oldy = unit.y

		# Clear previously occupied tiles
		for i in range(-unit.radius, unit.radius+1):
			for j in range(-unit.radius, unit.radius+1):
				self.tiles[unit.x+i][unit.y+j].unit = None

		unit.x = x
		unit.y = y

		# Poit occupied tiles to unit
		for i in range(-unit.radius, unit.radius+1):
			for j in range(-unit.radius, unit.radius+1):
				self.tiles[x+i][y+j].unit = unit

		# Execute burrow
		if unit.burrowing:
			for occ in unit.iter_occupied_points():
				if self.tiles[occ.x][occ.y].is_wall():
					self.make_floor(occ.x, occ.y)
					self.show_effect(occ.x, occ.y, Tags.Physical)

		# allow swaps
		if swapper:
			self.tiles[oldx][oldy].unit = swapper
			swapper.x = oldx
			swapper.y = oldy
			self.event_manager.raise_event(EventOnMoved(unit, oldx, oldy, teleport=False), swapper)			

			# Fix perma circle on swap
			if swapper.is_player_controlled:
				prop = self.tiles[swapper.x][swapper.y].prop
				if prop:
					prop.on_player_exit(swapper)


		self.event_manager.raise_event(EventOnMoved(unit, x, y, teleport=teleport), unit)

		
		prop = self.tiles[x][y].prop
		if prop:
			if unit.is_player_controlled:
				prop.on_player_enter(unit)
			prop.on_unit_enter(unit)

		cloud = self.tiles[x][y].cloud
		if cloud:
			cloud.on_unit_enter(unit)
		
	def act_cast(self, unit, spell, x, y, pay_costs=True, queue=True):		
		assert(isinstance(unit, Unit)), "caster is not of type unit, is %s" % type(unit)

		if unit.is_player_controlled:
			if spell.item:
				self.item_counts[spell.name] += 1
			else:
				self.spell_counts[spell.name] += 1

		self.combat_log.debug("%s uses %s" % (unit.name, spell.name))

		# flip sprite if needed
		if x < unit.x:
			unit.sprite.face_left = True
		if x > unit.x:
			unit.sprite.face_left = False

		if pay_costs:
			assert(spell.can_cast(x, y)), "%s trying to cast spell %s on untargetable tile %d, %d" % (unit.name, spell.name, x, y)
			assert(spell.can_pay_costs()), "%s trying to cast spell %s, but cannot pay costs" % (unit.name, spell.name)

		if pay_costs:
			spell.pay_costs()
		
		
		# If we want to queue the spell, queue it.  Else return the generator so the calling spell can iterate over it.
		if queue:
			self.queue_spell(spell.cast(x, y))
			rval = None
		else:
			rval = spell.cast(x, y)

		self.event_manager.raise_event(EventOnSpellCast(spell, unit, x, y), unit)

		return rval

	def act_shop(self, unit, item):

		if item is None:
			self.cur_shop = None
			return

		assert(isinstance(unit, Unit))
		assert(self.cur_shop)

		self.cur_shop.buy(unit, item)

	def can_stand(self, x, y, unit, check_unit=True):
		assert(isinstance(unit, Unit))

		# Use a weird loop format to avoid heap allocating range objects since can_stand is called *constantly*
		i = -unit.radius

		chasms = 0

		while i <= unit.radius:
			j = -unit.radius
			while j <= unit.radius:

				cur_x = x + i
				cur_y = y + j

				if not self.is_coord_in_bounds(cur_x, cur_y):
					return False

				if check_unit and self.get_unit_at(cur_x, cur_y) not in [None, unit]:
					return False

				# Only flyers can go over chasms
				tile = self.tiles[cur_x][cur_y]
				if tile.is_chasm and not unit.flying:
					chasms += 1

				# Only burrowers can go through walls
				if tile.is_wall() and not unit.burrowing:
					if not self.tiles[cur_x][cur_y].can_fly:
						return False

				j += 1
			i += 1

		total_sq_occupied = (1 + 2*unit.radius) * (1 + 2*unit.radius) 
		if not unit.flying and chasms > total_sq_occupied / 2.0:
			return False

		return True

	def can_walk(self, x, y, check_unit=False):

		if not self.is_point_in_bounds(Point(x, y)):
			return False

		if check_unit:
			if self.get_unit_at(x, y) is not None:
				return False

		return self.tiles[x][y].can_walk

	def find_path(self, start, target, pather, pythonize=False, cosmetic=False, unit_penalty=4):
		
		# Early out if the pather is surrounded by units and walls
		# If the unit cannot move, we dont care how it should move
		# Do not do this for cosmetic paths- they can step over units, and are infrequently called anyways
		if not cosmetic and unit_penalty != 0:
			boxed_in = True
			for p in self.get_adjacent_points(start, filter_walkable=False):
				if self.can_stand(p.x, p.y, pather):
					boxed_in = False
					break

			if boxed_in:
				return None

		def path_func(xFrom, yFrom, xTo, yTo, userData):
			# If the previous point is basically 'arrived', we dont need to check further points.
			if pather.radius:
				if distance(Point(xFrom, yFrom), target, diag=True) <= pather.radius + 1:
					return 0.5

			if not self.can_stand(xTo, yTo, pather, check_unit=False):
				return False

			# By default, all traversable tiles have cost 1.
			# But various things can penalize this- units in the way, props on the ground
			cost = 1.0


			for i in range(-pather.radius, pather.radius+1):
				for j in range(-pather.radius, pather.radius+1):

					tile = self.tiles[xTo+i][yTo+j]
					blocker_unit = tile.unit if tile.unit != pather else None
			
					if blocker_unit:
						if blocker_unit.stationary:
							cost += 12.5 * unit_penalty
						else:
							cost += unit_penalty
					if not blocker_unit:
						if tile.prop:
							# player pathing avoids props unless prop is the target
							if (isinstance(tile.prop, Portal) or isinstance(tile.prop, Shop)) and pythonize and not (xTo == target.x and yTo == target.y):
								return False
							# creatuers slight preference to avoid props
							cost += 0.1
			return cost

		path = libtcod.path_new_using_function(self.width, self.height, path_func)
		libtcod.path_compute(path, start.x, start.y, target.x, target.y)
		if pythonize:
			ppath = []
			for i in range(libtcod.path_size(path)):
				x, y = libtcod.path_get(path, i)
				ppath.append(Point(x, y))
			libtcod.path_delete(path)
			return ppath
		return path

	def advance(self, full_turn=False):
		#self.advance_effects()
		self.frame_start_time = time.time()
		self.frame_units_moved = 0
		if not self.turns:
			self.turns = self.iter_frame()
		
		if not full_turn:
			next(self.turns)
		else:
			i = 0
			while not next(self.turns):
				# Limit to 5000 iterations
				i += 1
				assert(i < 5000)

	def advance_effects(self, advance=True):
		if self.effects:
			if advance:
				for effect in self.effects:
					effect.advance()

			# Cull expired effects
			self.effects = [fx for fx in self.effects if fx.frames_left > 0]
			advanced_effects = True

		#for tile in self.iter_tiles():
		#	tile.advance_cosmetic()
		if self.chasm_anims:
			self.chasm_anims.advance()

	def advance_spells(self):
		if not self.active_spells:
			return

		# gather all spells at beginning of queue with same code
		to_advance = []
		for s in self.active_spells:
			if s.gi_code == self.active_spells[0].gi_code:
				to_advance.append(s)

		for s in to_advance:
			stopped = next(s, "Stopped")
			if stopped == "Stopped":
				self.active_spells.remove(s)

	def can_advance_spells(self):
		return len(self.active_spells) > 0

	def get_next_unit(self):
		return 

	def iter_frame(self, mark_turn_end=False):

		while self.can_advance_spells():
			yield self.advance_spells()

		# An iterator representing the order of turns for all game objects
		while True:

			# Yield once per iteration if there are no units to prevent infinite loop
			if not self.units:
				yield

			self.turn_no += 1

			if any(u.team != TEAM_PLAYER for u in self.units):
				self.next_log_turn()
				self.combat_log.debug("Level %d, Turn %d begins." % (self.level_no, self.turn_no))

			# Cache unit list here to enforce summoning delay
			turn_units = list(self.units)
			for is_player_turn in [True, False]:
				clouds = [cloud for cloud in self.clouds if cloud.owner.is_player_controlled == is_player_turn]
				if clouds:
					for cloud in clouds:
						if cloud.is_alive:
							cloud.advance()
					while self.can_advance_spells():
						yield self.advance_spells()

				units = [unit for unit in turn_units if unit.is_player_controlled == is_player_turn]
				random.shuffle(units)

				for unit in units:
					if not unit.is_alive():
						continue

					unit.pre_advance()

					finished_advance = False
					while not finished_advance:
						if unit.is_player_controlled and not unit.is_stunned() and not self.requested_action:
							self.is_awaiting_input = True
							yield
						
						# Yield for 1 frame if stunned to prevent jarring time skip
						if unit.is_player_controlled and unit.is_stunned():
							yield

						# Clear turn summary as soon as player chooses an action, before it is executed
						# But group all things happening during stuns together
						if unit.is_player_controlled and not unit.is_stunned():
							self.turn_summary.clear()

						finished_advance = unit.advance()

						#yield
						while self.can_advance_spells():
							yield self.advance_spells()

					# Advance buffs after advancing spells
					unit.advance_buffs()

					while self.can_advance_spells():
						yield self.advance_spells()

					self.frame_units_moved += 1
					
					# Yield if the current advance frame is aboive the advance time budget
					if time.time() - self.frame_start_time > MAX_ADVANCE_TIME:
						yield

			# Advance all props similtaneously
			for prop in list(self.props):
				prop.advance()

			# In the unlikely event that that created effects, advance them
			while self.can_advance_spells():
				yield self.advance_spells()

			if not visual_mode:
				yield True


	def get_unit_at(self, x, y):
		if not self.is_point_in_bounds(Point(x, y)):
			return None
		return self.tiles[x][y].unit

	def get_connected_group_from_point(self, x, y, avoid_tags=[], required_tags=[], ignored_units=[], check_hostile=False, num_targets=-1):
		#Avoid Tags: If a unit has these tags, it will be ignored.
		#Required Tags: If a unit does not have these tags, it will be ignored.
		#Ignored Units: Add units you want to be ignored, e.g. the player.
		#Check Hostile: Determines whether or not to check if units are player-controlled.
		candidates = set([Point(x, y)])
		unit_group = set()

		while candidates:
			candidate = candidates.pop()
			unit = self.get_unit_at(candidate.x, candidate.y)
			if unit and unit not in unit_group:

				skip = False

				if unit in ignored_units:
					continue

				for tag in required_tags:
					if not tag in unit.tags:
						skip = True

				for tag in avoid_tags:
					if tag in unit.tags:
						skip = True

				if skip:
					continue

				if check_hostile and unit.is_player_controlled:
					continue

				if num_targets > -1 and len(unit_group) >= num_targets:
					break

				unit_group.add(unit)

				for p in self.get_adjacent_points(Point(unit.x, unit.y), filter_walkable=False):
					candidates.add(p)

		return list(unit_group)

	def get_summon_point(self, x, y, radius_limit=5, sort_dist=True, flying=False, diag=False):
		options = list(self.get_points_in_ball(x, y, radius_limit, diag=diag))
		random.shuffle(options)

		if sort_dist:
			options.sort(key=lambda p: distance(p, Point(x, y)))

		for o in options:
			tile = self.tiles[o.x][o.y]
			if not flying:
				if not tile.can_walk:
					continue
			else:
				if not tile.can_fly:
					continue
			if self.get_unit_at(o.x, o.y):
				continue
			return o

		return None

	def get_drop_point(self, x, y, radius_limit=5):
		options = list(self.get_points_in_ball(x, y, radius_limit))
		random.shuffle(options)
		options.sort(key=lambda p: distance(p, Point(x, y)))
		for o in options:
			if self.can_walk(o.x, o.y) and self.tiles[o.x][o.y].prop is None:
				return o
		return None

	def iter_tiles(self):
		for i in range(len(self.tiles)):
			for j in range(len(self.tiles[i])):
				yield self.tiles[i][j]

	def is_point_in_bounds(self, point):
		return point.x >= 0 and point.x < self.width and point.y >= 0 and point.y < self.height

	def is_coord_in_bounds(self, x, y):
		return x >= 0 and x < self.width and y >= 0 and y < self.height


	def get_points_in_rect(self, xmin, ymin, xmax, ymax):
		xmin = max(xmin,0)
		xmax = min(xmax+1,self.width)
		ymin = max(ymin,0)
		ymax = min(ymax+1,self.height)
		
		for x in range(xmin, xmax):
			for y in range(ymin, ymax):
				yield Point(x, y)

	def get_adjacent_points(self, point, filter_walkable=True, check_unit=False):
		adjacent = (p for p in self.get_points_in_rect(point.x - 1, point.y - 1, point.x + 1, point.y + 1) if p != point)
		if filter_walkable:
			return (p for p in adjacent if self.can_walk(p.x, p.y, check_unit=check_unit))
		else:
			return adjacent

	def get_tiles_in_ball(self, x, y, radius):
		return [self.tiles[p.x][p.y] for p in self.get_points_in_ball(x, y, radius)]

	def get_points_in_ball(self, x, y, radius, diag=False):
		rounded_radius = int(math.ceil(radius))
		for (cur_x, cur_y) in self.get_points_in_rect(x - rounded_radius, y - rounded_radius, x + rounded_radius, y + rounded_radius):
			if distance(Point(cur_x, cur_y), Point(x, y), diag=diag) <= radius:
				yield Point(cur_x, cur_y)

	def adjust_beam(self, points):

		for i in range(1, len(points)-1):
			pre = points[i-1]
			cur = points[i]
			nex = points[i+1]

			# Do not adjust points along straight line segments
			if pre.x == nex.x or pre.y == nex.y:
				continue

			# Do not adjust points outside of the map.
			if not self.is_point_in_bounds(cur):
				continue

			# No blocker?  ok cool
			#if self.tiles[cur.x][cur.y].can_see:
			#	continue
			if self.can_see(points[0].x, points[0].y, cur.x, cur.y):
				continue

			opts = self.get_points_in_rect(cur.x-1, cur.y-1, cur.x+1, cur.y+1)
			better_opt = None
			for opt in opts:
				if opt == cur:
					continue
				if not self.tiles[opt.x][opt.y].can_see:
					continue
				if distance(opt, nex) <= 1.5 and distance(opt, pre) <= 1.5:
					better_opt = opt
					break
			if better_opt:
				points[i] = better_opt

	# Returns all points on the line going through dest perpendicular to origin
	def get_perpendicular_line(self, origin, dest, length=99):

		results = set([dest])
		
		if origin == dest:
			return results

		# reverse the slope
		dy = dest.x - origin.x
		dx = dest.y - origin.y

		longer_len = max(abs(dy), abs(dx))
		if longer_len:
			dx /= longer_len
			dy /= -longer_len
		# Default to a flat line if origin = dest
		else:
			dx = 1
			dy = 0

		line_start = Point(round(dest.x + length * dx), round(dest.y + length * dy))
		line_end = Point(round(dest.x - length * dx), round(dest.y - length * dy))
		return [p for p in self.get_points_in_line(line_start, line_end, two_pass=False) if self.is_point_in_bounds(p)]
		
	def show_beam(self, start, end, dtype, minor=True, inclusive=False):

		points = self.get_points_in_line(start, end)
		if not inclusive:
			points = points[1:-1]

		for p in points:
			self.show_effect(p.x, p.y, dtype, minor=minor)

	def get_points_in_line(self, start, end, two_pass=True, find_clear=False, no_diag=False):
		steep = abs(end.y - start.y) > abs(end.x - start.x);

		# Orient the line so that it is going left to right with slope between 1 and -1
		if steep:
			start = Point(start.y, start.x)
			end = Point(end.y, end.x)

		reverse = False
		if start.x > end.x:
			reverse = True

			swap_temp = end
			end = start
			start = swap_temp

		dx = end.x - start.x
		dy = abs(end.y - start.y)
		
		if not find_clear:
			starting_err_vals = [dx / 2.0]
		else:
			starting_err_vals = list(range(dx+1))
			starting_err_vals = sorted(starting_err_vals, key=lambda v: abs(v - (dx / 2.0)))

		for starting_err_val in starting_err_vals:
			err = starting_err_val

			ystep = 1 if start.y < end.y else -1
			y = start.y

			result = []
			if isinstance(start.x, float) or isinstance(end.x, float):
				assert(False)

			clear = True
			for x in range(start.x, end.x + 1):
				if not steep:
					next_point = Point(x, y)
				else:
					next_point = Point(y, x)

				result.append(next_point)


				err = err - dy
				if (not reverse and err < 0) or (reverse and err <= 0):
					y += ystep
					err += dx

			if find_clear and not clear:
				continue

			if two_pass:
				for i in range(2):
					self.adjust_beam(result)

			if find_clear:
				valid = True
				for p in result:
					if not self.is_point_in_bounds(p):
						valid = False
					elif not self.tiles[p.x][p.y].can_see:
						valid = False
				if not valid:
					continue

			if reverse:
				result.reverse()

			if no_diag:
				insertions = []
				for i in range(len(result)-1):
					p = result[i]
					q = result[i+1]
					if p.x != q.x and p.y != q.y:
						if random.random() > .5:
							insertions.append((Point(p.x, q.y), i))
						else:
							insertions.append((Point(q.x, p.y), i))

				insert_num = 0
				for new_point, index in insertions:
					result.insert(insert_num + index, new_point)
					insert_num += 1

			return result

		# If we are looking for a clear path but none are clear return the default
		assert(find_clear)
		return []
		#return self.get_points_in_line(start, end, find_clear=False)

	def set_default_resitances(self, unit):

		if Tags.Demon in unit.tags:
			unit.resists.setdefault(Tags.Holy, -100)
			unit.resists.setdefault(Tags.Dark, 100)

		if Tags.Metallic in unit.tags:
			unit.resists.setdefault(Tags.Fire, 50)
			unit.resists.setdefault(Tags.Physical, 50)
			unit.resists.setdefault(Tags.Ice, 75)
			unit.resists.setdefault(Tags.Lightning, 100)

		if Tags.Undead in unit.tags:
			unit.resists.setdefault(Tags.Holy, -100)
			unit.resists.setdefault(Tags.Dark, 100)
			unit.resists.setdefault(Tags.Ice, 50)

		if Tags.Glass in unit.tags:
			unit.resists.setdefault(Tags.Fire, 50)
			unit.resists.setdefault(Tags.Physical, -100)
			unit.resists.setdefault(Tags.Lightning, 100)
			unit.resists.setdefault(Tags.Ice, 100)

		# Poison only works on living, nature, or demons.  Not so hot vs arcane, constructs, ect.
		if Tags.Living in unit.tags:
			unit.resists.setdefault(Tags.Poison, 0)
		if Tags.Nature in unit.tags:
			unit.resists.setdefault(Tags.Poison, 0)
		elif Tags.Demon in unit.tags:
			unit.resists.setdefault(Tags.Poison, 0)
		else:
			unit.resists.setdefault(Tags.Poison, 100)

		# Creatures with radius should also uh 'resist' stuns
		if unit.radius:
			unit.gets_clarity = True

	def can_add_cloud(self, p):
		t = self.tiles[p.x][p.y]
		if t.cloud:
			return False
		if not (t.can_walk or t.can_fly):
			return False
		return True

	def add_obj(self, obj, x, y):
		obj.x = x
		obj.y = y
		obj.level = self

		if not hasattr(obj, 'level_id'):
			obj.level_id = self.level_id

		if isinstance(obj, Unit):
			self.event_manager.raise_event(EventOnUnitPreAdded(obj), obj)

			if obj.max_hp <= 1:
				obj.max_hp = 1

			if not obj.cur_hp:
				obj.cur_hp = obj.max_hp
				assert(obj.cur_hp > 0)
				
			
			for i in range(-obj.radius, obj.radius+1):
				for j in range(-obj.radius, obj.radius+1):
					cur_x = x + i
					cur_y = y + j

					if not self.tiles[cur_x][cur_y].unit is None:
						print("Cannot add %s at %s, already has %s" % (obj.name, str((x, y)), self.tiles[cur_x][cur_y].unit.name))
						assert(self.tiles[cur_x][cur_y].unit is None)

					self.tiles[cur_x][cur_y].unit = obj

			# Hack- allow improper adding in monsters.py
			for spell in obj.spells:
				spell.caster = obj
				spell.owner = obj

			self.set_default_resitances(obj)

			for buff in list(obj.buffs):
				# Apply unapplied buffs- these can come from Content on new units
				could_apply = buff.apply(obj) != ABORT_BUFF_APPLY

				# Remove buffs which cannot be applied (happens with stun + clarity potentially)
				if not could_apply:
					obj.buffs.remove(obj)

				# Monster buffs are all passives
				if not obj.is_player_controlled:
					buff.buff_type = BUFF_TYPE_PASSIVE

			self.units.append(obj)
			self.event_manager.raise_event(EventOnUnitAdded(obj), obj)

			obj.ever_spawned = True

		elif isinstance(obj, Cloud):

			# kill any existing clouds
			cur_cloud = self.tiles[x][y].cloud 
			if cur_cloud is not None:

				if cur_cloud.can_be_replaced_by(obj):
					cur_cloud.kill()
				else:
					return

			self.tiles[x][y].cloud = obj
			self.clouds.append(obj)

		elif isinstance(obj, Prop):
			self.add_prop(obj, x, y)

		else:
			assert(False) # Unknown obj type

	def remove_obj(self, obj):
		if isinstance(obj, Unit):

			# Unapply to unsubscribe
			for buff in obj.buffs:
				buff.unapply()

			radius = obj.radius if hasattr(obj, 'radius') else 0
			
			for i in range(-radius, radius+1):
				for j in range(-radius, radius+1):
					cur_x = obj.x + i
					cur_y = obj.y + j
					
					assert(self.tiles[cur_x][cur_y].unit == obj)
					self.tiles[cur_x][cur_y].unit = None

			assert(obj in self.units)
			self.units.remove(obj)

		if isinstance(obj, Cloud):
			assert(self.tiles[obj.x][obj.y].cloud == obj)
			self.tiles[obj.x][obj.y].cloud = None
			self.clouds.remove(obj)

		if isinstance(obj, Prop):
			self.remove_prop(obj)

		obj.removed = True

	def add_prop(self, prop, x, y):
		prop.x = x
		prop.y = y
		prop.level = self
		self.tiles[x][y].prop = prop
		self.props.append(prop)

	def remove_prop(self, prop):
		self.props.remove(prop)
		self.tiles[prop.x][prop.y].prop = None 

	def spawn_player(self, player_unit):
		self.player_unit = player_unit
		self.add_obj(player_unit, self.start_pos.x, self.start_pos.y)

		prop = self.tiles[self.start_pos.x][self.start_pos.y].prop
		if prop:
			prop.on_player_enter(player_unit)

	def summon(self, owner, unit, target=None, radius=3, team=None, sort_dist=True):
		if not target:
			target = owner
			
		p = self.get_summon_point(target.x, target.y, radius_limit=radius, flying=unit.flying, sort_dist=sort_dist)
		if not team:
			team = owner.team
		unit.team = team

		if p:
			self.add_obj(unit, p.x, p.y)
			self.show_effect(p.x, p.y, Tags.Conjuration)
			return unit
		else:
			return False

	def deal_damage(self, x, y, amount, damage_type, source, flash=True):

		# Auto make effects if none were already made
		if flash:
			effect = Effect(x, y, damage_type.color, Color(0, 0, 0), 12)
			if amount == 0:
				effect.minor = True
			self.effects.append(effect)

		cloud = self.tiles[x][y].cloud
		if cloud and amount > 0:
			cloud.on_damage(damage_type)

		unit = self.get_unit_at(x, y)
		if not unit:
			return 0
		if not unit.is_alive():
			return 0


		# Raise pre damage event (for conversions)
		pre_damage_event = EventOnPreDamaged(unit, amount, damage_type, source)
		self.event_manager.raise_event(pre_damage_event, unit)

		# Factor in shields and resistances after raising the raw pre damage event
		resist_amount = unit.resists.get(damage_type, 0)

		# Cap effective resists at 100- shenanigans ensue if we do not
		resist_amount = min(resist_amount, 100)

		if resist_amount:
			multiplier = (100 - resist_amount) / 100.0
			amount = int(math.ceil(amount * multiplier))

		source_name = "%s's %s" % (source.owner.name, source.name) if source.owner else source.name

		if amount > 0 and unit.shields > 0:
			unit.shields = unit.shields - 1
			self.combat_log.debug("%s blocked %d %s damage from %s" % (unit.name, amount, damage_type.name, source_name))
			self.show_effect(unit.x, unit.y, Tags.Shield_Expire)				
			return 0

		# Cap damage to current hp, cap healing to missing hp
		if amount > 0:
			amount = min(amount, unit.cur_hp)
		elif amount < 0:
			amount = max(amount, unit.cur_hp - unit.max_hp)

		unit.cur_hp = unit.cur_hp - amount

		# Logging
		if amount > 0:
			self.combat_log.debug("%s took %d %s damage from %s" % (unit.name, amount, damage_type.name, source_name))
		elif amount < 0:
			self.combat_log.debug("%s healed %d from %s" % (unit.name, -amount, source_name))

		# Processing
		if amount < 0:
			evt = EventOnHealed(unit, amount, source)
			self.event_manager.raise_event(evt, unit)

		elif amount > 0:
			# Record damage sources when a player unit exists (aka not in unittests)
			if self.player_unit:
				# Enemy
				if are_hostile(unit, self.player_unit):
					key = source.name
					if source.owner and source.owner.source and not (isinstance(source, Buff) and source.buff_type == BUFF_TYPE_CURSE):
						key = source.owner.name

					self.damage_dealt_sources[key] += amount
					self.turn_summary.damage_dealt[key] += amount
				# Ally/Self
				else:
					if isinstance(source, Buff) and source.buff_type == BUFF_TYPE_CURSE:
						key = source.name
					elif source.owner:
						key = source.owner.name
					else:
						key = source.name	
					
					# Self
					if unit == self.player_unit:
						self.damage_taken_sources[key] += amount
						self.turn_summary.self_damage_taken[key] += amount
					# Ally
					else:
						self.turn_summary.ally_damage_taken[key] += amount
	

			damage_event = EventOnDamaged(unit, amount, damage_type, source)
			self.event_manager.raise_event(damage_event, unit)
		
			if (unit.cur_hp <= 0):
				unit.kill(damage_event = damage_event)			

				if (unit.cur_hp <= 0):
					unit.kill(damage_event = damage_event)			
				
			if (unit.cur_hp > unit.max_hp):
				unit.cur_hp = unit.max_hp
		# set amount to 0 if there is no unit- ie, if an empty tile or dead unit was hit
		else:
			amount = 0

		if (unit.cur_hp > unit.max_hp):
			unit.cur_hp = unit.max_hp

		return amount

	def flash(self, x, y, color):
		self.effects.append(Effect(x, y, color, Color(0, 0, 0), 12))

	def show_effect(self, x, y, effect_tag, fill_color=Color(0, 0, 0), minor=False, speed=1):
		effect = Effect(x, y, effect_tag.color, fill_color, 12)
		effect.minor = minor
		effect.speed = speed
		self.effects.append(effect)

	def show_path_effect(self, start, finish, effect_tag, fill_color=Color(0, 0, 0), minor=False, straight=False, inclusive=True):

		unit = Unit()
		unit.can_fly = True
		path = self.find_path(start, finish, unit, pythonize=True, cosmetic=True)
		if straight or not path:
			path = self.get_points_in_line(start, finish)

		if not inclusive:
			path = path[0:-1]

		i = 0
		for p in path:
			if isinstance(effect_tag, list):
				i += 1
				cur_tag = effect_tag[i % len(effect_tag)]
			else:
				cur_tag = effect_tag

			self.show_effect(p.x, p.y, cur_tag, fill_color, minor)


	def leap_effect(self, x, y, color, unit):
		effect = Effect(x, y, Tags.Leap.color, color, 12)
		effect.leap_unit = unit
		self.effects.append(effect)

	def projectile_effect(self, x, y, proj_name, proj_origin, proj_dest, proj_color=None):
		if not proj_color:
			proj_color = Color(0, 0, 0)
		effect = Effect(x, y, Tags.Arrow.color, proj_color, 7)
		effect.proj_name = proj_name
		effect.proj_origin = proj_origin
		effect.proj_dest = proj_dest
		self.effects.append(effect)

	def queue_spell(self, spell):
		assert(hasattr(spell, "__next__"))
		self.active_spells.append(spell)

	def are_hostile(self, unit1, unit2):
		return are_hostile(unit1, unit2)

	def get_units_in_ball(self, center, radius, diag=False):
		return [u for u in self.units if distance(Point(u.x, u.y), center, diag=diag) <= radius]

	def get_units_in_los(self, point):
		return [u for u in self.units if self.can_see(u.x, u.y, point.x, point.y)]

	def get_points_in_los(self, point):
		for i in range(0, len(self.tiles)):
			for j in range(0, len(self.tiles[i])):
				if self.can_see(point.x, point.y, i, j):
					yield Point(i, j)

	def all_enemies_dead(self):
		return len([u for u in self.units if self.are_hostile(self.player_unit, u)]) == 0

	def set_brush_tileset(self, tileset):
		self.brush_tileset = tileset

	def make_wall(self, x, y, calc_glyph=True):

		tile = self.tiles[x][y]
		tile.can_walk = False
		tile.can_see = False
		tile.can_fly = False
		tile.is_chasm = False
		tile.name = "Wall"
		tile.description = "Solid rock"
		
		if self.brush_tileset:
			tile.tileset = self.brush_tileset

		if calc_glyph:
			tile.calc_glyph()

		self.clear_tile_sprite(tile)

		if self.tcod_map:
			libtcod.map_set_properties(self.tcod_map, tile.x, tile.y, tile.can_see, tile.can_walk)

	def make_floor(self, x, y, calc_glyph=True):

		tile = self.tiles[x][y]
		tile.can_walk = True
		tile.can_see = True
		tile.can_fly = True
		tile.is_chasm = False
		tile.name = "Floor"
		tile.description = "A rough rocky floor"

		if self.brush_tileset:
			tile.tileset = self.brush_tileset

		if calc_glyph:
			tile.calc_glyph()

		self.clear_tile_sprite(tile)

		if self.tcod_map:
			libtcod.map_set_properties(self.tcod_map, tile.x, tile.y, tile.can_see, tile.can_walk)

	def make_chasm(self, x, y, calc_glyph=True):
		tile = self.tiles[x][y]
		tile.can_walk = False
		tile.can_see = True
		tile.can_fly = True
		tile.is_chasm = True
		tile.name = "The Abyss"
		tile.description = "Look closely and you might see the glimmer of distant worlds."

		if calc_glyph:
			tile.calc_glyph()

		self.clear_tile_sprite(tile)

		if self.tcod_map:
			libtcod.map_set_properties(self.tcod_map, tile.x, tile.y, tile.can_see, tile.can_walk)

	def clear_tile_sprite(self, tile):
		if not self.turn_no:
			return

		for p in self.get_points_in_rect(tile.x - 1, tile.y - 1, tile.x + 1, tile.y + 1):
			self.tiles[p.x][p.y].sprites = None


	def make_map(self):
		self.tcod_map = libtcod.map_new(len(self.tiles), len(self.tiles[0]))
		for tile in self.iter_tiles():
			libtcod.map_set_properties(self.tcod_map, tile.x, tile.y, tile.can_see, tile.can_walk)

	def can_see(self, x1, y1, x2, y2, light_walls=False):
		if not hasattr(self, 'tcod_map') or not self.tcod_map:
			self.make_map()

		if not light_walls and (not self.tiles[x1][y1].can_see or not self.tiles[x2][y2].can_see):
			return False

		libtcod.map_compute_fov(self.tcod_map, x1, y1, radius=40, light_walls=False, algo=self.fov)
		first = libtcod.map_is_in_fov(self.tcod_map, x2, y2)

		if first:
			return True

		# Force symmetry permissively
		else:
			libtcod.map_compute_fov(self.tcod_map, x2, y2, radius=40, light_walls=False, algo=self.fov)
			return libtcod.map_is_in_fov(self.tcod_map, x1, y1)

	def set_tileset(self, tileset):
		for tile in self.iter_tiles():
			tile.tileset = tileset

	def get_random_sublevel(self, randomizer):
		xsize = randomizer.randint(10, 20)
		ysize = randomizer.randint(10, 20)
		xstart = randomizer.randint(0, self.size - xsize - 1)
		ystart = randomizer.randint(0, self.size - ysize - 1)
		return SubLevel(self, xstart, ystart, xsize, ysize, randomizer)

	def get_random_lump(self, size, randomizer):
		start = Point(randomizer.randint(0, self.size - 1), randomizer.randint(0, self.size - 1))
		candidates = [start]
		chosen = set()
		for j in range(size):
			cur_point = randomizer.choice(candidates)
			candidates.remove(cur_point)

			chosen.add(cur_point)

			for point in self.get_points_in_ball(cur_point.x, cur_point.y, 1):
				if point not in candidates and point not in chosen:
					candidates.append(point)

		return list(chosen)

# A class used by Vaults in order to treat a subsection of the level as a whole level for mutators
class SubLevel():

	def __init__(self, level, xstart, ystart, xsize, ysize, randomizer):
		self.master_level = level
		self.level = self # hack for levelgen helpers
		self.xstart = xstart
		self.ystart = ystart
		self.width = xsize
		self.height = ysize

		self.random = randomizer

	def get_spawn_points(self):
		# Find points to put stuff
		floor_spawn_points = []
		wall_spawn_points = []
		for i in range(self.width):
			for j in range(self.height):
				
				cur_point = self.translate_coords(i, j)
				if not cur_point:
					continue

				if self.master_level.get_unit_at(cur_point[0], cur_point[1]):
					continue

				if self.master_level.can_walk(cur_point[0], cur_point[1]):
					floor_spawn_points.append(cur_point)

				else:
					if len([p for p in self.master_level.get_adjacent_points(cur_point)]) > 1:
						wall_spawn_points.append(cur_point)

		self.random.shuffle(floor_spawn_points)
		self.random.shuffle(wall_spawn_points)

		return floor_spawn_points, wall_spawn_points

	def translate_coords(self, x, y):
		if x >= self.width:
			return None
		if y >= self.height:
			return None

		new_coords = Point(x + self.xstart, y + self.ystart)
		return new_coords

	def iter_tiles(self):
		for i in range(0, self.width):
			for j in range(0, self.height):
				coords = self.translate_coords(i, j)
				if coords is not None:
					yield self.master_level.tiles[coords[0]][coords[1]]

	def set_tileset(self, tileset):
		for tile in self.iter_tiles():
			tile.tileset = tileset

	def fill_walls(self):
		for i in range(0, self.width):
			for j in range(0, self.height):
				self.make_wall(i, j)

	def fill_chasms(self):
		for i in range(0, self.width):
			for j in range(0, self.height):
				self.make_chasm(i + self.xstart, j + self.ystart)

	def fill_floors(self):
		for i in range(0, self.width):
			for j in range(0, self.height):
				self.make_floor(i + self.xstart, j + self.ystart)

	def make_floor(self, x, y):
		translated_coords = self.translate_coords(x, y)
		if translated_coords is None:
			return

		self.master_level.make_floor(translated_coords[0], translated_coords[1])

	def make_chasm(self, x, y):
		translated_coords = self.translate_coords(x, y)
		if translated_coords is None:
			return

		self.master_level.make_chasm(translated_coords[0], translated_coords[1])

	def make_wall(self, x, y):
		translated_coords = self.translate_coords(x, y)
		if translated_coords is None:
			return

		self.master_level.make_wall(translated_coords[0], translated_coords[1])

	def add_obj(self, obj, x, y):
		translated_coords = self.translate_coords(x, y)
		if translated_coords is None:
			return

		self.master_level.add_obj(obj, translated_coords[0], translated_coords[1])


class TurnSummary():

	def __init__(self):
		self.ally_kill_counts = defaultdict(lambda: 0)
		self.enemy_kill_counts = defaultdict(lambda: 0)
		self.ally_damage_taken = defaultdict(lambda: 0)
		self.damage_dealt = defaultdict(lambda: 0)
		self.self_damage_taken = defaultdict(lambda: 0)

	def clear(self):
		self.ally_kill_counts.clear()
		self.enemy_kill_counts.clear()
		self.ally_damage_taken.clear()
		self.damage_dealt.clear()
		self.self_damage_taken.clear()

class NameLookupCollection():
	def __init__(self, elements):
		self.elements = elements

	def __getattr__(self, attr_name):
		candidates = [t for t in self.elements if t.name == attr_name]
		assert(len(candidates) == 1)
		return candidates[0]

	def __iter__(self):
		return self.elements.__iter__()

Tag = namedtuple("Tag", "name color asset", defaults=(None,))

class Tag():
	def __init__(self, name, color, asset=None):
		self.name = name
		self.color = color
		self.asset = asset

	def __hash__(self):
		return hash((self.name, self.color))

	def __eq__(self, other):
		if not isinstance(other, Tag):
			return False
		return self.color == other.color

Tags = NameLookupCollection([
	Tag("Physical", Color(230, 210, 210)),
	Tag("Fire", Color(229, 28, 35)),
	Tag("Lightning", Color(255, 238, 88)),
	Tag("Ice", Color(79, 195, 247)),
	Tag("Nature", Color(114, 213, 114)),
	Tag("Arcane", Color(240, 98, 146)),
	Tag("Dark", Color(156, 39, 176)),
	Tag("Holy", Color(246, 254, 141)),
	Tag("Sorcery", Color(233, 30, 99)),
	Tag("Conjuration", Color(243, 108, 96)),
	Tag("Enchantment",  Color(49, 164, 144)),
	Tag("Word", Color(255, 213, 79)),
	Tag("Orb", Color(248, 168, 183)),
	Tag("Dragon", Color(176, 18, 10)),
	Tag("Translocation", Color(186, 104, 200)),
	Tag("Undead", Color(97, 97, 97)),
	Tag("Elemental", Color(255, 235, 59)),
	Tag("Heal", Color(66, 189, 66)),
	Tag("Acid", Color(66, 189, 65)),
	Tag("Demon", Color(240, 70, 70)),
	Tag("Spider", Color(10, 126, 7)),
	Tag("Poison", Color(66, 189, 65)),
	Tag("Living", Color(174, 213, 129)),
	Tag("Construct", Color(188, 170, 164)),
	Tag("Metallic", Color(144, 156, 186)),
	Tag("Eye", Color(255, 255, 255)),
	Tag("Glass", Color(43, 175, 43)),
	Tag("Chaos", Color(255, 171, 77)),
	Tag("Blood", Color(134, 13, 7)),
	Tag("Tongue", Color(236, 94, 149)),
	Tag("Slime", Color(206, 220, 56)),
	# Getting hacky here
	Tag("Shield", Color(77, 253, 252)),

	# Super hacky now
	Tag("Buff_Apply", Color(0, 0, 1)),
	Tag("Debuff_Apply", Color(0, 0, 2)),
	Tag("Shield_Apply", Color(0, 0, 3)),
	Tag("Shield_Expire", Color(0, 0, 4)),
	Tag("Sound_Effect", Color(0, 0, 5)),
	Tag("Leap", Color(0, 0, 6)),

	Tag("Arrow", Color(0, 0, 7)),	
	Tag("Petrification", Color(0, 0, 8)),
	Tag("Glassification", Color(0, 0, 9)),

	Tag("Immolate", Color(0, 0, 10)),
	Tag("Thunderstrike", Color(0, 0, 11)),
	Tag("ArmageddonBlade", Color(0, 0, 12)),
])

damage_tags = [
	Tags.Physical,
	Tags.Fire,
	Tags.Lightning,
	Tags.Dark,
	Tags.Poison,
	Tags.Holy,
	Tags.Arcane,
	Tags.Ice
]

Knowledges = [
	Tags.Fire,
	Tags.Ice,
	Tags.Lightning,
	Tags.Nature,
	Tags.Dark,
	Tags.Holy,
	Tags.Arcane,
	Tags.Sorcery,
	Tags.Conjuration,
	Tags.Enchantment
]

attr_colors = {
	'damage': COLOR_DAMAGE,
	'range': COLOR_RANGE,
	'minion_health': Tags.Conjuration.color,
	'minion_damage': Tags.Conjuration.color,
	'breath_damage': Tags.Conjuration.color,
	'minion_duration': Tags.Conjuration.color,
	'minion_range': COLOR_RANGE,
	'duration': Tags.Enchantment.color,
	'max_charges': COLOR_CHARGES,
	'radius': Tags.Sorcery.color,
	'num_summons': COLOR_CHARGES,
	'num_targets': COLOR_CHARGES,
	'shields': COLOR_SHIELD,
	'shot_cooldown': Tags.Enchantment.color, # TODO- different color?
	'strikechance': Tags.Sorcery.color,
	'cooldown': Tags.Enchantment.color,
	'cascade_range': COLOR_CHARGES,
}

