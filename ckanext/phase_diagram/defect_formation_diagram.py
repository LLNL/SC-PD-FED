import numpy as np
from numpy.linalg import LinAlgError

import vector_helpers
import itertools


class DefectFormationEnergyDiagram(object):
  def __init__(self, data, chemical_potentials, charges, fermi_energy_bounds):
    # data is a dict with defect name as keys, and [(charge coefs), and (defect formation energies)] as the values
    for name, coefs_dfes in data.iteritems():
      data[name] = [map(int, coefs_dfes[0]),
              map(lambda x: float(x) if x is not None else x, coefs_dfes[1])]
    self.data = data
    self.chemical_potentials = np.array(chemical_potentials)
    self.charges = charges
    self.fermi_energy_bounds = fermi_energy_bounds

  def get_equations(self, coefs_dfes):
    # Return (A, b) s.t. Ax=b
    # The equation we have is
    # formation energy = formation energy when ef = 0, delta = 0 - sum(# atoms element added * chemical potential of element) + qEf
    # I.E.
    # y = defect_formation_energy - coefs * chemical_potential + charge * x
    # rewritten to
    # - charge * x + y = defect_formation_energy - coefs * chemical_potential
    coefs = np.array(coefs_dfes[0])
    defect_formation_energies = coefs_dfes[1]
    A = []
    b = []
    for dfe, charge in zip(defect_formation_energies, self.charges):
      if dfe is None:
        continue
      A.append([-charge, 1])
      b.append(dfe - np.sum(coefs * self.chemical_potentials))
    return np.array(A), np.array(b)

  def get_lowest_points(self):
    res = {}
    for name, coefs_dfes in self.data.iteritems():
      A, b = self.get_equations(coefs_dfes)
      res[name] = self.find_lowest_lines_points(A, b, self.fermi_energy_bounds)["points"]
    return res

  def find_intrinsic_fermi_level(self):
    """Just find intersections of all pos and neg slope lines"""
    # TODO: do some accessor/cache thing to save result of find_lowest_lines_points
    lowest_points = {}
    lowest_lines = {}
    for name, coefs_dfes in self.data.iteritems():
      A, b = self.get_equations(coefs_dfes)
      r = self.find_lowest_lines_points(A, b, self.fermi_energy_bounds)
      lowest_points[name] = r["points"]
      lowest_lines[name] = r["lines"]

    startx, endx = self.fermi_energy_bounds
    pos = {}
    neg = {}
    for name, coefs_dfes in self.data.iteritems():
      #pos_coefs_dfes = [coefs_dfes[i] for i in pos_positions]
      #neg_coefs_dfes = [coefs_dfes[i] for i in neg_positions]
      #pA, pb = self.get_equations(pos_coefs_dfes)
      #nA, nb = self.get_equations(neg_coefs_dfes)
      charges = [self.charges[i] for i, e in enumerate(coefs_dfes[1]) if e is not None]
      pos_positions = [i for i, c in enumerate(charges) if c > 0]
      neg_positions = [i for i, c in enumerate(charges) if c < 0]
      A, b = self.get_equations(coefs_dfes)
      inds = np.arange(len(charges))
      pA, pb, pi = A[pos_positions,:], b[pos_positions], inds[pos_positions]
      nA, nb, ni = A[neg_positions,:], b[neg_positions], inds[neg_positions]
      pos[name] = (pA, pb, pi)
      neg[name] = (nA, nb, ni)
    # Find intersections of lines
    intersections = []
    #pflat = [(name, eq) for name, value in pos.iteritems() for eq in value]
    #nflat = [(name, eq) for name, value in neg.iteritems() for eq in value]
    pflat = [(name, value[2][i], (value[0][i], value[1][i])) for name, value in pos.iteritems() for i in range(len(value[0]))]
    nflat = [(name, value[2][i], (value[0][i], value[1][i])) for name, value in neg.iteritems() for i in range(len(value[0]))]
    for pos_neg in itertools.product(pflat, nflat):
      ((pname, pi, peq), (nname, ni, neq)) = pos_neg
      try:
        pcpos = lowest_lines[pname].index(pi)
        ncpos = lowest_lines[nname].index(ni)
        try:
          i = vector_helpers.intersection(peq[0], peq[1], neq[0], neq[1])
          # Is valid? Check if the intersection falls on the section that is 'lowest'
          pcharge = peq[0][0]
          ncharge = neq[0][0]
          # in the right segments by x axis
          good = lowest_points[pname][pcpos][0] <= i[0] <= lowest_points[pname][pcpos+1][0] and \
            lowest_points[nname][ncpos][0] <= i[0] <= lowest_points[nname][ncpos+1][0]
          if good:
            intersections.append(i)
        except LinAlgError:
          continue
      except ValueError:
        continue
    # Lowest intersection
    if len(intersections) > 0:
      return min(intersections, key=lambda i: i[1])
    else:
      return None

  @staticmethod
  def find_lowest_lines_points(A, b, domain):
    """Get np array of lowest points sorted by x"""
    # Ax=b
    # ASSUME NO LINES OF SAME SLOPE
    # Go from left to right
    startx, endx = domain
    curx = startx
    res = []
    # TODO: sympy?
    # TODO: rename b and bb
    c = -A[:, 0] / A[:, 1]
    bb = b / A[:, 1]
    ys = c * curx + bb
    min_eq = np.argmin(ys)
    cury = ys[min_eq]
    vertices = [np.array([curx, cury])]
    lines = [min_eq]

    while True:
      #other_inds = np.arange(A.shape[0]) != min_eq
      intersections = []
      for i in range(A.shape[0]):
        if i != min_eq:
          intersections.append(vector_helpers.intersection(A[min_eq], b[min_eq], A[i], b[i]))
        else:
          intersections.append(None)
      on_right_in_domain = []
      for intersection in intersections:
        if intersection is not None and intersection[0] > curx and intersection[0] <= endx:
          on_right_in_domain.append(True)
        else:
          on_right_in_domain.append(False)
      if not len(filter(None, on_right_in_domain)):
        break

      # Minimum x
      miny = float("inf")
      minx = float("inf")
      mini = None
      for i, intersection in enumerate(intersections):
        if intersection is not None and on_right_in_domain[i] and intersection[0] < minx:
          minx = intersection[0]
          mini = i
      min_eq = mini
      lines.append(min_eq)
      cur = curx, cury = intersections[min_eq]
      if curx < endx:
        vertices.append(cur)

    if endx != vertices[-1][0]:
      endy = c[min_eq] * endx + bb[min_eq]
      vertices.append(np.array([endx, endy]))

    return {"points": np.array(vertices),
            "lines": lines}


