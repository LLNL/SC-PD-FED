import numpy as np


def perpendicular(v):
  # Only for 2d vectors, sigh
  assert v.shape == (2,) or v.shape == (1,2)
  if v[0] == 0 and v[1] == 0:
    raise ValueError("zero vector")
  if v[0] == 0:
    return np.array([1,0])
  elif v[1] == 0:
    return np.array([0,1])
  else:
    # Satisfy mx+b=y, for m=1, b=0
    return np.array([v[1], -v[0]])


def points_on_lines(hyperplanes):
  """Given rows of normal vectors to line L, return points (rows) that are somewhere on each line
  Just find intersection with some basis line.
  """
  intersections = []
  for row in hyperplanes:
    intersections.append(an_intersection(row[:-1], -row[-1]))
  return np.array(intersections)


def an_intersection(v1, b1):
  """Get intersection with some basis line"""
  try:
    return intersection(v1, b1, np.array([1,1]), 0)
  except np.linalg.linalg.LinAlgError:
    print v1
    return intersection(v1, b1, np.array([-1,1]), 0)


def intersection(v1, b1, v2, b2):
  # TODO: just let this raise LinAlgError or return None?
  a = np.array([v1, v2])
  b = np.array([b1, b2])
  # solves ax=b
  return np.linalg.solve(a,b)

def intersection2(vs, bs):
  a = np.array(vs)
  b = np.array(bs)
  # solves ax=b
  return np.linalg.solve(a,b)

