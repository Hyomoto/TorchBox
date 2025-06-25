from . import Symbol

class Resolver:
    """A generic resolver for symbols in the Firestarter language."""
    def __init__(self):
        pass
        
    def resolve(self, node: Symbol):
        return node