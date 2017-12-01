# encoding: utf-8

from logging import getLogger

import ckan.plugins as p
import ckan.plugins.toolkit as tk
from ckan.common import json
from flask import jsonify

import phase_diagram
from defect_formation_diagram import DefectFormationEnergyDiagram

log = getLogger(__name__)
ignore_empty = p.toolkit.get_validator('ignore_empty')
natural_number_validator = p.toolkit.get_validator('natural_number_validator')
Invalid = p.toolkit.Invalid


@tk.side_effect_free
def phase_diagram_view(context, data_dict):
  data = tk.get_action("datastore_search")(data_dict={"resource_id": data_dict["resource_id"]})["records"]
  compounds = [
    "CuInSe2 -2.37",
    "CuGaSe2 -2.67",
    "CuIn5Se8 -9.37",
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

  points = [
    ['A', -0.5, -1.87],
    ['B', -0.1, -1.3],
    ['C', -0.4, -1.],
    ['D', -0.0, -0.2],
    ['E', -0.0, -0.9],
    ['F', -0.4, -2.],
  ]

  compounds = phase_diagram.parse_compounds(compounds)

  # TODO: have ["Cu", "In", "Se"] be passed in by request
  cu_in_se_compounds = phase_diagram.select_compounds(compounds, ["Cu", "In", "Se"])
  CuInSe2 = compounds[0]
  lower_lims = [-3, -3]
  sd = phase_diagram.StabilityDiagram(CuInSe2, cu_in_se_compounds, ["Cu", "In", "Se"], lower_lims)

  regions = sd.get_regions()
  regions = [{"formula": formula, "vertices": v.vertices.tolist()} for formula, v in regions.iteritems()]
  default_coord = {"x": (lower_lims[0] - 0) / 2.0,
                   "y": (lower_lims[1] - 0) / 2.0
                   }
  data = {"regions": regions,
          "bounds": [[-3, 0], [-3, 0]],
          "default_coord": default_coord,
          }
  return jsonify(data)


def _defect_fect_formation_diagram_view(context, data_dict):
  dfes = {
    "In_Cu": [(-1, 1, 0), [None, -1.01, 0.24, 1.86, None, None, None]],
    "In_DX": [(-1, 1, 0), [None, None, None, 1.61, None, None, None]],
    "V_Cu": [(-1, 0, 0), [None, None, None, None, 1.19, None, None]],
    # "Cu_In": [(1, -1, 0), [None, None, None, 1.54, 1.83, 2.41, None]],
    "Cu_In": [(1, -1, 0), [None, None, None, 2.08, 2.22, 2.84, None]],
    "V_In": [(0, -1, 0), [None, None, None, 3.85, 3.88, 4.3, 4.99]],
    "V_Se": [(0, 0, -1), [None, 2.39, None, 2.45, 3.43, 4.78, 5.66]],
    "Cu_i": [(1, 0, 0), [None, None, 0.17, 1.68, None, None, None]],
    "In_i": [(0, 1, 0), [0.60, 0.95, 1.43, 2.84, None, None, None]],
    "Se_i": [(0, 0, 1), [None, 2.48, 2.67, 2.87, 3.51, 4.87, None]],
    "In_Cu-2V_Cu": [(-1 + (-2), 1, 0), [None, None, None, 1.07, None, None, None]],
    "V_Se-V_Cu": [(-1, 0, -1), [None, None, 2.9, None, 3.47, 4.33, 5.66]],
  }
  charges = [3, 2, 1, 0, -1, -2, -3]
  defaults_mu = [-0.5, -1.87]
  # TODO: use validator
  mu_cu = float(data_dict.get("x", defaults_mu[0]))
  mu_in = float(data_dict.get("y", defaults_mu[1]))
  mu_se = (-2.37 - mu_cu - mu_in) / 2.0
  chemical_potentials = [mu_cu, mu_in, mu_se]
  fermi_energy_lim = [0, 1]
  fermi_energy_axis_lim = [-0.2, 2]
  dfe_lim = [-0.7, 4]

  diagram = DefectFormationEnergyDiagram(dfes, chemical_potentials, charges, fermi_energy_lim)
  vert_dict = diagram.get_lowest_points()
  lines = [{"label": k, "vertices": v.tolist()} for k, v in vert_dict.iteritems()]
  data = {"lines": lines,
          "bounds": [fermi_energy_axis_lim, dfe_lim],
          "minor_bounds": [[0, 1], [0]],  # little gray lines
          }
  return jsonify(data)


@tk.side_effect_free
def defect_fect_formation_diagram_view(context, data_dict):
  #resource = tk.get_action("resource_show")(data_dict={"id": data_dict["resource_id"]})
  data = tk.get_action("datastore_search")(data_dict={"resource_id": data_dict["resource_id"]})["records"]
  dfes = {}
  for d in data:
    dfes[d["defect"]] = [(d["c1"], d["c2"], d["c3"]), map(lambda k: d.get(k, None), ["e1", "e2", "e3", "e4", "e5", "e6", "e7"])]

  charges = [3, 2, 1, 0, -1, -2, -3]
  # TODO: get default mu, fermi*lim, dfe_lim from somewhere else
  defaults_mu = [-0.5, -1.87]
  # TODO: use validator
  mu_cu = float(data_dict.get("x", defaults_mu[0]))
  mu_in = float(data_dict.get("y", defaults_mu[1]))
  mu_se = (-2.37 - mu_cu - mu_in) / 2.0
  chemical_potentials = [mu_cu, mu_in, mu_se]
  fermi_energy_lim = [0, 1]
  fermi_energy_axis_lim = [-0.2, 2]
  dfe_lim = [-0.7, 4]

  diagram = DefectFormationEnergyDiagram(dfes, chemical_potentials, charges, fermi_energy_lim)
  vert_dict = diagram.get_lowest_points()
  lines = [{"label": k, "vertices": v.tolist()} for k, v in vert_dict.iteritems()]
  data = {"lines": lines,
          "bounds": [fermi_energy_axis_lim, dfe_lim],
          "minor_bounds": [[0, 1], [0]],  # little gray lines
          }
  return jsonify(data)

def in_list(list_possible_values):
  '''
    Validator that checks that the input value is one of the given
    possible values.

    :param list_possible_values: function that returns list of possible values
        for validated field
    :type possible_values: function
    '''

  def validate(key, data, errors, context):
    if not data[key] in list_possible_values():
      raise Invalid('"{0}" is not a valid parameter'.format(data[key]))

  return validate


def datastore_fields(resource, valid_field_types):
  '''
    Return a list of all datastore fields for a given resource, as long as
    the datastore field type is in valid_field_types.

    :param resource: resource dict
    :type resource: dict
    :param valid_field_types: field types to include in returned list
    :type valid_field_types: list of strings
    '''
  data = {'resource_id': resource['id'], 'limit': 0}
  fields = tk.get_action('datastore_search')({}, data)['fields']
  return [{'value': f['id'], 'text': f['id']} for f in fields
          if f['type'] in valid_field_types]


class PhaseDiagramPlugin(p.SingletonPlugin):
  '''
  This base class for the Recline view extensions.
  '''
  p.implements(p.IConfigurer, inherit=True)
  p.implements(p.IResourceView, inherit=True)
  #p.implements(p.ITemplateHelpers, inherit=True)
  p.implements(p.IActions)

  def update_config(self, config):
    '''
    Set up the resource library, public directory and
    template directory for the view
    '''
    tk.add_public_directory(config, 'theme/public')
    tk.add_template_directory(config, 'theme/templates')
    tk.add_resource('theme/public', 'ckanext-spdview')

  # def can_view(self, data_dict):
  #  resource = data_dict['resource']
  #  return (resource.get('datastore_active') or
  #          '_datastore_only_resource' in resource.get('url', ''))

  def setup_template_variables(self, context, data_dict):
    resource = data_dict["resource"]
    name = resource["name"]
    name = name.split(" ", 1)[0]
    package = data_dict["package"]
    id_name = {r["name"]: r["id"] for r in package["resources"]}
    pd_resource_id = id_name[name+"_pd_data.csv"]
    dfe_resource_id = id_name[name+"_dfe_data.csv"]
    return {'resource_json': json.dumps(data_dict['resource']),
            'resource_view_json': json.dumps(data_dict['resource_view']),
            'resource': resource,
            'pd_resource_id': pd_resource_id,
            'dfe_resource_id': dfe_resource_id,
            'dataset_id': package['id']
            }

  def view_template(self, context, data_dict):
    return 'phase_diagram.html'

  def info(self):
    return {'name': 'semiconductor_stability_phase_diagram_view',
            'title': 'Semiconductor Stability Phase Diagram',
            'icon': 'eye-open',
            'requires_datastore': True,
            # 'default_title': p.toolkit._('View'),
            }

  def can_view(self, data_dict):
    # Return whether plugin can render a particular resource
    # TODO: done?
    resource = data_dict['resource']

    if (resource.get('datastore_active') or
            '_datastore_only_resource' in resource.get('url', '')):
      return True
    resource_format = resource.get('format', None)
    print 'format is', resource_format
    #if resource_format:
    #  return resource_format.lower() in ['csv', 'xls', 'xlsx', 'tsv']
    #else:
    #  return False
    # TODO: check if there are two more resources in this dataset that start wth the same compound and are like *dfe_data.json *pd_data.csv
    return True

  # IActions
  def get_actions(self):
    actions = {
      "semiconductor_phase_diagram": phase_diagram_view,
      "semiconductor_dfe_diagram": defect_fect_formation_diagram_view,
    }
    return actions
