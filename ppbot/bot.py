import asyncio
import os

import logbook
from aiotg import Bot, Chat, CallbackQuery, BotApiError

from ppbot.utils import init_logging
from ppbot.game import GameRegistry

TOKEN = os.environ["PP_BOT_TOKEN"]
DB_PATH = os.environ.get("PP_BOT_DB_PATH", os.path.expanduser("~/.tg_pp_bot.db"))

bot = Bot(TOKEN)
storage = GameRegistry()
init_logging()


@bot.command("/poker (.+)")
async def get_url(chat: Chat, match):
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


@bot.callback(r"(reveal|restart)-click-(.*?)$")
async def reveal_click(chat: Chat, cq: CallbackQuery, match):
    operation = match.group(1)
    vote_id = match.group(2)
    game = await storage.get_game(chat.id, vote_id)
    if not game:
        return await cq.answer(text="No such game")

    if cq.src["from"]["id"] != game.initiator["id"]:
        return await cq.answer(text="{} is available only for initiator".format(operation))

    if operation == "restart":
        game.restart()
    else:
        game.revealed = True
    await storage.save_game(game)
    try:
        await bot.edit_message_text(chat.id, game.reply_message_id, **game.get_send_kwargs())
    except BotApiError:
        logbook.exception("Error when updating markup")
    await cq.answer()


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(storage.init_db(DB_PATH))
    bot.run(reload=False)


if __name__ == '__main__':
    main()