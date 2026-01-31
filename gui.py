import tkinter as tk
from DartsGame import DartsGame
from MainGame import parse_score

#Initialize shite
root = tk.Tk()  # Initialize the root window first
root.title("Checkout 26")
root.geometry("400x600")
game = None
current_multiplier = tk.StringVar(value="S")  # Create StringVar after initializing root

#------------ Screen management --------------
def clear_screen():
    for widget in root.winfo_children():
        widget.destroy()

#------------ Start Screen --------------
def start_screen():
    clear_screen()
    tk.Label(root, text="welcome to Checkout 26", font=("Arial", 24)).pack(pady=20)
    tk.Label(root, text="Player Name:").pack()
    name_entry = tk.Entry(root, font=("Arial", 14))
    name_entry.pack(pady=5)
    tk.Label(root, text="Starting Score:").pack()
    start_score_var = tk.IntVar(value=501)
    tk.OptionMenu(root, start_score_var, 301, 501).pack(pady=5)
    def start_game():
        global game
        name = name_entry.get().strip() or "Player"
        game = DartsGame(start_score=start_score_var.get())
        game_screen()
    tk.Button(root, text="Start Game", font=("Arial", 14),
              command=start_game).pack(pady=20)
#------------ Game Screen --------------
def game_screen():
    clear_screen()
    score_label = tk.Label(root, font=("Arial", 32))
    score_label.pack(pady=10)

    player_label = tk.Label(root, font=("Arial", 16))
    player_label.pack()

    avg_label = tk.Label(root, font=("Arial", 14))
    avg_label.pack()

    turn_label = tk.Label(root, font=("Arial", 12))
    turn_label.pack(pady=5)

    status_label = tk.Label(root, font=("Arial", 14), fg="red")
    status_label.pack()


    def refresh():
        score_label.config(text=f"Score: {game.score}")
        turn_label.config(text=f"Darts this turn: {', '.join(game.turn_darts)}")
        avg_label.config(text=f"Average: {game.average():.2f}")
        turn_label.config(text=f"Turn: "+", ".join(game.turn_darts))

    def throw_dart(value):
        if value not in ["MISS", "25", "50"]:
            dart = f"{current_multiplier.get()}{value}"
        else:
            dart = value

        result = game.throw(dart)
        refresh()

        if result == "WIN":
            status_label.config(text="🎯 GAME SHOT!")
        elif result == "BUST":
            status_label.config(text="BUST!")
        else:
            status_label.config(text="")

    # Multipliers
    mult_frame = tk.Frame(root)
    mult_frame.pack(pady=10)
    for m in ["S", "D", "T"]:
        tk.Button(mult_frame, text=m, width=10, height=2, font=("Arial", 16),
                  command=lambda x=m: current_multiplier.set(x)).pack(side="left", padx=5, pady=5)

    # Number buttons
    num_frame = tk.Frame(root)
    num_frame.pack(pady=10)

    for i in range(1, 21):
        tk.Button(num_frame, text=str(i), width=8, height=3, font=("Arial", 16),
                  command=lambda x=i: throw_dart(str(x))
                  ).grid(row=(i-1)//5, column=(i-1)%5, padx=5, pady=5)

    # Specials
    special_frame = tk.Frame(root)
    special_frame.pack(pady=10)
    for s in ["25", "50", "MISS"]:
        tk.Button(special_frame, text=s, width=10, height=2, font=("Arial", 16),
                  command=lambda x=s: throw_dart(x)).pack(side="left", padx=5, pady=5)

    refresh()

# ---------- Start App ----------

start_screen()
root.mainloop()