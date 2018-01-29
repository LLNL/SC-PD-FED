ckan.module('stability_phase_diagram_view', function(jQuery) {
    function initialize() {
        var result_parser = function (res) {
          return res.result;
        };
        var phase_div_id = "#phase-diagram",
            dfe_div_id = "#defect-formation-energy-diagram",
            pd_endpoint = this.sandbox.client.url('/api/action/' + 'semiconductor_phase_diagram'),
            dfe_endpoint = this.sandbox.client.url('/api/action/' + 'semiconductor_dfe_diagram'),
            element_select_endpoint = this.sandbox.client.url('/api/action/' + 'semiconductor_element_select');

        var query_data = {
            "pd_resource_id": this.options.pdResourceId,
            "dfe_resource_id": this.options.dfeResourceId,
            "elements": this.options.elementConfigData.elements,
        };
        var params = {
            "pd_params": this.options.pdParams,
            "dfe_params": this.options.dfeParams,
        };
        // Element selects
        // Function to execute on submit
        function phase_diagram_init_using_query_data(query_data) {
            if(!query_data.package_id) {
                query_data.package_id = this.options.packageId;
            }
            var phase_diagram = new PhaseDiagram(phase_div_id, dfe_div_id, pd_endpoint, dfe_endpoint, params, query_data, result_parser);
            phase_diagram.init();
        }
        init_element_selects("#pd-elements",
            this.options.elementConfigData.default_values,
            this.options.elementConfigData.default_selected_values,
            element_select_endpoint,
            phase_diagram_init_using_query_data);
        // TODO: deal with padding/margins better
        var pwidth = this.el[0].offsetWidth,
            w = pwidth/2 - 50;
        Object.assign(params.pd_params, {"width": w, "height": w});
        Object.assign(params.dfe_params, {"width": w, "height": w});

        var phase_diagram = new PhaseDiagram(phase_div_id, dfe_div_id, pd_endpoint, dfe_endpoint, params, query_data, result_parser);
        phase_diagram.init();
    }
    return {
        initialize: initialize
    }
});
