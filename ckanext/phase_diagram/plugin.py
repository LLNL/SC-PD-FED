# encoding: utf-8

from logging import getLogger

import ckan.plugins as p
import ckan.plugins.toolkit as tk
from ckan.common import json
from collections import defaultdict
import re

import phase_diagram
from defect_formation_diagram import DefectFormationEnergyDiagram
from polyhedron import ConvexPolyhedron

#log = getLogger(__name__)
#ignore_empty = p.toolkit.get_validator('ignore_empty')
#natural_number_validator = p.toolkit.get_validator('natural_number_validator')
#Invalid = p.toolkit.Invalid
@tk.side_effect_free
def select_compound(context, data_dict):
  if data_dict.get("material", None):
    if data_dict["material"] == "chalcopyrite":
      if data_dict["property"] != "formation_energy":
        return {"success": False,
            "msg": "Only formation energy supported"}
    else:
      raise NotImplementedError()
    elements_numbers = parse_nested_list("elements_nums", data_dict)
    name = ""
    for ele, num in elements_numbers:
      num = int(num)
      if num > 0:
        name += ele
        if num > 1:
          name += str(num)
    if name not in ["CuInSe2", "CuGaSe2"]:
      return {"success": False,
          "msg": "Selection not supported, only CuInSe2 and CuGaSe2 currently supported"}
    package = tk.get_action("package_show")(data_dict={"id": data_dict["package_id"]})
    pd_resource_id, dfe_resource_id = corresponding_resource_id(name, package)
    return {"pd_resource_id": pd_resource_id,
            "dfe_resource_id": dfe_resource_id,
            "elements_nums": elements_numbers}
  else:
    raise Exception()
@tk.side_effect_free
def phase_diagram_view(context, data_dict):
  # Example ["Cu", "In", "Se"]
  # TODO: , coords, be passed in by request
  # elements[] bc CKAN controller.api._get_request_data flattens when not POST and side_effect_free. This is dumb.
  elements_nums = parse_nested_list("elements_nums", data_dict)
  elements = [en[0] for en in elements_nums]
  name = ""
  for ele, num in elements_nums:
    num = int(num)
    if num > 0:
      name += ele
      if num > 1:
        name += str(num)
  if data_dict.get("resource_id", None):
    pd_resource_id = data_dict["resource_id"]
  else:
    package = tk.get_action("package_show")(data_dict={"id": data_dict["package_id"]})
    pd_resource_id, _ = corresponding_resource_id(name, package)
  data = tk.get_action("datastore_search")(data_dict={"resource_id": pd_resource_id})["records"]
    # Figure out the appropriate resource_id from query data
  compounds = [[d['compound'], d['fe']] for d in data]
  compounds = phase_diagram.parse_compounds(compounds)
  # Formation energy of the specified compound
  for c in compounds:
    if str(c) == name:
      compound_hf = c.hf
      break
  specified_compounds = phase_diagram.select_compounds(compounds, elements)
  specified_compound = filter(lambda c: str(c) == name, specified_compounds)[0]
  lower_lims = [-3, -3]
  sd = phase_diagram.StabilityDiagram(specified_compound, specified_compounds, elements, lower_lims)

  regions = sd.get_regions()
  regions_l = [{"formula": formula, "vertices": v.vertices.tolist()} for formula, v in regions.iteritems()]

  print "Is compound of interest %s among regions %s" % (specified_compound, str(regions))
  #default_coord = {"x": (lower_lims[0] - 0) / 2.0,
  #                 "y": (lower_lims[1] - 0) / 2.0
  #                 }
  default_coord = {"x": -0.3,
                   "y": -1}
  data = {"regions": regions_l,
          "relevant_region": regions[str(specified_compound)].vertices.tolist(),
          "bounds": [[-3, 0], [-3, 0]],
          "default_coord": default_coord,
          "x_label": "ΔμCu eV",
          "y_label": "ΔμIn eV",
          "compound_formation_energy": compound_hf,
          }
  return data

