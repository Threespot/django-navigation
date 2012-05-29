(function($) {
    $(document).ready(function(){
        $("#rebuild-nav a").click(function(evt) {
            var message = $('<div id="rebuild-message"></div>');
            message.css({
                'background': '#fff',
                'border': '6px solid #417690',
                'font-size': '12px',
                'font-weight': 'bold',
                'height': '18px',
                'left': '200px',
                'padding': '15px',
                'position': 'absolute',
                'text-align': 'center',
                'top': '50px',
                'width': '260px',
                'z-index': '1000',
                '-webkit-box-shadow':  '4px 4px 8px 8px rgba(0, 0, 0, .6)',
                'box-shadow':  '4px 4px 8px 8px rgba(0, 0, 0, .6)'

            }).html("Please wait while the nav is rebuilt...")
            $("#container").prepend(message);
            evt.preventDefault();
            $.get($(this).attr("href"), function(data, status) {
                message.html("Done. " + data)
                setTimeout(function () { message.fadeOut(); }, 1700);
            })
        });
    });
})(django.jQuery)