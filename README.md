# Rift Wizard 汉化工程

## (从头) 准备环境

1. 安装 `uv` <https://docs.astral.sh/uv/getting-started/>
2. `uv sync`
3. 把游戏盖到 `game` 目录上，不要覆盖 `.py` 文件
4. 在 `game/rl_data/` 下放置 `sarasa-mono-sc-bold.ttf`

## 减小体积 (可选)

1. 将 `game/rl_data/music/` 下的 `wav` 格式音乐转化为 `ogg` 格式
2. 将 `game/RiftWizard2.py@play_music` 里读取音乐格式改为 `ogg`
3. 删掉原本的 `wav` 文件
4. 删掉 `game/rl_data/old_music/` 文件夹

## 升级游戏版本

## 注意

- 技能和物品等文本会写进存档, 尽量清空存档后再测试。
