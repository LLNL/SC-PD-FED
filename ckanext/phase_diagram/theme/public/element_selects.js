function init_element_selects(select_div, data, default_values) {
    var $element_select_div = $(select_div+" "+"#pd-element-selects");
    // Create the selects
    // material
    var $materials = $(select_div+" "+"#pd-material-type");
    for(var material in data.materials) {
        $materials.append($("<option>", {value:material, text:data.materials[material].text}));

    }
    // property
    var $properties = $(select_div+" "+"#pd-property");
    property_select($properties, data, default_values);
    // elements
    var $element_selects_div = $(select_div+" "+"#pd-element-selects");
    property_select($element_selects_div, data, default_values);
}
function property_select($property_select, data, selected_value) {
    var properties = data.materials[selected_value.material].properties;
    for(var p in properties) {
        $property_select.append($("<option>", {value:p[0], text:p[1]}));
    }
}
function init_element_select($selects_div, data, selected_values) {
    var element_group = data.materials[selected_values.material].elements;
    for(var i = 0; i<element_group.length; i++) {
        var group_choices = element_group[i]; // data for elements in this group that you can pick
        var selected_ele = selected_values[i];
        var ele_range = group_choices[selected_ele];
        var $ele_div = $("<div>", {class: "pd-element-number"});
        var $s = $("<select>", {class: "pd-ele"});
        for(var ele in group_choices) {
            $s.append($("<option>", {value: ele, text: group_choices[ele].text}));
        }
        var $num = $("<select>", {class: "pd-ele-num"});
        $ele_div.append($s);
        $ele_div.append($num);
        $selects_div.append($ele_div);
        element_num_select($ele_div, group_choices[selected_ele].text);
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

