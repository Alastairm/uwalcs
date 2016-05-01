/*
 *
 */
function getRootURL() {
  return document.URL.substr(0,document.URL.lastIndexOf('/'));
}

function createCookie(name) {
    var expires = "";
    document.cookie = name+"="+name+expires+"; path=/";
}

function readCookie(name) {
    var nameEQ = name + "=";
    var ca = document.cookie.split(';');
    for(var i=0;i < ca.length;i++) {
        var c = ca[i];
        while (c.charAt(0)==' ') c = c.substring(1,c.length);
        if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
    }
    return null;
}

function eraseCookie(name) {
    createCookie(name,"",-1);
}

function stringInList( string, list) {
    var dict = {};
    for (var i=0; i < list.length; i++){dict[list[i]]="";}
    return string in dict;
}

function unitRedirect(){
    var rootURL = getRootURL();
    var unitCode = $('#unitCode').val();
    unitCode = unitCode.toUpperCase()
    window.location = rootURL+'/units/'+unitCode+'.html';
    return false;
}

function getUnitShortcuts() {
    var cookies = document.cookie.split(';');
    var navbar = document.getElementById("navbar-list");
    for (var i = 0; i < cookies.length; i++) {
        var unitCode = cookies[i].slice(9);
        var link = '/units/'+unitCode+'.html';
        var li = document.createElement('li');
        var a = document.createElement('a');
        a.innerHTML = unitCode;
        a.href = link;
        li.appendChild(a);
        navbar.appendChild(li);
    }
}

function addUnitShortcutButton() {
    var cookies = document.cookie.split(';');
    var unitCode = document.title;
    var button = document.createElement('button');
    button.type = 'button';
    if (stringInList(unitCode, cookies)) {
        button.setAttribute('class','btn btn-danger');
        button.setAttribute('onclick','removeUnitShortcut("'+unitCode+'")');
        button.innerHTML = 'Remove Shortcut';
    }
    else {
        button.setAttribute('class','btn btn-success');
        button.setAttribute('onclick','addUnitShortcut("'+unitCode+'")');
        button.innerHTML = 'Add Shortcut';
    }
    var pageHeader = document.getElementById('unit-title-div');
    pageHeader.appendChild(button);
}

function addUnitShortcut(unitCode) {
    createCookie(unitCode);
    document.location.reload(true);
}

function removeUnitShortcut(unitCode) {
    eraseCookie(unitCode);
    document.location.reload(true);
}

//From https://stackoverflow.com/questions/179355/clearing-all-cookies-with-javascript
function deleteAllCookies() {
    var cookies = document.cookie.split(";");

    for (var i = 0; i < cookies.length; i++) {
    	var cookie = cookies[i];
    	var eqPos = cookie.indexOf("=");
    	var name = eqPos > -1 ? cookie.substr(0, eqPos) : cookie;
    	document.cookie = name + "=;expires=Thu, 01 Jan 1970 00:00:00 GMT";
    }
}

function insertResources() {
  document.write('\
    <!-- jQuery Version 1.11.1 -->\
    <script src="https://code.jquery.com/jquery-1.11.2.min.js"></script>\
    \
    <!-- Bootstrap Core CSS -->\
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.6/css/bootstrap.min.css" integrity="sha384-1q8mTJOASx8j1Au+a5WDVnPi2lkFfwwEAa8hDDdjZlpLegxhjVME1fgjWPGmkzs7" crossorigin="anonymous">\
    \
    <!-- Bootstrap Core JavaScript -->\
    <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.6/js/bootstrap.min.js" integrity="sha384-0mSbJDEHialfmuBBQP6A4Qrprq5OVfW37PRR3j5ELqxss1yVqOtnepnHVP9aJ7xS" crossorigin="anonymous"></script>\
    \
    <!-- Custom CSS -->\
    <link rel="stylesheet" href="/uwalcsdl.css">\
    \
  ')
}

function insertNavbar() {
document.write('\
  <nav class="navbar navbar-inverse navbar-fixed-top" role="navigation">\
      <div class="container">\
          <!-- Brand and toggle get grouped for better mobile display -->\
          <div class="navbar-header">\
              <button type="button" class="navbar-toggle" data-toggle="collapse" data-target="#bs-example-navbar-collapse-1">\
                  <span class="sr-only">Toggle navigation</span>\
                  <span class="icon-bar"></span>\
                  <span class="icon-bar"></span>\
                  <span class="icon-bar"></span>\
              </button>\
              <a class="navbar-brand" href="index.html">UWA LCS DL</a>\
          </div>\
          <!-- Collect the nav links, forms, and other content for toggling -->\
          <div class="collapse navbar-collapse" id="bs-example-navbar-collapse-1">\
              <ul class="nav navbar-nav" id="navbar-list">\
                  <li>\
                      <a href="/index.html">Find Unit</a>\
                  </li>\
                  <li>\
                      <a href="/unitList.html">List Units</a>\
                  </li>\
              </ul>\
              <ul class="nav navbar-nav navbar-right">\
                <li class="dropdown">\
                  <a href="#" class="dropdown-toggle" data-toggle="dropdown">\
                    <span class="glyphicon glyphicon-cog"></span>\
                  </a>\
                  <ul class="dropdown-menu">\
                    <li><a href="/customUnitID.html">Request Unit</a></li>\
                    <li><a href="/pastUnits.html"> Past Units</a></li>\
                    <li role="separator" class="divider"></li>\
                    <li><a href="/about.html">About</a></li>\
                    <li><a href="https://github.com/uwalcsdl/uwalcsdl.github.io">GitHub</a></li>\
                    <li role="separator" class="divider"></li>\
                    <li><a onclick="deleteAllCookies()" href="#">Clear Shortcuts</a></li>\
                  </ul>\
                </li>\
              </ul>\
          </div>\
          <!-- /.navbar-collapse -->\
      </div>\
      <!-- /.container -->\
  </nav>\
')
}
