def space_joiner(tags):
  names = [t.name for t in tags]
  return " ".join(sorted(names))

