function init_element_selects(select_div, data, default_values, endpoint, query_data, phase_diagram_init_func, result_parser) {
    function submit($form, phase_diagram_init) {
        // Query_data will be the values in the selects
        var elements = [];
        var elements_nums = [];
        $form.find(".pd-element-number").each(function(index, ele_num) {
            var ele = $(this).find(".pd-ele").val();
            var num = $(this).find(".pd-ele-num").val();
            elements.push(ele);
            elements_nums.push([ele, num]);
        });
        // Check that the selected values are allowed, IE we have resources named after it
        function check_allowed() {
          var material = $(select_div+" "+"#pd-material-type").find("option[selected]").attr("value");
          var material_dict = get_material_dict(data, material);
          var allowed = material_dict.allowed;
          for(var i = 0; i < allowed.length; i++) {
              var good = true;
              var chem = allowed[i];
              for(var j = 0; j < elements_nums.length; j++) {
                  if(chem[elements_nums[0]] != elements_nums[1]){
                      good = false;
                      break;
                  }
              }
              if(good){
                  return true
              }
          }
          return false
        }
        if(!check_allowed()) {
            // Do not submit, show message
            alert("No data found for selected compound. Check the resources of this dataset");
            return
        }
        var qd = {
            material: material,
            property: $(select_div+" "+"#pd-property").find("option[selected]").attr("value"),
            elements_nums: elements_nums
        };
        $.extend(query_data, qd);
        console.log("Submitting element selections");
        $.ajax({
           content: this,
           type: "GET",
           contentType: "application/json",
           dataType: "json",
           url: endpoint,
            async: true,
            data: query_data,
            success: function(phase_diagram_query_data) {
                if(result_parser) {
                  phase_diagram_query_data = result_parser(phase_diagram_query_data);
                }
                if(phase_diagram_query_data.success === false) {
                  validation_msg(phase_diagram_query_data.msg);
                }
                else {
                  phase_diagram_init(phase_diagram_query_data);
                  validation_msg("");
                }
            },
            error: function(result){
                console.log("element_select submit Ajax error: ", result)
            }
        });
    }
    function validation_msg(string) {
      $(select_div).find("#pd-elements-msg").text(string);
    }
    var $element_select_div = $(select_div+" "+"#pd-element-selects");
    // Create the selects
    // material
    var $materials = $(select_div+" "+"#pd-material-type");
    for(var i =0; i<data.materials.length; i++) {
        // Find matchng material
        var value = data.materials[i].material,
            text = data.materials[i].text;
        if(value == default_values.material) {
            $materials.append($("<option>", {value:value, text:text, selected:"selected"}));
        }
        else {
            $materials.append($("<option>", {value:value, text:text}));
        }
    }
    // property
    var $properties = $(select_div+" "+"#pd-property");
    create_property_select($properties, data, default_values);
    // elements
    var $element_selects_div = $(select_div+" "+"#pd-element-selects");
    create_element_num_selects($element_selects_div, data, default_values);
    // Attach submit to button
    var $submit_button = $(select_div+" "+"button");
    $submit_button.on("click", function(event) { // TODO: submit not click. Something's wrong with the button
        event.preventDefault();
        var $form = $(select_div);
        submit($form, phase_diagram_init_func);
    });
}
function get_material_dict(data, material) {
    var materials = data.materials;
    for(var i=0; i<materials.length; i++) {
        if(materials[i].material==material){
            return materials[i];
        }
    }
}
function create_property_select($property_select, data, selected_values) {
    var properties = get_material_dict(data, selected_values.material).properties;
    for(var i=0; i<properties.length; i++) {
        var p = properties[i];
        if(p[0] == selected_values.property) {
            $property_select.append($("<option>", {value:p[0], text:p[1], selected:"selected"}));
        }
        else {
            // NOTE: Hardcoded, only formation energy is selectable
            $property_select.append($("<option>", {value:p[0], text:p[1], disabled:"disabled"}));
        }
    }
}
function create_element_num_selects($selects_div, data, selected_values) {
    var element_groups = get_material_dict(data, selected_values.material).elements;
    for(var i = 0; i<element_groups.length; i++) {
        var group_choices = element_groups[i]; // data for elements in this group that you can pick
        var selected_ele = selected_values.elements_nums[i][0];
        // Find matching
        var $ele_div = $("<span>", {class: "pd-element-number"});
        var $ele = $("<select>", {class: "pd-ele"});
        for(var j=0; j<group_choices.length; j++) {
            var element_data = group_choices[j];
            var option_attrs = {value: element_data.text, text: element_data.text};
            if(element_data.text == selected_ele) {
                option_attrs["selected"] = "selected";
                var $num = $("<select>", {class: "pd-ele-num"});
                var num_values = element_data.values;
            }
            $ele.append($("<option>", option_attrs));
        }
        var selected_num = selected_values.elements_nums[i][1];
        element_num_select($num, num_values, selected_num);
        $ele_div.append($ele);
        $ele_div.append($num);
        $selects_div.append($ele_div);
    }
}

function element_num_select($num, nums, selected_num) {
    // Change number selections
    // Clear and add the new numbers
    $num.html("");
    for(var i=0; i<nums.length; i++) {
        var n = nums[i];
        if(n == selected_num){
          $num.append($("<option>", {value: n, text: n, selected:"selected"}));
        }
        else{
          $num.append($("<option>", {value: n, text: n}));
        }
    }
}

