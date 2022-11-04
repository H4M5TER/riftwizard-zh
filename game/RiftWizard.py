import os
import sys
import re
import webbrowser
import loc

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

# Make all the relative file accesses work
cheats_enabled = False
can_enable_cheats = False
if getattr(sys, 'frozen', False):
	dname = os.path.dirname(sys.executable)
	can_enable_cheats = 'cheatmode' in sys.argv
elif __file__:
	dname = os.path.dirname(os.path.abspath(__file__))
	can_enable_cheats = True
os.chdir(dname)

import pygame
import pygame.locals
from Game import *
from collections import defaultdict
from copy import copy

from LevelGen import all_biomes
import gc
import time

import dill as pickle
import text

import SteamAdapter
from Variants import *
from Mutators import *


main_view = None


idle_frame = 0
idle_subframe = 0

cloud_frame_clock = 0

STATUS_ICON_SIZE = 3
SPRITE_SIZE = 16

ANIM_FLINCH = 0
ANIM_ATTACK = 1
ANIM_IDLE = 2

SUB_FRAMES = [
	12,
	12,
	6
]

HIT_FLASH_FLASHES = 3
HIT_FLASH_SUBFRAMES = 2

STATUS_SUBFRAMES = 12

CHAR_HEART = 'HP'#chr(3)
CHAR_SHIELD = 'SH' #chr(4)
CHAR_CLARITY = 'CL'

BORDER_COLOR = (100, 100, 100)

COLOR_CLARITY = (2, 136, 209)

HIGHLIGHT_COLOR = (127, 127, 127)

ATTACK_FINISHED_FRAME = 3

SLIDE_FRAMES = 0

STATE_LEVEL = 0
STATE_CHAR_SHEET = 1
STATE_SHOP = 2
STATE_TITLE = 3
STATE_OPTIONS = 4
STATE_MESSAGE = 5
STATE_CONFIRM = 6
STATE_REMINISCE = 7
STATE_REBIND = 8
STATE_COMBAT_LOG = 9
STATE_PICK_MODE = 10
STATE_PICK_TRIAL = 11
STATE_SETUP_CUSTOM = 12

SHOP_TYPE_SPELLS = 0
SHOP_TYPE_UPGRADES = 1
SHOP_TYPE_SPELL_UPGRADES = 2
SHOP_TYPE_SHOP = 3
SHOP_TYPE_BESTIARY = 4

CHAR_SHEET_SELECT_TYPE_SPELLS = 0
CHAR_SHEET_SELECT_TYPE_SKILLS = 1

MAX_PATH_DELAY = 1

STAR_SPAWN_CHANCE = 0.0001

RENDER_WIDTH = 1600
RENDER_HEIGHT = 900

SPELL_FAIL_LOCKOUT_FRAMES = 12

COLOR_VICTORY = Tags.Ice.color.to_tup()

# How many squares per frame are flipped from one level to the next during deploy/undeploy
DEPLOY_SPEED = 4

# Attempt to fix high DPI for windows
try:
	import ctypes
	errorCode = ctypes.windll.shcore.SetProcessDpiAwareness(2)
except:
	pass

# Hack to fix highlight bug
class SpellCharacterWrapper(object):
	def __init__(self, spell):
		self.spell = spell

	def __eq__(self, other):
		if not isinstance(other, SpellCharacterWrapper):
			return False
		return self.spell == other.spell

class TooltipExamineTarget(object):

	def __init__(self, desc):
		self.description = desc

LEARN_SPELL_TARGET = TooltipExamineTarget("学习新法术")
LEARN_SKILL_TARGET = TooltipExamineTarget("学习新能力")
CHAR_SHEET_TARGET = TooltipExamineTarget("学习新法术和能力")
INSTRUCTIONS_TARGET = TooltipExamineTarget("学习如何游玩")
OPTIONS_TARGET = TooltipExamineTarget("调整游戏设置")

WELCOME_TARGET = TooltipExamineTarget(text.welcome_text)
DEPLOY_TARGET = TooltipExamineTarget(text.deploy_text)

TOOLTIP_PREV = 0
TOOLTIP_NEXT = 1
TOOLTIP_EXIT = 2
TOOLTIP_UPGRADE = 3

UI_TOP = 0
UI_LEFT = 1
UI_RIGHT = 2
UI_BOTTOM = 3
UI_UPPER_LEFT = 4
UI_UPPER_RIGHT = 5
UI_LOWER_LEFT = 6
UI_LOWER_RIGHT = 7
UI_FIRST = 0
UI_LAST = UI_LOWER_RIGHT

TITLE_SELECTION_LOAD = 0
TITLE_SELECTION_ABANDON = 1
TITLE_SELECTION_NEW = 2
TITLE_SELECTION_OPTIONS = 3
TITLE_SELECTION_BESTIARY = 4
TITLE_SELECTION_DISCORD = 5
TITLE_SELECTION_EXIT = 6
TITLE_SELECTION_QQ = 7
TITLE_SELECTION_INSTRUCTIONS = 8
TITLE_SELECTION_MAX = TITLE_SELECTION_INSTRUCTIONS

OPTION_HELP = 0
OPTION_SOUND_VOLUME = 1
OPTION_MUSIC_VOLUME = 2
OPTION_SPELL_SPEED = 3
OPTION_CONTROLS = 4
OPTION_RETURN = 5
OPTION_EXIT = 6
OPTION_MAX = OPTION_EXIT
OPTION_SMART_TARGET = 7

GAME_MODE_NORMAL = 0
GAME_MODE_TRIALS = 1
GAME_MODE_WEEKLY = 2
GAME_MODE_CUSTOM = 3
GAME_MODE_MAX = GAME_MODE_WEEKLY

COLOR_XP = (229, 191, 0)

tooltip_colors = {}
for tag in Tags:
	tooltip_colors[tag.name.lower()] = tag.color
tooltip_colors.update(attr_colors)
tooltip_colors['petrify'] = Tags.Construct.color
tooltip_colors['petrified'] = tooltip_colors['petrify']
tooltip_colors['petrifies'] = tooltip_colors['petrify']
tooltip_colors['frozen'] = Tags.Ice.color
tooltip_colors['freezes'] = Tags.Ice.color
tooltip_colors['freeze'] = Tags.Ice.color
tooltip_colors['stunned'] = Tags.Physical.color
tooltip_colors['stun'] = tooltip_colors['stunned']
tooltip_colors['stuns'] = tooltip_colors['stunned']
tooltip_colors['berserk'] = COLOR_DAMAGE
tooltip_colors['poisoned'] = Tags.Poison.color
tooltip_colors['blind'] = Tags.Holy.color
tooltip_colors['blinded'] = tooltip_colors['blind']
tooltip_colors['glassify'] = Tags.Glass.color
tooltip_colors['glassified'] = Tags.Glass.color

REPEAT_INTERVAL = .05
REPEAT_DELAY = .2

import logging
mem_log = logging.getLogger("memory")
mem_log.setLevel(logging.DEBUG)
mem_log.propagate = False
mem_log.addHandler(logging.FileHandler('mem_log.txt', mode='w'))

Channel = namedtuple('Channel', 'name channel base_volume')

image_cache = {}
def get_image(asset, fill_color=None, alphafy=False):
	assert(asset)
	assert(isinstance(asset, list))
	assert(isinstance(asset[0], str))

	# First check
	path = os.path.join('rl_data', *asset) + '.png'
	key = (path, fill_color, alphafy) if fill_color else path
	if key in image_cache:
		return image_cache[key]

	# If the path cannot be resolved in the main data directory, try treating it as a mod path
	if not os.path.exists(path):
		mod_path = os.path.join('mods', *asset) + '.png'
		if os.path.exists(mod_path):
			path = mod_path

	if not os.path.exists(path):
		# Todo- cache None?
		return None

	image = pygame.image.load(path)

	if alphafy:
		image.set_colorkey((0, 0, 0))

	if fill_color:
		image.fill(fill_color, special_flags=pygame.BLEND_RGBA_MIN)
		image_cache[(path, fill_color)] = image

	image_cache[key] = image

	return image_cache[key]

def get_spell_asset(spell):
	if spell.asset:
		asset = spell.asset
	elif isinstance(spell, Item):
		asset = ['tiles', 'items', 'animated', spell.name.lower().replace(' ', '_')]
	else:
		asset = ['UI', 'spell skill icons', spell.name.lower().replace(' ', '_')]
	return asset

def get_unit_asset(unit, forced_name=None):

	if unit.asset:
		return unit.asset

	if forced_name:
		name = forced_name
	else:
		name = unit.get_asset_name()

	if "skeletal" in name:

		if unit.stationary:
			name = "skeletal_stationary"
		elif unit.flying:
			name = 'skeletal_flying'
		else:
			name = "skeletal"

	if unit.is_lair:
		name = "lair"

	return ['char', name]

def pixel_is_empty(p):
	if p.a == 0:
		return True
	if p.r == p.g == p.b == 0:
		return True
	return False

def get_glow(surface, color, outline=False):

	glow_frame = pygame.Surface((SPRITE_SIZE, SPRITE_SIZE), flags=pygame.SRCALPHA)

	for i in range(0, SPRITE_SIZE):
		for j in range(0, SPRITE_SIZE):
			c = surface.get_at((i, j))

			if pixel_is_empty(c):
				continue

			if outline:

				# If an edge pixel is non empty, color it
				if i == 0 or j == 0 or i == SPRITE_SIZE - 1 or j == SPRITE_SIZE - 1:
					glow_frame.set_at((i, j), color.to_tup())

				# If a non edge pixel is non empty, color empty neighbors
				else:
					for p in [(i-1, j), (i+1, j), (i, j-1), (i, j+1)]:
						if pixel_is_empty(surface.get_at(p)):
							glow_frame.set_at(p, color.to_tup())
			else:
				glow_frame.set_at((i, j), color.to_tup())

	return glow_frame


class LookSpell(Spell):

	def on_init(self):
		self.range = 99
		self.requires_los = False
		self.show_tt = False
		self.quick_cast = True

	def can_cast(self, x, y):
		return True

	def cast_instant(self, x, y):
		pass

	def get_tab_targets(self):
		return [tile.unit or tile.prop for tile in self.caster.level.iter_tiles() if (tile.prop or tile.unit) and (tile.unit != self.caster)]

class WalkSpell(Spell):

	def on_init(self):
		self.range = 99
		self.requires_los = False
		self.show_tt = False

	def can_cast(self, x, y):
		return not any(are_hostile(u, self.caster) for u in self.caster.level.units)

	def get_tab_targets(self):
		props = [tile.prop for tile in self.caster.level.iter_tiles() if tile.prop]
		portals = [p for p in props if isinstance(p, Portal)]
		others = [p for p in props if not isinstance(p, Portal)]
		others.sort(key = lambda p: distance(p, self.caster))

		return others + portals

	def cast_instant(self, x, y):
		main_view.path = self.caster.level.find_path(self.caster, Point(x, y), self.caster, pythonize=True)

COLOR_LAIR_PRIMARY = (255, 0, 0, 255)
COLOR_LAIR_SECONDARY = (0, 255, 0, 255)

