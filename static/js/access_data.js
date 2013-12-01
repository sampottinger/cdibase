$(window).load(function () {
    $('#status-display').hide();
    $('#coming-msg').hide();

    $('#download-button').click(function() {
        $('#coming-msg').hide();
        $('#download-button-holder').hide();
        $('#coming-msg').slideDown(function () {
            $('#mcdi-form').submit();
            $('#download-button-holder').fadeIn();
        });
        return false;
    });

    $('#abort-link').click(function () {
        restoreDownloadButton();
        return false;
    });

});