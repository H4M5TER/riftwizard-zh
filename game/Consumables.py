from Level import *
from Spells import *
from Monsters import *
from CommonContent import *

class HealPotSpell(Spell):
	def on_init(self):
		self.range = 0

	def cast_instant(self, x, y):
		self.caster.remove_buffs(Poison)
		self.caster.deal_damage(-self.caster.max_hp, Tags.Heal, self)

	def can_cast(self, x, y):
		if self.caster.has_buff(Poison):
			return False
		return Spell.can_cast(self, x, y)

class TeleporterSpell(Teleport):

	def on_init(self):
		self.range = RANGE_GLOBAL
		self.requires_los = False

	def get_description(self):
		return "Teleport to target tile"

	def can_cast(self, x, y):
		return self.caster.level.can_walk(x, y, check_unit=True) and Spell.can_cast(self, x, y)

	def cast_instant(self, x, y):
		self.caster.level.act_move(self.caster, x, y, teleport=True)

def heal_potion():
	item = Item()
	item.name = "Healing Potion"
	item.description = "Drinking this potion restores the drinker to full health.\nCannot be used while poisoned."
	item.set_spell(HealPotSpell())
	return item

def teleporter():
	item = Item()
	item.name = "Teleporter"
	item.description = "Teleport anywhere on the map."
	item.set_spell(TeleporterSpell())
	return item

class ChaosBellSpell(Spell):


	def on_init(self):
		self.range = 0

	def cast_instant(self, x, y):
		for unit in self.caster.level.units:
			if unit.is_player_controlled:
				continue

			if not self.caster.level.are_hostile(self.caster, unit):
				continue

			if random.random() < .5:
				unit.apply_buff(BerserkBuff(), 10)

def chaos_bell():
	item = Item()
	item.name = "Chaos Bell"
	item.description = "Each enemy unit has a 50% chance to go berserk and attack its friends for 10 turns"
	item.set_spell(ChaosBellSpell())
	return item

class TimeStopSpell(Spell):


	def on_init(self):
		self.range = 0

	def cast_instant(self, x, y):
		for unit in self.caster.level.units:
			if self.caster.level.are_hostile(self.caster, unit):
				unit.apply_buff(Stun(), 10)

def golden_stopwatch():
	item = Item()
	item.name = "Golden Stopwatch"
	item.description = "Stun each enemy unit for 10 turns"
	item.set_spell(TimeStopSpell())
	return item

class DeathDiceSpell(Spell):

	def on_init(self):
		self.range = 0

	def cast_instant(self, x, y):
		targets = [u for u in self.caster.level.units if self.caster.level.are_hostile(self.caster, u)]
		random.shuffle(targets)

		for t in targets[:6]:
			t.deal_damage(666, Tags.Dark, self)

def death_dice():
	item = Item()
	item.name = "Death Dice"
	item.description = "Roll the dice to deal 666 Dark damage to 6 random enemies"
	item.set_spell(DeathDiceSpell())
	return item

class PotionSpell(Spell):

	def __init__(self, buff, duration):
		Spell.__init__(self)
		self.buff = buff
		self.duration = duration

	def on_init(self):
		self.range = 0

	def cast_instant(self, x, y):
		self.caster.apply_buff(self.buff(), self.duration)

class EnergyShield(Buff):

	def on_init(self):
		self.name = "Energy Shield"
		self.color = Tags.Arcane.color
		self.resists[Tags.Arcane] = 100
		self.resists[Tags.Dark] = 100
		self.resists[Tags.Holy] = 100
		self.resists[Tags.Lightning] = 100

def energy_shield():
	item = Item()
	item.name = "Energy Shield"
	item.description = "Gain immunity to [arcane], [dark], [lightning], and [holy] damage for 30 turns"
	item.set_spell(PotionSpell(EnergyShield, 30))
	return item

class StoneShield(Buff):

	def on_init(self):
		self.name = "Stone Shield"
		self.color = Tags.Physical.color
		self.resists[Tags.Physical] = 100
		self.resists[Tags.Fire] = 100
		self.resists[Tags.Ice] = 100
		
def stone_shield():
	item = Item()
	item.name = "Stone Shield"
	item.description = "Gain immunity to [physical], [fire], and [ice] damage for 30 turns"
	item.set_spell(PotionSpell(StoneShield, 30))
	return item



class SpellCouponSpell(Spell):

	def on_init(self):
		self.range = 0

	def cast_instant(self, x, y):
		for spell in self.caster.spells:
			spell.cur_charges = spell.get_stat('max_charges')

def mana_potion():
	item = Item()
	item.name = "Mana Potion"
	duration = 3
	item.description = "Refresh charges for all of your spells"
	item.set_spell(SpellCouponSpell())
	return item

