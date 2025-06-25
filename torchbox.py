class Object(dict):
    pass

class Namespace(dict):
    pass

class Object(dict):
    pass

class Torchbox:
    def __init__(self):
        self.namespaces = {
            "global" : Namespace(),
        }

    def run(self):
        while True:
            break
        
    def __repr__(self):
        return f"Torchbox()"
    
