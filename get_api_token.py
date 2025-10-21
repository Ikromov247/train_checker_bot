import random

tokens = [
    "58135170-034a-453c-a0b4-eeaaf1d5470e",
    "cc232334-dcd3-4218-ac3f-19657d3fc883"
]

def get_random_token()->str:
    return random.choice(tokens)