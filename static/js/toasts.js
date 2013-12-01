$(window).load(function () {
    $('.confirmation')
    .hide()
    .slideDown(function () {
        $('.icon-white').css({
            'background-image': 'url("/static/img/glyphicons-halflings-white.png")'
        });
    })
    .delay(3000)
    .slideUp();
    
    $('.error')
    .hide()
    .slideDown(function () {
        $('.icon-white').css({
            'background-image': 'url("/static/img/glyphicons-halflings-white.png")'
        }).fadeOut(function () {
            $('.icon-white').fadeIn();
        });
    });
});