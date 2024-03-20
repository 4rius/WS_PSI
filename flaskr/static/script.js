$(document).ready(function(){
    $('select').formSelect();
    update_devices();
    get_port();
    get_id();
    $('#connect').prop('disabled', true);
});

function get_id() {
    $.get('/api/id', function(data){
        $('#id').text(data.id);
    });
}

function loader() {
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
}

function update_devices() {
    loader();
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
            '<button class="btn waves-effect waves-light" onclick="FindIntersection(\'' + key + '\', \'' + 'Paillier' + '\')">Paillier</button>'
            +
            ' <button class="btn waves-effect waves-light" onclick="FindIntersection(\'' + key + '\', \'' + 'Damgard-Jurik' + '\')">Damgard-Jurik</button></p>' +
            ' <button class="btn waves-effect waves-light" onclick="FindIntersection(\'' + key + '\', \'' + 'Paillier OPE' + '\', \'' + 'PSI' +'\')">Paillier - OPE</button>' +
            ' <button class="btn waves-effect waves-light" onclick="FindIntersection(\'' + key + '\', \'' + 'Damgard-Jurik OPE' + '\', \'' + 'PSI' +'\')">Damgard-Jurik - OPE</button>' +
            ' <button class="btn waves-effect waves-light" onclick="FindIntersection(\'' + key + '\', \'' + 'Paillier OPE PSI-CA' + '\', \'' + 'PSI-CA' +'\')">Cardinality - Paillier</button>' +
            ' <button class="btn waves-effect waves-light" onclick="FindIntersection(\'' + key + '\', \'' + 'Damgard-Jurik OPE PSI-CA' + '\', \'' + 'PSI-CA' +'\')">Cardinality - Damgard-Jurik</button>' +
            ' <button class="btn waves-effect waves-light" onclick="test(\'' + key + '\')">STRESS TEST</button>'
            );
        });
    });
}

function ping(device) {
    loader();
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
function int_paillier(device) {
    $.post('/api/int_paillier/' + device, function(data){
    }).done(function(data){
        const message = data.status;
        M.toast({html: message});
    })
    .fail(function() {
        M.toast({html: "Error returned, likely the node threw an exception. Check the logs for more information."});
    });
}

function int_dj(device) {
    $.post('/api/int_dj/' + device, function(data){
    }).done(function(data){
        const message = data.status;
        M.toast({html: message});
    })
    .fail(function() {
        M.toast({html: "Error returned, likely the node threw an exception. Check the logs for more information."});
    });
}

function int_paillier_ope(device) {
    $.post('/api/int_paillier_ope/' + device, function(data){
    })
    .done(function(data) {
        const message = data.status;
        M.toast({html: message});
    })
    .fail(function() {
        M.toast({html: "Error returned, likely the node threw an exception. Check the logs for more information."});
    });
}

function int_dj_ope(device) {
    $.post('/api/int_dj_ope/' + device, function(data){
    })
    .done(function(data) {
        const message = data.status;
        M.toast({html: message});
    })
    .fail(function() {
        M.toast({html: "Error returned, likely the node threw an exception. Check the logs for more information."});
    });
}

function ca_paillier(device) {
    $.post('/api/ca_paillier/' + device, function(data){
    })
    .done(function(data) {
        const message = data.status;
        M.toast({html: message});
    })
    .fail(function() {
        M.toast({html: "Error returned, likely the node threw an exception. Check the logs for more information."});
    });
}

function FindIntersection(device, scheme, type) {
    $.post(`/api/intersection?device=${device}&scheme=${scheme}&type=${type}`, function(data){
    })
    .done(function(data) {
        const message = data.status;
        M.toast({html: message});
    })
    .fail(function() {
        M.toast({html: "Error returned, likely the node threw an exception. Check the logs for more information."});
    });
}

function test(device) {
    $.post(`/api/test?device=${device}`, function(data){
    })
    .done(function(data) {
        const message = data.status;
        M.toast({html: message});
    })
    .fail(function() {
        M.toast({html: "Error returned, likely the node threw an exception. Check the logs for more information."});
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
        window.open().document.write('<pre>' + message + '</pre>');
    });
}

function my_data() {
    $.get('/api/dataset', function(data){
        const message = "Dataset: " + data.dataset;
        window.open().document.write('<pre>' + message + '</pre>');
    });
}

function results() {
    $.get('/api/results', function(data){
        const message = "Result: " + JSON.stringify(data.result, null, 2);
        window.open().document.write('<pre>' + message + '</pre>');
    });
}

function genkeys(scheme) {
    $.post(`/api/genkeys?scheme=${scheme}`, function(data){
        const message = data.status;
        M.toast({html: message});
    });
}

function discover_peers() {
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
    $.ajax({
        type: 'POST',
        url: '/api/discover_peers',
        beforeSend: function() {
            // Muestra el spinner antes de enviar la solicitud
            $('.preloader-wrapper').show();
        },
        success: function(data) {
            const message = data.status;
            M.toast({html: message});

            // Espera 2 segundos antes de ocultar el spinner
            setTimeout(function() {
                $('.preloader-wrapper').hide();
                update_devices();
            }, 2000);
        }
    });
}

