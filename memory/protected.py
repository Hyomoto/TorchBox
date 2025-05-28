"""
this is the protected memory module for the Sock & Sorcery game.
it provides constants and functions that are protected from modification
and can be accessed globally.
"""
import random
import os

def api_random_number( start: int, end: int):
    return random.randint(int(start), int(end))

def clear_screen():
    """Clear the console screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

map = {
    "PROG_NAME": "Socks & Sorcery",
    "VERSION": "0.1",
    "random": api_random_number,
    "clear_screen": clear_screen,
}