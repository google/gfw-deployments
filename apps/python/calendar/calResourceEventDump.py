#!/usr/bin/python
#
# Copyright (C) 2009 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

__author__ = 'Marcello Pedersen'

try:
  from xml.etree import ElementTree
except ImportError:
  from elementtree import ElementTree
import gdata.calendar.service
import gdata.service
import getopt
import sys
import traceback
import datetime
import urllib
import httplib


class CalendarSearch:

  def __init__(self, CONSUMER_KEY, CONSUMER_SECRET, requestor_id):
    """Creates a CalendarService and provides Oauth auth details to it. """

    SIG_METHOD = gdata.auth.OAuthSignatureMethod.HMAC_SHA1
    
    self.cal_client = gdata.calendar.service.CalendarService()
    self.cal_client.SetOAuthInputParameters(
        SIG_METHOD, CONSUMER_KEY, consumer_secret=CONSUMER_SECRET,
        two_legged_oauth=True, requestor_id=requestor_id)

  def _DateRangeQuery(self, resource_email, start_date='2007-01-01', end_date='2050-07-01'):
    """Retrieves events from the server which occur during the specified date
    range.  This uses the CalendarEventQuery class to generate the URL which is
    used to retrieve the feed.  For more information on valid query parameters,
    see: http://code.google.com/apis/calendar/reference.html#Parameters"""
    
    print 'Date range query for events on %s: %s to %s' % (resource_email, 
        start_date, end_date,)
    query = gdata.calendar.service.CalendarEventQuery(resource_email, 'private', 
        'full')
    query.start_min = start_date
    query.start_max = end_date 
    feed = self.cal_client.CalendarQuery(query)
    for i, an_event in zip(xrange(len(feed.entry)), feed.entry):
      print '\t%s. %s' % (i, an_event.title.text,)
      for a_when in an_event.when:
        print '\t\tStart time: %s' % (a_when.start_time,)
        print '\t\tEnd time:   %s' % (a_when.end_time,)
      for i in an_event.who:
        print '\t\t%s %s' % ("Guests: ",  i.email)


  def Run(self, resource_email, start_date):
    """Runs the specified functions 
    """
    # Getting feeds and query results
    self._DateRangeQuery(resource_email, start_date)

def main():
  """Runs the CalendarSearch application with the provided CONSUMER_KEY and
  and CONSUMER_SECRET values.  OAUTH Authentication details are required."""

  # parse command line options
  try:
    opts, args = getopt.getopt(sys.argv[1:], "", ["CONSUMER_KEY=", "CONSUMER_SECRET=", "admin_email=", "password="])
  except getopt.error, msg:
    print ('python calResourceDump.py --CONSUMER_KEY [domainname.com] --CONSUMER_SECRET [OAUTH SECRET] --admin_email [admin_email for prov API] --password [password]')
    sys.exit(2)

  # Process options
  for o, a in opts:
    if o == "--CONSUMER_KEY":
      CONSUMER_KEY = a
      domain = a
    elif o == "--CONSUMER_SECRET":
      CONSUMER_SECRET = a
    elif o == "--admin_email":
      email = a  
    elif o == "--password":
      password = a
      

  # If any option is missing, quit the application
  if CONSUMER_KEY == '' or CONSUMER_SECRET == '' or email == '' or password == '':
    print ('python calResourceDump.py --CONSUMER_KEY [domainname.com] --CONSUMER_SECRET [OAUTH SECRET] --admin_email [admin_email for prov API] --password [password]')
    sys.exit(2)  
  
  
  # Get the prov API auth token
  auth_token = clientLogin(email, domain, password)
  
  # Get resouce email list via prov API. Returns a list of resources
  resourceList = RetrieveResources(auth_token, domain)
  
  # Use the admin email address as the Oauth signed for calendar search requests
  service = CalendarSearch(CONSUMER_KEY, CONSUMER_SECRET, email)
  
  # Iterate over resource and for each resource search its calendar
  numOfWeeks = -2
  start_date =  str(datetime.date.today() + datetime.timedelta(weeks=numOfWeeks))
  
  for resourceEmail in resourceList:
    try:
      service.Run(resourceEmail, start_date)
    except:
      print "Exception in user code:"
      print '-'*60
      traceback.print_exc()
      print '-'*60
  

def clientLogin(Admin_email, Domain, Admin_password):  
  
  aliasURL = '/a/feeds/alias/2.0/%s' % (Domain)
  url = 'https://www.google.com/accounts/ClientLogin'
  headers = {'Content-type' : 'application/x-www-form-urlencoded'}
  values = {'Email' : Admin_email,
            'Passwd' : Admin_password,
            'accountType' : 'HOSTED', 
            'service' : 'apps'}
  data = urllib.urlencode(values)
  try:
    connection = httplib.HTTPSConnection('www.google.com')
    connection.set_debuglevel(0)
    connection.request('POST', url, body=data, headers=headers)
    response = connection.getresponse()
    status = response.status
    response = response.read()
    #print 'received %i OK response, %s' % (status, response)
  except:
    print "Could not connect to client login"
    print '-'*60
    traceback.print_exc()
    print '-'*60
    
  # auth_token is the substring between 'Auth=' and the end of response string
  return response[response.index('Auth=')+5:len(response)]
  
# get all aliases for a user
def RetrieveResources(auth_token, Domain):
  aliasURL = '/a/feeds/calendar/resource/2.0/%s/' % (Domain)
  headers = {'Content-type' : 'application/atom+xml',
  'Authorization' : '%s%s' % ('GoogleLogin auth=', auth_token)}
  try:
    connection = httplib.HTTPSConnection('apps-apis.google.com')
    connection.set_debuglevel(0)
    connection.request('GET', aliasURL, None, headers)
    response = connection.getresponse()
    response = response.read()   
  except:
    print "Could not connect get full list of resources "
    print '-'*60
    traceback.print_exc()
    print '-'*60
  
  XMLTree = ElementTree.fromstring(response)
  iter = XMLTree.getiterator()
  resourceList = []
  for element in iter:      
    if element.tag == '{http://schemas.google.com/apps/2006}property':
      if element.get('name') == 'resourceEmail':
        resourceList.append(element.get('value'))
  
  return resourceList

if __name__ == '__main__':
  main()
