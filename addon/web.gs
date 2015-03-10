function doGet(request) {
  return HtmlService.createTemplateFromFile('index').evaluate()
}

function include(filename) {
  return HtmlService.createHtmlOutputFromFile(filename)
      .setSandboxMode(HtmlService.SandboxMode.IFRAME)
      .getContent();
}

function requestToggle() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('config');
  var cell = sheet.getRange(2, 2);
  value = cell.getValue()
  if ( value.toLowerCase() == 'off' ) {
    cell.setValue('on')
    return 1
  } else {
    cell.setValue('off')
  }
//  add loop to wait for update
  
}

function updateButton() {
//  get correct value
}
