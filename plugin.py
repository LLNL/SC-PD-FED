# encoding: utf-8

from logging import getLogger

from ckan.common import json, config
import ckan.plugins as p
import ckan.plugins.toolkit as toolkit
from flask import jsonify

import phase_diagram
from defect_formation_diagram import DefectFormationEnergyDiagram

log = getLogger(__name__)
ignore_empty = p.toolkit.get_validator('ignore_empty')
natural_number_validator = p.toolkit.get_validator('natural_number_validator')
Invalid = p.toolkit.Invalid


#def get_mapview_config():
#    '''
#    Extracts and returns map view configuration of the reclineview extension.
#    '''
#    namespace = 'ckanext.spatial.common_map.'
#    return dict([(k.replace(namespace, ''), v) for k, v in config.iteritems()
#                 if k.startswith(namespace)])

def phase_diagram_view(context, data_dict):
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

  cu_in_se_compounds = phase_diagram.select_compounds(compounds, ["Cu", "In", "Se"])
  CuInSe2 = compounds[0]
  lower_lims = [-3, -3]
  sd = phase_diagram.StabilityDiagram(CuInSe2, cu_in_se_compounds, ["Cu", "In", "Se"], lower_lims)

  regions = sd.get_regions()
  regions = [{"formula": formula, "vertices": v.vertices.tolist()} for formula, v in regions.iteritems()]
  default_coord = {"x": (lower_lims[0] - 0)/2.0,
                   "y": (lower_lims[1] - 0)/2.0
                   }
  data = {"regions": regions,
          "bounds": [[-3, 0], [-3, 0]],
          "default_coord": default_coord,
          }
  return jsonify(data)

def defect_fect_formation_diagram_view(context, data_dict):
  dfes = {
    "In_Cu": [(-1, 1, 0), [None, -1.01, 0.24, 1.86, None, None, None]],
    "In_DX": [(-1, 1, 0), [None, None, None, 1.61, None, None, None]],
    "V_Cu": [(-1, 0, 0), [None, None, None, None, 1.19, None, None]],
    #"Cu_In": [(1, -1, 0), [None, None, None, 1.54, 1.83, 2.41, None]],
    "Cu_In": [(1, -1, 0), [None, None, None, 2.08, 2.22, 2.84, None]],
    "V_In": [(0, -1, 0), [None, None, None, 3.85, 3.88, 4.3, 4.99]],
    "V_Se": [(0, 0, -1), [None, 2.39, None, 2.45, 3.43, 4.78, 5.66]],
    "Cu_i": [(1, 0, 0), [None, None, 0.17, 1.68, None, None, None]],
    "In_i": [(0, 1, 0), [0.60, 0.95, 1.43, 2.84, None, None, None]],
    "Se_i": [(0, 0, 1), [None, 2.48, 2.67, 2.87, 3.51, 4.87, None]],
    "In_Cu-2V_Cu": [(-1+(-2), 1, 0), [None, None, None, 1.07, None, None, None]],
    "V_Se-V_Cu": [(-1, 0, -1), [None, None, 2.9, None, 3.47, 4.33, 5.66]],
  }
  charges = [3,2,1,0,-1,-2,-3]
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
          "minor_bounds": [[0, 1], [0]], # little gray lines
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
    fields = toolkit.get_action('datastore_search')({}, data)['fields']
    return [{'value': f['id'], 'text': f['id']} for f in fields
            if f['type'] in valid_field_types]


