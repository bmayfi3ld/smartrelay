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
  
  var cell = sheet.getRange(1, 1, sheet.getLastRow()-1, 7);
  range = cell.getValues();
  // checking if date is definitly wrong
  for ( var i = 1; i < range.length; i++ ) {
    if (typeof range[i][0].getMonth === 'function' && range[i][0].getFullYear() < 2015) {
      range.splice(i,1)
    }
  }
  
  // convert to string for transfer to client
  for ( var i = 1; i < range.length; i++ ) {
    range[i][0] = range[i][0].toString()
  }
  
  // check if blank row
  for (var i = range.length-1; i > 0; i--) {
    if (range[i][0] == '') {
      range.splice(i,1)      
    }
  }
  
  // round temp
  for (var i = 1; i < range.length; i++) {
    if (range[i][0] == '') {
      range[i][1] = Math.round(range[i][1])
    }
  }
 
  for ( var i = 1; i < range.length; i++ ) {
    Logger.log(range[i][0])
  }
      
  return range
  
//  return range.map(function (row) { return [row[0].toString(), row[1], row[2], row[3], row[4], row[5], row[6]]; } );  
//  Logger.log(cell.getValues())
//  return cell.getValues();
}
