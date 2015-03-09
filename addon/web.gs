function doGet(request) {
  return HtmlService.createTemplateFromFile('index').evaluate()
}

function include(filename) {
  return HtmlService.createHtmlOutputFromFile(filename)
      .setSandboxMode(HtmlService.SandboxMode.IFRAME)
      .getContent();
}