class EarthquakeOrb(Spell):

	def on_init(self):
		self.description = "Deals 25 physical damage and destroys walls on 50% of all level tiles."
		self.range = 0

	def cast_instant(self, x, y):
		for i in range(len(self.caster.level.tiles)):
			for j in range(len(self.caster.level.tiles[i])):
				if i == self.caster.x and j == self.caster.y:
					continue
				if random.random() < .5:
					self.caster.level.make_floor(i, j)
					self.caster.level.deal_damage(i, j, 25, Tags.Physical, self)

def quake_orb():
	item = Item()
	item.name =  "Earthquake Orb"
	item.description = "Deals 25 physical damage and destroys walls on 50% of all level tiles."
	item.set_spell(EarthquakeOrb())
	return item 

class DragonHornSpell(Spell):

	def on_init(self):
		self.range = 0

	def cast(self, x, y):
		points = list(self.caster.level.get_adjacent_points(Point(self.caster.x, self.caster.y), check_unit=True, filter_walkable=False))

		random.shuffle(points)
		spawner = random.choice([FireDrake, FireDrake, FireDrake, StormDrake, StormDrake, StormDrake, IceDrake, GoldDrake, VoidDrake])
		for p in points:

			if not self.caster.level.tiles[p.x][p.y].can_fly:
				continue

			if self.caster.level.tiles[p.x][p.y].unit:
				continue

			dragon = spawner()
			
			dragon.team = self.caster.team
			self.caster.level.add_obj(dragon, p.x, p.y)
			yield

def dragon_horn():
	item = Item()
	item.name = "Dragon Horn"
	item.description = "Summon friendly dragons in each unoccupied adjacent square"
	item.set_spell(DragonHornSpell())
	return item

class DisruptPortalsSpell(Spell):


	def on_init(self):
		self.range = 0

	def cast_instant(self, x, y):
		gates = [tile.prop for tile in self.caster.level.iter_tiles() if isinstance(tile.prop, Portal)]
		for gate in gates:
			gate.level_gen_params = self.caster.level.gen_params.make_child_generator()
			gate.description = gate.level_gen_params.get_description()
			gate.next_level = None
			self.caster.level.flash(gate.x, gate.y, Tags.Arcane.color)

def portal_disruptor():
	item = Item()
	item.name = "Portal Disruptor"
	item.description = "Change the destination of all portals in the current level"
	item.set_spell(DisruptPortalsSpell())
	return item


class DisruptShrinesSpell(Spell):

	def on_init(self):
		self.range = 0

	def cast_instant(self, x, y):
		shrines = [tile.prop for tile in self.caster.level.iter_tiles() if isinstance(tile.prop, Shop)]

		for shrine in shrines:
			if not hasattr(shrine, 'reroll'):
				continue
			self.caster.level.remove_prop(shrine)
			new_shrine = shrine.reroll(self.caster.spells)
			new_shrine.reroll = shrine.reroll
			self.caster.level.add_prop(new_shrine, shrine.x, shrine.y)

def shrine_disruptor():
	item = Item()
	item.name = "Shrine Disruptor"
	item.description = "Remake all of the shrines in the current level."
	item.set_spell(DisruptShrinesSpell())
	return item

class PortalKeySpell(Spell):

	def on_init(self):
		self.range = 0

	def cast_instant(self, x, y):

		candidates = [t for t in self.caster.level.iter_tiles() if t.unit != self.caster and t.can_walk and not t.prop]
		if not candidates:
			return

		tile = random.choice(candidates)

		portal = Portal(self.caster.level.gen_params.make_child_generator())
		portal.unlock()
		self.caster.level.add_prop(portal, tile.x, tile.y)

def portal_key():
	item = Item()
	item.name = "Portal Key"
	item.description = "Create a new unlocked rift at a random location in the current level"
	item.set_spell(PortalKeySpell())
	return item

def corruption_orb():
	item = Item()
	item.name = "Orb of Corruption"
	item.description = "An evil and dangerous artifact capable of corrupting creation.  A wise Wizard would surely only use it in the most dire of circumstances."
	spell = MordredCorruption()
	item.set_spell(spell)
	spell.num_exits = 3
	return item

class YouthElixerBuff(Buff):

	def on_init(self):
		self.owner_triggers[EventOnSpellCast] = self.on_spell_cast
		self.description = "Spell charges are refunded"
		self.name = "Youth"

	def on_spell_cast(self, evt
		):
		evt.spell.cur_charges += 1
		evt.spell.cur_charges = min(evt.spell.cur_charges, evt.spell.get_stat('max_charges'))

def youth_elixer():
	item = Item()
	item.name = "Elixir of Youth"
	item.description = "For 7 turns, all spell charges spent are instantly refunded"
	item.set_spell(PotionSpell(YouthElixerBuff, 7))
	return item

