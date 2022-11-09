import dict_monsters_full
import dict_monsters_words

def getLocale(name):
  locale = dict_monsters_full.names.get(name, name)
  if locale == name:
    for (k, v) in dict_monsters_words.dict.items():
      locale = locale.replace(k, v)
    # locale.replace(' ', '')
  return locale
