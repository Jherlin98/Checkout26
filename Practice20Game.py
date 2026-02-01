import MainGame as mg

class Practice20Game:
    def __init__(self, name="Player", max_darts=99, start_score=0):
        self.name = name
        self.max_darts = max_darts
        self.start_score = 0 # Practice starts at 0 and counts up
        self.score = 0
        self.turn_darts = []
        self.history = [] # Stores score state before each throw for undo
        self.throw_history = [] # Stores the actual dart strings for stats undo
        self.stats = {
            "20": 0,
            "T20": 0,
            "5": 0,
            "1": 0,
            "12": 0,
            "18": 0
        }
        self.dart_coords = []
        self.game_type = "practice_20"
        self.legs_won = 0
        self.checkouts_hit = 0
        self.checkout_attempts = 0

    def throw(self, dart_input, coords=None):
        if coords:
            self.dart_coords.append(coords)

        score, _ = mg.parse_score(dart_input)
        
        # Save current score to history before updating (for undo)
        self.history.append(self.score)
        self.throw_history.append(dart_input)
        
        # Only score if it hit the 20 segment
        if "20" in dart_input:
            self.score += score
        
        # Update Stats
        raw_input = str(dart_input).upper()
        if raw_input == "20":
            self.stats["20"] += 1
        elif raw_input == "T20":
            self.stats["T20"] += 1
        elif "5" in raw_input and "15" not in raw_input and "25" not in raw_input:
            # Matches 5, D5, T5
            self.stats["5"] += 1
        elif raw_input in ["1", "D1", "T1"]:
            self.stats["1"] += 1
        elif "12" in raw_input:
            self.stats["12"] += 1
        elif "18" in raw_input:
            self.stats["18"] += 1

        self.turn_darts.append(dart_input)
        
        if self.total_darts_thrown >= self.max_darts:
            return "WIN"
        
        return "OK"

    def reset(self):
        self.score = 0
        self.turn_darts = []
        self.history = []
        self.throw_history = []
        self.dart_coords = []
        self.stats = {"20": 0, "T20": 0, "5": 0, "1": 0, "12": 0, "18": 0}

    def undo(self):
        if self.history:
            self.score = self.history.pop()
            
            if self.throw_history:
                last_throw = self.throw_history.pop()
                raw_input = str(last_throw).upper()
                if raw_input == "20":
                    self.stats["20"] -= 1
                elif raw_input == "T20":
                    self.stats["T20"] -= 1
                elif "5" in raw_input and "15" not in raw_input and "25" not in raw_input:
                    self.stats["5"] -= 1
                elif raw_input in ["1", "D1", "T1"]:
                    self.stats["1"] -= 1
                elif "12" in raw_input:
                    self.stats["12"] -= 1
                elif "18" in raw_input:
                    self.stats["18"] -= 1

            if self.turn_darts:
                self.turn_darts.pop()
            if self.dart_coords:
                self.dart_coords.pop()

    def end_turn(self):
        self.turn_darts = []

    def average(self):
        if self.total_darts_thrown == 0:
            return 0.0
        return (self.score / self.total_darts_thrown) * 3

    def get_turn_score(self):
        total = 0
        for dart in self.turn_darts:
            score, _ = mg.parse_score(dart)
            total += score
        return total

    def checkout_suggestion(self):
        return None

    def export_session(self):
        return {
            "player": self.name,
            "game_type": self.game_type,
            "score": self.score,
            "stats": self.stats,
            "stats_percentages": self.stats_percentages,
            "total_darts_thrown": self.total_darts_thrown,
            "average": self.average()
        }

    @property
    def total_darts_thrown(self):
        return len(self.history)

    @property
    def checkout_percentage(self):
        return 0.0

    @property
    def stats_percentages(self):
        total = self.total_darts_thrown
        if total == 0:
            return {k: 0.0 for k in self.stats}
        return {k: (v / total) * 100 for k, v in self.stats.items()}