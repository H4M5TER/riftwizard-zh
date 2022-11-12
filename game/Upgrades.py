from Spells import *
from Monsters import *
import text
import loc

class GlobalBonus(Upgrade):
	def __init__(self, attribute, amount, level, tags, name=None):
		Upgrade.__init__(self)
		self.tags = tags
		self.global_bonuses[attribute] = amount
		self.name = name if name else "Increased %s" % format_attr(attribute)
		self.description = "提升所有法术 %d %s%s" % (amount, loc.attrc_dic(attribute, ''), format_attr(attribute))
		self.level = level
		self.attribute = attribute
		self.amount = amount


class TagBonus(Upgrade):
	def __init__(self, tag, attribute, amount, level, name=None):
		Upgrade.__init__(self)
		self.tag_bonuses[tag][attribute] = amount
		self.name = name if name else "%s %s" % (tag.name, format_attr(attribute))
		self.description = "提升 [%s] 法术 %d %s%s" % (tag.name, amount, loc.attrc_dic(attribute, ''), format_attr(attribute))
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
		self.tag_bonuses[Tags.Translocation]['range'] = 3

		self.level = 7

class ArchEnchanter(Upgrade):

	def on_init(self):
		self.name = "Arch Enchanter"
		self.tags = [Tags.Enchantment]

		self.tag_bonuses[Tags.Enchantment]['max_charges'] = 2
		self.tag_bonuses[Tags.Enchantment]['duration'] = 3
		self.tag_bonuses[Tags.Enchantment]['damage'] = 5

		self.level = 7

class ArchSorcerer(Upgrade):

	def on_init(self):
		self.name = "Arch Sorcerer"
		self.tags = [Tags.Sorcery]

		self.tag_bonuses[Tags.Sorcery]['max_charges'] = 2
		self.tag_bonuses[Tags.Sorcery]['damage'] = 7
		self.tag_bonuses[Tags.Sorcery]['range'] = 2

		self.level = 7

class ArchConjurer(Upgrade):

	def on_init(self):
		self.name = "Arch Conjurer"
		self.tags = [Tags.Conjuration]

		self.tag_bonuses[Tags.Conjuration]['max_charges'] = 2
		self.tag_bonuses[Tags.Conjuration]['minion_damage'] = 3
		self.tag_bonuses[Tags.Conjuration]['minion_health'] = 7
		self.tag_bonuses[Tags.Conjuration]['minion_range'] = 1
		self.tag_bonuses[Tags.Conjuration]['minion_duration'] = 1

		self.level = 7
		
class FireLord(Upgrade):

	def on_init(self):
		self.name = "Fire Lord"
		self.tags = [Tags.Fire]

		self.tag_bonuses[Tags.Fire]['max_charges'] = 1
		self.tag_bonuses[Tags.Fire]['damage'] = 12
		self.tag_bonuses[Tags.Fire]['radius'] = 1

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
		self.tag_bonuses[Tags.Lightning]['damage'] = 8
		self.resists[Tags.Lightning] = 50
		self.tag_bonuses[Tags.Lightning]['cascade_range'] = 2
		self.tag_bonuses[Tags.Lightning]['num_targets'] = 1

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
		self.tag_bonuses[Tags.Dark]['damage'] = 6
		
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
		self.tag_bonuses[Tags.Holy]['minion_duration'] = 7

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
		return "每当召唤的小兵目睹敌人受到 [fire] 伤害，该小兵治疗伤害一半生命。"

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
		return "每当你以 [lightning] 法术造成伤害时，获得等量的电焰充能 10 回合。\n每当敌人受到 [fire] 伤害时，消耗等量的电焰充能，对受伤单位视线内至多充能数个单位造成充能数的 [lightning] 伤害。"

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
		return ("每当一个敌方单位死亡时，你的每个 [dark] 法术各有 10% 几率获得一点充能。\n"
				"若该单位死于 [dark] 伤害，几率变为三倍。")

class ArcaneCombustion(Upgrade):

	def on_init(self):
		self.tags = [Tags.Arcane]
		self.level = 4
		self.name = "Arcane Combustion"
		self.global_triggers[EventOnDeath] = self.on_death
		self.damage = 12

	def on_death(self, evt):
		if evt.damage_event and evt.damage_event.damage_type == Tags.Arcane:
			self.owner.level.queue_spell(self.explosion(evt.unit))

	def explosion(self, evt):
		for p in self.owner.level.get_points_in_ball(evt.x, evt.y, 1, diag=True):
			self.owner.level.deal_damage(p.x, p.y, self.get_stat('damage'), Tags.Arcane, self)
			if self.owner.level.tiles[p.x][p.y].is_wall():
				self.owner.level.make_floor(p.x, p.y)
		yield

	def get_description(self):
		return ("每当一个单位死于 [arcane] 伤害，该单位爆炸，对 [3_格:radius] 的方形内造成 [%d_点奥术:arcane] 伤害，熔化受影响地块上的墙。") % self.get_stat('damage')

