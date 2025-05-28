from constants import Ansi
import os
from firestarter import *

def main():
    grammar = Peg()

    with open("./firestarter/peg.peg", "r") as f:
        peg_grammar = f.read()

    matches = grammar.parse(peg_grammar)
    print(f"Comparing {Ansi.LIGHT_BLUE}peg.peg{Ansi.RESET} with {Ansi.LIGHT_BLUE}peg.py")
    differences = compare_rules(grammar.rule, matches[-1].rule)
    for nomatch in differences:
        print(f"{Ansi.RED}Error: {nomatch[0]} != {nomatch[1]}{Ansi.RESET}")
    print(f"Total differences: {len(differences)}{Ansi.RESET}")
    pretty_print_matches(matches[-1], peg_grammar)

def pretty_print_matches(match: Match, tokens: str):
    def render(match: Match, tokens, depth=0):
        if match.rule.identifier_:
            out = f"{' ' * depth}{match.rule.identifier}<{match.slice(tokens)!r}>\n"
        else:
            out = ''# f"{' ' * depth}{match.rule.__class__}:'{match.slice(tokens)!r}'\n"
        for child in match.children:
            out += render(child, tokens, depth + 2)
        return out
    print(render(match,tokens).rstrip())

def compare_grammar(grammar1: "Grammar", grammar2: "Grammar"):
    """Compare two grammars and return a list of differences."""
    return compare_rules( grammar1.rule, grammar2.rule) # type: ignore
    
def compare_rules(rule1: Rule, rule2: Rule):
    differences = []
    visited = []
    stack = [ rule1, rule2 ]
    while stack:
        that = stack.pop() # rule 2
        this = stack.pop() # rule 1
        if this in visited:
            continue
        visited.append(this)
        if this != that:
            differences.append((this, that))
            continue # no need to compare children if the rule itself is different
        if isinstance(this, RuleSingle):
            stack.append(this.rule)
            stack.append(that.rule)
        elif isinstance(this, RuleMultiple):
            for i, rule in enumerate(this.rules):
                    stack.append(rule)
                    stack.append(that.rules[i])
    return differences
        

if __name__ == "__main__":
    main()