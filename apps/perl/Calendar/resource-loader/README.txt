Scripts to load Calendar resources into Google Apps Premier Edition via API.

Reference Doc:
http://code.google.com/apis/apps/calendar_resource/docs/1.0/calendar_resource_developers_guide_protocol.html#Creating

Files:
  api-global.pl - Library for common Apps functions like logging in and creating various HTTP requests
  genlist.pl - Script to generate test data (don't upload unless you want to do some cleanup)
  list.csv - Sample CSV list of resources (replace with your own data)
  resource-loader.pl - The magic script to generate and send the requests via API
  template.xml - The necessary Atom to create a resource in Google Apps

Usage:
  ./resource-loader.pl [list.csv]


