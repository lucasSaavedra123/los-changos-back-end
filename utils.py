import random
import string


def create_random_string(string_length):
    characters = [chr(ascii_code) for ascii_code in range(33, 126 + 1)]
    return ''.join(
        random.choice(string.ascii_uppercase + string.ascii_lowercase) for i in range(string_length)
    )

def create_random_color_string():
    R = random.randint(0,255)
    G = random.randint(0,255)
    B = random.randint(0,255)
    return f"rgba({R},{G},{B},0.2)"
