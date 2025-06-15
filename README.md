<div id=badges align=center>
  <img align="center" alt="HvZ" width="10%" src="https://raw.githubusercontent.com/jenks2709/Tagger/585c974dd6106db566cb0292027ec7cdb163ba30/files/hvz_logo.png" />
</div>

# Tagger
Repository containing the code for the Tagger bot used by [RHUL HvZ Society](https://www.su.rhul.ac.uk/societies/a-z/hvz/)

## What is HvZ?
Humans vs Zombies is a 24/7 survival tag game that is played across days or weeks. 

Zombies hunt humans and can convert them by tagging them with a "full palm touch", Humans are able to temporarily stun them by throwing socks or firing nerf darts at them. 

Most of our games are closed to non-students but we do host annual "Invitational" games that are open to the public, if you are interested in learning more, please join [our discord server](http://tinyurl.com/discordhvz)

## Running the bot
Create a file called `token.txt` containing [your bots token](https://www.madpenguin.org/how-to-get-your-discord-bot-token/)

Run `bot.py`

The bot should show as "online" in discord

## Architecture:

The as stated above `bot.py` is the base script, but most of the codebase is stored other in python scripts held in `./cogs/`. These contain the code for specific commands and are split into several scripts based on the commands purpose and which discord users have access to them.

For example `human_commands.py` contains gameplay commands specific to the human team and requires the user to have the `human` role or an administrative role such as `moderator`. 

An SQLite3 database is used to store game data and other relevant information, such as player's discord IDs. 

Assets such as images or braincode wordlists are stored in the `./files` directory. 

## Dependencies:
* python
* discord.py
* [matplotlib](https://matplotlib.org/)
* [networkx](https://networkx.org/documentation/stable/index.html)
* pydot
* SQLite3




## 

![Map of Campus](./files/campus_map.png)