class AetherDaggerSpell(Spell):

	def on_init(self):
		self.range = 0

	def get_impacted_tiles(self, x, y):
		for u in self.owner.level.get_units_in_los(self.caster):
			if are_hostile(u, self.caster):
				shown = False
				for t in u.resists:
					if u.resists[t] > 0:
						yield u

	def cast_instant(self, x, y):
		for u in self.owner.level.get_units_in_los(self.caster):
			if are_hostile(u, self.caster):
				shown = False
				for t in u.resists:
					if u.resists[t] > 0:
						u.resists[t] = 0
						if not shown:
							self.owner.level.show_effect(u.x, u.y, Tags.Arcane)
							shown = True

def aether_knife():
	item = Item()
	item.name = "Aether Dagger"
	item.description = "Enemy units in line of sight of the user lose all resistances and immunities"
	item.set_spell(AetherDaggerSpell())
	return item

class OculusBuff(Buff):

	def on_init(self):
		self.global_bonuses['requires_los'] = -1
		self.global_bonuses['range'] = 15
		#self.description = "May cast spells without line of sight"
		self.name = "Oculus"

def oculus():
	item = Item()
	item.name = "Oculus"
	item.description = "For 10 turns, your spells gain 15 range and do not require line of sight"
	item.set_spell(PotionSpell(OculusBuff, 10))
	return item

class MemoryEnhancement(Buff):

	def on_init(self):
		self.name = "Memory Enhancement"
		self.description = "The effect of memory orbs is doubled"
		self.owner_triggers[EventOnItemPickup] = self.on_pickup

	def on_pickup(self, evt):
		if isinstance(evt.item, ManaDot):
			self.owner.xp += 1

def memory_draught():
	item = Item()
	item.name = "Draught of Memories"
	item.description = "For 10 turns, gain double the effect of each memory orb you pick up"
	item.set_spell(PotionSpell(MemoryEnhancement, 10))
	return item

def bag_of_spikes():
	item = Item()
	item.name = "Bag of Spikes"
	item.description = "Summon 8 friendly rolling spikeballs"
	summon_spell = SimpleSummon(SpikeBall, 8)
	summon_spell.range = 0
	item.set_spell(summon_spell)
	return item

def bag_of_bags():
	item = Item()
	item.name = "Bag of Bags"
	item.description = "Summon 8 friendly bags of bugs"
	summon_spell = SimpleSummon(BagOfBugs, 8)
	summon_spell.range = 0
	item.set_spell(summon_spell)
	return item

def troll_crown():
	item = Item()
	item.name = "Troll Crown"
	item.description = "Creates 4 friendly troll gates"
	summon_spell = SimpleSummon(lambda: MonsterSpawner(Troll), 4)
	summon_spell.range = 0
	item.set_spell(summon_spell)
	return item

def storm_troll_crown():
	item = Item()
	item.name = "Storm Troll Crown"
	item.description = "Creates 4 friendly storm troll gates"
	summon_spell = SimpleSummon(lambda: MonsterSpawner(StormTroll), 4)
	summon_spell.range = 0
	item.set_spell(summon_spell)
	return item

def earth_troll_crown():
	item = Item()
	item.name = "Earth Troll Crown"
	item.description = "Creates 4 friendly earth troll gates"
	summon_spell = SimpleSummon(lambda: MonsterSpawner(EarthTroll), 4)
	summon_spell.range = 0
	item.set_spell(summon_spell)
	return item

COMMON = 12
UNCOMMON = 6
RARE = 3
SUPER_RARE = 1

all_consumables = [
	(teleporter, COMMON),
	(portal_disruptor, COMMON),
	(golden_stopwatch, UNCOMMON),
	(portal_key, UNCOMMON),
	(energy_shield, UNCOMMON),
	(stone_shield, UNCOMMON),
	(chaos_bell, UNCOMMON),
	(death_dice, UNCOMMON),
	(quake_orb, RARE),
	(dragon_horn, RARE),
	(youth_elixer, RARE),
	(oculus, RARE),
	(troll_crown, RARE),
	(aether_knife, RARE),
	(memory_draught, SUPER_RARE),
	(corruption_orb, SUPER_RARE),
	(bag_of_spikes, SUPER_RARE),
	(bag_of_bags, SUPER_RARE),
	(storm_troll_crown, SUPER_RARE),
	(earth_troll_crown, SUPER_RARE)
]

for item, freq in all_consumables:
	assert(item() is not None)
	assert(item().spell is not None)

def roll_consumable(prng=None):

	if not prng:
		prng = random

	max_roll = sum(freq for cons, freq in all_consumables)
	roll = prng.randint(0, max_roll)

	index = 0
	while roll > all_consumables[index][1]:
		roll -= all_consumables[index][1]
		index += 1

	# somewhat weird to do this here but oh well for now
	item = all_consumables[index][0]()
	item.sprite.color = COLOR_CONSUMABLE
	return item