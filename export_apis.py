from typing import List, Dict, Optional, Any
from tinder.api import API
import re

class APIDoc:
    """Class to represent API documentation."""
    def __init__(self, name: str, description: str, methods: List['MethodDoc'], permissions: Optional[List[str]] = None):
        self.name = name
        self.description = description
        self.methods = methods
        self.permissions = permissions

class MethodDoc:
    """Class to represent method documentation."""
    def __init__(self, name: str, description: str, parameters: Dict[str, 'ParameterDoc'], kwargs: Optional[Dict[str, 'ParameterDoc']] = None, return_type: Optional[str] = None):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.kwargs = kwargs
        self.return_type = return_type

class ParameterDoc:
    """Class to represent parameter documentation."""
    def __init__(self, name: str, type: str, desc: str, default: str = None):
        self.name = name
        self.type = type
        self.desc = desc
        self.default = default

def export_api(apis: Dict[str, API]):
    def make_navbar(sections: List[str]) -> str:
        header = "| Jump To | " + " | ".join(f"[{s}](#{s.lower()})" for s in sections) + " |"
        sep = "|" + "---------|" * (len(sections) + 1)
        return f"{header}\n{sep}"

    def markdown_escape(text):
        # Quick helper to escape markdown special chars if needed, basic pass
        return str(text).replace('_', '\\_') if text else ""

    def extract_kwargs(doc) -> Dict[str, ParameterDoc]:
        """
        Extract kwargs from a docstring.
        Returns a list of dicts: [{'name', 'type', 'desc', 'default'}]
        """
        if not doc:
            return {}
        # Find the "Kwargs:" section
        m = re.search(r'Kwargs:\s*((?:\s*-\s.+\n?)+)', doc)
        if not m:
            return {}
        kwargs_text = m.group(1)
        results = {}
        for line in kwargs_text.strip().splitlines():
            # Match: "- name (type): desc (default: ...)"
            match = re.match(
                r'\s*-\s*(\w+)(?:\s*\(([^)]+)\))?:\s*(.+)', line
            )
            if match:
                name, typ, desc = match.groups()
                # Try to extract default value if present at end of description
                default_match = re.search(r'\(default:\s*([^)]+)\)', desc)
                default = default_match.group(1) if default_match else None
                desc_clean = re.sub(r'\s*\(default:.*\)', '', desc).strip()
                results[name] = ParameterDoc(
                    name=name,
                    type=typ,
                    desc=desc_clean,
                    default=default
                )
        return results

    def extract_args(doc) -> Dict[str, ParameterDoc]:
        """
        Extract args from a docstring.
        Returns a list of dicts: [{'name', 'type', 'desc', 'default'}]
        """
        if not doc:
            return {}
        # Find the "Args:" section
        m = re.search(r'Args:\s*((?:\s*-\s.+\n?)+)', doc)
        if not m:
            return {}
        params_text = m.group(1)
        results = {}
        for line in params_text.strip().splitlines():
            # Match: "- name (type): desc (default: ...)"
            match = re.match(
                r'\s*-\s*(\w+)(?:\s*\(([^)]+)\))?:\s*(.+)', line
            )
            if match:
                name, typ, desc = match.groups()
                # Try to extract default value if present at end of description
                default_match = re.search(r'\(default:\s*([^)]+)\)', desc)
                default = default_match.group(1) if default_match else None
                desc_clean = re.sub(r'\s*\(default:.*\)', '', desc).strip()
                results[name] = ParameterDoc(
                    name=name,
                    type=typ,
                    desc=desc_clean,
                    default=default
                )
        return results

    def extract_return_type(doc):
        if not doc:
            return None
        # Find the "Returns:" section
        m = re.search(r'Returns:\s*(.+)', doc)
        if not m:
            return None
        return m.group(1)

    def clean_header(doc:str) -> str:
        """Clean the header of a docstring."""
        if not doc:
            return ""
        # Include only up to the Kwargs, Args or Returns section
        sections = re.split(r'\n\s*(?:Kwargs|Args|Returns):', doc, maxsplit=1)
        return sections[0].strip()

    docs: Dict[str, APIDoc] = {}

    for name, item in apis.items():
        items = item.export()
        doc = APIDoc(
            name=name,
            description=item.__doc__,
            methods=[],
            permissions=item.permissions if hasattr(item, 'permissions') else None
        )
        methods: List[MethodDoc] = doc.methods
        for key, value in items.items():
            if callable(value):
                methods.append(MethodDoc(
                    name=key,
                    description=clean_header(value.__doc__),
                    parameters=extract_args(value.__doc__),
                    kwargs = extract_kwargs(value.__doc__),
                    return_type=extract_return_type(value.__doc__)
                ))
            else:
                methods.append(MethodDoc(
                    name=key,
                    description=str(value),
                    parameters=None,
                    return_type=None
                ))
        docs[name] = doc

    markdown = {}
    for api_name, api_doc in docs.items():
        output = ""
        output += f"# API: {markdown_escape(api_name)}\n"
        output += "---\n"
        #output += make_navbar([name.name for name in api_doc.methods]) + "\n"
        if api_doc.permissions:
            output += "\n**Requires Permissions:**[" + ", ".join(f"`{perm}`" for perm in api_doc.permissions) + "]\n"
        desc = api_doc.description or "\n_No description provided._"
        output += f"{desc}\n"
        for method in api_doc.methods:
            signature = f"`{method.name}("
            params = [name for name in method.parameters.keys()] if method.parameters else []
            if method.kwargs:
                params.append("**kwargs")
            output += f"## {signature}{', '.join(params)})`\n"
            mdesc = method.description or "_No description provided._"
            output += f"{mdesc}\n"
            if method.parameters:
                output += "\n**Parameters:**\n"
                for pname, pval in method.parameters.items():
                    output += f"- `{pname}`: *{pval.type}*{f' (default: {pval.default})' if pval.default else ''}\n"
            if method.kwargs:
                output += "\n**Kwargs:**\n"
                for kname, kval in method.kwargs.items():
                    output += f"- `{kname}`: *{kval.type}*{f' (default: {kval.default})' if kval.default else ''}\n"
            if method.return_type:
                output += f"\n**Returns:** *{method.return_type}*\n"
            else:
                output += "\n**Returns:** _None_"
            output += "\n"
        output += "\n---\n"
        markdown[api_name] = output

    # generate pages
    for name, doc in markdown.items():
        with open(f"./docs/{name}.md", "w", encoding="utf-8") as f:
            f.write(doc)
        print(f"API documentation generated in ./docs/API/{name}.md")

    # generate sidebar
    with open("./docs/_sidebar.md", "w", encoding="utf-8") as f:
        f.write(
            '<center>\n\t<a href="/" style="text-decoration: none; color: inherit;">\n\t\t<div>\n'
            '\t\t\t<img src="tinder.svg" alt="drawing" width="32" />\n'
            '\t\t</div><font size="4">Tinder</font>\n\t</a>\n</center>\n'
            '\n'
            '- [Home](language.md)\n'
        )
        for name in markdown.keys():
            f.write(f"- [{name}]({name}.md)\n")

if __name__ == "__main__":
    from game.apis import import_api
    apis = import_api({})
    export_api(apis)