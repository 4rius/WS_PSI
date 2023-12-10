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
            let displayKey = key;
            // Check if the key is an IPv6 address
            if (/:/.test(key)) {
                // Abbreviate the IPv6 address for display
                displayKey = key.replace(/:.*:/, '::');
            }
            $('#devices').append('<p id="' + key + '">' + displayKey + ': Last seen: ' + value +
            ' <button class="btn waves-effect waves-light" onclick="ping(\'' + key + '\')">Ping</button>' +
            ' <button class="btn waves-effect waves-light" onclick="find_intersection(\'' + key + '\')">Buscar intersección</button>' +
            ' <button class="btn waves-effect waves-light" onclick="pubkey(\'' + key + '\')">Clave pública</button>');
            // +
            //' <button class="btn waves-effect waves-light red" onclick="hide_device(\'' + key + '\')">Hide Device</button></p>');
        });
    });
}

function ping(device) {
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
    $.post('/api/ping/' + device, function(data){
    }).done(function(data){
        const message = data.status;
        M.toast({html: message});
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
        const message = data.status;
        M.toast({html: message});
        update_devices();
        get_port();
        $('#connect').prop('disabled', true);
        $('#disconnect').prop('disabled', false);
    });
}

function disconnect() {
    $.post('/api/disconnect', function(data){
        const message = data.status;
        M.toast({html: message});
        update_devices();
        get_port();
        $('#connect').prop('disabled', false);
        $('#disconnect').prop('disabled', true);
    });
}

function find_intersection(device) {
    $.post('/api/intersection/' + device, function(data){
        alert(data.status);
    });
}

function pubkey(device) {
    $.get('/api/pubkey/' + device, function(data){
        alert(data.status);
    });
}

function mykeys() {
    $.get('/api/mykeys', function(data){
        const message = "Clave pública: " + "\nN: " + data.pubkeyN + "\ng: " + data.pubkeyG
            + "\nClave privada: " + "\nP: " + data.privkeyP + "\nQ: " + data.privkeyQ;
        alert(message);
    });
}
