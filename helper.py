import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), 'game'))
import Spells, Upgrades, Consumables, Equipment, Level
from functools import reduce

tasks = [
    ("spells", [c().name for c in Spells.all_player_spell_constructors]),
    ("skills", [c().name for c in Upgrades.skill_constructors]),
    ('upgrades', [u.name for u in reduce(lambda a, b: a + b, [c().spell_upgrades for c in Spells.all_player_spell_constructors])]),
    ("consumables", [c().name for (c, _) in Consumables.all_consumables]),
    ("equipments", [c().name for c in Equipment.all_items if c not in [Equipment.RandomWand, Equipment.RandomSheild, Equipment.RandomLittleRing]]),
]

def process(names):
    return "".join([f"\n    \"{n}\": \"{n}\"," for n in names])

# jsons = [f"{type} = {{{"".join([f"\n\t\"{n}\" = \"{n}\"," for n in names])}\n}}\n" for (type, names) in tasks]
jsons = [f"{type} = {{{process(names)}\n}}\n" for (type, names) in tasks]

f = open("extracted.py", "w")
f.write('\n'.join(jsons))
f.close()
