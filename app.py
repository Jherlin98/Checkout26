from flask import Flask, render_template, request, redirect, url_for, Response
import json
from DartsGame import DartsGame
from Practice20Game import Practice20Game
from scoring_logic import get_coords_from_score

app = Flask(__name__)
match = None


class Match:
    def __init__(self, players, best_of=1):
        self.players = players
        self.current_player_index = 0
        self.best_of = int(best_of)
        self.starting_player_index = 0

    @property
    def current_player(self):
        return self.players[self.current_player_index]

    def next_player(self):
        self.current_player_index = (self.current_player_index + 1) % len(self.players)

    def next_leg(self):
        self.starting_player_index = (self.starting_player_index + 1) % len(self.players)
        self.current_player_index = self.starting_player_index
        for p in self.players:
            p.reset()

    @property
    def is_over(self):
        if self.best_of == 1:
            return any(p.legs_won >= 1 for p in self.players)
        legs_needed = (self.best_of // 2) + 1
        return any(p.legs_won >= legs_needed for p in self.players)
    
    def export_session(self):
        """Export the full multiplayer session as a dict."""
        return {
            "players": [player.export_session() for player in self.players],
            "current_player_index": self.current_player_index,
            "best_of": self.best_of,
            "starting_player_index": self.starting_player_index
        }


@app.route("/", methods=["GET", "POST"])
def start():
    global match
    if request.method == "POST":
        names_input = request.form.get("names", "Player")
        start_score = int(request.form.get("start_score", 501))
        best_of = int(request.form.get("best_of", 1))
        mode = request.form.get("mode", "normal")
        game_type = request.form.get("game_type", "x01")
        max_darts = int(request.form.get("max_darts", 99))
        
        # Split names by comma or newline and filter empty strings
        names = [n.strip() for n in names_input.replace("\r", ",").replace("\n", ",").split(",") if n.strip()]
        if not names:
            names = ["Player 1"]
            
        players = []
        for name in names:
            if game_type == "practice_20":
                players.append(Practice20Game(name, max_darts=max_darts))
            else:
                players.append(DartsGame(name, start_score))
        
        match = Match(players, best_of)
        
        return redirect(url_for("game_view"))
    return render_template("start.html")


@app.route("/game", methods=["GET", "POST"])
def game_view():
    global match
    if match is None:
        return redirect(url_for("start"))

    if request.method == "POST":
        game = match.current_player
        action = request.form.get("action")
        
        if action == "next_turn":
            game.end_turn()
            match.next_player()
            return redirect(url_for("game_view"))

        elif action == "next_leg":
            match.next_leg()
            return redirect(url_for("game_view"))
            
        elif action == "throw":
            dart = request.form.get("dart")
            coords = get_coords_from_score(dart)
            result = game.throw(dart, coords=coords)
            
            if result == "TURN_OVER":
                # Check for 180 in the last turn
                last_turn_score = 0
                if hasattr(game, 'turns') and game.turns:
                    last_turn_score = sum(d['score'] for d in game.turns[-1])
                
                is_180 = (last_turn_score == 180)

                match.next_player()
                return redirect(url_for("game_view", transition="true", one80="true" if is_180 else None))

            status = ""
            if result == "WIN":
                game.legs_won += 1
                if match.is_over:
                    status = "🎯 GAME SHOT!"
                else:
                    status = "🎯 LEG WON!"
            elif result == "BUST":
                status = "BUST!"
            elif result == "NO_DOUBLE":
                status = "No Double!"
            return redirect(url_for("game_view", status=status if status else None))

        elif action == "undo":
            if hasattr(game, "undo_last_dart"):
                game.undo_last_dart()
            elif hasattr(game, "undo"):
                game.undo()
            return redirect(url_for("game_view"))

        elif action == "export":
            if hasattr(match, "export_session"):
                data = match.export_session()
                return Response(
                    json.dumps(data, indent=2),
                    mimetype="application/json",
                    headers={"Content-Disposition": 'attachment;filename="darts_match_session.json"'}
                )
            return redirect(url_for("game_view"))

    game = match.current_player
    status = request.args.get("status", "")
    transition = request.args.get("transition")
    one80 = request.args.get("one80")
    return render_template(
        "game.html",
        match=match,
        game=game,
        status=status,
        suggestion=game.checkout_suggestion(),
        transition=transition,
        one80=one80
    )


@app.route("/restart")
def restart():
    global match
    if match:
        # Re-create players with same names and start score
        new_players = []
        for p in match.players:
            if p.game_type == "practice_20":
                new_players.append(Practice20Game(p.name, max_darts=p.max_darts))
            else:
                new_players.append(DartsGame(p.name, start_score=p.start_score))
        match = Match(new_players, match.best_of)
    return redirect(url_for("game_view"))


@app.route("/quit")
def quit():
    global match
    match = None
    return "<html><body style='background-color: #0f172a; color: #94a3b8; display: flex; justify-content: center; align-items: center; height: 100vh; font-family: sans-serif;'><h1>Game Quit. You can close this tab.</h1></body></html>"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
