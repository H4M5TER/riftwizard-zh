const fs = require('fs')

const files = [
  'CommonContent',
  'Consumables',
  'Monsters',
  'RareMonsters',
  'Shrines',
  'Spells',
  'Upgrades',
  'Variants'
]

try {
  for (let file of files) {
    let regex = /\.name\s*=\s*['"]/
    const content = fs.readFileSync(`game/${file}.py`, 'utf-8').trim()
    const lines = content.split(/\r?\n/)
    const matched = lines.filter(line => regex.test(line)).map(line => line.trim())
    const result = matched.sort().join('\n')
    fs.writeFileSync(`generated/${file}.py`, result, 'utf-8')
    regex = false
    switch (file) {
      case 'Shrines':
      case 'Spells':
      case 'Upgrades':
        regex = /^self\.name\s*=\s*("[^"]+"|'[^']+')$/
        break
      case 'Consumables':
        regex = /^item\.name\s*=\s*("[^"]+"|'[^']+')$/
      default:
    }
    if (!regex)
      continue
    let names = matched.filter(line => regex.test(line))
      .map(line => line.replace(regex, '$1').slice(1, -1))
      .map(line => `  "${line}": "${line}",`)
    fs.writeFileSync(`game/dict_${file.toLowerCase()}.py`,
      `names = {\n${names.join('\n')}\n}\n`, 'utf-8')
  }
} catch (error) {
  console.error(error)
}