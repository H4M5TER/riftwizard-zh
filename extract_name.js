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
    const result = matched.join('\n')
    fs.writeFileSync(`generated/${file}.py`, result,'utf-8')
  }
} catch (error) {
  console.error(error)
}