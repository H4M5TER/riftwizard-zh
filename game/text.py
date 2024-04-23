intro_text = """Welcome back once again Wizard, to the ruins of the universe.

Aeons passed while you slumbered.
You have sleptwalk across many worlds.

Weep for Avalon, o lonely old Wizard!
Love and beauty transmuted to chaos and ruin.

Your beloved Avalon, and you, her loyal servant, as well.

Once a great Wizard,
Your memories and magics have faded.

Now a thirst for revenge awakens you.
The Dark Wizard Mordred is nearby.

Regain your power.
Slay Mordred.
Vengeance for Avalon.
"""

unused_new_intro_text = """Arise Wizard,

Aeons passed while you slumbered.
You have sleptwalk across many worlds.

Weep for Avalon!
The dread serpent Jormangandr has laid waste to your beautiful empire.

But the phase of the moon turns,
And the Serpent returns to the material plane.

You will awaken one last time.
Gather again your lost memories, and put the beasts of chaos to rest.
"""


old_victory_text = """VICTORY

Mordred is defeated.

Order and justice will soon return to the universe.

Exhausted, you fade from conciousness back into sleep.

Perhaps this time, you may dream.
"""

victory_text = """The Dark Wizard is slain.

His beasts have been broken and made tame.

The beauty of avalon will be built again.

Your soul is permitted to sleep and dream once more.

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

Finish 20 levels and slay your nemesis to win the game.
Destroy all enemies to finish a level.

After completing a level, walk onto a rift to peek inside.
Teleport through the rift by clicking any empty tile, or abort the teleport using escape.  
After you teleport into a level, you cannot leave until it is finished.  Teleport with care.

Spells and passive skills can all purchased with skillpoints (SP) from the Character Sheet.
Spells can be individually upgraded from the Character sheet using SP.

Spells have limited charges.  Casting a spell costs one charge from that spell.
Regain charges by drinking a mana potion or completing the level.

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
poison_desc = "[Poisoned] units take 1 [poison] damage each turn and cannot heal."
blind_desc = "[Blind] units have all their spell ranges reduced to 1."