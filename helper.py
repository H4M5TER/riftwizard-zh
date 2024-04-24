import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), 'game'))
import Spells, Upgrades, Consumables, Equipment, Monsters, RareMonsters
from Equipment import RandomWand, RandomSheild, RandomLittleRing
from functools import reduce

spells = Spells.make_player_spells()
skills = Upgrades.make_player_skills()

tasks = [
    ("spells", [spell.name for spell in spells]),
    ("skills", [skill.name for skill in skills]),
    ('upgrades', sorted([u.name for u in reduce(lambda a, b: a + b, [spell.spell_upgrades for spell in spells])])),
    ("consumables", [c().name for (c, _) in Consumables.all_consumables]),
    ("equipments", [c().name for c in Equipment.all_items if c not in [RandomWand, RandomSheild, RandomLittleRing]]),
    ("monsters", [c().name for (c, _) in Monsters.spawn_options]),
    ("rare_monsters", [c[0]().name for c in RareMonsters.rare_monsters])
]

def process(names):
    return "".join([f"\n    \"{n}\": \"{n}\"," for n in names])

# jsons = [f"{type} = {{{"".join([f"\n\t\"{n}\" = \"{n}\"," for n in names])}\n}}\n" for (type, names) in tasks]
jsons = [f"{type} = {{{process(names)}\n}}\n" for (type, names) in tasks]

f = open("extracted.py", "w")
f.write('\n'.join(jsons))
f.close()