class SearingHeat(Upgrade):

	def on_init(self):
		self.tags = [Tags.Fire]
		self.level = 5
		self.name = "Searing Heat"
		self.owner_triggers[EventOnSpellCast] = self.on_cast
		self.damage = 3

	def on_cast(self, evt):
		if Tags.Fire in evt.spell.tags:
			for u in list(self.owner.level.units):
				if not self.owner.level.are_hostile(u, self.owner):
					continue
				if not self.owner.level.can_see(evt.x, evt.y, u.x, u.y):
					continue

				u.deal_damage(self.damage, Tags.Fire, self)

	def get_description(self):
		return "每当你施放 [fire] 法术时，对目标视线内的所有敌人造成 [3_点火焰:fire] 伤害。\n此伤害值固定，无法被修正。".format(**self.fmt_dict())

class DevourerOfNations(Upgrade):

	def on_init(self):
		self.tags = [Tags.Dark]
		self.level = 3
		self.name = "Devourer of Nations"
		self.global_triggers[EventOnDeath] = self.on_death
		self.heal = 25

	def get_description(self):
		return "每当你摧毁一个巢穴时，获得 %d 点生命。" % self.heal

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
		return "每当你消灭一个头目时，随机一个 4 级法术获得一点充能。"

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
		return "每回合治疗你的所有小兵 [2_点生命:heal]。"

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
		self.level = 5
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

	def get_description(self):
		return ("当你连续施放三个 [arcane] 法术时，随机一个 [translocation] 法术获得一点充能，召唤 [2_个仙灵:num_summons]。\n"
				"仙灵有 [{minion_health}_点生命:minion_health]、[{shields}_点护盾:shields] 和 [75_点奥术:arcane] 抗性，可飞行，可被动扑闪。\n"
			    "仙灵可治疗友军 [{heal}_点生命:heal]，射程为 [{minion_range}_格:minion_range]。\n"
			    "仙灵的攻击造成 [{minion_damage}_点奥术:arcane] 伤害，射程为 [{minion_range}_格:minion_range]。\n"
			    "仙灵在 [{minion_duration}_回合:minion_duration] 后消失。\n").format(**self.fmt_dict())

	def on_advance(self):
		if not self.cast_last:
			self.casts = 0
		self.cast_last = False

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
				else:
					print('no candis')

				for i in range(2):
					p = self.owner.level.get_summon_point(self.owner.x, self.owner.y, sort_dist=False, flying=True, radius_limit=4)
					if not p:
						continue

					unit = Unit()
					unit.sprite.char = 'f'
					unit.sprite.color = Color(252, 141, 249)
					unit.name = "Good Faery"
					unit.description = "任性的生物，乐于慰藉巫师"
					unit.max_hp = self.minion_health
					unit.shields = self.get_stat('shields')
					unit.buffs.append(TeleportyBuff(chance=.7))
					unit.spells.append(HealAlly(heal=self.get_stat('heal'), range=self.get_stat('minion_range') + 2))
					unit.spells.append(SimpleRangedAttack(damage=self.get_stat('minion_damage'), range=self.get_stat('minion_range'), damage_type=Tags.Arcane))
					unit.turns_to_death = self.get_stat('minion_duration')
					unit.team = self.owner.team
					unit.tags = [Tags.Nature, Tags.Arcane, Tags.Living]
					self.owner.level.add_obj(unit, *p)

class ArcaneCredit(Buff):

	def on_init(self):
		self.name = "Arcane Credit"
		self.owner_triggers[EventOnSpellCast] = self.on_cast
		self.color = Tags.Arcane.color
		self.description = "下个非 [arcane] 法术的充能会得到返还。"

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
		return "每当你施放最后一个充能的 [arcane] 法术时，你的下个非 [arcane] 法术可免费施放，持续 1 回合。"

	def on_spell_cast(self, evt):
		if Tags.Arcane in evt.spell.tags and evt.spell.cur_charges == 0:
			self.owner.apply_buff(ArcaneCredit(), 2)

class NaturalHealing(Upgrade):

	def on_init(self):
		self.tags = [Tags.Nature]
		self.level = 5
		self.name = "Natural Healing"
		self.owner_triggers[EventOnSpellCast] = self.on_spell_cast

	def get_description(self):
		return "每当你施放 [nature] 法术时，治疗 [5_点生命:heal]。"

	def on_spell_cast(self, evt):
		if Tags.Nature in evt.spell.tags:
			self.owner.deal_damage(-5, Tags.Heal, self)

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
		self.level = 5
		self.name = "Lightning Frenzy"
		self.owner_triggers[EventOnSpellCast] = self.on_spell_cast
		self.bonus = 4
		self.buff_duration = 6

	def get_description(self):
		return "每当你施放 [lightning] 法术时，你的 [lightning] 法术和被动获得 [%d_点伤害:damage]，持续 [%d_回合:duration]。" % (self.bonus, self.buff_duration)

	def on_spell_cast(self, evt):
		if Tags.Lightning in evt.spell.tags:
			self.owner.apply_buff(LightningFrenzyStack(self.bonus), duration=self.buff_duration)

