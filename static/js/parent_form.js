/**
 * Client-side logic for allowing a parent to complete a CDI form online.
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


var currentPage = 1;
var finalPage = null;


function scrollToBottom() {
    $("html, body").animate({ scrollTop: $(document).height()-$(window).height() });
}


function goToNext() {
    currentPage++;
    $('#cur-page-display').html(currentPage);
    $('.parent-form-category').fadeOut();
    $('#category-' + currentPage.toString()).fadeIn(function() {
        window.location.hash = '#' + currentPage;
        $('html, body').animate({scrollTop:$('#category-' + currentPage.toString()).offset().top - 150});
    });

    if (currentPage == finalPage) {
        $('#next-link').hide();
        $('#parent-submit-button').show();
    } else {
        $('#next-link').show();
        $('#parent-submit-button').hide();
    }
    $('#previous-link').show();

    return false;
}


$(window).on('hashchange',function() {
    var hash = location.hash.substring(1);
    currentPage = parseInt(hash);

    if (isNaN(currentPage))
        currentPage = 1;

    $('#cur-page-display').html(currentPage);
    $('.parent-form-category').hide();
    $('#category-' + currentPage.toString()).show();

    if (currentPage == 1) {
        $('#previous-link').hide();
        $('#next-link').show();
        $('#parent-submit-button').hide();
    } else if (currentPage == finalPage) {
        $('#next-link').hide();
        $('#parent-submit-button').show();
        $('#previous-link').show();
    } else {
        $('#previous-link').show();
        $('#next-link').show();
        $('#parent-submit-button').hide();
    }
});


function goToPrevious() {
    currentPage--;
    $('#cur-page-display').html(currentPage);
    $('.parent-form-category').hide();
    $('#category-' + currentPage.toString()).fadeIn(function() {
        window.location.hash = '#' + currentPage;
        $('html, body').animate({scrollTop:$('#category-' + currentPage.toString()).offset().top - 150}, 1);
    });

    if (currentPage == 1) {
        $('#previous-link').hide();
    } else {
        $('#previous-link').show();
    }
    $('#next-link').show();
    $('#parent-submit-button').hide();

    return false;
}


$( document ).ready(function() {
    $('#next-link').click(goToNext);
    $('#previous-link').click(goToPrevious);
    $('#previous-link').hide();

    $('#cur-page-display').html(currentPage);
    $('.parent-form-category').hide();
    $('#category-' + currentPage.toString()).fadeIn();

    finalPage = parseInt($('#total-pages').html());
});
