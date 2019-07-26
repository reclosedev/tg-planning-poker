import asyncio
import os

import logbook
from aiotg import Bot, Chat, CallbackQuery, BotApiError

from ppbot.utils import init_logging
from ppbot.game import GameRegistry, Game

TOKEN = os.environ["PP_BOT_TOKEN"]
DB_PATH = os.environ.get("PP_BOT_DB_PATH", os.path.expanduser("~/.tg_pp_bot.db"))
GREETING = """
Use 
/poker task url or description 
to start game.

Multiline is also supported
/poker line1
line2
Currently there is only one scale: 1, 2, 3, 5, 8, 13, 20, 40, ❔, ☕
"""

bot = Bot(TOKEN)
storage = GameRegistry()
init_logging()
REVEAL_RESTART_COMMANDS = [Game.OP_REVEAL, Game.OP_RESTART, Game.OP_RESTART_NEW, Game.OP_REVEAL_NEW]


@bot.command("/start")
@bot.command("/?help")
async def start_poker(chat: Chat, match):
    await chat.send_text(GREETING)


@bot.command("(?s)/poker\s+(.+)$")
@bot.command("/(poker)$")
async def start_poker(chat: Chat, match):
    vote_id = str(chat.message["message_id"])
    text = match.group(1)
    game = storage.new_game(chat.id, vote_id, chat.sender, text)
    resp = await chat.send_text(**game.get_send_kwargs())
    game.reply_message_id = resp["result"]["message_id"]
    await storage.save_game(game)


@bot.callback(r"vote-click-(.*?)-(.*?)$")
async def vote_click(chat: Chat, cq: CallbackQuery, match):
    logbook.info("{}", cq)
    vote_id = match.group(1)
    point = match.group(2)
    result = "Answer {} accepted".format(point)
    game = await storage.get_game(chat.id, vote_id)
    if not game:
        return await cq.answer(text="No such game")
    if game.revealed:
        return await cq.answer(text="Can't change vote after cards are opened")

    game.add_vote(cq.src["from"], point)
    await storage.save_game(game)
    try:
        await bot.edit_message_text(chat.id, game.reply_message_id, **game.get_send_kwargs())
    except BotApiError:
        logbook.exception("Error when updating markup")

    await cq.answer(text=result)


@bot.callback(r"({})-click-(.*?)$".format("|".join(REVEAL_RESTART_COMMANDS)))
async def reveal_click(chat: Chat, cq: CallbackQuery, match):
    operation = match.group(1)
    vote_id = match.group(2)
    game = await storage.get_game(chat.id, vote_id)
    if not game:
        return await cq.answer(text="No such game")

    if cq.src["from"]["id"] != game.initiator["id"]:
        return await cq.answer(text="{} is available only for initiator".format(operation))

    current_text = game.get_text()
    if operation in (Game.OP_RESTART, Game.OP_RESTART_NEW):
        game.restart()
    else:
        game.revealed = True
        current_text = game.get_text()

    if operation in (Game.OP_RESTART, Game.OP_REVEAL):
        try:
            await bot.edit_message_text(chat.id, game.reply_message_id, **game.get_send_kwargs())
        except BotApiError:
            logbook.exception("Error when updating markup")
    else:
        try:
            await bot.edit_message_text(chat.id, game.reply_message_id, text=current_text)
        except BotApiError:
            logbook.exception("Error when updating markup")
        resp = await chat.send_text(**game.get_send_kwargs())
        game.reply_message_id = resp["result"]["message_id"]

    await storage.save_game(game)
    await cq.answer()


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(storage.init_db(DB_PATH))
    bot.run(reload=False)


if __name__ == '__main__':
    main()
