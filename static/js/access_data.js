$(window).load(function () {
    $('#status-display').hide();
    $('#coming-msg').hide();
    $('#studies-list').hide();

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

    $('.study-id-link').click(function (event) {
        var study = $(event.target).html();
        var operand =  $('#operand-input').val();
        if (operand === '')
            operand = study;
        else
            operand += ',' + study;
        $('#operand-input').val(operand);
        return false;
    });

    $('#field-select').change(function (event) {
        var val = $(event.target).val();
        if (val === 'study') {
            $('#studies-list').slideDown();
        } else {
            $('#studies-list').slideUp();
        }
    });

});