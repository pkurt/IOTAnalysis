# Copyright 2011-2014 Splunk, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"): you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""Retrieves a list of installed apps from Splunk using the client module."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import splunklib.client as client
# added new
#import splunklib.results as results
############
HOST = "localhost"
PORT = 8000
USERNAME = "admin"
PASSWORD = "Pg18december"

service = client.connect(
    host=HOST,
    port=PORT,
    username=USERNAME,
    password=PASSWORD)

# added new
#job = service.jobs.create("search * | head 5")
#rr = results.ResultsReader(job.preview())
#for result in rr:
 #   if isinstance(result, results.Message):
         # Diagnostic messages may be returned in the results
  #       print '%s: %s' % (result.type, result.message)
   # elif isinstance(result, dict):
         # Normal events are returned as dicts
    #    print result
#if rr.is_preview:
 #   print "Preview of a running search job."
#else:
  #  print "Job is finished. Results are final."
##############

for app in service.apps:
    print app.name
