from Spells import *
from Monsters import *
from BossSpawns import *
import text


class GlobalBonus(Upgrade):
	def __init__(self, attribute, amount, level, tags, name=None):
		Upgrade.__init__(self)
		self.tags = tags
		self.global_bonuses[attribute] = amount
		self.name = name if name else "Increased %s" % format_attr(attribute)
		self.description = "Increase all spell %s by %d" % (format_attr(attribute), amount)
		self.level = level
		self.attribute = attribute
		self.amount = amount


class TagBonus(Upgrade):
	def __init__(self, tag, attribute, amount, level, name=None):
		Upgrade.__init__(self)
		self.tag_bonuses[tag][attribute] = amount
		self.name = name if name else "%s %s" % (tag.name, format_attr(attribute))
		self.description = "Increase %s spell %s by %d" % (tag.name, format_attr(attribute), amount)
		self.level = level
		self.tags = [tag]
		self.attribute = attribute
		self.amount = amount


class UnblinkingEye(Upgrade):

	def on_init(self):
		self.name = "Unblinking Eye"
		self.tags = [Tags.Eye]

		self.tag_bonuses[Tags.Eye]['shot_cooldown'] = -1
		self.tag_bonuses[Tags.Eye]['duration'] = 10
		self.tag_bonuses[Tags.Eye]['minion_duration'] = 10
		self.tag_bonuses[Tags.Eye]['max_charges'] = 1

		self.level = 7

class StoneCollector(Upgrade):

	def on_init(self):
		self.name = "Rock Collection"
		self.tags = [Tags.Sorcery]

		self.tag_bonuses[Tags.Sorcery]['num_stones'] = 3
		self.level = 3

class DragonLord(Upgrade):

	def on_init(self):
		self.name = "Dragon Lord"
		self.tags = [Tags.Dragon]

		self.tag_bonuses[Tags.Dragon]['max_charges'] = 3
		self.tag_bonuses[Tags.Dragon]['minion_health'] = 25
		self.tag_bonuses[Tags.Dragon]['breath_damage'] = 10

		self.level = 7

class Translocator(Upgrade):

	def on_init(self):
		self.name = "Translocation Master"
		self.tags = [Tags.Translocation]

		self.tag_bonuses[Tags.Translocation]['max_charges'] = 5
		self.tag_bonuses_pct[Tags.Translocation]['range'] = 25

		self.level = 7

class ArchEnchanter(Upgrade):

	def on_init(self):
		self.name = "Arch Enchanter"
		self.tags = [Tags.Enchantment]

		self.tag_bonuses[Tags.Enchantment]['max_charges'] = 2
		self.tag_bonuses[Tags.Enchantment]['duration'] = 3
		self.tag_bonuses_pct[Tags.Enchantment]['damage'] = 40

		self.level = 7

class ArchSorcerer(Upgrade):

	def on_init(self):
		self.name = "Arch Sorcerer"
		self.tags = [Tags.Sorcery]

		self.tag_bonuses[Tags.Sorcery]['damage'] = 7
		self.tag_bonuses[Tags.Sorcery]['range'] = 2
		self.tag_bonuses_pct[Tags.Sorcery]['max_charges'] = 25

		self.level = 7

class ArchConjurer(Upgrade):

	def on_init(self):
		self.name = "Arch Conjurer"
		self.tags = [Tags.Conjuration]

		self.tag_bonuses[Tags.Conjuration]['max_charges'] = 2
		self.tag_bonuses[Tags.Conjuration]['minion_damage'] = 3
		self.tag_bonuses[Tags.Conjuration]['minion_range'] = 1
		
		self.tag_bonuses_pct[Tags.Conjuration]['minion_health'] = 50
		self.tag_bonuses_pct[Tags.Conjuration]['minion_duration'] = 50

		self.level = 7
		
class FireLord(Upgrade):

	def on_init(self):
		self.name = "Fire Lord"
		self.tags = [Tags.Fire]

		self.tag_bonuses[Tags.Fire]['max_charges'] = 1
		self.tag_bonuses[Tags.Fire]['radius'] = 1
		self.tag_bonuses[Tags.Fire]['damage'] = 3
		self.tag_bonuses_pct[Tags.Fire]['damage'] = 60

		self.level = 7

class IceLord(Upgrade):

	def on_init(self):
		self.name = "Ice Lord"
		self.tags = [Tags.Ice]

		self.tag_bonuses[Tags.Ice]['max_charges'] = 1
		self.tag_bonuses[Tags.Ice]['damage'] = 6
		self.tag_bonuses[Tags.Ice]['duration'] = 2

		self.level = 7

class ThunderLord(Upgrade):

	def on_init(self):
		self.name = "Thunder Lord"
		self.tags = [Tags.Lightning]
		
		self.tag_bonuses[Tags.Lightning]['max_charges'] = 1
		self.tag_bonuses_pct[Tags.Lightning]['damage'] = 50

		self.tag_bonuses[Tags.Lightning]['cascade_range'] = 2
		self.tag_bonuses[Tags.Lightning]['num_targets'] = 1

		self.resists[Tags.Lightning] = 50

		self.level = 7

class NatureLord(Upgrade):

	def on_init(self):
		self.name = "Nature Lord"
		self.tags = [Tags.Nature]
		
		self.tag_bonuses[Tags.Nature]['max_charges'] = 3
		self.tag_bonuses[Tags.Nature]['duration'] = 2
		self.tag_bonuses[Tags.Nature]['minion_damage'] = 7
		self.tag_bonuses[Tags.Nature]['minion_health'] = 10

		self.level = 7

class DarkLord(Upgrade):

	def on_init(self):
		self.name = "Dark Lord"
		self.tags = [Tags.Dark]

		self.tag_bonuses[Tags.Dark]['max_charges'] = 3
		self.tag_bonuses[Tags.Dark]['minion_damage'] = 6
		self.tag_bonuses_pct[Tags.Dark]['damage'] = 40
		
		self.level = 7

class VoidLord(Upgrade):

	def on_init(self):
		self.name = "Void Lord"
		self.tags = [Tags.Arcane]

		self.tag_bonuses[Tags.Arcane]['max_charges'] = 2
		self.tag_bonuses[Tags.Arcane]['damage'] = 8
		self.tag_bonuses[Tags.Arcane]['range'] = 2

		self.level = 7

class HeavenLord(Upgrade):

	def on_init(self):
		self.name = "Light Lord"
		self.tags = [Tags.Holy]

		self.tag_bonuses[Tags.Holy]['max_charges'] = 2
		self.tag_bonuses[Tags.Holy]['damage'] = 12
		self.tag_bonuses[Tags.Holy]['minion_health'] = 15
		self.tag_bonuses_pct[Tags.Holy]['minion_duration'] = 75

		self.level = 7


class OrbLord(Upgrade):

	def on_init(self):
		self.name = "Orb Lord"
		self.tags = [Tags.Orb]
		self.tag_bonuses[Tags.Orb]['max_charges'] = 3
		self.tag_bonuses[Tags.Orb]['range'] = 4
		self.tag_bonuses[Tags.Orb]['minion_health'] = 35

		self.level = 7

class MetalLord(Upgrade):

	def on_init(self):
		self.name = "Metal Lord"
		self.tags = [Tags.Metallic]
		self.tag_bonuses[Tags.Metallic]['max_charges'] = 3
		self.tag_bonuses[Tags.Metallic]['duration'] = 5
		self.tag_bonuses[Tags.Metallic]['range'] = 4

		self.level = 7
		self.resists[Tags.Physical] = 25

class PyrophiliaUpgrade(Upgrade):

	def on_init(self):
		self.name = "Pyrophilia"
		self.tags = [Tags.Fire, Tags.Nature]
		self.global_triggers[EventOnDamaged] = self.on_spell_cast
		self.level = 5

	def on_spell_cast(self, event):
		if event.damage_type != Tags.Fire:
			return

		heal = event.damage // 2
		if heal <= 0:
			return

		if not are_hostile(self.owner, event.unit):
			return

		for unit in self.owner.level.get_units_in_los(event.unit):
			if unit == self.owner:
				continue
			if not are_hostile(self.owner, unit):
				unit.deal_damage(-heal, Tags.Heal, self)

	def get_description(self):
		return "Whenever a summoned minion witnesses an enemy take [fire] damage, that minion heals for half that damage."

class PyrostaticStack(Buff):

	def on_init(self,):
		self.name = "Pyrostatic Charge"
		self.color = Tags.Lightning.color
		self.tags = [Tags.Lightning]
		self.level = 4
		self.stack_type = STACK_INTENSITY


class PyrostaticsBuff(Upgrade):

	def on_init(self):
		self.name = "Pyrostatics"
		self.tags = [Tags.Fire, Tags.Lightning]
		self.level = 5
		self.owner_triggers[EventOnSpellCast] = self.on_spell_cast
		self.global_triggers[EventOnDamaged] = self.on_damaged
		self.duration = 10

	def on_spell_cast(self, event):
		if Tags.Lightning in event.spell.tags:
			for i in range(2):
				self.owner.apply_buff(PyrostaticStack(), self.get_stat('duration'))

	def on_damaged(self, evt):
		if evt.damage_type != Tags.Fire:
			return

		if not are_hostile(self.owner, evt.unit):
			return

		buff = self.owner.get_buff(PyrostaticStack)
		if not buff:
			return

		self.owner.level.queue_spell(self.do_damage(evt, stacks=self.owner.get_buff_stacks(PyrostaticStack)))
		self.owner.remove_buffs(PyrostaticStack)

	def do_damage(self, evt, stacks):

		targets = [u for u in self.owner.level.get_units_in_los(evt.unit) if are_hostile(u, self.owner) and u != evt.unit]
		num_targets = min(len(targets), stacks)

		chosen = random.sample(targets, k=num_targets)
		for t in chosen:
			t.deal_damage(evt.damage, Tags.Lightning, self)
			yield

	def get_description(self):
		return "Whenever you deal damage with a [lightning] spell, gain that many stacks of pyrostatic charge for 10 turns.\n Whenever an enemy takes [fire] damage, consume that many pyrostatic charges and deal that much [lightning] damage to up that many units in line of sight of the damaged enemy."

class SoulHarvest(Upgrade):

	def on_init(self):
		self.global_triggers[EventOnDamaged] = self.on_damaged
		self.name = "Soul Harvest"
		self.tags = [Tags.Dark]
		self.level = 7

	def on_damaged(self, damage_event):

		# No harvesting your summons
		if not self.owner.level.are_hostile(self.owner, damage_event.unit):
			return

		if damage_event.unit.cur_hp <= 0:
			chance = .1
			if damage_event.damage_type == Tags.Dark:
				chance *= 3
			if random.random() < chance:
				for spell in self.owner.spells:
					if Tags.Dark in spell.tags and spell.cur_charges < spell.get_stat('max_charges'):
						spell.cur_charges += 1
				self.owner.level.show_effect(self.owner.x, self.owner.y, Tags.Dark)

	def get_description(self):
		return ("Whenever an enemy unit dies, each of your [dark] spells has a 10% chance of gaining a charge.\n"
				"This chance is tripled if the unit died to [dark] damage.")

class ArcaneCombustion(Upgrade):

	def on_init(self):
		self.tags = [Tags.Arcane]
		self.level = 4
		self.name = "Arcane Combustion"
		self.global_triggers[EventOnDeath] = self.on_death
		self.damage = 12
		self.radius = 1

	def on_death(self, evt):
		if evt.damage_event and evt.damage_event.damage_type == Tags.Arcane:
			self.owner.level.queue_spell(self.explosion(evt.unit))

	def explosion(self, evt):
		for p in self.owner.level.get_points_in_ball(evt.x, evt.y, self.get_stat('radius'), diag=True):
			self.owner.level.deal_damage(p.x, p.y, self.get_stat('damage'), Tags.Arcane, self)
			if self.owner.level.tiles[p.x][p.y].is_wall():
				self.owner.level.make_floor(p.x, p.y)
		yield

	def get_description(self):
		return ("Whenever a unit is killed by arcane damage, that unit explodes for [%d_arcane:arcane] damage in a [3_tile:radius] square, melting walls on effected tiles.") % self.get_stat('damage')

class SearingHeat(Upgrade):

	def on_init(self):
		self.tags = [Tags.Fire]
		self.level = 5
		self.name = "Searing Heat"
		self.owner_triggers[EventOnSpellCast] = self.on_cast

	def on_cast(self, evt):
		if Tags.Fire in evt.spell.tags:
			for u in list(self.owner.level.units):
				if not self.owner.level.are_hostile(u, self.owner):
					continue
				if not self.owner.level.can_see(evt.x, evt.y, u.x, u.y):
					continue

				u.deal_damage(1, Tags.Fire, self)

	def get_description(self):
		return "Whenever you cast a [fire] spell, deal [1_fire:fire] damage to all enemies in line of sight of the target.\nThis damage is fixed and cannot be modified.".format(**self.fmt_dict())

class DevourerOfNations(Upgrade):

	def on_init(self):
		self.tags = [Tags.Dark]
		self.level = 3
		self.name = "Devourer of Nations"
		self.global_triggers[EventOnDeath] = self.on_death
		self.heal = 25

	def get_description(self):
		return "Gain %d health whenever you destroy a lair" % self.heal

	def on_death(self, evt):
		if "lair" in evt.unit.name.lower():
			self.owner.deal_damage(-self.heal, Tags.Heal, self)

class DevourerOfChampions(Upgrade):

	def on_init(self):
		self.tags = [Tags.Dark]
		self.level = 3
		self.name = "Devourer of Champions"
		self.global_triggers[EventOnDeath] = self.on_death

	def get_description(self):
		return "Gain a charge of a random level 4 spell whenever you kill a boss"

	def on_death(self, evt):
		if "boss" in evt.unit.name.lower():
			choices = [s for s in self.owner.spells if s.level == 4 and s.cur_charges < s.get_stat('max_charges')]
			if choices:
				random.choice(choices).cur_charges += 1

