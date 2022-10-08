import random
import string


def create_random_string(string_length):
    characters = [chr(ascii_code) for ascii_code in range(33, 126 + 1)]
    return ''.join(
        random.choice(string.ascii_uppercase + string.ascii_lowercase) for i in range(string_length)
    )
