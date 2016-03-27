import redis
import json
import random

ERGO_CARD_A, ERGO_CARD_B, ERGO_CARD_C, ERGO_CARD_D = 1, 2, 3, 4
ERGO_CARD_AND, ERGO_CARD_OR, ERGO_CARD_THEN, ERGO_CARD_NOT = 5, 6, 7, 8
ERGO_PARENTHESIS = 9
ERGO_CARD_JUSTIFICATION, ERGO_CARD_FALLACY = 10, 11
ERGO_CARD_TABULA_RASA, ERGO_CARD_REVOLUTION = 12, 13
ERGO_CARD_WILD_OPERATOR, ERGO_CARD_WILD_VARIABLE = 14, 15
ERGO_CARD_ERGO = 16
ERGO_CARDS_AMOUNT = [0, 4, 4, 4, 4, 4, 4, 4, 4, 6, 8, 3, 3, 1, 1, 1, 1, 3]

ERGO_EVENT_DRAG, ERGO_EVENT_PLACE, ERGO_EVENT_DISCARD = 1, 2, 3
ERGO_EVENT_TAKE_CARD = 4
ERGO_EVENT_LOOK_UP, ERGO_EVENT_SEND_MSG, ERGO_EVENT_COMMIT = 5, 6, 7

# Events
# Drag: [line] [position from left]
# Place: [card id] [line] [position from left]
# Discard: [card id]
# Look up: [line] [position from left]


class RedisDB:
    def __init__(self, host, port):
        self._rs = redis.StrictRedis(host=host, port=port, db=0)
        self.pre = "session"
        self.sep = ":"

    def _key(self, session_id, instance, index=None):
        if index is None:
            return self.sep.join([self.pre, str(session_id), instance])
        else:
            index = str(index)
            return self.sep.join([self.pre, str(session_id), instance, index])

    def _get(self, session_id, instance, index=None):
        return json.loads(self._rs.get(
            self._key(session_id, instance, index)).decode("utf-8"))

    def _set(self, session_id, instance, value, index=None):
        return self._rs.set(self._key(session_id, instance, index), value)

    def _count(self, key):
        return self._rs.get(self.sep.join([key, "count"]))

    def _next(self, key):
        return self._rs.incr(self.sep.join([key, "count"])) - 1

    def count_session(self):
        return self._count(self.pre)

    def next_session(self):
        return self._next(self.pre)

    def get_game(self, session_id):
        return self._get(session_id, "game")

    def set_game(self, session_id, value):
        return self._set(session_id, "game", value)

    def count_card(self, session_id):
        return self._count(self._key(session_id, "card"))

    def next_card(self, session_id):
        return self._next(self._key(session_id, "card"))

    def get_card(self, session_id, index):
        return self._get(session_id, "card", index=index)

    def set_card(self, session_id, index, value):
        return self._set(session_id, "card", value, index=index)

    def count_player(self, session_id):
        return self._count(self._key(session_id, "player"))

    def next_player(self, session_id):
        return self._next(self._key(session_id, "player"))

    def get_player(self, session_id, index):
        return self._get(session_id, "player", index=index)

    def set_player(self, session_id, index, value):
        return self._set(session_id, "player", value, index=index)


db = RedisDB('localhost', 6379)


class ErgoJSONData:
    def __init__(self):
        self._vars = []

    def json(self):
        attr = dict()
        for var in self._vars:
            attr[var] = getattr(self, var)
        return json.dumps(attr)


class ErgoGame(ErgoJSONData):
    def __init__(self, players=None, deck=None, lines=None):
        super().__init__()
        self._vars = list(self.__class__.__init__.__code__.co_varnames[1:])
        self.players, self.deck, self.lines = players, deck, lines

    @classmethod
    def create(cls, host_player_id):
        return cls([host_player_id],
                   [i for i in range(sum(ERGO_CARDS_AMOUNT))],
                   [[], [], [], []])

    @classmethod
    def from_db(cls, session_id):
        game = db.get_game(session_id)
        return cls(*[game[arg] for arg in
                     cls.__init__.__code__.co_varnames[1:]])

    def push(self, session_id):
        return db.set_game(session_id, self.json())

    def push_back(self):
        session_id = db.next_session()
        self.push(session_id)
        return session_id

    def shuffle_deck(self):
        random.shuffle(self.deck)

    def deck_pop(self):
        return self.deck.pop()


class ErgoCard(ErgoJSONData):
    def __init__(self, id, type, line=0, fixed=False):
        super().__init__()
        self._vars = list(self.__class__.__init__.__code__.co_varnames[1:])
        self.id, self.type, self.line, self.fixed = \
            id, type, line, fixed

    @classmethod
    def create(cls, id, type):
        return cls(id, type, line=0, fixed=False)

    @classmethod
    def from_db(cls, session_id, index):
        card = db.get_card(session_id, index)
        return cls(*[card[arg] for arg in
                     cls.__init__.__code__.co_varnames[1:]])

    def push(self, session_id, index):
        return db.set_card(session_id, index, self.json())

    def push_back(self, session_id):
        index = db.next_card(session_id)
        self.push(session_id, index)
        return index