class MinionRepair(Upgrade):

	def on_init(self):
		self.tags = [Tags.Nature, Tags.Holy]
		self.level = 4
		self.name = "Minion Regeneration"

	def get_description(self):
		return "Each turn, heal each of your minions for [2_HP:heal]"

	def on_advance(self):
		for unit in self.owner.level.units:
			if unit != self.owner and not self.owner.level.are_hostile(unit, self.owner):
				if unit.cur_hp == unit.max_hp:
					continue
				heal_amount = 2
				unit.deal_damage(-heal_amount, Tags.Heal, self)

class Teleblink(Upgrade):

	def on_init(self):
		self.tags = [Tags.Arcane, Tags.Translocation]
		self.level = 4
		self.name = "Glittering Dance"
		self.owner_triggers[EventOnSpellCast] = self.on_spell_cast
		self.casts = 0

		self.minion_damage = 4
		self.heal = 5

		self.minion_range = 4
		self.minion_duration = 10
		self.minion_health = 9
		self.shields = 1
		self.cast_last = False

		self.num_summons = 2

	def get_extra_examine_tooltips(self):
		return [self.make_faery()]

	def get_description(self):
		return ("When you cast three [arcane] spells in a row, regain a charge of a random [translocation] spell and summon [2_faeries:num_summons].\n"
				"The faeries fly, blink, are shielded, can heal their allies, and have an [arcane] ranged attack.\n"
			    "The faeries vanish after [{minion_duration}_turns:minion_duration].\n").format(**self.fmt_dict())

	def on_advance(self):
		if not self.cast_last:
			self.casts = 0
		self.cast_last = False

	def make_faery(self):
		unit = Unit()
		unit.name = "Faery"
		unit.asset_name = "good_faery"
		unit.max_hp = self.minion_health
		unit.shields = self.get_stat('shields')
		unit.buffs.append(TeleportyBuff(chance=.7))
		unit.spells.append(HealAlly(heal=self.get_stat('heal'), range=self.get_stat('minion_range') + 2))
		unit.spells.append(SimpleRangedAttack(damage=self.get_stat('minion_damage'), range=self.get_stat('minion_range'), damage_type=Tags.Arcane))
		unit.turns_to_death = self.get_stat('minion_duration')
		unit.tags = [Tags.Nature, Tags.Arcane, Tags.Living]
		return unit

	def on_spell_cast(self, evt):
		if Tags.Arcane in evt.spell.tags:
			if self.casts < 2:
				self.casts += 1
				self.cast_last = True
			else:
				self.casts = 0
				self.cast_last = False
				candidates = [s for s in self.owner.spells if Tags.Translocation in s.tags and s.cur_charges < s.get_stat('max_charges')]
				if candidates:
					candidate = random.choice(candidates)
					candidate.cur_charges += 1

				for i in range(self.get_stat('num_summons')):
					unit = self.make_faery()
					self.summon(unit)

class ArcaneCredit(Buff):

	def on_init(self):
		self.name = "Arcane Credit"
		self.owner_triggers[EventOnSpellCast] = self.on_cast
		self.color = Tags.Arcane.color
		self.description = "Charge cost of next non [arcane] spell will be refunded."

	def on_cast(self, evt):
		if Tags.Arcane not in evt.spell.tags:
			evt.spell.cur_charges += 1
			evt.spell.cur_charges = min(evt.spell.cur_charges, evt.spell.get_stat('max_charges'))
			self.owner.remove_buff(self)

class ArcaneAccountant(Upgrade):

	def on_init(self):
		self.tags = [Tags.Arcane]
		self.level = 4
		self.name = "Arcane Accounting"
		self.owner_triggers[EventOnSpellCast] = self.on_spell_cast

	def get_description(self):
		return "Whenever you cast the last charge of an [arcane] spell, your next non arcane spell is free for 1 turn."

	def on_spell_cast(self, evt):
		if Tags.Arcane in evt.spell.tags and evt.spell.cur_charges == 0:
			self.owner.apply_buff(ArcaneCredit(), 2)

class NaturalHealing(Upgrade):

	def on_init(self):
		self.tags = [Tags.Nature]
		self.level = 4
		self.name = "Natural Healing"
		self.owner_triggers[EventOnSpellCast] = self.on_spell_cast
		self.heal = 5

	def get_description(self):
		return "Whenever you cast a [nature] spell, you and all [living] allies heal [{heal}_HP:heal].".format(**self.fmt_dict())

	def on_spell_cast(self, evt):
		if Tags.Nature in evt.spell.tags:
			self.owner.deal_damage(-self.get_stat('heal'), Tags.Heal, self)

		for u in self.owner.level.units:
			if u == self.owner:
				continue

			if are_hostile(self.owner, u):
				continue

			if not Tags.Living in u.tags:
				continue

			u.deal_damage(-self.get_stat('heal'), Tags.Heal, self)

class LightningFrenzyStack(Buff):

	def __init__(self, damage):
		Buff.__init__(self)
		self.name = "Crackling Frenzy"
		self.color = Tags.Lightning.color
		self.stack_type = STACK_INTENSITY
		self.tag_bonuses[Tags.Lightning]['damage'] = damage
		self.asset = ['status', 'crackling_frenzy']

class LightningFrenzy(Upgrade):

	def on_init(self):
		self.tags = [Tags.Lightning]
		self.level = 6
		self.name = "Lightning Frenzy"
		self.owner_triggers[EventOnSpellCast] = self.on_spell_cast
		self.bonus = 4
		self.duration = 6

	def get_description(self):
		return "Whenever you cast a [lightning] spell, your [lightning] spells and skills gain [%d_damage:damage] for [%d_turns:duration]" % (self.bonus, self.get_stat('duration'))

	def on_spell_cast(self, evt):
		if Tags.Lightning in evt.spell.tags:
			self.owner.apply_buff(LightningFrenzyStack(self.bonus), duration=self.get_stat('duration'))

class MeltedArmor(Buff):

	def on_init(self):
		self.resists[Tags.Physical] = -10
		self.name = "Armor Melted"
		self.buff_type = BUFF_TYPE_CURSE
		self.stack_type = STACK_INTENSITY
		self.asset = ['status', 'melted_armor']
		self.color = Tags.Fire.color

class ArmorMelter(Upgrade):

	def on_init(self):
		self.tags = [Tags.Fire, Tags.Metallic]
		self.level = 4
		self.name = "Melting Armor"
		self.global_triggers[EventOnDamaged] = self.on_damage

	def get_description(self):
		return "Whenever an enemy takes [fire] damage, it loses [10_physical:physical] resist."

	def on_damage(self, evt):
		if Tags.Fire == evt.damage_type and self.owner.level.are_hostile(evt.unit, self.owner):
			evt.unit.apply_buff(MeltedArmor())

class NaturalVigor(Upgrade):

	def on_init(self):
		self.tags = [Tags.Nature]
		self.global_triggers[EventOnUnitAdded] = self.on_unit_added
		self.name = "Natural Vigour"
		self.level = 4

	def get_description(self):
		return "Your summoned units gain [25_physical:physical] resist, [25_lightning:lightning] resist, [25_ice:ice] resist and [25_fire:fire] resist."

	def on_unit_added(self, evt):
		if evt.unit.is_player_controlled:
			return
			
		if not self.owner.level.are_hostile(self.owner, evt.unit):
			evt.unit.resists[Tags.Physical] += 25
			evt.unit.resists[Tags.Fire] += 25
			evt.unit.resists[Tags.Ice] += 25
			evt.unit.resists[Tags.Lightning] += 25

class HungerLifeLeechSpell(Spell):

	def on_init(self):
		self.cool_down = 3
		self.name = "Hunger"
		self.range = 3
		self.damage = 7
		self.damage_type = Tags.Dark

	def cast(self, x, y):
		target = Point(x, y)

		for point in Bolt(self.caster.level, self.caster, target):
			# TODO- make a flash using something other than deal_damage
			self.caster.level.show_effect(point.x, point.y, Tags.Dark)
			yield

		damage_dealt = self.caster.level.deal_damage(x, y, self.damage, Tags.Dark, self)
		self.caster.deal_damage(-damage_dealt, Tags.Heal, self)

class Hunger(Upgrade):

	def on_init(self):
		self.name = "Hungry Dead"
		self.tags = [Tags.Dark]
		self.level = 4
		self.minion_range = 3
		self.minion_damage = 7
		self.global_triggers[EventOnUnitAdded] = self.on_unit_add

	def get_description(self):
		return ("Your summoned [undead] units gain Hunger.\n"
			  	"Hunger deals [{minion_damage}_dark:dark] damage to a target up to [{minion_range}_tiles:range] away, "
			  	"healing the caster for all damage dealt, and has a [3_turn:cooldown] cooldown.\n".format(**self.fmt_dict()))

	def should_grant(self, unit):
		return not are_hostile(unit, self.owner) and Tags.Undead in unit.tags

	def grant(self, unit):
		# Dont grant copies, for instance, on ressurection
		if unit.get_spell(HungerLifeLeechSpell):
			return False

		spell = HungerLifeLeechSpell()
		spell.damage = self.get_stat('minion_damage')
		spell.range = self.get_stat('minion_range')
		#weird cause im trying to insert at 0
		spell.caster = unit
		spell.owner = unit
		unit.spells.insert(0, spell)

	def on_unit_add(self, evt):
		if self.should_grant(evt.unit):
			self.grant(evt.unit)

	def on_advance(self):
		for unit in self.owner.level.units:
			hunger = [s for s in unit.spells if isinstance(s, HungerLifeLeechSpell)]
			if hunger and not self.should_grant(unit):
				unit.remove_spell(hunger[0])
			elif not hunger and self.should_grant(unit):
				self.grant(unit)

class LightningWarp(Upgrade):

	def on_init(self):
		self.owner_triggers[EventOnSpellCast] = self.on_spell_cast
		self.damage = 9
		self.name = "Lightning Warp"
		self.level = 4
		self.tags = [Tags.Lightning, Tags.Translocation]
		self.radius = 3

	def get_description(self):
		return "Whenever you cast a [lightning] spell, all non stationary enemy units within [3_tiles:radius] of the target are teleported to random spaces up to [5_tiles:range] away and take [{damage}_lightning:lightning] damage.  Enemies will always be teleported at least 4 tiles away from the wizard.".format(**self.fmt_dict())

	def on_spell_cast(self, evt):

		if Tags.Lightning not in evt.spell.tags:
			return

		self.owner.level.queue_spell(self.do_teleports(evt))

	def do_teleports(self, evt):
		for unit in self.owner.level.get_units_in_ball(evt, self.get_stat('radius')):
			if not self.owner.level.are_hostile(unit, self.owner):
				continue

			# Dont warp gates, its obnoxious
			if unit.stationary:
				continue

			self.owner.level.show_beam(evt, unit, Tags.Lightning, inclusive=True)

			points = self.owner.level.get_points_in_ball(evt.x, evt.y, 5)
			points = [p for p in points if distance(p, self.owner) >= 4 and self.owner.level.can_stand(p.x, p.y, unit)]
			if points:
				point = random.choice(points)
				
				
				for p in self.owner.level.get_points_in_line(unit, point)[1:-1]:
					self.owner.level.show_effect(p.x, p.y, Tags.Translocation, minor=True)

				self.owner.level.act_move(unit, point.x, point.y, teleport=True)
				unit.deal_damage(self.get_stat('damage'), Tags.Lightning, self)
				
				yield

class Starfire(Upgrade):

	def on_init(self):
		self.name = "Starfire"
		self.level = 5
		self.tags = [Tags.Fire, Tags.Arcane]
		self.num_targets = 4
		self.global_triggers[EventOnDamaged] = self.on_damage


	def get_description(self):
		return "Whenever an enemy takes [fire], deal that much [arcane] damage to up to [{num_targets}:num_targets] adjacent enemies.".format(**self.fmt_dict())

	def on_damage(self, evt):
		if evt.damage_type != Tags.Fire:
			return

		if not are_hostile(self.owner, evt.unit):
			return

		self.owner.level.queue_spell(self.deal_damage(evt))

	def deal_damage(self, evt):

		r = 1 + evt.unit.radius
		adjacent_points = [p for p in self.owner.level.get_points_in_rect(evt.unit.x - r, evt.unit.y - r, evt.unit.x + r, evt.unit.y + r)]

		for p in evt.unit.iter_occupied_points():
			adjacent_points.remove(p)

		adjacent_units = [self.owner.level.get_unit_at(*p) for p in adjacent_points if self.owner.level.get_unit_at(*p)]
		candidates = [u for u in adjacent_units if are_hostile(self.owner, u)]

		random.shuffle(candidates)

		for u in candidates[:self.get_stat('num_targets')]:
			u.deal_damage(evt.damage, Tags.Arcane, self)
			yield



class ShockAndAwe(Upgrade):

	def on_init(self):
		self.name = "Shock Value"
		self.global_triggers[EventOnDeath] = self.on_death
		self.tags = [Tags.Lightning]
		self.level = 7
		self.duration = 5

	def get_description(self):
		return ("Whenever an enemy dies to [lightning] damage, another random enemy in line of sight of that enemy goes [berserk] for [5_turns:duration].\n"
				+ text.berserk_desc).format(**self.fmt_dict())

	def on_death(self, evt):
		if evt.damage_event is not None and evt.damage_event.damage_type == Tags.Lightning and self.owner.level.are_hostile(evt.unit, self.owner):
			def eligible(u):
				if u == evt.unit:
					return False
				if not self.owner.level.are_hostile(u, self.owner):
					return False
				if not self.owner.level.can_see(evt.unit.x, evt.unit.y, u.x, u.y):
					return False
				if u.stationary:
					return False
				if u.has_buff(BerserkBuff):
					return False
				return True

			candidates = [u for u in self.owner.level.units if eligible(u)]
			if candidates:
				candidate = random.choice(candidates)
				candidate.apply_buff(BerserkBuff(), self.get_stat('duration'))

