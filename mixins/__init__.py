from typing import List, Dict, Set, Any

class Taggable:
  """A mixin class that provides tagging functionality to any class that inherits from it.
    It allows adding, removing, and checking for tags. Tags are stored as a list of strings."""
  def __init__(self, tags: Set[str] | None = None, **kwargs):
    self.tags = tags or set()
    if not isinstance(self.tags, set):
      raise TypeError("Tags must be a set of strings.")
    super().__init__(**kwargs)

  def add_tag(self, *tag: str):
    for t in tag:
      if t not in self.tags:
        self.tags.add(t)

  def remove_tag(self, *tag: str):
    for t in tag:
      if t in self.tags:
        self.tags.remove(t)

  def has_tag(self, tag: str) -> bool:
    return tag in self.tags

  def intersection(self, tags: Set[str]) -> Set[str]:
    """Returns the intersection of tags with another set."""
    return self.tags.intersection(tags)

  def union(self, tags: Set[str]) -> Set[str]:
    """Returns the union of tags with another set."""
    return self.tags.union(tags)

  def difference(self, tags: Set[str]) -> Set[str]:
    """Returns the difference of tags with another set."""
    return self.tags.difference(tags)