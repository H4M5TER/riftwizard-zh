import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), 'game'))
import Spells, Upgrades, Consumables, Equipment, LevelGen
from Equipment import RandomWand, RandomSheild, RandomLittleRing
from Level import damage_tags, Knowledges, attr_colors, Tags
from functools import reduce

spells = Spells.make_player_spells()
skills = Upgrades.make_player_skills()
upgrades = [u.name for u in reduce(lambda a, b: a + b, [spell.spell_upgrades for spell in spells])]
deduped = []
s = set()
# 直接把 list 喂进 set 会丢失顺序
for u in upgrades:
    if (u not in s):
        s.add(u)
        deduped.append(u)

s = set()
tags = []
for tag in damage_tags + Knowledges + Tags.elements:
    if (tag.name not in s):
        s.add(tag.name)
        tags.append(tag.name.lower())
for (n,_) in attr_colors.items():
    tags.append(n)
tags = tags + ["petrify", "petrified", "petrifies", "glassify", "glassified", "frozen", "freezes", "freeze", "stunned", "stun", "stuns", "berserk", "poisoned", "blind", "blinded", "quick_cast",]

tasks = [
    ("tags", tags),
    ("spells", [spell.name for spell in spells]),
    ("skills", [skill.name for skill in skills]),
    ('upgrades', deduped),
    ("consumables", [c().name for (c, _) in Consumables.all_consumables]),
    ("equipments", [c().name for c in Equipment.all_items if c not in [RandomWand, RandomSheild, RandomLittleRing]]),
    ("monsters", LevelGen.make_bestiary()),
]

def process(names):
    return "".join([f"\n    \"{n}\": \"{n}\"," for n in names])

# jsons = [f"{type} = {{{"".join([f"\n\t\"{n}\" = \"{n}\"," for n in names])}\n}}\n" for (type, names) in tasks]
jsons = [f"{type} = {{{process(names)}\n}}\n" for (type, names) in tasks]

f = open("extracted.py", "w")
f.write('\n'.join(jsons))
f.close()
