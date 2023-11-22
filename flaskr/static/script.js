$(document).ready(function(){
    $('select').formSelect();
        update_devices();
        get_port();
        $('#connect').prop('disabled', true);
    });

function update_devices() {
    $('#devices').html('<div class="preloader-wrapper small active">\
                            \n<div class="spinner-layer spinner-green-only">\
                            \n<div class="circle-clipper left">\
                            \n<div class="circle"></div>\
                            \n</div><div class="gap-patch">\
                            \n<div class="circle"></div>\
                            \n</div><div class="circle-clipper right">\
                            \n<div class="circle"></div>\
                            \n</div>\
                            \n</div>\
                            \n</div>');
    $.getJSON('/api/devices', function(data){
        $('#devices').empty();
        $.each(data, function(key, value){
            $('#devices').append('<p id="' + key + '">' + key + ': Last seen: ' + value + ' <button class="btn waves-effect waves-light" onclick="ping(\'' + key + '\')">Ping</button></p>');
        });
    });
}

function ping(device) {
    $.post('/api/ping/' + device, function(data){
    }).done(function(data){
        alert(data.status);
        update_devices();
    });
}

function get_port() {
    $.get('/api/port', function(data){
        $('#port').text(data.port);
    });

}

function connect() {
    $.post('/api/connect', function(data){
        alert(data.status);
        update_devices();
        get_port();
        $('#connect').prop('disabled', true);
        $('#disconnect').prop('disabled', false);
    });
}

function disconnect() {
    $.post('/api/disconnect', function(data){
        alert(data.status);
        update_devices();
        get_port();
        $('#connect').prop('disabled', false);
        $('#disconnect').prop('disabled', true);
    });
}