def parse_nested_list(key, data_dict, cast_to=None):
  # Parse the flattened list of lists flattened curtosy of CKAN's controller.api._get_request_data
  nested_list = []
  # key[] bc CKAN controller.api._get_request_data flattens when not POST and side_effect_free. This is dumb.
  d_lists = filter(lambda x: x.startswith(key+"["), data_dict.keys())
  for i in range(len(d_lists)):
    l = data_dict[key+"["+str(i)+"][]"]
    if cast_to is None:
      nested_list.append(l)
    else:
      l2 = []
      for x in l:
        try:
          l2.append(cast_to(x))
        except ValueError:
          l2.append(x)
      nested_list.append(l2)
  return nested_list

@tk.side_effect_free
def defect_fect_formation_diagram_view(context, data_dict):
  data = tk.get_action("datastore_search")(data_dict={"resource_id": data_dict["resource_id"]})["records"]
  dfes = {}
  for d in data:
    dfes[d["defect"]] = [map(int, (d["c1"], d["c2"], d["c3"])), map(lambda k: float(d[k]) if d.get(k, None) is not None else None, ["e1", "e2", "e3", "e4", "e5", "e6", "e7"])]

  charges = [3, 2, 1, 0, -1, -2, -3]
  # TODO: get default mu, fermi*lim, dfe_lim from somewhere else
  defaults_mu = [-0.7, -0.7]
  # TODO: use validator
  # Example, CuInSe2, mu1 -> Cu, mu2 -> In, mu3 -> Se2, c1=c2=1, c3=2
  elements_numbers = parse_nested_list("elements_nums", data_dict, int)
  # TODO: make this deal with when the unknown chemical isn't always the last
  chemical_potentials = [None]*len(elements_numbers)#["chemical_potentials[]"] # Does nothing rn
  compound_formation_energy = float(data_dict["compound_formation_energy"])
  c = []
  #mus = []
  for ele_num, mu in zip(elements_numbers, chemical_potentials):
    c.append(ele_num[1])
    #mus.append(mu)
  mu1 = float(data_dict.get("x", defaults_mu[0]))
  mu2 = float(data_dict.get("y", defaults_mu[1]))

  # Only continue if the point was in the relevant region, 
  # ie if phase diagram is for CuInSe2, only show dfe if click was in CuInSe2 region
  if data_dict.get("only_relevant") == "true":
    # Is in region?
    relevant_region = parse_nested_list("relevant_region", data_dict, float)
    region = ConvexPolyhedron(vertices=relevant_region)
    is_relevant = region.is_interior((mu1, mu2))
    if not is_relevant:
      return {"status": 1,}

  mu3 = (compound_formation_energy - c[0]*mu1 - c[1]*mu2) / c[2]
  # example, mu_se = (-2.37 - mu_cu - mu_in) / 2
  chemical_potentials = [mu1, mu2, mu3]
  fermi_energy_lim = [0, 1.6]
  fermi_energy_axis_lim = [-0.2, 2]
  dfe_lim = [-0.7, 4]

  diagram = DefectFormationEnergyDiagram(dfes, chemical_potentials, charges, fermi_energy_lim)
  vert_dict = diagram.get_lowest_points()
  ifl = diagram.find_intrinsic_fermi_level().tolist()
  lines = [{"label": k, "vertices": v.tolist()} for k, v in vert_dict.iteritems()]
  data = {"lines": lines,
          "bounds": [fermi_energy_axis_lim, dfe_lim],
          "minor_bounds": [fermi_energy_lim, [0]],  # little gray lines
          "intrinsic_fermi_level": ifl, #[x, y]
          "x_label": "Fermi energy [eV]",
          "y_label": "Formation energy [eV]",
          "status": 0,
          }
  return data

def corresponding_resource_names(resource_name):
  pd_name, dfe_name = (resource_name+"_pd_data.csv", resource_name+"_dfe_data.csv")
  return pd_name, dfe_name

def corresponding_resource_id(base_name, package):
  pd_name, dfe_name = corresponding_resource_names(base_name)
  name_id = {r["name"]: r["id"] for r in package["resources"]}
  pd_resource_id = name_id[pd_name]
  dfe_resource_id = name_id[dfe_name]
  return (pd_resource_id, dfe_resource_id)

class ResourceNotFound(Exception):
  pass

