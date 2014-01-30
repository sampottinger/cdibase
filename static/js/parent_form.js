var currentPage = 1;
var finalPage = null;


function scrollToBottom() {
    $("html, body").animate({ scrollTop: $(document).height()-$(window).height() });
}


function goToNext() {
    currentPage++;
    $('#cur-page-display').html(currentPage);
    $('.parent-form-category').slideUp();
    $('#category-' + currentPage.toString()).slideDown(function() {
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
    $('#parent-submit-button').hide();
});


function goToPrevious() {
    currentPage--;
    $('#cur-page-display').html(currentPage);
    $('.parent-form-category').hide();
    $('#category-' + currentPage.toString()).slideDown(function() {
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