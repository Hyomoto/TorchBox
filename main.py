from constants import Ansi
import os
from firestarter.grammar import Grammar, GrammarError, make_grammar_from_file

def main():
    try:
        grammar = make_grammar_from_file("./firestarter/peg.peg")
    except GrammarError as e:
        print(e)
        return
    #print(grammar)

if __name__ == "__main__":
    main()