if __name__ == "__main__":
  charges = [3, 2, 1, 0, -1, -2, -3]
  dfes = {
  "In_Cu": [(-1, 1, 0), [None, -1.01, 0.24, 1.86, None, None, None]],
    "In_DX": [(-1, 1, 0), [None, None, None, 1.61, None, None, None]],
    "V_Cu": [(-1, 0, 0), [None, None, None, None, 1.19, None, None]],
    "Cu_In": [(1, -1, 0), [None, None, None, 2.08, 2.22, 2.84, None]],
    "V_In": [(0, -1, 0), [None, None, None, 3.85, 3.88, 4.3, 4.99]],
    "V_Se": [(0, 0, -1), [None, 2.39, None, 2.45, 3.43, 4.78, 5.66]],
    "Cu_i": [(1, 0, 0), [None, None, 0.17, 1.68, None, None, None]],
    "In_i": [(0, 1, 0), [0.60, 0.95, 1.43, 2.84, None, None, None]],
    "Se_i": [(0, 0, 1), [None, 2.48, 2.67, 2.87, 3.51, 4.87, None]],
    "In_Cu-2V_Cu": [(-1+(-2), 1, 0), [None, None, None, 1.07, None, None, None]],
    "V_Se-V_Cu": [(-1, 0, -1), [None, None, 2.9, None, 3.47, 4.33, 5.66]],
  }

  points = [
    #[-0.5, -1.87],
    [-0.55, -1.8],
    [-0.1, -1.3],
    [-0.4, -1.],
    [-0.0, -0.2],
    [-0.0, -0.9],
    #[-0.4, -2.],
    [-0.3, -1.6],
    [-0.15, -1.3]
  ]
  mu_cu, mu_in = points[-1]
  mu_cu, mu_in = -0.3, -1 # -0.5, -1.87
  mu_se = (-2.37 - mu_cu - mu_in) / 2.0
  chemical_potentials = np.array([mu_cu, mu_in, mu_se])
  fermi_energy_lim = [0, 1]

  diagram = DefectFormationEnergyDiagram(dfes, chemical_potentials, charges, fermi_energy_lim)

  import matplotlib.pyplot as plt

  fig = plt.figure()
  ax = fig.add_subplot('111', aspect='equal')
  #ax.xaxis.set_ticks_position("top")
  #ax.yaxis.set_ticks_position("right")
  xlim, ylim = (-.2, 1.6), (-1.5, 4)
  ax.set_xlim(xlim)
  ax.set_ylim(ylim)
  #for name, coef_energy in dfes.iteritems():
  #  for charge, energy in zip(charges, coef_energy[1]):
  #    coef = coef_energy[0]
  #    if energy is not None:
  #      x = [0, 1]
  #      y0 = energy - (mu_cu*coef[0] + mu_in*coef[1]) + charge*x[0]
  #      y1 = energy - (mu_cu*coef[0] + mu_in*coef[1]) + charge*x[1]
  #      y = [y0, y1]
  #      ax.plot(x, y, '.', linestyle="solid", markersize=2, alpha=0.5, label="{} {}".format(name, charge))
  vert_dict = diagram.get_lowest_points()
  ife = diagram.find_intrinsic_fermi_level()
  ax.plot(ife[0], ife[1], '.', markersize="10")
  for name, vertices in vert_dict.iteritems():
    #A, b = get_equations(coef_energy)
    #vertices = find_lowest_points(A, b, fermi_energy_lim)
    ax.plot(vertices[:, 0], vertices[:, 1], '.', linestyle="solid", linewidth=2, markersize=3, label="{}".format(name))

  box = ax.get_position()
  ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])

  # Put a legend to the right of the current axis
  ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
  #legend = ax.legend()#loc='upper left', shadow=True)
  plt.show()

