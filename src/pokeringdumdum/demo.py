"""Local-only explorer server. Rules and opponent decisions remain in Python."""

import json
import random
import secrets
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from pokeringdumdum.game import (
    DEALS,
    acting_player,
    is_terminal,
    legal_actions,
    terminal_utility_player_zero,
)


class Hand:
    def __init__(self, policy, seed):
        self.policy = policy
        self.rng = random.Random(seed)
        self.cards = self.rng.choice(DEALS)
        self.history = ""

    def view(self):
        terminal = is_terminal(self.history)
        result = {"card": self.cards[0], "history": self.history, "terminal": terminal}
        if terminal:
            result.update(
                opponent_card=self.cards[1],
                payoff=terminal_utility_player_zero(self.cards, self.history),
            )
        return result

    def act(self, action):
        if (
            is_terminal(self.history)
            or acting_player(self.history) != 0
            or action not in legal_actions(self.history)
        ):
            raise ValueError("illegal action")
        self.history += action
        if not is_terminal(self.history) and acting_player(self.history) == 1:
            # The policy key contains only the acting player's card and public history.
            probabilities = self.policy[1, self.cards[1], self.history]
            self.history += "p" if self.rng.random() < probabilities[0] else "b"
        return self.view()


class Handler(SimpleHTTPRequestHandler):
    policy = {}
    sessions = {}

    def do_POST(self):
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size < 4096:
                raise ValueError("invalid request size")
            body = json.loads(self.rfile.read(size))
            if self.path == "/api/new":
                if len(self.sessions) >= 1000:
                    self.sessions.clear()
                token = secrets.token_urlsafe(24)
                hand = Hand(self.policy, secrets.randbits(64))
                self.sessions[token] = hand
                result = {"token": token, **hand.view()}
            elif self.path == "/api/act":
                result = self.sessions[body["token"]].act(body["action"])
            else:
                raise ValueError("unknown endpoint")
            payload = json.dumps(result).encode()
            self.send_response(200)
        except (ValueError, KeyError, TypeError):
            payload = b'{"error":"Invalid action or expired hand"}'
            self.send_response(400)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def main():
    directory = Path("explorer").resolve()
    data = json.loads((directory / "strategy.json").read_text())
    Handler.policy = {
        (n["player"], n["card"], n["history"]): n["probabilities"]
        for n in data["information_sets"]
    }
    print("Kuhn explorer: http://127.0.0.1:8765", flush=True)
    ThreadingHTTPServer(
        ("127.0.0.1", 8765), partial(Handler, directory=str(directory))
    ).serve_forever()


if __name__ == "__main__":
    main()