class SpriteSheet(object):

	def __init__(self, param, color=None, lair_colors=None):
		self.color = color
		self.param = param
		assert(param)

		if isinstance(param, Sprite):
			self.image = self.make_ascii_sprite(param)
		elif isinstance(param, list):
			self.image = get_image(param)
		else:
			# Unsupported sprite sheet param type
			assert(False)

		assert(self.image.get_width() % SPRITE_SIZE == 0)

		if self.color:
			self.image.fill(color, special_flags=pygame.BLEND_RGBA_MIN)

		# For lair colors- replace (255, 0, 0) with first, replace (0, 255, 0) with second
		if lair_colors:
			self.image = self.image.copy()
			for i in range(self.image.get_width()):
				for j in range(self.image.get_height()):
					cur_color = self.image.get_at((i, j))
					if cur_color == COLOR_LAIR_PRIMARY:
						self.image.set_at((i, j), lair_colors[0])
					elif cur_color == COLOR_LAIR_SECONDARY:
						self.image.set_at((i, j), lair_colors[1])

		self.anim_frames = {k: [] for k in [ANIM_ATTACK, ANIM_FLINCH, ANIM_IDLE]}
		self.anim_frames_flipped = {k: [] for k in [ANIM_ATTACK, ANIM_FLINCH, ANIM_IDLE]}

		self.glow_frames = {k: [] for k in [ANIM_ATTACK, ANIM_FLINCH, ANIM_IDLE]}
		self.glow_frames_flipped = {k: [] for k in [ANIM_ATTACK, ANIM_FLINCH, ANIM_IDLE]}

		self.ally_frames = {k: [] for k in [ANIM_ATTACK, ANIM_FLINCH, ANIM_IDLE]}
		self.ally_frames_flipped = {k: [] for k in [ANIM_ATTACK, ANIM_FLINCH, ANIM_IDLE]}

		self.anim_lengths = {}

		image_anims = self.image.get_height() // SPRITE_SIZE

		for anim in [ANIM_ATTACK, ANIM_FLINCH, ANIM_IDLE]:

			frames = 0
			for i in range(self.image.get_width() // SPRITE_SIZE):
				subimage_y = min(anim, image_anims - 1) * SPRITE_SIZE
				subimage = self.image.subsurface(pygame.Rect(SPRITE_SIZE * frames, subimage_y, SPRITE_SIZE, SPRITE_SIZE))
				pixels = [subimage.get_at((i, j)) for i in range(0, SPRITE_SIZE) for j in range(0, SPRITE_SIZE)]
				if all(p.a == 0 for p in pixels):
					break
				frames += 1
				self.anim_frames[anim].append(subimage)
				self.anim_frames_flipped[anim].append(pygame.transform.flip(subimage, True, False))

			self.anim_lengths[anim] = frames

		self.glow_cache = {}



	def get_glow_frame(self, anim, frame, color, flipped, outline=False):
		key = (anim, frame, color, flipped, outline)
		if key in self.glow_cache:
			return self.glow_cache[key]

		frame_dict = self.anim_frames if not flipped else self.anim_frames_flipped

		# Default to idle frame 1 if requested frame does not exist
		if anim not in frame_dict or len(frame_dict[anim]) <= frame:
			frame = self.anim_frames[ANIM_IDLE][0]
		else:
			frame = frame_dict[anim][frame]

		glow_frame = get_glow(frame, color, outline)
		self.glow_cache[key] = glow_frame

		return glow_frame

	def make_ascii_sprite(self, ascii_sprite):
		image = pygame.Surface((SPRITE_SIZE, SPRITE_SIZE*3))
		image.fill((0, 0, 0, 0))
		color = ascii_sprite.color.to_tup()
		if color == (0, 0, 0):
			color = (255, 255, 255)

		flinch = main_view.font.render(ascii_sprite.char, False, color)
		attack = main_view.font.render(ascii_sprite.char, False, color)
		idle = main_view.font.render(ascii_sprite.char, False, color)

		for cur_image, anim in [(flinch, ANIM_FLINCH), (idle, ANIM_IDLE), (attack, ANIM_ATTACK)]:
			x_margin = (SPRITE_SIZE - cur_image.get_width()) // 2 + 1
			y_margin = SPRITE_SIZE - cur_image.get_height()
			image.blit(cur_image, (x_margin, SPRITE_SIZE*anim))
		return image

	def get_lair_colors(self):
		if not hasattr(self, 'common_color'):
			pixels = [self.anim_frames[ANIM_IDLE][0].get_at((i, j)) for i in range(SPRITE_SIZE) for j in range(SPRITE_SIZE)]
			pixels = [p for p in pixels if p[3]]
			first = max(pixels, key = pixels.count)
			other_colors = [p for p in pixels if p != first]
			if other_colors:
				second = max([p for p in pixels if p != first], key = pixels.count)
			else:
				second = first

		return tuple(first), tuple(second)

	def __reduce__(self):
		return (SpriteSheet, (self.param, self.color))

class LeapEffect(object):

	def __init__(self, x, y, unit, color, duration=7):
		colors = [tween_color(color, Color(0, 0, 0), i / duration) for i in range(duration)]

		anim = unit.Transform_Anim or unit.Anim
		if anim:
			self.sprites = [anim.sheet.get_glow_frame(ANIM_ATTACK, 0, color, flipped=unit.sprite.face_left, outline=True) for color in colors]
		else:
			self.sprites = None
			self.finished = True
		self.frame = 0
		self.duration = duration
		self.finished = False
		self.x = x
		self.y = y

	def draw(self, display):
		if self.sprites:
			display.blit(self.sprites[self.frame], (self.x * SPRITE_SIZE, self.y * SPRITE_SIZE))
		self.frame += 1
		if self.frame >= self.duration:
			self.finished = True

class ProjectileEffect(object):

	def __init__(self, x, y, sprite, origin, dest, proj_color=None, duration=4):
		# Todo: rotate sprite

		if proj_color and proj_color != Color(0, 0, 0):
			sprite = sprite.copy()
			sprite.fill(proj_color.to_tup(), special_flags=pygame.BLEND_RGBA_MIN)

		flip_x = origin.x > dest.x
		flip_y = origin.y < dest.y

		rotate = abs(origin.y - dest.y) > abs(origin.x - dest.x)

		def get_faded(sprite, i):

			s = sprite
			if rotate:
				s = pygame.transform.rotate(sprite, 90)

			s = pygame.transform.flip(s, flip_x, flip_y)

			# Fade the sprite to the requested level
			fade_color = tween_color(Color(255, 255, 255), Color(0, 0, 0), i / duration)
			s.fill(fade_color.to_tup(), special_flags=pygame.BLEND_RGB_MIN)

			return s

		self.sprites = [get_faded(sprite, i) for i in range(duration)]
		self.frame = 0
		self.duration = duration
		self.finished = False
		self.x = x
		self.y = y

	def draw(self, display):
		display.blit(self.sprites[self.frame], (self.x * SPRITE_SIZE, self.y * SPRITE_SIZE))
		self.frame += 1
		if self.frame >= self.duration:
			self.finished = True

class UnitSprite(object):

	def __init__(self, unit, sprite_sheet, view, boss_glow=False):
		self.anim = ANIM_IDLE
		self.anim_frame = 0
		self.anim_subframe = 0
		self.unit = unit

		self.unit.level.event_manager.register_entity_trigger(EventOnSpellCast, unit, self.on_attack)
		self.unit.level.event_manager.register_entity_trigger(EventOnDamaged, unit, self.on_damaged)
		self.unit.level.event_manager.register_entity_trigger(EventOnMoved, unit, self.on_moved)
		self.unit.level.event_manager.register_entity_trigger(EventOnDeath, unit, self.on_death)
		self.unit.level.event_manager.register_entity_trigger(EventOnItemPickup, unit, self.on_item)

		self.sheet = sprite_sheet
		self.slide_frames = 0

		self.hit_flashes_shown = 0
		self.hit_flash_sub_frame = 0
		self.hit_flash_colors = []

		self.boss_glow = boss_glow

		self.finished = False

		self.is_death_flash = False

	def unregister(self):
		self.unit.level.event_manager.unregister_entity_trigger(EventOnSpellCast, self.unit, self.on_attack)
		self.unit.level.event_manager.unregister_entity_trigger(EventOnDamaged, self.unit, self.on_damaged)
		self.unit.level.event_manager.unregister_entity_trigger(EventOnMoved, self.unit, self.on_moved)
		self.unit.level.event_manager.unregister_entity_trigger(EventOnDeath, self.unit, self.on_death)
		self.unit.level.event_manager.unregister_entity_trigger(EventOnItemPickup, self.unit, self.on_item)

	def advance(self):
		self.anim_subframe += 1

		if self.anim_subframe >= SUB_FRAMES[self.anim]:
			self.anim_subframe = 0
			self.anim_frame += 1
			if self.anim_frame >= self.sheet.anim_lengths[self.anim]:
				# For now always go back to idle.  So idle loops, and other anims return to idle.
				self.anim = ANIM_IDLE
				self.anim_frame = 0


		# Synchronize idle anims
		if self.anim == ANIM_IDLE:
			self.anim_frame = idle_frame % self.sheet.anim_lengths[self.anim]
			# Prevent flashing of placeholders
			if self.anim_frame >= self.sheet.anim_lengths[self.anim]:
				self.anim_frame = 0
			# freeze stunned creature
			if self.unit.is_stunned():
				self.anim_frame = 0
		self.last_position = Point(self.unit.x, self.unit.y)
		if self.slide_frames:
			self.slide_frames -= 1

		# Channelers always in attack, and always ready to snap out of it
		if self.unit.has_buff(ChannelBuff):
			self.anim == ANIM_ATTACK
			self.anim_subframe = SUB_FRAMES[ANIM_ATTACK] - 2

	def on_attack(self, evt):

		if not evt.spell.animate:
			return

		# Do not try to play attack anim if it does not exist
		if not self.sheet.anim_lengths.get(ANIM_ATTACK, None):
			return

		self.anim = ANIM_ATTACK
		self.anim_frame = 0
		self.anim_subframe = 0

		if type(evt.spell) not in [SimpleMeleeAttack]:
			if self.unit.is_player_controlled:
				if evt.spell.item:
					main_view.play_sound("item_use")
				else:
					if Tags.Conjuration in evt.spell.tags:
						main_view.play_sound("summon_3")
					elif Tags.Translocation in evt.spell.tags:
						main_view.play_sound("teleport_3")
					elif Tags.Word in evt.spell.tags:
						main_view.play_sound("sorcery_5")
					elif Tags.Sorcery in evt.spell.tags:
						main_view.play_sound("sorcery_ally")
					elif Tags.Enchantment in evt.spell.tags:
						main_view.play_sound("enchant_2")

			else:
				main_view.play_sound("sorcery_enemy")


	def on_damaged(self, evt):
		color = Color(255, 255, 255) if self.unit.is_alive() else Color(255, 0, 0)
		self.hit_flash_colors = [color]
		self.hit_flash_sub_frame = 0
		self.hit_flashes_shown = 0

		# sound
		if self.unit.is_player_controlled:
			main_view.play_sound("hit_4")
		else:
			main_view.play_sound("hit_enemy")

	def on_moved(self, evt):
		# Dont slide teleports
		if evt.teleport:
			return
		self.old_pos = self.last_position
		self.slide_frames = SLIDE_FRAMES

	def on_death(self, evt):
		# On death, make a copy of self, add it to the list of effects, and trigger its on damaged
		if evt.damage_event:
			s = copy(self)
			s.x = self.unit.x
			s.y = self.unit.y
			s.is_death_flash = True

			if not self.unit.is_player_controlled and not self.unit.name == "Mordred":
				main_view.queue_effect(s)
			else:
				# Clear all effects on the square except last death
				main_view.effects = [e for e in main_view.effects if not ((e.x == self.unit.x) and (e.y == self.unit.y))]
				main_view.effects.append(s)

		if self.unit.is_player_controlled:
			# Streak back to 0
			SteamAdapter.set_stat('s', 0)
			# 1 more loss
			losses = SteamAdapter.get_stat('l')
			SteamAdapter.set_stat('l', losses + 1)
			main_view.play_music('lose')
			main_view.play_sound("death_player")

		else:
			if self.unit.is_boss:
				main_view.play_sound("death_boss")
			else:
				main_view.play_sound("death_enemy")

		SteamAdapter.unlock_bestiary(self.unit.name)
		if self.unit.parent:
			SteamAdapter.unlock_bestiary(self.unit.parent.name)


	def on_item(self, evt):
		main_view.play_sound("item_pickup")

	def draw(self, surface, no_pos=False):
		self.advance()

		if not no_pos:
			x = SPRITE_SIZE * self.unit.x
			y = SPRITE_SIZE * self.unit.y
		elif no_pos:
			x = 0

			y = 0

		if self.slide_frames:
			oldx = SPRITE_SIZE * self.old_pos.x
			oldy = SPRITE_SIZE * self.old_pos.y
			tween = self.slide_frames / float(SLIDE_FRAMES)
			xdiff = oldx - x
			ydiff = oldy - y
			x += tween * xdiff
			y += tween * ydiff

		if self.hit_flash_colors and self.hit_flash_sub_frame < HIT_FLASH_SUBFRAMES:
			flash_image = self.sheet.get_glow_frame(self.anim, self.anim_frame, self.hit_flash_colors[0], self.unit.sprite.face_left)
			surface.blit(flash_image, (x, y))
		elif self.unit.is_alive():
			frame_dict = self.sheet.anim_frames_flipped if self.unit.sprite.face_left else self.sheet.anim_frames

			frame = frame_dict[self.anim]
			if self.anim_frame >= len(frame):
				assert False, "Trying to render frame %d of anim %d on %s, impossible" % (self.anim_frame, self.anim, self.unit.name)
			to_draw = frame[self.anim_frame]
			surface.blit(to_draw, (x, y))

		if self.boss_glow:
			glow_image = self.sheet.get_glow_frame(self.anim, self.anim_frame, Color(255, 80, 0), self.unit.sprite.face_left, outline=True)
			surface.blit(glow_image, (x, y))


		if self.hit_flash_colors:
			self.hit_flash_sub_frame += 1
			if self.hit_flash_sub_frame >= HIT_FLASH_SUBFRAMES * 2:
				self.hit_flashes_shown += 1
				self.hit_flash_sub_frame = 0
				if self.hit_flashes_shown == HIT_FLASH_FLASHES:
					self.hit_flash_colors = self.hit_flash_colors[1:]
					self.hit_flashes_shown = 0
					if not self.hit_flash_colors:
						self.finished = self.is_death_flash

	def is_idle(self):
		#if self.slide_frames:
		#   return False
		if self.anim == ANIM_ATTACK:
			return self.anim_frame >= ATTACK_FINISHED_FRAME
		else:
			return self.anim == ANIM_IDLE

class SimpleSprite(object):

	def __init__(self, x, y, image, speed=1, loop=False, sync=False):
		self.image = image
		self.speed = speed
		self.x = x
		self.y = y
		self.loop = loop

		self.finished = False
		self.frame = 0
		self.subframe = 0
		self.sync = sync

	def draw(self, surface):
		self.advance()

		x = SPRITE_SIZE * self.x
		y = SPRITE_SIZE * self.y
		sourcerect = (SPRITE_SIZE * self.frame, 0, SPRITE_SIZE, SPRITE_SIZE)
		surface.blit(self.image, (x, y), sourcerect)

	def advance(self):
		if self.sync:
			if idle_subframe == 0:
				self.frame += 1

		else:
			self.subframe += 1

			if self.subframe == self.speed:
				self.subframe = 0
				self.frame += 1

		if self.frame >= (self.image.get_width() // SPRITE_SIZE):
			if not self.loop:
				self.finished = True
			else:
				self.frame = 0
				self.subframe = 0


class EffectRect(object):

	def __init__(self, x, y, color, frames):
		self.color = color
		self.total_frames = frames
		self.finished = False
		self.frame = 0

		self.x = x
		self.y = y

	def draw(self, surface):
		x = SPRITE_SIZE * self.x
		y = SPRITE_SIZE * self.y
		rect = (x, y, SPRITE_SIZE, SPRITE_SIZE)
		t = (self.total_frames - self.frame) / float(self.total_frames)
		color = tween_color(self.color, Color(0, 0, 0), t)
		pygame.draw.rect(surface, color.to_tup(), rect)
		self.advance()

	def advance(self):
		self.frame += 1
		if self.frame == self.total_frames:
			self.finished = True

class Star(object):

	def __init__(self, image):
		self.orig_image = image
		self.image = image.copy()
		self.frame = 0
		self.lifetime = 1200

	def advance(self):
		self.frame += 1
		high_point = self.lifetime // 2
		intensity = (high_point - abs(self.frame - high_point)) / high_point
		intensity = math.pow(intensity, 2)
		v = math.ceil(255 * intensity)


		self.image.blit(self.orig_image, (0, 0))
		self.image.fill((v, v, v), special_flags=pygame.BLEND_RGB_MULT)

	def is_finished(self):
		return self.frame >= self.lifetime

KEY_BIND_UP = 0
KEY_BIND_DOWN = 1
KEY_BIND_LEFT = 2
KEY_BIND_RIGHT = 3
KEY_BIND_UP_RIGHT = 4
KEY_BIND_UP_LEFT = 5
KEY_BIND_DOWN_RIGHT = 6
KEY_BIND_DOWN_LEFT = 7
KEY_BIND_PASS = 8
KEY_BIND_CONFIRM = 9
KEY_BIND_ABORT = 10
KEY_BIND_SPELL_1 = 11
KEY_BIND_SPELL_2 = 12
KEY_BIND_SPELL_3 = 13
KEY_BIND_SPELL_4 = 14
KEY_BIND_SPELL_5 = 15
KEY_BIND_SPELL_6 = 16
KEY_BIND_SPELL_7 = 17
KEY_BIND_SPELL_8 = 18
KEY_BIND_SPELL_9 = 19
KEY_BIND_SPELL_10 = 20
KEY_BIND_MODIFIER_1 = 21
KEY_BIND_MODIFIER_2 = 22
KEY_BIND_TAB = 23
KEY_BIND_CTRL = 24
KEY_BIND_VIEW = 25
KEY_BIND_WALK = 26
KEY_BIND_AUTOPICKUP = 27
KEY_BIND_CHAR = 28
KEY_BIND_SPELLS = 29
KEY_BIND_SKILLS = 30
KEY_BIND_HELP = 31
KEY_BIND_INTERACT = 32
KEY_BIND_MESSAGE_LOG = 33
KEY_BIND_THREAT = 34
KEY_BIND_LOS = 35
KEY_BIND_NEXT_EXAMINE_TARGET = 36
KEY_BIND_PREV_EXAMINE_TARGET = 37
KEY_BIND_FF = 38
KEY_BIND_MAX = KEY_BIND_FF

KEY_BIND_OPTION_ACCEPT = KEY_BIND_MAX + 1
KEY_BIND_OPTION_ABORT = KEY_BIND_MAX + 2
KEY_BIND_OPTION_RESET = KEY_BIND_MAX + 3


default_key_binds = {
	KEY_BIND_UP : [pygame.K_UP, pygame.K_KP8],
	KEY_BIND_DOWN : [pygame.K_DOWN, pygame.K_KP2],
	KEY_BIND_LEFT : [pygame.K_LEFT, pygame.K_KP4],
	KEY_BIND_RIGHT : [pygame.K_RIGHT, pygame.K_KP6],
	KEY_BIND_UP_RIGHT : [pygame.K_KP9, None],
	KEY_BIND_UP_LEFT: [pygame.K_KP7, None],
	KEY_BIND_DOWN_RIGHT: [pygame.K_KP3, None],
	KEY_BIND_DOWN_LEFT: [pygame.K_KP1, None],
	KEY_BIND_PASS : [pygame.K_SPACE, pygame.K_KP5],
	KEY_BIND_CONFIRM : [pygame.K_RETURN, pygame.K_KP_ENTER],
	KEY_BIND_ABORT : [pygame.K_ESCAPE, None],
	KEY_BIND_SPELL_1 : [pygame.K_1, None],
	KEY_BIND_SPELL_2 : [pygame.K_2, None],
	KEY_BIND_SPELL_3 : [pygame.K_3, None],
	KEY_BIND_SPELL_4 : [pygame.K_4, None],
	KEY_BIND_SPELL_5 : [pygame.K_5, None],
	KEY_BIND_SPELL_6 : [pygame.K_6, None],
	KEY_BIND_SPELL_7 : [pygame.K_7, None],
	KEY_BIND_SPELL_8 : [pygame.K_8, None],
	KEY_BIND_SPELL_9 : [pygame.K_9, None],
	KEY_BIND_SPELL_10 : [pygame.K_0, None],
	KEY_BIND_MODIFIER_1 : [pygame.K_LSHIFT, pygame.K_RSHIFT],
	KEY_BIND_MODIFIER_2 : [pygame.K_LALT, pygame.K_RALT],
	KEY_BIND_TAB : [pygame.K_TAB, None],
	KEY_BIND_CTRL : [pygame.K_LCTRL, pygame.K_RCTRL],
	KEY_BIND_VIEW : [pygame.K_v, None],
	KEY_BIND_WALK : [pygame.K_w, None],
	KEY_BIND_AUTOPICKUP : [pygame.K_a, None],
	KEY_BIND_CHAR : [pygame.K_c, pygame.K_BACKQUOTE],
	KEY_BIND_SPELLS : [pygame.K_s, None],
	KEY_BIND_SKILLS : [pygame.K_k, None],
	KEY_BIND_HELP : [pygame.K_h, pygame.K_SLASH],
	KEY_BIND_INTERACT : [pygame.K_i, pygame.K_PERIOD],
	KEY_BIND_MESSAGE_LOG : [pygame.K_m, None],
	KEY_BIND_THREAT: [pygame.K_t, None],
	KEY_BIND_LOS: [pygame.K_l, None],
	KEY_BIND_PREV_EXAMINE_TARGET: [pygame.K_PAGEUP, None],
	KEY_BIND_NEXT_EXAMINE_TARGET: [pygame.K_PAGEDOWN, None],
	KEY_BIND_FF: [pygame.K_BACKSPACE, None]
}

key_names = {
	KEY_BIND_UP : "up",
	KEY_BIND_DOWN : "down",
	KEY_BIND_LEFT : "left",
	KEY_BIND_RIGHT : "right",
	KEY_BIND_UP_RIGHT : "up-right",
	KEY_BIND_UP_LEFT: "up-left",
	KEY_BIND_DOWN_RIGHT: "down-right",
	KEY_BIND_DOWN_LEFT: "down-left",
	KEY_BIND_PASS : "pass/channel",
	KEY_BIND_CONFIRM : "confirm/cast",
	KEY_BIND_ABORT : "abort/cast",
	KEY_BIND_SPELL_1 : "Spell 1",
	KEY_BIND_SPELL_2 : "Spell 2",
	KEY_BIND_SPELL_3 : "Spell 3",
	KEY_BIND_SPELL_4 : "Spell 4",
	KEY_BIND_SPELL_5 : "Spell 5",
	KEY_BIND_SPELL_6 : "Spell 6",
	KEY_BIND_SPELL_7 : "Spell 7",
	KEY_BIND_SPELL_8 : "Spell 8",
	KEY_BIND_SPELL_9 : "Spell 9",
	KEY_BIND_SPELL_10 : "Spell 10",
	KEY_BIND_MODIFIER_1 : "Spell Modifier Key",
	KEY_BIND_MODIFIER_2 : "Item Modifier Key",
	KEY_BIND_TAB : "Next Target",
	KEY_BIND_CTRL : "Show Line of Sight",
	KEY_BIND_VIEW : "Look",
	KEY_BIND_WALK : "Walk",
	KEY_BIND_AUTOPICKUP : "Autopickup",
	KEY_BIND_CHAR : "Character Sheet",
	KEY_BIND_SPELLS : "Spells",
	KEY_BIND_SKILLS : "Skills",
	KEY_BIND_HELP : "Help",
	KEY_BIND_INTERACT : "Interact",
	KEY_BIND_MESSAGE_LOG : "Message Log",
	KEY_BIND_THREAT : "Show Threat Zone",
	KEY_BIND_LOS : "Show Line of Sight",
	KEY_BIND_PREV_EXAMINE_TARGET : "Next tooltip",
	KEY_BIND_NEXT_EXAMINE_TARGET : "Prev tooltip",
	KEY_BIND_FF: "Fast Forward",
}

class PyGameView(object):

	def __init__(self):
		self.game = None

		try:
			with open('options2.dat', 'rb') as options_file:
				self.options = pickle.load(options_file)
		except:
			self.options = {}

		if 'sound_volume' not in self.options:
			self.options['sound_volume'] = 100
		if 'music_volume' not in self.options:
			self.options['music_volume'] = 100
		if 'smart_targeting' not in self.options:
			self.options['smart_targeting'] = False
		if 'spell_speed' not in self.options:
			self.options['spell_speed'] = 0

		self.rebinding = False
		self.key_binds = dict(default_key_binds)
		self.key_binds.update(self.options.get('key_binds', {}))

		pygame.mixer.pre_init(buffer=512)
		pygame.init()
		pygame.display.init()

		pygame.display.set_caption("Rift Wizard")

		level_width = LEVEL_SIZE * SPRITE_SIZE

		self.h_margin = (1600 - (2 * level_width)) // 2

		# Weird trick to do a fast 2x blit, probably unnecceary
		self.whole_level_display = pygame.Surface((800, 450))
		self.level_display = self.whole_level_display.subsurface(pygame.Rect(self.h_margin // 2, 0, SPRITE_SIZE * LEVEL_SIZE, SPRITE_SIZE * LEVEL_SIZE))
		self.targeting_display = pygame.Surface((self.level_display.get_width(), self.level_display.get_height()))

		self.character_display = pygame.Surface((self.h_margin, 900))
		self.examine_display = pygame.Surface((self.h_margin, 900))

		self.middle_menu_display = pygame.Surface((1600 - 2 * self.h_margin, 900))\

		self.real_display = None

		self.outer_x_margin = 0
		self.outer_y_margin = 0
		self.tiny_mode = False

		modes = pygame.display.list_modes()

		self.screen = pygame.Surface((1600, 900))

		self.windowed = 'windowed' in sys.argv
		self.native_res = 'native_res' in sys.argv

		# Windowed
		info = pygame.display.Info()
		self.display_res = (info.current_w, info.current_h)
		if self.display_res not in modes:
			self.display_res = modes[0]

		if self.windowed:
			# For windowed- try 1600 x 900(1x), but for smaller displays do 1/2 scale
			# For now 4K users will have to maximize or resize, and thats ok.
			if info.current_w > 1600:
				self.display_res = (1600, 900)
			else:
				self.display_res = (800, 450)
			pygame.display.set_mode(self.display_res, pygame.RESIZABLE)
		elif self.native_res:
			# If no res opts are given just use the current desktop res
			assert((1600, 900) in modes)
			self.display_res = (1600, 900)
			pygame.display.set_mode(self.display_res, pygame.FULLSCREEN)
		else:
			# If no res opts are given just use the current desktop res
			pygame.display.set_mode(self.display_res, pygame.FULLSCREEN | pygame.SCALED)


		self.clock = pygame.time.Clock()

		#pygame.mixer.init()
		self.can_play_sound = False
		if not 'nosound' in sys.argv:
			try:
				self.hit_sound_channel = pygame.mixer.Channel(0)
				self.hit_player_sound_channel = pygame.mixer.Channel(1)
				self.death_sound_channel = pygame.mixer.Channel(2)
				self.cast_sound_channel = pygame.mixer.Channel(3)
				self.step_sound_channel = pygame.mixer.Channel(4)
				self.misc_sound_channel = pygame.mixer.Channel(5)
				self.ui_sound_channel = pygame.mixer.Channel(6)

				pygame.mixer.set_reserved(6)

				self.base_volumes = {
					self.hit_sound_channel : .5,
					self.hit_player_sound_channel: .6,
					self.death_sound_channel: .75,
					self.cast_sound_channel: .65,
					self.step_sound_channel: .15,
					self.misc_sound_channel: .75,
					self.ui_sound_channel: .25
				}

				sound = True #'sound' in sys.argv

				if not sound:
					pygame.mixer.music.stop()
					channels = [self.hit_sound_channel, self.hit_player_sound_channel, self.death_sound_channel, self.cast_sound_channel, self.step_sound_channel]
					for channel in channels:
						channel.set_volume(0)

				self.can_play_sound = True

				self.adjust_volume(0, "sound")

			except:
				pass

		pygame.font.init()
		# 字体锚点
		font_path = os.path.join("rl_data", "sarasa-mono-sc-bold.ttf")
		self.font = pygame.font.Font(font_path, 16)
		self.space_width = self.font.size(' ')[0]
		self.ascii_idle_font = pygame.font.Font(font_path, 16)
		self.ascii_attack_font = pygame.font.Font(font_path, 16)
		self.ascii_flinch_font = pygame.font.Font(font_path, 16)

		self.frameno = 0

		floor_path = os.path.join("rl_data", "floor_tile.png")

		self.load_chasm_sprites()
		self.load_wall_sprites()
		self.load_floor_sprites()

		self.effects = []

		self.load_effect_images()

		self.sprite_sheets = {}
		self.cur_spell = None
		self.cur_spell_target = None
		self.targetable_tiles = None
		self.examine_target = None

		prop_path = os.path.join("rl_data", "tiles", "shrine", "shrine_white.png")
		self.prop_sprite = pygame.image.load(prop_path)

		self.deploy_target = None
		self.border_margin = 12
		self.linesize = self.font.get_linesize() + 2

		self.state = None
		self.return_to_title()

		self.char_sheet_select_index = 0
		self.char_sheet_select_type = 0
		self.shop_type = SHOP_TYPE_SPELLS
		self.shop_upgrade_spell = None
		self.shop_selection_index = 0
		self.shop_page = 0
		self.max_shop_objects = 35  # 每页上限 原始44 更纱黑体行高较高

		self.tag_keys = {
			'f': Tags.Fire,
			'i': Tags.Ice,
			'l': Tags.Lightning,
			'n': Tags.Nature,
			'a': Tags.Arcane,
			'd': Tags.Dark,
			'h': Tags.Holy,
			'm': Tags.Metallic,

			's': Tags.Sorcery,
			'e': Tags.Enchantment,
			'c': Tags.Conjuration,

			'y': Tags.Eye,
			'r': Tags.Dragon,
			'b': Tags.Orb,
			'o': Tags.Chaos,
			'w': Tags.Word,
			't': Tags.Translocation
		}

		self.reverse_tag_keys = {v: k.upper() for k, v in self.tag_keys.items()}

		self.tag_filter = set()

		self.path = []

		self.effect_queue = []
		self.sound_effects = {}

		self.ui_tiles = {}
		self.red_ui_tiles = {}
		self.load_ui_tiles()

		self.examine_icon_surface = pygame.Surface((16, 16))
		self.char_panel_examine_lines = {}

		self.second_step = False

		self.path_delay = 0

		self.option_selection = OPTION_SOUND_VOLUME

		self.message = None

		self.gameover_frames = 0
		self.gameover_tiles = None

		self.deploy_anim_frames = 0

		self.title_image = get_image(['title'])
		self.title_frame = 0

		self.los_image = get_image(['UI', 'los'])
		self.hostile_los_image = get_image(['UI', 'hostile_los'])

		self.shop_scroll_frame = 0

		self.ui_rects = []

		self.threat_zone = None
		self.last_threat_highlight = None

		icon = get_image(['UI', 'icon'])
		pygame.display.set_icon(icon)

		self.repeat_keys = {}

		fill_color = (255, 255, 255, 150)
		self.tile_targetable_image = get_image(['UI', 'square_valid_animated'])
		self.tile_targetable_image.fill(fill_color, special_flags=pygame.BLEND_RGBA_MIN)
		self.tile_impacted_image = get_image(['UI', 'square_impacted_animated'])
		self.tile_impacted_image.fill(fill_color, special_flags=pygame.BLEND_RGBA_MIN)
		self.tile_targeted_image = get_image(['UI', 'square_targeted_animated'])
		self.tile_targeted_image.fill(fill_color, special_flags=pygame.BLEND_RGBA_MIN)
		self.tile_invalid_target_image = get_image(['UI', 'square_invalid_target_animated'])
		self.tile_invalid_target_image.fill(fill_color, special_flags=pygame.BLEND_RGBA_MIN)
		self.tile_invalid_target_in_range_image = get_image(['UI', 'square_invalid_target_animated']).copy()
		self.tile_invalid_target_in_range_image.fill((255, 255, 255, 45), special_flags=pygame.BLEND_RGBA_MIN)

		self.reminisce_folder = None
		self.reminisce_index = 0

		self.abort_to_spell_shop = False


		self.examine_icon_subframe = 0
		self.examine_icon_frame = 0

		self.cast_fail_frames = 0
		#pygame.mouse.set_visible(False)

		self.combat_log_offset = 0
		self.combat_log_turn = 0
		self.combat_log_level = 0

		self.confirm_text = None
		self.confirm_yes = None
		self.confirm_no = None

		self.next_message = None
		self.fast_forward = False

	def resize_window(self, evt):
		if not self.windowed:
			return

		size = (max(evt.size[0], RENDER_WIDTH // 2), max(evt.size[1], RENDER_HEIGHT // 2))
		pygame.display.set_mode(size, pygame.RESIZABLE)

	def get_draw_scale(self):

		h_scale = pygame.display.get_surface().get_width() // RENDER_WIDTH
		v_scale = pygame.display.get_surface().get_height() // RENDER_HEIGHT

		# We will attempt to draw at half scale if we cannot even draw at 1.0 scale.
		# I currently see no reason to try for .25 scale but perhaps it is worth checking if .25 is better than .5 in this situation.
		scale = min(h_scale, v_scale)
		scale = max(scale, .5)
		return scale

	def get_draw_margins(self):
		scale = self.get_draw_scale()
		x_margin = int(pygame.display.get_surface().get_width() - RENDER_WIDTH * scale) // 2
		y_margin = int(pygame.display.get_surface().get_height() - RENDER_HEIGHT * scale) // 2

		return x_margin, y_margin

	def draw_screen(self, color=None):
		# Do not try to draw the screen when the game is minimized
		if not pygame.display.get_active():
			return

		#if pygame.display.get_width() == 0:
			#return

		margins = self.get_draw_margins()
		scale = self.get_draw_scale()

		if False:
			btns = pygame.mouse.get_pressed()
			if btns[0]:
				if self.state == STATE_LEVEL:
					cursor = get_image(['UI', 'cursor_down'])
				else:
					cursor = get_image(['UI', 'cursor_down_menu'])
			elif btns[2]:
				if self.state == STATE_LEVEL:
					cursor = get_image(['UI', 'cursor_down_r'])
				else:
					cursor = get_image(['UI', 'cursor_down_r_menu'])
			else:
				if self.state == STATE_LEVEL:
					cursor = get_image(['UI', 'cursor'])
				else:
					cursor = get_image(['UI', 'cursor_menu'])
			self.screen.blit(cursor, self.get_mouse_pos())

		if scale == 1:
			pygame.display.get_surface().blit(self.screen, self.get_draw_margins())
		else:
			subsurf = pygame.display.get_surface().subsurface(margins[0], margins[1], int(self.screen.get_width() * scale), int(self.screen.get_height() * scale))
			pygame.transform.scale(self.screen, subsurf.get_size(), subsurf)

		pygame.display.flip()

	def get_surface_pos(self, surf):
		if surf == self.middle_menu_display:
			return (self.h_margin, 0)
		elif surf == self.examine_display:
			return (self.screen.get_width() - self.h_margin, 0)
		else:
			return (0, 0)

	def load_ui_tiles(self):

		ui_color = Color(255, 255, 255)


		for red in [True, False]:
			if red:
				tiles = self.red_ui_tiles
			else:
				tiles = self.ui_tiles

			if red:
				edge_fn = "edge_red.png"
				corner_fn = "corner_red.png"
			else:
				edge_fn = "edge.png"
				corner_fn = "corner.png"

			edge_path = os.path.join("rl_data", "UI", edge_fn)
			edge = pygame.image.load(edge_path)

			corner_path = os.path.join("rl_data", "UI", corner_fn)
			corner = pygame.image.load(corner_path)

			tiles[UI_RIGHT] = edge
			tiles[UI_LEFT] = pygame.transform.rotate(edge, 180)
			tiles[UI_TOP] = pygame.transform.rotate(edge, 90)
			tiles[UI_BOTTOM] = pygame.transform.rotate(edge, -90)

			tiles[UI_UPPER_RIGHT] = corner
			tiles[UI_UPPER_LEFT] = pygame.transform.rotate(corner, 90)
			tiles[UI_LOWER_LEFT] = pygame.transform.rotate(corner, 180)
			tiles[UI_LOWER_RIGHT] = pygame.transform.rotate(corner, -90)



	def play_sound(self, sound_name):
		if not self.can_play_sound:
			return

		if sound_name not in self.sound_effects:
			filename = os.path.join("rl_data", "soundFX", sound_name) + '.wav'
			self.sound_effects[sound_name] = pygame.mixer.Sound(filename)
		sound = self.sound_effects[sound_name]

		if 'hit_4' in sound_name:
			self.hit_player_sound_channel.play(sound)
		elif 'hit' in sound_name:
			self.hit_sound_channel.play(sound)
		elif 'step' in sound_name:
			self.step_sound_channel.play(sound)
		elif 'death' in sound_name:
			self.death_sound_channel.play(sound)
		elif 'sorcery_enemy' in sound_name:
			self.cast_sound_channel.play(sound)
		elif 'menu' in sound_name:
			self.ui_sound_channel.play(sound)
		else:
			self.misc_sound_channel.play(sound)

	def play_music(self, track_name):
		if not self.can_play_sound:
			return

		music_path = os.path.join('rl_data', 'music', track_name + '.wav')
		pygame.mixer.music.load(music_path)
		self.adjust_volume(0, 'music')
		pygame.mixer.music.play(-1)


	def deploy(self, p):

		if self.game.try_deploy(self.deploy_target.x, self.deploy_target.y):

			self.deploy_anim_frames = 0
			self.make_level_screenshot()

			self.game.p1.Anim = None
			self.effects = []

			if self.game.level_num < LAST_LEVEL:
				self.play_sound("victory_new")
			else:
				self.play_sound("victory_bell")
				self.play_music("mordred_theme")

			self.deploy_target = None


			SteamAdapter.set_presence_level(self.game.level_num)

			prev_max = SteamAdapter.get_stat('r')
			if self.game.level_num > prev_max:
				# Set reached level
				SteamAdapter.set_stat('r', self.game.level_num)

		else:
			self.play_sound("menu_abort")

	def on_level_finish(self):

		# Log obj graph
		mem_log.debug("After level %d:" % self.game.level_num)
		import objgraph
		for t, c in objgraph.most_common_types():
			mem_log.debug("%s: %d" % (t, c))
		mem_log.debug('\n')

		# Clear examine target to show summary
		self.examine_target = None
		self.make_level_end_screenshot()

		if not (self.game.gameover or self.game.victory):
			self.game.save_game()

		if self.game.level_num == LAST_LEVEL:
			wins = SteamAdapter.get_stat('w')
			wins += 1
			SteamAdapter.set_stat('w', wins)

			streak = SteamAdapter.get_stat('s')
			streak += 1
			SteamAdapter.set_stat('s', streak)

			if self.game.trial_name:
				SteamAdapter.set_trial_complete(self.game.trial_name)

		self.play_sound("learn_spell_or_skill")


	def choose_spell(self, spell):
		if spell.show_tt:
			self.examine_target = spell

		if self.deploy_target:
			self.play_sound("menu_abort")
			return

		if spell.max_charges and not spell.cur_charges:
			self.play_sound("menu_abort")
			self.cast_fail_frames = SPELL_FAIL_LOCKOUT_FRAMES
			return

		prev_spell = self.cur_spell
		self.cur_spell = spell

		def can_tab_target(t):
			unit = self.game.cur_level.get_unit_at(t.x, t.y)
			if unit is None:
				return False
			return are_hostile(self.game.p1, unit)

		self.play_sound("menu_confirm")
		#p = self.get_mouse_level_point()
		#if p and spell.can_cast(*p):
		#   self.cur_spell_target = p
		self.targetable_tiles = spell.get_targetable_tiles()
		if hasattr(spell, 'get_tab_targets'):
			self.tab_targets = spell.get_tab_targets()
		else:
			self.tab_targets = [t for t in self.cur_spell.get_targetable_tiles() if can_tab_target(t)]
			self.tab_targets.sort(key=lambda t: distance(t, self.game.p1))

		self.tab_targets = [Point(t.x, t.y) if not isinstance(t, Point) else t for t in self.tab_targets]

		if self.options['smart_targeting']:
			# If the unit we last targeted is dead, dont target the empty space where it died
			if isinstance(self.cur_spell_target, Unit):
				if not self.cur_spell_target.is_alive():
					self.cur_spell_target = None

			# If we dont have a target, target the first tab target option if it exists
			if not self.cur_spell_target:
				if self.tab_targets:
					self.cur_spell_target = self.tab_targets[0]
				else:
					self.cur_spell_target = Point(self.game.p1.x, self.game.p1.y)
		else:
			if not prev_spell:
				self.cur_spell_target = Point(self.game.p1.x, self.game.p1.y)


	def abort_cur_spell(self):
		self.cur_spell = None
		self.play_sound("menu_abort")

	def cast_cur_spell(self):
		success = self.game.try_cast(self.cur_spell, self.cur_spell_target.x, self.cur_spell_target.y)
		if not success:
			self.play_sound('menu_abort')
		#if self.examine_target == self.cur_spell:
			#self.examine_target = None
		self.cur_spell = None
		unit = self.game.cur_level.get_unit_at(self.cur_spell_target.x, self.cur_spell_target.y)
		if unit:
			self.cur_spell_target = unit


	def cycle_tab_targets(self):

		target = self.deploy_target or self.cur_spell_target
		if not self.tab_targets:
			return

		if target in self.tab_targets:
			index = self.tab_targets.index(target)
			new_index = (index + 1) % len(self.tab_targets)
		else:
			new_index = 0

		target = self.tab_targets[new_index]

		if self.deploy_target:
			self.deploy_target = target
		if self.cur_spell_target:
			self.cur_spell_target = target

		self.try_examine_tile(target)


	def get_tileset_color(self, tileset):
		if not hasattr(self, 'tileset_colors'):
			self.tileset_colors = {}

		if tileset not in self.tileset_colors:
			floor = self.floor_tiles[tileset][0]

			for i in range(floor.get_width()):
				for j in range(floor.get_height()):
					c = floor.get_at((i, j))
					if c.a == 0:
						continue
					if c.r or c.g or c.b:
						self.tileset_colors[tileset] = (c.r, c.g, c.b, 255)

		return self.tileset_colors[tileset]

	def get_filled_sprite(self, sprite, color):
		if not hasattr(self, 'filled_sprites'):
			self.filled_sprites = {}
		key = (sprite, color)
		if key not in self.filled_sprites:
			surf = pygame.Surface((sprite.get_width(), sprite.get_height()), flags=pygame.SRCALPHA)
			surf.fill((0, 0, 0, 0))

			for i in range(sprite.get_width()):
				for j in range(sprite.get_height()):
					cur_source_color = sprite.get_at((i, j))

					if cur_source_color.r == cur_source_color.g == cur_source_color.b == 0 and cur_source_color.a > 0:
						surf.set_at((i, j), cur_source_color)
					elif cur_source_color.a == 0:
						continue
					else:
						surf.set_at((i, j), color)

			self.filled_sprites[key] = surf

		return self.filled_sprites[key]

	def load_chasm_sprites(self):
		self.chasm_sprites = defaultdict(lambda: [])

		for left in [0, 1]:
			for right in [0, 1]:
				for up in [0, 1]:
					for down in [0, 1]:
						filename = "chasm"
						if left:
							filename += "_left"
						if right:
							filename += "_right"
						if up:
							filename += "_up"
						if down:
							filename += "_down"
						for i in range(1, 10):
							cur_filename = filename + "_%d.png" % i

							path = os.path.join("rl_data", "tiles", "chasm", cur_filename)
							if os.path.exists(path):
								cur_img = pygame.image.load(path)
								self.chasm_sprites[(left, right, up, down)].append(cur_img)

		self.chasm_corners = defaultdict(lambda: [])
		for i in range(1, 10):
			cur_filename = "chasm_corner_%d.png" % i
			path = os.path.join("rl_data", "tiles", "chasm", cur_filename)
			if os.path.exists(path):
				image = pygame.image.load(path)
				self.chasm_corners[UI_UPPER_LEFT].append(image)
				self.chasm_corners[UI_LOWER_LEFT].append(pygame.transform.rotate(image, 90))
				self.chasm_corners[UI_LOWER_RIGHT].append(pygame.transform.rotate(image, 180))
				self.chasm_corners[UI_UPPER_RIGHT].append(pygame.transform.rotate(image, 270))

	def get_star_sprites(self, stars_name):
		if not hasattr(self, 'star_tiles'):
			self.star_tiles = {}
		if stars_name not in self.star_tiles:
			self.star_tiles[stars_name] = []

			i = 1
			while True:
				cur_filename = "%d.png" % i
				path = os.path.join("rl_data", "tiles", "stars", stars_name, cur_filename)

				if not os.path.exists(path):
					break
				else:
					self.star_tiles[stars_name].append(pygame.image.load(path))
				i += 1

		return self.star_tiles[stars_name]

	def load_wall_sprites(self):
		self.wall_tiles = {}
		filenames = ['wall']
		for i in range(100):
			filenames += ['wall_%d' % i]
		for biome in all_biomes:
			self.wall_tiles[biome.tileset] = []
			paths = [os.path.join("rl_data", "tiles", "wall", "%s wall" % biome.tileset, f + '.png') for f in filenames]
			for p in paths:
				if os.path.exists(p):
					self.wall_tiles[biome.tileset].append(pygame.image.load(p))

	def load_floor_sprites(self):
		self.floor_tiles = {}
		filenames = ['floor']
		for i in range(10):
			filenames += ['floor_%d' % i]

		for biome in all_biomes:
			self.floor_tiles[biome.tileset] = []
			paths = [os.path.join("rl_data", "tiles", "floor", "%s floor" % biome.tileset, f + '.png') for f in filenames]
			for p in paths:
				if os.path.exists(p):
					self.floor_tiles[biome.tileset].append(pygame.image.load(p))

	def get_display_level(self):
		return self.game.next_level or self.game.cur_level

	def make_ascii_sprite_sheet(self, ascii_sprite):
		return SpriteSheet(ascii_sprite)

	def get_sprite_sheet(self, asset, fill_color=None, lair_colors=None):
		key = (tuple(asset), fill_color, lair_colors)

		if key not in self.sprite_sheets:
			self.sprite_sheets[key] = SpriteSheet(asset, fill_color, lair_colors)

		return self.sprite_sheets[key]

	def get_anim(self, unit, forced_name=None):

		# Find the asset name
		asset = get_unit_asset(unit, forced_name)

		# Determine lair colors for lairs
		lair_colors = None
		if unit.is_lair:
			example_monster = unit.buffs[0].example_monster
			example_sprite_name = example_monster.get_asset_name()
			example_sprite = self.get_sprite_sheet(get_unit_asset(example_monster))
			lair_colors = example_sprite.get_lair_colors()

		sprite = self.get_sprite_sheet(asset, lair_colors=lair_colors)

		return UnitSprite(unit, sprite, view=self)

	def load_effect_images(self):
		self.effect_images = {}
		self.minor_effect_images = {}
		for tag in Tags:
			asset = ['effects', tag.name.lower()]

			if tag.asset:
				asset = tag.asset

			# Minor asset is always the major asset but with _0 apended to the filename (before the extension)
			minor_asset = asset[0:-1] + [asset[-1] + '_0']

			image = get_image(asset)
			if image:
				self.effect_images[tag.color.to_tup()] = image

			minor_image = get_image(minor_asset)
			if minor_image:
				self.minor_effect_images[tag.color.to_tup()] = minor_image

	def get_filled_effect_image(self, effect_color, fill_color):
		key = (effect_color, fill_color)
		if key not in self.effect_images:
			image = self.effect_images[effect_color].copy()
			image.fill(fill_color, special_flags=pygame.BLEND_RGBA_MIN)
			self.effect_images[key] = image
			return image
		else:
			return self.effect_images[key]

	def queue_effect(self, new_effect):
		self.effect_queue.append(new_effect)

	def advance_queued_effects(self):

		effect_tiles = set((e.x, e.y) for e in self.effects)
		#level_effect_tiles = set((e.x, e.y) for e in self.get_display_level().effects)
		level_effect_tiles = set()

		for effect in list(self.effect_queue):
			effect_point = (effect.x, effect.y)
			if effect_point not in effect_tiles:
				self.effects.append(effect)
				self.effect_queue.remove(effect)
				effect_tiles.add((effect.x, effect.y))

	def get_effect(self, effect, color=None):
		# Go from level effect to PygameView effects
		if effect.color == Tags.Sound_Effect.color:
			# So bad but so good
			assert(isinstance(effect.end_color, str))
			self.play_sound(effect.end_color)
			return None
		elif effect.color == Tags.Leap.color:
			return LeapEffect(effect.x, effect.y, effect.leap_unit, effect.end_color, effect.frames)
		elif effect.color == Tags.Arrow.color:
			sprite = get_image(['effects', 'proj', effect.proj_name])
			return ProjectileEffect(effect.x, effect.y, sprite, effect.proj_origin, effect.proj_dest, effect.end_color)
		elif effect.color.to_tup() in self.effect_images:
			if effect.end_color and effect.end_color != Color(0, 0, 0):
				image = self.get_filled_effect_image(effect.color.to_tup(), effect.end_color.to_tup())
			else:
				if effect.minor and effect.color.to_tup() in self.minor_effect_images:
					image = self.minor_effect_images[effect.color.to_tup()]
				else:
					image = self.effect_images[effect.color.to_tup()]
			return SimpleSprite(effect.x, effect.y, image, speed=1)
		print("No effect found for %s" % effect.color)
		return EffectRect(effect.x, effect.y, effect.color, effect.frames)

	def get_mouse_rel(self):
		return self.mouse_dx, self.mouse_dy

	def get_mouse_pos(self):
		# Translate current absolute mouse pos to position on the self.screen surface
		# Account for differing resolutions
		disp = pygame.display.get_surface()

		scale = self.get_draw_scale()
		margins = self.get_draw_margins()

		mx, my = pygame.mouse.get_pos()

		mx = round((mx - margins[0]) / scale)
		my = round((my - margins[1]) / scale)

		return mx, my

	def get_mouse_level_point(self):
		# Get the integer coordinates of the mouse on the battlefield if it is on the battlefield
		x, y = self.get_mouse_pos()
		x -= self.h_margin

		x //= 2*SPRITE_SIZE
		y //= 2*SPRITE_SIZE

		if x < 0 or y < 0:
			return None
		if x >= LEVEL_SIZE or y >= LEVEL_SIZE:
			return None

		return Point(x, y)

	def try_move(self, movedir):
		result = self.game.try_move(*movedir)
		if result:
			self.play_sound("step_player")
			self.second_step = 1 - self.second_step
		return result

	def try_examine_tile(self, point):
		if point:
			tile = self.get_display_level().tiles[point.x][point.y]
			self.examine_target = (tile.unit if tile.unit != self.game.p1 else None) or tile.cloud or tile.prop

	def is_animating_deploy(self):
		return self.deploy_anim_frames not in (0, self.get_max_deploy_frames())

	def can_execute_inputs(self):
		return self.cast_fail_frames <= 0 and self.game.is_awaiting_input() and not self.is_animating_deploy()

	def move_examine_target(self, movedir):
		# if is spell
		if isinstance(self.examine_target, Spell):
			if movedir == 1:
				self.examine_target = self.examine_target.spell_upgrades[0]
			else:
				self.examine_target = self.examine_target.spell_upgrades[-1]
		# if it is a spell upgrade
		elif hasattr(self.examine_target, 'prereq') and isinstance(self.examine_target.prereq, Spell):
			# We assume the spell upgrade is in the spells list of spell upgrades
			assert(self.examine_target in self.examine_target.prereq.spell_upgrades)

			cur_idx = self.examine_target.prereq.spell_upgrades.index(self.examine_target)
			cur_idx += movedir
			cur_idx = cur_idx % (len(self.examine_target.prereq.spell_upgrades) + 1)

			if cur_idx == len(self.examine_target.prereq.spell_upgrades):
				self.examine_target = self.examine_target.prereq
			else:
				self.examine_target = self.examine_target.prereq.spell_upgrades[cur_idx]

	def process_examine_panel_input(self):
		for evt in self.events:
			if not evt.type == pygame.KEYDOWN:
				continue

			if evt.key in self.key_binds[KEY_BIND_NEXT_EXAMINE_TARGET]:
				self.move_examine_target(1)
			elif evt.key in self.key_binds[KEY_BIND_PREV_EXAMINE_TARGET]:
				self.move_examine_target(-1)


	def process_level_input(self):

		if self.cast_fail_frames:
			self.cast_fail_frames -= 1

		if any(evt.type == pygame.KEYDOWN for evt in self.events) and self.gameover_frames > 8 and not self.gameover_tiles:
			self.enter_reminisce()
			return

		level_point = self.get_mouse_level_point()
		movedir = None
		keys = pygame.key.get_pressed()

		if self.can_execute_inputs() and self.path:
			if not self.path_delay:
				next_point = self.path[0]
				self.path = self.path[1:]
				movedir = Point(next_point.x - self.game.p1.x, next_point.y - self.game.p1.y)
				self.try_move(movedir)
				self.path_delay = MAX_PATH_DELAY
			else:
				self.path_delay -= 1

		# Disable ff after 1 round
		if self.can_execute_inputs() and self.fast_forward:
			self.fast_forward = False

		for evt in self.events:
			if not evt.type == pygame.KEYDOWN:
				continue

			# Cancel path on key down
			# do this here instead of by checking pressed keys to deal with pygame alt tab bug
			self.path = []

			if evt.key == pygame.K_BACKSPACE:
				self.fast_forward = True

			if self.can_execute_inputs():
				if evt.key in self.key_binds[KEY_BIND_UP]:
					movedir = Point(0, -1)
				if evt.key in self.key_binds[KEY_BIND_DOWN]:
					movedir = Point(0, 1)
				if evt.key in self.key_binds[KEY_BIND_LEFT]:
					movedir = Point(-1, 0)
				if evt.key in self.key_binds[KEY_BIND_RIGHT]:
					movedir = Point(1, 0)
				if evt.key in self.key_binds[KEY_BIND_DOWN_RIGHT]:
					movedir = Point(1, 1)
				if evt.key in self.key_binds[KEY_BIND_DOWN_LEFT]:
					movedir = Point(-1, 1)
				if evt.key in self.key_binds[KEY_BIND_UP_LEFT]:
					movedir = Point(-1, -1)
				if evt.key in self.key_binds[KEY_BIND_UP_RIGHT]:
					movedir = Point(1, -1)

				if evt.key in self.key_binds[KEY_BIND_CONFIRM]:
					if self.cur_spell:
						self.cast_cur_spell()
					elif self.game.deploying:
						self.deploy(level_point)

				if evt.key in self.key_binds[KEY_BIND_PASS]:
					if not self.cur_spell:
						self.game.try_pass()

				for bind in range(KEY_BIND_SPELL_1, KEY_BIND_SPELL_10+1):
					if evt.key in self.key_binds[bind] and not self.game.deploying:
						index = bind - KEY_BIND_SPELL_1

						for modifier in self.key_binds[KEY_BIND_MODIFIER_1]:
							if modifier and keys[modifier]:
								index += 10

						# Item
						is_item = False
						for modifier in self.key_binds[KEY_BIND_MODIFIER_2]:
							if modifier and keys[modifier]:
								is_item = True

						if is_item:
							if len(self.game.p1.items) > index:
								self.choose_spell(self.game.p1.items[index].spell)
						else:
							if len(self.game.p1.spells) > index:
								self.choose_spell(self.game.p1.spells[index])

				if evt.key in self.key_binds[KEY_BIND_WALK]:
					if not any(are_hostile(u, self.game.p1) for u in self.game.cur_level.units):
						spell = WalkSpell()
						spell.caster = self.game.p1
						self.choose_spell(spell)

				if evt.key in self.key_binds[KEY_BIND_VIEW]:
					spell = LookSpell()
					spell.caster = self.game.p1
					self.choose_spell(spell)

				if evt.key in self.key_binds[KEY_BIND_CHAR]:
					self.open_char_sheet()
					self.char_sheet_select_index = 0

				if evt.key in self.key_binds[KEY_BIND_SPELLS]:
					self.open_shop(SHOP_TYPE_SPELLS)

				if evt.key in self.key_binds[KEY_BIND_SKILLS]:
					self.open_shop(SHOP_TYPE_UPGRADES)

				if evt.key in self.key_binds[KEY_BIND_TAB] and (self.cur_spell or self.deploy_target):
					self.cycle_tab_targets()

				if evt.key in self.key_binds[KEY_BIND_HELP]:
					self.show_help()

				if evt.key in self.key_binds[KEY_BIND_AUTOPICKUP] and all(not are_hostile(self.game.p1, u) for u in self.game.cur_level.units):
					self.autopickup()

				if evt.key in self.key_binds[KEY_BIND_INTERACT] and self.game.cur_level.tiles[self.game.p1.x][self.game.p1.y].prop:
					self.game.cur_level.tiles[self.game.p1.x][self.game.p1.y].prop.on_player_enter(self.game.p1)

					if self.game.cur_level.cur_shop:
						self.open_shop(SHOP_TYPE_SHOP)

					if self.game.cur_level.cur_portal and not self.game.deploying:
						self.game.enter_portal()

				if evt.key in self.key_binds[KEY_BIND_ABORT]:
					if self.cur_spell:
						self.abort_cur_spell()
					elif self.game.deploying:
						self.deploy_target = None
						self.examine_target = None
						self.game.try_abort_deploy()
						self.play_sound("menu_abort")
					else:
						self.open_options()

				if evt.key in self.key_binds[KEY_BIND_MESSAGE_LOG]:
					self.open_combat_log()

			global cheats_enabled
			if can_enable_cheats and evt.key == pygame.K_z and keys[pygame.K_LSHIFT] and keys[pygame.K_LCTRL]:
				cheats_enabled = True

			if cheats_enabled:
				if evt.key == pygame.K_t and level_point:
					if self.game.cur_level.can_move(self.game.p1, level_point.x, level_point.y, teleport=True):
						self.game.cur_level.act_move(self.game.p1, level_point.x, level_point.y, teleport=True)

				if evt.key == pygame.K_x:
					self.game.p1.xp += 100

				if evt.key == pygame.K_y:
					self.game.p1.xp -= 10

				if evt.key == pygame.K_h:
					self.game.p1.max_hp += 250
					self.game.p1.cur_hp += 250

				if evt.key == pygame.K_k:
					for unit in list(self.game.cur_level.units):
						if unit != self.game.p1:
							unit.kill()

				if evt.key == pygame.K_g:
					self.game.p1.kill()

				if evt.key == pygame.K_r:
					for spell in self.game.p1.spells:
						spell.cur_charges = spell.get_stat('max_charges')

				if evt.key == pygame.K_i:
					for i, c in all_consumables:
						self.game.p1.add_item(i())

				if evt.key == pygame.K_s:
					self.game.save_game('./cheat_save')

				if evt.key == pygame.K_l:
					self.game = continue_game('cheat_save')

				if evt.key == pygame.K_c and keys[pygame.K_LSHIFT]:
					x = self.game.cur_level.tiles[9999][9999]

				if evt.key == pygame.K_h:
					self.game.p1.cur_hp = self.game.p1.max_hp

				if evt.key == pygame.K_d:
					gates = [tile.prop for tile in self.game.cur_level.iter_tiles() if isinstance(tile.prop, Portal)]
					for gate in gates:
						gate.level_gen_params = LevelGenerator(self.game.level_num + 1, self.game)
						gate.description = gate.level_gen_params.get_description()
						gate.next_level = None
						self.game.cur_level.flash(gate.x, gate.y, Tags.Arcane.color)

				if evt.key == pygame.K_f:
					self.examine_target = self.get_display_level().gen_params

				if evt.key == pygame.K_v:
					to_blit = self.screen
					scale = 1
					w = to_blit.get_width() * scale
					h = to_blit.get_height() * scale
					surf = pygame.transform.scale(to_blit, (w, h))

					for i in range(100):
						path = "screencap\\ss_%d.png" % i
						if not os.path.exists(path):
							pygame.image.save(surf, path)
							break

				if evt.key == pygame.K_EQUALS:
					self.game.level_num += 1

				if evt.key == pygame.K_MINUS:
					self.game.level_num -= 1

				if evt.key == pygame.K_m:
					for monster, cost in spawn_options:
						unit = monster()
						p = self.game.cur_level.get_summon_point(0, 0, radius_limit=40)
						if p:
							self.game.cur_level.add_obj(unit, p.x, p.y)

				if evt.key == pygame.K_b and level_point:
					unit = Mordred()
					p = self.game.cur_level.get_summon_point(level_point.x, level_point.y)
					if p:
						self.game.cur_level.add_obj(unit, p.x, p.y)

				if evt.key == pygame.K_p:
					import pdb
					pdb.set_trace()

				if evt.key == pygame.K_o and level_point:
					self.game.cur_level.add_obj(ManaDot(), level_point.x, level_point.y)

				if evt.key == pygame.K_q and level_point:
					points = [p for p in self.game.cur_level.get_points_in_ball(level_point.x, level_point.y, 7)]
					for s in new_shrines:
						p = points.pop()
						shrine = make_shrine(s[0](), self.game.p1)
						self.game.cur_level.add_obj(shrine, p.x, p.y)

		if movedir:
			repeats = 1
			if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
				repeats = 4
			if self.cur_spell:
				for _ in range(repeats):
					new_spell_target = Point(self.cur_spell_target.x + movedir.x, self.cur_spell_target.y + movedir.y)
					if self.game.cur_level.is_point_in_bounds(new_spell_target):
						self.cur_spell_target = new_spell_target
						self.try_examine_tile(new_spell_target)
			elif self.game.deploying and self.deploy_target:
				for _ in range(repeats):
					new_point = Point(self.deploy_target.x + movedir.x, self.deploy_target.y + movedir.y)
					if self.game.next_level.is_point_in_bounds(new_point):
						self.deploy_target = new_point
						self.try_examine_tile(new_point)
			else:
				self.try_move(movedir)
				self.cur_spell_target = None


		mouse_dx, mouse_dy = self.get_mouse_rel()
		if mouse_dx or mouse_dy:
			if level_point:
				if self.cur_spell:
					self.cur_spell_target = level_point
				if self.game.deploying:
					self.deploy_target = level_point

				self.try_examine_tile(level_point)

		for click in self.events:
			if click.type != pygame.MOUSEBUTTONDOWN:
				continue

			# Cancel click to move on subsequent clicks
			self.path = []

			if self.gameover_frames > 8 and not self.gameover_tiles:
				self.enter_reminisce()
				return

			mx, my = self.get_mouse_pos()
			if mx < self.h_margin:
				self.process_click_character(click.button, mx, my)

			if click.button == pygame.BUTTON_LEFT and self.can_execute_inputs():
				if self.cur_spell and click.button == pygame.BUTTON_LEFT and level_point:
					self.cur_spell_target = level_point
					self.cast_cur_spell()
				elif self.game.deploying and level_point:
					self.deploy_target = level_point
					self.deploy(self.deploy_target)
				elif level_point and all(u.team == TEAM_PLAYER for u in self.game.cur_level.units):
					self.path = self.game.cur_level.find_path(self.game.p1, level_point, self.game.p1, pythonize=True, cosmetic=True)
				elif level_point and distance(level_point, self.game.p1, diag=True) >= 1:
					path = self.game.cur_level.find_path(self.game.p1, level_point, self.game.p1, pythonize=True, cosmetic=True)
					if path:
						movedir = Point(path[0].x - self.game.p1.x, path[0].y - self.game.p1.y)
						self.try_move(movedir)
				elif level_point and distance(level_point, self.game.p1) == 0:
					self.game.try_pass()

			if click.button == pygame.BUTTON_RIGHT:
				if self.cur_spell:
					self.abort_cur_spell()
				if self.game.deploying:
					self.deploy_target = None
					self.examine_target = None
					self.game.try_abort_deploy()
					self.play_sound("menu_abort")

			# Only process one mouse evt per frame
			#break

	def autopickup(self):
		props = [tile.prop for tile in self.game.cur_level.iter_tiles() if tile.prop]
		pickups = [p for p in props if isinstance(p, ManaDot) or isinstance(p, ItemPickup) or isinstance(p, HeartDot) or isinstance(p, SpellScroll)]
		destinations = [p for p in pickups if self.game.cur_level.find_path(self.game.p1, p, self.game.p1, pythonize=True)]


		full_path = []
		prev_dest = self.game.p1
		while destinations:
			destinations.sort(key=lambda d: distance(prev_dest, d), reverse=True)
			d = destinations.pop()
			path = self.game.cur_level.find_path(prev_dest, d, self.game.p1, pythonize=True)
			if path:
				full_path += path
				prev_dest = d

		self.path = full_path

	def draw_char_sheet(self):
		self.middle_menu_display.fill((0, 0, 0))
		self.draw_panel(self.middle_menu_display)

		# Spells
		spell_x_offset = self.border_margin + 18
		cur_x = spell_x_offset
		cur_y = self.linesize
		self.draw_string("法术", self.middle_menu_display, cur_x, cur_y)

		m_loc = self.get_mouse_pos()

		cur_y += self.linesize
		cur_y += self.linesize
		spell_index = 0

		col_width = self.middle_menu_display.get_width() // 2 - 2*self.border_margin

		#Spells
		for spell in self.game.p1.spells:
			self.draw_string(spell.name, self.middle_menu_display, cur_x, cur_y, mouse_content=spell, content_width=col_width)
			cur_y += self.linesize

			# Upgrades
			for upgrade in sorted((b for b in self.game.p1.buffs if isinstance(b, Upgrade) and b.prereq == spell), key=lambda b: b.shrine_name is None):
				fmt = upgrade.name
				if upgrade.shrine_name:
					color = COLOR_XP
					fmt = upgrade.name.replace('(%s)' % spell.name, '')
				else:
					color = (255, 255, 255)
				self.draw_string(' ' + fmt, self.middle_menu_display, cur_x, cur_y, mouse_content=upgrade, content_width=col_width, color=color)

				cur_y += self.linesize

			available_upgrades = len([b for b in spell.spell_upgrades if not b.applied])
			if available_upgrades:
				self.draw_string(' %d 项可选升级' % available_upgrades, self.middle_menu_display, cur_x, cur_y)
				cur_y += self.linesize



			spell_index += 1


		learn_color = (255, 255, 255) if len(self.game.p1.spells) < 20 else (170, 170, 170)

		self.draw_string("学习法术 (S)", self.middle_menu_display, cur_x, cur_y, learn_color, mouse_content=LEARN_SPELL_TARGET, content_width=col_width)

		# Skills
		skill_x_offset = self.middle_menu_display.get_width() // 2 + self.border_margin
		cur_x = skill_x_offset
		cur_y = self.linesize
		self.draw_string("能力", self.middle_menu_display, cur_x, cur_y)

		cur_y += self.linesize
		cur_y += self.linesize

		for skill in self.game.p1.get_skills():
			self.draw_string(skill.name, self.middle_menu_display, cur_x, cur_y, mouse_content=skill, content_width=col_width)
			cur_y += self.linesize
		self.draw_string("学习能力 (K)", self.middle_menu_display, cur_x, cur_y, mouse_content=LEARN_SKILL_TARGET,  content_width=col_width)

		self.screen.blit(self.middle_menu_display, (self.h_margin, 0))

	def open_shop(self, shop_type, spell=None):
		self.prev_state = self.state

		self.play_sound("menu_confirm")

		self.shop_open_examine_target = self.examine_target

		self.shop_type = shop_type
		if spell:
			self.shop_upgrade_spell = spell

		self.state = STATE_SHOP
		self.shop_page = 0

		shoptions = self.get_shop_options()
		if shoptions:
			self.examine_target = shoptions[0]

		self.tag_filter.clear()

	def open_abandon_prompt(self):
		self.state = STATE_CONFIRM
		self.confirm_text = "确认放弃本次冒险?"
		self.confirm_yes = self.confirm_abandon
		self.confirm_no = self.abort_abandon
		self.examine_target = False

	def confirm_abandon(self):
		SteamAdapter.set_stat('s', 0)
		SteamAdapter.set_stat('l', SteamAdapter.get_stat('l') + 1)
		abort_game()
		self.play_sound("menu_confirm")
		self.state = STATE_TITLE
		self.examine_target = TITLE_SELECTION_NEW

	def abort_abandon(self):
		self.play_sound("menu_confirm")
		self.state = STATE_TITLE
		self.examine_target = TITLE_SELECTION_LOAD

	def open_buy_prompt(self, item):
		self.play_sound("menu_confirm")
		self.state = STATE_CONFIRM
		self.confirm_yes = self.confirm_buy
		self.confirm_no = self.abort_buy

		self.chosen_purchase = item

		if self.shop_type == SHOP_TYPE_SHOP:
			attr = self.chosen_purchase.name.replace(self.chosen_purchase.shrine_name + ' ', '').lower()
			self.confirm_text = "对 %s 使用 %s 吗?" % (self.chosen_purchase.prereq.name, self.game.cur_level.cur_shop.name)
		else:
			cost = self.game.get_upgrade_cost(self.chosen_purchase)
			self.confirm_text = "支付 %s 点 SP, 学习 %s, 确定吗?" % (cost, self.chosen_purchase)

		# Default to no (?)
		self.examine_target = False

	def confirm_buy(self):

		success = self.game.try_shop(self.chosen_purchase)
		if not success:
			return

		if self.shop_type in [SHOP_TYPE_SPELLS, SHOP_TYPE_UPGRADES]:
			self.char_sheet_select_index += 1

		self.abort_to_spell_shop = False
		self.close_shop()

	def abort_buy(self):
		self.state = STATE_SHOP
		self.chosen_purchase = None
		self.play_sound("menu_abort")

	def draw_confirm(self):
		self.middle_menu_display.fill((0, 0, 0))

		cur_y = self.linesize * 5
		cur_x = (self.middle_menu_display.get_width() - self.font.size(self.confirm_text)[0]) // 2
		self.draw_string(self.confirm_text, self.middle_menu_display, cur_x, cur_y)

		cur_y += 2*self.linesize
		cur_x = (self.middle_menu_display.get_width()) // 4
		self.draw_string("是", self.middle_menu_display, cur_x, cur_y, mouse_content=True)

		cur_x = (self.middle_menu_display.get_width()) * 3 // 4 - self.font.size("No")[0]
		self.draw_string("否", self.middle_menu_display, cur_x, cur_y, mouse_content=False)

		self.screen.blit(self.middle_menu_display, (self.h_margin, 0))

	def process_confirm_input(self):

		mx, my = self.get_mouse_pos()
		for evt in self.events:
			if evt.type == pygame.KEYDOWN:
				if evt.key in self.key_binds[KEY_BIND_ABORT]:
					self.confirm_no()
				if evt.key in self.key_binds[KEY_BIND_CONFIRM]:
					if self.examine_target == True:
						self.confirm_yes()
					if self.examine_target == False:
						self.confirm_no()

				if evt.key in self.key_binds[KEY_BIND_LEFT] or evt.key in self.key_binds[KEY_BIND_RIGHT]:
					if self.examine_target in [True, False]:
						self.examine_target = not self.examine_target
					else:
						if evt.key in self.key_binds[KEY_BIND_LEFT]:
							self.examine_target = True
						else:
							self.examine_target = False

			elif evt.type == pygame.MOUSEBUTTONDOWN:

				if evt.button == pygame.BUTTON_LEFT:
					for r, c in self.ui_rects:
						if r.collidepoint((mx, my)):
							if c == True:
								self.confirm_yes()
							elif c == False:
								self.confirm_no()
				if evt.button == pygame.BUTTON_RIGHT:
					self.confirm_no()

	def open_key_rebind(self):
		self.state = STATE_REBIND
		self.examine_target = [0, 0]
		self.rebinding = False
		self.new_key_binds = dict(self.key_binds)

	def draw_key_rebind(self):
		cur_x = 0
		cur_y = 0

		col_xs = [100, 400, 700]


		self.draw_string("FUNCTION", self.screen, col_xs[0], cur_y)
		self.draw_string("MAIN KEY", self.screen, col_xs[1], cur_y)
		self.draw_string("SECONDARY KEY", self.screen, col_xs[2], cur_y)


		cur_y += self.linesize * 3

		for bind in range(KEY_BIND_MAX+1):
			cur_x = col_xs[0]
			self.draw_string("%s:" % key_names[bind], self.screen, cur_x, cur_y)

			key1, key2 = self.new_key_binds[bind]

			index = 0
			for k in [key1, key2]:
				cur_x = col_xs[index + 1]
				fmt = pygame.key.name(k) if k else "Unbound"
				content = [bind, index] if not self.rebinding else None
				cur_color = (0, 255, 0) if (self.rebinding and self.examine_target == [bind, index]) else (255, 255, 255)
				self.draw_string(fmt, self.screen, cur_x, cur_y, color=cur_color, mouse_content=content, content_width=170)
				index += 1

			cur_y += self.linesize

		cur_x = col_xs[0]
		cur_y += self.linesize*2


		self.draw_string("Reset to Default", self.screen, cur_x, cur_y, mouse_content=KEY_BIND_OPTION_RESET if not self.rebinding else None)
		cur_y += self.linesize
		self.draw_string("Done", self.screen, cur_x, cur_y, mouse_content=KEY_BIND_OPTION_ACCEPT if not self.rebinding else None)


	def process_key_rebind(self):
		# If there already is a selection- keys set the selection
		if self.rebinding:
			for evt in self.events:
				if evt.type == pygame.KEYDOWN:
					if evt.key in self.key_binds[KEY_BIND_ABORT]:
						self.rebinding = False
						continue

					key = evt.key
					if evt.key == pygame.K_BACKSPACE and self.examine_target[1] > 0:
						key = None

					# Check for dual keybinds
					for f, (k1, k2) in self.new_key_binds.items():
						if k1 == evt.key:
							self.new_key_binds[f] = (k2, None)
						if k2 == evt.key:
							self.new_key_binds[f] = (k1, None)

					cur_controls = self.new_key_binds[self.examine_target[0]]
					new_control = list(cur_controls)
					new_control[self.examine_target[1]] = key
					self.new_key_binds[self.examine_target[0]] = new_control
					self.rebinding = False
			return
		# If nothing is selected- enter sets selection, escape leaves the screen, clicks set selection, right click leaves
		else:
			for evt in self.events:
				if evt.type == pygame.KEYDOWN:
					contents = [c for (r, c) in self.ui_rects]
					cur_index = contents.index(self.examine_target)
					if evt.key in self.key_binds[KEY_BIND_UP]:

						if cur_index > 1:
							self.play_sound("menu_confirm")
						else:
							self.play_sound("menu_abort")


						# Skip by two if in the grid of primary-secondary keys
						if isinstance(self.examine_target, list):
							if self.examine_target[0] == 0:
								continue
							cur_index -= 1

						cur_index -= 1
						cur_index = max(0, cur_index)
						self.examine_target = contents[cur_index]
					if evt.key in self.key_binds[KEY_BIND_DOWN]:

						if cur_index < len(self.ui_rects) - 1:
							self.play_sound("menu_confirm")
						else:
							self.play_sound("menu_abort")

						# Skip by two until we get to the end of the key bind grid
						if cur_index < KEY_BIND_MAX * 2 + 1:
							cur_index += 1

						cur_index += 1

						cur_index = min(len(contents) - 1, cur_index)
						self.examine_target = contents[cur_index]
					if evt.key in self.key_binds[KEY_BIND_LEFT]:

						if isinstance(self.examine_target, list) and self.examine_target[1] == 1:
							self.examine_target[1] = 0
							self.play_sound("menu_confirm")
						else:
							self.play_sound("menu_abort")

					if evt.key in self.key_binds[KEY_BIND_RIGHT]:

						if isinstance(self.examine_target, list) and self.examine_target[1] == 0:
							self.examine_target[1] = 1
							self.play_sound("menu_confirm")
						else:
							self.play_sound("menu_abort")

					if evt.key in self.key_binds[KEY_BIND_CONFIRM]:
						self.key_bind_select_option(self.examine_target)
					if evt.key in self.key_binds[KEY_BIND_ABORT]:
						self.key_bind_select_option(KEY_BIND_OPTION_ACCEPT)
				if evt.type == pygame.MOUSEBUTTONDOWN:
					if evt.button == pygame.BUTTON_LEFT:
						self.key_bind_select_option(self.examine_target)
					if evt.button == pygame.BUTTON_RIGHT:
						self.key_bind_select_option(KEY_BIND_OPTION_ABORT)

	def key_bind_select_option(self, option):
		if isinstance(option, list):
			self.rebinding = True
			# And the examine target is already set
		elif option == KEY_BIND_OPTION_ABORT:
			self.play_sound("menu_abort")
			self.open_options()
		elif option == KEY_BIND_OPTION_ACCEPT:
			self.play_sound("menu_confirm")
			self.key_binds = dict(self.new_key_binds)
			self.open_options()
		elif option == KEY_BIND_OPTION_RESET:
			self.play_sound("menu_confirm")
			self.new_key_binds = dict(default_key_binds)

	def enter_reminisce(self):
		self.state = STATE_REMINISCE
		self.reminisce_folder = os.path.join('saves', str(self.game.run_number))
		self.reminisce_imgs = [os.path.join(self.reminisce_folder, f) for f in os.listdir(self.reminisce_folder) if f.endswith('.png')]

		def sort_key(fn):
			prefix = 'level_'
			postfix1 = '_begin.png'
			postfix2 = '_finish.png'

			fn = fn.split('/')[-1]
			fn = fn.split('\\')[-1]

			modifier = (1 if postfix2 in fn else 0)
			fn = fn.replace(prefix, '')
			fn = fn.replace(postfix1, '')
			fn = fn.replace(postfix2, '')

			try:
				level = int(fn)
			except:
				level = -1

			index = level * 2 + modifier
			return index

		self.reminisce_imgs = sorted(self.reminisce_imgs, key=sort_key)

		self.game = None
		self.reminisce_index = 0

	def draw_reminisce(self):

		img_fn = self.reminisce_imgs[self.reminisce_index]

		image = pygame.image.load(img_fn)
		self.screen.blit(image, (0, 0))

	def get_max_reminisce_index(self):
		return len(self.reminisce_imgs) - 1

	def process_reminisce_input(self):

		# Left and right add or subtract
		for evt in self.events:
			if evt.type == pygame.KEYDOWN:
				if evt.key in [pygame.K_LEFT, pygame.K_DOWN, pygame.K_KP2, pygame.K_KP4]:
					self.reminisce_index -= 1
					if self.reminisce_index < 0:
						self.reminisce_index = 0
				if evt.key in [pygame.K_RIGHT, pygame.K_UP, pygame.K_KP6, pygame.K_KP8]:
					self.reminisce_index += 1
					if self.reminisce_index > self.get_max_reminisce_index():
						self.reminisce_index = self.get_max_reminisce_index()
				if evt.key in [pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER]:
					self.reminisce_index += 1
					if self.reminisce_index > self.get_max_reminisce_index():
						self.return_to_title()
				if evt.key in [pygame.K_ESCAPE]:
					self.return_to_title()

			if evt.type == pygame.MOUSEBUTTONDOWN:
				if evt.button == pygame.BUTTON_LEFT:
					self.reminisce_index += 1
					if self.reminisce_index > self.get_max_reminisce_index():
						self.return_to_title()
				if evt.button == pygame.BUTTON_RIGHT:
					self.reminisce_index -= 1
					if self.reminisce_index < 0:
						self.reminisce_index = 0

	def adjust_char_sheet_selection(self, diff):
		assert(diff in [1, -1])

		skills = self.game.p1.get_skills()

		# Looking at known spell
		if isinstance(self.examine_target, Spell) and self.examine_target in self.game.p1.spells:

			spell_index = self.game.p1.spells.index(self.examine_target)
			new_index = spell_index + diff  # Pressing up at top of spell list

			if new_index < 0:
				self.play_sound("menu_abort")
			if 0 <= new_index < len(self.game.p1.spells):
				self.play_sound("menu_confirm")
				self.examine_target = self.game.p1.spells[new_index]
			if new_index >= len(self.game.p1.spells):
				self.play_sound("menu_confirm")
				self.examine_target = LEARN_SPELL_TARGET
		# Looking at known skill
		elif isinstance(self.examine_target, Upgrade) and self.examine_target.prereq == None:

			skill_index = skills.index(self.examine_target)
			new_index = skill_index + diff

			if new_index < 0:
				self.play_sound("menu_abort")
			if 0 <= new_index < len(skills):
				self.play_sound("menu_confirm")
				self.examine_target = skills[new_index]
			if new_index >= len(skills):
				self.play_sound("menu_confirm")
				self.examine_target = LEARN_SKILL_TARGET
		# Looking at spell upgrade for known spell
		elif isinstance(self.examine_target, Upgrade) and self.examine_target.prereq in self.game.p1.spells:

			prereq_index = self.game.p1.spells.index(self.examine_target.prereq)
			new_index = prereq_index + diff

			if new_index < 0:
				self.play_sound("menu_abort")
			if 0 <= new_index <= len(self.game.p1.spells) - 1:
				self.play_sound("menu_confirm")
				self.examine_target = self.game.p1.spells[new_index]
			if new_index == len(self.game.p1.spells):
				self.play_sound("menu_confirm")
				self.examine_target = LEARN_SPELL_TARGET
			else:
				self.play_sound("menu_abort")

		# Looking at 'Learn Skill'
		elif self.examine_target == LEARN_SPELL_TARGET:

			if diff < 0 and self.game.p1.spells:
				self.play_sound("menu_confirm")
				self.examine_target = self.game.p1.spells[-1]
			else:
				self.play_sound("menu_abort")
		# Looking at 'Learn Spell'
		elif self.examine_target == LEARN_SKILL_TARGET:

			if diff < 0 and skills:
				self.play_sound("menu_confirm")
				self.examine_target = skills[-1]
			else:
				self.play_sound("menu_abort")

		# other random exmaine targets
		else:
			self.play_sound("menu_confirm")
			self.examine_target = self.game.p1.spells[0] if self.game.p1.spells else LEARN_SPELL_TARGET

	def toggle_char_sheet_selection_type(self):
		# Always succeeds
		self.play_sound("menu_confirm")

		skills = self.game.p1.get_skills()
		if isinstance(self.examine_target, Spell) or self.examine_target == LEARN_SPELL_TARGET:
			self.examine_target = skills[0] if skills else LEARN_SKILL_TARGET

		elif self.examine_target in skills or self.examine_target == LEARN_SKILL_TARGET:
			self.examine_target = self.game.p1.spells[0] if self.game.p1.spells else LEARN_SPELL_TARGET

		# Skill upgrade
		elif isinstance(self.examine_target, Upgrade):
			self.examine_target = skills[0] if skills else LEARN_SKILL_TARGET

		# Other random examine targets
		else:
			self.examine_target = skills[0] if skills else LEARN_SKILL_TARGET

	def adjust_spell_pos(self, amt):
		if self.examine_target not in self.game.p1.spells:
			return
		cur_index = self.game.p1.spells.index(self.examine_target)
		new_index = cur_index + amt

		if new_index < 0:
			return
		if new_index >= len(self.game.p1.spells):
			return

		if amt > 0:
			self.game.p1.spells.insert(new_index+1, self.examine_target)
			self.game.p1.spells.pop(cur_index)
		else:
			self.game.p1.spells.pop(cur_index)
			self.game.p1.spells.insert(new_index, self.examine_target)


	def process_char_sheet_input(self):

		keys = pygame.key.get_pressed()
		for evt in self.events:
			if evt.type != pygame.KEYDOWN:
				continue

			if evt.key in self.key_binds[KEY_BIND_DOWN]:
				if not keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
					self.adjust_char_sheet_selection(1)
					self.play_sound("menu_confirm")
				else:
					self.adjust_spell_pos(1)

			if evt.key in self.key_binds[KEY_BIND_UP]:
				if not keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
					self.adjust_char_sheet_selection(-1)
					self.play_sound("menu_confirm")
				else:
					self.adjust_spell_pos(-1)
			if evt.key in self.key_binds[KEY_BIND_LEFT] or evt.key in self.key_binds[KEY_BIND_RIGHT]:
				self.toggle_char_sheet_selection_type()
			if evt.key in self.key_binds[KEY_BIND_ABORT]:
				self.play_sound("menu_confirm")
				self.state = STATE_LEVEL
				self.tag_filter.clear()

			if evt.key in self.key_binds[KEY_BIND_CONFIRM]:
				if self.examine_target == LEARN_SKILL_TARGET:
					self.open_shop(SHOP_TYPE_UPGRADES)
				elif self.examine_target == LEARN_SPELL_TARGET:
					self.open_shop(SHOP_TYPE_SPELLS)
				elif self.examine_target in self.game.p1.spells:
					self.open_shop(SHOP_TYPE_SPELL_UPGRADES, self.examine_target)
				elif self.examine_target in self.game.p1.get_skills():
					self.open_shop(SHOP_TYPE_UPGRADES)
				elif hasattr(self.examine_target, "prereq") and self.examine_target.prereq in self.game.p1.spells:
					self.open_shop(SHOP_TYPE_SPELL_UPGRADES, self.examine_target.prereq)

			if evt.key in self.key_binds[KEY_BIND_SPELLS]:
				self.open_shop(SHOP_TYPE_SPELLS)

			if evt.key in self.key_binds[KEY_BIND_SKILLS]:
				self.open_shop(SHOP_TYPE_UPGRADES)

			for bind in range(KEY_BIND_SPELL_1, KEY_BIND_SPELL_10):
				if evt.key in self.key_binds[bind]:
					index = bind - KEY_BIND_SPELL_1

					for key in self.key_binds[KEY_BIND_MODIFIER_1]:
						if key and keys[key]:
							index += 10

					if len(self.game.p1.spells) > index:
						self.examine_target = self.game.p1.spells[index]

			char_sheet_selection_max = len(self.game.p1.spells) if self.char_sheet_select_type == CHAR_SHEET_SELECT_TYPE_SPELLS else len(self.game.p1.get_skills())

			if self.char_sheet_select_index < 0:
				self.char_sheet_select_index = char_sheet_selection_max
			if self.char_sheet_select_index > char_sheet_selection_max:
				self.char_sheet_select_index = 0

			if cheats_enabled and evt.key == pygame.K_v:
				self.play_sound("menu_confirm")

				contents = [
					ChainLightningSpell(),
					NightmareSpell(),
					MeteorShower(),
					StoneAuraSpell(),
					AngelicChorus(),
				]

				to_blit = self.examine_display
				full_surf = pygame.Surface((len(contents) * to_blit.get_width(), to_blit.get_height()))
				i = 0
				for s in contents:
					if isinstance(s, Unit):
						p = self.game.cur_level.get_summon_point(self.game.p1.x, self.game.p1.x)
						self.game.cur_level.add_obj(s, p.x, p.y)
						s.Anim = self.get_anim(s)
					self.examine_target = s
					self.draw_examine()
					to_blit = self.examine_display

					scale = 1
					w = to_blit.get_width() * scale
					h = to_blit.get_height() * scale
					surf = pygame.transform.scale(to_blit, (w, h))
					full_surf.blit(surf, (w*i, 0))
					i += 1

				for i in range(100):
					path = "screencap\\ss_%d.png" % i
					if not os.path.exists(path):
						pygame.image.save(full_surf, path)
						break

		mx, my = self.get_mouse_pos()
		for evt in self.events:
			if evt.type !=pygame.MOUSEBUTTONDOWN:
				continue

			if evt.button == pygame.BUTTON_LEFT:
				if self.examine_target == LEARN_SPELL_TARGET:
					self.open_shop(SHOP_TYPE_SPELLS)
				elif self.examine_target == LEARN_SKILL_TARGET:
					self.open_shop(SHOP_TYPE_UPGRADES)
				elif isinstance(self.examine_target, Spell):
					self.open_shop(SHOP_TYPE_SPELL_UPGRADES, self.examine_target)
				elif isinstance(self.examine_target, Upgrade) and self.examine_target.prereq is None:
					self.open_shop(SHOP_TYPE_UPGRADES)
				elif isinstance(self.examine_target, Upgrade) and self.examine_target is not None:
					self.open_shop(SHOP_TYPE_SPELL_UPGRADES, self.examine_target.prereq)

			if evt.button == pygame.BUTTON_RIGHT:
				self.state = STATE_LEVEL
				self.play_sound("menu_abort")


	def get_shop_options(self):
		if self.shop_type == SHOP_TYPE_SPELLS:
			return [s for s in self.game.all_player_spells if all(t in s.tags for t in self.tag_filter)]
		if self.shop_type == SHOP_TYPE_UPGRADES:
			return [u for u in self.game.all_player_skills if all(t in u.tags for t in self.tag_filter)]
		if self.shop_type == SHOP_TYPE_SPELL_UPGRADES:
			return [u for u in self.shop_upgrade_spell.spell_upgrades]
		if self.shop_type == SHOP_TYPE_SHOP:
			if self.game.cur_level.cur_shop:
				return self.game.cur_level.cur_shop.items
		if self.shop_type == SHOP_TYPE_BESTIARY:
			return all_monsters
		else:
			return []

	def draw_shop(self):

		# Spells: show spells show filters
		# Upgrades: show upgrades
		# Spell Upgrades: show upgrades for spell
		# Bestary: show all monsters (cannot purchase)

		self.shop_rects = []
		self.middle_menu_display.fill((0, 0, 0))
		self.draw_panel(self.middle_menu_display)

		# Draw Shrine Background
		if self.shop_type == SHOP_TYPE_SHOP:
			cur_shop = self.game.cur_level.tiles[self.game.p1.x][self.game.p1.y].prop
			if cur_shop:
				# TODO- draw the sprite onto a surface so that animation works and blit THAT surface
				image = get_image(cur_shop.asset).subsurface((0, 0, SPRITE_SIZE, SPRITE_SIZE))
				big_shop = pygame.transform.scale(image, (SPRITE_SIZE*32, SPRITE_SIZE*32))
				dx = (self.middle_menu_display.get_width() - big_shop.get_width()) // 2
				dy = (self.middle_menu_display.get_height() - big_shop.get_height()) // 2
				big_shop.fill((255, 255, 255, 90), special_flags=pygame.BLEND_RGBA_MULT)
				self.middle_menu_display.blit(big_shop, (dx, dy))

		mx, my = self.get_mouse_pos()
		options = self.get_shop_options()

		spell_x_offset = self.border_margin + 18
		cur_x = spell_x_offset
		cur_y = self.linesize

		tag_offset = 16 * 32

		spell_column_width = (self.middle_menu_display.get_width() - 2 * self.border_margin) // 2
		level_x = cur_x + 16 * 29

		shoptions = self.get_shop_options()
		num_options = len(shoptions)

		if self.shop_type == SHOP_TYPE_SPELLS:
			self.draw_string("学习法术: ", self.middle_menu_display, cur_x, cur_y)
			self.draw_string("SP", self.middle_menu_display, level_x - self.font.size('X')[0], cur_y, COLOR_XP)
			self.draw_string("类别", self.middle_menu_display, cur_x + tag_offset, cur_y)
		if self.shop_type == SHOP_TYPE_UPGRADES:
			self.draw_string("学习能力: ", self.middle_menu_display, cur_x, cur_y)
		if self.shop_type == SHOP_TYPE_SPELL_UPGRADES:
			self.draw_string("升级%s: " % self.shop_upgrade_spell.name, self.middle_menu_display, cur_x, cur_y)
		if self.shop_type == SHOP_TYPE_SHOP:
			self.draw_string(self.get_display_level().cur_shop.name, self.middle_menu_display, 0, cur_y, content_width=self.middle_menu_display.get_width(), center=True)
		if self.shop_type == SHOP_TYPE_BESTIARY:
			self.draw_string("怪物图鉴: 消灭过 %d/%d 种怪兽" % (SteamAdapter.get_num_slain(), len(all_monsters)), self.middle_menu_display, cur_x, cur_y)


		cur_y += self.linesize
		cur_y += self.linesize

		if not shoptions:
			if self.shop_type == SHOP_TYPE_SHOP:
				self.draw_string("None of your spells can be improved at this shrine", self.middle_menu_display, 0, cur_y, content_width=self.middle_menu_display.get_width(), center=True)
			elif self.shop_type in [SHOP_TYPE_SPELLS, SHOP_TYPE_SPELLS]:
				self.draw_string("No spells fit these filters", self.middle_menu_display, cur_x, cur_y, HIGHLIGHT_COLOR)

		start_index = self.shop_page * self.max_shop_objects
		end_index = start_index + self.max_shop_objects

		for opt in shoptions[start_index:end_index]:

			cur_x = spell_x_offset
			if self.shop_type in [SHOP_TYPE_SPELLS, SHOP_TYPE_UPGRADES]:
				self.draw_spell_icon(opt, self.middle_menu_display, cur_x, cur_y)
				cur_x += 20

			fmt = opt.name
			cur_color = (255, 255, 255)

			if self.shop_type == SHOP_TYPE_BESTIARY and not SteamAdapter.has_slain(opt.name):
				fmt = "?????????????????????"
				cur_color = (100, 100, 100)

			if self.shop_type != SHOP_TYPE_BESTIARY:
				cost = self.game.get_upgrade_cost(opt)
				if self.game.has_upgrade(opt):
					cur_color = (0, 255, 0)
				elif self.game.can_buy_upgrade(opt):
					cur_color = self.game.p1.discount_tag.color.to_tup() if self.game.p1.discount_tag in opt.tags else (255, 255, 255)
				else:
					cur_color = (100, 100, 100)

			if self.shop_type == SHOP_TYPE_SHOP:
				self.draw_string(fmt, self.middle_menu_display, 0, cur_y, cur_color, mouse_content=opt, content_width=self.middle_menu_display.get_width(), center=True)
			else:
				self.draw_string(fmt, self.middle_menu_display, cur_x, cur_y, cur_color, mouse_content=opt, content_width=spell_column_width)

			if hasattr(opt, 'level') and isinstance(opt.level, int) and opt.level > 0:
				fmt = str(cost)
				if opt.name in self.game.p1.scroll_discounts:
					fmt += '*'
				self.draw_string(fmt, self.middle_menu_display, level_x, cur_y, cur_color)


			if self.shop_type != SHOP_TYPE_BESTIARY and hasattr(opt, 'tags'):
				tag_x = cur_x + tag_offset
				for tag in Tags:
					if tag not in opt.tags:
						continue
					self.draw_string(self.reverse_tag_keys[tag], self.middle_menu_display, tag_x, cur_y, tag.color.to_tup())
					tag_x += self.font.size(tag.name[0])[0]


			cur_y += self.linesize

		if self.shop_type in [SHOP_TYPE_UPGRADES, SHOP_TYPE_SPELLS]:
			# Draw filters
			cur_x = 16 * 40
			cur_y = self.linesize

			tag_width = self.middle_menu_display.get_width() - cur_x - self.border_margin
			self.draw_string("过滤: ", self.middle_menu_display, cur_x, cur_y)
			cur_y += 2*self.linesize

			for tag in self.game.spell_tags:

				color = tag.color.to_tup() if tag in self.tag_filter else (150, 150, 150)
				self.draw_string(tag.name, self.middle_menu_display, cur_x, cur_y, color, mouse_content=tag, content_width=tag_width)

				idx = 0

				for c in tag.name:
					if self.tag_keys.get(c.lower(), None) == tag:
						self.draw_string(c, self.middle_menu_display, cur_x + self.font.size(tag.name[:idx])[0], cur_y, tag.color.to_tup())
						break
					idx += 1

				cur_y += self.linesize


		cur_x = spell_x_offset
		cur_y = self.linesize * (self.max_shop_objects+4)
		max_shop_pages = self.get_max_shop_pages()

		if max_shop_pages > 1:

			can_prev = self.shop_page > 0
			prev_fmt = "<<<<"
			cur_color = (255, 255, 255) if can_prev else HIGHLIGHT_COLOR
			self.draw_string(prev_fmt, self.middle_menu_display, cur_x, cur_y, cur_color, mouse_content=TOOLTIP_PREV if can_prev else None)

			cur_x += self.font.size(prev_fmt + '   ')[0]
			fmt = "第 %d/%d 页" % (self.shop_page + 1, self.get_max_shop_pages())
			self.draw_string(fmt, self.middle_menu_display, cur_x, cur_y)

			cur_x += self.font.size(fmt + '   ')[0]
			#cur_x = spell_x_offset + spell_column_width - self.font.size(prev_fmt)[0]

			can_next = self.shop_page < max_shop_pages - 1
			next_fmt = ">>>>"
			cur_color = (255, 255, 255) if can_next else HIGHLIGHT_COLOR
			self.draw_string(next_fmt, self.middle_menu_display, cur_x, cur_y, cur_color, mouse_content=TOOLTIP_NEXT if can_next else None)


		self.screen.blit(self.middle_menu_display, (self.h_margin, 0))

	def try_buy_shop_selection(self, prompt=True):

		if self.shop_type == SHOP_TYPE_BESTIARY:
			return

		# If its an owned spell, open upgrades shop for that spell
		if self.examine_target in self.game.p1.spells:
			self.play_sound("menu_confirm")
			self.open_shop(SHOP_TYPE_SPELL_UPGRADES, spell=self.examine_target)
			self.abort_to_spell_shop = True
			return

		success = self.game.can_shop(self.examine_target)
		if not success:
			self.play_sound("menu_abort")
			return

		self.open_buy_prompt(self.examine_target)

		if not prompt:
			self.confirm_buy()


	def toggle_shop_filter(self, tag):
		self.play_sound("menu_confirm")
		if tag in self.tag_filter:
			self.tag_filter.remove(tag)
		else:
			self.tag_filter.add(tag)
		self.shop_page = 0
		self.shop_selection_index = 0

		new_shoptions = self.get_shop_options()
		self.examine_target = None
		if new_shoptions:
			self.examine_target = new_shoptions[0]

	def get_max_shop_pages(self):
		return math.ceil(len(self.get_shop_options()) / self.max_shop_objects)

	def shop_selection_adjust(self, inc):
		# Bump examine target up by inc, roll over if it goes over the shop page
		shoptions = self.get_shop_options()
		if not shoptions:
			return
		self.play_sound("menu_confirm")

		if self.examine_target in shoptions:
			shop_selection_index = shoptions.index(self.examine_target)
		elif hasattr(self.examine_target, 'prereq') and self.examine_target.prereq in shoptions:
			shop_selection_index = shoptions.index(self.examine_target.prereq)
		else:
			shop_selection_index = self.get_max_shop_pages() * self.shop_page
			inc = 0

		shop_selection_index += inc

		shop_selection_index = max(self.shop_page * self.max_shop_objects, shop_selection_index)
		shop_selection_index = min((self.shop_page + 1) * self.max_shop_objects - 1, shop_selection_index)
		shop_selection_index = min(len(shoptions) - 1, shop_selection_index)

		self.examine_target = shoptions[shop_selection_index]

	def shop_page_adjust(self, inc):
		max_shop_pages = self.get_max_shop_pages()

		if max_shop_pages < 1:
			return

		if max_shop_pages > 1:
			self.play_sound("menu_confirm")
		else:
			self.play_sound("menu_abort")

		self.shop_page += inc
		self.shop_page = self.shop_page % max_shop_pages
		shop_selection_index = self.shop_page * self.max_shop_objects

		self.examine_target = self.get_shop_options()[shop_selection_index]

	def close_shop(self):

		if not self.game:
			self.return_to_title()
			return

		if self.abort_to_spell_shop:
			self.play_sound("menu_abort")
			self.abort_to_spell_shop = False
			self.open_shop(SHOP_TYPE_SPELLS)
			return

		self.game.try_shop(None)

		if self.shop_type == SHOP_TYPE_SHOP or self.prev_state == STATE_LEVEL:
			self.play_sound("menu_confirm")
			self.state = STATE_LEVEL

		elif self.shop_type != SHOP_TYPE_SHOP:
			self.open_char_sheet()
			self.examine_target = self.shop_open_examine_target


	def open_char_sheet(self):
		self.play_sound("menu_confirm")
		self.state = STATE_CHAR_SHEET
		if self.examine_target not in self.game.p1.spells + self.game.p1.get_skills() + [LEARN_SKILL_TARGET, LEARN_SPELL_TARGET]:
			self.examine_target = LEARN_SPELL_TARGET

	def process_shop_input(self):

		shop_options = self.get_shop_options()
		num_options = len(shop_options)
		for evt in self.events:
			if evt.type != pygame.KEYDOWN:
				continue

			if evt.key in self.key_binds[KEY_BIND_DOWN]:
				self.shop_selection_adjust(1)

			if evt.key in self.key_binds[KEY_BIND_UP]:
				self.shop_selection_adjust(-1)

			if evt.key in self.key_binds[KEY_BIND_LEFT]:
				self.shop_page_adjust(-1)

			if evt.key in self.key_binds[KEY_BIND_RIGHT]:
				self.shop_page_adjust(1)

			if (pygame.K_a <= evt.key <= pygame.K_z) and chr(evt.key) in self.tag_keys:
				tag = self.tag_keys[chr(evt.key)]
				self.toggle_shop_filter(tag)

			if evt.key in self.key_binds[KEY_BIND_CONFIRM]:
				self.try_buy_shop_selection(prompt=False)
				break

			if evt.key in self.key_binds[KEY_BIND_ABORT]:
				self.close_shop()

			# Screenshot cheat
			if cheats_enabled and evt.key == pygame.K_v:
					to_blit = self.screen
					scale = 1
					w = to_blit.get_width() * scale
					h = to_blit.get_height() * scale
					surf = pygame.transform.scale(to_blit, (w, h))

					for i in range(100):
						path = "screencap\\ss_%d.png" % i
						if not os.path.exists(path):
							pygame.image.save(surf, path)
							break

		mouse_pos = self.get_mouse_pos()

		shop_start_index = self.max_shop_objects * self.shop_page
		for click in self.events:
			if click.type != pygame.MOUSEBUTTONDOWN:
				continue

			if click.button == pygame.BUTTON_WHEELDOWN:
				self.play_sound("menu_confirm")
				self.shop_page_adjust(1)

			if click.button == pygame.BUTTON_WHEELUP:
				self.play_sound("menu_confirm")
				self.shop_page_adjust(-1)

			if click.button == pygame.BUTTON_LEFT:

				for r, c in self.ui_rects:
					if r.collidepoint(mouse_pos):
						if c == TOOLTIP_NEXT:
							self.shop_page_adjust(1)
						elif c == TOOLTIP_PREV:
							self.shop_page_adjust(-1)
						elif c == TOOLTIP_EXIT:
							self.close_shop()
						elif isinstance(c, Tag):
							self.toggle_shop_filter(c)
							break
						else:
							if click.button == pygame.BUTTON_LEFT:
								self.try_buy_shop_selection(prompt=True)
								break

			elif click.button == pygame.BUTTON_RIGHT:
					self.close_shop()
					self.play_sound("menu_abort")

	def get_tile_sprites(self, tile):
		x = tile.x
		y = tile.y
		tileset = tile.tileset
		if 'tileset' in sys.argv:
			tileset = sys.argv[sys.argv.index('tileset') + 1]
		if tile.is_floor():
			tile_index = hash((2*x, y)) % len(self.floor_tiles[tileset])
			yield self.floor_tiles[tileset][tile_index]
			return
		if tile.is_wall():
			tile_index = hash((2*x, y)) % len(self.wall_tiles[tileset])
			yield self.wall_tiles[tileset][tile_index]
			return
		if tile.is_chasm:

			def is_chasm(i, j):
				level = tile.level
				if not level.is_point_in_bounds(Point(i, j)):
					return True

				cur_tile = level.tiles[i][j]
				return cur_tile.is_chasm

			chasm_left  = is_chasm(x - 1, y)
			chasm_right = is_chasm(x + 1, y)
			chasm_above = is_chasm(x, y - 1)
			chasm_below = is_chasm(x, y + 1)

			image_opts = self.chasm_sprites[(not chasm_left, not chasm_right, not chasm_above, not chasm_below)]
			if image_opts:

				num_images = len(image_opts)
				image_index = hash((x, y)) % num_images
				yield image_opts[image_index]

			chasm_upper_left = is_chasm(x - 1, y - 1)
			chasm_lower_left = is_chasm(x - 1, y + 1)
			chasm_lower_right = is_chasm(x + 1, y + 1)
			chasm_upper_right = is_chasm(x + 1, y - 1)

			# test corners
			num_corner_images = len(self.chasm_corners[UI_UPPER_LEFT])
			if chasm_above and chasm_left and not chasm_upper_left:
				index = hash((x, y, UI_UPPER_LEFT)) % num_corner_images
				yield self.chasm_corners[UI_UPPER_LEFT][index]
			if chasm_left and chasm_below and not chasm_lower_left:
				index = hash((x, y, UI_LOWER_LEFT)) % num_corner_images
				yield self.chasm_corners[UI_LOWER_LEFT][index]
			if chasm_below and chasm_right and not chasm_lower_right:
				index = hash((x, y, UI_LOWER_RIGHT)) % num_corner_images
				yield self.chasm_corners[UI_LOWER_RIGHT][index]
			if chasm_right and chasm_above and not chasm_upper_right:
				index = hash((x, y, UI_UPPER_RIGHT)) % num_corner_images
				yield self.chasm_corners[UI_UPPER_RIGHT][index]

	def make_tile_sprite(self, tile, occupied):
		sprite = pygame.Surface((SPRITE_SIZE, SPRITE_SIZE))
		if tile.is_chasm:
			if tile.water or 'water' in sys.argv:
				if 'water' in sys.argv:
					water_name = sys.argv[sys.argv.index('water') + 1]
				else:
					water_name = tile.water

				water_tile = get_image(['tiles', 'water', water_name])

				if occupied:
					pygame.draw.rect(sprite, water_tile.get_at((0, 0)), (0, 0, SPRITE_SIZE, SPRITE_SIZE))
				else:
					sprite.blit(water_tile, (0, 0))

		sprites = list(self.get_tile_sprites(tile))

		for image in sprites:

			tileset = tile.level.tileset
			if 'tileset' in sys.argv:
				tileset = sys.argv[sys.argv.index('tileset') + 1]

			if tile.is_chasm:
				color = self.get_tileset_color(tileset)
				image = self.get_filled_sprite(image, color)
			sprite.blit(image, (0, 0))

		return sprite

	def draw_tile(self, tile, partial_occulde=False):
		x = tile.x * SPRITE_SIZE
		y = tile.y * SPRITE_SIZE

		if not tile.sprites:
			tile.sprites = [None, None]

		if not partial_occulde:
			if not tile.sprites[0]:
				tile.sprites[0] = self.make_tile_sprite(tile, 0)
			image = tile.sprites[0]
		else:
			if not tile.sprites[1]:
				tile.sprites[1] = self.make_tile_sprite(tile, 1)
			image = tile.sprites[1]

		#image = self.floor_tiles['ruby'][0]
		self.level_display.blit(image, (x, y))

	def draw_unit(self, u):
		x = u.x * SPRITE_SIZE
		y = u.y * SPRITE_SIZE

		if u.transform_asset_name:
			if not u.Transform_Anim:
				u.Transform_Anim = self.get_anim(u, forced_name=u.transform_asset_name)
			u.Transform_Anim.draw(self.level_display)
		else:
			if not u.Anim:
				u.Anim = self.get_anim(u)
			u.Anim.draw(self.level_display)

		# Friendlyness icon
		if not u.is_player_controlled and not are_hostile(u, self.game.p1):
			image = get_image(['friendly'])

			num_frames = image.get_width() // STATUS_ICON_SIZE
			frame_num = cloud_frame_clock // STATUS_SUBFRAMES % num_frames
			source_rect = (STATUS_ICON_SIZE*frame_num, 0, STATUS_ICON_SIZE, STATUS_ICON_SIZE)

			self.level_display.blit(image, (x + SPRITE_SIZE - 4, y+1), source_rect)

		# Lifebar
		if u.cur_hp != u.max_hp:
			hp_percent = u.cur_hp / float(u.max_hp)
			max_bar = SPRITE_SIZE - 2
			bar_pixels = int(hp_percent * max_bar)
			margin = (max_bar - bar_pixels) // 2
			pygame.draw.rect(self.level_display, (255, 0, 0, 128), (x + 1 + margin, y+SPRITE_SIZE-2, bar_pixels, 1))

		# Draw Buffs
		status_effects = []

		def get_buffs():
			seen_types = set()
			for b in u.buffs:
				# Do not display icons for passives- aka, passive regeneration
				if b.buff_type == BUFF_TYPE_PASSIVE:
					continue
				if type(b) in seen_types:
					continue
				if b.asset == None:
					continue
				seen_types.add(type(b))
				yield b

		status_effects = list(get_buffs())
		if not status_effects:
			return

		buff_x = x+1
		buff_index = cloud_frame_clock // (STATUS_SUBFRAMES * 4) % len(status_effects)

		b = status_effects[buff_index]

		if not b.asset:
			color = b.color if b.color else Color(255, 255, 255)
			pygame.draw.rect(self.level_display, color.to_tup(), (buff_x, y+1, 3, 3))
		else:
			image = get_image(b.asset)
			num_frames = image.get_width() // STATUS_ICON_SIZE

			frame_num = cloud_frame_clock // STATUS_SUBFRAMES % num_frames
			source_rect = (STATUS_ICON_SIZE*frame_num, 0, STATUS_ICON_SIZE, STATUS_ICON_SIZE)
			self.level_display.blit(image, (buff_x, y+1), source_rect)
		buff_x += 4

	def draw_cloud(self, cloud, secondary=False):
		if not cloud.asset_name:
			return

		if secondary:
			filename = cloud.asset_name + '_2'
		else:
			filename = cloud.asset_name + '_1'

		asset = ['tiles', 'clouds', filename]

		image = get_image(asset)

		num_frames = image.get_width() // SPRITE_SIZE
		cur_frame = (cloud_frame_clock // SUB_FRAMES[ANIM_IDLE]) % num_frames

		subarea = (SPRITE_SIZE * cur_frame, 0, SPRITE_SIZE, SPRITE_SIZE)

		x = cloud.x * SPRITE_SIZE
		y = cloud.y * SPRITE_SIZE

		self.level_display.blit(image, (x, y), subarea)

	def get_prop_image(self, p):
		asset = p.asset if hasattr(p, 'asset') else ['char', 'unknown']
		fill_color = None
		if isinstance(p, PlaceOfPower):
			fill_color = p.tag.color.to_tup()

		return get_image(asset, fill_color)

	def draw_prop(self, p, surface=None):
		x = p.x * SPRITE_SIZE
		y = p.y * SPRITE_SIZE

		image = self.get_prop_image(p)
		if not hasattr(p, 'Sprite') or not p.Sprite or p.Sprite.image != image:
			sync = False
			if isinstance(p, Portal):
				speed = 1
			else:
				sync = True
				speed = 12
			p.Sprite = SimpleSprite(p.x, p.y, image, speed=speed, loop=True, sync=sync)

		p.Sprite.draw(surface or self.level_display)

	def draw_effect(self, e):
		e.draw(self.level_display)

	def draw_targeting(self):
		blit_area = (idle_frame * SPRITE_SIZE, 0, SPRITE_SIZE, SPRITE_SIZE)

		# Current main target
		x = self.cur_spell_target.x * SPRITE_SIZE
		y = self.cur_spell_target.y * SPRITE_SIZE
		if self.cur_spell.can_cast(self.cur_spell_target.x, self.cur_spell_target.y):
			image = self.tile_targeted_image
		else:
			image = self.tile_invalid_target_image

		to_blit = []
		to_blit.append((image, (x, y), blit_area))

		used_tiles = set()
		used_tiles.add(Point(self.cur_spell_target.x, self.cur_spell_target.y))

		# Currently impacted squares
		if self.cur_spell.can_cast(self.cur_spell_target.x, self.cur_spell_target.y):
			for p in self.cur_spell.get_impacted_tiles(self.cur_spell_target.x, self.cur_spell_target.y):
				if p in used_tiles:
					continue
				x = p.x * SPRITE_SIZE
				y = p.y * SPRITE_SIZE
				to_blit.append((self.tile_impacted_image, (x, y), blit_area))
				used_tiles.add(Point(p.x, p.y))

		if self.cur_spell.show_tt:
			# Targetable squares
			for p in self.targetable_tiles:
				if p in used_tiles:
					continue
				x = p.x * SPRITE_SIZE
				y = p.y * SPRITE_SIZE
				to_blit.append((self.tile_targetable_image, (x, y), blit_area))
				used_tiles.add(Point(p.x, p.y))

			# Untargetable but in range squares
			if self.cur_spell.melee:
				aoe = self.game.cur_level.get_points_in_ball(self.game.p1.x, self.game.p1.y, 1, diag=True)
			else:
				aoe = self.game.cur_level.get_points_in_ball(self.game.p1.x, self.game.p1.y, self.cur_spell.get_stat('range'))

			requires_los = self.cur_spell.get_stat('requires_los')
			for p in aoe:
				if p in used_tiles:
					continue
				if p.x == self.game.p1.x and p.y == self.game.p1.y and not self.cur_spell.can_target_self:
					continue
				if requires_los and not self.game.cur_level.can_see(self.game.p1.x, self.game.p1.y, p.x, p.y):
					continue

				x = p.x * SPRITE_SIZE
				y = p.y * SPRITE_SIZE
				to_blit.append((self.tile_invalid_target_in_range_image, (x, y), blit_area))

		self.level_display.blits(to_blit)

	def add_threat(self,level,x,y):
		if x >= 0 and x < LEVEL_SIZE and y >= 0 and y < LEVEL_SIZE:
			t = level.tiles[x][y]
			if t.can_walk or t.can_fly:
				self.threat_zone.add((x,y))

	def draw_threat(self):
		level = self.get_display_level()
		# Narrow to one unit maybe
		highlighted_unit = None
		mouse_point = self.get_mouse_level_point()
		if mouse_point:
			highlighted_unit = level.get_unit_at(mouse_point.x, mouse_point.y)

		if highlighted_unit and highlighted_unit.is_player_controlled:
			highlighted_unit = None

		if not self.threat_zone or highlighted_unit != self.last_threat_highlight:
			self.last_threat_highlight = highlighted_unit
			self.threat_zone = set()


			units = []
			possible_spells = []
			possible_buffs = []
			if not highlighted_unit:
				for u in level.units:
					if are_hostile(self.game.p1, u):
						self.threat_zone.add((u.x, u.y))
						possible_spells += u.spells
						possible_buffs += u.buffs
						units.append(u)
			else:
				units.append(highlighted_unit)
				possible_spells += highlighted_unit.spells
				possible_buffs += highlighted_unit.buffs
				self.threat_zone.add((highlighted_unit.x, highlighted_unit.y))

			spells = []
			for s in possible_spells:
				if s.melee:
					self.add_threat(level, s.caster.x-1, s.caster.y-1)
					self.add_threat(level, s.caster.x-1, s.caster.y)
					self.add_threat(level, s.caster.x-1, s.caster.y+1)
					self.add_threat(level, s.caster.x, s.caster.y-1)
					self.add_threat(level, s.caster.x, s.caster.y+1)
					self.add_threat(level, s.caster.x+1, s.caster.y-1)
					self.add_threat(level, s.caster.x+1, s.caster.y)
					self.add_threat(level, s.caster.x+1, s.caster.y+1)
				else:
					spells.append(s)

			spells.sort(key = lambda s: s.range, reverse = True)

			buffs = []
			for b in possible_buffs:
				# kind of bizarre but Buff.can_threaten always returns false
				# so we just have to detect those buffs with the default method
				if not b.can_threaten.__func__ == Buff.can_threaten:
					buffs.append(b)

			for t in level.iter_tiles():
				# Dont bother with walls
				if not t.can_walk and not t.can_fly:
					continue

				if t in self.threat_zone:
					continue

				for s in spells:
					if s.can_threaten(t.x, t.y):
						self.threat_zone.add((t.x, t.y))
						break
				for b in buffs:
					if b.can_threaten(t.x, t.y):
						self.threat_zone.add((t.x, t.y))
						break

		blit_area = (idle_frame * SPRITE_SIZE, 0, SPRITE_SIZE, SPRITE_SIZE)

		to_blit = []

		image = self.tile_invalid_target_image
		for t in self.threat_zone:
			to_blit.append((image, (SPRITE_SIZE * t[0], SPRITE_SIZE * t[1]), blit_area))

		self.level_display.blits(to_blit)

	def draw_los(self):

		global idle_frame
		cur_frame = idle_frame
		blit_area = (cur_frame * SPRITE_SIZE, 0, SPRITE_SIZE, SPRITE_SIZE)
		image = self.tile_targetable_image

		level = self.get_display_level()
		p = self.deploy_target or (self.cur_spell_target if self.cur_spell else self.get_mouse_level_point() or Point(self.game.p1.x, self.game.p1.y))
		for x in range(LEVEL_SIZE):
			for y in range(LEVEL_SIZE):
				if level.can_see(p.x, p.y, x, y):

					unit = level.get_unit_at(x, y)

					draw_point = (SPRITE_SIZE * x, SPRITE_SIZE * y)
					self.level_display.blit(image, draw_point, blit_area)

	def get_max_deploy_frames(self):
		# Number of frames needed to show animation = maximum taxicab distance btw player and a corner
		return max(
			distance(self.game.p1, Point(0, 0), euclidean=False),
			distance(self.game.p1, Point(0, LEVEL_SIZE-1), euclidean=False),
			distance(self.game.p1, Point(LEVEL_SIZE-1, 0), euclidean=False),
			distance(self.game.p1, Point(LEVEL_SIZE-1, LEVEL_SIZE-1), euclidean=False)) // DEPLOY_SPEED + 1

	def draw_level(self):
		if self.gameover_frames >= 8:
			return

		level = self.get_display_level()
		self.level_display.fill((0, 0, 0))

		#Transform and drain the levels effects
		to_remove = []
		for effect in level.effects:
			if not hasattr(effect, 'graphic'):
				graphic = self.get_effect(effect)
				if not graphic:
					to_remove.append(effect)
					continue

				effect.graphic = graphic
				graphic.level_effect = effect
				# Queue buff effects, instantly play other effects

				# Damage effects can replace damage effects
				# Buff effects queue after everything
				# Damage effects queue after buff effects

				queued_colors = [
					Tags.Buff_Apply.color,
					Tags.Debuff_Apply.color,
					Tags.Shield_Apply.color,
					Tags.Shield_Expire.color,
				]
				if hasattr(effect, 'color') and effect.color in queued_colors:
					self.queue_effect(graphic)
				else:
					self.effects.append(graphic)

		# Kill sound effects
		for effect in to_remove:
			level.effects.remove(effect)

		# Draw the board
		self.advance_queued_effects()

		effect_tiles = set()
		for e in self.effects:
			effect_tiles.add((e.x, e.y))

		if hasattr(self.examine_target, 'level') and hasattr(self.examine_target, 'x') and hasattr(self.examine_target, 'y'):
			if isinstance(self.examine_target, Unit) and self.examine_target.cur_hp > 0:

				if self.examine_target.has_buff(Soulbound):
					b = self.examine_target.get_buff(Soulbound)

					rect = (b.guardian.x * SPRITE_SIZE, b.guardian.y * SPRITE_SIZE, SPRITE_SIZE, SPRITE_SIZE)
					color = (60, 0, 0)
					pygame.draw.rect(self.level_display, color, rect)

				if self.examine_target.has_buff(ChannelBuff):
					b = self.examine_target.get_buff(ChannelBuff)

					rect = (b.spell_target.x * SPRITE_SIZE, b.spell_target.y * SPRITE_SIZE, SPRITE_SIZE, SPRITE_SIZE)
					color = (60, 0, 0)
					# TODO- red target circle(or green if ally) instead of grey background block
					# TODO- all impacted tiles of target
					pygame.draw.rect(self.level_display, color, rect)

		if self.game.next_level:
			self.deploy_anim_frames += 1
			self.deploy_anim_frames = min(self.deploy_anim_frames, self.get_max_deploy_frames())
		elif self.game.prev_next_level and self.deploy_anim_frames > 0:
			self.deploy_anim_frames -= 1

		def get_level(i, j):
			if not self.deploy_anim_frames:
				return self.game.cur_level

			cur_radius = DEPLOY_SPEED*self.deploy_anim_frames
			if abs(i-self.game.p1.x) + abs(j-self.game.p1.y) > cur_radius:
				return self.game.cur_level
			else:
				return self.game.next_level or self.game.prev_next_level


		for i in range(0, LEVEL_SIZE):
			for j in range(0, LEVEL_SIZE):

				level = get_level(i, j)

				tile = level.tiles[i][j]

				should_draw_tile = True
				if tile.prop:
					should_draw_tile = False
				if tile.unit and not tile.is_chasm:
					should_draw_tile = False
				if should_draw_tile:
					partial_occulde = tile.unit or (i, j) in effect_tiles
					self.draw_tile(tile, partial_occulde=partial_occulde)

				if self.examine_target and (self.examine_target in [tile.unit, tile.cloud, tile.prop]):
						rect = (self.examine_target.x * SPRITE_SIZE, self.examine_target.y * SPRITE_SIZE, SPRITE_SIZE, SPRITE_SIZE)
						color = (60, 60, 60)
						pygame.draw.rect(self.level_display, color, rect)

		# Draw LOS if requested
		keys = pygame.key.get_pressed()
		if any(k and keys[k] for k in self.key_binds[KEY_BIND_LOS]):
			self.draw_los()
		# Draw threat if requested
		elif any(k and keys[k] for k in self.key_binds[KEY_BIND_THREAT]) and self.game.is_awaiting_input():
			self.draw_threat()
		# Draw targeting if a spell is chosen
		elif self.cur_spell:
			self.draw_targeting()

		for i in range(0, LEVEL_SIZE):
			for j in range(0, LEVEL_SIZE):

				level = get_level(i, j)

				tile = level.tiles[i][j]

				if tile.unit:
					self.draw_unit(tile.unit)
					if tile.cloud:
						self.draw_cloud(tile.cloud)
				elif tile.cloud:
					self.draw_cloud(tile.cloud)
				elif tile.prop and(i, j) not in effect_tiles:
					self.draw_prop(tile.prop)

		if isinstance(self.examine_target, Unit):
			buff = self.examine_target.get_buff(OrbBuff)
			if buff and buff.dest:
				dest = buff.dest
				rect = (dest.x * SPRITE_SIZE, dest.y * SPRITE_SIZE, SPRITE_SIZE, SPRITE_SIZE)
				self.level_display.blit(self.hostile_los_image, (dest.x * SPRITE_SIZE, dest.y * SPRITE_SIZE))

		for e in self.effects:
			self.draw_effect(e)

		for e in self.effects:
			if e.finished:
				if hasattr(e, 'level_effect'):
					# Sometimes this will fail if you transfer to the next level
					# Whatever (itll be garbage collected with the level anyway)
					if e.level_effect in self.game.cur_level.effects:
						self.game.cur_level.effects.remove(e.level_effect)
					elif self.game.next_level and e.level_effect in self.game.next_level.effects:
						self.game.next_level.effects.remove(e.level_effect)

		self.effects = [e for e in self.effects if not e.finished]


		# Draw deploy
		if self.game.deploying and self.deploy_target:
			image = get_image(["UI", "deploy_ok_animated"]) if level.can_stand(self.deploy_target.x, self.deploy_target.y, self.game.p1) else get_image(["UI", "deploy_no_animated"])
			deploy_frames = image.get_width() // SPRITE_SIZE
			deploy_frame = idle_frame % deploy_frames
			self.level_display.blit(image, (self.deploy_target.x * SPRITE_SIZE, self.deploy_target.y * SPRITE_SIZE), (deploy_frame * SPRITE_SIZE, 0, SPRITE_SIZE, SPRITE_SIZE))



		# Blit to main screen
		pygame.transform.scale(self.whole_level_display, (self.screen.get_width(), self.screen.get_height()), self.screen)

	def draw_string(self, string, surface, x, y, color=(255, 255, 255), mouse_content=None, content_width=None, center=False, char_panel=False, font=None):

		if not font:
			font = self.font

		width = content_width if content_width else font.size(string)[0]
		if center:
			line_size = self.font.size(string)[0]
			x = x + (width - line_size) // 2
			width = line_size

		if mouse_content is not None:
			surf_pos = self.get_surface_pos(surface)

			rect_y = y - 2
			rel_rect = pygame.Rect(x, rect_y, width, self.linesize)
			abs_rect = pygame.Rect(x + surf_pos[0], rect_y + surf_pos[1], width, self.linesize)

			self.ui_rects.append((abs_rect, mouse_content))

			# If the mouse moved, and is over this text, set this mouse content as examine target
			dx, dy = self.get_mouse_rel()
			if (dx or dy) and abs_rect.collidepoint(self.get_mouse_pos()):
				self.examine_target = mouse_content

			# If, for whatever reason, this content is the examine target, draw the highlight rect
			if self.examine_target == mouse_content:
				should_highlight = True
				if char_panel:
					if not abs_rect.collidepoint(self.get_mouse_pos()):
						should_highlight = False
				if should_highlight:
					pygame.draw.rect(surface, HIGHLIGHT_COLOR, rel_rect)

		string_surface = font.render(string, True, color)
		surface.blit(string_surface, (x, y))

	def draw_wrapped_string(self, string, surface, x, y, width, color=(255, 255, 255), center=False, indent=False, extra_space=False): 
		lines = string.split('\n') 
 
		cur_y = y # start y pos
		num_lines = 0 
		linesize = self.linesize # font linesize +2
		max_width = width

		for line in lines:
			cur_x = x # start x pos
			# 这个正则用来决定哪些文本被视为不会被切断的整块
			# 对于中文来说似乎不是很需要
			# 改动后优先匹配颜色块
			exp = "\[[^]]+\]|[a-zA-Z]+| |."
			words = re.findall(exp, line)
			# print(words)
			words.reverse()

			while words: 
				cur_color = color 
 
				word = words.pop() 

				if word != ' ': 
 
					# Process complex tooltips- strip off the []s and look up the color 
					if word and word[0] == '[' and word[-1] == ']': 
						tokens = word[1:-1].split(':') 
						if len(tokens) == 1: 
							word = tokens[0] # todo- fmt attribute? 
							cur_color = tooltip_colors[word.lower()].to_tup() 
						elif len(tokens) == 2: 
							word = tokens[0].replace('_', ' ') 
							cur_color = tooltip_colors[tokens[1].lower()].to_tup() 

					# check exceed max width
					word_width = self.font.size(word)[0]
					if cur_x + word_width > x + max_width:
						# 避免行首标点
						if (word != ',' and word != '。' and word != ':' and word != '、'):
							cur_y += linesize
							num_lines += 1
							# Indent by one for next line
							cur_x = x + self.space_width

					self.draw_string(word, surface, cur_x, cur_y, cur_color, content_width=max_width)
					cur_x += word_width

				else:
					cur_x += self.space_width
 
			cur_y += linesize 
			num_lines += 1 
			if extra_space: 
				cur_y += linesize 
				num_lines += 1 
 
		return num_lines 
 
	def process_click_character(self, button, x, y):

		target = None
		for (r, c) in self.ui_rects:
			if r.collidepoint((x, y)):
				target = c

		if not target:
			return

		if target == CHAR_SHEET_TARGET:
			self.open_char_sheet()
			self.char_sheet_select_index = 0
		elif target == INSTRUCTIONS_TARGET:
			self.show_help()
		elif target == OPTIONS_TARGET:
			self.open_options()
		elif button == pygame.BUTTON_LEFT:
			if isinstance(target, SpellCharacterWrapper):
				self.choose_spell(target.spell)
			if isinstance(target, Item):
				self.choose_spell(target.spell)
		elif button == pygame.BUTTON_RIGHT:
			self.examine_target = target

	def draw_panel(self, display, bounds = None):
		display.fill((0, 0, 0))

		# Assume uniform tile size for now
		tile_size = self.ui_tiles[0].get_width()

		display_width = display.get_width()
		display_height = display.get_height()

		if self.state == STATE_LEVEL and self.cast_fail_frames > 0:
			tiles = self.red_ui_tiles
		else:
			tiles = self.ui_tiles

		# Draw borders between them
		cur_x = tile_size
		while cur_x + tile_size <= display_width:
			display.blit(tiles[UI_TOP], (cur_x, 0))
			display.blit(tiles[UI_BOTTOM], (cur_x, display_height - tile_size))
			cur_x += tile_size

		cur_y = tile_size
		while cur_y <= display_height:
			display.blit(tiles[UI_LEFT], (0, cur_y))
			display.blit(tiles[UI_RIGHT], (display_width - tile_size, cur_y))
			cur_y += tile_size

		# Draw each corner
		display.blit(tiles[UI_UPPER_LEFT], (0, 0))
		display.blit(tiles[UI_UPPER_RIGHT], (display_width - tile_size, 0))
		display.blit(tiles[UI_LOWER_LEFT], (0, display_height - tile_size))
		display.blit(tiles[UI_LOWER_RIGHT], (display_width - tile_size, display_height - tile_size))

	def draw_spell_icon(self, spell, surface, x, y, grey=False, animated=False):

		asset = get_spell_asset(spell)
		image = get_image(asset, alphafy=True)

		if not image:
			return

		frame = 4
		if isinstance(spell, Item):
			frame = 1

		x1 = 16 * frame
		icon = image.subsurface((x1, 0, 16, 16))

		if icon:
			surface.blit(icon, (x, y))

	def draw_character(self):

		self.draw_panel(self.character_display)

		self.char_panel_examine_lines = {}

		cur_x = self.border_margin
		cur_y = self.border_margin
		linesize = self.linesize

		hpcolor = (255, 255, 255)
		if self.game.p1.cur_hp <= 25:
			hpcolor = (255, 0, 0)

		self.draw_string("%s %d/%d" % (CHAR_HEART, self.game.p1.cur_hp, self.game.p1.max_hp), self.character_display, cur_x, cur_y, color=hpcolor)
		self.draw_string("%s" % CHAR_HEART, self.character_display, cur_x, cur_y, (255, 0, 0))
		cur_y += linesize

		if self.game.p1.shields:
			self.draw_string("%s %d" % (CHAR_SHIELD, self.game.p1.shields), self.character_display, cur_x, cur_y)
			self.draw_string("%s" % (CHAR_SHIELD), self.character_display, cur_x, cur_y, color=COLOR_SHIELD.to_tup())
			cur_y += linesize

		self.draw_string("SP %d" % self.game.p1.xp, self.character_display, cur_x, cur_y, color=COLOR_XP)
		cur_y += linesize

		self.draw_string("区域 %d" % self.game.level_num, self.character_display, cur_x, cur_y)
		cur_y += linesize

		# TODO- buffs here

		cur_y += linesize

		self.draw_string("法术: ", self.character_display, cur_x, cur_y)
		cur_y += linesize

		# Spells
		index = 1
		for spell in self.game.p1.spells:


			spell_number = (index) % 10
			mod_key = 'C' if index > 20 else 'S' if index > 10 else ''
			hotkey_str = "%s%d" % (mod_key, spell_number)

			if spell == self.cur_spell:
				cur_color = (0, 255, 0)
			elif spell.can_pay_costs():
				cur_color = (255, 255, 255)
			else:
				cur_color = (128, 128, 128)

			fmt = "%3s    %-17s%2d" % (hotkey_str, spell.name, spell.cur_charges)

			self.draw_string(fmt, self.character_display, cur_x, cur_y, cur_color, mouse_content=SpellCharacterWrapper(spell), char_panel=True)
			self.draw_spell_icon(spell, self.character_display, cur_x + self.space_width * 4, cur_y)

			cur_y += linesize
			index += 1

		cur_y += linesize
		# Items

		self.draw_string("物品: ", self.character_display, cur_x, cur_y)
		cur_y += linesize
		index = 1
		for item in self.game.p1.items:

			hotkey_str = "A%d" % (index % 10)

			cur_color = (255, 255, 255)
			if item.spell == self.cur_spell:
				cur_color = (0, 255, 0)
			fmt = "%3s    %-17s%2d" % (hotkey_str, item.name, item.quantity)

			self.draw_string(fmt, self.character_display, cur_x, cur_y, cur_color, mouse_content=item)
			self.draw_spell_icon(item, self.character_display, cur_x + self.space_width * 4, cur_y)

			cur_y += linesize
			index += 1

		# Buffs
		status_effects = [b for b in self.game.p1.buffs if b.buff_type != BUFF_TYPE_PASSIVE]
		counts = {}
		for effect in status_effects:
			if effect.name not in counts:
				counts[effect.name] = (effect, 0, 0, None)
			_, stacks, duration, color = counts[effect.name]
			stacks += 1
			duration = max(duration, effect.turns_left)

			counts[effect.name] = (effect, stacks, duration, effect.get_tooltip_color().to_tup())

		if status_effects:
			cur_y += linesize
			self.draw_string("状态效果: ", self.character_display, cur_x, cur_y, (255, 255, 255))
			cur_y += linesize
			for buff_name, (buff, stacks, duration, color) in counts.items():

				fmt = buff_name

				if stacks > 1:
					fmt += ' x%d' % stacks

				if duration:
					fmt += ' (%d)' % duration

				self.draw_string(fmt, self.character_display, cur_x, cur_y, color, mouse_content=buff)
				cur_y += linesize

		skills = [b for b in self.game.p1.buffs if b.buff_type == BUFF_TYPE_PASSIVE and not b.prereq]
		if skills:
			cur_y += linesize

			self.draw_string("能力: ", self.character_display, cur_x, cur_y)
			cur_y += linesize

			skill_x_max = self.character_display.get_width() - self.border_margin - 16
			for skill in skills:
				self.draw_spell_icon(skill, self.character_display, cur_x, cur_y)
				cur_x += 18
				if cur_x > skill_x_max:
					cur_x = self.border_margin
					cur_y += self.linesize

		cur_x = self.border_margin
		cur_y = self.character_display.get_height() - self.border_margin - 3*self.linesize

		self.draw_string("菜单 (ESC)", self.character_display, cur_x, cur_y, mouse_content=OPTIONS_TARGET)
		cur_y += linesize

		self.draw_string("帮助 (H)", self.character_display, cur_x, cur_y, mouse_content=INSTRUCTIONS_TARGET)
		cur_y += linesize

		color = self.game.p1.discount_tag.color.to_tup() if self.game.p1.discount_tag else (255, 255, 255)
		self.draw_string("角色界面 (C)", self.character_display, cur_x, cur_y, color=color, mouse_content=CHAR_SHEET_TARGET)

		self.screen.blit(self.character_display, (0, 0))

	def draw_examine(self):

		if (self.game and getattr(self.examine_target, "level", None) == self.game.cur_level) and self.game.deploying:
			self.examine_target = None

		self.examine_display.fill((0, 0, 0))

		self.draw_panel(self.examine_display)

		if self.examine_target:
			if isinstance(self.examine_target, Spell):
				self.draw_examine_spell()
			elif isinstance(self.examine_target, SpellCharacterWrapper):
				old = self.examine_target
				self.examine_target = self.examine_target.spell
				self.draw_examine_spell()
				self.examine_target = old
			elif isinstance(self.examine_target, Unit):
				self.draw_examine_unit()
			elif isinstance(self.examine_target, Buff):
				self.draw_examine_upgrade()
			#elif isinstance(self.examine_target, Buff):
			#   self.draw_examine_buff()
			elif isinstance(self.examine_target, Portal):
				self.draw_examine_portal()
			else:
				self.draw_examine_misc()
		elif self.game:
			if self.game.deploying:
				self.draw_examine_misc(DEPLOY_TARGET)
			elif self.game.has_granted_xp:
				self.draw_level_stats()
			elif self.game.level_num == 1:
				self.draw_examine_misc(WELCOME_TARGET)

		if self.game and self.game.gameover:
			self.draw_level_stats()

		self.screen.blit(self.examine_display, (self.screen.get_width() - self.h_margin, 0))

	def draw_examine_upgrade(self):
		path = ['UI', 'spell skill icons', self.examine_target.name.lower().replace(' ', '_') + '.png']
		self.draw_examine_icon()

		border_margin = self.border_margin
		cur_x = border_margin
		cur_y = border_margin

		width = self.examine_display.get_width() - 2 * border_margin
		lines = self.draw_wrapped_string(self.examine_target.name, self.examine_display, cur_x, cur_y, width=width)
		cur_y += self.linesize * (lines+1)

		# Draw upgrade tags
		if not getattr(self.examine_target, 'prereq', None) and hasattr(self.examine_target, 'tags'):
			for tag in Tags:
				if tag not in self.examine_target.tags:
					continue
				self.draw_string(tag.name, self.examine_display, cur_x, cur_y, (tag.color.r, tag.color.g, tag.color.b))
				cur_y += self.linesize
			cur_y += self.linesize

		if getattr(self.examine_target, 'level', None):
			self.draw_string("等级 %d" % self.examine_target.level, self.examine_display, cur_x, cur_y)
			cur_y += self.linesize

		cur_y += self.linesize

		is_passive = isinstance(self.examine_target, Upgrade) and not self.examine_target.prereq

		# Autogen boring part of description
		for tag, bonuses in self.examine_target.tag_bonuses.items():
			for attr, val in bonuses.items():
				#cur_color = tag.color
				fmt = "%s法术和能力获得 [%s_%s:%s]。" % (tag.name, val, attr, attr)
				lines = self.draw_wrapped_string(fmt, self.examine_display, cur_x, cur_y, width=width)
				cur_y += (lines+1) * self.linesize
			cur_y += self.linesize


		for spell, bonuses in self.examine_target.spell_bonuses.items():
			spell_ex = spell()

			useful_bonuses = [(attr, val) for (attr, val) in bonuses.items() if hasattr(spell_ex, attr)]
			if not useful_bonuses:
				continue

			for attr, val in useful_bonuses:
				if attr in tooltip_colors:
					fmt = "%s 获得 [%s_点%s:%s]" % (spell_ex.name, val, attr, attr)
				else:
					fmt = "%s 获得 %d %s" % (spell_ex.name, val, format_attr(attr))
				lines = self.draw_wrapped_string(fmt, self.examine_display, cur_x, cur_y, width=width)
				cur_y += (lines+1) * self.linesize
			cur_y += self.linesize

		for attr, val in self.examine_target.global_bonuses.items():
			if val >= 0:
				fmt = "所有法术和能力获得 %d %s" % (val, format_attr(attr))
			else:
				fmt = "所有法术和能力失去 %d %s" % (-val, format_attr(attr))
			lines = self.draw_wrapped_string(fmt, self.examine_display, cur_x, cur_y, width)
			cur_y += (lines+1) * self.linesize

		has_resists = False
		for tag in Tags:
			if tag not in self.examine_target.resists:
				continue
			self.draw_string('%d%% %s抵抗' % (self.examine_target.resists[tag], tag.name), self.examine_display, cur_x, cur_y, tag.color.to_tup())
			has_resists = True
			cur_y += self.linesize

		if has_resists:
			cur_y += self.linesize

		desc = self.examine_target.get_description()
		if not desc:
			desc = self.examine_target.get_tooltip()

		# Warn player about replacing shrine buffs
		if getattr(self.examine_target, 'shrine_name', None):
			existing = [b for b in self.game.p1.buffs if isinstance(b, Upgrade) and b.prereq == self.examine_target.prereq and b.shrine_name and b != self.examine_target]
			if existing:
				if not desc:
					desc = ""
				desc += "\nWARNING: Will replace %s" % existing[0].name

		if desc:
			self.draw_wrapped_string(desc, self.examine_display, cur_x, cur_y, width, extra_space=True)

	def draw_examine_misc(self, target=None):
		border_margin = self.border_margin
		cur_x = border_margin
		cur_y = border_margin


		if not target:
			target = self.examine_target

		if hasattr(target, "name"):
			lines = self.draw_wrapped_string(target.name, self.examine_display, cur_x, cur_y, width=23*16)
			cur_y += (lines + 1) * self.linesize
		if hasattr(target, "get_description"):
			self.draw_wrapped_string(target.get_description(), self.examine_display, cur_x, cur_y, self.examine_display.get_width() - 2 * self.border_margin, extra_space=True)
		elif hasattr(target, "description"):
			self.draw_wrapped_string(target.description, self.examine_display, cur_x, cur_y, self.examine_display.get_width() - 2 * self.border_margin, extra_space=True)

	def draw_examine_icon(self):

		icon = get_image(get_spell_asset(self.examine_target))
		if not icon:
			return

		self.examine_icon_surface.fill((0, 0, 0))

		source = (self.examine_icon_frame * SPRITE_SIZE, 0, SPRITE_SIZE, SPRITE_SIZE)
		self.examine_icon_surface.blit(icon, (0, 0), source)

		subsurface = self.examine_display.subsurface((self.examine_display.get_width() - self.border_margin - 64, self.border_margin, 64, 64))
		pygame.transform.scale(self.examine_icon_surface, (64, 64), subsurface)

		self.examine_icon_subframe += 1
		if self.examine_icon_subframe >= SUB_FRAMES[ANIM_IDLE]:
			self.examine_icon_subframe = 0
			self.examine_icon_frame += 1

			if self.examine_icon_frame >= icon.get_width() // SPRITE_SIZE:
				self.examine_icon_frame = 0

	def draw_examine_spell(self):

		self.draw_examine_icon()

		border_margin = self.border_margin
		cur_x = border_margin
		cur_y = border_margin
		linesize = self.linesize

		spell = self.examine_target
		self.draw_string(spell.name, self.examine_display, cur_x, cur_y)
		cur_y += linesize
		cur_y += linesize
		tag_x = cur_x
		for tag in Tags:
			if tag not in spell.tags:
				continue

			self.draw_string(tag.name, self.examine_display, tag_x, cur_y, (tag.color.r, tag.color.g, tag.color.b))
			cur_y += linesize
		cur_y += linesize

		if spell.level:
			self.draw_string("等级 %d" % spell.level, self.examine_display, cur_x, cur_y)
			cur_y += linesize

		if spell.melee:
			self.draw_string("近战范围", self.examine_display, cur_x, cur_y)
			cur_y += self.linesize
		elif spell.range:
			fmt = "射程 %d" % spell.get_stat('range')
			if not spell.requires_los:
				fmt += "（无需视线）"
			self.draw_string(fmt, self.examine_display, cur_x, cur_y)
			cur_y += self.linesize

		if spell.max_charges:
			self.draw_string("充能 %d/%d " % (self.examine_target.cur_charges, self.examine_target.get_stat('max_charges')), self.examine_display, cur_x, cur_y)
			cur_y += self.linesize

		cur_y += linesize

		lines = self.draw_wrapped_string(spell.get_description(), self.examine_display, cur_x, cur_y, self.examine_display.get_width() - 2*self.border_margin, extra_space=True)
		cur_y += linesize * lines

		if spell.spell_upgrades:
			self.draw_string("升级: ", self.examine_display, cur_x, cur_y)
			cur_y += linesize

			for upg in spell.spell_upgrades:

				cur_color = (255, 255, 255)
				if self.game.has_upgrade(upg):
					cur_color = (0, 255, 0)

				self.draw_string('%d - %s' % (upg.level, upg.name), self.examine_display, cur_x, cur_y, color=cur_color)
				cur_y += linesize

	def draw_examine_portal(self):


		border_margin = self.border_margin
		cur_x = border_margin
		cur_y = border_margin

		linesize = self.linesize

		gen_params = self.examine_target.level_gen_params

		self.draw_string("Rift", self.examine_display, cur_x, cur_y)
		cur_y += linesize

		if self.game.next_level:
			cur_y += linesize
			self.draw_string("????????", self.examine_display, cur_x, cur_y)
			return

		if self.examine_target.locked:
			cur_y += linesize

			width = self.examine_display.get_width() - 2*border_margin
			lines = self.draw_wrapped_string("(Defeat all enemies and destroy all gates to unlock)", self.examine_display, cur_x, cur_y, width)
			cur_y += lines*linesize

		cur_y += linesize

		self.draw_string("Contents:", self.examine_display, cur_x, cur_y)
		cur_y += 2*linesize

		images = []

		COLOR_POP = (255, 255, 255)
		COLOR_BOSS = (253, 143, 77)
		COLOR_ELITE = COLOR_BOSS
		COLOR_ENC = (255, 0, 0)

		for s, l in gen_params.spawn_options:
			unit = s()
			sprite_sheet = self.get_sprite_sheet(get_unit_asset(unit))
			images.append((sprite_sheet, unit.name, COLOR_POP))

			#lair_sheet = self.get_sprite_sheet('lair', fill_color=sprite_sheet.get_lair_color())
			#images.append((lair_sheet, '%s Lair' % unit.name))

		drawn_bosses = set()
		for b in gen_params.bosses:
			if b.name in drawn_bosses:
				continue
			# Dont draw old style bosses
			if 'boss' in b.get_asset_name():
				continue
			drawn_bosses.add(b.name)

			sprite_sheet = self.get_sprite_sheet(get_unit_asset(b))
			images.append((sprite_sheet, b.name, COLOR_BOSS if not b.is_boss else COLOR_ENC))

		for image, name, color in images:

			frame = (cloud_frame_clock // 12) % (len(image.anim_frames[ANIM_IDLE]))

			sprite = image.anim_frames[ANIM_IDLE][frame]
			scaledimage = pygame.transform.scale(sprite, (32, 32))

			self.examine_display.blit(scaledimage, (cur_x, cur_y))
			if len(name) > 20:
				name = name[0:18] + '..'
			self.draw_string(name, self.examine_display, cur_x + 36, cur_y + 10, color)
			cur_y += 32 + 4

		cur_y += linesize

		width = self.examine_display.get_width() - 2 *border_margin
		if gen_params.shrine:
			name = gen_params.shrine.name

			image = self.get_prop_image(gen_params.shrine)
			frame = (cloud_frame_clock // 12) % (image.get_width() // 16)
			sourcerect = (SPRITE_SIZE * frame, 0, SPRITE_SIZE, SPRITE_SIZE)
			subimage = image.subsurface(sourcerect)
			scaledimage = pygame.transform.scale(subimage, (64, 64))

			self.examine_display.blit(scaledimage, (cur_x, cur_y))

			self.draw_string(gen_params.shrine.name, self.examine_display, 64 + border_margin, cur_y + 24, content_width=width)

			cur_y += 64 + linesize

			lines = self.draw_wrapped_string(gen_params.shrine.description, self.examine_display, cur_x, cur_y, width, extra_space=True)
			cur_y += linesize * lines


		for item in gen_params.items:
			image = get_image(item.get_asset())

			frame = (cloud_frame_clock // 12) % (image.get_width() // 16)
			sourcerect = (SPRITE_SIZE * frame, 0, SPRITE_SIZE, SPRITE_SIZE)
			subimage = image.subsurface(sourcerect)
			scaledimage = pygame.transform.scale(subimage, (32, 32))

			self.examine_display.blit(scaledimage, (cur_x, cur_y))
			self.draw_string(item.name, self.examine_display, cur_x + 38, cur_y+8)

			cur_y += 32

		for s in gen_params.scroll_spells:
			asset = ['tiles', 'library', 'library_white']
			image = get_image(asset)

			frame = (cloud_frame_clock // 12) % (image.get_width() // 16)
			sourcerect = (SPRITE_SIZE * frame, 0, SPRITE_SIZE, SPRITE_SIZE)
			subimage = image.subsurface(sourcerect)
			scaledimage = pygame.transform.scale(subimage, (32, 32))

			self.examine_display.blit(scaledimage, (cur_x, cur_y))
			self.draw_wrapped_string(s.name, self.examine_display, cur_x + 38, cur_y+8, width - 38)

			cur_y += 32

		cur_x = border_margin



	def draw_examine_unit(self):

		# If a game is running, do not display dead monsters or the player
		if self.game:
			if self.examine_target.cur_hp <= 0:
				return

			if self.examine_target == self.game.p1:
				return

		if self.state == STATE_SHOP and self.shop_type == SHOP_TYPE_BESTIARY:
			if not SteamAdapter.has_slain(self.examine_target.name):
				return

		border_margin = self.border_margin
		cur_x = border_margin
		cur_y = border_margin
		linesize = self.linesize
		unit = self.examine_target

		lines = self.draw_wrapped_string(unit.name, self.examine_display, cur_x, cur_y, width=17*16)
		cur_y += (lines+1) * linesize

		if unit.team == TEAM_PLAYER:
			self.draw_string("Friendly", self.examine_display, cur_x, cur_y, Tags.Conjuration.color.to_tup())
			cur_y += linesize

		if unit.turns_to_death:
			self.draw_string("%d turns left" % unit.turns_to_death, self.examine_display, cur_x, cur_y)
			cur_y += linesize


		self.examine_icon_surface.fill((0, 0, 0))

		if not self.examine_target.Anim:
			self.examine_target.Anim = self.get_anim(self.examine_target)

		if self.examine_target.Anim:
			self.examine_target.Anim.draw(self.examine_icon_surface, True)

		subsurface = self.examine_display.subsurface((self.examine_display.get_width() - self.border_margin - 64, self.border_margin, 64, 64))
		pygame.transform.scale(self.examine_icon_surface, (64, 64), subsurface)


		self.draw_string("%s %d/%d" % (CHAR_HEART, unit.cur_hp, unit.max_hp), self.examine_display, cur_x, cur_y)
		self.draw_string("%s" % CHAR_HEART, self.examine_display, cur_x, cur_y, (255, 0, 0))
		cur_y += linesize

		if unit.shields:
			self.draw_string("%s %d" % (CHAR_SHIELD, unit.shields), self.examine_display, cur_x, cur_y)
			self.draw_string("%s" % (CHAR_SHIELD), self.examine_display, cur_x, cur_y, color=COLOR_SHIELD.to_tup())
			cur_y += linesize

		if unit.clarity:
			self.draw_string("%s %d" % (CHAR_CLARITY, unit.clarity), self.examine_display, cur_x, cur_y)
			self.draw_string("%s" % (CHAR_CLARITY), self.examine_display, cur_x, cur_y, color=COLOR_CLARITY)
			cur_y += linesize

		cur_y += linesize
		for tag in unit.tags:
			self.draw_string(tag.name, self.examine_display, cur_x, cur_y, (tag.color.r, tag.color.g, tag.color.b))
			cur_y += linesize

		cur_y += linesize
		for spell in unit.spells:
			if hasattr(spell, 'damage_type') and isinstance(spell.damage_type, Tag):
				cur_color = spell.damage_type.color.to_tup()
			else:
				cur_color = (255, 255, 255)

			fmt = "%s" % spell.name
			self.draw_string(fmt, self.examine_display, cur_x, cur_y, cur_color)
			cur_y += linesize
			hasattrs = False
			if hasattr(spell, 'damage'):
				if hasattr(spell, 'damage_type') and isinstance(spell.damage_type, Tag):
					fmt = ' %d %s damage' % (spell.get_stat('damage'), spell.damage_type.name)
				elif hasattr(spell, 'damage_type') and isinstance(spell.damage_type, list):
					fmt = ' %d %s damage' % (spell.damage, ' or '.join([t.name for t in spell.damage_type]))
				else:
					fmt = ' %d damage' % spell.get_stat('damage')
				lines = self.draw_wrapped_string(fmt, self.examine_display, cur_x, cur_y, self.examine_display.get_width() - 2*border_margin, color=COLOR_DAMAGE.to_tup())
				cur_y += lines * linesize
				hasattrs = True
			if spell.range > 1.5:
				fmt = ' %d range' % spell.get_stat('range')
				self.draw_string(fmt, self.examine_display, cur_x, cur_y, COLOR_RANGE.to_tup())
				cur_y += linesize
				hasattrs = True
			if hasattr(spell, 'radius') and spell.get_stat('radius') > 0:
				fmt = ' %d radius' % spell.radius
				self.draw_string(fmt, self.examine_display, cur_x, cur_y, attr_colors['radius'].to_tup())
				cur_y += linesize
				hasattrs = True
			if spell.cool_down > 0:
				rem_cd = spell.caster.cool_downs.get(spell, 0)
				if not rem_cd:
					fmt = ' %d turn cooldown' % spell.cool_down
				else:
					fmt = ' %d turn cooldown (%d)' % (spell.cool_down, rem_cd)
				self.draw_string(fmt, self.examine_display, cur_x, cur_y)
				cur_y += linesize
				hasattrs = True

			# Prioritize spell.description so it can be overriden
			desc = spell.description or spell.get_description()
			if desc:
				indent = 16
				lines = self.draw_wrapped_string(desc, self.examine_display, cur_x+16, cur_y, self.examine_display.get_width() - (indent+2*border_margin))
				cur_y += lines*linesize
			cur_y += linesize

		if unit.flying:
			self.draw_string("Flying", self.examine_display, cur_x, cur_y)
			cur_y += linesize

		if unit.stationary:
			self.draw_string("Immobile", self.examine_display, cur_x, cur_y)
			cur_y += linesize

		if unit.flying or unit.stationary:
			cur_y += linesize

		resist_tags = [t for t in Tags if t in self.examine_target.resists and self.examine_target.resists[t] != 0]
		resist_tags.sort(key = lambda t: -self.examine_target.resists[t])

		for negative in [False, True]:
			has_resists = False
			for tag in resist_tags:

				if not ((self.examine_target.resists[tag] < 0) == negative):
					continue

				self.draw_string('%d%% Resist %s' % (self.examine_target.resists[tag], tag.name), self.examine_display, cur_x, cur_y, tag.color.to_tup())
				has_resists = True
				cur_y += self.linesize

			if has_resists:
				cur_y += self.linesize

		# Unit Passives
		for buff in unit.buffs:
			if buff.buff_type != BUFF_TYPE_PASSIVE:
				continue

			buff_desc = buff.get_tooltip()
			if not buff_desc:
				continue

			buff_color = buff.get_tooltip_color()
			if not buff_color:
				buff_color = Color(255, 255, 255)
			buff_color = (buff_color.r, buff_color.g, buff_color.b)


			lines = self.draw_wrapped_string(buff_desc, self.examine_display, cur_x, cur_y, self.examine_display.get_width() - 2*border_margin, buff_color)
			cur_y += linesize * (lines+1)

		cur_y += linesize

		status_effects = [b for b in self.examine_target.buffs if b.buff_type != BUFF_TYPE_PASSIVE]
		counts = {}
		for effect in status_effects:
			if effect.name not in counts:
				counts[effect.name] = (effect, 0, 0, None)
			_, stacks, duration, color = counts[effect.name]
			stacks += 1
			duration = max(duration, effect.turns_left)

			counts[effect.name] = (effect, stacks, duration, effect.get_tooltip_color().to_tup())


		if status_effects:
			cur_y += linesize
			self.draw_string("Status Effects:", self.examine_display, cur_x, cur_y, (255, 255, 255))
			cur_y += linesize
			for buff_name, (buff, stacks, duration, color) in counts.items():

				fmt = buff_name

				if stacks > 1:
					fmt += ' x%d' % stacks

				if duration:
					fmt += ' (%d)' % duration

				self.draw_string(fmt, self.examine_display, cur_x, cur_y, color, mouse_content=buff)
				cur_y += linesize


	def draw_title(self):
		title_disp_frame = self.title_frame // 16 % 2
		self.screen.blit(self.title_image, (0, 0, 1600, 900), (title_disp_frame*1600, 0, 1600, 900))

		m_loc = self.get_mouse_pos()

		self.title_frame += 1

		cur_x = 770
		cur_y = 560

		rect_w = self.font.size("继续游戏")[0]

		opts = []
		if can_continue_game():
			opts.append((TITLE_SELECTION_LOAD, "继续冒险"))
			opts.append((TITLE_SELECTION_ABANDON, "放弃冒险"))
		else:
			opts.append((TITLE_SELECTION_NEW, "开始游戏"))

		opts.extend([(TITLE_SELECTION_OPTIONS, "游戏设置"),
					 (TITLE_SELECTION_INSTRUCTIONS, "如何游玩"),
					 (TITLE_SELECTION_BESTIARY, "怪物图鉴"),
					 (TITLE_SELECTION_DISCORD, "DISCORD"),
					 (TITLE_SELECTION_QQ, "QQ 群"),
					 (TITLE_SELECTION_EXIT, "退出游戏")])

		for o, w in opts:

			cur_color = (255, 255, 255)
			self.draw_string(w, self.screen, cur_x, cur_y, cur_color, mouse_content=o, content_width=rect_w)
			cur_y += self.linesize + 2

		cur_y += 3*self.linesize

		#self.draw_string("Wins:   %d" % SteamAdapter.get_stat('w'), self.screen, cur_x, cur_y)
		cur_y += self.linesize
		#self.draw_string("Loses:  %d" % SteamAdapter.get_stat('l'), self.screen, cur_x, cur_y)
		cur_y += self.linesize
		#self.draw_string("Streak: %d" % SteamAdapter.get_stat('s'), self.screen, cur_x, cur_y)

	def process_title_input(self):
		selection = None
		m_loc = self.get_mouse_pos()

		for evt in self.events:
			if evt.type == pygame.KEYDOWN:

				if evt.key in self.key_binds[KEY_BIND_CONFIRM]:
					self.play_sound('menu_confirm')
					selection = self.examine_target

				direction = 0
				if evt.key in self.key_binds[KEY_BIND_UP] or evt.key in self.key_binds[KEY_BIND_LEFT]:
					direction = -1

				elif evt.key in self.key_binds[KEY_BIND_DOWN] or evt.key in self.key_binds[KEY_BIND_RIGHT]:
					direction = 1

				if direction:
					self.play_sound('menu_confirm')
					self.examine_target += direction
					self.examine_target = min(self.examine_target, TITLE_SELECTION_MAX)

					min_selection = TITLE_SELECTION_LOAD if can_continue_game() else TITLE_SELECTION_NEW
					self.examine_target = max(min_selection, self.examine_target)

					# do not allow selection of new game no savegame exists
					if can_continue_game():
						if self.examine_target == TITLE_SELECTION_NEW:
							self.examine_target += direction

			if evt.type == pygame.MOUSEBUTTONDOWN:

				if evt.button == pygame.BUTTON_LEFT:
					for r, o in self.ui_rects:
						if r.collidepoint(m_loc):
							self.play_sound('menu_confirm')
							selection = o
							break
					else:
						self.play_sound('menu_abort')

		dx, dy = self.get_mouse_rel()
		if dx or dy:
			for r, o in self.ui_rects:
				if r.collidepoint(m_loc):
					if self.examine_target != o:
						self.play_sound('menu_confirm')
					self.examine_target = o

		if selection == TITLE_SELECTION_NEW:
			self.state = STATE_PICK_MODE
			self.examine_target = 0
		if selection == TITLE_SELECTION_LOAD:
			if can_continue_game():
				self.load_game()
		if selection == TITLE_SELECTION_ABANDON:
			self.open_abandon_prompt()
		if selection == TITLE_SELECTION_OPTIONS:
			self.open_options()
		if selection == TITLE_SELECTION_INSTRUCTIONS:
			self.show_help()
		if selection == TITLE_SELECTION_BESTIARY:
			self.open_shop(SHOP_TYPE_BESTIARY)
		if selection == TITLE_SELECTION_DISCORD:
			webbrowser.open("https://discord.gg/NngFZ7B")
		if selection == TITLE_SELECTION_QQ:
			webbrowser.open("https://jq.qq.com/?_wv=1027&k=C1ejcsdb")
		if selection == TITLE_SELECTION_EXIT:
			self.running = False

	def draw_pick_mode(self):
		opts = [("普通冒险", GAME_MODE_NORMAL),
				("魔导师的试炼", GAME_MODE_TRIALS),
				("每周挑战", GAME_MODE_WEEKLY)]

		rect_w = self.font.size("魔导师的试炼")[0]
		cur_x = self.screen.get_width() // 2 - (self.font.size("魔导师的试炼")[0] // 2)
		cur_y = self.screen.get_height() // 2 - self.linesize * 4

		cur_color = (255, 255, 255)
		for t, o in opts:

			cur_color = (255, 255, 255)

			self.draw_string(t, self.screen, cur_x, cur_y, cur_color, mouse_content=o, content_width=rect_w)
			if ((o == GAME_MODE_NORMAL and SteamAdapter.get_stat('w')) or
			   (o == GAME_MODE_WEEKLY and SteamAdapter.get_trial_status(get_weekly_name())) or
			   (o == GAME_MODE_TRIALS and all(SteamAdapter.get_trial_status(t.name) for t in all_trials))):
				self.draw_string("*", self.screen, cur_x - 16, cur_y, COLOR_VICTORY)

			cur_y += self.linesize

	def process_pick_mode_input(self):

		selection = None
		m_loc = self.get_mouse_pos()

		for evt in self.events:
			if evt.type == pygame.KEYDOWN:

				if evt.key in [pygame.K_RETURN, pygame.K_KP_ENTER]:
					self.play_sound('menu_confirm')
					selection = self.examine_target

				if evt.key in [pygame.K_UP, pygame.K_KP8, pygame.K_LEFT, pygame.K_KP4]:
					self.play_sound('menu_confirm')
					if self.examine_target is None:
						self.examine_target = 0
					else:
						self.examine_target -= 1
						self.examine_target = max(0, self.examine_target)
				if evt.key in [pygame.K_DOWN, pygame.K_KP2, pygame.K_RIGHT, pygame.K_KP6]:
					self.play_sound('menu_confirm')
					if self.examine_target is None:
						self.examine_target = 0
					else:
						self.examine_target += 1
						self.examine_target = min(self.examine_target, GAME_MODE_MAX)

				if evt.key in [pygame.K_ESCAPE]:
					self.state = STATE_TITLE
					self.examine_target = TITLE_SELECTION_NEW
					self.play_sound('menu_abort')

			if evt.type == pygame.MOUSEBUTTONDOWN:

				if evt.button == pygame.BUTTON_LEFT:
					for r, o in self.ui_rects:
						if r.collidepoint(m_loc):
							self.play_sound('menu_confirm')
							selection = o
							break
					else:
						self.play_sound('menu_abort')

				if evt.button == pygame.BUTTON_RIGHT:
					self.state = STATE_TITLE
					self.play_sound('menu_abort')

		dx, dy = self.get_mouse_rel()
		if dx or dy:
			for r, o in self.ui_rects:
				if r.collidepoint(m_loc):
					if self.examine_target != o:
						self.play_sound('menu_confirm')
					self.examine_target = o

		if selection == GAME_MODE_NORMAL:
			self.new_game()
		if selection == GAME_MODE_TRIALS:
			self.state = STATE_PICK_TRIAL
			self.examine_target = all_trials[0]
		if selection == GAME_MODE_WEEKLY:
			self.new_game(mutators=get_weekly_mutators(), seed=get_weekly_seed(), trial_name=get_weekly_name())
		# TODO: all other modes


	def draw_pick_trial(self):

		rect_w = max(self.font.size(trial.name)[0] for trial in all_trials)
		cur_x = self.screen.get_width() // 2 - rect_w // 2
		cur_y = self.screen.get_height() // 2 - self.linesize * 4

		cur_color = (255, 255, 255)
		for trial in all_trials:
			self.draw_string(trial.name, self.screen, cur_x, cur_y, cur_color, mouse_content=trial, content_width=rect_w)
			if SteamAdapter.get_trial_status(trial.name):
				self.draw_string("*", self.screen, cur_x - 16, cur_y, COLOR_VICTORY)
			cur_y += self.linesize

		cur_y += self.linesize * 6

		if isinstance(self.examine_target, Trial):
			desc = self.examine_target.get_description()
			for line in desc.split('\n'):
				cur_x = (self.screen.get_width() // 2) - (self.font.size(line)[0] // 2)
				self.draw_string(line, self.screen, cur_x, cur_y)
				cur_y += self.linesize

	def process_pick_trial_input(self):
		selection = None
		m_loc = self.get_mouse_pos()

		for evt in self.events:
			if evt.type == pygame.KEYDOWN:

				if evt.key in [pygame.K_RETURN, pygame.K_KP_ENTER]:
					self.play_sound('menu_confirm')
					selection = self.examine_target

				if evt.key in [pygame.K_UP, pygame.K_KP8, pygame.K_LEFT, pygame.K_KP4]:
					self.play_sound('menu_confirm')
					if self.examine_target is None or self.examine_target not in all_trials:
						self.examine_target = all_trials[0]
					else:
						cur_index = all_trials.index(self.examine_target)
						new_index = cur_index - 1
						new_index = max(0, new_index)
						self.examine_target = all_trials[new_index]

				if evt.key in [pygame.K_DOWN, pygame.K_KP2, pygame.K_RIGHT, pygame.K_KP6]:
					self.play_sound('menu_confirm')
					if self.examine_target is None or self.examine_target not in all_trials:
						self.examine_target = all_trials[0]
					else:
						cur_index = all_trials.index(self.examine_target)
						new_index = cur_index + 1
						new_index = min(new_index, len(all_trials) - 1)
						self.examine_target = all_trials[new_index]

				if evt.key in [pygame.K_ESCAPE]:
					self.state = STATE_TITLE
					self.examine_target = TITLE_SELECTION_NEW
					self.play_sound('menu_abort')

			if evt.type == pygame.MOUSEBUTTONDOWN:

				if evt.button == pygame.BUTTON_LEFT:
					for r, o in self.ui_rects:
						if r.collidepoint(m_loc):
							self.play_sound('menu_confirm')
							selection = o
							break
					else:
						self.play_sound('menu_abort')

				if evt.button == pygame.BUTTON_RIGHT:
					self.state = STATE_TITLE
					self.play_sound('menu_abort')

		dx, dy = self.get_mouse_rel()
		if dx or dy:
			for r, o in self.ui_rects:
				if r.collidepoint(m_loc):
					if self.examine_target != o:
						self.play_sound('menu_confirm')
					self.examine_target = o

		if selection:
			self.new_game(trial_name=selection.name, mutators=selection.mutators)

	def draw_options_menu(self):

		cur_x = self.screen.get_width() // 2 - self.font.size("Sound Volume")[0]
		cur_y = self.screen.get_height() // 2 - self.linesize * OPTION_MAX

		rect_w = self.font.size("动画速度: 最快")[0]

		self.draw_string("如何游玩", self.screen, cur_x, cur_y, mouse_content=OPTION_HELP, content_width=rect_w)
		cur_y += self.linesize

		self.draw_string("音效大小: %3d" % self.options['sound_volume'], self.screen, cur_x, cur_y, mouse_content=OPTION_SOUND_VOLUME, content_width=rect_w)
		cur_y += self.linesize

		self.draw_string("音乐大小: %3d" % self.options['music_volume'], self.screen, cur_x, cur_y, mouse_content=OPTION_MUSIC_VOLUME, content_width=rect_w)
		cur_y += self.linesize

		if self.options['spell_speed'] == 0:
			speed_fmt = "普通"
		elif self.options['spell_speed'] == 1:
			speed_fmt = "快速"
		if self.options['spell_speed'] == 2:
			speed_fmt = "更快"
		if self.options['spell_speed'] == 3:
			speed_fmt = "最快"


		self.draw_string("动画速度: %s" % speed_fmt, self.screen, cur_x, cur_y, mouse_content=OPTION_SPELL_SPEED, content_width=rect_w)
		cur_y += self.linesize

		self.draw_string("调整键位", self.screen, cur_x, cur_y, mouse_content=OPTION_CONTROLS, content_width=rect_w)
		cur_y += self.linesize

		#self.draw_string("Smart Targeting: %5s" % str(self.options['smart_targeting']), self.screen, cur_x, cur_y, mouse_content=OPTION_SMART_TARGET, content_width=rect_w)
		#cur_y += self.linesize

		if self.game:
			self.draw_string("继续游戏", self.screen, cur_x, cur_y, mouse_content=OPTION_RETURN, content_width=rect_w)
			cur_y += self.linesize

			self.draw_string("保存并退出", self.screen, cur_x, cur_y, mouse_content=OPTION_EXIT, content_width=rect_w)
			cur_y += self.linesize

		else:
			self.draw_string("返回标题界面", self.screen, cur_x, cur_y, mouse_content=OPTION_EXIT, content_width=rect_w)
			cur_y += self.linesize


	def draw_message(self):
		cur_y = self.border_margin
		for line in self.message.split('\n'):
			if line:
				self.draw_string(line, self.screen, 0, cur_y, center=self.center_message, content_width=self.screen.get_width())
			cur_y += self.linesize


	def process_message_input(self):
		for evt in self.events:
			if evt.type in [pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN]:
				self.play_sound("menu_confirm")
				if self.next_message:
					self.message = self.next_message
					self.next_message = None
				elif self.game:
					self.state = STATE_LEVEL
				else:
					self.state = STATE_TITLE

	def show_help(self):
		self.state = STATE_MESSAGE
		self.center_message = False
		self.message = text.how_to_play
		self.next_message = text.advanced_tips

	def adjust_volume(self, amount, stype):
		if not self.can_play_sound:
			return

		cur_volume = self.options['%s_volume' % stype]
		new_volume = cur_volume + amount

		new_volume = new_volume % 110

		self.options['%s_volume' % stype] = new_volume

		if stype == 'music':
			amt = new_volume / 100.0
			pygame.mixer.music.set_volume(new_volume / 100.0)

		if stype == 'sound':
			for channel, base_volume in self.base_volumes.items():
				channel.set_volume(base_volume * new_volume / 100.0)

		self.save_options()

	def toggle_smart_targeting(self):
		self.options['smart_targeting'] = not self.options['smart_targeting']
		self.save_options()

	def save_options(self):
		with open('options2.dat', 'wb') as options_file:
			self.options['key_binds'] = self.key_binds
			pickle.dump(self.options, file=options_file)

	def exit_options(self):
		if self.game:
			self.game.save_game()
		self.return_to_title()

	def process_options_input(self):
		for evt in [e for e in self.events if e.type == pygame.KEYDOWN]:

			if evt.key in self.key_binds[KEY_BIND_UP]:
				if self.examine_target is None:
					self.examine_target = 0
				else:
					self.examine_target -= 1
					if not self.game and self.examine_target == OPTION_RETURN:
						self.examine_target -= 1
					self.examine_target = max(0, self.examine_target)
					self.play_sound("menu_confirm")
			if evt.key in self.key_binds[KEY_BIND_DOWN]:
				if self.examine_target is None:
					self.examine_target = 0
				else:
					self.examine_target += 1
					if not self.game and self.examine_target == OPTION_RETURN:
						self.examine_target += 1
					self.examine_target = min(self.examine_target, OPTION_MAX)
					self.play_sound("menu_confirm")

			if evt.key in self.key_binds[KEY_BIND_LEFT]:
				self.play_sound("menu_confirm")
				if self.examine_target == OPTION_MUSIC_VOLUME:
					self.adjust_volume(-10, 'music')
				if self.examine_target == OPTION_SOUND_VOLUME:
					self.adjust_volume(-10, 'sound')
				if self.examine_target == OPTION_SMART_TARGET:
					self.toggle_smart_targeting()
				if self.examine_target == OPTION_SPELL_SPEED:
					self.options['spell_speed'] = (self.options['spell_speed'] - 1) % 4

			if evt.key in self.key_binds[KEY_BIND_RIGHT]:
				self.play_sound("menu_confirm")
				if self.examine_target == OPTION_MUSIC_VOLUME:
					self.adjust_volume(10, 'music')
				if self.examine_target == OPTION_SOUND_VOLUME:
					self.adjust_volume(10, 'sound')
				if self.examine_target == OPTION_SMART_TARGET:
					self.toggle_smart_targeting()
				if self.examine_target == OPTION_SPELL_SPEED:
					self.options['spell_speed'] = (self.options['spell_speed'] + 1) % 4


			if evt.key in self.key_binds[KEY_BIND_CONFIRM]:
				if self.examine_target == OPTION_EXIT:
					if self.game:
						self.game.save_game()
					self.return_to_title()

				elif self.examine_target == OPTION_RETURN:
					self.play_sound("menu_confirm")
					self.state = STATE_LEVEL
				elif self.examine_target == OPTION_HELP:
					self.play_sound("menu_confirm")
					self.show_help()
				elif self.examine_target == OPTION_SMART_TARGET:
					self.toggle_smart_targeting()
				elif self.examine_target == OPTION_CONTROLS:
					self.open_key_rebind()
				elif self.examine_target == OPTION_SPELL_SPEED:
					self.options['spell_speed'] = (self.options['spell_speed'] + 1) % 4


			if evt.key in self.key_binds[KEY_BIND_ABORT]:
				self.state = STATE_LEVEL if self.game else STATE_TITLE
				if self.state == STATE_TITLE:
					self.examine_target = TITLE_SELECTION_LOAD if can_continue_game() else TITLE_SELECTION_NEW
				self.play_sound("menu_confirm")


		m_loc = self.get_mouse_pos()
		for evt in [e for e in self.events if e.type == pygame.MOUSEBUTTONDOWN]:

			for r, o in self.ui_rects:
				if r.collidepoint(m_loc):
					if evt.button == pygame.BUTTON_LEFT:
						self.play_sound("menu_confirm")
						if o == OPTION_EXIT:
							self.save_options()
							if self.game:
								self.game.save_game()
							self.return_to_title()
							break
						if o == OPTION_RETURN:
							self.play_sound("menu_confirm")
							self.state = STATE_LEVEL
							break
						if o == OPTION_HELP:
							self.play_sound("menu_confirm")
							self.show_help()
							break
						if o == OPTION_SOUND_VOLUME:
							self.adjust_volume(10, 'sound')
							break
						if o == OPTION_MUSIC_VOLUME:
							self.adjust_volume(10, 'music')
							break
						if o == OPTION_SMART_TARGET:
							self.toggle_smart_targeting()
							break
						if self.examine_target == OPTION_CONTROLS:
							self.open_key_rebind()
							break
						elif self.examine_target == OPTION_SPELL_SPEED:
							self.options['spell_speed'] = (self.options['spell_speed'] + 1) % 4
							break

					if evt.button == pygame.BUTTON_RIGHT:
						self.play_sound("menu_confirm")
						if o == OPTION_SOUND_VOLUME:
							self.adjust_volume(-10, 'sound')
							break
						if o == OPTION_MUSIC_VOLUME:
							self.adjust_volume(-10, 'music')
							break
						elif self.examine_target == OPTION_SPELL_SPEED:
							self.options['spell_speed'] = (self.options['spell_speed'] - 1) % 4
							break
			else:
				self.play_sound("menu_confirm")
				if self.game:
					self.state = STATE_LEVEL
				else:
					self.return_to_title()

	def open_combat_log(self):
		self.combat_log_level = self.game.level_num
		self.combat_log_offset = 0
		self.combat_log_turn = 0

		if self.game.cur_level.turn_no == 1 and self.game.level_num > 1:
			self.combat_log_level = self.game.level_num - 1

		self.set_combat_log_display(self.combat_log_level, self.combat_log_max_turn())


		self.state = STATE_COMBAT_LOG

	def set_combat_log_display(self, level, turn):
		self.combat_log_level = level
		self.combat_log_turn = turn
		self.combat_log_lines = []

		log_fn = os.path.join('saves', str(self.game.run_number), 'log', str(level), 'combat_log.%d.txt' % turn)
		if os.path.exists(log_fn):
			with open(log_fn, 'r') as logfile:
				self.combat_log_lines = [s.strip() for s in logfile.readlines()]

	def draw_combat_log(self):
		cur_x = self.border_margin
		cur_y = self.border_margin

		self.middle_menu_display.fill((0, 0, 0))
		self.draw_panel(self.middle_menu_display)

		self.draw_string("等级 %d" % self.combat_log_level, self.middle_menu_display, cur_x, cur_y)
		cur_y += self.linesize
		self.draw_string("回合 %d" % self.combat_log_turn, self.middle_menu_display, cur_x, cur_y)
		cur_y += self.linesize
		cur_y += self.linesize

		for line in self.combat_log_lines[1+ self.combat_log_offset:]:

			lines = self.draw_wrapped_string(line, self.middle_menu_display, cur_x, cur_y, self.middle_menu_display.get_width())
			cur_y += lines * self.linesize

			if cur_y + self.border_margin > self.middle_menu_display.get_height():
				break

		self.screen.blit(self.middle_menu_display, (self.h_margin, 0))

	def combat_log_max_turn(self):
		cur_dir = os.path.join('saves', str(self.game.run_number), 'log', str(self.combat_log_level))
		log_files = [f for f in os.listdir(cur_dir) if f.startswith('combat_log.')]
		return len(log_files) - 1 # highest turn num in cur dir, minus current turn

	def combat_log_scroll(self, direction):
		min_turn = 1
		max_turn = self.combat_log_max_turn()

		min_level = 1
		max_level = self.game.level_num

		self.combat_log_turn += direction
		# Trying to go to prev level
		if self.combat_log_turn < min_turn:
			# Go to prev level if possible
			if self.combat_log_level > min_level:
				self.combat_log_level -= 1
				self.combat_log_turn = self.combat_log_max_turn()
			# Else undo change
			else:
				self.combat_log_turn -= direction
		# Trying to go to next level
		elif self.combat_log_turn > max_turn:
			# Go to next level if possible
			if self.combat_log_level < max_level:
				self.combat_log_level += 1
				self.combat_log_turn = min_turn
			# Else undo change
			else:
				self.combat_log_turn -= direction

		self.set_combat_log_display(self.combat_log_level, self.combat_log_turn)

	def process_combat_log_input(self):
		for evt in [e for e in self.events if e.type == pygame.KEYDOWN]:
			if evt.key in self.key_binds[KEY_BIND_ABORT]:
				self.state = STATE_LEVEL
			if evt.key in self.key_binds[KEY_BIND_UP]:
				self.combat_log_offset -= 1
				self.combat_log_offset = max(0, self.combat_log_offset)
			if evt.key in self.key_binds[KEY_BIND_DOWN]:
				self.combat_log_offset += 1
				self.combat_log_offset = min(self.combat_log_offset, len(self.combat_log_lines) - 1)
			if evt.key in self.key_binds[KEY_BIND_LEFT]:
				self.combat_log_scroll(-1)
			if evt.key in self.key_binds[KEY_BIND_RIGHT]:
				self.combat_log_scroll(1)
			if evt.key in self.key_binds[KEY_BIND_MESSAGE_LOG]:
				self.state = STATE_LEVEL


	def new_game(self, mutators=None, trial_name=None, seed=None):

		# If you are overwriting an old game, break streak
		if can_continue_game():
			SteamAdapter.set_stat('s', 0)
			SteamAdapter.set_stat('l', SteamAdapter.get_stat('l') + 1)

		self.game = Game(save_enabled=True, mutators=mutators, trial_name=trial_name, seed=seed)
		self.message = text.intro_text

		if mutators:
			self.message += "\n\n\n\n挑战修正: "
			for mutator in mutators:
				self.message += "\n" + mutator.description

		self.center_message = True
		self.state = STATE_MESSAGE
		self.play_music('battle_2')
		self.make_level_screenshot()
		SteamAdapter.set_presence_level(1)

	def make_level_screenshot(self):

		self.draw_level()
		self.draw_character()
		fake_portal = Portal(self.game.cur_level.gen_params)
		self.examine_target = fake_portal
		self.draw_examine()


		filename = os.path.join('saves', str(self.game.run_number), 'level_%d_begin.png' % self.game.level_num)

		dirname = os.path.dirname(filename)
		if not os.path.exists(dirname):
			os.makedirs(dirname)

		pygame.image.save(self.screen, filename)

		self.examine_target = None
		self.draw_examine()

	def make_level_end_screenshot(self):

		self.draw_level()
		self.draw_character()

		self.examine_display.fill((0, 0, 0))
		self.draw_panel(self.examine_display)

		self.draw_level_stats()

		self.screen.blit(self.examine_display, (self.screen.get_width() - self.h_margin, 0))

		#TODO HERE: draw a panel on the right with the summary text

		filename = os.path.join('saves', str(self.game.run_number), 'level_%d_finish.png' % self.game.level_num)

		dirname = os.path.dirname(filename)
		if not os.path.exists(dirname):
			os.makedirs(dirname)

		pygame.image.save(self.screen, filename)

	def draw_level_stats(self):
		# TODO- this is really gross and expensive- either cache it or do it without a file
		# But it never happens during a busy frame so I dont care right now
		stats_filename = os.path.join('saves', str(self.game.run_number), 'stats.level_%d.txt' % self.game.level_num)
		if not os.path.exists(stats_filename):
			# Occurs when cheating in debug
			return

		with open(stats_filename, 'r') as statfile:
			lines = [s.strip() for s in statfile.readlines()]

		border_margin = self.border_margin
		cur_x = border_margin
		cur_y = border_margin
		self.draw_panel(self.examine_display)
		for line in lines:
			num_lines = self.draw_wrapped_string(line, self.examine_display, cur_x, cur_y, width=self.examine_display.get_width() - (self.border_margin*2), indent=True)
			cur_y += num_lines * self.linesize

	def make_game_end_screenshot(self):

		self.examine_display.fill((0, 0, 0))
		self.draw_char_sheet()
		self.draw_character()

		filename = os.path.join('saves', str(self.game.run_number), 'char_sheet.png')

		dirname = os.path.dirname(filename)
		if not os.path.exists(dirname):
			os.makedirs(dirname)

		pygame.image.save(self.screen, filename)

		self.draw_examine()

	def load_game(self, filename=None):
		self.game = continue_game(filename=filename)
		self.state = STATE_LEVEL
		if self.game.level_num != LAST_LEVEL:
			self.play_music('battle_2')
		else:
			self.play_music('mordred_theme')

	def return_to_title(self):
		self.game = None
		self.effects = []
		self.effect_queue = []
		self.state = STATE_TITLE
		self.gameover_frames = 0
		self.deploy_anim_frames = 0

		if can_continue_game():
			self.examine_target = TITLE_SELECTION_LOAD
		else:
			self.examine_target = TITLE_SELECTION_NEW

		self.play_music('battle_1')

		SteamAdapter.set_presence_menu()


	def open_options(self):
		self.play_sound("menu_confirm")
		self.state = STATE_OPTIONS
		self.examine_target = 0

	def draw_gameover(self):

		if self.gameover_frames <= 8:
			self.gameover_tiles = [(x, y) for x in range(LEVEL_SIZE) for y in range(LEVEL_SIZE)]

		random.shuffle(self.gameover_tiles)

		if self.gameover_frames < 15 * 1:
			return

		speed = (self.gameover_frames - 15 * 1) // 25
		for i in range(speed):

			if not self.gameover_tiles:
				break

			x, y = self.gameover_tiles.pop()
			rect = (x*SPRITE_SIZE*2 + self.character_display.get_width(),
					y*SPRITE_SIZE*2,
					2*SPRITE_SIZE,
					2*SPRITE_SIZE)

			pygame.draw.rect(self.screen, (0, 0, 0,), rect)

		if not self.gameover_tiles:
			if self.game.victory:
				cur_y = self.screen.get_height() // 2 - 200
				for line in text.victory_text.split('\n'):
					if line:
						self.draw_string(line, self.screen, 0, cur_y, center=True, content_width=self.screen.get_width())
					cur_y += self.linesize

			else:
				end_message = "DEFEATED"
				self.draw_string(end_message, self.screen, self.screen.get_width() // 2 - (self.font.size(end_message)[0] // 2), self.screen.get_height() // 2 - 100)


	def run(self):

		self.running = True
		profile = False

		# Disable garbage collection, manually collect at start of each level
		# Cause the game takes ~40mb of RAM and the occasionall hiccup is not worth it
		gc.disable()
		frame_time = 0
		while self.running:

			global cloud_frame_clock
			cloud_frame_clock += 1
			cloud_frame_clock %= 100000

			global idle_frame, idle_subframe
			idle_subframe += 1
			if idle_subframe >= SUB_FRAMES[ANIM_IDLE]:
				idle_subframe = 0
				idle_frame += 1
				idle_frame = idle_frame % 2


			self.clock.tick(30)
			self.events = pygame.event.get()

			keys = pygame.key.get_pressed()
			for repeat_key, repeat_time in list(self.repeat_keys.items()):

				if keys[repeat_key] and time.time() > repeat_time:
					self.events.append(pygame.event.Event(pygame.KEYDOWN, key=repeat_key))
					self.repeat_keys[repeat_key] = time.time() + REPEAT_INTERVAL

				if not keys[repeat_key]:
					del self.repeat_keys[repeat_key]

			for event in self.events:
				if event.type == pygame.QUIT:
					if self.game and self.game.p1.is_alive():
						self.game.save_game()
					self.running = False

				# Allow repeating of directional keys (but no other keys)
				if event.type == pygame.KEYDOWN and event.key not in self.repeat_keys:
					for bind in [KEY_BIND_LEFT, KEY_BIND_UP_LEFT, KEY_BIND_UP, KEY_BIND_UP_RIGHT,
								 KEY_BIND_RIGHT, KEY_BIND_DOWN_RIGHT, KEY_BIND_DOWN, KEY_BIND_DOWN_LEFT,
								 KEY_BIND_PASS]:
						if event.key in self.key_binds[bind]:
							self.repeat_keys[event.key] = time.time() + REPEAT_DELAY

				if event.type == pygame.VIDEORESIZE:
					self.resize_window(event)

			if profile:
				import cProfile
				import pstats
				pr = cProfile.Profile()

				start = time.time()

				pr.enable()

			self.ui_rects = []

			self.mouse_dx, self.mouse_dy = pygame.mouse.get_rel()

			# Reset examine target if mouse was moved and not in any ui rects
			if self.mouse_dy or self.mouse_dx:
				mx, my = self.get_mouse_pos()
				if self.state == STATE_TITLE:
					pass
				elif self.state == STATE_LEVEL and mx > self.h_margin:
					pass
				elif self.state == STATE_REBIND:
					pass
				else:
					self.examine_target = None

			self.frameno += 1

			if self.gameover_frames < 8:
				self.screen.fill((0, 0, 0))
			elif self.game:
				self.draw_gameover()

			if self.state == STATE_TITLE:
				self.draw_title()
			elif self.state == STATE_PICK_MODE:
				self.draw_pick_mode()
			elif self.state == STATE_PICK_TRIAL:
				self.draw_pick_trial()
			elif self.state == STATE_OPTIONS:
				self.draw_options_menu()
			elif self.state == STATE_REBIND:
				self.draw_key_rebind()
			elif self.state == STATE_MESSAGE:
				self.draw_message()
			elif self.state == STATE_REMINISCE:
				self.draw_reminisce()
			else:
				if self.state == STATE_LEVEL:
					self.draw_level()
				if self.state == STATE_CHAR_SHEET:
					self.draw_char_sheet()
				if self.state == STATE_SHOP:
					self.draw_shop()
				if self.state == STATE_CONFIRM:
					self.draw_confirm()
				if self.state == STATE_COMBAT_LOG:
					self.draw_combat_log()

				if self.game:
					self.draw_character()
				if self.game or self.state == STATE_SHOP:
					self.draw_examine()

			if self.game and profile and frame_time > (1.0 / 60.0):
				pygame.draw.rect(self.screen, (255, 0, 0), (0, 0, 5, 5))
			self.draw_screen()

			if self.state in [STATE_LEVEL, STATE_CHAR_SHEET, STATE_SHOP]:
				self.process_examine_panel_input()

			advanced = False
			if self.game and self.state == STATE_LEVEL:
				level = self.get_display_level()
				# If any creatuers are doing a cast anim, do not process effects or spells or later moves
				#if any(u.Anim.anim == ANIM_ATTACK for u in level.units):
				#   continue

				if self.game.gameover or self.game.victory:
					self.gameover_frames += 1

				if self.gameover_frames == 4:
					# Redo the level end screenshot so that it has the red mordred (or wizard) flash frame
					self.make_level_end_screenshot()
					self.make_game_end_screenshot()

					# Force level finish on victory- the level might not be finished but we are done
					if self.game.victory:
						self.play_music('victory_theme')

				if self.game and self.game.deploying and not self.deploy_target:
					self.deploy_target = Point(self.game.p1.x, self.game.p1.y)
					self.tab_targets = [t for t in self.game.next_level.iter_tiles() if isinstance(t.prop, Portal)]

				self.process_level_input()

				if self.game and self.game.victory_evt:
					self.game.victory_evt = False
					self.on_level_finish()

				if self.game and not self.game.is_awaiting_input() and not self.gameover_frames:
					self.threat_zone = None
					advanced = True

					top_spell = self.game.cur_level.active_spells[0] if self.game.cur_level.active_spells else None
					self.game.advance()

					# Continually advance everything in super turbo, attemptng to do full turn in 1 go
					if self.fast_forward or self.options['spell_speed'] == 3:
						while not self.game.is_awaiting_input() and not self.game.gameover and not self.game.victory:
							self.game.advance()
					# Do another spell advance on speed 1
					elif self.options['spell_speed'] == 1:
						if self.game.cur_level.active_spells and top_spell and top_spell == self.game.cur_level.active_spells[0]:
							self.game.advance()
					# Continually spell advance on speed 2 until the top spell is finished
					elif self.options['spell_speed'] == 2:
						while self.game.cur_level.active_spells and top_spell == self.game.cur_level.active_spells[0]:
							self.game.advance()


					# Check triggers
					if level.cur_shop:
						self.open_shop(SHOP_TYPE_SHOP)

			elif self.state == STATE_CHAR_SHEET:
				self.process_char_sheet_input()
			elif self.state == STATE_TITLE:
				self.process_title_input()
			elif self.state == STATE_PICK_MODE:
				self.process_pick_mode_input()
			elif self.state == STATE_PICK_TRIAL:
				self.process_pick_trial_input()
			elif self.state == STATE_OPTIONS:
				self.process_options_input()
			elif self.state == STATE_REBIND:
				self.process_key_rebind()
			elif self.state == STATE_SHOP:
				self.process_shop_input()
			elif self.state == STATE_REMINISCE:
				self.process_reminisce_input()
			elif self.state == STATE_MESSAGE:
				self.process_message_input()
			elif self.state == STATE_CONFIRM:
				self.process_confirm_input()
			elif self.state == STATE_COMBAT_LOG:
				self.process_combat_log_input()

			# If not examining anything- examine cur spell if possible
			if not self.examine_target and self.cur_spell and self.cur_spell.show_tt:
				self.examine_target = self.cur_spell

			if self.game and profile:
				pr.disable()

				finish = time.time()
				frame_time = finish - start

				if frame_time > 1 / 10.0:
					print("draw time ms: %f" % (frame_time * 1000))
					stats = pstats.Stats(pr)
					stats.sort_stats("cumtime")
					stats.dump_stats("draw_profile.stats")
					stats.print_stats()
loaded_mods = []
def load_mods():
	if not os.path.exists('mods'):
		return

	from importlib import import_module

	for f in os.listdir('mods'):
		if not os.path.isdir(os.path.join('mods', f)):
			continue
		# Skip mods who dont have a properly named main python file
		if not os.path.exists(os.path.join('mods', f, f + '.py')):
			continue
		p = '.'.join(['mods', f, f])
		import_module(p)
		loaded_mods.append(f)

load_mods()

# Manually call this after loading mods as mods may impact the bestiary
make_bestiary()


import traceback
try:
	set_visual_mode(True)
	main_view = PyGameView()
	main_view.run()
except:
	traceback.print_exc(file=sys.stdout)
	print('')
	if loaded_mods:
		print("Loaded mods:")
		for mod in loaded_mods:
			print(mod)

	with open('crash.txt', 'w') as file:
		traceback.print_exc(file=file)
		if loaded_mods:
			file.write("Loaded mods:\n")
			for mod in loaded_mods:
				file.write(mod + '\n')
