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


function goToPrevious() {
    currentPage--;
    $('#cur-page-display').html(currentPage);
    $('.parent-form-category').hide();
    $('#category-' + currentPage.toString()).fadeIn(function() {
        $('html, body').animate({scrollTop:$('#category-' + currentPage.toString()).offset().top - 150});
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