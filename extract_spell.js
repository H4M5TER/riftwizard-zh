const fs = require('fs')

try {
  const content = fs.readFileSync('game/Spells.py', 'utf-8')
  // const regex = /class\s+(.+)\(.+\):(\s*\r?\n)+(\t+.+(\r?\n)+)+/g
  const regex = /(class\s+(.+)\(.*Spell.*\)|class\s+(.+Spell)\(.+\)):(\s*\r?\n)+(\t+.+(\r?\n)+)+/g
  let spells = []
  let names = []
  for (let match of content.matchAll(regex)) {
    let name = match[0].match(/self\.name\s*=\s*"(.+)"/)?.at(1)
    if (!name)
      continue
    let description = match[0].match(/self\.description\s*=\s*"(.+)"/)?.at(1)
    if (!description) {
      description = match[0].match(/\tdef\s+get_description\(.+\):\r?\n\t\treturn\s+(".+"|\(".+"(\s+".+")*\))/)?.at(1)
      if (description) {
        if (/^\(/.test(description))
          description = description.slice(1, -1)
        description = description.replace(/\s*("[^"]+"|'[^']+')/g, '$1').replace(/"([^"]+)"/g, '$1').replace(/'([^']+)'/g, '$1')
      } else {
        description = ''
      }
    }
    let upgrades = {}
    for (let upgrade of
      Array.from(match[0].matchAll(/self.upgrades\['.+'\]\s*=\s*\((.+)\)/g))
        .map(v => Array.from(v[1].matchAll(/("[^"]+"|'[^']+')/g)).map(v => v[1].slice(1, -1)))) {
      if (!upgrade.length)
        continue
      upgrades[upgrade[0]] = upgrade.slice(1)
    }
    names.push(name)
    spells.push({
      name: name,
      description: description,
      upgrades: upgrades
    })
  }
  fs.writeFileSync(`generated/Spells.json`, JSON.stringify(spells, null, 2))
  fs.writeFileSync(`game/dict_spells.py`,
    `names = {\n${names.map(v => `  "${v}": "${v}",`).join('\n')}\n}\n`, 'utf-8')
} catch (error) {
  console.error(error)
}