(function ($)
{

var self = this;

this.DFEDiagram = function(svg_div, chemical_potentials_coords, endpoint, data) {
    console.log("DFEDiagram constructor");
    this.svg_div = svg_div;
    this.chemical_potential = chemical_potentials_coords;
    this.endpoint = endpoint;
    data["resource_id"] = data["dfe_resource_id"];
    this.query_data = data;

    var defaults = {
        "height": 500,
        "width": 400,
        "padding": 30,
        "margin": {top: 20, right: 30, bottom: 20, left: 30},
    };

    this.colors = [
        "crimson",
        "green",
        "blue",
        "coral",
        "darkblue",
        "red",
        "darkgrey",
        "cyan",
        "mediumpurple",
        "lightskyblue",
        "black",
    ];
    this.options = defaults;

};

DFEDiagram.prototype.init = function() {
    console.log("DFEDiagram init");
    // Setup graph (without data)
    // TODO: jquery proxy?
   // setup_graph.call(this);
    // Get region data
    $.ajax({
        context: this,
        type: "GET",
        contentType: "application/json",
        dataType: "json",
        url: this.endpoint,
        async: true,
        data: $.extend({}, this.chemical_potential, this.query_data),
        success: function(data) {
            setup_graph.call(this, data);
            drawLines.call(this, data);
        },
        error: function(result){
            console.log("Ajax error: ", result)
        }
    })
};

DFEDiagram.prototype.update = function(coords) {
    this.chemical_potential = {"x": coords[0], "y": coords[1]};
    $.ajax({
        context: this,
        type: "GET",
        contentType: "application/json",
        dataType: "json",
        url: this.endpoint,
        async: true,
        data: $.extend({}, this.chemical_potential, this.query_data),
        success: drawLines,
        error: function(result){
            console.log("Ajax error: ", result)
        }
    })
}

function setup_graph(data) {
    var margin = this.options.margin,
        width = this.options['width'] - margin.left - margin.right,
        height = this.options['height'] - margin.top - margin.bottom;

    var padding = this.options['padding'];
    this.bounds = data.bounds;
    this.xScale = d3.scaleLinear().domain([this.bounds[0][0], this.bounds[0][1]]).range([0, width]);
    this.yScale = d3.scaleLinear().domain([this.bounds[1][0], this.bounds[1][1]]).range([height, 0]);

    var svg_whole = d3.select(this.svg_div).append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom);
    this.svg = svg_whole.append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    // Axis
    var xAxis = d3.axisBottom(this.xScale);
    var yAxis = d3.axisRight(this.yScale);
    var xAxisG = this.svg.append("g")
        .attr("transform", "translate(0 " + 0 + ")")
        .call(xAxis);
    var yAxisG = this.svg.append("g")
        .call(yAxis);

    xAxisG.selectAll("text")
        .attr("transform", "translate(0, -20)")
    yAxisG.selectAll("text")
        .attr("transform", "translate(-38, 0)");

    var _ = this;

    this.polyline_g = this.svg.append("g");
    this.polyline_g.append("clipPath")
        .attr("id", "dfe-clip")
        .append("rect")
        .attr("width", width)
        .attr("height", height);

    this.polyline_minor_bounds_x = this.svg.append("g")
        .attr("class", "minor-bound");
    this.polyline_minor_bounds_x.selectAll("polyline").data(data.minor_bounds[0]).enter()
        .append("polyline")
        .attr("points", function(d) {
            s = "" + _.xScale(d) + "," + 0 + " ";
            s += _.xScale(d) + "," + height;
            console.log("xs", s);
            return s
        })
        .style("stroke", "gray");
    this.polyline_minor_bounds_y = this.svg.append("g")
        .attr("class", "minor-bound");
    this.polyline_minor_bounds_y.selectAll("polyline").data(data.minor_bounds[1]).enter()
        .append("polyline")
        .attr("points", function(d) {
            s = "0" + "," + _.yScale(d) + " ";
            s += width + "," + _.yScale(d);
            console.log("ys", s);
            return s
        })
        .style("stroke", "gray")
        .style("stroke-dasharray", "2, 3")
        .attr("class", "minor-bounds");


    // TODO: dfe-labels bad
    var legend_div = document.createElement("DIV");
    //document.getElementsByName(this.svg_div).appendChild(legend_div);
    //d3.select(legend_div).append()
    var divs_in_legend = d3.select(this.svg_div).select("#dfe-labels").append("div").selectAll("div").data(data.lines).enter()
        .append("div");
    divs_in_legend.append("span").text("____").style("color", function(d, i) {return _.colors[i % _.colors.length]});
    divs_in_legend.append("span").text(function(d) { return d.label;});
}

function reset_lines() {
        //$("polyline", this.svg_div).remove();
    this.polyline_g.selectAll("polyline").remove();
}

function drawLines(data) {
    reset_lines.call(this);

    // Polylines
    var _ = this;
    //var color = d3.scaleOrdinal(d3.schemeCategory10);
    this.polyline_g.selectAll("polyline").data(data.lines).enter().append("polyline").attr("points", function(d) {
        s = "";
        d.vertices.forEach(function(vert){
            vert = [_.xScale(vert[0]), _.yScale(vert[1])];
            s += vert.toString() + " ";
        });
        return s;
    }).style("stroke", function(d, i) {
       return _.colors[i % _.colors.length];
    }).style("fill", "None")
        .attr("clip-path", "url(#dfe-clip)");

    //// Labels
    //regions.forEach(function(region) {
    //    if(region.vertices.length > 0) {
    //        var center = get_center(region.vertices);
    //        region.cx = center[0];
    //        region.cy = center[1];
    //    }
    //});

    //svg.selectAll("text.region_label").data(regions).enter().append("svg:text").text(function(d) {
    //    return d.formula;
    //}).attr("x", function(d) {return xScale(d.cx);})
    //    .attr("y", function(d) {return yScale(d.cy);})
    //    .attr("text-anchor", "middle").attr("class", "region_label");

}

} (jQuery));
