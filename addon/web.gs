Url = "https://docs.google.com/spreadsheets/d/1SUDN3LiJ_agl7H60vPusyyG3stN6vADjsIDmeogkTcI/edit#gid=284061806"

function doGet() {
  return HtmlService
      .createTemplateFromFile('index')
      .evaluate()
      .setSandboxMode(HtmlService.SandboxMode.IFRAME);
}

function include(filename) {
  return HtmlService.createHtmlOutputFromFile(filename)
      .setSandboxMode(HtmlService.SandboxMode.IFRAME)
      .getContent();
}

function requestToggle() {
  var sheet = SpreadsheetApp.openByUrl(Url).getSheetByName('config');
  var cell = sheet.getRange(2, 2);
  value = cell.getValue()
  if ( value.toLowerCase() == 'off' ) {
    cell.setValue('on')
    return "On"
  } else {
    cell.setValue('off')
    return "Off"
  }
//  add loop to wait for update
  
}

function getStatus() {
  var sheet = SpreadsheetApp.openByUrl(Url).getSheetByName('config');
  var cell = sheet.getRange(1, 2);
  var timer = new Date(sheet.getRange(3, 2).getValue());
//  Logger.log( timer)
  var timer2 = new Date();
//  Logger.log( timer2)
  var diff = (timer2 - timer)/1000
//  Logger.log(diff) 
  if (diff > 60) {
    return 'Offline'
  } else {
    return cell.getValue()
  }
}

function getData() {
  var sheet = SpreadsheetApp.openByUrl(Url).getSheetByName('logs');
  var cell = sheet.getRange(2, 1, sheet.getLastRow()-1, 7);
  range = cell.getValues();
//  for (i in values) {
//    values[i][0] = values[i][0].toString()
//  }
  return range.map(function (row) { return [row[0].toString(), row[1], row[2], row[3], row[4], row[5], row[6]]; } );  
  Logger.log(cell.getValues())
  return cell.getValues();
}

