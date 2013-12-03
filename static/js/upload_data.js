$(window).load(function () {
    $('#status-display').hide();
    $('#coming-msg').hide();

    $('#import-button').click(function() {
        $('#import-button-holder').hide();
        $('#status-display').slideDown(function () {
            $('#import-form').submit();
        });
        return false;
    });
});