def resource_pair_names(package, num=None):
  """Return (pd_resource_id, dfe_resource_id) of num or all the pairs in this package"""
  name_id = {r["name"]: r["id"] for r in package["resources"]}
  base_names = []
  pairs = []
  count = 0
  for name, id in name_id.iteritems():
    if name.endswith("_pd_data.csv") or name.endswith("_dfe_data.csv"):
      base_name = name.rsplit("_pd_data.csv",1)[0].rsplit("_dfe_data.csv", 1)[0]
      if base_name in base_names:
        pairs.append(base_name)
        if num:
          count += 1
          if count == num:
            break
      base_names.append(base_name)
  return pairs

def resource_pairs(package, num=None):
  """Return (pd_resource_id, dfe_resource_id) of num or all the pairs in this package"""
  name_id = {r["name"]: r["id"] for r in package["resources"]}
  base_names = []
  pairs = []
  count = 0
  for name, id in name_id.iteritems():
    if name.endswith("_pd_data.csv") or name.endswith("_dfe_data.csv"):
      base_name = name.rsplit("_pd_data.csv",1)[0].rsplit("_dfe_data.csv", 1)[0]
      if base_name in base_names:
        pairs.append((name_id[base_name+"_pd_data.csv"], name_id[base_name+"_dfe_data.csv"]))
        if num:
          count += 1
          if count == num:
            break
      base_names.append(base_name)
  return pairs

def first_resource_pair(package):
  """Return (pd_resource_id, dfe_resource_id) of the first pair
  of x_pd_data.csv, x_dfe_data.csv in package"""
  first = resource_pairs(package, 1)
  if not first:
    raise ResourceNotFound
  return first[0]

