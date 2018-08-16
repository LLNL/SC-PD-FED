from itertools import combinations
from math import atan2, sqrt

import numpy as np
from numpy.linalg import LinAlgError
from scipy.optimize import linprog
from scipy.spatial.qhull import HalfspaceIntersection, QhullError
from scipy.spatial import ConvexHull


class ConvexPolyhedron(object):
  def __init__(self, vertices=None, halfspaces=None):#, bounded=True):
    if vertices is not None:
      vertices = np.array(vertices)
    if halfspaces is not None:
      halfspaces = np.array(halfspaces)
    if halfspaces is not None:
      self.halfspaces = halfspaces
      try:
        feasible_point = interior_point(halfspaces)
        hsi = HalfspaceIntersection(halfspaces, feasible_point) # can throw QHullError
        self.vertices = hsi.intersections
        self.fromwhich = "halfspace qhull"
      except (CantFindInteriorPoint, QhullError):
        self.bounded = False
        self.vertices = self.feasible_vertices(halfspaces)
        self.fromwhich = "halfspace intersections (feasible_vertices)"
      if vertices is not None:
        if not np.array_equal(np.sort(self.vertices, axis=0), np.sort(vertices, axis=0)):
          raise Exception("provided vertices and halfspaces do not match")
    elif vertices is not None:
      self.halfspaces = halfspaces
      self.vertices = vertices
      self.fromwhich = "vertices"
      # TODO: some check for convexity?
    if self.vertices is not None and len(self.vertices):
      self.hull = ConvexHull(self.vertices)

  def __repr__(self):
    s = "From {}\nVertices:\n{}\nHalfspaces:\n{}\n".format(self.fromwhich, self.vertices, self.halfspaces)
    return s

  def is_interior(self, point):
    # Return true if point is on or interior of region boundaries, using self.vertices as the region boundary, assuming convex
    # Using self.hull.equations instead of self.halfspaces b/c self.halfspaces has those extra halfspaces inside
    point = np.array(point)
    tolerance = 1e-12
    A = self.hull.equations[:, :-1]
    b = self.hull.equations[:, -1]
    return np.all(np.dot(A, point) + b <= tolerance) 

  @staticmethod
  def feasible_vertices(halfspaces):
    """Get intersections of all hyperplanes, then make sure they're feasible"""
    # linalg solve Ax=b
    # halfspaces are c1x1+c2x2+c3 <= 0
    A = halfspaces[:, :-1]
    b = -halfspaces[:, -1]
    Ab = zip(A,b)
    dim = A.shape[-1]
    vertices = []
    for (ab1, ab2) in combinations(Ab,dim):
      try:
        v = np.linalg.solve(np.vstack([ab1[0], ab2[0]]), [ab1[1], ab2[1]])
        vertices.append(v)
      except LinAlgError:
        continue
    vertices = np.array(vertices)
    # feasibility for each halfspace (maybe that's not how you're supposed to use the word lol)
    bp = A.dot(vertices.T)
    feasibility = np.logical_or(bp <= b.reshape((b.size,1)), np.isclose(bp, b.reshape((b.size,1))))
    assert feasibility.shape == (halfspaces.shape[0],vertices.shape[0])
    # feasibility for all halfspaces
    feasibility = np.all(feasibility, axis=0)

    # Graham scan to order the vertices
    vertices = vertices[feasibility]
    return ConvexPolyhedron.graham_scan(vertices)

  @staticmethod
  def graham_scan(vertices):
    """Use graham scan to order the vertices in ccw order"""
    # https://en.wikipedia.org/wiki/Graham_scan
    def ccw(p1, p2, p3):
      # Three points are a counter-clockwise turn if ccw > 0, clockwise if
      # ccw < 0, and collinear if ccw = 0 because ccw is a determinant that
      # gives twice the signed  area of the triangle formed by p1, p2 and p3.
      return (p2[0] - p1[0])*(p3[1] - p1[1]) - (p2[1] - p1[1])*(p3[0] - p1[0])

    def polar_angle(v):
      vp = v - lowest_v
      return atan2(vp[1], vp[0])

    def square_dist(v):
      vp = v - lowest_v
      return sqrt(vp[0]**2 + vp[1]**2)

    def sort_key(v):
      # Compare by polar angle, and distance if equal angle
      angle = polar_angle(v)
      vp = v - lowest_v
      dist = sqrt(vp[0]**2 + vp[1]**2)
      return polar_angle, dist

    n = vertices.shape[0]
    if n < 3:
      return vertices

    lowest_v, lowest_vi = vertices[0], 0
    for vi, v in enumerate(vertices[1:]):
      if np.isclose(lowest_v[1], v[1]):
        if v[0] < lowest_v[0]:
          lowest_v = v
          lowest_vi = vi + 1
      elif v[1] < lowest_v[1]:
        lowest_v = v
        lowest_vi = vi + 1

    temp_v = np.copy(vertices)
    temp_v[0] = vertices[[lowest_vi]]
    temp_v[lowest_vi] = vertices[[0]]
    vertices = temp_v
    other_v = vertices[1:]
    angles = np.array([[polar_angle(v) for v in other_v]]).T
    dist = np.array([[square_dist(v) for v in other_v]]).T
    other_v = np.hstack((angles, dist, other_v))
    sorted_v = other_v[other_v[:,1].argsort()]
    sorted_v = sorted_v[sorted_v[:,0].argsort()]
    keep_v = []
    last_v = sorted_v[0]
    #for v in sorted_v[1:]:
    #  if v[0] == last_v[0] and v[1] > last_v[1]:
    #    last_v = v
    #  elif v[0] != last_v[0]:
    #    keep_v.append(v)
    sorted_other_v = np.array(sorted_v)[:, 2:]
    if other_v.shape[0] < 2:
      raise Exception("< 3 vertices (of different polar angle)")
    output_v = [lowest_v, sorted_other_v[0], sorted_other_v[1]]
    for v in sorted_other_v[2:]:
      if ccw(output_v[-2], output_v[-1], v) <= 0: # clockwise
        del output_v[-1]
      output_v.append(v)
    return np.array(output_v)


class CantFindInteriorPoint(Exception):
  pass


def interior_point(halfspaces, bounds=((None, 0), (None, 0), (None, None))):
  # The Chebyshev center (center of maximum inscribed circle)
  # https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.HalfspaceIntersection.html#r395
  # Things tried and failed? least square error, http://www.geom.uiuc.edu/software/qhull/html/qhalf.htm#notes
  norm_vector = np.reshape(np.linalg.norm(halfspaces[:, :-1], axis=1),
                           (halfspaces.shape[0], 1))
  c = np.zeros((halfspaces.shape[1],))
  c[-1] = -1
  A = np.hstack((halfspaces[:, :-1], norm_vector))
  b = - halfspaces[:, -1:]
  res = linprog(c, A_ub=A, b_ub=b, bounds=bounds)
  ip = res.x[:-1]
  # Check it's actually interior, not on perimeter
  valid = halfspaces[:, :-1].dot(ip) < b
  if np.all(valid):
    return ip
  else:
    raise CantFindInteriorPoint


if __name__ == "__main__":
  v = np.array([[1, 1], [5, 3], [3, 2], [2, 6]])
  vs = ConvexPolyhedron.graham_scan(v)
