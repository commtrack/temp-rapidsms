function thisMovie(movieName) {
  if (navigator.appName.indexOf("Microsoft") != -1) {
       return window[movieName];
  } else {
      return document[movieName];
  }
}
function trigger(value) {
        thisMovie("map_test").receiveNotification(value);
}

function triggerXml(xmlurl,value) {
        thisMovie("map_test").receiveXML(xmlurl,value);
}
