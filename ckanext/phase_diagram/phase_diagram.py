"""Stability diagram for HydroGEN project.
Peggy Li, li54@llnl.gov

Data from:
Pohl, Johan, and Karsten Albe. "Intrinsic point defects in CuInSe 2 and CuGaSe
2 as seen via screened-exchange hybrid density functional theory." Physical
Review B 87.24 (2013): 245203.
"""

from polyhedron import interior_point, ConvexPolyhedron
from vector_helpers import points_on_lines
import re
import numpy as np
from collections import OrderedDict


class Compound(object):
  def __init__(self, formula_dict, enthalpy_of_formation):
    self.formula = formula_dict
    self.elements = formula_dict.keys()
    self.hf = enthalpy_of_formation

  @property
  def molecular_formula(self):
    s = ""
    for ele, num in self.formula.iteritems():
      if num == 1:
        s+=ele
      else:
        s += ele + str(num)
    return s

  def num(self, element):
    try:
      return self.formula[element]
    except KeyError:
      return 0

  @staticmethod
  def parse_string_to_dict(c):
    pattern = re.compile(r'([A-Z][a-z]*)([0-9]*)')
    element_nums = pattern.findall(c)
    d = OrderedDict()
    for ele, num in element_nums:
      if num == "":
        num = 1
      else:
        num = int(num)
      d[ele] = num
    return d

  @staticmethod
  def from_list(l):
    """list/tuple like ["CuInSe2", 0.6]"""
    d = Compound.parse_string_to_dict(l[0])
    return Compound(d, float(l[1]))

  @staticmethod
  def from_string(s):
    c, h = s.split(" ")
    h = float(h)
    d = Compound.parse_string_to_dict(c)
    return Compound(d, h)

  def __repr__(self):
    return self.molecular_formula

  def __eq__(self, other):
    return self.formula == other.formula

  def __ne__(self, other):
    return not(self.__eq__(other))


class CompoundNotInDiagram(Exception):
  pass


