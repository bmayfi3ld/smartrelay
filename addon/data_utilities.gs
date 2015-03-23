//Sets up UI
function onOpen() {
  //SpreadsheetApp.getUi().createAddonMenu().addItem('Open', 'openMenu').addToUi();
  SpreadsheetApp.getActiveSpreadsheet().toast('Smart Relay is installed on this spreadsheet');
  //create pages if they don't exist
  var cexists,lexists, eexists, hexists;
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var ssArr = ss.getSheets();
  for(var i = 0; i < ssArr.length; i++ ) {
    if(ssArr[i].getName() == 'config') cexists = true;
    if(ssArr[i].getName() == 'logs') lexists = true;
    if(ssArr[i].getName() == 'errorLog') eexists = true;
    if(ssArr[i].getName() == 'charts') hexists = true;
  }
  if(!cexists) ss.insertSheet('config');
  if(!lexists) ss.insertSheet('logs');
  if(!eexists) ss.insertSheet('errorLog');
  if(!hexists) ss.insertSheet('charts');
  

  
  
  //add useful names to page
  var configArr = ['Status','Command','Last Response Time','Email'];
  var logArr = ['Timestamp','Voltage','Amps','Temperature','Battery Voltage', 'Humidity', 'Frequency'];
  configArr = configArr.concat(logArr);
  var workingCell = ss.getSheetByName('config').getRange(1, 1);
  for(i = 0; i < configArr.length; i++) {
    workingCell.setValue(configArr[i]);
    workingCell = workingCell.offset(1,0);
  }

  var workingSheet = ss.getSheetByName('logs');
  workingSheet.setFrozenRows(1);
  workingCell = workingSheet.getRange(1, 1);
  for(i = 0; i < logArr.length; i++) {
    workingCell.setValue(logArr[i]);
    workingCell = workingCell.offset(0,1);
  }
  
  //Create Charts (Voltage, Amps)
  //myChartBuilder('Voltage');
  
  
  //clean up logs page
  //TODO: get data range and delete excess rows
  workingSheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('logs');
  var end = workingSheet.getLastRow()
  for(i = end; i >= 2; i--) {
    if(workingSheet.getRange(i, 1).isBlank()) workingSheet.deleteRow(i); //TODO: Speed up slow run
  }
}

//Data Management (runs when new data is added)
function onEdit(e){
  var range = e.range
  var sheet = range.getSheet();
  //determine if valid range
  debug(e.range.getValues());
  if(range.getNumRows() != 1 || sheet.getName() != 'logs' || range.getNumColumns() != getHeaderColumns(sheet)) return; 
  debug('check one');
  for(var i = 1; i <= range.getNumColumns(); i++) {
    if(isNaN(range.getCell(1,i).getValue())) return; 
  }
  debug('check two');
  
  //check if an alert needs to be made
  var value, variable
  for(var i = 1; i <= range.getNumColumns(); i++) {
    value = range.getCell(1,i).getValue();
    variable = sheet.getRange(1,i).getValue();
    debug(value + ':' + variable);
    threshCheck(value,variable);
  }
  
  //Update Charts
}

//Email Alert
function threshCheck(value,variable) {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('config');
  var cell = sheet.getRange(1, 1);
  while(cell.getValue() != variable) cell = cell.offset(1,0); //TODO: add case that variable can't be found
  var lowerThresh = cell.offset(0,1).getValue();
  var upperThresh = cell.offset(0,2).getValue();
  debug(variable + ':' + value + ':' + upperThresh + ':' + lowerThresh); //TODO: add check for daily quota
  if(value < lowerThresh) MailApp.sendEmail(Session.getActiveUser().getEmail(),'Smart Relay: ' + variable + ' ' + value + ' is below set threshold','');
  if(value > upperThresh) MailApp.sendEmail(Session.getActiveUser().getEmail(),'Smart Relay: ' + variable + ' ' + value + ' is above set threshold','');  
}

//Stretch Goal
//function openMenu() {
//  var html = HtmlService.createHtmlOutputFromFile('index')
//      .setSandboxMode(HtmlService.SandboxMode.IFRAME)
//      .setTitle('Smart Relay');
//  SpreadsheetApp.getUi()
//      .showSidebar(html);
//}


//My Utility Functions
function errorLog(english, id, time) {
  //TODO: stretch
  //Ideas: no sheet, no variable, no thresh
}

function getHeaderColumns(sheetIN) {
  var colNum = sheetIN.getLastColumn()
  var range = sheetIN.getRange(1,1,1,colNum);
  
  for(var i = 1; i <= colNum; i++) {
    if(range.getCell(1,i).isBlank()) return (i-1);
  }
  return colNum;
}

//Trigger for first time addon is added
function onInstall(e) {
  onOpen();
  MailApp.sendEmail(Session.getActiveUser().getEmail(),'You have successfully installed Smart Relay','');
  //TODO: add triggers automatically
}

function debug(myIn) {
 Logger.log(myIn); 
}

function myChartBuilder(variableIN) {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('charts');
   var chartBuilder = sheet.newChart();
  chartBuilder.addRange(sheet.getRange("A1:D8"))
       .setChartType(Charts.ChartType.LINE)
       .setOption('title', variableIN);
   sheet.insertChart(chartBuilder.setPosition(3, 3, 3, 3).build());
}
