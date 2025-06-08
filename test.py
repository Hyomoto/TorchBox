from firestarter.grammar import make_grammar_from_file, Flags
from tinder import Tinderstarter
from constants import BLUE, RED, RESET

def read_file(path: str) -> str:
    with open(path, "r") as f:
        return f.read()

if __name__ == "__main__":
    tinderstarter = Tinderstarter()
    print(f"{BLUE}Start of compilation...{RESET}")
    try:
        tinder = tinderstarter.compile(read_file("./scripts/login.v2.tinder"), "v2")
        print(f"{BLUE}Compilation successful!{RESET}")
    except Exception as e:
        print(e)
        print(f"{RED}Compilation failed!{RESET}")
    print(tinder)
    