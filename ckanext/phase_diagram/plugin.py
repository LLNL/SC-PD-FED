# encoding: utf-8

from logging import getLogger

import ckan.plugins as p
import ckan.plugins.toolkit as tk
from ckan.common import json

import phase_diagram
from defect_formation_diagram import DefectFormationEnergyDiagram

#log = getLogger(__name__)
#ignore_empty = p.toolkit.get_validator('ignore_empty')
#natural_number_validator = p.toolkit.get_validator('natural_number_validator')
#Invalid = p.toolkit.Invalid


@tk.side_effect_free
def phase_diagram_view(context, data_dict):
  data = tk.get_action("datastore_search")(data_dict={"resource_id": data_dict["resource_id"]})["records"]
  compounds = [[d['compound'], d['fe']] for d in data]
  compounds = phase_diagram.parse_compounds(compounds)

  # Example ["Cu", "In", "Se"]
  # TODO: , coords, be passed in by request
  elements = data_dict["elements"]
  cu_in_se_compounds = phase_diagram.select_compounds(compounds, elements)
  CuInSe2 = compounds[0]
  lower_lims = [-3, -3]
  sd = phase_diagram.StabilityDiagram(CuInSe2, cu_in_se_compounds, elements, lower_lims)

  regions = sd.get_regions()
  regions = [{"formula": formula, "vertices": v.vertices.tolist()} for formula, v in regions.iteritems()]
  #default_coord = {"x": (lower_lims[0] - 0) / 2.0,
  #                 "y": (lower_lims[1] - 0) / 2.0
  #                 }
  default_coord = {"x": -0.3,
                   "y": -1}
  data = {"regions": regions,
          "bounds": [[-3, 0], [-3, 0]],
          "default_coord": default_coord,
          "x_label": "ΔμCu eV",
          "y_label": "ΔμIn eV"
          }
  return data

@tk.side_effect_free
def defect_fect_formation_diagram_view(context, data_dict):
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
  ifl = diagram.find_intrinsic_fermi_level().tolist()
  lines = [{"label": k, "vertices": v.tolist()} for k, v in vert_dict.iteritems()]
  data = {"lines": lines,
          "bounds": [fermi_energy_axis_lim, dfe_lim],
          "minor_bounds": [[0, 1], [0]],  # little gray lines
          "intrinsic_fermi_level": ifl, #[x, y]
          "x_label": "Fermi energy [eV]",
          "y_label": "Formation energy [eV]",
          }
  return data

class PhaseDiagramPlugin(p.SingletonPlugin):
  '''
  This base class for the Recline view extensions.
  '''
  p.implements(p.IConfigurer, inherit=True)
  p.implements(p.IResourceView, inherit=True)
  p.implements(p.IActions)

  def update_config(self, config):
    '''
    Set up the resource library, public directory and
    template directory for the view
    '''
    tk.add_public_directory(config, 'theme/public')
    tk.add_template_directory(config, 'theme/templates')
    tk.add_resource('theme/public', 'ckanext-spdview')

  def corresponding_resource_names(self, resource):
    name = resource["name"]
    name = name.split(" ", 1)[0]
    return (name+"_pd_data.csv", name+"_dfe_data.csv")

  def corresponding_resource_id(self, resource, package):
    pd_name, dfe_name = self.corresponding_resource_names(resource)
    id_name = {r["name"]: r["id"] for r in package["resources"]}
    pd_resource_id = id_name[pd_name]
    dfe_resource_id = id_name[dfe_name]
    return (pd_resource_id, dfe_resource_id)

  def old_setup_template_variables(self, context, data_dict):
    resource = data_dict["resource"]
    package = tk.get_action("package_show")(data_dict={"id": resource["package_id"]})
    pd_resource_id, dfe_resource_id = self.corresponding_resource_id(resource, package)
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

  def setup_template_variables(self, context, data_dict):
    resource = data_dict["resource"]
    package = tk.get_action("package_show")(data_dict={"id": resource["package_id"]})
    pd_resource_id, dfe_resource_id = self.corresponding_resource_id(resource, package)
    return {'resource_json': json.dumps(data_dict['resource']),
            'resource_view_json': json.dumps(data_dict['resource_view']),
            'resource': resource,
            'pd_resource_id': pd_resource_id,
            'dfe_resource_id': dfe_resource_id,
            'elements': {"elements": ["Cu", "In", "Se"]},# TODO: hardcoded
            'pd_params': json.dumps({}),
            'dfe_params': json.dumps({}),
            'dataset_id': package['id']
            }

  def view_template(self, context, data_dict):
    return 'phase_diagram.html'

  def info(self):
    return {'name': 'semiconductor_stability_phase_diagram_view',
            'title': 'Semiconductor Stability Phase Diagram',
            'icon': 'eye-open',
            'requires_datastore': True,
            }

  def can_view(self, data_dict):
    # Return whether plugin can render a particular resource
    # TODO: done?
    resource = data_dict['resource']
    package = tk.get_action("package_show")(data_dict={"id": resource["package_id"]})
    requirements = self.corresponding_resource_names(resource)
    pkg_resources = map(lambda r: r['name'], package['resources'])
    valid = all(req in pkg_resources for req in requirements)

    #if (resource.get('datastore_active') or
    #        '_datastore_only_resource' in resource.get('url', '')):
    #  return True
    #resource_format = resource.get('format', None)
    return valid

  # IActions
  def get_actions(self):
    actions = {
      "semiconductor_phase_diagram": phase_diagram_view,
      "semiconductor_dfe_diagram": defect_fect_formation_diagram_view,
    }
    return actions
