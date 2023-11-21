$(document).ready(function(){
        $.getJSON('/api/devices', function(data){
            $.each(data, function(key, value){
                $('#devices').append('<p id="' + key + '">' + key + ': Last seen: ' + value + ' <button class="btn waves-effect waves-light" onclick="ping(\'' + key + '\')">Ping</button></p>');
            });
        });
        get_port();
    });

    function ping(device) {
        $.get('/api/ping/' + device, function(data){
            $('#' + device).text(device + ': Last seen: ' + data.time);
            alert(data.status);
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
        });
    }

    function disconnect() {
        $.post('/api/disconnect', function(data){
            alert(data.status);
        });
    }