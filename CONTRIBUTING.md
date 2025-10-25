<!-- omit from toc -->
# Setting up the development environment 

- [Dev tools](#dev-tools)
- [Setup](#setup)
- [Project structure](#project-structure)

## Dev tools

Links to downloads/info you may want/need

- https://discord.com/developers/applications
- https://git-scm.com/downloads
- https://cli.github.com/
- https://www.python.org/downloads/
- https://docs.python.org/3/library/sqlite3.html
- https://code.visualstudio.com/download
- https://discord.com/developers/docs/
- https://discordpy.readthedocs.io/en/latest/api.html

Note you may need to complete an MFA step in the browser before you can generate a bot token. 

## Setup

You may want to fork it first

`git clone https://github.com/danielzting/clearurls-discord-bot.git`

or 

`gh repo clone danielzting/clearurls-discord-bot`

Having installed `python`, create a virtual environment to manage dependencies 

`python -m venv .`

Activate the environment with `scripts\activate` (Windows) or `source bin\activate` (Linux).

Then install dependencies with `pip install -r requirements.txt`

## Project structure 

The [unalix](https://github.com/AmanoTeam/Unalix/tree/master/unalix) library is archived. Its source is included in this project in the `unalix` folder.

The `data.min.json` file is sourced from [https://docs.clearurls.xyz/latest/specs/rules/](https://docs.clearurls.xyz/latest/specs/rules/) because the version provided by Unalix was outdated. Pull requests to update this file and keep it in sync with the official ClearURLs ruleset are welcome!

The bot itself is in `main.py`.

The bot uses a sqlite table to persist server settings. Functions to initialize and interact with the database are in the `database` folder.

`guildsettings.py` is for Discord server specific settings. Currently we use a small lookup table to store server specific flags. So far we are not using an ORM layer and there is no handling for migrations. Be careful as you work to add additional settings.

`util.py` has a function for getting a sqlite db connection with some flags that enable better support for timestamps.
