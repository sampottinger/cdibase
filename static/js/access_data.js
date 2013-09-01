function restoreDownloadButton () {
    $('#status-display').hide();
    $('#download-button-holder').slideDown(function () {
        $('#coming-msg').fadeIn();
    });
}


function checkIfDone () {
    $.getJSON('/access_data/is_waiting', function(status) {
        if (!status.is_waiting)
            restoreDownloadButton();
        else
            setTimeout(checkIfDone, 1000);
    });
}


$(window).load(function () {
    $('#status-display').hide();
    $('#coming-msg').hide();

    $('#download-button').click(function() {
        $('#download-button-holder').hide();
        $('#status-display').slideDown(function () {
            var url = '/access_data/download_mcdi_results?';
            url = url +  $('#mcdi-form').serialize();
            $('#hidden-frame').attr('src', url);
            checkIfDone();
        });
        return false;
    });

    $('#abort-link').click(function () {
        restoreDownloadButton();
        return false;
    });

});