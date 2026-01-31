def parse_score(input_string):
    s = input_string.strip().upper()

    if s == "MISS" or s == "0":
        return 0, False
    if s == "50":
        return 50, True
    if s == "25":
        return 25, False
    
    multiplier = 1
    if s.startswith("D"):
        multiplier = 2
        s = s[1:]
    elif s.startswith("T"):
        multiplier = 3
        s = s[1:]

    if not s.isdigit():
        raise ValueError("Invalid score input")
    value = int(s)

    if value < 0 or value > 20:
        raise ValueError("Score must be between 0 and 20")
    return value * multiplier, multiplier == 2

    