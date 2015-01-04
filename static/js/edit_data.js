/**
 * Client-side logic for updating participant metadata.
 *
 * Copyright (C) 2014 A. Samuel Pottinger ("Sam Pottinger", gleap.org)
 * 
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
**/

var ENTER_KEY = 13;

var selectedGlobalID = null;


/**
 * Callback function when the user changes the participant lookup method.
 *
 * Callback function that changes the UI depending on which lookup method the
 * user selected (by database global ID or by study + study ID).
**/
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


/**
 * Hide all of the UI for looking up ("loading") a participant to edit.
 *
 * Convenience function that hides all of the user interface elements used to
 * look up a participant whose metadata needs updating. Some of the UI elements
 * are shown or hidden depending on the step the user is on within the edit
 * participant metadata proceedure.
**/
function hideAllForLoading() {
    $('#inner-lookup-instructions-panel').hide();
    $('#expected-lookup-error').hide();
    $('#unexpected-lookup-error').hide();
    $('#loading-lookup-panel').hide();
    $('#edit-pane').hide();
}


/**
 * Hide all of the UI for editing ("updating") a participant's metadata.
 *
 * Convenience function that hides all of the user interface elements used to
 * edit a participant's metadata. Some of the UI elements are shown or hidden
 * depending on the step the user is on within the edit participant metadata
 * proceedure.
**/
function hideAllForUpdate() {
    $('#update-success-msg').hide();
    $('#update-fail-msg').hide();
    $('#loading-update-panel').hide();
}


function makeDateHuman(isoDate) {
    var components = isoDate.split('/');
    var humanDate;

    if (components.length === 3) {
        humanDate = components[1] + '/';
        humanDate += components[2] + '/';
        humanDate += components[0];
    } else {
        humanDate = isoDate;
    }

    return humanDate;
}


function makeDateISO(humanDate) {
    var components = humanDate.split('/');
    var isoDate;
    if (components.length == 3) {
        isoDate = components[2] + '/';
        isoDate += components[0] + '/';
        isoDate += components[1];
    } else {
        isoDate = humanDate;
    }

    return isoDate;
}


/**
 * Respond to the user having successfully retrieved a participant.
**/
function onLookupSuccess(data) {
    hideAllForLoading();
    hideAllForUpdate();

    selectedGlobalID = data['global_id'];

    // Rearrange birthday
    var isoBirthday = data['metadata']['birthday'];
    var humanBirthday = makeDateHuman(isoBirthday);

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
    data['cdis'].forEach(function(studyInfo) {
        var checkboxCode = '<td class="cdi-selector-holder">'
        checkboxCode += '<input type="checkbox" class="cdi-selector" '
        checkboxCode += 'study="' + studyInfo['study'] + '" ';
        checkboxCode += 'studyid="' + studyInfo['id'] + '"';
        checkboxCode += '></input></td>';

        var row = $('<tr>');
        row.append(checkboxCode);
        row.append('<td>' + makeDateHuman(studyInfo['date']) + '</td>');
        row.append('<td>' + studyInfo['study'] + '</td>');
        row.append('<td>' + studyInfo['study_id'] + '</td>');
        $('#study-body').append(row);
    });

    $('#edit-pane').fadeIn();
}


/**
 * Respond to an unexpected error in a user looking up a participant.
**/
function onLookupUnexpectedFailure() {
    hideAllForLoading();
    $('#unexpected-lookup-error').fadeIn();
    return false;
}


/**
 * Respond to a user asking for a participant not in the lab database.
**/
function onLookupNotFound() {
    hideAllForLoading();
    $('#expected-lookup-error').fadeIn();
    return false;
}


/**
 * Respond to a user having successfully updated a participant's metadata.
 *
 * Show a confirmation / success message in response to a user having
 * successfully updated a participant's metadata.
**/
function onUpdateSuccess() {
    hideAllForUpdate();
    $('#update-success-msg').slideDown();
    return false;
}


/**
 * Respond to a user having tried but failed to update a participant's metadata.
 *
 * Show an error message with a description for why a user's attempt to update
 * a participant's metadata failed.
**/
function onUpdateFailure(jqXHR) {
    hideAllForUpdate();
    $('#update-fail-msg-details').html(jqXHR.responseText);
    $('#update-fail-msg').slideDown();
    return false;
}


/**
 * Lookup a participant based on user input. 
**/
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
                study_id: $('#study-id-input').val(),
                study: $('#study-input').val()
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


/**
 * Update a participant's metadata given updated user input.
**/
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
        var birthdayVal = makeDateISO(rawBirthdayVal);

        var snapshotIDs = [];
        $('.cdi-selector:checked').each(function() {
            var selection = $(this);
            var study = selection.attr('study');
            var id = parseInt(selection.attr('studyid'));
            snapshotIDs.push({study: study, id: id});
        });

        var data = {
            global_id: selectedGlobalID,
            gender: genderVal,
            birthday: birthdayVal,
            languages: languagesVal,
            hard_of_hearing: hardOfHearingVal,
            snapshot_ids: JSON.stringify(snapshotIDs)
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


// Attach listeners to textboxes and buttons
$('.lookup-end-input').keyup(function(e){
    if (e.keyCode == ENTER_KEY) { executeLookup(); }
});

$('.update-end-input').keyup(function(e){
    if (e.keyCode == ENTER_KEY) { executeUpdate(); }
});

$('#find-participant-button').click(executeLookup);

$('#update-participant-button').click(executeUpdate);
