import collections
import json


AVAILABLE_POINTS = [
    "1", "2", "3", "5", "8",
    "13", "20", "40", "?", "☕",
]
HALF_POINTS = len(AVAILABLE_POINTS) // 2
ALL_MARKS = "♥♦♠♣"


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


class Game:
    def __init__(self, vote_id, initiator, text):
        self.vote_id = vote_id
        self.initiator = initiator
        self.text = text
        self.reply_message_id = 0
        self.votes = collections.defaultdict(Vote)
        self.revealed = False

    def add_vote(self, initiator, point):
        self.votes[self._initiator_str(initiator)].set(point)

    def get_text(self):
        result = "Vote for:\n{}\nInitiator: {}".format(self.text, self._initiator_str(self.initiator))
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

    def get_markup(self):
        points_keys = [
            {
                "type": "InlineKeyboardButton",
                "text": point,
                "callback_data": "vote-click-{}-{}".format(self.vote_id, point),
            }
            for point in AVAILABLE_POINTS
        ]
        return {
            "type": "InlineKeyboardMarkup",
            "inline_keyboard": [
                points_keys[:HALF_POINTS],
                points_keys[HALF_POINTS:],
                [
                    {
                        "type": "InlineKeyboardButton",
                        "text": "Restart",
                        "callback_data": "restart-click-{}".format(self.vote_id),
                    }
                ],
                [
                    {
                        "type": "InlineKeyboardButton",
                        "text": "Open Cards",
                        "callback_data": "reveal-click-{}".format(self.vote_id),
                    },
                ],
            ],
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


class Storage:
    def __init__(self):
        self._games = {}

    def new_game(self, chat_id, incoming_message_id: str, initiator: dict, text: str):
        self._games[(chat_id, incoming_message_id)] = game = Game(incoming_message_id, initiator, text)
        return game

    def get_game(self, chat_id, incoming_message_id: str) -> Game:
        return self._games.get((chat_id, incoming_message_id))
