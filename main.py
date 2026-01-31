from DartsGame import DartsGame

def main():
    game = DartsGame()

    print("Welcome to the Darts Game! Starting score is 501.")
    print("Ctrl.c to exit.\n")

    while game.score > 0:
        print (f"Score: {game.score}")
        dart= input("Throw: ")
        try:
            game.throw(dart)
        except ValueError as e:
            print(e)
    print("game shot")
if __name__ == "__main__":
    main()
