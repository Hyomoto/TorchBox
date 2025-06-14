from typing import List, Dict
import re

class Macro:
    def __init__(self, name: str, body: str):
        self.name = name
        self.body = body
        
    def match_and_expand(self, line: str):
        return re.sub(rf'\b{self.name}\b', self.body, line)

class PatternMacro:
    def __init__(self, pattern: str, template: str):
        # Pattern with $vars, e.g. "for $a ; $b ; $c end"
        # Convert to regex: "for (.+?) ; (.+?) ; (.+?) end"
        self.placeholders = re.findall(r'\$([a-zA-Z_]\w*)', pattern)
        # Escape special chars, then sub $vars with (.+?)
        pat_escaped = re.escape(pattern)
        for ph in self.placeholders:
            pat_escaped = pat_escaped.replace('\\$' + ph, r'(.+?)')
        self.regex = re.compile(pat_escaped)
        self.template = template

    def match_and_expand(self, line: str):
        m = self.regex.fullmatch(line.strip())
        if not m:
            return None
        subs = dict(zip(self.placeholders, m.groups()))
        # Replace $placeholders in template
        result = self.template
        for k, v in subs.items():
            result = result.replace(f'${k}', v.strip())
        return result

class Preprocessor:
    def __init__(self):
        self.macros: List[PatternMacro] = []

    def pattern(self, pattern: str, template: str):
        self.macros.append(PatternMacro(pattern, template))

    def define(self, name: str, body: str):
        self.macros.append(Macro(name, body))

    def process(self, source: str) -> str:
        output = []
        for line in source.split('\n'):
            for macro in self.macros:
                expanded = macro.match_and_expand(line)
                if not expanded:
                    continue
                line = expanded or line
            output.append(line)
        return '\n'.join(output)