class PhaseDiagramPlugin(p.SingletonPlugin):
  '''
  This base class for the Recline view extensions.
  '''
  p.implements(p.IConfigurer, inherit=True)
  p.implements(p.IResourceView, inherit=True)
  p.implements(p.IResourceController, inherit=True)
  p.implements(p.IActions)

  def update_config(self, config):
    '''
    Set up the resource library, public directory and
    template directory for the view
    '''
    tk.add_public_directory(config, 'theme/public')
    tk.add_template_directory(config, 'theme/templates')
    tk.add_resource('theme/public', 'ckanext-spdview')

  def old_setup_template_variables(self, context, data_dict):
    resource = data_dict["resource"]
    package = tk.get_action("package_show")(data_dict={"id": resource["package_id"]})
    pd_resource_id, dfe_resource_id = corresponding_resource_id(resource["name"], package)
    return {'resource_json': json.dumps(data_dict['resource']),
            'resource_view_json': json.dumps(data_dict['resource_view']),
            'resource': resource,
            'pd_resource_id': pd_resource_id,
            'dfe_resource_id': dfe_resource_id,
            'pd_params': json.dumps({}),
            'dfe_params': json.dumps({}),
            'dataset_id': package['id']
            }

  def get_pd_dfe_resource_id(self, material):
    pass

  def get_possible_elements(self, material):
    three = ["In", "Ga"]
    six = ["Se"]
    if material == "chalcopyrite":
      return {3: three, 6: six}
    else:
      raise Exception("Material type selected invalid: " + material)

  def setup_material_properties(self, material, package):
    class BadRule(Exception):
      pass
    def get_rules(material):
      """Get list of rules in stoichiometry.csv resource for material"""
      stoich_resource = filter(lambda x: x["name"] == "stoichiometry.csv", package["resources"])[0]
      data = tk.get_action("datastore_search")(data_dict={"resource_id": stoich_resource["id"]})["records"]
      rules = []
      # Get rules
      for d in data:
        if d["material"] == material:
          rules.append(d["stoich"])
      return rules
    def parse_stoich(rules):
      """Look for stoich rule in dataset's stoichiometry, get values each chem could be"""
      # Example rules: Cu Ga_x In_1-x S_y Se_(2-y) where 0<=x<=1 ; 0<=y<=1
      # Constraints must be either form of c1<=x<=c2, using either <= or <
      def check_parens(s):
        """Check there are no nested parens, and that all open and close parens have match, return True if good"""
        saw_open = False
        for c in s:
          if c == "(":
            if saw_open:
              return False
            saw_open = True
          elif c == ")":
            if not saw_open:
              return False
            saw_open = False
        return not saw_open

      delims = "(\<=|\>=|\<|\>)"
      operators = ["<=", ">=", "<", ">"]
      valid_operators = ["<=", "<"]
      validated_element_values = defaultdict(lambda: [100,  -100])
      try:
        # Parse rules
        for rule in rules:
          try:
            parts = map(lambda x: x.strip(), rule.split("where"))
            if len(parts) != 2:
              continue
            # Get the elements and vars and
            var_values = {} # The (min, max) values, inclusive
            # Validate the constraints
            for constraint in parts[1].split(";"):
              saw_operator_last = True
              constraint = constraint.strip()
              tokens = re.split(delims, constraint)
              if len(tokens) != 5:
                raise BadRule()
              var = ""
              validated_tokens = []
              for t in tokens:
                t = t.strip()
                # [int|alpha] must preceed and follow an operator
                if saw_operator_last:
                  if t in operators:
                    raise BadRule()
                  saw_operator_last = False
                  try:
                    # Check for integer, or alphabetical
                    t = int(t)
                    validated_tokens.append(t)
                  except ValueError:
                    if var:
                      # This constraint has two variables; not simple, ignoring rule. Ex: 0<x<y<5
                      raise BadRule()
                    else:
                      var = t
                      validated_tokens.append(t)
                else: # Should be an operator now
                  if t in valid_operators:
                    validated_tokens.append(t)
                    saw_operator_last = True
                  else:
                    raise BadRule()
              # Get the min and max values for the var
              # Every odd token should be a comparison operator
              if validated_tokens[1] == "<=":
                min_v = validated_tokens[0]
              else:
                min_v = validated_tokens[0] + 1
              if validated_tokens[3] == "<=":
                max_v = validated_tokens[4]
              else:
                max_v = validated_tokens[4] - 1
              var_values[var] = (min_v, max_v)

            # Get the elements and min max values
            element_values = {}
            delims = "(-|\+)"
            valid_operators = ["-", "+"]
            for ele in parts[0].split():
              try:
                ele, stoich_rule = ele.split("_")
                stoich_rule = stoich_rule.strip()
                if check_parens(stoich_rule): # Check for good parens
                  # If there was parens
                  if stoich_rule[0] == "(":
                    stoich_rule = stoich_rule[1:-1]
              except ValueError:
                if ele.isalpha():
                  element_values[ele] = (1,1)
                  continue
                raise BadRule()
              min_v = 0
              max_v = 0
              tokens = re.split(delims, stoich_rule)
              # Validate, make sure integers and vars in constraints only
              # And update the min/max value of element
              vars_in_rule = []
              for i, t in enumerate(tokens):
                # If number/variable, look at sign before it
                if t in valid_operators:
                  continue
                if i == 0:
                  sign = 1
                elif tokens[i-1] == "+":
                  sign = 1
                else:  # -
                  sign = -1
                if t in var_values.keys():
                  vars_in_rule.append(t)
                  # Use the min/max values of var to update min/max of element
                  if sign == 1:
                    min_v += var_values[t][0]
                    max_v += var_values[t][1]
                  else:
                    min_v -= var_values[t][1]
                    max_v -= var_values[t][0]
                else:  # Check if int
                  try:
                    t = int(t)
                    max_v += sign * t
                    min_v += sign * t
                  except ValueError:
                    raise BadRule()
              element_values[ele] = (min_v, max_v)
            # If got here, that means this rule in dataset was ok
            # Update the mins and max of this element
            for ele, min_max in element_values.iteritems():
              min0, max0 = validated_element_values[ele]
              min1, max1 = min_max
              validated_element_values[ele] = (min(min0, min1), max(max0, max1))
          except BadRule:
            continue
        # Return formatted list of dicts, each entry in list corresponding to options in a select box
        return validated_element_values
      except IndexError:
        return None
    def format_elements(material, ele_values):
      """Given {"Cu": [1,1], "Ga": [0,1]}, return a formatted list for web page. See code"""
      if not ele_values:  # Return defaults
        # stoich not found, return defaults
        if material == "chalcopyrite":
          default = [  # Keep a list of dicts so it's ordered?
                      [{"text": "Cu",
                        "values": [1]},
                       ],
                      [{"text": "In",
                        "values": list(range(1, 3)),
                        },
                       {"text": "Ga",
                        "values": list(range(1, 3)),
                        }
                       ],
                      [{"text": "Se",
                        "values": list(range(1, 3)),
                        },
                       ]
                    ]
        return default
      else:
        if material == "chalcopyrite":
          pos = {"Cu": 0, "In": 1, "Ga": 1, "S": 2, "Se": 2} # The select to be shown in
          retv = [[], [], []]
          for ele, values in ele_values.iteritems():
            retv[pos[ele]].append({"text": ele, "values": range(values[0], values[1]+1)})
          return retv
    def allowed_values(package):
      """Look up the chems that are in the dataset"""
      chems_with_data = resource_pair_names(package)
      allowed_values = []
      for chem in chems_with_data:
        allowed_values.append(phase_diagram.Compound.parse_string_to_dict(chem))
      return allowed_values

    possible_materials = ["chalcopyrite"]
    assert(material in possible_materials)
    properties = [("formation_energy", "Formation Energy"),
                   ("band_edge_position", "Band Edge Position")]
    if material == "chalcopyrite":
      properties = {
        "material": "chalcopyrite",
        "text": "Chalcopyrite",
        "properties": properties,
        "elements": format_elements(material, parse_stoich(get_rules(material))),
        "allowed": allowed_values(package)
      }
    return properties

  def setup_template_variables(self, context, data_dict):
    resource = data_dict["resource"]
    package = tk.get_action("package_show")(data_dict={"id": resource["package_id"]})
    id_name = {r["name"]: r["id"] for r in package["resources"]}
    # Pick the first "X_pd_data.csv, X_dfe_data.csv" resource pair
    try:
      pd_resource_id, dfe_resource_id = first_resource_pair(package)
    except ResourceNotFound:
      return {"msg": "No *_pd_data.csv, *_dfe_data.csv pair found"}

    element_select_values = {
      "materials": [
        self.setup_material_properties("chalcopyrite", package),
      ],
    }
    default_selected_element_values = {
      "material": "chalcopyrite",
      "property": "formation_energy",
      "elements_nums": [("Cu", 1), ("In", 1), ("Se", 2),]
    }
    element_config_data = { "default_selected_values": default_selected_element_values,
                           "select_values": element_select_values,
                           }

    return {'resource_json': json.dumps(data_dict['resource']),
            'resource_view_json': json.dumps(data_dict['resource_view']),
            'resource': resource,
            'pd_resource_id': pd_resource_id,
            'dfe_resource_id': dfe_resource_id,
            'element_config_data': json.dumps(element_config_data),
            'pd_params': json.dumps({}),
            'dfe_params': json.dumps({}),
            'package_id': package['id']
            }

  def view_template(self, context, data_dict):
    return 'phase_diagram.html'

  def info(self):
    return {'name': 'semiconductor_stability_phase_diagram_view_llnl_smc',
            'title': 'Semiconductor Stability Phase Diagram',
            'icon': 'eye-open',
            'requires_datastore': True,
            }

  def can_view(self, data_dict):
    return True

  def after_create(self, context, resource):
    if resource.has_key('data_tool') and resource['data_tool'] == 'Semiconductor Stability Phase Diagram':
      data_dict = {
        'resource_id': resource['id'],
        'title': 'Solar Cell Phase & Defect Formation Energy',
        'view_type': 'semiconductor_stability_phase_diagram_view_llnl_smc'
      }
      tk.get_action('resource_view_create')(context, data_dict)

  def after_update(self, context, resource):
    if resource.has_key('data_tool') and resource['data_tool'] == 'Semiconductor Stability Phase Diagram':
      resource_views = tk.get_action('resource_view_list')(context, resource)
      result = False
      for rv in resource_views:
        print(rv)
        if rv['view_type'] == 'semiconductor_stability_phase_diagram_view_llnl_smc':
          result = True
      if not result:
        data_dict = {
          'resource_id': resource['id'],
          'title': 'Solar Cell Phase & Defect Formation Energy',
          'view_type': 'semiconductor_stability_phase_diagram_view_llnl_smc'
        }
    tk.get_action('resource_view_create')(context, data_dict)

  # IActions
  def get_actions(self):
    actions = {
      "semiconductor_phase_diagram_llnl_smc": phase_diagram_view,
      "semiconductor_dfe_diagram_llnl_smc": defect_fect_formation_diagram_view,
      "semiconductor_element_select_llnl_smc": select_compound,
    }
    return actions
