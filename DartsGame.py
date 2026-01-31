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
        self.turn_dart_score = start_score
        self.history = []
        self.checkout_attempts = 0
        self.checkouts_hit = 0
        self.legs_won = 0

    def throw(self, dart_input, coords=None):
        if coords:
            self.dart_coords.append(coords)

        score, is_double = mg.parse_score(dart_input)
        new_score = self.score - score

        # Check for bust conditions
        if new_score < 0 or new_score == 1:
            self._bust()
            return "BUST"
        # Check for double out condition
        if new_score == 0 and not is_double:
            self._bust()
            return "NO_DOUBLE"
        
        # Track checkout attempts (Score is 50 or <= 40 and even)
        if self.score == 50 or (self.score <= 40 and self.score % 2 == 0 and self.score > 0):
            self.checkout_attempts += 1

        self.history.append(self.score)
        self.score = new_score
        self.turn_darts.append(dart_input)

        if self.score == 0:
            self.checkouts_hit += 1
            return "WIN"
        
        return "OK"

    def _bust(self):
        self.score = self.turn_dart_score

    def end_turn(self):
        self.turn_dart_score = self.score
        self.turn_darts = []

    def reset(self):
        self.score = self.start_score
        self.turn_darts = []
        self.turn_dart_score = self.start_score
        self.history = []
        self.checkout_attempts = 0
        self.checkouts_hit = 0
        self.dart_coords = []

    def undo(self):
        if self.history:
            self.score = self.history.pop()
            if self.dart_coords:
                self.dart_coords.pop()

    def average(self):
        total_points = self.start_score - self.score  # Calculate total points scored
        total_darts = len(self.history) + len(self.turn_darts)  # Total darts thrown
        if total_darts == 0:
            return 0.0
        return (total_points / total_darts) * 3

    def get_turn_score(self):
        total = 0
        for dart in self.turn_darts:
            score, _ = mg.parse_score(dart)
            total += score
        return total
    
    def checkout_suggestion(self):
        suggestion = CHECKOUTS.get(self.score)
        if suggestion is None:
            return None

        darts_remaining = 3 - len(self.turn_darts)
        if darts_remaining > 0 and len(suggestion) > darts_remaining:
            return suggestion[:darts_remaining]
            
        return suggestion

    @property
    def total_darts_thrown(self):
        return len(self.history) + len(self.turn_darts)

    @property
    def checkout_percentage(self):
        if self.checkout_attempts == 0:
            return 0.0
        return (self.checkouts_hit / self.checkout_attempts) * 100