class MeltedArmor(Buff):

	def on_init(self):
		self.resists[Tags.Physical] = -10
		self.resists[Tags.Fire] = -10
		self.name = "Armor Melted"
		self.buff_type = BUFF_TYPE_CURSE
		self.stack_type = STACK_INTENSITY
		self.asset = ['status', 'melted_armor']
		self.color = Tags.Fire.color

class ArmorMelter(Upgrade):

	def on_init(self):
		self.tags = [Tags.Fire, Tags.Metallic]
		self.level = 5
		self.name = "Melting Armor"
		self.global_triggers[EventOnDamaged] = self.on_damage

	def get_description(self):
		return "每当敌人受到 [fire] 伤害，它失去 [10_点物理:physical] 和 [10_点火焰:fire] 抗性。"

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
		return "你召唤的单位获得 [25_点物理:physical] 抗性、[25_点闪电:lightning] 抗性、[25_点寒冰:ice] 和 [25_点火焰:fire] 抗性。"

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

	def get_description(self):
		return ("你召唤的 [undead] 单位获得饥饿。\n"
			  	"饥饿对 [{minion_range}_格:range] 内的一个目标造成 [{minion_damage}_点黑暗:dark] 伤害。"
			  	"治疗施法者等量的生命，[3_回合:cooldown] 冷却。\n".format(**self.fmt_dict()))

	def should_grant(self, unit):
		return not are_hostile(unit, self.owner) and Tags.Undead in unit.tags

	def on_advance(self):
		for unit in self.owner.level.units:
			hunger = [s for s in unit.spells if isinstance(s, HungerLifeLeechSpell)]
			if hunger and not self.should_grant(unit):
				unit.remove_spell(hunger[0])
			elif not hunger and self.should_grant(unit):
				spell = HungerLifeLeechSpell()
				spell.damage = self.get_stat('minion_damage')
				spell.range = self.get_stat('minion_range')
				#weird cause im trying to insert at 0
				spell.caster = unit
				unit.spells.insert(0, spell)

class LightningWarp(Upgrade):

	def on_init(self):
		self.owner_triggers[EventOnSpellCast] = self.on_spell_cast
		self.damage = 12
		self.name = "Lightning Warp"
		self.level = 6
		self.tags = [Tags.Lightning, Tags.Translocation]

	def get_description(self):
		return "每当你施放 [lightning] 法术时，目标 [3_格:radius] 内的所有敌方单位随机传送到 [4_到_8_格:range] 远的地块，受到 [{damage}_点闪电:lightning] 伤害。".format(**self.fmt_dict())

	def on_spell_cast(self, evt):

		if Tags.Lightning not in evt.spell.tags:
			return

		self.owner.level.queue_spell(self.do_teleports(evt))

	def do_teleports(self, evt):
		for unit in self.owner.level.get_units_in_ball(evt, 3):
			if not self.owner.level.are_hostile(unit, self.owner):
				continue

			points = self.owner.level.get_points_in_ball(evt.x, evt.y, 8)
			points = [p for p in points if distance(p, self.owner) >= 4 and self.owner.level.can_stand(p.x, p.y, unit)]
			if points:
				point = random.choice(points)
				self.owner.level.act_move(unit, point.x, point.y, teleport=True)
				unit.deal_damage(self.get_stat('damage'), Tags.Lightning, self)
				yield

class Starfire(Upgrade):

	def on_init(self):
		self.name = "Starfire"
		self.level = 6
		self.tags = [Tags.Fire, Tags.Arcane]
		self.conversions[Tags.Fire][Tags.Arcane] = .5

	def get_description(self):
		return "你和你小兵造成 [fire] 伤害时还造成一半的 [arcane] 伤害。"