class StabilityDiagram(object):
  _n_elements = 3

  def __init__(self, compound_of_interest, compounds, elements,  bounds):
    # elements is list of elements present in order of axis, last one is the one left out
    self.main_compound = compound_of_interest

    self.elements = elements
    axis_compounds = elements[:-1]
    # The element that is not included in the graph, and is determined by the compound of interest
    # IE, if CuInSe2 was the main compound and the axis are delta mu Cu and delta mu In
    # the graph will be on the plane for which delta mu Se is constrained by
    # delta mu Cu + delta mu In + 2 * delta mu Se = -2.37
    self.sub_el = elements[-1]
    self.sub_ind = len(elements) - 1 # self.elements.index(self.sub_el)

    # Exclude the single elements that aren't the substituted element
    self.compounds = compounds
    self.present_compounds = [c for c in compounds if c.molecular_formula not in axis_compounds]

    # TODO: less hackish. 'equations' variable in addition to compounds
    # bounds is brittle. Assumes a halfspace that goes from negative towards the zero
    # for the left/bottom bounds of a graph
    for c, bound in zip(axis_compounds, bounds):
      self.compounds.append(Compound({c: -1}, -bound))

    self.validate_axis(axis_compounds)
    self.x_el, self.y_el = axis_compounds
    col_i = {(el, i) for i, el in enumerate(self.elements)}

  def get_elements(self, compounds):
    coms = set()
    for c in compounds:
      coms.update(c.elements)
    if len(coms) != self._n_elements:
      raise Exception("Number of different elements in compound list != {0}. StabilityDiagram only configured for {0}".format(self._n_elements))
    return list(coms)

  def validate_axis(self, axis_compounds):
    assert len(axis_compounds) == self._n_elements - 1
    for a in axis_compounds:
      assert a in self.elements

  def get_regions(self):
    """Return dict of polyhedrons for each region"""
    res = {}
    for compound in self.present_compounds:
      res[str(compound)] = self.get_region(compound)
    return res

  def get_region(self, compound):
    """Get a polyhedron representing the region of stability for this phase. Doesn't have to be a bound region"""
    if compound not in self.present_compounds:
      raise CompoundNotInDiagram
    hs = self.halfspaces(compound)
    return ConvexPolyhedron(vertices=None, halfspaces=hs)

  # TODO: move
  def sub_equation_coefficients(self, compound):
    offset = compound.hf
    coeffs = [compound.num(el) for el in self.elements]
    orig_sub_coeff = coeffs[self.sub_ind]
    del coeffs[self.sub_ind]

    # A vector of the coefficients of the right-hand side of the equation solved for the sub_element
    # If the sub element is Se, the 3rd element
    # [-c1/c3 -c2/c3 b] such that if x=[c1 c2 c3] and Vx-b = 0. ie c1*x1 + c2*x2 + c3*x3 = b,
    # ie x3 = -c1/c3*x1 - c2/c3*x2 + b

    # 2*d_mu(Cu) + d_mu(In) + 2*d_mu(Se) = -42
    # transformed to
    # d_mu(Se) = -1*d_mu(Cu) -0.5*d_mu(In) - 21
    # gives the vector
    # [-1 -0.5 -21]
    sub_eq_coeffs = np.array(coeffs) * -1
    sub_eq_coeffs = np.append(sub_eq_coeffs, [offset])
    print 'sub_eq_coeff size', sub_eq_coeffs.size
    if orig_sub_coeff == 0:
      sub_eq_coeffs = np.zeros(sub_eq_coeffs.size)
    else:
      sub_eq_coeffs = sub_eq_coeffs / orig_sub_coeff
    #sub_eq_coeffs = sub_eq_coeffs.reshape((1, len(self.elements)))
    return sub_eq_coeffs

  def halfspaces(self, compound, other_compounds=None):
    # TODO: warning and skip when other compound isn't even on this plane
    # example: sd.halfspaces(Cu compound). Se... messes things up
    if other_compounds is None:
      other_compounds = [c for c in self.compounds if c != compound]

    sub_eq_coeffs = self.sub_equation_coefficients(compound)

    # Get the normals of the equilibrium lines between the compound of interest and all other compounds
    # m by n matrix, m = # other compounds, n = # elements in all compounds
    # Will remove the column w/ the sub element???
    normal_vectors = []
    offsets = []
    for c in other_compounds:
      normal_vectors.append([c.num(el) for el in self.elements])
      offsets.append(-1 * c.hf)
    normal_vectors = np.array(normal_vectors)
    offsets = np.array(offsets).reshape((len(offsets), 1))
    # Remove sub element dimension. We then work on the plane defined by c1*x1 + c2*x2 + c3*x3 = b
    m = len(other_compounds)
    n = len(self.elements) - 1
    slice_index = list(range(n + 1))
    slice_index.remove(self.sub_ind)

    sub_coeffs = normal_vectors[:, self.sub_ind].reshape((m,1))
    assert sub_coeffs.shape == (m, 1)
    normal_vectors = normal_vectors[:, slice_index]
    assert normal_vectors.shape == (m, n)
    # a is a m by (n+1) matrix
    # [[c1 c2 b] [...]] from c1*d_mu(x1) + c2*d_mu(x2) + c3*d_mu(x3) <= -b = enthalpy of formation
    # (eq. 1) c1*d_mu(x1) + c2*d_mu(x2) + c3*d_mu(x3) <= -b = enthalpy of formation
    # and c3*d_mu(x3) is substituted out using the compound of interest's formula
    a = np.concatenate((normal_vectors, offsets), axis=1)
    a = a + sub_coeffs*sub_eq_coeffs

    # Make sure normal vector points in direction indicated by the halfspace from eq. 1
    # Find a point on the hyperplane, offset by normal vector, see if result in the halfspace
    # Point intersecting with the unit vector
    normal_vectors = a[:, :-1]
    assert normal_vectors.shape == (m, n)
    ps_on_lines = points_on_lines(a)

    assert ps_on_lines.shape == normal_vectors.shape == ps_on_lines.shape
    points = ps_on_lines + -normal_vectors
    # Check if point satisfies inequality
    dot_products = np.sum(points * normal_vectors, axis=1).reshape(m)
    in_halfspace = dot_products <= (-1*a[:, -1])
    # Flip vectors/points that don't satisfy inequality
    a[~in_halfspace] *= -1

    return a

