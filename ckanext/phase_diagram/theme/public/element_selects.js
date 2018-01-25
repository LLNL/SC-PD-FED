function init_element_selects(select_div, data, default_values, phase_diagram_init_func) {
    function submit($form, phase_diagram_init) {
        // Query_data will be the values in the selects
        var elements = [];
        var elements_nums = [];
        $(select_div+" "+"pd-ele-num").each(function(index, ele_num) {
            elements.append($(this).find("#pd-ele").attr("value"));
            elements_nums.append({ele: $(this).find("#pd-ele").attr("value"),
                             num: $(this).find("#pd-ele-number").attr("value")});
        });
        var query_data = {
            material: $(select_div+" "+"#pd-material-type").find("option[selected]").attr("value"),
            property: $(select_div+" "+"#pd-property").find("option[selected]").attr("value"),
            elements: elements,
            elements_nums: elements_nums
        };
        phase_diagram_init(query_data);
    }
    var $element_select_div = $(select_div+" "+"#pd-element-selects");
    // Create the selects
    // material
    var $materials = $(select_div+" "+"#pd-material-type");
    for(var i in data.materials) {
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
    $submit_button.on("submit", function(event) {
        var $form = $(select_div);
        submit($form, phase_diagram_init_func);
    });
}
function get_material_dict(data, material) {
    for(var i in data) {
        if(data[i].material==material){
            return data[i];
        }
    }
}
function create_property_select($property_select, data, selected_values) {
    var properties = get_material_dict(data, selected_values.material).properties;
    for(var i in properties) {
        var p = properties[i];
        if(p[0] == selected_values.property) {
            $property_select.append($("<option>", {value:p[0], text:p[1], selected:"selected"}));
        }
        else {
            $property_select.append($("<option>", {value:p[0], text:p[1]}));
        }
    }
}
function create_element_num_selects($selects_div, data, selected_values) {
    var element_groups = get_material_dict(data, selected_values.material).elements;
    for(var i = 0; i<element_groups.length; i++) {
        var group_choices = element_groups[i]; // data for elements in this group that you can pick
        var selected_ele = selected_values[i];
        // Find matching
        var $ele_div = $("<div>", {class: "pd-ele-number"});
        var $s = $("<select>", {class: "pd-ele"});
        for(var element_data in group_choices) {
            var option_attrs = {value: element_data.text, text: element_data.text};
            if(element_data.text == selected_ele) {
                option_attrs["selected"] = "selected";
            }
            $s.append($("<option>", option_attrs));
        }
        var $num = $("<select>", {class: "pd-ele-num"});
        $ele_div.append($s);
        $ele_div.append($num);
        $selects_div.append($ele_div);
        element_num_select($ele_div, selected_ele);
    }
}

function element_num_select($element_number_div, nums) {
    // Change number selections
    var $nums = $element_number_div.find(".pd-ele-num");
    // Clear and add the new numbers
    $nums.html("");
    for(var n in nums) {
        $nums.append($("option", {value: n, text: n}));
    }
}