class ShockAndAwe(Upgrade):

	def on_init(self):
		self.name = "Shock Value"
		self.global_triggers[EventOnDeath] = self.on_death
		self.tags = [Tags.Lightning]
		self.level = 7
		self.duration = 5

	def get_description(self):
		return ("每当敌人死于 [lightning] 伤害时，该敌人视线内随机一个敌人 [berserk] [5_回合:duration]。\n"
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
		self.description = "每当敌人死于 [dark] 伤害时，该敌人视线内至多 [3:num_targets] 个敌人被 [stunned] [5_回合:duration]。"
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
		return "每当你施放半径大于 0 的 [fire] 法术时，对目标点造成 [%d_点火焰:fire] 伤害。" % self.get_stat('damage')

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
		return ("每当敌人在同一回合受到 [fire]、[lightning] 和 [physical] 伤害时，在该敌人旁召唤钢铁小鬼、电光小鬼和火焰小鬼个一个。\n"
				"小鬼有 [{minion_health}_点生命:minion_health]，可飞行。\n"
				"小鬼的远程攻击造成 [{minion_damage}_点伤害:minion_damage]，射程为 [{minion_range}_格:minion_range]。\n"
				"小鬼各持续 [{minion_duration}_回合:minion_duration]。\n").format(**self.fmt_dict())

	def on_damaged(self, evt):
		if not self.owner.level.are_hostile(evt.unit, self.owner):
			return
		if evt.damage_type not in [Tags.Fire, Tags.Lightning, Tags.Physical]:
			return
		if evt.unit in self.procs_this_turn:
			return

		self.damage_this_turn.add((evt.damage_type, evt.unit))
		needed_tuples = {(Tags.Fire, evt.unit), (Tags.Lightning, evt.unit), (Tags.Physical, evt.unit)}
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
		self.description = "每当你施放 [arcane] 法术时，若你没有护盾，获得 [1_点护盾:shields]."
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
		self.description = "你召唤的 [arcane] 小兵获得 [3_点护盾:shields]，其他小兵获得 [1_点护盾:shields]。"
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
		self.level = 4

		self.fire_victims = set()
		self.dark_victims = set()
		self.blackfire_victims = set()

		self.minion_health = 4
		self.minion_damage = 7
		self.minion_range = 5
		self.minion_duration = 10

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

	def do_summon(self, x, y):
		p = self.owner.level.get_summon_point(x, y, flying=True)
		if not p:
			return

		ghost = Ghost()
		ghost.max_hp = self.get_stat('minion_health')
		ghost.sprite.color = Tags.Fire.color
		ghost.spells[0] = SimpleRangedAttack(damage=self.get_stat('minion_damage'), range=self.get_stat('minion_range'), damage_type=Tags.Fire)
		ghost.name = "Burning Ghost"
		ghost.asset_name = "fire_ghost"
		ghost.resists[Tags.Fire] = 100
		ghost.team = TEAM_PLAYER
		ghost.turns_to_death = self.get_stat('minion_duration')
		self.owner.level.add_obj(ghost, p.x, p.y)
		yield

	def get_description(self):
		return ("每当敌人在同一回合受到 [dark] 和 [fire] 伤害时，在该敌人旁召唤一个燃烧的幽灵。\n"
				"燃烧的幽灵有 [100_点火焰:fire] 抗性和 [100_点黑暗:dark] 抗性，可被动扑闪。\n"
				"燃烧的幽灵的远程攻击造成 [{minion_damage}_点火焰:fire] 伤害，射程为 [{minion_range}_格:minion_range]。\n"
				"燃烧的幽灵在 [{minion_duration}_回合:minion_duration] 后消失。").format(**self.fmt_dict())

class LastWord(Upgrade):

	def on_init(self):
		self.name = "Last Word"

		self.description = "每当你通过一关时，你的每个 [word] 法术获得一点充能。"
		self.tags = [Tags.Word]
		self.level = 5

		self.global_triggers[EventOnDeath] = self.on_death

	def on_death(self, evt):

		if not are_hostile(evt.unit, self.owner):
			return
		if all(not are_hostile(u, self.owner) or u == evt.unit for u in self.owner.level.units):
			words = [s for s in self.owner.spells if Tags.Word in s.tags and s.cur_charges < s.get_stat('max_charges')]
			for word in words:
				word.cur_charges += 1

class PrinceOfRuin(Upgrade):

	def on_init(self):
		self.name = "Prince of Ruin"
		self.global_triggers[EventOnDeath] = self.on_death
		self.fire_triggered = False
		self.light_triggered = False
		self.phys_triggered = False

		self.level = 5
		self.damage = 13
		self.radius = 5

		self.tags = [Tags.Chaos]

	def get_description(self):
		return "每当敌人死于 [fire]、[physical] 或 [lightning] 伤害时，随机对目标视线 [{radius}_格:radius] 内的一个敌人造成该类型的 [{damage}_点伤害:damage]。".format(**self.fmt_dict())

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
			target.deal_damage(self.damage, evt.damage_event.damage_type, self)
		yield

class MarchOfTheRighteous(Upgrade):

	def on_init(self):
		self.name = "Righteous March"
		self.description = "每当敌人死于 [holy] 伤害时，目睹的友军若无护盾则获得 [1_点护盾:shields]。"
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
		self.level = 7
		self.tags = [Tags.Fire, Tags.Holy]
		self.conversions[Tags.Fire][Tags.Holy] = .5

	def get_description(self):
		return "你和你小兵造成 [fire] 伤害时还造成一半的 [holy] 伤害。"


class HolyThunder(Upgrade):

	def on_init(self):
		self.name = "Holy Thunder"
		self.level = 7
		self.tags = [Tags.Lightning, Tags.Holy]
		self.conversions[Tags.Lightning][Tags.Holy] = .5

	def get_description(self):
		return "你和你小兵造成 [lightning] 伤害时还造成一半的 [holy] 伤害。"

class Chastisement(Upgrade):

	def on_init(self):
		self.name = "Chastisement"
		self.description = "每当敌人受到 [holy] 伤害时，它有 50% 几率被 [stunned] [1_回合:duration]。"
		self.tags = [Tags.Holy]
		self.level = 4
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
		self.description = "每当你施放 [chaos] 法术时，你有 25% 几率随机获得其他 [chaos] 法术的一点充能。"
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
		self.description = ("每当你召唤 [undead] 或 [demon] 单位时，若你控制 [holy] 单位，该召唤的单位获得 [7_点伤害:damage]。\n"
							"每当你召唤 [holy] 单位时，若你控制 [undead] 或 [demon] 单位，该召唤的单位获得 [7_点伤害:damage]。\n")

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
		self.minion_duration = 6

		self.owner_triggers[EventOnSpellCast] = self.on_spell_cast

	def get_description(self):
		return ("每当你施放 [arcane] 或 [nature] 法术时，在目标旁召唤 [2:num_summons] 个仙灵荆棘。\n"
		    	"仙灵荆棘有 [{minion_health}_点生命:minion_health]，不可移动。\n"
		    	"仙灵荆棘的近战攻击造成 [{minion_damage}_点物理:physical]。\n"
		    	"仙灵荆棘在 [{minion_duration}_回合:minion_duration] 后消失。").format(**self.fmt_dict())

	def on_spell_cast(self, evt):
		if Tags.Arcane in evt.spell.tags or Tags.Nature in evt.spell.tags:
			self.owner.level.queue_spell(self.do_summons(evt))

	def do_summons(self, evt):
		for i in range(2):
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
		self.description = "若你施放的下个法术是 %d 级或更低的 %s 法术，其为免费。" % (self.level, loc.dic.get(self.tag.name, self.tag.name))
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
		self.description = ("每当你施放 [dark] 法术时，若你施放的下个法术是更低等级的 [holy] 法术，后者的充能得到返还。\n"
							"每当你施放 [holy] 法术时，若你施放的下个法术是更低等级的 [dark] 法术，后者的充能得到返还。")

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
		self.description = "每当主人施放 [nature] 法术时，仙灵石治疗 [10_点生命:heal]\n\n每当主人施放 [arcane] 法术时，仙灵石传送到目标旁，获得 [1_点护盾:shields]。"
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
		self.minion_health = 120

		self.description = ("每关开始时有一个友方的仙灵石。仙灵石是坚固而固定不动的近战单位。"
						    "\n\n每当你施放 [arcane] 法术时，仙灵石传送到目标旁，获得 [1_点护盾:shields]。"
						    "\n\n每当你施放 [nature] 法术时，仙灵石治疗 [10_点生命:heal]。")
		self.global_triggers[EventOnUnitAdded] = self.on_unit_added

	def get_description(self):
		return ("每当你进入新关卡时，在附近召唤一个仙灵石。\n"
				"仙灵石有 [{minion_health}_点生命:minion_health]，固定不动。\n"
				"每当你施放 [nature] 法术时，仙灵石治疗 [10_点生命:heal]。\n"
				"每当你施放 [arcane] 法术时，仙灵石传送到目标旁，获得 [1_点护盾:shields]。").format(**self.fmt_dict())

	def on_unit_added(self, evt):
		if evt.unit != self.owner:
			return

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

		self.summon(faestone, sort_dist=False)

class Houndlord(Upgrade):

	def on_init(self):
		self.name = "Houndlord"
		self.level = 5
		self.tags = [Tags.Fire, Tags.Conjuration]
		self.description = "每关开始时有被友方的地狱猎犬包围。"
		self.minion_damage = 6
		self.minion_health = 19
		self.minion_range = 4

		self.owner_triggers[EventOnUnitAdded] = self.on_unit_added

	def get_description(self):
		return ("每关开始时有被友方的地狱猎犬包围。\n"
				"地狱猎犬有 [{minion_health}_点生命:minion_health]、[100_点火焰:fire] 抗性、[50_点黑暗:dark] 抗性和 [-50_点寒冰:ice] 抗性。\n"
				"地狱猎犬的火热身躯对近战攻击者造成 [4_点火焰:fire] 伤害。\n"
				"地狱猎犬的近战攻击造成 [{minion_damage}_点火焰:fire] 伤害。\n"
				"地狱猎犬的跳跃攻击造成 [{minion_damage}_点火焰:fire]，射程为 [{minion_range}_格:minion_range]。\n").format(**self.fmt_dict())

	def on_unit_added(self, evt):

		if evt.unit != self.owner:
			return

		for p in self.owner.level.get_adjacent_points(self.owner, check_unit=False):
			existing = self.owner.level.tiles[p.x][p.y].unit

			if existing:
				continue

			unit = HellHound()
			
			for s in unit.spells:
				s.damage = self.get_stat('minion_damage')

			unit.spells[1].range = self.get_stat('minion_range')
			unit.max_hp = self.get_stat('minion_health')
			
			self.summon(unit, p)

class Boneguard(Upgrade):

	def on_init(self):
		self.name = "Bone Guard"
		self.level = 6
		self.tags = [Tags.Dark, Tags.Conjuration]
		self.description = "每关开始时有 4 个友方的白骨卫士陪伴。"

		self.owner_triggers[EventOnUnitAdded] = self.on_unit_added

		example = BoneKnight()
		self.minion_health = example.max_hp
		self.minion_damage = example.spells[0].damage
		self.num_summons = 4

	def get_description(self):
		return ("每关开始时有 4 个白骨卫士陪伴。\n"
				"白骨卫士有 [{minion_health}_点生命:minion_health]、[1_点护盾:shields]、[100_点黑暗:dark] 抗性和 [50_点寒冰:ice] 抗性。\n"
				"白骨卫士的近战攻击造成 [{minion_damage}_点黑暗:dark] 伤害，吸取 2 点生命上限。\n").format(**self.fmt_dict())

	def on_unit_added(self, evt):
		if evt.unit != self.owner:
			return

		for i in range(self.get_stat('num_summons')):
			p = self.owner.level.get_summon_point(self.owner.x, self.owner.y)
			unit = BoneKnight()
			
			for s in unit.spells:
				s.damage = self.get_stat('minion_damage')

			unit.max_hp = self.get_stat('minion_health')
			
			self.summon(unit, p)


class Cracklevoid(Upgrade):
	def on_init(self):
		self.name = "Cracklevoid"
		self.level = 6
		self.tags = [Tags.Lightning, Tags.Arcane]

		self.damage = 7
		self.num_targets = 2
		self.radius = 6

		self.global_triggers[EventOnDamaged] = self.on_damage

	def get_description(self):
		return ("每当敌人受到 [arcane] 伤害时，对 [{radius}_格:radius] 半径内至多 [{num_targets}:num_targets] 个敌方单位造成等量的 [lightning] 伤害。").format(**self.fmt_dict())

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
		self.description = "每当敌人死于 [poison] 伤害时，在附近召唤一个友方的蜘蛛。"
		self.global_triggers[EventOnDeath] = self.on_death

		spider_default = GiantSpider()
		self.minion_health = spider_default.max_hp
		self.minion_damage = spider_default.spells[0].damage
		self.duration = spider_default.spells[0].buff_duration

	def get_description(self):
		return ("每当敌人死于 [poison] 伤害时，在附近召唤一个友方的巨型蜘蛛。\n"
				"巨型蜘蛛有 [{minion_health}_点生命:minion_health]，可织蛛网。\n"
			 	"巨型蜘蛛的近战攻击造成 [{minion_damage}_点物理:physical] 伤害，施加 [5_回合:duration] 的 [poison]。\n"
			 	"蛛网 [stun] 步入的非 [spider] 单位 [1_回合:duration]。\n"
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
		self.description = "每当敌人受到 [poison] 伤害时，它有 25% 几率被 [stunned] [1_回合:duration]。"
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
		self.description = "施加 [poison] 10 回合。"
		self.name = "Venom Spit"

class VenomSpit(Upgrade):

	def on_init(self):
		self.name = "Venom Spit"
		self.tags = [Tags.Nature]
		self.level = 4
		self.minion_damage = 4
		self.minion_range = 6


	def get_description(self):
		return ("你召唤的 [living] 和 [nature] 单位可进行毒液喷吐。\n"
				"毒液喷吐是远程攻击，造成 [{minion_damage}_点毒性:poison] 伤害，施加 [poison] [10_回合:duration]。\n"
				"毒液喷吐射程为 [{minion_range}_格:range]，[4_回合:cooldown] 冷却。").format(**self.fmt_dict())

	def should_grant(self, unit):
		if unit.is_player_controlled:
			return False
		return not are_hostile(unit, self.owner) and (Tags.Nature in unit.tags or Tags.Living in unit.tags)

	def on_advance(self):
		for unit in self.owner.level.units:
			spit = [s for s in unit.spells if isinstance(s, VenomSpitSpell)]
			if spit and not self.should_grant(unit):
				unit.remove_spell(spit[0])
			elif not spit and self.should_grant(unit):
				spell = VenomSpitSpell()
				spell.damage = self.get_stat('minion_damage')
				spell.range = self.get_stat('minion_range')
				#weird cause im trying to insert at 0
				spell.caster = unit
				unit.spells.append(spell)

class FrozenSouls(Upgrade):

	def on_init(self):
		self.name = "Icy Vengeance"
		self.tags = [Tags.Ice, Tags.Dark]
		self.level = 6
		self.description = "每当你的小兵死亡时，[5_格:radius] 半径内随机至多 [3:num_targets] 个敌人受到 [ice] 伤害，数量为死亡小兵生命上限的一半。"
		self.global_triggers[EventOnDeath] = self.on_death
		self.radius = 5

	def on_death(self, evt):
		if are_hostile(evt.unit, self.owner):
			return
		self.owner.level.queue_spell(self.do_damage(evt))

	def do_damage(self, evt):
		units = self.owner.level.get_units_in_ball(evt.unit, self.get_stat('radius'))
		units = [u for u in units if are_hostile(self.owner, u)]
		random.shuffle(units)
		for unit in units[:3]:
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
		return "每当你以被 [frozen] 的单位为目标施放 [arcane] 法术时，对视线内所有其他被 [frozen] 的单位复制该法术并对其施放。\n移除所有受影响单位的 [frozen]。".format(**self.fmt_dict())

	def on_spell_cast(self, evt):
		if self.copying:
			return False

		unit = self.owner.level.get_unit_at(evt.x, evt.y)
		if not unit:
			return

		b = unit.get_buff(FrozenBuff)
		if not b:
			return
		unit.remove_buff(b)

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
		self.level = 6
		self.tags = [Tags.Ice, Tags.Dark]
		self.damage = 7

	def get_description(self):
		return "每回合所有被 [frozen] 的单位受到 [{damage}_点黑暗:dark] 伤害。".format(**self.fmt_dict())

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
		return ("每当单位被 [fire] 伤害解冻时，在附近召唤 [3:num_summons] 个蒸汽元素。\n"
				"蒸汽元素有 [{minion_health}_点生命:minion_health]、[100_点物理:physical] 抗性、[100_点寒冰:ice] 抗性和 [100_点火焰:fire] 抗性。\n"
				"蒸汽元素的远程攻击造成 [{minion_damage}_点火焰:fire] 伤害，射程为 [{minion_range}_格:minion_range]。\n"
				"蒸汽元素在 [{minion_duration}_回合:minion_duration] 后消失。").format(**self.fmt_dict())

	def on_unfrozen(self, evt):
		if evt.dtype != Tags.Fire:
			return

		for i in range(self.get_stat('num_summons')):
			elemental = Unit()
			elemental.name = "Steam Elemental"
			elemental.max_hp = self.get_stat('minion_health')
			elemental.resists[Tags.Physical] = 100
			elemental.resists[Tags.Fire] = 100
			elemental.resists[Tags.Ice] = 100
			elemental.tags = [Tags.Elemental, Tags.Fire]
			elemental.turns_to_death = self.get_stat('minion_duration')
			elemental.spells.append(SimpleRangedAttack(damage=self.get_stat('minion_damage'), damage_type=Tags.Fire, range=self.get_stat('minion_range')))

			self.summon(elemental, target=evt.unit)

class StormCaller(Upgrade):

	def on_init(self):
		self.global_triggers[EventOnDamaged] = self.on_damage
		self.name = "Storm Caller"
		self.level = 5
		self.tags = [Tags.Lightning, Tags.Ice, Tags.Nature]
		self.duration = 5

	def get_description(self):
		return ("每当对敌方单位造成 [ice] 或 [lightning] 伤害时在附近生成暴风雪或风暴云。\n"
				"风暴持续 [{duration}_回合:duration]。").format(**self.fmt_dict())

	def on_damage(self, evt):
		if not are_hostile(self.owner, evt.unit):
			return

		if evt.damage_type not in [Tags.Ice, Tags.Lightning]:
			return

		cloud = random.choice([BlizzardCloud(self.owner), StormCloud(self.owner)])
		cloud.damage += self.get_stat('damage') # Apply damage bonuses

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
		self.description = "每当被 [frozen] 的敌人受到 [holy] 伤害时，视线内的你和所有友军获得 [1_点护盾:shields]，上限为 [5:shields]。"
		self.level = 4
		self.global_triggers[EventOnDamaged] = self.on_damage
		self.tags = [Tags.Holy, Tags.Ice]

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

class HibernationBuff(Buff):

	def on_init(self):
		self.buff_type = BUFF_TYPE_PASSIVE
		self.resists[Tags.Ice] = 75
		self.owner_triggers[EventOnDamaged] = self.on_damaged

	def on_pre_advance(self):
		if self.owner.has_buff(FrozenBuff):
			self.owner.deal_damage(-15, Tags.Heal, self)

	def on_damaged(self, evt):
		if evt.damage_type == Tags.Ice:
			if not self.owner.has_buff(FrozenBuff):
				self.owner.apply_buff(FrozenBuff(), 3)

class Hibernation(Upgrade):

	def on_init(self):
		self.name = "Hibernation"
		self.description = ("你的 [living] 小兵获得 [75_点寒冰:ice] 抗性。\n"
							"你的 [living] 小兵受到 [ice] 伤害时 [freeze] [3_回合:duration]。\n"
							"你的 [living] 小兵被 [frozen] 时每回合治疗 [15_点生命:heal]。\n")
		self.global_triggers[EventOnUnitAdded] = self.on_unit_add
		self.tags = [Tags.Ice, Tags.Nature]
		self.level = 4

	def on_unit_add(self, evt):
		if are_hostile(self.owner, evt.unit):
			return
		if self.owner == evt.unit:
			return
		if Tags.Living not in evt.unit.tags:
			return
		evt.unit.apply_buff(HibernationBuff())

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
		self.description = "每有一个被 [frozen] 或 [glassified] 的敌人，你的 [sorcery] 法术获得 [2_点伤害:damage]。"
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
		return "每当你施放 [ice] 法术时，[freeze] 法术目标最近且未冻结的敌人 [{duration}_回合:duration]。".format(**self.fmt_dict())

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
		self.damage = 9

	def get_description(self):
		return "每当单位解冻或被 [frozen] 的单位被消灭时，[6_格:radius] 半径内至多 [3_个敌人:num_targets] 受到 [{damage}_点寒冰:ice] 伤害和 [{damage}_点物理:physical] 伤害。".format(**self.fmt_dict())

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
		self.level = 5
		self.tags = [Tags.Ice]
		self.description = "每当敌人被 [frozen] 时，解冻前降低该敌人的 [physical] 和 [ice] 抗性 100 点"
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
		return "每当友方的 [dragon] 使用吐息武器时，所有你的召唤单位获得吐息武器类型的 100 点抗性 [{duration}_回合:duration]。".format(**self.fmt_dict())

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
		self.description = "每回合对最近的敌人造成 [dark] 伤害，数量为对所有伤害造成的 [poison] 伤害的两倍。"

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
		self.description = "每当敌人受到 [arcane] 伤害时，该敌人视线内的所有 [holy] 小兵再对其造成一半的 [holy] 伤害。"

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
		return "每当你、你的 [arcane] 或 [undead] 友军受到敌人的伤害时，对伤害来源造成 [{damage}_点奥术:arcane] 伤害。".format(**self.fmt_dict())

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
		return "你每控制一个 [undead] 友军便 +1 [lightning] 伤害。"

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
		return "每当你或友军对敌人造成 [physical] 伤害时，若伤害被护盾抵挡，再对其造成 50% 的 [arcane] 伤害和 50% 的 [holy] 伤害。"

	def on_damage(self, evt):
		if evt.damage_type != Tags.Physical:
			return
		if not evt.source or not evt.source.owner:
			return
		if evt.source.owner.shields < 1:
			return
		if are_hostile(self.owner, evt.source.owner):
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
		self.level = 5
		self.global_triggers[EventOnSpellCast] = self.on_cast

	def on_applied(self, owner):
		self.owner.tags.append(Tags.Spider)

	def on_unapplied(self):
		self.owner.tags.remove(Tags.Spider)

	def get_description(self):
		return ("你是蜘蛛。\n"
				"每回合随机在一个无单位和墙的相邻地块上生成一个蛛网。\n"
				"每当你以蛛网为目标施放 [translocation] 法术时，返还一点该法术的充能，消耗该蛛网。")

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
		self.damage = 2
		self.duration = 10

	def get_description(self):
		return ("每当你施放 [fire] 法术时，你的所有 [metallic] 友军获得 [2_点伤害:damage] 的 [fire] 光环，半径为法术等级，持续 [{duration}_回合:duration]。\n"
			    "此伤害值固定，无法用神龛、被动或增益提升。\n").format(**self.fmt_dict())

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

			aura = DamageAuraBuff(damage=self.damage, damage_type=Tags.Fire, radius=evt.spell.level)
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
		return ("[Poisoned] 的敌人每回合额外受到 [{damage}:poison] 点 [poison] 伤害。").format(**self.fmt_dict())

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
		self.description = "每回合随机酸化一个未被酸化的敌人。\n被酸化的敌人失去 100 点 [poison] 抗性。"
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
			available_targets.remove(target)

class PurpleFlameSorcery(Upgrade):

	def on_init(self):
		self.name = "Voidflame Lantern"
		self.tags = [Tags.Fire, Tags.Arcane]
		
		self.level = 4
		self.owner_triggers[EventOnSpellCast] = self.on_spell_cast

		self.damage = 6

	def get_description(self):
		return ("每当你施放 [fire] 或 [arcane] 法术时，获得星光充能，持续回合为法术等级。\n"
			    "星光充能每回合对视线内随机一个敌人造成 [{damage}_点火焰:fire] 伤害，对另一个造成 [{damage}_点奥术:arcane] 伤害。").format(**self.fmt_dict())

	def on_spell_cast(self, evt):
		if Tags.Fire in evt.spell.tags or Tags.Arcane in evt.spell.tags:
			self.owner.apply_buff(Starcharge(self), evt.spell.level)


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
	#NaturalHealing,
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
	WhiteFlame,
	ChaosBuddies,
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
	PurpleFlameSorcery
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
		return "提升 %d%% %s抗性" % (self.amount, loc.dic.get(self.tag.name, self.tag.name))

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
		return "提升 %d 生命上限" % self.amount


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
			for s in all_player_skills:
				if tag1 in s.tags and tag2 in s.tags:
					print(s.name)
			print('\n')
