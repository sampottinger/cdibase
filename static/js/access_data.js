/**
 * Client-side logic for making requests to access lab data.
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


$(window).load(function () {
    $('#status-display').hide();
    $('#coming-msg').hide();
    $('#studies-list').hide();

    $('#download-button').click(function() {
        $('#coming-msg').hide();
        $('#download-button-holder').hide();
        $('#coming-msg').slideDown(function () {
            $('#cdi-form').submit();
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