(function ($)
{

var self = this;

this.PhaseDiagram = function(phase_diagram_div, dfe_div, endpoint, dfe_endpoint, params, query_data, result_parser) {
    this.svg_div = phase_diagram_div;
    this.dfe_svg_div = dfe_div;
    this.endpoint = endpoint;
    this.dfe_endpoint = dfe_endpoint;
    if(query_data.pd_resource_id)
      query_data["resource_id"] = query_data["pd_resource_id"];
    this.query_data = query_data;
    this.result_parser = result_parser;

    var defaults = {
        "height": 500,
        "width": 500,
        "margin": {top: 35, right: 35, bottom: 20, left: 30},
    };
    this._params = params;
    this.params = Object.assign({}, defaults, this._params.pd_params);
    if(params.margin_top !== undefined){
        this.params.margin.top = params.margin_top;
    }else if(params.margin_bottom !== undefined) {
        this.params.margin.bottom = params.margin_bottom;
    }else if(params.margin_right !== undefined) {
        this.params.margin.right = params.margin_right;
    }else if(params.margin_left !== undefined) {
        this.params.margin.left = params.margin_left;
    }

};

PhaseDiagram.prototype.init = function() {
    console.log("phasediagram init");
    $.ajax({
        context: this,
        type: "GET",
        contentType: "application/json",
        dataType: "json",
        url: this.endpoint,
        async: true,
        data: this.query_data,
        success: function(data) {
          if(this.result_parser) {
            data = this.result_parser(data);
          }
          setup.call(this, data);
        },
        error: function(result){
            console.log("Ajax error: ", result)
        }
    })
};

function setup(data) {
    function get_center(vertices) {
        // Return center (average) point given vertices
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

    // Clear divs
    $(this.svg_div).html("");
    $(this.dfe_svg_div).html("");
    this.DFEDiagram = new DFEDiagram(this.dfe_svg_div, data.default_coord, data.compound_formation_energy,
                                    this.dfe_endpoint, this._params, this.query_data, this.result_parser);
    this.DFEDiagram.init();

    var margin = this.params.margin,
        width = this.params['width'] - margin.left - margin.right,
        height = this.params['height'] - margin.top - margin.bottom;

    var bounds = data.bounds;
    var all_regions = data.regions;
    var regions = feasible_regions(all_regions);
    var relevant_region = data.relevant_region;
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
        .attr("transform", "translate(0, -22)");
    yAxisG.selectAll("text")
        .attr("transform", "translate(30, 0)");

    // Axis labels
    var labels = svg_whole.append("g");
    labels.append("text")
        .attr("x", this.params['width']/2)
        .attr("y", 15)
        .attr("text-anchor", "middle")
        .text(data['x_label']);
    var lx = this.params.width-10,
        ly = this.params.height/2;
    labels.append("text")
        .attr("x", lx)
        .attr("y", ly)
        .attr("text-anchor", "middle")
        .attr("transform", "rotate(90 "+lx+" "+ly+")")
        .text(data['y_label']);

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
    var pdx = 20,
        pdy = 10;
    function move_point(coord, g, text) {
        var px = coord[0],
            py = coord[1];
        g.attr("transform", "translate(" + (px-pdx) + "," + (py-pdy) + ")");
        var f = d3.format(".3r");
        text.text(f(xScale.invert(px)) + ", " + f(yScale.invert(py)));
    }
    var px = xScale(data.default_coord.x),
        py = yScale(data.default_coord.y);
    var cur_point_g = polygon_g.append("g")
        .attr("transform", "translate(" + px + "," + py + ")");
    var cur_point = cur_point_g.append("circle")
        .attr("cx", pdx)
        .attr("cy", pdy)
        .attr("r", 5)
        .attr("class", "cur-point")
        .style("fill", "#2e3ccc");
    var cur_point_text = cur_point_g.append("text")
        .attr("x", 0)
        .attr("y", 0)
        .attr("text-anchor", "middle")
        .style("font-size", "0.7em");
    move_point([px, py], cur_point_g, cur_point_text);

    // Compound Labels
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

    // Check if click in relevant region if necessary
    // On click, get new dfe
    var _ = this;
    console.log(svg);
    polygon_g.on("click", function() {
        var only_relevant = $("#only_relevant_dfe").prop("checked");
        var coords = d3.mouse(this);
        var inverted_coords = [
            xScale.invert(coords[0]),
            yScale.invert(coords[1])
        ];
        move_point(coords, cur_point_g, cur_point_text);

        _.DFEDiagram.update(inverted_coords, only_relevant, relevant_region)
    });

}
} (jQuery));
