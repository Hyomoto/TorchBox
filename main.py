from tinder import Tinderstarter, TinderBurn
from tinder.crucible import Crucible

def main():
    with open("./scripts/battle.tinder", "r") as f:
        input = f.read()
    tinder = Tinderstarter()
    script = tinder.compile(input)
    crucible = Crucible()
    line = script.run(0, crucible)
    print(line)
    print(crucible.variables)

if __name__ == "__main__":
    main()