class SemiconductorStabilityPhaseDiagramView(p.SingletonPlugin):
  '''
  This base class for the Recline view extensions.
  '''
  p.implements(p.IConfigurer, inherit=True)
  p.implements(p.IResourceView, inherit=True)
  p.implements(p.ITemplateHelpers, inherit=True)
  p.implements(p.IActions)

  def update_config(self, config):
    '''
    Set up the resource library, public directory and
    template directory for the view
    '''
    toolkit.add_public_directory(config, 'theme/public')
    toolkit.add_template_directory(config, 'theme/templates')
    toolkit.add_resource('theme/public', 'ckanext-spdview')

  #def can_view(self, data_dict):
  #  resource = data_dict['resource']
  #  return (resource.get('datastore_active') or
  #          '_datastore_only_resource' in resource.get('url', ''))

  def setup_template_variables(self, context, data_dict):
    return {'resource_json': json.dumps(data_dict['resource']),
            'resource_view_json': json.dumps(data_dict['resource_view'])}

  def view_template(self, context, data_dict):
    return 'phase_diagram.html'

  def info(self):
    return {'name': 'semiconductor_stability_phase_diagram_view',
            'title': 'Semiconductor Stability Phase Diagram',
            'icon': 'eye-open',
            'requires_datastore': True,
            #'default_title': p.toolkit._('View'),
            }

  def can_view(self, data_dict):
    # Return whether plugin can render a particular resource
    # TODO: done?
    resource = data_dict['resource']

    if (resource.get('datastore_active') or
            '_datastore_only_resource' in resource.get('url', '')):
      return True
    resource_format = resource.get('format', None)
    if resource_format:
      return resource_format.lower() in ['csv', 'xls', 'xlsx', 'tsv']
    else:
      return False

  # IActions
  def get_actions(self):
    actions = {
      "semiconductor_phase_diagram": phase_diagram_view,
      "semiconductor_dfe_diagram": defect_fect_formation_diagram_view,
    }
    return actions
#  def get_helpers(self):
#    return {
#      'get_map_config': get_mapview_config
#    }
class ReclineViewBase(p.SingletonPlugin):
    '''
    This base class for the Recline view extensions.
    '''
    p.implements(p.IConfigurer, inherit=True)
    p.implements(p.IResourceView, inherit=True)
    p.implements(p.ITemplateHelpers, inherit=True)

    def update_config(self, config):
        '''
        Set up the resource library, public directory and
        template directory for the view
        '''
        toolkit.add_public_directory(config, 'theme/public')
        toolkit.add_template_directory(config, 'theme/templates')
        toolkit.add_resource('theme/public', 'ckanext-reclineview')

    def can_view(self, data_dict):
        resource = data_dict['resource']
        return (resource.get('datastore_active') or
                '_datastore_only_resource' in resource.get('url', ''))

    def setup_template_variables(self, context, data_dict):
        return {'resource_json': json.dumps(data_dict['resource']),
                'resource_view_json': json.dumps(data_dict['resource_view'])}

    def view_template(self, context, data_dict):
        return 'recline_view.html'

    def get_helpers(self):
        return {
            'get_map_config': get_mapview_config
        }


class ReclineView(ReclineViewBase):
    '''
    This extension views resources using a Recline MultiView.
    '''

    def info(self):
        return {'name': 'recline_view',
                'title': 'Data Explorer',
                'filterable': True,
                'icon': 'table',
                'requires_datastore': False,
                'default_title': p.toolkit._('Data Explorer'),
                }

    def can_view(self, data_dict):
        resource = data_dict['resource']

        if (resource.get('datastore_active') or
                '_datastore_only_resource' in resource.get('url', '')):
            return True
        resource_format = resource.get('format', None)
        if resource_format:
            return resource_format.lower() in ['csv', 'xls', 'xlsx', 'tsv']
        else:
            return False


class ReclineGridView(ReclineViewBase):
    '''
    This extension views resources using a Recline grid.
    '''

    def info(self):
        return {'name': 'recline_grid_view',
                'title': 'Grid',
                'filterable': True,
                'icon': 'table',
                'requires_datastore': True,
                'default_title': p.toolkit._('Table'),
                }


