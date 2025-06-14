import sys
import os
from pathlib import Path

src_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = Path(src_dir)
extract_dir = src_dir / "extracted"

import orjson
from icecream import ic

sys.path.append(os.path.abspath("game"))
from RiftWizard2 import tooltip_colors
from Spells import make_player_spells
from Upgrades import make_player_skills
from Consumables import all_consumables
from LevelGen import all_monster_names
from Equipment import (
    all_items,
    RandomSheild,
    RandomLittleRing,
    ring_tags,
    ring_stats,
)
from Shrines import (
    chest_opts,
    reward_table,
    roll_chest,
    ring_chest,
    random,
)


class MockObject:
    pass


def items2dict(items):
    dic = {}
    for item in items:
        name = item.name
        dic[name] = {
            "name": {
                "en": name,
                "zh": "",
            },
        }
        description = getattr(item, "description", None)
        if not description and hasattr(item, "get_description"):
            description = item.get_description()
        if description:
            dic[name]["description"] = {
                "en": description,
                "zh": "",
            }
    return dic


spells = make_player_spells()
spell_dict = items2dict(spells)
for spell in spells:
    upgrades = {}
    for k, v in spell.upgrades.items():
        upgrades[k] = {
            "val": v[0],
            "cost": v[1],
        }
        if len(v) >= 3:
            upgrades[k]["name"] = v[2]
            if len(v) >= 4:
                upgrades[k]["description"] = v[3]
    spell_dict[spell.name]["upgrades"] = upgrades

skills = make_player_skills()
skill_dict = items2dict(skills)

equipments = [e() for e in all_items if e not in [RandomSheild, RandomLittleRing]]
equipment_dict = items2dict(equipments)


fake_player = MockObject()
fake_player.game = MockObject()
fake_player.game.all_player_spells = []
fake_player.game.all_player_skills = []

chest_opts = [c[0] for c in chest_opts]
# chest_opts = [c for c in chest_opts if c not in [ring_chest]]
chest_opts = filter(lambda c: c not in [ring_chest], chest_opts)
chests = [c(1, random) for c in chest_opts]
shrine_opts = [s[0] for s in reward_table]
shrine_opts = filter(lambda s: s not in [roll_chest], shrine_opts)
shrines = [s(1, random, fake_player) for s in shrine_opts]
shrines = chests + shrines
shrine_dict = items2dict(shrines)

consumables = [c() for (c, _) in all_consumables]
consumable_dict = items2dict(consumables)

tags = {
    "tags": tooltip_colors.keys(),
    "ring_tags": [tag[1] for tag in ring_tags],
    "ring_stats": [stat[1].capitalize() for stat in ring_stats],
}
dic = {}
for key in tags.keys():
    dic[key] = {}
    for name in tags[key]:
        dic[key][name] = ""

tasks = [
    ("spells.json", spell_dict),
    ("skills.json", skill_dict),
    ("equipments.json", equipment_dict),
    ("consumables.json", consumable_dict),
    ("shrines.json", shrine_dict),
    ("dictionary.json", dic),
]

extract_dir.mkdir(parents=True, exist_ok=True)
for filename, data in tasks:
    file_path = extract_dir / filename
    with open(file_path, "wb") as f:
        f.write(orjson.dumps(data, option=orjson.OPT_INDENT_2))
