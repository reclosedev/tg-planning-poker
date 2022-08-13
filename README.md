# Planning Poker Bot for Telegram

This bot allows to play Planning Poker game in group chat.

# Usage

Add https://t.me/devpoker_bot to group chat.

To start **Planning Poker** use `/poker` command.
Add any description after the command to provide context. 

Example:
```
/poker Redesign Planning Poker Bot keyboard layout
``` 

Example with multiline description:
```
/poker Redesign planning poker bot keyboard layout
https://issue\.tracker/TASK-123
```

Only initiator can open cards or restart game at any moment. 

Currently, there is only one scale of numbers:
```
0, 0.5, 1, 2, 3, 4
5, 6, 7, 8, 9, 10
12, 18, 24, 30
```

Additional votes:
* ❓— Still unsure how to estimate
* ∞ — Task is too large, impossible to estimate
* ☕ — Let's take a break

# Self-hosted usage

Bot works on Python 3.6.

Run `run.sh` script with bot api token to start the Docker container.

You need to obtain own bot token from https://t.me/BotFather, then run:

```shell
PP_BOT_TOKEN=11111424242:some-token ./run.sh
```

It will recreate image and container `ppbot`. Bot uses sqlite database at host in `~/.ppbot/tg_pp_bot.db`.
