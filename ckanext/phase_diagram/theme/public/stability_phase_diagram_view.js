ckan.module('stability_phase_diagram_view', function(jQuery) {
    function initialize() {
        var result_parser = function (res) {
          return res.result;
        };
        var phase_div_id = "#phase-diagram",
            dfe_div_id = "#defect-formation-energy-diagram",
            pd_endpoint = this.sandbox.client.url('/api/action/' + 'semiconductor_phase_diagram'),
            dfe_endpoint = this.sandbox.client.url('/api/action/' + 'semiconductor_dfe_diagram');

        var data = {
          "pd_resource_id": this.options.pdResourceId,
          "dfe_resource_id": this.options.dfeResourceId,
          "pd_params": JSON.parse(this.options.pdParams),
            "dfe_params": JSON.parse(this.options.dfeParams),
        };
        var phase_diagram = new PhaseDiagram(phase_div_id, dfe_div_id, pd_endpoint, dfe_endpoint, data, result_parser);
        phase_diagram.init();
    }
    return {
        initialize: initialize
    }
});
