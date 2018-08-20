ckan.module('stability_phase_diagram_view', function(jQuery) {
    function initialize() {
        var result_parser = function (res) {
          return res.result;
        };
        var phase_div_id = "#phase-diagram",
            dfe_div_id = "#defect-formation-energy-diagram",
            pd_endpoint = this.sandbox.client.url('/api/action/' + 'semiconductor_phase_diagram_llnl_smc'),
            dfe_endpoint = this.sandbox.client.url('/api/action/' + 'semiconductor_dfe_diagram_llnl_smc'),
            element_select_endpoint = this.sandbox.client.url('/api/action/' + 'semiconductor_element_select_llnl_smc');

        var pdId = this.options.pdResourceId,
            dfeId = this.options.dfeResourceId;
        var query_data = {
            "pd_resource_id": pdId,
            "dfe_resource_id": dfeId,
            "elements_nums": this.options.elementConfigData.default_selected_values.elements_nums,
        };
        var params = {
            "pd_params": this.options.pdParams,
            "dfe_params": this.options.dfeParams,
        };
        // Element selects
        // Function to execute on submit
        function phase_diagram_init_using_query_data(query_data) {
            var phase_diagram = new PhaseDiagram(phase_div_id, dfe_div_id, pd_endpoint, dfe_endpoint, params, query_data, result_parser);
            phase_diagram.init();
        }
        init_element_selects("#pd-elements",
            this.options.elementConfigData.select_values,
            this.options.elementConfigData.default_selected_values,
            element_select_endpoint,
            {"package_id": this.options.packageId},
            phase_diagram_init_using_query_data,
            result_parser);
        // TODO: deal with padding/margins better
        var pwidth = this.el[0].offsetWidth,
            w = pwidth/2 - 50;
        Object.assign(params.pd_params, {"width": w, "height": w});
        Object.assign(params.dfe_params, {"width": w, "height": w});

        // var phase_diagram = new PhaseDiagram(phase_div_id, dfe_div_id, pd_endpoint, dfe_endpoint, params, query_data, result_parser);
        // phase_diagram.init();
        phase_diagram_init_using_query_data(query_data)
    }
    return {
        initialize: initialize
    }
});
