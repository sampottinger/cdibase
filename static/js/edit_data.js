var ENTER_KEY = 13;

var selectedGlobalID = null;


$('#method-dropdown').change(function() {
    var selectedMethod = $('#method-dropdown').find(':selected').val();

    if(selectedMethod === 'by_global_id') {
        $('#by-study-id-panel').slideUp();
        $('#by-global-id-panel').slideDown();
    } else if(selectedMethod === 'by_study_id') {
        $('#by-global-id-panel').slideUp();
        $('#by-study-id-panel').slideDown();
    }
});

function hideAllForLoading() {
    $('#inner-lookup-instructions-panel').hide();
    $('#expected-lookup-error').hide();
    $('#unexpected-lookup-error').hide();
    $('#loading-lookup-panel').hide();
    $('#edit-pane').hide();
}

function hideAllForUpdate() {
    $('#update-success-msg').hide();
    $('#update-fail-msg').hide();
    $('#loading-update-panel').hide();
}

function onLookupSuccess(data) {
    hideAllForLoading();
    hideAllForUpdate();

    selectedGlobalID = data['global_id'];

    // Rearrange birthday
    var isoBirthday = data['metadata']['birthday'];
    var birthdayComponents = isoBirthday.split('/');
    var humanBirthday = birthdayComponents[1] + '/';
    humanBirthday += birthdayComponents[2] + '/';
    humanBirthday += birthdayComponents[0];

    // Display free text properties
    $('#global-id-display').html(selectedGlobalID);
    $('#birthday-input').val(humanBirthday);
    $('#languages-input').val(data['metadata']['languages']);

    // Display radio button values
    $('.gender-radio[value=' + data['metadata']['gender'] + ']')
        .attr('checked', true);

    var hardOfHearingVal = data['metadata']['hard_of_hearing'];
    $('.hard-of-hearing-radio[value=' + hardOfHearingVal + ']')
        .attr('checked', true);

    // Display table of studies
    $('#study-body').find('tr').remove();
    data['studies'].forEach(function(studyInfo) {
        var row = $('<tr>');
        row.append('<td>' + studyInfo['study'] + '</td>');
        row.append('<td>' + studyInfo['study_id'] + '</td>');
        $('#study-body').append(row);
    });

    $('#edit-pane').fadeIn();
}

function onLookupUnexpectedFailure() {
    hideAllForLoading();
    $('#unexpected-lookup-error').fadeIn();
    return false;
}

function onLookupNotFound() {
    hideAllForLoading();
    $('#expected-lookup-error').fadeIn();
    return false;
}

function onUpdateSuccess() {
    hideAllForUpdate();
    $('#update-success-msg').slideDown();
    return false;
}

function onUpdateFailure(jqXHR) {
    hideAllForUpdate();
    $('#update-fail-msg-details').html(jqXHR.responseText);
    $('#update-fail-msg').slideDown();
    return false;
}

function executeLookup() {
    var selectedMethod = $('#method-dropdown').find(':selected').val();
    var data;

    function sendRequest() {
        if(selectedMethod === 'by_global_id') {
            data = {
                method: 'by_global_id',
                global_id: $('#child-id-input').val()
            };
        } else if(selectedMethod === 'by_study_id') {
            data = {
                method: 'by_study_id',
                study_id: $('#study-input').val(),
                study: $('#study-id-input').val()
            };
        }

        $.ajax({
            type: 'POST',
            url: '/base/edit_data/lookup_user',
            data: data,
            statusCode: {
                200: onLookupSuccess,
                404: onLookupNotFound,
                400: onLookupUnexpectedFailure
            },
            dataType: 'json'
        });
    }

    selectedGlobalID = null;
    hideAllForLoading();
    $('#loading-lookup-panel').fadeIn(sendRequest);

    return false;
}

function executeUpdate() {
    if(selectedGlobalID === null) {
        return;
    }

    function sendRequest() {
        var genderVal = $('.gender-radio:checked').val();
        var rawBirthdayVal = $('#birthday-input').val();
        var languagesVal = $('#languages-input').val();
        var hardOfHearingVal = $('.hard-of-hearing-radio:checked').val();

        // Rearrange birthday if date provided with forward slashes
        var birthdayComponents = rawBirthdayVal.split('/');
        var birthdayVal;
        if (birthdayComponents.length == 3) {
            var birthdayVal = birthdayComponents[2] + '/';
            birthdayVal += birthdayComponents[0] + '/';
            birthdayVal += birthdayComponents[1];
        } else {
            birthdayVal = rawBirthdayVal;
        }

        var data = {
            global_id: selectedGlobalID,
            gender: genderVal,
            birthday: birthdayVal,
            languages: languagesVal,
            hard_of_hearing: hardOfHearingVal
        };

        $.ajax({
            type: 'POST',
            url: '/base/edit_data',
            data: data,
            statusCode: {
                200: onUpdateSuccess,
                400: onUpdateFailure
            },
            complete: function() {
                $('#update-participant-button').slideDown();
            },
            dataType: 'json'
        });
    }

    $('#update-participant-button').slideUp();
    $('#loading-update-panel').slideDown(sendRequest);

    return false;
}

$('.lookup-end-input').keyup(function(e){
    if (e.keyCode == ENTER_KEY) { executeLookup(); }
});

$('.update-end-input').keyup(function(e){
    if (e.keyCode == ENTER_KEY) { executeUpdate(); }
});

$('#find-participant-button').click(executeLookup);

$('#update-participant-button').click(executeUpdate);
