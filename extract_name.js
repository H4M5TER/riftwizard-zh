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
  const regex = /\.name\s*=\s*['"]/
  for (let file of files) {
    const content = fs.readFileSync(`game/${file}.py`, 'utf-8').trim()
    const lines = content.split(/\r?\n/)
    const matched = lines.filter(line => regex.test(line)).map(line => line.trim())
    const result = matched.sort().join('\n')
    fs.writeFileSync(`generated/${file}.py`, result, 'utf-8')
    switch (file) {
      case 'Shrines':
      case 'Spells':
      case 'Upgrades':
      case 'Consumables':
        let names = matched.filter(line => /^self\.name\s*=\s*("[^"]+"|'[^']+')$/.test(line))
          .map(line => line.replace(/self\.name\s*=\s*("[^"]+"|'[^']+')$/, '$1').slice(1, -1))
          .map(line => `  "${line}": "${line}",`)
        fs.writeFileSync(`game/dict_${file.toLowerCase()}.py`,
          `names = {\n${names.join('\n')}\n}\n`, 'utf-8')
      default:
    }
  }
} catch (error) {
  console.error(error)
}