from torchbox import TorchBox, Ember
from torchbox.realm import Realm, User
from tinder import Tinderstarter, Tinder, TinderBurn
from tinder.crucible import Crucible, PROTECTED, READ_ONLY, NO_SHADOWING
from constants import RESET
from memory.protected import map as protectedMemory
from memory.globals import map as globalMemory
from memory.user import map as userMemory
from memory.user import data as userData
import copy

def get_file(path: str):
    with open("./scripts/" + path, "r") as f:
        return f.read()

realm = Realm("Socks & Sorcery Realm", "A realm for Socks & Sorcery users.")
user = realm.addUser(User("admin", "default"))

tinderstarter = Tinderstarter()

def get_user(username: str):
    try:
        return realm.getUser(username)
    except Exception as e:
        return None

loginAPI = {
    "find_user": get_user,
    "check_password": lambda user, password: user.checkPassword(password),
    "set_password": lambda user, password: user.setPassword(password),
    "set_nickname": lambda user, nickname: user.setNickname(nickname),
    "new_user": lambda username, password: realm.addUser(User(username, password, userData)),
}
protectedMemory.update({"login" : loginAPI})
protectedMemory.update({"debug" : lambda x: print(f"[debug] {x}")})

class Game(TorchBox):
    def __init__(self):
        super().__init__()
        self.add("login", tinderstarter.compile(get_file("login.tinder")))
        # build the memory environment
        self.env = Crucible(PROTECTED, parent=Crucible(READ_ONLY).update(protectedMemory)).update(globalMemory)

    def run(self, entry: str):
        user = Crucible(NO_SHADOWING, parent = self.env ).update(copy.copy(userMemory))
        local = Crucible(NO_SHADOWING, parent = user )
        user["LINE"] = 0
        user["SCENE"] = entry
        self.scenes[user["SCENE"]].writeJumpTable(local)
        #print(self.scenes[user["SCENE"]])
        while True:
            line = user["LINE"]
            script = self.scenes[user["SCENE"]]
            
            if not script:
                raise Ember(f"Scene '{entry}' not found.")
            
            try:
                line = script.run(line, local)
            except TinderBurn as e:
                print(f"Error in scene '{user['SCENE']}': {e}")
                break
            print(self.substitute(user["OUTPUT"], user, self.macros).replace("\\n", "\n"))

            if user["SCENE"] == "exit":
                print("Exiting game.")
                break
            
            user["INPUT"] = input(self.substitute(user["INPUT"], user, self.macros).replace("\\n", "\n") + f" {RESET}").lower()
            user["OUTPUT"] = ""
            user["LINE"] = line

if __name__ == "__main__":
    game = Game()
    game.run("login")