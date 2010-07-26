
function new_message(reporter_id, div_id) {
    // uses jqModal to show a message popup in an ajaxy way.  Pass in the reporter
    // to message, and the div where you want to display your ajax.
    $(div_id).jqm({ajax: '/schools/message/' + reporter_id, trigger: 'div.messagetrigger'});
}