class ReclineGraphView(ReclineViewBase):
    '''
    This extension views resources using a Recline graph.
    '''

    graph_types = [{'value': 'lines-and-points',
                    'text': 'Lines and points'},
                   {'value': 'lines', 'text': 'Lines'},
                   {'value': 'points', 'text': 'Points'},
                   {'value': 'bars', 'text': 'Bars'},
                   {'value': 'columns', 'text': 'Columns'}]

    datastore_fields = []

    datastore_field_types = ['numeric', 'int4', 'timestamp']

    def list_graph_types(self):
        return [t['value'] for t in self.graph_types]

    def list_datastore_fields(self):
        return [t['value'] for t in self.datastore_fields]

    def info(self):
        # in_list validator here is passed functions because this
        # method does not know what the possible values of the
        # datastore fields are (requires a datastore search)
        schema = {
            'offset': [ignore_empty, natural_number_validator],
            'limit': [ignore_empty, natural_number_validator],
            'graph_type': [ignore_empty, in_list(self.list_graph_types)],
            'group': [ignore_empty, in_list(self.list_datastore_fields)],
            'series': [ignore_empty, in_list(self.list_datastore_fields)]
        }
        return {'name': 'recline_graph_view',
                'title': 'Graph',
                'filterable': True,
                'icon': 'bar-chart-o',
                'requires_datastore': True,
                'schema': schema,
                'default_title': p.toolkit._('Graph'),
                }

    def setup_template_variables(self, context, data_dict):
        self.datastore_fields = datastore_fields(data_dict['resource'],
                                                 self.datastore_field_types)
        vars = ReclineViewBase.setup_template_variables(self, context,
                                                        data_dict)
        vars.update({'graph_types': self.graph_types,
                     'graph_fields': self.datastore_fields})
        return vars

    def form_template(self, context, data_dict):
        return 'recline_graph_form.html'


class ReclineMapView(ReclineViewBase):
    '''
    This extension views resources using a Recline map.
    '''

    map_field_types = [{'value': 'lat_long',
                        'text': 'Latitude / Longitude fields'},
                       {'value': 'geojson', 'text': 'GeoJSON'}]

    datastore_fields = []

    datastore_field_latlon_types = ['numeric']

    datastore_field_geojson_types = ['text']

    def list_map_field_types(self):
        return [t['value'] for t in self.map_field_types]

    def list_datastore_fields(self):
        return [t['value'] for t in self.datastore_fields]

    def info(self):
        # in_list validator here is passed functions because this
        # method does not know what the possible values of the
        # datastore fields are (requires a datastore search)
        schema = {
            'offset': [ignore_empty, natural_number_validator],
            'limit': [ignore_empty, natural_number_validator],
            'map_field_type': [ignore_empty,
                               in_list(self.list_map_field_types)],
            'latitude_field': [ignore_empty,
                               in_list(self.list_datastore_fields)],
            'longitude_field': [ignore_empty,
                                in_list(self.list_datastore_fields)],
            'geojson_field': [ignore_empty,
                              in_list(self.list_datastore_fields)],
            'auto_zoom': [ignore_empty],
            'cluster_markers': [ignore_empty]
        }
        return {'name': 'recline_map_view',
                'title': 'Map',
                'schema': schema,
                'filterable': True,
                'icon': 'map-marker',
                'default_title': p.toolkit._('Map'),
                }

    def setup_template_variables(self, context, data_dict):
        map_latlon_fields = datastore_fields(
            data_dict['resource'], self.datastore_field_latlon_types)
        map_geojson_fields = datastore_fields(
            data_dict['resource'], self.datastore_field_geojson_types)

        self.datastore_fields = map_latlon_fields + map_geojson_fields

        vars = ReclineViewBase.setup_template_variables(self, context,
                                                        data_dict)
        vars.update({'map_field_types': self.map_field_types,
                     'map_latlon_fields': map_latlon_fields,
                     'map_geojson_fields': map_geojson_fields
                     })
        return vars

    def form_template(self, context, data_dict):
        return 'recline_map_form.html'