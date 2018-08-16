(function ($)
{

var self = this;

this.DFEDiagram = function(svg_div, chemical_potentials_coords, compound_formation_energy, endpoint, params, query_data, result_parser) {
    this.svg_div = svg_div;
    this.chemical_potential = chemical_potentials_coords;
    this.compound_formation_energy = compound_formation_energy;
    this.endpoint = endpoint;
    if(query_data.dfe_resource_id)
      query_data["resource_id"] = query_data["dfe_resource_id"];
    this.query_data = query_data;
    this.result_parser = result_parser;

    var defaults = {
        "height": 500,
        "width": 400,
        "margin": {top: 35, right: 30, bottom: 20, left: 37},
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
    this._params = params;
    this.params = Object.assign({}, defaults, this._params.dfe_params);
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
        data: setup_query_data(this),
        success: function(data) {
            if(this.result_parser) {
              data = this.result_parser(data);
            }
            setup_graph.call(this, data);
            drawLines.call(this, data);
        },
        error: function(result){
            console.log("Ajax error: ", result)
        }
    })
};

DFEDiagram.prototype.update = function(coords, only_relevant, relevant_region) {
    // only_relevant: bool, relevant_region: halfspaces 
    this.chemical_potential = {"x": coords[0], "y": coords[1]};
    var data = setup_query_data(this, {"only_relevant": only_relevant, "relevant_region": relevant_region});
    console.log("data ", data);
    $.ajax({
        context: this,
        type: "GET",
        contentType: "application/json",
        dataType: "json",
        url: this.endpoint,
        async: true,
        data: data,
        success: function(data) {
          if(this.result_parser) {
            data = this.result_parser(data);
          }
          if(data["status"] == 0) {
            drawLines.call(this, data);
          } else {
            reset_lines.call(this);
          }
        },
        error: function(result){
            console.log("Ajax error: ", result)
        }
    })
};

function setup_query_data(_this, extras) {
    return $.extend({}, _this.chemical_potential, {"compound_formation_energy": _this.compound_formation_energy}, _this.query_data, extras);
}

function setup_graph(data) {
    var margin = this.params.margin,
        width = this.params['width'] - margin.left - margin.right,
        height = this.params['height'] - margin.top - margin.bottom;

    var padding = this.params['padding'];
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
        .attr("transform", "translate(-27, 0)");

    var labels = svg_whole.append("g");
    labels.append("text")
        .attr("x", this.params['width']/2)
        .attr("y", 15)
        .attr("text-anchor", "middle")
        .text(data['x_label']);
    var lx = 12,
        ly = this.params.height/2;
    labels.append("text")
        .attr("x", lx)
        .attr("y", ly)
        .attr("text-anchor", "middle")
        .attr("transform", "rotate(270"+" "+lx+" "+ly+")")
        .text(data['y_label']);

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
            return s
        })
        .style("stroke", "gray")
        .style("stroke-dasharray", "2, 3")
        .attr("class", "minor-bounds");

    // intrinsic fermi level
    var iflx = data.intrinsic_fermi_level[0],
        ifly = data.intrinsic_fermi_level[1],
        siflx = _.xScale(iflx),
        sifly = _.yScale(ifly);
    this.intrinsic_fermi_level_g = this.svg.append("g");
    this.intrinsic_fermi_level_g.append("line")
        .attr("x1", 0).attr("y1", 0)
        .style("stroke-width", "1")
        .style("stroke", "black");
    this.intrinsic_fermi_level_g.append("polygon");
    move_ifl_indicator.call(this, siflx, sifly);

    // TODO: dfe-labels in a separate plain div, lines in legened look bad
    d3.select(this.svg_div).append("div").attr("id", "dfe-labels");
    var divs_in_legend = d3.select(this.svg_div).select("#dfe-labels").append("div").selectAll("div").data(data.lines).enter()
        .append("div");
    divs_in_legend.append("span").text("____").style("color", function(d, i) {return _.colors[i % _.colors.length]});
    divs_in_legend.append("span").text(function(d) { return d.label;});
}

function move_ifl_indicator(x, y) {
    var margin = this.params.margin,
        width = this.params['width'] - margin.left - margin.right,
        height = this.params['height'] - margin.top - margin.bottom;
    var aw = 3,
        ah = 6;
    if(y > height) {
      this.intrinsic_fermi_level_g
        .style("display", "none");
    } else {
      this.intrinsic_fermi_level_g
        .attr("transform", "translate(" + x + "," + y + ")")
        .style("display", "initial");
      this.intrinsic_fermi_level_g.select("line")
        .attr("x2", 0).attr("y2", height-y-ah);
      this.intrinsic_fermi_level_g.select("polygon")
        .attr("points", ""+-aw+","+(height-y-ah)+" "+aw+","+(height-y-ah)+" "+0+","+(height-y));
    }
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

    move_ifl_indicator.call(this, _.xScale(data.intrinsic_fermi_level[0]), _.yScale(data.intrinsic_fermi_level[1]));
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
