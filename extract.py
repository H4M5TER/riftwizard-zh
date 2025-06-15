import sys
import os
from pathlib import Path

src_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = Path(src_dir)
extract_dir = src_dir / "extracted"

import orjson
from collections import OrderedDict
from icecream import ic

sys.path.append(os.path.abspath("game"))
from RiftWizard2 import (
    tooltip_colors,
    LEARN_SPELL_TARGET,
    LEARN_SKILL_TARGET,
    CHAR_SHEET_TARGET,
    INSTRUCTIONS_TARGET,
    OPTIONS_TARGET,
    STUNNED_TARGET,
    REROLL_PORTALS_TARGET,
    WELCOME_TARGET,
    DEPLOY_TARGET,
    UNPURCHASED_TARGET,
    UNVICTORIED_TARGET,
)

target_names = [
    "LEARN_SPELL_TARGET",
    "LEARN_SKILL_TARGET",
    "CHAR_SHEET_TARGET",
    "INSTRUCTIONS_TARGET",
    "OPTIONS_TARGET",
    "STUNNED_TARGET",
    "REROLL_PORTALS_TARGET",
    "WELCOME_TARGET",
    "DEPLOY_TARGET",
    "UNPURCHASED_TARGET",
    "UNVICTORIED_TARGET",
]


from Spells import make_player_spells
from Upgrades import make_player_skills
from Consumables import all_consumables
from LevelGen import all_monsters
from Equipment import (
    all_items,
    RandomSheild,
    RandomLittleRing,
    ring_tags,
    ring_stats,
    GenericOculusEquip,
    FreeCastStaff,
    SummonOnDeathStaff,
    TagHelm,
    GenericFrenzyMask,
    SeasonCrown,
    MinionCastHat,
    SummonShoes,
    SpellBoots,
    ThornItem,
    DamageToPetsAmulet,
    PrinceOfRuinLike,
    JarOfBossness,
    CursePipe,
    CurseDoll,
    DebuffDamager,
)

equipment_boilerplates = [
    GenericOculusEquip,
    FreeCastStaff,
    SummonOnDeathStaff,
    TagHelm,
    GenericFrenzyMask,
    SeasonCrown,
    MinionCastHat,
    SummonShoes,
    SpellBoots,
    ThornItem,
    DamageToPetsAmulet,
    PrinceOfRuinLike,
    JarOfBossness,
    CursePipe,
    CurseDoll,
    DebuffDamager,
]

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
    dic = OrderedDict()
    for item in items:
        name = item.name
        dic[name] = {
            "name": {
                "en": name,
                "zh": "",
            },
        }
        if type(item) in equipment_boilerplates:
            continue
        description = item.get_description() if hasattr(item, "get_description") else None
        alt = False
        if (
            description is None
            or description.strip() == ""
            or description == "Undescribed"
        ):
            alt = True
        if alt:
            description = getattr(item, "description", None)
        if (
            description
            and not description == "Undescribed"
            and not description.strip() == ""
        ):
            dic[name]["description"] = {
                "en": description,
                "zh": "",
            }
    return dic


spells = make_player_spells()
spell_dict = items2dict(spells)
for spell in spells:
    upgrades = OrderedDict()
    for k, v in spell.upgrades.items():
        upgrades[k] = {
            "amount": v[0],
            "cost": v[1],
        }
        if len(v) >= 3:
            upgrades[k]["name"] = {
                "en": v[2],
                "zh": "",
            }
        if len(v) >= 4:
            upgrades[k]["description"] = {
                "en": v[3],
                "zh": "",
            }
    spell_dict[spell.name]["upgrades"] = upgrades

skills = make_player_skills()
for skill in skills:
    if skill.description:
        skill.description = skill.get_description()
skill_dict = items2dict(skills)

equipments = [e() for e in all_items if e not in [RandomSheild, RandomLittleRing]]
equipment_dict = items2dict(equipments)

monster_dict = items2dict(all_monsters)


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


import text

text_indices = [i for i in dir(text) if not i.startswith("__")]
text_indices = [
    i
    for i in text_indices
    if i
    not in [
        "endings",
        "welcome_text",
        "deploy_text",
    ]
]
text_dict = {}
for i in text_indices:
    text_dict[i] = {
        "en": getattr(text, i, ""),
        "zh": "",
    }

for name in target_names:
    text_dict[name[0:-7]] = {
        "en": globals()[name].description,
        "zh": "",
    }


def names2dict(names):
    dic = OrderedDict()
    for name in names:
        dic[name] = {
            "en": name,
            "zh": "",
        }
    return dic


tasks = [
    ("spells.json", spell_dict),
    ("skills.json", skill_dict),
    ("equipments.json", equipment_dict),
    ("monsters.json", monster_dict),
    ("consumables.json", consumable_dict),
    ("shrines.json", shrine_dict),
    ("text.json", text_dict),
    ("tags.json", names2dict(tooltip_colors.keys())),
    ("ring_tags.json", names2dict([tag[1] for tag in ring_tags])),
    ("ring_stats.json", names2dict([stat[1].capitalize() for stat in ring_stats])),
]

extract_dir.mkdir(parents=True, exist_ok=True)
for filename, data in tasks:
    file_path = extract_dir / filename
    with open(file_path, "wb") as f:
        f.write(orjson.dumps(data, option=orjson.OPT_INDENT_2))