####################################
# helpers
####################################
def parse_compounds(compounds):
  """
  Returns list of Compounds. Can accept list of dicts like {"Cu": 1, "In": 1, "Se": 2, "dHf": -2.37}
  or list of strings "CuInSe2 -2.37"
  or lists of tuples like [("CuInSe2", -2,37)]
  :param compounds:
  :type compounds: List[OrderedDict] or List[str]
  """
  compound_list = []
  # Make sure to deal with "" or [None, None], for example. In case the data comes with extraneous empty values...
  if isinstance(compounds[0], str):
    for c in compounds:
      if c.strip():
        compound_list.append(Compound.from_string(c))
  elif isinstance(compounds[0], tuple) or isinstance(compounds[0], list):
    for c in compounds:
      if any(c):
        compound_list.append(Compound.from_list(c))
  else:
    for c in compounds:
      h = float(c["dHf"])
      del c["dHf"]
      compound_list.append(Compound(c, h))
  return compound_list


def select_compounds(compounds, accepted_elements):
  """
  Return only the compounds whose elements are one of the elements of interest
  :param compounds: List of Compounds
  :type compounds: List[Compound]
  :param elements: Elements of interest
  :type elements: List[str]
  """
  return filter(lambda c: set(c.elements).issubset(accepted_elements), compounds)

def plot(halfspaces, poly):
  """Fill in the spaces opposite of the halfspaces"""
  # https://docs.scipy.org/doc/scipy-0.19.1/reference/generated/scipy.spatial.HalfspaceIntersection.html
  import matplotlib.pyplot as plt
  fig = plt.figure()
  ax = fig.add_subplot('111', aspect='equal')
  ax.xaxis.set_ticks_position("top")
  ax.yaxis.set_ticks_position("right")
  xlim, ylim = (-3, 1), (-3, 1)
  ax.set_xlim(xlim)
  ax.set_ylim(ylim)
  x = np.linspace(-3, 0, 100)
  n_halfspaces = len(halfspaces)
  symbols = ['-', '+', 'x', '*', '\\', 'o', 'O', '.']
  symbols = symbols*(n_halfspaces/len(symbols)+1)
  signs = [0, 0, -1, -1]
  fmt = {"color": None, "edgecolor": "b", "alpha": 0.3}
  for h, sym in zip(halfspaces, symbols):
    hlist = h.tolist()
    fmt["hatch"] = sym
    if h[1] == 0:
      ax.axvline(-h[2] / h[0], label='{}x+{}y+{}=0'.format(*hlist))
      if h[0] > 0:
        fill_to = ylim[-1]
      else:
        fill_to = ylim[0]
      xi = np.linspace(fill_to, -h[2] / h[0], 100)
      ax.fill_between(xi, ylim[0], ylim[1], **fmt)
    else:
      # h = [c_x, c_y, b]?? c_x*x +c_y*y + b = 0
      # if c_y=1, c_x*x + y + b = 0, y = -c_x*x - b
      # (-b - c_x*x) / c_y = y
      ax.plot(x, (-h[2] - h[0] * x) / h[1], label='{}x+{}y+{}=0'.format(*hlist))
      # Normal points to exterior of halfspace... fill in the exterior
      if h[1] > 0:
        fill_to = ylim[-1]
      else:
        fill_to = ylim[0]
      ax.fill_between(x, (-h[2] - h[0] * x) / h[1], fill_to, **fmt)
  #x, y = zip(*hsi.intersections)
  #feasible_point = interior_point(halfspaces)
  #x = x + (feasible_point[0],)
  #y = y + (feasible_point[1],)
  x, y = poly.vertices[:, 0], poly.vertices[:, 1]
  ax.plot(x, y, 'o', markersize=5)
  plt.show()


def plot_compounds(compound, compounds):
  sd = StabilityDiagram(compound, compounds, ["Cu", "In"], [-3, -3])
  #halfspace_intersection = sd.get_halfspace_intersection()
  other_compounds = [c for c in compounds if c != compound]
  halfspaces = sd.halfspaces(compound, other_compounds)
  poly = sd.get_region(compound)
  #halfspaces, hsi = sd.get_halfspace_intersection(compound)
  plot(halfspaces, poly)

