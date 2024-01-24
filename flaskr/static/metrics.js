$(document).ready(function(){
    get_id();
    populate_table();
});

function get_id() {
    $.get('/api/id', function(data){
        $('#mylogs').text("Logs recuperados de " + data.id);
    });
}

function populate_table() {
    $.getJSON('/api/logs', function(data){
        $.each(data, function(key, value){
            $('#logs').append('<tr><td>' + value['timestamp'] + '</td><td>' + value['activity_code'] + '</td><td>' + value['time'] + '</td><td>' + value['RAM'] + '</td><td>' + value['Instance_RAM'] + '</td><td>' + value['CPU'] + '</td></tr>');
        });
    });
}