class Horror(Upgrade):

	def on_init(self):
		self.name = "Horror"
		self.tags = [Tags.Dark]
		self.level = 5
		self.description = "Whenever an enemy dies to [dark] damage, up to [3:num_targets] random enemies in line of sight of that enemy are [stunned] for [5_turns:duration]"
		self.global_triggers[EventOnDeath] = self.on_death
		self.duration = 5

	def on_death(self, evt):
		if evt.damage_event is not None and evt.damage_event.damage_type == Tags.Dark and self.owner.level.are_hostile(evt.unit, self.owner):
			def eligible(u):
				if u == evt.unit:
					return False
				if not self.owner.level.are_hostile(u, self.owner):
					return False
				if not self.owner.level.can_see(evt.unit.x, evt.unit.y, u.x, u.y):
					return False
				if u.stationary:
					return False
				if u.is_stunned():
					return False
				return True

			candidates = [u for u in self.owner.level.units if eligible(u)]
			random.shuffle(candidates)
			for c in candidates[:3]:
				c.apply_buff(Stun(), self.get_stat('duration'))


class WhiteFlame(Upgrade):

	def on_init(self):
		self.name = "White Flame"
		self.tags = [Tags.Fire]
		self.level = 4
		self.damage = 18
		self.owner_triggers[EventOnSpellCast] = self.on_spell_cast

	def get_description(self):
		return "Whenever you cast a [fire] spell with range greater than zero, deal [%d_fire:fire] damage to the targeted point." % self.get_stat('damage')

	def on_spell_cast(self, evt):
		self.owner.level.queue_spell(self.effect(evt))

	def effect(self, evt):
		if Tags.Fire not in evt.spell.tags:
			return

		# dont white flame yourself with eye of fire or whatever
		if evt.x == self.owner.x and evt.y == self.owner.y:
			return

		self.owner.level.deal_damage(evt.x, evt.y, self.get_stat('damage'), Tags.Fire, self)
		yield

class ChaosBuddies(Upgrade):

	def on_init(self):
		self.name = "Chaos Buddies"
		self.tags = [Tags.Chaos]
		self.level = 4
		
		self.minion_health = 5
		self.minion_damage = 4
		self.minion_duration = 7
		self.minion_range = 3

		self.damage_this_turn = set()
		self.procs_this_turn = set()
		self.global_triggers[EventOnDamaged] = self.on_damaged

	def on_advance(self):
		self.procs_this_turn = set()
		self.damage_this_turn = set()

	def get_description(self):
		return ("Whenever an enemy takes [fire], [lightning], and [physical] damage in the same turn, summon an iron imp, a spark imp, and a fire imp near that enemy.\n"
				"Imps have [{minion_health}_HP:minion_health] and can fly.\n"
				"Imps have a ranged attack dealing [{minion_damage}_damage:minion_damage] with a [{minion_range}_tile:minion_range] range.\n"
				"The imps each last [{minion_duration}_turns:minion_duration].\n").format(**self.fmt_dict())

	def on_damaged(self, evt):
		if not self.owner.level.are_hostile(evt.unit, self.owner):
			return
		if evt.damage_type not in [Tags.Fire, Tags.Lightning, Tags.Physical]:
			return
		if evt.unit in self.procs_this_turn:
			return

		self.damage_this_turn.add((evt.damage_type, evt.unit))
		needed_tuples = set([
			(Tags.Fire, evt.unit),
			(Tags.Lightning, evt.unit),
			(Tags.Physical, evt.unit)
		])
		if needed_tuples.issubset(self.damage_this_turn):
			self.procs_this_turn.add(evt.unit)
			self.owner.level.queue_spell(self.summon_imps(evt.unit.x, evt.unit.y))

	def summon_imps(self, x, y):

		for imp in [FireImp(), SparkImp(), IronImp()]:
			imp.spells[0].damage = self.get_stat('minion_damage')
			imp.spells[0].range = self.get_stat('minion_range')
			imp.max_hp = self.get_stat('minion_health')
			imp.turns_to_death = self.get_stat('minion_duration')
			self.summon(imp, target=Point(x, y), sort_dist=False)
			yield
			

class ArcaneShield(Upgrade):

	def on_init(self):
		self.name = "Arcane Shield"
		self.tags = [Tags.Arcane]
		self.level = 4
		self.description = "Whenever you cast an [arcane] spell, if you have no shields, gain [1_SH:shields]."
		self.owner_triggers[EventOnSpellCast] = self.on_spell_cast
	
	def on_spell_cast(self, evt):
		if Tags.Arcane in evt.spell.tags:
			if self.owner.shields == 0:
				self.owner.shields = 1
				self.owner.level.flash(self.owner.x, self.owner.y, Tags.Arcane.color)

class MinionShield(Upgrade):

	def on_init(self):
		self.name = "Shielded Minions"
		self.tags = [Tags.Arcane]
		self.level = 4
		self.description = "Arcane minions you summon gain [3_SH:shields].  Other minions you summon gain [1_SH:shields]."
		self.global_triggers[EventOnUnitAdded] = self.on_unit_add

	def on_unit_add(self, evt):
		if self.owner.level.are_hostile(evt.unit, self.owner):
			return

		if evt.unit.is_player_controlled:
			return

		if Tags.Arcane in evt.unit.tags:
			shields = 3
		else:
			shields = 1
		evt.unit.add_shields(shields)

class GhostfireUpgrade(Upgrade):

	def on_init(self):
		self.color = Tags.Dark.color

		self.name = "Ghostfire"
		self.global_triggers[EventOnDamaged] = self.on_damaged

		self.tags = [Tags.Fire, Tags.Dark]
		self.level = 5

		self.fire_victims = set()
		self.dark_victims = set()
		self.blackfire_victims = set()

		self.minion_health = 4
		self.minion_damage = 7
		self.minion_range = 5
		self.minion_duration = 10

	def get_extra_examine_tooltips(self):
		return [self.make_ghost()]

	def on_advance(self):
		self.fire_victims.clear()
		self.dark_victims.clear()
		self.blackfire_victims.clear()

	def on_damaged(self, evt):
		if evt.damage_type not in [Tags.Fire, Tags.Dark]:
			return

		if evt.unit in self.blackfire_victims:
			return

		if not are_hostile(self.owner, evt.unit):
			return

		if evt.damage_type == Tags.Fire:
			self.fire_victims.add(evt.unit)
			if evt.unit in self.dark_victims:
				self.blackfire_victims.add(evt.unit)
				self.owner.level.queue_spell(self.do_summon(evt.unit.x, evt.unit.y))
			
		if evt.damage_type == Tags.Dark:
			self.dark_victims.add(evt.unit)
			if evt.unit in self.fire_victims:
				self.blackfire_victims.add(evt.unit)
				self.owner.level.queue_spell(self.do_summon(evt.unit.x, evt.unit.y))

	def make_ghost(self):
		ghost = Ghost()
		ghost.max_hp = self.get_stat('minion_health')
		ghost.sprite.color = Tags.Fire.color
		ghost.spells[0] = SimpleRangedAttack(damage=self.get_stat('minion_damage'), range=self.get_stat('minion_range'), damage_type=Tags.Fire)
		ghost.name = "Burning Ghost"
		ghost.asset_name = "fire_ghost"
		ghost.resists[Tags.Fire] = 100
		return ghost

	def do_summon(self, x, y):
		ghost = self.make_ghost()
		ghost.turns_to_death = self.get_stat('minion_duration')
		self.summon(ghost, target=Point(x, y))
		yield

	def get_description(self):
		return ("Whenever an enemy takes [dark] damage and [fire] damage in the same turn, summon a burning ghost near that enemy.\n"
				"Burning ghosts fly, have [100_fire:fire] resist and [100_dark:dark] resist, and passively blink.\n"
				"Burning ghosts have a ranged attack which deals [{minion_damage}_fire:fire] damage with a [{minion_range}_tile:minion_range] range.\n"
				"The ghosts vanish after [{minion_duration}_turns:minion_duration].").format(**self.fmt_dict())

class LastWord(Upgrade):

	def on_init(self):
		self.name = "Wordspeaker"
		self.tags = [Tags.Word]
		self.level = 5
		self.tag_bonuses[Tags.Word]['max_charges'] = 2

class PrinceOfRuin(Upgrade):

	def on_init(self):
		self.name = "Prince of Ruin"
		self.global_triggers[EventOnDeath] = self.on_death
		self.fire_triggered = False
		self.light_triggered = False
		self.phys_triggered = False

		self.level = 4
		self.damage = 13
		self.radius = 5

		self.tags = [Tags.Chaos, Tags.Fire, Tags.Lightning]

	def get_description(self):
		return "Whenever an enemy dies to [fire], [physical], or [lightning] damage, deal [{damage}_damage:damage] of that type to a random enemy in line of sight of the target up to [{radius}_tiles:radius] away.".format(**self.fmt_dict())

	def on_death(self, evt):
		if not are_hostile(evt.unit, self.owner):
			return
		damage_event = evt.damage_event
		if damage_event and damage_event.damage_type in [Tags.Fire, Tags.Lightning, Tags.Physical]:
			self.owner.level.queue_spell(self.trigger(evt))

	def trigger(self, evt):
		candidates = [u for u in self.owner.level.get_units_in_ball(evt.unit, self.radius) if are_hostile(self.owner, u)]
		candidates = [u for u in candidates if self.owner.level.can_see(evt.unit.x, evt.unit.y, u.x, u.y)]

		if candidates:
			target = random.choice(candidates)
			for p in self.owner.level.get_points_in_line(evt.unit, target, find_clear=True)[1:-1]:
				self.owner.level.show_effect(p.x, p.y, evt.damage_event.damage_type)
			target.deal_damage(self.get_stat('damage'), evt.damage_event.damage_type, self)
		yield

class MarchOfTheRighteous(Upgrade):

	def on_init(self):
		self.name = "Righteous March"
		self.description = "Whenever an enemy dies to [holy] damage, allies witnessing it gain [1_SH:shields] if they are not already shielded."
		self.global_triggers[EventOnDeath] = self.on_death
		self.tags = [Tags.Holy]

		self.level = 5

	def on_death(self, evt):
		damage_evt = evt.damage_event
		if not damage_evt:
			return
		if damage_evt.damage_type != Tags.Holy:
			return
		self.owner.level.queue_spell(self.trigger())

	def trigger(self):
		units = [u for u in self.owner.level.get_units_in_los(self.owner) if not are_hostile(self.owner, u)]
		for u in units:
			if u.shields < 1:
				u.add_shields(1)
				yield

class FieryJudgement(Upgrade):

	def on_init(self):
		self.name = "Fiery Judgement"
		self.level = 5
		self.tags = [Tags.Fire, Tags.Holy]
		self.conversions[Tags.Fire][Tags.Holy] = 1

	def get_description(self):
		return "Whenever an enemy takes [fire] damage, redeal that damage as [holy] damage."


class HolyThunder(Upgrade):

	def on_init(self):
		self.name = "Holy Thunder"
		self.level = 5
		self.tags = [Tags.Lightning, Tags.Holy]
		self.conversions[Tags.Lightning][Tags.Holy] = 1

	def get_description(self):
		return "Whenever an enemy takes [lightning] damage, redeal that damage as [holy] damage."

class Chastisement(Upgrade):

	def on_init(self):
		self.name = "Chastisement"
		self.description = "Whenever an enemy takes [holy] damage, it has a 50% chance to be [stunned] for [1_turn:duration]."
		self.tags = [Tags.Holy]
		self.level = 6
		self.global_triggers[EventOnDamaged] = self.on_damage

	def on_damage(self, evt):
		if evt.damage_type != Tags.Holy:
			return

		if not are_hostile(evt.unit, self.owner):
			return

		if random.random() > .5:
			return

		evt.unit.apply_buff(Stun(), 1)

class ChaosCasting(Upgrade):

	def on_init(self):
		self.name = "Chaos Casting"
		self.description = "Whenever you cast a [chaos] spell, you have a 25% chance of regaining a charge of another random [chaos] spell"
		self.level = 5
		self.tags = [Tags.Chaos]
		self.global_triggers[EventOnSpellCast] = self.on_cast

	def on_cast(self, evt):
		if Tags.Chaos not in evt.spell.tags:
			return

		if random.random() > .25:
			return

		candidates = [s for s in self.owner.spells if s != evt.spell and s.cur_charges != s.get_stat('max_charges') and Tags.Chaos in s.tags]
		if candidates:
			candidate = random.choice(candidates)
			candidate.cur_charges += 1

class UnholyAlliance(Upgrade):

	def on_init(self):
		self.name = "Unholy Alliance"
		self.description = ("Whenever you summon an [undead] or [demon], if you control a holy unit, the newly summoned unit gains [7_damage:damage].\n"
							"Whenever you summon a [holy] creature, if you control an [undead] or [demon], the newly summoned unit gains [7_damage:damage].\n")

		self.level = 4
		self.tags = [Tags.Dark, Tags.Holy]
		self.global_triggers[EventOnUnitAdded] = self.on_unit_add

	def on_unit_add(self, evt):

		if are_hostile(evt.unit, self.owner):
			return

		if Tags.Holy in evt.unit.tags:
			if any((Tags.Undead in u.tags or Tags.Demon in u.tags) and not are_hostile(u, evt.unit) for u in self.owner.level.units):
				for s in evt.unit.spells:
					if hasattr(s, 'damage'):
						s.damage += 7
				return

		if Tags.Undead in evt.unit.tags or Tags.Demon in evt.unit.tags:
			if any(Tags.Holy in u.tags and not are_hostile(u, evt.unit) for u in self.owner.level.units):
				for s in evt.unit.spells:
					if hasattr(s, 'damage'):
						s.damage += 7
				return

class FaeThorns(Upgrade):

	def on_init(self):
		self.name = "Thorn Garden"

		self.tags = [Tags.Arcane, Tags.Nature]
		self.level = 5
		
		self.minion_health = 10
		self.minion_damage = 4
		self.minion_duration = 9
		self.num_summons = 3

		self.owner_triggers[EventOnSpellCast] = self.on_spell_cast

	def get_description(self):
		return ("Whenever you cast an [arcane] or [nature] spell, summon [{num_summons}:num_summons] fae thorns near the target.\n"
		    	"Fae Thorns have [{minion_health}_HP:minion_health], and cannot move.\n"
		    	"Fae Thorns have a melee attack which deals [{minion_damage}_physical:physical] damage.\n"
		    	"The thorns vanish after [{minion_duration}_turns:minion_duration].").format(**self.fmt_dict())

	def get_extra_examine_tooltips(self):
		return [FaeThorn()]

	def on_spell_cast(self, evt):
		if Tags.Arcane in evt.spell.tags or Tags.Nature in evt.spell.tags:
			self.owner.level.queue_spell(self.do_summons(evt))

	def do_summons(self, evt):
		for i in range(self.get_stat('num_summons')):
			thorn = FaeThorn()

			thorn.max_hp = self.get_stat('minion_health')
			thorn.spells[0].damage = self.get_stat('minion_damage')

			thorn.turns_to_death = self.get_stat('minion_duration')

			self.summon(thorn, evt, radius=2, sort_dist=False)
		yield

