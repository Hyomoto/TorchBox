from typing import List, Dict, Optional, Any
from tinder.library import Library, import_libraries
import re

PATH = "./docs/libraries/"

class LibraryDoc:
    """Class to represent Library documentation."""
    def __init__(self, name: str, description: str, methods: List['MethodDoc'], permissions: Optional[List[str]] = None):
        self.name = name
        self.description = description
        self.methods = methods
        self.permissions = permissions

class MethodDoc:
    """Class to represent method documentation."""
    def __init__(self, name: str, description: str, parameters: Dict[str, 'ParameterDoc'], kwargs: Optional[Dict[str, 'ParameterDoc']] = None, return_type: Optional[str] = None, resolvable: bool = False):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.kwargs = kwargs
        self.return_type = return_type
        self.resolvable = resolvable

class ParameterDoc:
    """Class to represent parameter documentation."""
    def __init__(self, name: str, type: str, desc: str, default: str = None):
        self.name = name
        self.type = type
        self.desc = desc
        self.default = default

def export_libraries(libraries: Dict[str, Library]):
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
    
    def extract_resolvable(value) -> bool:
        return getattr(value, '_resolvable', False)

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

    docs: Dict[str, LibraryDoc] = {}

    for name, item in libraries.items():
        items = item.export()
        doc = LibraryDoc(
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
                    return_type = extract_return_type(value.__doc__),
                    resolvable = extract_resolvable(value)
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
    for library_name, library_doc in docs.items():
        output = ""
        output += f"# Library: {markdown_escape(library_name)}\n"
        output += "---\n"
        #output += make_navbar([name.name for name in library_doc.methods]) + "\n"
        if library_doc.permissions:
            output += "\n**Requires Permissions:**[" + ", ".join(f"`{perm}`" for perm in library_doc.permissions) + "]\n"
        desc = library_doc.description or "\n_No description provided._"
        output += f"{desc}\n"
        for method in library_doc.methods:
            signature = f"`{method.name}("
            params = [name for name in method.parameters.keys()] if method.parameters else []
            if method.kwargs:
                params.append("**kwargs")
            output += f"## {signature}{', '.join(params)})`\n\n"
            mdesc = (method.description or "_No description provided._") + "\n\n"
            output += f"> {mdesc}\n"
            if method.parameters:
                output += "#### **Parameters:**\n\n"
                output += "| Name | Type | Default |\n"
                output += "| ---- | ---- | ------- |\n"
                for pname, pval in method.parameters.items():
                    output += f"| {pname} | `{pval.type}` | {pval.default or ''} |\n"
            if method.kwargs:
                output += "#### **Kwargs:**\n\n"
                output += "| Name | Type | Default |\n"
                output += "| ---- | ---- | ------- |\n"
                for kname, kval in method.kwargs.items():
                    output += f"| {kname} | `{kval.type}` | {kval.default or ''} |\n"
            output += f"\n#### **Returns:**\n\n" + (f"*{method.return_type}*" if method.return_type else "_None_")
            output += "\n\n"
            if method.resolvable:
                output += "?> This method can be pure.\n\n"
            output += "\n\n"
        output += "\n---\n"
        markdown[library_name] = output

    # generate pages
    for name, doc in markdown.items():
        with open(f"{PATH}{name}.md", "w", encoding="utf-8") as f:
            f.write(doc)
        print(f"Library {name} generated at {PATH}{name}.md")

    # generate sidebar
    with open(f"{PATH}_sidebar.md", "w", encoding="utf-8") as f:
        f.write('<div><a href="./" style="text-decoration: none; color: inherit;">\n<center><img src="sas.svg" alt="drawing" width="128" />\n</a></div>\n\n---\n\n- [Libraries](libraries/home.md)\n')
        for name in markdown.keys():
            f.write(f"- [{name}](libraries/{name}.md)\n")
    print(f"Sidebar generated at {PATH}_sidebar.md")

if __name__ == "__main__":
    from game.libraries import import_libraries
    libraries = import_libraries({})
    export_libraries(libraries)