def plot_regions(compound, compounds, axis, bounds):
  sd = StabilityDiagram(compound, compounds, axis, bounds)
  #sd.get_region(Compound.from_string("Cu 0"))
  regions = sd.get_regions()
  rr = regions[str(compound)]
  print rr.is_interior((-0.0, -0.34))
  print rr.is_interior((-0.2, -0.1))
  import matplotlib.pyplot as plt
  fig = plt.figure()
  ax = fig.add_subplot('111', aspect='equal')
  ax.xaxis.set_ticks_position("top")
  ax.yaxis.set_ticks_position("right")
  xlim, ylim = (-2.6, 0.3), (-2.6, 0.3)
  ax.set_xlim(xlim)
  ax.set_ylim(ylim)
  ax.xaxis.set_ticks(np.arange(xlim[0], xlim[1], 0.2))
  ax.yaxis.set_ticks(np.arange(ylim[0], ylim[1], 0.2))
  ax.tick_params(axis="both", which="major", labelsize=8)
  ax.tick_params(axis="both", which="minor", labelsize=8)
  for c, polygon in regions.iteritems():
    vertices = polygon.vertices
    if vertices.size:
      vertices = np.vstack((vertices, vertices[0, :]))
      x = vertices[:, 0]
      y = vertices[:, 1]
      ax.plot(x, y, '.', linestyle="solid", markersize=2, label=c)

  points = [
    #[-0.5, -1.87],
    [-0.55, -1.8],
    [-0.1, -1.3],
    [-0.4, -1.],
    [-0.0, -0.2],
    [-0.0, -0.9],
    #[-0.4, -2.],
    [-0.3, -1.6],
  ]
  points = np.array(points)
  ax.plot(points[:,0], points[:,1], "bo")

  box = ax.get_position()
  ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])

  # Put a legend to the right of the current axis
  ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
  #legend = ax.legend(loc='upper left', shadow=True)
  plt.show()

if __name__ == "__main__":
  compounds = [
    "CuInSe2 -2.37",
    "CuGaSe2 -2.67",
    "CuIn5Se8 -9.37",
    "CuGa5Se8 -10.96",
    "CuSe -0.53",
    "Cu2Se -0.68",
    "Cu3Se2 -1.12",
    "InSe -1.28",
    "In2Se3 -3.25",
    "In4Se3 -3.55",
    "GaSe -1.47",
    "Ga2Se3 -3.62",
    "Ga 0",
    "Cu 0",
    "In 0",
    "Se 0",
  ]

  compounds_expt = [
    "CuInSe2 -2.12",
    "CuGaSe2 -2.75",
    "CuIn5Se8 -9.37", # hse06
    "CuGa5Se8 -10.96", # hse06
    "CuSe -0.42",
    "Cu2Se -0.61",
    "Cu3Se -1.03",
    "InSe -1.22",
    "In2Se3 -3.57",
    "In4Se3 -3.79",
    "GaSe -1.65",
    "Ga2Se3 -4.56",
    "Ga 0",
    "Cu 0",
    "In 0",
    "Se 0",
  ]
  compounds_gga = [
    "CuInSe2 -1.79",
    "CuGaSe2 -2.33",
    "CuIn5Se8 -7.04",
    "CuGa5Se8 -7.97",
    "CuSe -0.27",
    "Cu2Se -0.02",
    "Cu3Se2 -0.58",
    "InSe -1.05",
    "In2Se3 -2.46",
    "In4Se3 -3.09",
    "GaSe -1.14",
    "Ga2Se3 -2.99",
    "Ga 0",
    "Cu 0",
    "In 0",
    "Se 0",
  ]

  compounds = parse_compounds(compounds)

  cu_in_se_compounds = select_compounds(compounds, ["Cu", "In", "Se"])

  CuInSe2 = compounds[0]
  # plot_compounds(CuInSe2, cu_in_se_compounds )
  plot_regions(CuInSe2, cu_in_se_compounds, ["Cu", "In", "Se"] , [-3, -3])

  #cu_ga_se_compounds = select_compounds(compounds, ["Cu", "Ga", "Se"])
  #CuGaSe2 = compounds[1]
  #plot_regions(CuGaSe2, cu_ga_se_compounds, ["Cu", "Ga", "Se"], [-2.7, -2.7])
