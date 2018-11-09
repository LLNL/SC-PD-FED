# ckanext-phase_diagram

Solar Cell Phase and Defect Formation Energy Diagram

This is a CKAN plugin for the HydroGEN project, showing phase diagrams and defect formation energy diagrams for semi-conductors.

The phase diagram basically calculates some intersection of halfspaces and the resultant polygons, using in part numpy and scipy. 
Users can select a point on the phase diagram and the defect formation energy diagram is graphed with those chosen values. The defect formation energy graphs the lowest energy state for several defects at concentrations of certain chemicals.

------------
Requirements
------------

For example, you might want to mention here which versions of CKAN this
extension works with.


### Installation

To install ckanext-phase_diagram:

1. Activate your CKAN virtual environment, for example::

     . /usr/lib/ckan/default/bin/activate

2. Install the ckanext-phase_diagram Python package into your virtual environment::

     pip install ckanext-phase_diagram

3. Add ``phase_diagram`` to the ``ckan.plugins`` setting in your CKAN
   config file (by default the config file is located at
   ``/etc/ckan/default/production.ini``).

4. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu::

     sudo service apache2 reload


### Config Settings

No plugin settings for now.

### Getting involved
If you would you like to know more about this plugin, contact li54@llnl.gov, or ogitsu1@llnl.gov. Information about HydroGEN can be found at datahub.h2awsm.org/.

### Release
LLNL-CODE-761115
Title: SCPDFED, Version: 0.1
Author(s) Peggy P. L

