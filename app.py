function doGet(e) {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  var rows = sheet.getDataRange().getValues();
  var headers = rows[0];
  var data = [];
  
  for (var i = 1; i < rows.length; i++) {
    var row = rows[i];
    var record = {};
    for (var j = 0; j < headers.length; j++) {
      record[headers[j]] = row[j];
    }
    data.push(record);
  }
  
  return ContentService.createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
}

function doPost(e) {
  try {
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
    var data = JSON.parse(e.postData.contents);
    
    var headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
    var idColIndex = headers.indexOf("id");
    
    var rows = sheet.getDataRange().getValues();
    var rowIndex = -1;
    
    // Buscar si el ID ya existe para actualizarlo o agregarlo como nuevo
    for (var i = 1; i < rows.length; i++) {
      if (rows[i][idColIndex].toString() === data.id.toString()) {
        rowIndex = i + 1; // Las filas en Sheets empiezan en 1
        break;
      }
    }
    
    var rowData = [];
    for (var j = 0; j < headers.length; j++) {
      var key = headers[j];
      rowData.push(data[key] !== undefined ? data[key] : "");
    }
    
    if (rowIndex > -1) {
      // Actualizar fila existente
      sheet.getRange(rowIndex, 1, 1, rowData.length).setValues([rowData]);
    } else {
      // Insertar nueva fila
      sheet.appendRow(rowData);
    }
    
    return ContentService.createTextOutput(JSON.stringify({"result": "success"}))
      .setMimeType(ContentService.MimeType.JSON);
      
} catch(error) {
    return ContentService.createTextOutput(JSON.stringify({"result": "error", "message": error.toString()}))
      .setMimeType(ContentService.MimeType.JSON);
  }
}
