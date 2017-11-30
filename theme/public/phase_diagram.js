(function ($)
{

var self = this;

this.PhaseDiagram = function(phase_diagram_div, dfe_div, endpoint) {
    console.log("phase diagram func");
    this.svg_div = phase_diagram_div;
    this.dfe_svg_div = dfe_div;
    this.endpoint = endpoint;

    var defaults = {
        "height": 500,
        "width": 500,
        "padding": 30,
        "margin": {top: 20, right: 30, bottom: 20, left: 30},
    };
    this.options = defaults;

};

PhaseDiagram.prototype.init = function() {
    //this.DFEDiagram = new DFEDiagram(this.dfe_svg_div);
    //this.DFEDiagram.init();
    // Get region data
    //var s = document.getElementsByName("formation_energy_data");
    //var data = {"fe_data": s};
    var endpoint = this.endpoint;
    console.log("phasediagram init");
    $.ajax({
        context: this,
        type: "GET",
        contentType: "application/json",
        dataType: "json",
        url: endpoint,
        async: true,
        data: "{}",//data,
        success: setup,
        error: function(result){
            console.log("Ajax error: ", result)
        }
    })
};

function setup(data) {
    function get_center(vertices) {
        // Return center (average) point given vertices
        if(vertices.length === 0)
            console.log('hi');
        var dim = vertices[0].length;
        var sums = [0,0];
        vertices.forEach(function(vert) {
            for (var i =0; i < dim; i++) {
                sums[i] += vert[i];
            }
        });
        var ave = [];
        sums.forEach(function(s) {ave.push(s/vertices.length);});
        return ave;
    }

    function feasible_regions(regions) {
        // Return array w/ the regions that have vertices
        var feasible = [];
        for(var i = 0; i < regions.length; i++) {
           if(regions[i].vertices.length > 0)
               feasible.push(regions[i]);
        }
        return feasible;
    }

    this.DFEDiagram = new DFEDiagram(this.dfe_svg_div, data.default_coord);
    this.DFEDiagram.init();

    var margin = this.options.margin,
        width = this.options['width'] - margin.left - margin.right,
        height = this.options['height'] - margin.top - margin.bottom;

    var bounds = data.bounds;
    var all_regions = data.regions;
    var regions = feasible_regions(all_regions);
    var xScale = d3.scaleLinear().domain([bounds[0][0], bounds[0][1]]).range([0, width]);
    var yScale = d3.scaleLinear().domain([bounds[0][0], bounds[1][1]]).range([height, 0]);

    var svg_whole = d3.select(this.svg_div).append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom);
    var svg = svg_whole.append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    // Axis
    var xAxis = d3.axisBottom(xScale);
    var yAxis = d3.axisLeft(yScale);
    var xAxisG = svg.append("g")
        .call(xAxis);
    var yAxisG = svg.append("g")
        .attr("transform", "translate(" + width +")")
        .call(yAxis);

    xAxisG.selectAll("text")
        .attr("transform", "translate(0, -22)")
    yAxisG.selectAll("text")
        .attr("transform", "translate(35, 0)")

    // Polygons
    var polygon_g = svg.append("g");
    var clickrect = polygon_g
        .append("rect")
        .attr("width", width)
        .attr("height", height)
        .style("fill-opacity", "0");
    polygon_g.append("clipPath")
        .attr("id", "pd-clip")
        .append("rect")
        .attr("width", width)
        .attr("height", height);
    polygon_g.selectAll("polygon").data(regions).enter().append("polygon").attr("points", function(d) {
        var s = "";
        d.vertices.forEach(function(vert){
            vert = [xScale(vert[0]), yScale(vert[1])];
            s += vert.toString() + " ";
        });
        return s;
    }).style("stroke", "blue" ).style("fill", "none")
        .attr("clip-path", "url(#pd-clip)");

    // Borders for left and bottom
    polygon_g.append("polyline")
        .attr("points", "0,0 " + "0," +height)
        .style("stroke", "black");
    polygon_g.append("polyline")
        .style("stroke", "black")
        .attr("points", "0," + height + " " + width+ "," + height);

    // Current Point
    var cur_point_g = polygon_g.append("g");
    var px = data.default_coord.x,
        py = data.default_coord.y;
    var cur_point = cur_point_g.append("circle")
        .attr("cx", xScale(px))
        .attr("cy", yScale(py))
        .attr("r", 3)
        .attr("class", "cur-point")
        .style("fill", "darkgray");
    var cur_point_text = cur_point_g.append("text")
        .text(px + ", " + py)
        .attr("x", xScale(px) - 13)
        .attr("y", yScale(py) - 7)
        .attr("text-anchor", "middle")
        .style("font-size", "0.7em");

    // Labels
    regions.forEach(function(region) {
        if(region.vertices.length > 0) {
            var center = get_center(region.vertices);
            region.cx = center[0];
            region.cy = center[1];
        }
    });
    svg.selectAll("text.region_label").data(regions).enter().append("svg:text").text(function(d) {
        return d.formula;
    }).attr("x", function(d) {return xScale(d.cx);})
        .attr("y", function(d) {return yScale(d.cy);})
        .attr("text-anchor", "middle").attr("class", "region_label");

    // On click, get new dfe
    var _ = this;
    console.log(svg);
    polygon_g.on("click", function() {
        var coords = d3.mouse(this);
        var inverted_coords = [
            xScale.invert(coords[0]),
            yScale.invert(coords[1])
        ];
        // TODO: $ is global. not searching under svg_div
        $(" #x").text(inverted_coords[0]);
        $(" #y").text(inverted_coords[1]);

        _.DFEDiagram.update(inverted_coords)
        //$.getJSON("/dfe", invert_coords, function() {
        //});
    });

}
} (jQuery));
