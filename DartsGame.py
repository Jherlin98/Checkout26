import MainGame as mg
from checkouts import CHECKOUTS
class DartsGame:
    def __init__(self, name="Player", start_score=501):
        self.name = name  # Store the player's name
        self.start_score = start_score
        self.score = start_score
        self.game_type = "x01"
        self.dart_coords = []
        self.turn_darts = []
        self.turns = []          # completed turns
        self.current_turn = []  # darts in this turn
        self.turn_start_score = start_score
        self.checkout_attempts = 0
        self.checkouts_hit = 0
        self.legs_won = 0

    def throw(self, dart_input, coords=None):
        is_180 = False


        if coords:
            self.dart_coords.append(coords)

        score, is_double = mg.parse_score(dart_input)
        new_score = self.score - score

        dart= {'input': dart_input, 'score': score,  'is_double': is_double}

        # Check for bust conditions
        if new_score < 0 or new_score == 1:
            self._bust()
            return "BUST", False


        # Check for double out condition
        if new_score == 0 and not is_double:
            self._bust()
            return "NO_DOUBLE", False
        
        # Track checkout attempts (Score is 50 or <= 40 and even)
        if self.score == 50 or (self.score <= 40 and self.score % 2 == 0 and self.score > 0):
            self.checkout_attempts += 1
        
        self.score = new_score
        self.current_turn.append(dart)
        if self.score == 0:
            self.checkouts_hit += 1
            return ("WIN", False)
        
        if len(self.current_turn) == 3:
            turn_score = sum(d['score'] for d in self.current_turn)

            is_180 = (
                turn_score == 180 and
                self.turn_start_score >= 180
            )

            self.end_turn()
            return ("TURN_OVER", is_180)

                
        return ("OK", False)


    def _bust(self):
        self.score = self.turn_start_score
        # Busts: If a player busts on their first or second dart of a turn, all three darts for that visit are counted as thrown.
        busted_turn = [
            {'input': 'BUST', 'score': 0, 'is_double': False},
            {'input': '', 'score': 0, 'is_double': False},
            {'input': '', 'score': 0, 'is_double': False}
        ]
        self.turns.append(busted_turn)
        self.current_turn = []

    def end_turn(self):
        if self.current_turn:
            self.turns.append(self.current_turn)
        self.current_turn = []
        self.turn_start_score = self.score


    def reset(self):
        self.score = self.start_score
        self.turn_darts = []
        self.turn_dart_score = self.start_score
        self.history = []
        self.checkout_attempts = 0
        self.checkouts_hit = 0
        self.dart_coords = []
        self.turns = []
        self.current_turn = []

    def undo_last_dart(self):
        if self.current_turn:
            dart= self.current_turn.pop()
            self.score += dart['score']
            return
        if self.turns:
            # Check if the last turn was a bust. If so, just remove it.
            # This correctly resets the player to the start of their turn
            # without attempting to restore a partial (busted) turn.
            if self.turns[-1] and self.turns[-1][0].get('input') == 'BUST':
                self.turns.pop()
                return

            last_turn = self.turns.pop()
            dart= last_turn.pop()
            self.score += dart['score']
            self.current_turn = last_turn

    def undo_last_turn(self):
        if not self.turns:
            return

        last_turn = self.turns.pop()
        self.score += sum(d["score"] for d in last_turn)


    def average(self):
        total_darts = sum(len(t) for t in self.turns) + len(self.current_turn)
        if total_darts == 0:
            return 0.0
        total_points = self.start_score - self.score
        return (total_points / total_darts) * 3
    
    def highest_score(self):
        highest = 0
        for turn in self.turns:
            turn_score = sum(d['score'] for d in turn)
            if turn_score > highest:
                highest = turn_score
        return highest

    def get_turn_score(self):
        return sum(d['score'] for d in self.current_turn)
    
    def checkout_suggestion(self):
        suggestion = CHECKOUTS.get(self.score)
        if suggestion is None:
            return None

        darts_remaining = 3 - len(self.current_turn)
        if darts_remaining > 0 and len(suggestion) > darts_remaining:
            return suggestion[:darts_remaining]
            
        return suggestion

    def export_session(self):
        all_turns = self.turns.copy()
        if self.current_turn:
            all_turns.append(self.current_turn.copy())
        return {
            "player": self.name,
            "start_score": self.start_score,
            "turns": all_turns,
            "checkout_attempts": self.checkout_attempts,
            "checkouts_hit": self.checkouts_hit,
            "average": self.average(),
            "highest_score":self.highest_score(),
            "total_darts_thrown": self.total_darts_thrown,
            "is_winner": self.score == 0
        }


    @property
    def total_darts_thrown(self):
        return sum(len(t) for t in self.turns) + len(self.current_turn)

    @property
    def checkout_percentage(self):
        if self.checkout_attempts == 0:
            return 0.0
        return (self.checkouts_hit / self.checkout_attempts) * 100