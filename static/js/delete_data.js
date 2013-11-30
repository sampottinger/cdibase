function restoreDeleteButton () {
    $('#status-display').hide();
    $('#delete-button-holder').slideDown(function () {
        $('#coming-msg').fadeIn();
    });
}


function checkIfDone () {
    $.getJSON('/base/delete_data/is_waiting', function(status) {
        if (!status.is_waiting)
            restoreDeleteButton();
        else
            setTimeout(checkIfDone, 1000);
    });
}


$(window).load(function () {
    $('#status-display').hide();
    $('#coming-msg').hide();

    $('#delete-button').click(function() {
        $('#delete-button-holder').hide();
        $('#status-display').slideDown(function () {
            var url = '/base/delete_data/delete_mcdi_results?';
            url = url +  $('#mcdi-form').serialize();
            $('#hidden-frame').attr('src', url);
            checkIfDone();
        });
        return false;
    });
});