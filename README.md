# PhoneGet userbot

kinda out of WIP but abandoned, code is super messy and most features are not usable without proper knowledge
also avito macro is not done and upgrade statistics is broken

## Getting started

### Dependencies
* python interpreter
* telethon library

### Launching
* put your api id and hash into corresponding files
* ```python main.py```

## Help
there are three types of commands: substitutes, handler and macros

substitutes are just shortcuts for bot commands and they start with `!`; you can edit them in `settings.json`

handlers react to a certain message from a bot

macros are doing something with a bot and usually have parameters such as `r`(rarity), `q`(quantity), `p`(price), `n`(name), etc.; currently available macros:
 * `.buy -r -q -n -p` - buy `q` phones of `r` rartity, `n` name and `p` price
 * `.upg -r -q -n -p` - same as `buy` but upgrade
 * `.sell -r -q -n -p` - same as `but` but sell
 * `.cti` - calculates total income of a farm(reply to the message with farm)
 * `.tdi -r -q -n -p` - same as `buy` but add to the opened trade(reply to the message with trade)
 * `.who -n -p -q` - find a phone in the database by name and price, `q` is upper limit of phones displayed
 * `.gps` - update phones database
 * `.dtc -q` - duplicate schedule tcard message `q` times with delay specified in `settings.json`
 * `.dam` - unchedules all tcard messages
 * `.ctl -n -v -r -q -s` - bot control; `-r1` to reload; `-q1` to shutdown; `-s1` to sleep(WIP); `-n"param_name" -v` to edit parameter; `-n"show"` to show all settings
 * `.scm -n -s` - schedule any message `-n` with delay `-s`
 * `.pup -n` - same as .who but displays profit after upgrade
* `.tac` - terminate all conversations

parameters are iterative and most are unnecessary, for `-q` specify `-1` for infinity 

Examples:
 * `.buy -r0,2 -q3,-1 -n"One",""` - buy 3 phones of rarity 0 that contain `One` in their title, and max number of phones of rarity 2 with any title
 * `.upg -r1,3 -q5` - upgrade 5 phones of rarities 1 and 3
 * `.ctl -n"tcard_reload" -v3600` - set tcard delay to 1 hour
 * `.ctl -n"whitelist","username1","username2" -v0,1` - remove `username1` from whitelist and add `username2`
