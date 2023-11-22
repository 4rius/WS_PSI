$(document).ready(function(){
    $('select').formSelect();
        $.getJSON('/api/devices', function(data){
            $.each(data, function(key, value){
                $('#devices').append('<p id="' + key + '">' + key + ': Last seen: ' + value + ' <button class="btn waves-effect waves-light" onclick="ping(\'' + key + '\')">Ping</button></p>');
            });
        });
        get_port();
        $('#connect').prop('disabled', true);
    });

function update_devices() {
    $.getJSON('/api/devices', function(data){
        $('#devices').empty();
        $.each(data, function(key, value){
            $('#devices').append('<p id="' + key + '">' + key + ': Last seen: ' + value + ' <button class="btn waves-effect waves-light" onclick="ping(\'' + key + '\')">Ping</button></p>');
        });
    });
}

function ping(device) {
    $.get('/api/ping/' + device, function(data){
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