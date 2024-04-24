import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), 'game'))
import Spells, Upgrades, Consumables, Equipment
# from Equipment import Staves, Hats, Robes, Boots, Amulets
# from functools import reduce

tasks = [
    ("spells", Spells.all_player_spell_constructors),
    ("skills", Upgrades.skill_constructors),
    ("equipments", [c for c in Equipment.all_items if c != Equipment.RandomWand]),
    # ("equipments", reduce(lambda a, b: a + b, [Staves, Hats, Robes, Boots, Amulets])),
    ("consumables", [c for (c, _) in Consumables.all_consumables]),
]

for (name, constructors) in tasks:
    instances = [c() for c in constructors]
    names = [i.name for i in instances]
    f = open(f"{name}.txt", "w")
    f.write('\n'.join(f"\"{n}\": \"\"," for n in names))
    f.close()
