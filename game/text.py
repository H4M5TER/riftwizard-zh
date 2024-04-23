intro_text = """Welcome back Wizard, to the ruins of the universe.

Aeons passed while you slumbered.
You have sleptwalk across many worlds.

The universe, once ordered and beautiful, lies in chaos and ruin.

And you as well:
You were a great wizard once, but your magic and your memories have faded.

Your purpose you remember.  Revenge.
The Dark Wizard Mordred is nearby.

Perhaps he is what woke you?

Regain your power, and slay Mordred.
"""


victory_text = """VICTORY

Mordred is defeated.

Order and justice will soon return to the universe.

Exhausted, you fade from conciousness back into sleep.

Perhaps this time, you may dream.
"""

welcome_text = """WELCOME
Welcome to Rift Wizard.
Press H for a full help screen and details on all the game's controls.
Mouseover something for a detailed description of what it does.
Press S to purchase a spell."""

deploy_text = """You have stepped halfway through the rift.  
You may choose any point in the next world to materialize at (Enter, left click), or you may step out of this rift and return to the previous world (ESC, right click).
Beware, for once you enter, there will be no way to return."""

how_to_play = """HOW TO PLAY

Finish 24 levels and kill Mordred to win the game.
Destroy all enemies to finish a level.

After completing a level, walk onto a rift to peek inside.
Teleport through the rift by clicking any empty tile, or abort the teleport using escape.  
After you teleport into a level, you cannot leave until it is finished.  Teleport with care.

Spells and passive skills can all purchased with skillpoints (SP) from the Character Sheet.
Spells can be individually upgraded from the Character sheet using SP, and at shrines found in the world.

Spells have limited charges.  Casting a spell costs one charge from that spell.
Regain charges by drinking mana potions, which can be found on the ground in some levels.

CONTROLS:

H: Help (This Screen)      C: Character Sheet      S: Learn Spells     K: Learn Skills

Left click: Move, or cast currently selected spell at the cursor's position.
Right click: Cancel current spell or exit current menu

Numpad:
7 8 9
4   6  -> Move one space in the corresponding direction.
1 2 3

Numpad 5: Wait one turn (Or continue channeling if channeling a spell)

        1 2 3 4 5 6 7 8 9 0: Cast/Select spell 1-10
Shift + 1 2 3 4 5 6 7 8 9 0: Cast/Select spell 11-20)
Alt   + 1 2 3 4 5 6 7 8 9 0: Use/Select item 1-10

Numpad/mouse: move the targeting reticle.
Esc: Cancel spell targeting
Enter: cast current spell or enter portal at current location

Advanced Controls:

l: Show line of sight           t: Show threatened tiles
Tab:  Next target               m:   Show message log

v: look (target a square to look, tab target to look at interesting places)
w: walk (target a square to walk there, tab target to walk to interesting places)
a: autopickup all loot (after clearing level)
Shift + up/down arrow on character sheet: change selected spell hotkey
i: interact with current tile (enter portal, open shop)
pgup/pgdown: view descriptions of spell upgrades (when viewing spell description)
"""

advanced_tips = """STATUS EFFECTS

Stunned: Cannot act.
Poisoned: Take 1 poison damage per turn and cannot heal.
Petrified: Cannot act, gain 100 ice and lightning resist, gain 75 physical and fire resist.
Glassified: Cannot act, gain 100 ice and lightning resist, 75 fire resist, lose 100 physical resist.
Frozen: Cannot act.  Ends upon taking fire or physical damage.  Cannot affect units with 100 ice resist.
Berserked: Become hostile to all other units.  Will attack and be attacked by allies.
Blind: All spell ranges reduced to 1.
Channeling: Will continue to cast previous spell with same target if no other action is taken.
Shield (SH): If a unit with SH would be dealt damage, it loses 1 SH instead.
"""

endings = ["Utopia", "Nirvana", "Ragnarok"]

frozen_desc = "[Frozen] units cannot act. Frozen units unfreeze upon taking [fire] or [physical] damage."
petrify_desc = ("[Petrified] units cannot act.\n"
				"[Petrified] units gain [100_ice:ice] resist.\n"
				"[Petrified] units gain [100_lightning:lightning] resist.\n"
				"[Petrified] units gain [75_physical:physical] resist.\n"
				"[Petrified] units gain [75_fire:fire] resist.")
glassify_desc = ("[Glassified] units cannot act.\n"
				"[Glassified] units gain [-100_physical:physical] resist.\n"
				"[Glassified] units gain [100_ice:ice] resist.\n"
				"[Glassified] units gain [100_lightning:lightning] resist.\n"
				"[Glassified] units gain [75_fire:fire] resist.")
stun_desc = "[Stunned] units cannot act."
berserk_desc = "[Berserk] units are hostile to all other units, they will attack and be attacked by their allies."
poison_desc = "[Poisoned] units take 1 [poison] damage each turn."
blind_desc = "[Blind] units have all their spell ranges reduced to 1."