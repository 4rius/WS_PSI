$(document).ready(function(){
    get_id();
    populate_table();
    document.getElementById('download-excel').addEventListener('click', downloadExcel);
});

function get_id() {
    $.get('/api/id', function(data){
        $('#mylogs').text("Logs recuperados de " + data.id);
    });
}

function populate_table() {
  $('#loading-spinner').show();

  $.getJSON('/api/logs', function(data){
      $('#logs').empty();

      $.each(data, function(key, value){
          $('#logs').append('<tr><td>' + value['timestamp'] + '</td><td>' + value['activity_code'] + '</td><td>' + value['time'] + '</td><td>' + value['Avg_RAM'] + '</td><td>' + value['Avg_instance_RAM'] + '</td><td>' + value['Avg_CPU'] + '</td><td>' + value['Avg_instance_CPU'] + '</td></tr>');
      });
  })
  .always(function() {
    $('#loading-spinner').hide();
  });
}

function downloadExcel() {
    const table = document.getElementById('logs');
    // Convertir la tabla a formato de SheetJS
    const ws = XLSX.utils.table_to_sheet(table);
    const wb = XLSX.utils.book_new();
    // Añadir la hoja de cálculo al libro
    XLSX.utils.book_append_sheet(wb, ws, 'Logs');
    // Generar el archivo
    XLSX.writeFile(wb, 'logs.xlsx');
}