class HypocrisyStack(Buff):

	def __init__(self, tag, level):
		self.tag = tag
		self.level = level
		Buff.__init__(self)

	def on_init(self):
		self.name = "%s Hypocrisy %d" % (self.tag.name, self.level)
		self.description = "If next spell cast is a %s spell of level %d or lower is free" % (self.tag.name, self.level)
		self.color = self.tag.color
		self.owner_triggers[EventOnSpellCast] = self.on_spell_cast
		self.stack_type = STACK_INTENSITY

	def on_spell_cast(self, evt):
		if self.tag in evt.spell.tags and evt.spell.level <= self.level:
			evt.spell.cur_charges += 1
			evt.spell.cur_charges = min(evt.spell.cur_charges, evt.spell.get_stat('max_charges'))
		self.owner.remove_buff(self)


class Hypocrisy(Upgrade):

	def on_init(self):
		self.name = "Hypocrisy"
		self.description = ("Whenever you cast a [dark] spell, if your next spell is a [holy] spell of a lower level, that spell's cost is refunded.\n"
							"Whenever you cast a [holy] spell, if your next spell is a [dark] spell of a lower level, that spell's cost is refunded.")

		self.tags = [Tags.Dark, Tags.Holy]
		self.level = 5

		self.owner_triggers[EventOnSpellCast] = self.on_spell_cast


	def on_spell_cast(self, evt):

		if evt.spell.level <= 1:
			return

		for tag in [Tags.Dark, Tags.Holy]:
			if tag not in evt.spell.tags:
				continue
			btag = Tags.Holy if tag == Tags.Dark else Tags.Dark
			b = HypocrisyStack(btag, evt.spell.level - 1)
			self.owner.apply_buff(b)

class FaestoneBuff(Buff):

	def on_init(self):
		self.name = "Fae Stone Buff"
		self.description = "Whenever its master casts a nature spell, gains 10 HP.\n\nWhenever its master casts an arcane spell, teleports near the target and gains 1 shield."
		self.global_triggers[EventOnSpellCast] = self.on_cast
		self.master = None
		self.damage = 7
		self.healing = 10

	def on_cast(self, evt):
		if evt.caster != self.master:
			return

		if Tags.Arcane in evt.spell.tags:

			self.owner.level.queue_spell(self.teleport(Point(evt.x, evt.y)))

		if Tags.Nature in evt.spell.tags:
			if self.owner.cur_hp < self.owner.max_hp:
				self.owner.deal_damage(-self.healing, Tags.Heal, self)

	def teleport(self, target):
		start = Point(self.owner.x, self.owner.y)
		dest = self.owner.level.get_summon_point(target.x, target.y, radius_limit=4)
		if dest:
			self.owner.level.act_move(self.owner, dest.x, dest.y, teleport=True)
			self.owner.add_shields(1)
		yield

class Faestone(Upgrade):

	def on_init(self):
		self.name = "Faestone"
		self.level = 4
		self.tags = [Tags.Arcane, Tags.Nature, Tags.Conjuration]

		self.minion_damage = 20
		self.minion_health = 350

		self.description = (" each level with a friendly Fae Stone.  The Fae Stone is a sturdy immobile melee unit."
						    "\n\nWhenever you cast an arcane spell, the Fae Stone teleports near the target and gains 1 shield."
						    "\n\nWhenever you cast a nature spell, the Fae Stone heals 10 HP.")
		self.global_triggers[EventOnUnitAdded] = self.on_unit_added

	def get_description(self):
		return ("Whenever you enter a new level, summon a Fae Stone nearby.\n"
				"The Fae Stone is stationary and hard to kill, and has a [physical] melee attack.\n"
				"Whenever you cast a [nature] spell, the Fae Stone heals for [10_HP:heal].\n"
				"Whenever you cast an [arcane] spell, the Fae Stone teleports near the target and gains [1_SH:shields].").format(**self.fmt_dict())

	def make_rock(self):
		faestone = Unit()
		faestone.name = "Fae Stone"

		faestone.max_hp = self.minion_health
		faestone.shields = 1

		faestone.spells.append(SimpleMeleeAttack(self.minion_damage))
		buff = FaestoneBuff()
		buff.master = self.owner
		faestone.buffs.append(buff)

		faestone.stationary = True

		faestone.resists[Tags.Physical] = 50
		faestone.resists[Tags.Fire] = 50
		faestone.resists[Tags.Lightning] = 50
		faestone.tags = [Tags.Nature, Tags.Arcane]

		apply_minion_bonuses(self, faestone)
		return faestone

	def get_extra_examine_tooltips(self):
		return [self.make_rock()]

	def on_unit_added(self, evt):
		if evt.unit != self.owner:
			return

		faestone = self.make_rock()

		self.summon(faestone, sort_dist=False)

class Houndlord(Upgrade):

	def on_init(self):
		self.name = "Houndlord"
		self.level = 4
		self.tags = [Tags.Fire, Tags.Conjuration]
		self.minion_damage = 6
		self.minion_health = 19
		self.minion_range = 4
		self.num_summons = 4

		self.owner_triggers[EventOnSpellCast] = self.on_spell_cast

		self.hh_name = HellHound().name

	def get_extra_examine_tooltips(self):
		return [HellHound()]

	def get_description(self):
		return ("Whenever you cast a [fire] spell, if you have less than [{num_summons}:num_summons] hellhounds, summon a hellhound.\n"
				"Hell hounds have a leap attack, fiery bodies which deal damage to melee attackers, and [fire] melee attacks.\n").format(**self.fmt_dict())

	def on_spell_cast(self, evt):
		if Tags.Fire not in evt.spell.tags:
			return

		num_hell_hounds = len([u for u in self.owner.level.units if not are_hostile(self.owner, u) and u.name == self.hh_name])

		if num_hell_hounds >= self.get_stat('num_summons'):
			return

		unit = HellHound()
		apply_minion_bonuses(self, unit)
		self.summon(unit)

class Boneguard(Upgrade):

	def on_init(self):
		self.name = "Bone Guard"
		self.level = 4
		self.tags = [Tags.Dark, Tags.Conjuration]

		example = BoneKnight()
		self.minion_health = example.max_hp
		self.minion_damage = example.spells[0].damage
		self.num_summons = 2
		self.guard_name = example.name

		self.counter_max = 5
		self.counter = self.counter_max

	def get_extra_examine_tooltips(self):
		return [BoneKnight()]

	def get_description(self):
		return ("Every 5 turns, if you have less than [{num_summons}:num_summons] Bone Knights, summon a Bone Knight.\n"
				"Bone knights are shielded melee units with a [dark] melee attack that drains max life.\n").format(**self.fmt_dict())

	def on_advance(self):

		num_guards = len([u for u in self.owner.level.units if not are_hostile(self.owner, u) and u.name in self.guard_name])
		if num_guards >= self.get_stat('num_summons'):
			return

		self.counter -= 1

		if self.counter <= 0:
			self.counter = self.counter_max
			unit = BoneKnight()
			apply_minion_bonuses(self, unit)
			self.summon(unit)


class Cracklevoid(Upgrade):

	def on_init(self):
		self.name = "Cracklevoid"
		self.level = 6
		self.tags = [Tags.Lightning, Tags.Arcane]
		self.num_targets = 2
		self.radius = 6

		self.global_triggers[EventOnDamaged] = self.on_damage

	def get_description(self):
		return ("Whenever an enemy takes [arcane] damage, deal that much [lightning] damage to up to [{num_targets}:num_targets] enemy units in a [{radius}_tile:radius] burst.").format(**self.fmt_dict())

	def on_damage(self, evt):
		if not are_hostile(evt.unit, self.owner):
			return

		if evt.damage_type == Tags.Arcane:
			self.owner.level.queue_spell(self.send_bolts(evt.unit, evt.damage))

	def bolt(self, damage, source, target):
		for point in Bolt(self.owner.level, source, target):
			self.owner.level.show_effect(point.x, point.y, Tags.Lightning)
			yield True

		target.deal_damage(damage, Tags.Lightning, self)
		yield False

	def send_bolts(self, source, damage):

		targets = self.owner.level.get_units_in_ball(source, self.get_stat('radius'))
		targets = [t for t in targets if are_hostile(t, self.owner) and t != source and self.owner.level.can_see(t.x, t.y, source.x, source.y)]
		random.shuffle(targets)

		bolts = [self.bolt(damage, source, t) for t in targets[:self.get_stat('num_targets')]]

		while bolts:
			bolts = [b for b in bolts if next(b)]
			yield

class SpiderSpawning(Upgrade):

	def on_init(self):
		self.name = "Spider Spawning"
		self.level = 4
		self.tags = [Tags.Nature]
		self.description = "Whenever an enemy dies to poison damage, summon a friendly spider nearby"
		self.global_triggers[EventOnDeath] = self.on_death

		spider_default = GiantSpider()
		self.minion_health = spider_default.max_hp
		self.minion_damage = spider_default.spells[0].damage
		self.duration = spider_default.spells[0].buff_duration

	def get_extra_examine_tooltips(self):
		return [GiantSpider()]

	def get_description(self):
		return ("Whenever an enemy dies to [poison] damage, summon a friendly spider nearby.\n"
				"Giant spiders have [{minion_health}_HP:minion_health] and spin webs.\n"
			 	"Giant spiders have a melee attack which deals [{minion_damage}_physical:physical] and inflicts [5_turns:duration] of [poison].\n"
			 	"Webs [stun] non spider units which step on them for [1_turn:duration].\n"
			 	+ text.poison_desc + text.stun_desc).format(**self.fmt_dict())

	def on_death(self, evt):
		if not evt.damage_event:
			return
		if evt.damage_event.damage_type != Tags.Poison:
			return

		if not are_hostile(self.owner, evt.unit):
			return

		spider = GiantSpider()
		spider.max_hp = self.get_stat('minion_health')
		spider.spells[0].damage = self.get_stat('minion_damage')
		spider.spells[0].buff_duration = self.get_stat('duration')
		self.summon(spider, target=evt.unit)

class ParalyzingVenom(Upgrade):

	def on_init(self):
		self.name = "Paralyzing Venom"
		self.description = "Whenever an enemy takes [poison] damage, it has a 25% chance to be [stunned] for [1_turn:duration]."
		self.tags = [Tags.Nature]
		self.level = 4
		self.global_triggers[EventOnDamaged] = self.on_damage

	def on_damage(self, evt):
		if evt.damage_type != Tags.Poison:
			return

		if not are_hostile(evt.unit, self.owner):
			return

		if random.random() > .25:
			return

		evt.unit.apply_buff(Stun(), 1)

class VenomSpitSpell(SimpleRangedAttack):

	def __init__(self):
		def apply_poison(caster, target):
			target.apply_buff(Poison(), 10)
		SimpleRangedAttack.__init__(self, damage=4, damage_type=Tags.Poison, onhit=apply_poison, cool_down=4, range=6)
		self.description = "Applies poison for 10 turns"
		self.name = "Venom Spit"

class VenomSpit(Upgrade):

	def on_init(self):
		self.name = "Venom Spit"
		self.tags = [Tags.Nature]
		self.level = 4
		self.minion_damage = 4
		self.minion_range = 6

		self.global_triggers[EventOnUnitAdded] = self.on_unit_add


	def get_description(self):
		return ("Your summoned [living] and [nature] units gain Venom Spit.\n"
				"Venom spit is a ranged attack which deals [{minion_damage}_poison:poison] damage and inflicts [poison] for [10_turns:duration].\n"
				"Venom spit has a [{minion_range}_tile:range] range, and a [4_turn:cooldown] cooldown.").format(**self.fmt_dict())

	def should_grant(self, unit):
		if unit.is_player_controlled:
			return False
		return not are_hostile(unit, self.owner) and (Tags.Nature in unit.tags or Tags.Living in unit.tags)

	def on_unit_add(self, evt):
		if self.should_grant(evt.unit):
			self.grant(evt.unit)

	def grant(self, unit):
		spell = VenomSpitSpell()
		spell.damage = self.get_stat('minion_damage')
		spell.range = self.get_stat('minion_range')
		#weird cause im trying to insert at 0
		spell.caster = unit
		unit.add_spell(spell, prepend=True)

	def on_advance(self):
		for unit in self.owner.level.units:
			spit = [s for s in unit.spells if isinstance(s, VenomSpitSpell)]
			if spit and not self.should_grant(unit):
				unit.remove_spell(spit[0])
			elif not spit and self.should_grant(unit):
				self.grant(unit)
				
