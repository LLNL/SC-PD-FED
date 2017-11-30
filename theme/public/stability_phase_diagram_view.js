ckan.module('stability_phase_diagram_view', function(jQuery) {
    function initialize() {
        var phase_diagram = new PhaseDiagram(phase_div_id, dfe_dive_id);
        phase_diagram.init();
    }
    return {
        initialize: initialize
    }
})