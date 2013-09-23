#!/usr/bin/python
#
# Copyright 2011 Google Inc. All Rights Reserved.
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
# limitations under the Licens

"""Creates an event for which every user in the domain is an invitee.

Usage: create_all_hands_event.py [options]

Options:
  -h, --help            show this help message and exit
  -u ADMIN_USER         admin user
  -p ADMIN_PASS         admin pass
  -d DOMAIN             Domain name
  -o ORGANIZER          The organizer's email address
  -k CONSUMER_KEY       OAuth Consumer Key
  -s CONSUMER_SECRET    Oauth Consumer Secret
  --title=TITLE         Title of the event
  --description=DESCRIPTION
                        Description of the event
  --where=WHERE         Location of the event
  --event_date=EVENT_DATE
                        The event_date in YYYY-MM-DD
  --start_time=START_TIME
                        Start time of the form HH24:MM in GMT
  --end_time=END_TIME   End time of the form HH24:MM in GMT
"""

__author__ = 'mdauphinee@google.com (Matt Dauphinee)'


from optparse import OptionParser
import sys
import atom
import atom.service
import gdata.apps.service as apps_service
import gdata.calendar
import gdata.calendar.service
import gdata.gauth


def CheckArgExists(arg, name, value):
  if value is None:
    print '%s (%s) is required' % (arg, name)
    sys.exit(1)


def ParseInputs():

  parser = OptionParser()
  parser.add_option('-u', dest='admin_user', help='admin user')
  parser.add_option('-p', dest='admin_pass', help='admin pass')
  parser.add_option('-d', dest='domain', help='Domain name')
  parser.add_option('-o', dest='organizer',
                    help="""The organizer's email address""",)
  parser.add_option('-k', dest='consumer_key', help='OAuth Consumer Key')
  parser.add_option('-s', dest='consumer_secret', help='Oauth Consumer Secret')
  parser.add_option('--title', dest='title', help='Title of the event')
  parser.add_option('--description', dest='description',
                    help='Description of the event')
  parser.add_option('--where', dest='where', help='Location of the event')
  parser.add_option('--event_date', dest='event_date',
                    help='The event_date in YYYY-MM-DD')
  parser.add_option('--start_time', dest='start_time',
                    help='Start time of the form HH24:MM in GMT')
  parser.add_option('--end_time', dest='end_time',
                    help='End time of the form HH24:MM in GMT')

  (options, unused_args) = parser.parse_args()

  CheckArgExists('-u', 'admin_user', options.admin_user)
  CheckArgExists('-p', 'admin_pass', options.admin_pass)
  CheckArgExists('-d', 'domain', options.domain)
  CheckArgExists('-o', 'organizer', options.organizer)
  CheckArgExists('-k', 'consumer_key', options.consumer_key)
  CheckArgExists('-s', 'consumer_secret', options.consumer_secret)
  CheckArgExists('--title', 'title', options.title)
  CheckArgExists('--description', 'description', options.description)
  CheckArgExists('--where', 'where', options.where)
  CheckArgExists('--event_date', 'event_date', options.event_date)
  CheckArgExists('--start_time', 'start_time', options.start_time)

  return options


def GetProvisionedUsers(options):
  conn = GetCalendarConnection(options)
  conn = apps_service.AppsService(email=options.admin_user,
                                  domain=options.domain,
                                  password=options.admin_pass)
  conn.ProgrammaticLogin()

  users = []
  user_feed = conn.RetrieveAllUsers()
  for user_entry in user_feed.entry:
    users.append('%s@%s' % (user_entry.login.user_name.lower(),
                            options.domain))
  return users


def GetCalendarConnection(options):
  sig_method = gdata.auth.OAuthSignatureMethod.HMAC_SHA1

  conn = gdata.calendar.service.CalendarService(source='create_all_hands')
  conn.SetOAuthInputParameters(signature_method=sig_method,
                               consumer_key=options.consumer_key,
                               consumer_secret=options.consumer_secret,
                               two_legged_oauth=True,
                               requestor_id=options.organizer)
  return conn


def CreateAllHandsEvent(options, users):

  url = '/calendar/feeds/default/private/full'
  status = gdata.calendar.AttendeeStatus()
  status.value = 'INVITED'
  att_type = gdata.calendar.AttendeeType()
  att_type.value = 'REQUIRED'

  conn = GetCalendarConnection(options)

  start_time = '%sT%s:00.000Z' % (options.event_date, options.start_time)
  end_time = '%sT%s:00.000Z' % (options.event_date, options.end_time)

  event = gdata.calendar.CalendarEventEntry()
  event.title = atom.Title(text=options.title)
  event.content = atom.Content(text=options.description)
  event.where.append(gdata.calendar.Where(value_string=options.where))
  new_who = []
  for u in users:
    new_who.append(gdata.calendar.Who(email=u,
                                      attendee_status=status,
                                      attendee_type=att_type))
  event.who = new_who

  event.when.append(gdata.calendar.When(start_time=start_time,
                                        end_time=end_time))
  event.send_event_notifications = gdata.calendar.SendEventNotifications(value="true")

  return conn.InsertEvent(event, url)


def main():

  options = ParseInputs()

  users = GetProvisionedUsers(options)
  new_event = CreateAllHandsEvent(options, users)

  print 'New single event inserted: %s' % (new_event.id.text,)


if __name__ == '__main__':
  main()