class ErgoPlayer(ErgoJSONData):
    def __init__(self, hand, events):
        super().__init__()
        self._vars = list(self.__class__.__init__.__code__.co_varnames[1:])
        self.hand, self.events = hand, events

    @classmethod
    def create(cls):
        return cls([], [])

    @classmethod
    def from_db(cls, session_id, index):
        player = db.get_player(session_id, index=index)
        return cls(*[player[arg] for arg in
                     cls.__init__.__code__.co_varnames[1:]])

    def push(self, session_id, index):
        return db.set_player(session_id, index, self.json())

    def push_back(self, session_id):
        index = db.next_player(session_id)
        self.push(session_id, index)
        return index


class ErgoEvent(ErgoJSONData):
    def __init__(self, type, args):
        super().__init__()
        self.type = type
        self.args = args

    @staticmethod
    def is_correct(self):
        e_args = self._attr['args']
        if self._attr['type'] == ERGO_EVENT_DRAG:
            line, pos = 0, 1
            if len(e_args) != 2:
                return False
            if not 1 <= e_args[line] <= 8:
                return False
            if pos < 0:
                return False
        elif self._attr['type'] == ERGO_EVENT_PLACE:
            card_id, line, pos = 0, 1, 2
            if len(e_args) != 3:
                return False
            if not 0 <= e_args[card_id] < sum(ERGO_CARDS_AMOUNT):
                return False
            if not 1 <= e_args[line] <= 8:
                return False
            if pos < 0:
                return False
        elif self._attr['type'] == ERGO_EVENT_DISCARD:
            if len(e_args) != 1:
                return False
            if not 0 <= e_args[0] < sum(ERGO_CARDS_AMOUNT):
                return False
        return True


class Session:
    def __init__(self, session_id, user_id):
        self.session_id = session_id
        self.user_id = user_id
        self.game = ErgoGame.from_db(session_id)
        self.player_id = self.game.players.index(user_id)
        self.player = ErgoPlayer.from_db(session_id, self.player_id)

    def move_card(self, id, line, pos):
        card = ErgoCard.from_db(self.session_id, id)

        if card.line == self.player_id + 1:
            if card.id in self.player.hand:
                self.player.hand.remove(card.id)
                card.line = 0
            else:
                print("card removing error: incorrect position (hand)")
                return
        elif 0 <= card.line - 5 <= 3:
            tmp = card.line - 5
            if card.id in self.game.lines[tmp]:
                self.game.lines[tmp].remove(card.id)
                card.line = 0
            else:
                print(card.id, self.game.lines[tmp])
                print("card removing error: incorrect position (line)")
                return
        else:
            print("card removing error: incorrect line")
            return

        if line == 0:
            self.player.hand = \
                self.player.hand[:pos] + [id] + self.player.hand[pos:]
            card.line = self.player_id + 1
        elif 1 <= line <= 4:
            tmp = self.game.lines[line - 1]
            self.game.lines[line - 1] = tmp[:pos] + [id] + tmp[pos:]
            card.line = line + 4
        else:
            print("card placing error: incorrect line")
            return
        self.game.push(self.session_id)
        self.player.push(self.session_id, self.player_id)
        card.push(self.session_id, id)


def start_new_session(host_player_id):
    game = ErgoGame.create(host_player_id)
    game.shuffle_deck()
    session_id = game.push_back()

    cur_id = 0
    for idx, amount in enumerate(ERGO_CARDS_AMOUNT):
        for i in range(amount):
            ErgoCard.create(cur_id, idx + 1).push_back(session_id)
            cur_id += 1

    ErgoPlayer.create().push_back(session_id)

    return session_id


def start_new_test_session(host_player_id):  # TODO: remove
    game = ErgoGame.create(host_player_id)
    game.shuffle_deck()

    game.lines = [[game.deck_pop() for j in range(5 - i)]
                  for i in range(len(game.lines))]
    session_id = game.push_back()

    cur_id = 0
    for idx, amount in enumerate(ERGO_CARDS_AMOUNT):
        for i in range(amount):
            ErgoCard.create(cur_id, idx + 1).push_back(session_id)
            cur_id += 1

    player = ErgoPlayer.create()
    player.hand = [game.deck_pop() for i in range(4)]
    player.push_back(session_id)

    for line in range(len(game.lines)):
        for pos in range(len(game.lines[line])):
            tmp = ErgoCard.from_db(session_id, game.lines[line][pos])
            tmp.line = line + 5
            tmp.push(session_id, game.lines[line][pos])
    for pos in range(len(player.hand)):
        tmp = ErgoCard.from_db(session_id, player.hand[pos])
        tmp.line = 1
        tmp.push(session_id, player.hand[pos])

    return session_id
