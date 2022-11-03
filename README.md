# Rift Wizard 汉化工程

## 起步

1. 导入 `.py` 以外的游戏文件
2. 将 `steamworks.zip` 解压到 `steamworks` 文件夹
3. 安装 Python 3.8.2
4. `pip install -r requirements.txt`
5. `python RiftWizard.py`

## 注意

- 技能和物品等文本会写进存档，尽量清空存档后再测试。

## TODO

- [怪物 0/5365](Monsters.py) 和 [稀有怪物 0/3079](RareMonsters.py) 的名称、技能和属性的翻译。
- [法术 1200/9054](Spells.py) 和 [能力 0/2360](Upgrades.py) 说明、升级说明的翻译。
- 其他文件的翻译
  - [祭祠 0/2109](Shrines.py)
  - [关卡 0/3498](Level.py)
  - [NPCs 0/25](NPCs.py)
- 最后再润色字体、大小和界面等。

## 考虑

- 拆分字典，这样`Giant Bear`根据单位或法术拆分成`巨熊`和`召唤巨熊`。
- 统一格式风格，特别是是否带空格和如何套色。

## DONE

- 改写`draw_wrapped_string`函数，更好地适应中文换行。
- 增加中文标点切割，但换行仍以标点和空格为截断依据，长文本加空格即可。
- 调用`draw_string`前查表替换。
- 调整一些界面函数和参数。
- 法术、能力、物品名称全翻译。
- 物品描述的翻译。

## 说明

- 游戏代码和资源来自7月版本`Rift.Wizard.Build.8752580`。
- `steamworks`库来自网络。
- 后续劳动来自群友。
- 本项目仅供学习，绝不能商用。
