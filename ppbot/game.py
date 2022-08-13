import collections
import json

import aiosqlite

ALL_MARKS = "♥♦♠♣"

POINTS_LAYOUT = [
    ["0", "0.5", "1", "2", "3", "4"],
    ["5", "6", "7", "8", "9", "10"],
    ["12", "18", "24", "30"],
    ["❓", "∞", "☕"],
]


class Vote:
    def __init__(self):
        self.point = ""
        self.version = -1

    def set(self, point):
        self.point = point
        self.version += 1

    @property
    def masked(self):
        return ALL_MARKS[self.version % len(ALL_MARKS)]

    def to_dict(self):
        return {
            "point": self.point,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, dct):
        res = cls()
        res.point = dct["point"]
        res.version = dct["version"]
        return res


class Game:
    OP_RESTART = "restart"
    OP_RESTART_NEW = "restart-new"
    OP_REVEAL = "reveal"
    OP_REVEAL_NEW = "reveal-new"

    def __init__(self, chat_id, vote_id, initiator, text):
        self.chat_id = chat_id
        self.vote_id = vote_id
        self.initiator = initiator
        self.text = text
        self.reply_message_id = 0
        self.votes = collections.defaultdict(Vote)
        self.revealed = False

    def add_vote(self, initiator, point):
        self.votes[self._initiator_str(initiator)].set(point)

    def get_text(self):
        result = "{} for:\n{}\nInitiator: {}".format(
            "Vote" if not self.revealed else "Results",
            self.text, self._initiator_str(self.initiator)
        )
        if self.votes:
            votes_str = "\n".join(
                "{:3s} {}".format(
                    vote.point if self.revealed else vote.masked, user_id
                )
                for user_id, vote in sorted(self.votes.items())
            )
            result += "\n\nCurrent votes:\n{}".format(votes_str)
        return result

    def get_send_kwargs(self):
        return {"text": self.get_text(), "reply_markup": json.dumps(self.get_markup())}

    def get_point_button(self, point):
        return {
            "type": "InlineKeyboardButton",
            "text": point,
            "callback_data": "vote-click-{}-{}".format(self.vote_id, point),
        }

    def get_reset_buttons(self):
        return [
            {
                "type": "InlineKeyboardButton",
                "text": "Restart",
                "callback_data": "{}-click-{}".format(self.OP_RESTART, self.vote_id),
            },
            {
                "type": "InlineKeyboardButton",
                "text": "Restart 🆕",
                "callback_data": "{}-click-{}".format(self.OP_RESTART_NEW, self.vote_id),
            },
        ]

    def get_open_cards_buttons(self):
        return [
            {
                "type": "InlineKeyboardButton",
                "text": "Open Cards",
                "callback_data": "{}-click-{}".format(self.OP_REVEAL, self.vote_id),
            },
            {
                "type": "InlineKeyboardButton",
                "text": "Open Cards 🆕",
                "callback_data": "{}-click-{}".format(self.OP_REVEAL_NEW, self.vote_id),
            },
        ]

    def get_markup(self):
        layout_rows = []

        for points_layout_row in POINTS_LAYOUT:
            points_buttons_row = []
            for point in points_layout_row:
                points_buttons_row.append(self.get_point_button(point))
            layout_rows.append(points_buttons_row)

        layout_rows.append(self.get_reset_buttons())
        layout_rows.append(self.get_open_cards_buttons())

        return {
            "type": "InlineKeyboardMarkup",
            "inline_keyboard": layout_rows,
        }

    def restart(self):
        self.votes.clear()
        self.revealed = False

    @staticmethod
    def _initiator_str(initiator: dict) -> str:
        return "@{} ({})".format(
            initiator.get("username") or initiator.get("id"),
            initiator["first_name"]
        )

    def to_dict(self):
        return {
            "initiator": self.initiator,
            "text": self.text,
            "reply_message_id": self.reply_message_id,
            "revealed": self.revealed,
            "votes": {user_id: vote.to_dict() for user_id, vote in self.votes.items()}
        }

    @classmethod
    def from_dict(cls, chat_id, vote_id, dct):
        res = cls(chat_id, vote_id, dct["initiator"], dct["text"])
        for user_id, vote in dct["votes"].items():
            res.votes[user_id] = Vote.from_dict(vote)
        res.revealed = dct["revealed"]
        res.reply_message_id = dct["reply_message_id"]
        return res


class GameRegistry:
    def __init__(self):
        self._db = None

    async def init_db(self, db_path):
        con = aiosqlite.connect(db_path)
        con.daemon = True
        self._db = await con
        # It's pretty dumb schema, but I'm too lazy for proper normalized tables for this task
        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS games (
                chat_id, game_id, 
                json_data,
                PRIMARY KEY (chat_id, game_id)
            )
        """)

    def new_game(self, chat_id, incoming_message_id: str, initiator: dict, text: str):
        return Game(chat_id, incoming_message_id, initiator, text)

    async def get_game(self, chat_id, incoming_message_id: str) -> Game:
        query = 'SELECT json_data FROM games WHERE chat_id = ? AND game_id = ?'
        async with self._db.execute(query, (chat_id, incoming_message_id)) as cursor:
            res = await cursor.fetchone()
            if not res:
                return None
            return Game.from_dict(chat_id, incoming_message_id, json.loads(res[0]))

    async def save_game(self, game: Game):
        await self._db.execute(
            "INSERT OR REPLACE INTO games VALUES (?, ?, ?)",
            (game.chat_id, game.vote_id, json.dumps(game.to_dict()))
        )
        await self._db.commit()
