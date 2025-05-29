from constants import Ansi
import os
from firestarter.grammar import PEG, Match, Grammar, GrammarError

def main():
    with open("./firestarter/peg.peg", "r") as f:
        peg_grammar = f.read()

    try:
        matches = PEG.parse(peg_grammar)
    except GrammarError as e:
        print(e)
        return
    pretty_print_matches(matches[-1], peg_grammar)

def pretty_print_matches(match: Match, tokens: str):
    def render(match: Match, tokens, depth=0):
        if match.rule.identifier_ :
            out = f"{' ' * depth}{match.rule.identifier}{Ansi.BLUE}<{Ansi.RESET}{match.slice(tokens)!r}{Ansi.BLUE}>{Ansi.RESET}\n"
        else:
            out = ''# f"{' ' * depth}{match.rule.__class__}:'{match.slice(tokens)!r}'\n"
        for child in match.children:
            out += render(child, tokens, depth + 2)
        return out
    print(render(match,tokens).rstrip())

if __name__ == "__main__":
    main()