class FrozenSouls(Upgrade):

	def on_init(self):
		self.name = "Icy Vengeance"
		self.tags = [Tags.Ice, Tags.Dark]
		self.level = 6
		self.global_triggers[EventOnDeath] = self.on_death
		self.radius = 5
		self.num_targets = 3

	def get_description(self):
		return ("Whenever one of your minions dies, up to [{num_targets}:num_targets] random enemies in a [{radius}_tile:radius] radius take [ice] damage equal to half the dead minion's max HP.").format(**self.fmt_dict())

	def on_death(self, evt):
		if are_hostile(evt.unit, self.owner):
			return
		self.owner.level.queue_spell(self.do_damage(evt))

	def do_damage(self, evt):
		units = self.owner.level.get_units_in_ball(evt.unit, self.get_stat('radius'))
		units = [u for u in units if are_hostile(self.owner, u)]
		random.shuffle(units)
		for unit in units[:self.get_stat('num_targets')]:
			for p in self.owner.level.get_points_in_line(evt.unit, unit)[1:-1]:
				self.owner.level.show_effect(p.x, p.y, Tags.Ice)
			unit.deal_damage(evt.unit.max_hp // 2, Tags.Ice, self)
			yield

class IceTap(Upgrade):

	def on_init(self):
		self.name = "Ice Tap"
		self.tags = [Tags.Ice, Tags.Arcane]
		self.level = 6

		self.damage = 8
		self.owner_triggers[EventOnSpellCast] = self.on_spell_cast
		self.radius = 3
		self.num_targets = 4

		self.copying = False

	def get_description(self):
		return "Whenever you cast an [arcane] spell targeting a [frozen] unit, make a copy of that spell targeting each other frozen unit in line of sight.\nRemove [frozen] from all affected units.".format(**self.fmt_dict())

	def on_spell_cast(self, evt):
		if self.copying:
			return False

		unit = self.owner.level.get_unit_at(evt.x, evt.y)
		if not unit:
			return

		b = unit.get_buff(FrozenBuff)
		if not b:
			return

		if Tags.Arcane not in evt.spell.tags:
			return

		copy_targets = [u for u in self.owner.level.get_units_in_los(unit) if are_hostile(self.owner, u) and u.has_buff(FrozenBuff) and u != unit]

		spell = type(evt.spell)()

		self.copying = True

		unit.remove_buff(FrozenBuff)
		for u in copy_targets:
			if evt.spell.can_copy(u.x, u.y):
				self.owner.level.act_cast(self.owner, evt.spell, u.x, u.y, pay_costs=False)
				b = u.get_buff(FrozenBuff)
				if b:
					u.remove_buff(b)

		self.copying = False

class Frostbite(Upgrade):

	def on_init(self):
		self.name = "Frostbite"
		self.level = 4
		self.tags = [Tags.Ice, Tags.Dark]
		self.damage = 6

	def get_description(self):
		return "Each turn all frozen enemies take [{damage}_dark:dark] damage.".format(**self.fmt_dict())

	def on_advance(self):
		for u in self.owner.level.units:
			if are_hostile(self.owner, u) and u.has_buff(FrozenBuff):
				u.deal_damage(self.get_stat('damage'), Tags.Dark, self)

class SteamAnima(Upgrade):

	def on_init(self):
		self.global_triggers[EventOnUnfrozen] = self.on_unfrozen

		self.tags = [Tags.Ice, Tags.Fire]
		self.level = 6

		self.name = "Steam Anima"
		self.description = "Whenever a unit is unfrozen by fire damage, spawn 3 friendly steam elementals nearby for 6 turns.\n\nThe steam elemental has a ranged fire attack, and is immune to fire, ice and physical damage."

		self.minion_duration = 5
		self.minion_damage = 9
		self.minion_range = 6
		self.minion_health = 16
		self.num_summons = 3

	def get_description(self):
		return ("Whenever a unit is unfrozen by fire damage, spawn [3:num_summons] steam elementals nearby.\n"
				"Steam elementals have [{minion_health}_HP:minion_health], [100_physical:physical] resist, [100_ice:ice] resist, and [100_fire:fire] resist.\n"
				"Steam elementals have a ranged attack which deals [{minion_damage}_fire:fire] damage, with a range of [{minion_range}_tiles:minion_range].\n"
				"The elementals vanish after [{minion_duration}_turns:minion_duration].").format(**self.fmt_dict())

	def get_extra_examine_tooltips(self):
		return [self.make_anima()]

	def make_anima(self):
		elemental = Unit()
		elemental.name = "Steam Elemental"
		elemental.max_hp = self.get_stat('minion_health')
		elemental.resists[Tags.Physical] = 100
		elemental.resists[Tags.Fire] = 100
		elemental.resists[Tags.Ice] = 100
		elemental.tags = [Tags.Elemental, Tags.Fire]
		elemental.turns_to_death = self.get_stat('minion_duration')
		elemental.spells.append(SimpleRangedAttack(damage=self.get_stat('minion_damage'), damage_type=Tags.Fire, range=self.get_stat('minion_range')))
		return elemental

	def on_unfrozen(self, evt):
		if evt.dtype != Tags.Fire:
			return

		for i in range(self.get_stat('num_summons')):
			elemental = self.make_anima()
			self.summon(elemental, target=evt.unit)

class StormCaller(Upgrade):

	def on_init(self):
		self.global_triggers[EventOnDamaged] = self.on_damage
		self.name = "Storm Caller"
		self.level = 6
		self.tags = [Tags.Lightning, Tags.Ice, Tags.Nature]
		self.duration = 5
		self.damage = 5

	def get_description(self):
		return ("Whenever [ice] or [lightning] damage is dealt to an enemy unit, create a blizzard or thundercloud nearby.\n"
				"The blizzards deal [{damage}_ice:ice] damage and may freeze enemies, the thunderclouds strike inconsistently but deal twice as much [lightning] damage.\n"
				"The clouds last [{duration}_turns:duration].").format(**self.fmt_dict())

	def get_thunder(self):
		cloud = StormCloud(self.owner)
		cloud.damage =  2*self.get_stat('damage')
		return cloud

	def get_blizzard(self):
		cloud = BlizzardCloud(self.owner)
		cloud.damage = self.get_stat('damage')
		return cloud

	def on_damage(self, evt):
		if not are_hostile(self.owner, evt.unit):
			return

		if evt.damage_type not in [Tags.Ice, Tags.Lightning]:
			return

		cloud = random.choice([self.get_thunder(), self.get_blizzard()])
		cloud.source = self

		if not self.owner.level.tiles[evt.unit.x][evt.unit.y].cloud:
			self.owner.level.add_obj(cloud, evt.unit.x, evt.unit.y)
		else:
			possible_points = self.owner.level.get_points_in_ball(evt.unit.x, evt.unit.y, 1, diag=True)
			def can_cloud(p):
				tile = self.owner.level.tiles[p.x][p.y]
				if tile.cloud:
					return False
				if tile.is_wall():
					return False
				return True

			possible_points = [p for p in possible_points if can_cloud(p)]
			if possible_points:
				point = random.choice(possible_points)
				self.owner.level.add_obj(cloud, point.x, point.y)

class HolyWater(Upgrade):

	def on_init(self):
		self.name = "Holy Water"

		self.level = 4
		self.global_triggers[EventOnDamaged] = self.on_damage
		self.tags = [Tags.Holy, Tags.Ice]

		self.damage = 17
		self.num_targets = 3

	def get_description(self):
		return ("Whenever a [frozen] enemy takes [holy] damage, you and all allies in line of sight gain [1_SH:shields], up to a max of [5:shields].\n"
				"Whenever a [frozen] enemy is slain by [holy] damage, deal [{damage}_holy:holy] damage to 3 random enemies in line of sight of the slain unit.").format(**self.fmt_dict())

	def on_damage(self, evt):
		if not are_hostile(self.owner, evt.unit):
			return
		if evt.damage_type != Tags.Holy:
			return
		if not evt.unit.has_buff(FrozenBuff):
			return

		for u in self.owner.level.get_units_in_los(evt.unit):
			if are_hostile(u, self.owner):
				continue
			if u.shields >= 5:
				continue
			u.add_shields(1)

		if evt.unit.cur_hp <= 0:
			self.owner.level.queue_spell(self.explode(evt.unit))

	def explode(self, target):
		
		targets = [u for u in self.owner.level.get_units_in_los(target) if u != target and are_hostile(u, self.owner)]

		random.shuffle(targets)

		targets = sorted(targets, key=lambda u: distance(u, target))

		for unit in targets[:self.get_stat('num_targets')]:
			self.owner.level.show_path_effect(self.owner, unit, Tags.Holy, minor=True)
			unit.deal_damage(self.get_stat('damage'), Tags.Holy, self)

		yield


class HibernationBuff(Buff):

	def __init__(self, upgrade):
		self.upgrade = upgrade
		Buff.__init__(self)

	def on_init(self):
		self.buff_type = BUFF_TYPE_PASSIVE
		self.resists[Tags.Ice] = 75
		self.owner_triggers[EventOnDamaged] = self.on_damaged

	def on_pre_advance(self):
		if self.owner.has_buff(FrozenBuff):
			self.owner.deal_damage(-15, Tags.Heal, self.upgrade)

	def on_damaged(self, evt):
		if evt.damage_type == Tags.Ice:
			buff = self.owner.get_buff(FrozenBuff)
			if not buff:
				self.owner.apply_buff(FrozenBuff(), self.upgrade.get_stat('duration'))
			else:
				buff.turns_left += self.upgrade.get_stat('duration')

class Hibernation(Upgrade):

	def on_init(self):
		self.name = "Hibernation"
		self.description = ("Your living minions gain [75_ice:ice] resist.\n"
							"Your living minions freeze for [3_turns:duration] upon taking ice damage.\n"
							"Your living minions heal for [15_HP:heal] each turn while [frozen].\n")
		self.global_triggers[EventOnUnitAdded] = self.on_unit_add
		self.tags = [Tags.Ice, Tags.Nature]
		self.level = 4
		self.duration = 3

	def on_unit_add(self, evt):
		if are_hostile(self.owner, evt.unit):
			return
		if self.owner == evt.unit:
			return
		if Tags.Living not in evt.unit.tags:
			return
		evt.unit.apply_buff(HibernationBuff(self))

class CrystallographerActiveBuff(Buff):

	def __init__(self, amt):
		self.amt = amt
		Buff.__init__(self)

	def on_init(self):
		self.buff_type = BUFF_TYPE_BLESS
		self.stack_type = STACK_INTENSITY
		self.tag_bonuses[Tags.Sorcery]['damage'] = self.amt
		self.color = Tags.Arcane.color
		self.name = "Crystal Power: %d" % self.amt
		self.show_effect = False

class Crystallographer(Upgrade):

	def on_init(self):
		self.name = "Crystal Power"
		self.description = "Your [sorcery] spells gain [2_damage:damage] for each [frozen] or [glassified] unit."
		self.tags = [Tags.Ice, Tags.Arcane, Tags.Sorcery]
		self.level = 4

	def on_pre_advance(self):

		amt = 0
		for u in self.owner.level.units:
			if u.has_buff(FrozenBuff) or u.has_buff(GlassPetrifyBuff):
				amt += 2
		
		if amt:
			self.owner.apply_buff(CrystallographerActiveBuff(amt), 1)

class RadiantCold(Upgrade):

	def on_init(self):
		self.name = "Radiant Chill"
		self.level = 4
		self.owner_triggers[EventOnSpellCast] = self.on_cast
		self.duration = 3
		self.tags = [Tags.Ice]

	def get_description(self):
		return "Whenever you cast an [ice] spell, [freeze] the nearest unfrozen enemy to that spell's target for [{duration}_turns:duration].".format(**self.fmt_dict())

	def on_cast(self, evt):

		if Tags.Ice not in evt.spell.tags:
			return

		self.owner.level.queue_spell(self.do_freeze(evt))

	def do_freeze(self, evt):
		targets = [u for u in self.owner.level.units if are_hostile(self.owner, u) and not u.has_buff(FrozenBuff)]
		if targets:
			# Shuffle first to randomly break ties
			random.shuffle(targets)
			targets.sort(key=lambda u: distance(Point(evt.x, evt.y), u))
			target = targets[0]
			self.owner.level.show_path_effect(Point(evt.x, evt.y), target, Tags.Ice, minor=True)
			target.apply_buff(FrozenBuff(), self.get_stat('duration'))

		yield

class ShatterShards(Upgrade):

	def on_init(self):
		self.name = "Shatter Shards"
		self.level = 6
		self.tags = [Tags.Ice]
		self.global_triggers[EventOnUnfrozen] = self.on_unfrozen
		self.radius = 6
		self.num_targets = 3
		self.damage = 6

	def get_description(self):
		return "Whenever a unit is unfrozen or a [frozen] unit is killed, up to [3_enemies:num_targets] in a [6_tile:radius] burst take [{damage}_ice:ice] and [{damage}_physical:physical] damage.".format(**self.fmt_dict())	

	def on_unfrozen(self, evt):
		self.owner.level.queue_spell(self.do_shards(evt))

	def bolt(self, u, v):
		for p in self.owner.level.get_points_in_line(u, v, find_clear=True):
			self.owner.level.show_effect(p.x, p.y, Tags.Ice)
			yield True

		for dtype in [Tags.Ice, Tags.Physical]:
			v.deal_damage(self.get_stat('damage'), dtype, self)
			yield True

		yield False

	def do_shards(self, evt):
		nearby_units = self.owner.level.get_units_in_ball(evt.unit, self.get_stat('radius'))
		nearby_units = [v for v in nearby_units if evt.unit != v and are_hostile(self.owner, v) and self.owner.level.can_see(v.x, v.y, evt.unit.x, evt.unit.y)]

		bolts = []

		#import pdb
		#pdb.set_trace()

		random.shuffle(nearby_units)
		for v in nearby_units[:self.get_stat('num_targets')]:
			bolts.append(self.bolt(evt.unit, v))		

		while any(bolts):
			bolts = [b for b in bolts if next(b)]
			yield

class FragilityBuff(Buff):

	def on_init(self):
		self.name = "Fragile"
		self.buff_type = BUFF_TYPE_CURSE
		self.color = Tags.Ice.color
		self.resists[Tags.Ice] = -100
		self.resists[Tags.Physical] = -100
		self.owner_triggers[EventOnBuffRemove] = self.on_unfreeze

	def on_unfreeze(self, evt):
		if isinstance(evt.buff, FrozenBuff):
			self.owner.remove_buff(self)


class FrozenFragility(Upgrade):

	def on_init(self):
		self.name = "Frozen Fragility"
		self.level = 4
		self.tags = [Tags.Ice]
		self.description = "Whenever an enemy is [frozen], reduces that enemy's [physical] and [ice] resist by 100 until it is unfrozen."
		self.global_triggers[EventOnBuffApply] = self.on_frozen

	def on_frozen(self, evt):
		if not isinstance(evt.buff, FrozenBuff):
			return
		if not are_hostile(self.owner, evt.unit):
			return
		evt.unit.apply_buff(FragilityBuff())

class DragonScalesBuff(Buff):

	def __init__(self, damage_type):
		Buff.__init__(self)
		self.resists[damage_type] = 100
		self.name = "%s Scales" % damage_type.name
		self.color = damage_type.color

class DragonScalesSkill(Upgrade):

	def on_init(self):
		self.name = "Scalespinner"
		self.level = 6
		self.tags = [Tags.Dragon]
		self.global_triggers[EventOnSpellCast] = self.on_spell_cast
		self.duration = 5

	def get_description(self):
		return "Whenever an allied [dragon] uses a breath weapon, all your summoned units gain 100 resist to that breath weapon's element for [{duration}_turns:duration]".format(**self.fmt_dict())

	def on_spell_cast(self, evt):
		if not isinstance(evt.spell, BreathWeapon):
			return
		if are_hostile(evt.caster, self.owner):
			return
		if evt.caster == self.owner:
			return
		for u in self.owner.level.units:
			if are_hostile(u, self.owner):
				continue
			if u.is_player_controlled:
				continue
			buff = DragonScalesBuff(evt.spell.damage_type)
			u.apply_buff(buff, self.get_stat('duration'))

class CollectedAgony(Upgrade):

	def on_init(self):
		self.name = "Collected Agony"
		self.global_triggers[EventOnDamaged] = self.on_damage
		self.charges = 0
		self.tags = [Tags.Dark, Tags.Nature]
		self.level = 5
		self.description = "Each turn, deal 2x the sum total of all [poison] damage dealt to all units to the nearest enemy as [dark] damage."

	def on_damage(self, evt):
		if evt.damage_type == Tags.Poison:
			self.charges += evt.damage

	def on_advance(self):
		if self.charges == 0:
			return

		options = [u for u in self.owner.level.units if are_hostile(u, self.owner)]

		options.sort(key=lambda u: distance(u, self.owner))
		if not options:
			return

		min_len = distance(options[0], self.owner)
		options = [o for o in options if distance(o, self.owner) <= min_len]

		target = random.choice(options)
		self.owner.level.queue_spell(self.do_damage(target, 2*self.charges))

		self.charges = 0

	def do_damage(self, target, damage):
		self.owner.level.show_path_effect(target, target,Tags.Dark)
		yield
		target.deal_damage(damage, Tags.Dark, self)

class Moonspeaker(Upgrade):

	def on_init(self):
		self.name = "Moonspeaker"
		self.global_triggers[EventOnDamaged] = self.on_damage
		self.tags = [Tags.Arcane, Tags.Holy]
		self.level = 6
		self.description = "Whenever an enemy takes [arcane] damage, all [holy] minions in line of sight of that enemy redeal 50% of that damage as [holy] damage."

	def on_damage(self, evt):
		if not are_hostile(self.owner, evt.unit):
			return
		if evt.damage_type != Tags.Arcane:
			return

		d = math.ceil(evt.damage * .5)

		for u in self.owner.level.get_units_in_los(evt.unit):
			if are_hostile(self.owner, u):
				continue
			if Tags.Holy not in u.tags:
				continue
			self.owner.level.queue_spell(self.bolt(u, evt.unit, d))

	def bolt(self, u, t, d):
		for p in self.owner.level.get_points_in_line(u, t, find_clear=True):
			self.owner.level.show_effect(p.x, p.y, Tags.Holy, minor=True)
			yield
		t.deal_damage(d, Tags.Holy, self)

class Voidthorns(Upgrade):

	def on_init(self):
		self.name = "Void Spikes"
		self.global_triggers[EventOnDamaged] = self.on_damage
		self.tags = [Tags.Arcane, Tags.Dark]
		self.level = 7
		self.damage = 5

	def get_description(self):
		return "Whenever you or one of your [arcane] or [undead] allies take damage from an enemy, deal [{damage}_arcane:arcane] damage to the source of that damage.".format(**self.fmt_dict())

	def on_damage(self, evt):
		if are_hostile(self.owner, evt.unit):
			return

		if not evt.source:
			return

		if not evt.source.owner:
			return

		if not are_hostile(evt.source.owner, self.owner):
			return

		if not (evt.unit == self.owner or Tags.Arcane in evt.unit.tags or Tags.Undead in evt.unit.tags):
			return

		evt.source.owner.deal_damage(self.get_stat('damage'), Tags.Arcane, self)

class NecrostaticStack(Buff):

	def __init__(self, strength):
		self.strength = strength
		Buff.__init__(self)

	def on_init(self):
		self.name = "Necrostatics %d" % self.strength
		self.tag_bonuses[Tags.Lightning]['damage'] = self.strength
		self.color = Tags.Lightning.color
		self.show_effect = False

class Necrostatics(Upgrade):

	def on_init(self):
		self.name = "Necrostatics"
		self.tags = [Tags.Lightning, Tags.Dark]
		self.level = 5

	def get_description(self):
		return "You get +1 [lightning] damage for each undead ally you control."

	def on_pre_advance(self):
		b = self.owner.get_buff(NecrostaticStack)
		if b:
			self.owner.remove_buff(b)

		num_undead_allies = len([u for u in self.owner.level.units if not are_hostile(u, self.owner) and Tags.Undead in u.tags])
		if num_undead_allies:
			self.owner.apply_buff(NecrostaticStack(num_undead_allies))

class Purestrike(Upgrade):

	def on_init(self):
		self.name = "Purestrike"
		self.tags = [Tags.Holy, Tags.Arcane]
		self.level = 5
		self.global_triggers[EventOnDamaged] = self.on_damage

	def get_description(self):
		return "Whenever you or an allied unit deals physical damage to an enemy, if the source of that damage is shielded, redeal 50% of that damage as arcane and 50% of that damage as holy."

	def on_damage(self, evt):
		if evt.damage_type != Tags.Physical:
			return
		if not evt.source or not evt.source.owner:
			return
		if evt.source.owner.shields < 1:
			return
		if evt.damage < 2:
			return
		self.owner.level.queue_spell(self.do_conversion(evt))

	def do_conversion(self, evt):
		evt.unit.deal_damage(evt.damage // 2, Tags.Holy, self)
		for i in range(5):
			yield
		evt.unit.deal_damage(evt.damage // 2, Tags.Arcane, self)

class SilkShifter(Upgrade):

	def on_init(self):
		self.name = "Silkshifter"
		self.tags = [Tags.Nature, Tags.Translocation]
		self.level = 4
		self.global_triggers[EventOnSpellCast] = self.on_cast

	def on_applied(self, owner):
		self.owner.tags.append(Tags.Spider)

	def on_unapplied(self):
		self.owner.tags.remove(Tags.Spider)

	def get_description(self):
		return ("You are a [spider].\n"
				"Passively spawn a web each turn on a random adjacent tile.  Webs will not spawn on top of units or walls.\n"
				"Whenever you cast a translocation spell targeting a web, refund 1 charge of that spell and consume the web.")

	def on_advance(self):
		if not any(are_hostile(self.owner, u) for u in self.owner.level.units):
			return
		spawn_webs(self.owner)

	def on_cast(self, evt):
		# refund a charge of the spell if there is a web at the target
		cloud = self.owner.level.tiles[evt.x][evt.y].cloud
		if not cloud or not isinstance(cloud, SpiderWeb):
			return

		# consume the web
		self.owner.level.remove_obj(cloud)

		if Tags.Translocation in evt.spell.tags:
			evt.spell.cur_charges += 1
			evt.spell.cur_charges = min(evt.spell.get_stat('max_charges'), evt.spell.cur_charges)

class InfernoEngines(Upgrade):

	def on_init(self):
		self.name = "Inferno Engines"
		self.tags = [Tags.Fire, Tags.Metallic]
		self.level = 6
		self.owner_triggers[EventOnSpellCast] = self.on_spell_cast
		self.duration = 10

	def get_description(self):
		return ("Whenever you cast a [fire] spell, all of your [metallic] allies gain [2_damage:damage] [fire] aura with radius equal to the level of the spell you cast for [{duration}_turns:duration].\n"
			    "This damage is fixed, and cannot be increased using shrines, skills, or buffs.\n").format(**self.fmt_dict())

	def on_spell_cast(self, evt):
		if evt.spell.level <= 0:
				return

		if Tags.Fire not in evt.spell.tags:
			return

		for u in self.owner.level.units:
			if are_hostile(u, self.owner):
				continue
			if u == self.owner:
				continue
			if Tags.Metallic not in u.tags:
				continue

			aura = DamageAuraBuff(damage=2, damage_type=Tags.Fire, radius=evt.spell.level)
			aura.name = "Inferno Engine"
			aura.stack_type = STACK_REPLACE

			u.apply_buff(aura, self.get_stat('duration'))

class Megavenom(Upgrade):

	def on_init(self):
		self.name = "Megavenom"
		self.level = 4
		self.tags = [Tags.Nature, Tags.Dark]
		self.damage = 4

	def get_description(self):
		return ("Poisoned enemies take [{damage}:poison] additional [poison] damage each turn.").format(**self.fmt_dict())

	def on_advance(self):
		for u in self.owner.level.units:
			if not are_hostile(u, self.owner):
				continue
			if u.has_buff(Poison):
				u.deal_damage(self.get_stat('damage'), Tags.Poison, self)

class AcidFumes(Upgrade):

	def on_init(self):
		self.name = "Acid Fumes"
		self.tags = [Tags.Nature, Tags.Dark]
		self.description = "Each turn, a random unacidified enemy is acidified.\nAcidified units lose 100 [poison] resist."
		self.level = 5

	def on_advance(self):
		candidates = [u for u in self.owner.level.units if are_hostile(u, self.owner) and not u.has_buff(Acidified)]
		if candidates:
			target = random.choice(candidates)
			target.apply_buff(Acidified())


class Starcharge(Buff):

	def __init__(self, spell):
		Buff.__init__(self)
		self.spell = spell

	def on_init(self):
		self.name = "Starcharged"
		self.color = Tags.Arcane.color
		self.buff_type = BUFF_TYPE_BLESS
		self.stack_type = STACK_DURATION

	def on_advance(self):
		available_targets = [u for u in self.owner.level.get_units_in_los(self.owner) if are_hostile(self.owner, u)]
		dtypes = [Tags.Arcane, Tags.Fire]
		random.shuffle(available_targets)
		for dtype in dtypes:
			# Dont waste hits on enemies that are immune to them
			cur_avail_targets = [t for t in available_targets if t.resists[dtype] < 100]
			if not cur_avail_targets:
				continue
			target = cur_avail_targets.pop()
			target.deal_damage(self.spell.get_stat('damage'), dtype, self)

			self.owner.level.show_path_effect(self.owner, target, dtype, minor=True, straight=True)

			available_targets.remove(target)

class PurpleFlameSorcery(Upgrade):

	def on_init(self):
		self.name = "Voidflame Lantern"
		self.tags = [Tags.Fire, Tags.Arcane]
		
		self.level = 4
		self.owner_triggers[EventOnSpellCast] = self.on_spell_cast

		self.damage = 6

	def get_description(self):
		return ("Whenever you cast a [fire] or [arcane] spell, gain starcharged with duration equal to the spell's level.\n"
			    "Starcharged deals [{damage}_arcane:arcane] damage to one random enemy in line of sight each turn, and then [{damage}_fire:fire] damage to another.").format(**self.fmt_dict())

	def on_spell_cast(self, evt):
		if Tags.Fire in evt.spell.tags or Tags.Arcane in evt.spell.tags:
			self.owner.apply_buff(Starcharge(self), evt.spell.level)

class SorcererPoet(Upgrade):

	def on_init(self):
		self.name = "Chaos Poet"
		self.tags = [Tags.Chaos, Tags.Conjuration]
		self.level = 7
		self.global_triggers[EventOnDamaged] = self.on_damage

		self.fire = 0
		self.lightning = 0
		self.physical = 0

	def get_description(self):
		return "Each turn, if atleast 13 fire, lightning and physical damage were dealt to enemies, summon a Chaos Quill."

	def get_extra_examine_tooltips(self):
		return [ChaosQuill(), LivingLightningScroll(), LivingFireballScroll()]

	def on_damage(self, evt):
		if not are_hostile(self.owner, evt.unit):
			return

		if evt.damage_type == Tags.Fire:
			self.fire += evt.damage
		if evt.damage_type == Tags.Physical:
			self.lightning += evt.damage
		if evt.damage_type == Tags.Lightning:
			self.physical += evt.damage

	def on_advance(self):

		if self.physical >= 13 and self.lightning >= 13 and self.fire >= 13:
			quill = ChaosQuill()
			apply_minion_bonuses(self, quill)
			self.summon(quill, sort_dist=False, radius=9)

		self.physical = 0
		self.lightning = 0
		self.fire = 0

class MasterOfSpace(Upgrade):

	def on_init(self):
		self.name = "Master of Space"
		self.tags = [Tags.Arcane]
		self.level = 5
		self.global_bonuses['range'] = 2
		self.global_bonuses['radius'] = 1

class MasterOfTime(Upgrade):

	def on_init(self):
		self.name = "Master of Time"
		self.tags = [Tags.Enchantment]
		self.level = 5
		self.global_bonuses['duration'] = 2
		self.global_bonuses['minion_duration'] = 2

class MasterOfMemories(Upgrade):

	def on_init(self):
		self.name = "Master of Memories"
		self.tags = [Tags.Arcane]
		self.level = 4
		self.global_bonuses['max_charges'] = 1

class SpellSniper(Upgrade):

	def on_init(self):
		self.name = "Spell Sniper"
		self.tags = [Tags.Sorcery]
		self.level = 4
		self.global_bonuses['range'] = 2

class Hordemancer(Upgrade):

	def on_init(self):
		self.name = "Hordemancer"
		self.tags = [Tags.Conjuration]
		self.level = 5
		self.global_bonuses['num_summons'] = 1

class Echomancy(Buff):

	def __init__(self, spell):
		self.spell = spell
		Buff.__init__(self)

	def on_init(self):
		self.name = "Echomancy: %s" % self.spell.name
		self.description = "Refund next charge used to cast %s" % self.spell.name
		self.color = Tags.Arcane.color
		# Do nothing in this buff, just let the upgrade do stuff by checking for this buff


class Echomancer(Upgrade):

	def on_init(self):
		self.name = "Echomancer"
		self.tags = [Tags.Sorcery]
		self.level = 6

		self.prev_spell = None

		self.idle_counter = 0
		self.refund_counter = 0

		self.owner_triggers[EventOnSpellCast] = self.on_spell_cast

	def get_description(self):
		return ("Whenever you cast the same [sorcery] spell twice in a row, gain a charge of that spell.\n")

	def on_advance(self):
		if self.idle_counter:
			self.idle_counter -= 1
			if self.idle_counter == 0:
				self.prev_spell = None
				self.refund_counter = 0


	def on_spell_cast(self, evt):
		
		if Tags.Sorcery not in evt.spell.tags:
			return

		existing = self.owner.get_buff(Echomancy)

		# If existing echomancy buff for this spell, gain charge
		if existing and existing.spell == evt.spell:
			evt.spell.cur_charges += 1
			self.owner.remove_buff(existing)
		else:
			self.owner.remove_buffs(Echomancy)
			self.owner.apply_buff(Echomancy(evt.spell), 2)

class Disintegrator(Upgrade):

	def on_init(self):
		self.name = "Disintegrator"
		self.level = 7
		self.tags = [Tags.Sorcery]

		self.description = "For every 40 damage dealt by [sorcery] spells you cast, deal [1_physical:physical] damage to all enemy units.\nThis damage cannot be boosted."

		self.global_triggers[EventOnDamaged] = self.on_damage

		self.threshold = 40
		self.charges = 0

	def on_damage(self, evt):
		if not isinstance(evt.source, Spell):
			return

		if evt.source.caster != self.owner:
			return

		if Tags.Sorcery not in evt.source.tags:
			return

		self.charges += evt.damage

		while self.charges > self.threshold:
			self.owner.level.queue_spell(self.do_damage())
			self.charges -= self.threshold

	def do_damage(self):
		for u in self.owner.level.units:
			if are_hostile(self.owner, u):
				u.deal_damage(1, Tags.Physical, self)
				if random.random() < .1:
					yield

class FaeMalevolence(Upgrade):

	def on_init(self):
		self.name = "Fae Malevolence"
		self.tags = [Tags.Arcane, Tags.Nature, Tags.Enchantment]
		self.description = ("Redeal 50% of all [physical], [poison], [lightning], and [ice] damage dealt to enemies by [enchantments:enchantment] as [arcane] damage."
						   "\nRedeal 50% of all other damage dealt to enemies by [enchantments:enchantment] as [poison] damage.")
		self.level = 5
		self.global_triggers[EventOnDamaged] = self.on_damage

	def on_damage(self, evt):
		if not are_hostile(evt.unit, self.owner):
			return

		if not evt.source:
			return

		if not isinstance(evt.source, Spell):
			return

		if Tags.Enchantment not in evt.source.tags:
			return

		dmg = evt.damage // 2
		if dmg:

			if evt.damage_type in [Tags.Physical, Tags.Poison, Tags.Lightning, Tags.Ice]:
				dtype = Tags.Arcane
			else:
				dtype = Tags.Poison

			evt.unit.deal_damage(dmg, dtype, self)

class BloodAnima(Upgrade):

	def on_init(self):
		self.name = "Blood Anima"
		self.owner_triggers[EventOnSpendHP] = self.on_spend_hp
		self.tags = [Tags.Conjuration, Tags.Blood]
		self.level = 5
		self.counter = 0
		self.minion_duration = 13

	def get_description(self):
		return "For every 6 HP spent casting spells, summon a bloodghast for 13 turns."

	def get_extra_examine_tooltips(self):
		return [Bloodghast()]

	def on_spend_hp(self, evt):
		self.counter += evt.hp

		while self.counter > 6:
			ghast = Bloodghast()
			apply_minion_bonuses(self, ghast)
			self.summon(ghast)
			self.counter -= 6

class BloodLord(Upgrade):

	def on_init(self):
		self.name = "Blood Lord"
		self.tags = [Tags.Blood]
		self.level = 7
		
		self.tag_bonuses[Tags.Blood]['max_charges'] = 1
		self.tag_bonuses[Tags.Blood]['range'] = 2
		self.tag_bonuses[Tags.Blood]['minion_damage'] = 3

		self.tag_bonuses_pct[Tags.Blood]['minion_health'] = 50
		self.tag_bonuses_pct[Tags.Blood]['damage'] = 50

class Bloodreaper(Upgrade):

	def on_init(self):
		self.name = "Blood Reaping"
		self.tags = [Tags.Blood]
		self.level = 5
		self.description = "Whenever an enemy [demon] or [living] unit dies, gain 2 HP"
		self.global_triggers[EventOnDeath] = self.on_death

	def on_death(self, evt):
		if not are_hostile(self.owner, evt.unit):
			return

		if not (Tags.Living in evt.unit.tags or Tags.Demon in evt.unit.tags):
			return

		self.owner.deal_damage(-2, Tags.Heal, self)

class ScentOfBlood(Upgrade):

	def on_init(self):
		self.name = "Scent of Blood"
		self.tags = [Tags.Blood, Tags.Nature]
		self.level = 7
		self.description = "Whenever 200 damage is dealt by [blood] or [nature] spells, skills, or summons, summon a blood hound"
		self.global_triggers[EventOnDamaged] = self.on_damage
		self.counter = 0

	def on_damage(self, evt):

		if not evt.source:
			return

		if not evt.source.owner:
			return

		if not hasattr(evt.source, 'tags'):
			return

		is_tagged_summon = False
		if evt.source.owner:
			if evt.source.owner.source:
				if hasattr(evt.source.owner.source, 'tags'):
					if (Tags.Blood in evt.source.owner.source.tags or Tags.Nature in evt.source.owner.source.tags):
						is_tagged_summon = True

		is_tagged_source = (Tags.Blood in evt.source.tags) or (Tags.Nature in evt.source.tags)


		if is_tagged_summon or is_tagged_source:

			self.counter += evt.damage

			while self.counter > 125:
				hound = Bloodhound()
				apply_minion_bonuses(self, hound)
				self.summon(hound)
				self.counter -= 125

class Stormbrood(Upgrade):

	def on_init(self):
		self.name = "Stormbrood Tricksters"
		self.tags = [Tags.Lightning, Tags.Translocation]
		self.level = 4

		example = StormTroll()
		self.minion_health = example.max_hp
		self.minion_damage = example.spells[0].damage

		self.owner_triggers[EventOnSpellCast] = self.on_cast

	def get_extra_examine_tooltips(self):
		return [StormTroll()]

	def get_description(self):
		return ("Whenever you cast a translocation spell, summon a stormtroll trickster at the location you cast the spell from.")

	def on_cast(self, evt):
		if Tags.Translocation not in evt.spell.tags:
			return

		self.owner.level.queue_spell(self.do_summon(self.owner.x, self.owner.y))

	def do_summon(self, x, y):
		stormtroll = StormTroll()
		apply_minion_bonuses(self, stormtroll)

		blink = BlinkSpell()
		blink.statholder = self.owner
		blink.max_charges = 0
		blink.cur_charges = 0
		blink.cool_down = 8

		stormtroll.spells.insert(0, blink)

		self.summon(stormtroll, Point(x, y))
		yield

class LifesparkBuff(Buff):

	def __init__(self, skill):
		self.skill = skill
		Buff.__init__(self)

	def on_init(self):
		self.buff_type = BUFF_TYPE_BLESS
		self.stack_type = STACK_DURATION
		self.color = Tags.Lightning.color
		self.name = "Lifespark"

	def on_advance(self):
		unit = LightningFlies()
		unit.turns_to_death = self.skill.get_stat('minion_duration')
		apply_minion_bonuses(self.skill, unit)
		self.summon(unit)

class LightningBugs(Upgrade):

	def on_init(self):
		self.name = "Lifespark Lantern"
		self.tags = [Tags.Lightning, Tags.Nature, Tags.Conjuration]
		self.level = 4
		self.minion_duration = 20

		self.description = ("Whenever you cast a [nature] or [lightning] spell, gain lifespark with duration equal to the spell's level.\n"
						    "Every turn you have active lifespark, summon a lightning bug swarm, which dissapears after 25 turns.\n")

		self.owner_triggers[EventOnSpellCast] = self.on_cast

	def get_extra_examine_tooltips(self):
		return [LightningFlies()]

	def on_cast(self, evt):
		if Tags.Lightning not in evt.spell.tags and Tags.Nature not in evt.spell.tags:
			return
		self.owner.apply_buff(LifesparkBuff(self), evt.spell.level)



class ScalefeatherEgregore(Upgrade):

	def on_init(self):
		self.name = "Scalefeather Egregore"
		self.tags = [Tags.Arcane, Tags.Nature, Tags.Conjuration]
		self.level = 5
		self.serpent = None

	def get_description(self):
		return("At the end of your turn, if you control 10 or more [living] or [arcane] allies and no Egregore, summon a Scalefeather Egregore.\n"
			   "The Egregore can cast your blizzard, nightmare aura, devour mind, void beam, toxin burst, and lumbriogenesis spells if you have them.\n"
			   "The Egregore is unsummoned at the end of your turn if you control fewer than 10 living allies.")

	def get_extra_examine_tooltips(self):
		return [FeatheredSerpent()]

	def has_snake(self):
		return self.serpent and self.serpent.is_alive() and self.serpent.level == self.owner.level

	def is_qualified_ally(self, u):
		return not are_hostile(self.owner, u) and u != self.owner and ((Tags.Living in u.tags) or (Tags.Arcane in u.tags))

	def on_advance(self):
		num_living_allies = len([u for u in self.owner.level.units if self.is_qualified_ally(u)])

		# Less than 10 qualified allies, kill any existing serpent 
		if num_living_allies < 10:
			if self.has_snake():
				self.owner.level.show_effect(self.serpent.x, self.serpent.y, Tags.Poison)
				self.serpent.kill(trigger_death_event=False)
			return

		if not self.has_snake():
			self.summon_snake()

	def summon_snake(self):
		serpent = FeatheredSerpent()
		apply_minion_bonuses(self, serpent)

		allowed_spells = [
			 (NightmareSpell, 30), 
			 (WormOffering, 12), 
			 (BlizzardSpell, 8), 
			 (ToxinBurst, 8),
			 (VoidBeamSpell, 4), 
			 (MindDevour, 2)]

		for spell, cooldown in reversed(allowed_spells):
			if self.owner.get_spell(spell):
				egre_spell = spell()
				egre_spell.statholder = self.owner
				egre_spell.max_charges = 0
				egre_spell.cur_charges = 0
				egre_spell.cool_down = cooldown

				serpent.spells.insert(0, egre_spell)

		if self.summon(serpent, radius=9):
			self.serpent = serpent

class ToadbloodSkill(Upgrade):

	def on_init(self):
		self.name = "Toadblood Transmutation"
		self.tags = [Tags.Nature, Tags.Blood, Tags.Conjuration]
		self.level = 4
		self.global_triggers[EventOnDamaged] = self.on_damage

		self.toadblood = 0

	def get_description(self):
		return ("Whenever a living ally takes damage, gain that much toadblood.\n"
				"At 250 toadblood, summon a towering toadbeast near the most recently damaged ally.\n"
				"Current toadblood: %d\n" % self.toadblood)
		
	def get_extra_examine_tooltips(self):
		return [GiantToad()]

	def on_damage(self, evt):
		if are_hostile(evt.unit, self.owner):
			return

		if Tags.Living not in evt.unit.tags:
			return

		self.toadblood += evt.damage

		while self.toadblood > 250:
			self.toadblood -= 250
			toadbeast = GiantToad()
			apply_minion_bonuses(self, toadbeast)
			self.summon(toadbeast, target=evt.unit)
		

class FarmiliarSkill(Upgrade):

	def on_init(self):
		self.farmiliar = None
		self.counter_max = 5
		self.counter = self.counter_max

		self.owner_triggers[EventOnUnitAdded] = self.on_enter_level

		self.minion_health = 26
		self.minion_damage = 5
		self.minoin_range = 5

	def on_enter_level(self, evt):
		self.counter = self.counter_max

	# Override with farmiliar making method
	def make_farmiliar(self):
		pass

	def summon_farmiliar(self):
		self.farmiliar = self.make_farmiliar()
		apply_minion_bonuses(self, self.farmiliar)
		self.summon(self.farmiliar)

	def has_farmiliar(self):
		return self.farmiliar and self.farmiliar.is_alive() and self.farmiliar.level == self.owner.level

	def on_advance(self):
		if not self.has_farmiliar():
			self.counter -= 1
			if self.counter <= 0:
				self.summon_farmiliar()
				self.counter = self.counter_max


class ChaosChimeraFarmiliar(FarmiliarSkill):

	def __init__(self):
		FarmiliarSkill.__init__(self)

		self.name = "Chaos Familiar"
		self.description = ("Every 5 turns, summon a chaos chimera familiar if you do not currently have one.\n"
							"The familiar has ranged [fire] and [lightning] attacks, and splits into a lightning snake and a fire lion on death.\n"
						    "The familiar can cast your Fireball, Lightning Bolt, Thunder Strike, Pyrostatic Pulse, Immolate, and Chaos Barrage spells on a 3 turn cooldown.\n")
		self.level = 4
		self.tags = [Tags.Chaos, Tags.Fire, Tags.Lightning, Tags.Conjuration]

	def get_extra_examine_tooltips(self):
		return [ChaosChimera()]

	def make_farmiliar(self):
		monster = ChaosChimera()

		allowed_spells = [
			FireballSpell,
			LightningBoltSpell,
			ThunderStrike,
			PyrostaticPulse,
			ImmolateSpell,
			FireballSpell,
			ChaosBarrage
		]

		for spell in reversed(self.owner.spells):
			if type(spell) in allowed_spells:
				chimera_spell = type(spell)()
				chimera_spell.statholder = self.owner
				chimera_spell.max_charges = 0
				chimera_spell.cur_charges = 0
				chimera_spell.cool_down = 3

				monster.spells.insert(0, chimera_spell)

		return monster

class DeathchillChimeraFarmiliar(FarmiliarSkill):

	def __init__(self):
		FarmiliarSkill.__init__(self)

		self.name = "Deathchill Familiar"
		self.description = ("Every 5 turns, summon a deathchill chimera familiar if you do not currently have one.\n"
							"The familiar has ranged [ice] and [dark] attacks, and splits into a death snake and an ice lion on death.\n"
						    "The familiar can cast your Deathbolt, Icicle, Freeze, Iceball, Life Drain, Touch of Death, and Plague of Undeath spells on a 3 turn cooldown.\n")
		self.level = 4
		self.tags = [Tags.Dark, Tags.Ice, Tags.Conjuration]

	def get_extra_examine_tooltips(self):
		return [DeathchillChimera()]

	def make_farmiliar(self):
		monster = DeathchillChimera()

		# Unbeamify the default ranged attacks, farmiliars dont really need this
		monster.spells[0].beam = False
		monster.spells[1].beam = False

		allowed_spells = [
			TouchOfDeath,
			BloodTapSpell,
			DeathBolt,
			Iceball,
			HallowFlesh,
			Icicle,
			Freeze,
		]


		for spell in reversed(self.owner.spells):
			if type(spell) in allowed_spells:
				chimera_spell = type(spell)()
				chimera_spell.statholder = self.owner
				chimera_spell.max_charges = 0
				chimera_spell.cur_charges = 0
				chimera_spell.cool_down = 3

				monster.spells.insert(0, chimera_spell)

		return monster

class DemonicCruelty(Upgrade):

	def on_init(self):
		self.name = "Demonic Cruelty"
		self.tags = [Tags.Dark, Tags.Chaos]
		self.level = 5
		self.description = "Redeal half of all damage dealt to enemy units by [demon] allies as [poison] damage"
		self.global_triggers[EventOnDamaged] = self.on_damage

	def on_damage(self, evt):
		if not are_hostile(self.owner, evt.unit):
			return

		if not Tags.Demon in evt.source.owner.tags:
			return

		dmg = evt.damage // 2
		if dmg:
			evt.unit.deal_damage(dmg, Tags.Poison, self)

class EnchantersBoon(Upgrade):

	def on_init(self):
		self.name = "Enchanters Boon"
		self.tags = [Tags.Enchantment]
		self.level = 7
		self.description = "Whenever you cast a self targeted enchantment spell, a random minion also casts it."
		self.owner_triggers[EventOnSpellCast] = self.on_spell_cast


	def on_spell_cast(self, evt):
		if not Tags.Enchantment in evt.spell.tags:
			return

		allies = [u for u in self.owner.level.units if u != self.owner and not are_hostile(self.owner, u)]
		if not allies:
			return

		newcaster = random.choice(allies)

		spell = type(evt.spell)()
		spell.cur_charges = 1
		spell.caster = newcaster
		spell.owner = newcaster
		spell.statholder = self.owner

		if spell.can_cast(newcaster.x, newcaster.y):
			self.owner.level.act_cast(newcaster, spell, newcaster.x, newcaster.y, pay_costs=False)



class EntropicBattlemagic(Upgrade):

	def on_init(self):
		self.name = "Entropic Battlemagic"
		self.tag_bonuses_pct[Tags.Ice]['damage'] = 50
		self.tag_bonuses_pct[Tags.Fire]['damage'] = 50
		self.tags = [Tags.Fire, Tags.Ice]
		self.level = 4

class ShamanicBattlemagic(Upgrade):

	def on_init(self):
		self.name = "Shamanic Battlemagic"
		self.tag_bonuses_pct[Tags.Dark]['damage'] = 50
		self.tag_bonuses_pct[Tags.Holy]['damage'] = 50
		self.tag_bonuses_pct[Tags.Nature]['damage'] = 50
		self.tags = [Tags.Dark, Tags.Holy, Tags.Nature]
		self.level = 4

class EnergeticBattlemagic(Upgrade):

	def on_init(self):
		self.name = "Energetic Battlemagic"
		self.tag_bonuses_pct[Tags.Arcane]['damage'] = 50
		self.tag_bonuses_pct[Tags.Lightning]['damage'] = 50
		self.level = 4
		self.tags = [Tags.Arcane, Tags.Lightning]

class ConjuredToughness(Upgrade):

	def on_init(self):
		self.name = "Conjured Vitality"
		self.tag_bonuses[Tags.Conjuration]['minion_health'] = 9
		self.tags = [Tags.Conjuration]
		self.level = 4

class ConjuredAggression(Upgrade):

	def on_init(self):
		self.name = "Conjured Aggression"
		self.tag_bonuses_pct[Tags.Conjuration]['minion_damage'] = 50
		self.level = 4
		self.tags = [Tags.Conjuration]

class ChaosSerpents(Upgrade):
	def on_init(self):
		self.name = "Serpents of Chaos"
		self.tags = [Tags.Conjuration, Tags.Chaos, Tags.Dragon]
		self.level = 7
		self.description = "Whenever you deal 6 or more fire, lightning, or physical damage, summon a corresponding snake for 4 turns.  The snakes attacks deal half the dealt damage."
		self.global_triggers[EventOnDamaged] = self.on_damage
		self.minion_duration = 4

	def get_extra_examine_tooltips(self):
		return [Snake(), GoldenSnake(), FireSnake()]

	def on_damage(self, evt):
		if evt.damage < 6:
			return

		if not are_hostile(self.owner, evt.unit):
			return

		if not evt.source:
			return

		if evt.source.owner != self.owner:
			return

		if evt.damage_type not in [Tags.Physical, Tags.Fire, Tags.Lightning]:
			return

		if evt.damage_type == Tags.Lightning:
			snake = GoldenSnake()
		if evt.damage_type == Tags.Fire:
			snake = FireSnake()
		if evt.damage_type == Tags.Physical:
			snake = Snake()

		apply_minion_bonuses(self, snake)

		for s in snake.spells:
			s.damage = evt.damage // 2

		snake.turns_to_death = self.get_stat('minion_duration')
		self.summon(snake, target=evt.unit)

class Multimancer(Upgrade):

	def on_init(self):
		self.name = "Multimancy"
		self.tags = [Tags.Arcane]
		self.level = 5
		self.global_bonuses_pct['num_targets'] = 50

class Armorer(Upgrade):

	def on_init(self):
		self.name = "Armorer"
		self.tags = [Tags.Metallic, Tags.Conjuration]
		self.level = 5
		self.description = "Each turn, a random summoned ally equips a copy of your armor."

	def on_advance(self):

		targets = [u for u in self.owner.level.units if not are_hostile(self.owner, u)]
		targets = [t for t in targets if not t.equipment.get(ITEM_SLOT_ROBE)]

		if not targets:
			return

		if not ITEM_SLOT_ROBE in self.owner.equipment:
			return

		armor = type(self.owner.equipment[ITEM_SLOT_ROBE])()
		unit = random.choice(targets)
		unit.equip(armor)
		self.owner.level.show_effect(unit.x, unit.y, Tags.Conjuration)


class Hemocorruptor(Upgrade):

	def on_init(self):
		self.name = "Hemocorruption"
		self.tags = [Tags.Blood, Tags.Nature, Tags.Dark]
		self.level = 5
		self.global_triggers[EventOnHealed] = self.on_heal
		self.num_targets = 2
		self.radius = 5

	def get_description(self):
		return ("Whenever an allied unit heals, deal that much [poison] damage to up to [{num_targets}:num_targets] enemy units in a [{radius}_tile:radius] burst.").format(**self.fmt_dict())

	def on_heal(self, evt):
		if are_hostile(evt.unit, self.owner):
			return

		self.owner.level.queue_spell(self.send_bolts(evt.unit, -evt.heal))

	def bolt(self, damage, source, target):
		for point in Bolt(self.owner.level, source, target):
			self.owner.level.show_effect(point.x, point.y, Tags.Poison)
			yield True

		target.deal_damage(damage, Tags.Poison, self)
		yield False

	def send_bolts(self, source, damage):

		targets = self.owner.level.get_units_in_ball(source, self.get_stat('radius'))
		targets = [t for t in targets if are_hostile(t, self.owner) and t != source and self.owner.level.can_see(t.x, t.y, source.x, source.y)]
		random.shuffle(targets)

		bolts = [self.bolt(damage, source, t) for t in targets[:self.get_stat('num_targets')]]

		while bolts:
			bolts = [b for b in bolts if next(b)]
			yield

class Tremors(Upgrade):

	def on_init(self):
		self.name = "Earthwrath"
		self.level = 5
		self.tags = [Tags.Nature, Tags.Chaos]
		self.radius = 8
		self.damage = 9
		self.description = ("Whenever you cast a [nature] or [chaos] spell, send out tremors along the ground from the target to nearby enemies.\n"
							"Each tremor deals [9_physical:physical] damage to the target and all units in its path.\n"
							"The base number of targets is equal to the level of the spell.\n"
							"The tremors can target enemies up to [8:radius] tiles away.\n")

		self.owner_triggers[EventOnSpellCast] = self.on_cast

	def on_cast(self, evt):
		if Tags.Chaos not in evt.spell.tags and Tags.Nature not in evt.spell.tags:
			return

		targets = self.owner.level.get_units_in_ball(evt, self.get_stat('radius'))
		random.shuffle(targets)

		num_targets = self.get_stat('num_targets', base=evt.spell.level)
		
		for u in targets:

			if u.x == evt.x and u.y == evt.y:
				continue

			if not are_hostile(self.owner, u):
				continue

			path = self.owner.level.find_path(evt, u, self.owner, pythonize=True, unit_penalty=0)
			if not path:
				continue

			self.owner.level.queue_spell(self.tremor(path))

			num_targets -= 1
			if num_targets <= 0:
				break

	def tremor(self, path):
		for p in path:
			self.owner.level.deal_damage(p.x, p.y, self.get_stat('damage'), Tags.Physical, self)
			yield
		


skill_constructors = [
	ArchEnchanter,
	ArchSorcerer,
	ArchConjurer,
	FireLord,
	IceLord,
	ThunderLord,
	NatureLord,
	DarkLord,
	VoidLord,
	HeavenLord,
	DragonLord,
	OrbLord,
	MetalLord,
	UnblinkingEye,
	Translocator,
	PyrophiliaUpgrade,
	#PyrostaticsBuff,
	MinionRepair,
	SearingHeat,
	ArcaneCombustion,
	SoulHarvest,
	ArcaneAccountant,
	NaturalHealing,
	Teleblink,
	LightningFrenzy,
	ArmorMelter,
	NaturalVigor,
	Hunger,
	LightningWarp,
	HolyThunder,
	FieryJudgement,
	Starfire,
	ShockAndAwe,
	Horror,
	#WhiteFlame,
	#ChaosBuddies,
	ArcaneShield,
	MinionShield,
	GhostfireUpgrade,
	LastWord,
	PrinceOfRuin,
	MarchOfTheRighteous,
	Chastisement,
	ChaosCasting,
	#StoneCollector,
	UnholyAlliance,
	FaeThorns,
	Faestone,
	Houndlord,
	Hypocrisy,
	Cracklevoid,
	Boneguard,
	SpiderSpawning,
	ParalyzingVenom,
	VenomSpit,
	FrozenSouls,
	IceTap,
	Frostbite,
	SteamAnima,
	StormCaller,
	HolyWater,
	Hibernation,
	Crystallographer,
	RadiantCold,
	ShatterShards,
	FrozenFragility,
	DragonScalesSkill,
	CollectedAgony,
	Moonspeaker,
	Voidthorns,
	Necrostatics,
	Purestrike,
	SilkShifter,
	InfernoEngines,
	Megavenom,
	AcidFumes,
	PurpleFlameSorcery,
	SorcererPoet,
	MasterOfSpace,
	MasterOfTime,
	MasterOfMemories,
	SpellSniper,
	Echomancer,
	Disintegrator,
	FaeMalevolence,
	BloodAnima,
	Bloodreaper,
	BloodLord,
	ScentOfBlood,
	Stormbrood,
	#WitchApprentice,
	LightningBugs,
	ScalefeatherEgregore,
	ToadbloodSkill,
	ChaosChimeraFarmiliar,
	DeathchillChimeraFarmiliar,
	DemonicCruelty,
	EnchantersBoon,
	Hordemancer,
	#EnergeticBattlemagic,
	#EntropicBattlemagic,
	#ShamanicBattlemagic,
	ConjuredToughness, 
	ConjuredAggression,
	ChaosSerpents,
	Multimancer,
	Armorer,
	Hemocorruptor,
	Tremors,
]

def make_player_skills():
	all_player_skills = []
	for c in skill_constructors:
		s = c()
		all_player_skills.append(s)
	
	all_player_skills.sort(key=lambda u: (u.level, u.name))
	return all_player_skills


class ResistUpgrade(Upgrade):

	def __init__(self, tag, amount):
		Upgrade.__init__(self)
		self.name = "Resist %s" % tag.name
		self.tag = tag
		self.amount = amount
		self.resists[tag] = amount

	def get_description(self):
		return "Increase resistance to %s damage by %d%%" % (self.tag.name, self.amount)

class MaxHPUpgrade(Upgrade):

	def __init__(self, amount):
		Upgrade.__init__(self)
		self.stack_type = STACK_INTENSITY
		self.name = "Max HP: %d" % amount
		self.amount = amount

	def on_applied(self, owner):
		self.owner.max_hp += self.amount
		self.owner.cur_hp += self.amount

	def on_unapplied(self):
		self.owner.max_hp -= self.amount
		self.owner.cur_hp -= self.amount

	def get_description(self):
		return "Increase Max HP by %d" % self.amount

spell_tags = [Tags.Fire, Tags.Ice, Tags.Dark, Tags.Holy, Tags.Nature, Tags.Lightning, Tags.Arcane]
if __name__ == "__main__":
	done = set()
	for tag1 in spell_tags:
		done.add(tag1)
		for tag2 in spell_tags:
			if tag2 in done:
				continue
			print("--------")
			print("%s + %s:\n" % (tag1.name, tag2.name))
			for s in make_player_skills():
				if tag1 in s.tags and tag2 in s.tags:
					print(s.name)
			print('\n')
