# Planning Poker Bot for Telegram
This bot allows to play Planning Poker game in group chat.

# Usage
Add https://t.me/planning_poker_with_bot to group chat. Also you can launch your own instance, see `Self-hosted usage` bellow

To start game use:
```
/poker task url or description
``` 

Multiline is also supported:
```
/poker some long description
of task
across multiple lines
```

Only initiator can open cards or restart game at any moment. 

Currently there is only one scale: 1, 2, 3, 5, 8, 13, 20, 40, ❔, ☕

# Self-hosted usage
Bot works with Python 3.6. There is `Dockerfile` and `run.sh` script for convenience

You need to obtain own bot token from https://t.me/BotFather, then run

```
PP_BOT_TOKEN=11111424242:some-token ./run.sh
```
It will recreate image and container `ppbot`. Bot uses sqlite database at host in ~/.ppbot/tg_pp_bot.db
