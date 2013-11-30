$(window).load(function () {
    $('#status-display').hide();
    $('#coming-msg').hide();

    $('#delete-button').click(function() {
        $('#delete-button-holder').hide();
        $('#status-display').slideDown(function () {
            $('#delete-form').submit();
        });
        return false;
    });
});
