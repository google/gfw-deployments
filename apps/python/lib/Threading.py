#!/usr/bin/python
#
# Copyright 2012 Google Inc. All Rights Reserved.

"""
Copyright (C) 2012 Google Inc.
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

###########################################################################
DISCLAIMER:

(i) GOOGLE INC. ("GOOGLE") PROVIDES YOU ALL CODE HEREIN "AS IS" WITHOUT ANY
WARRANTIES OF ANY KIND, EXPRESS, IMPLIED, STATUTORY OR OTHERWISE, INCLUDING,
WITHOUT LIMITATION, ANY IMPLIED WARRANTY OF MERCHANTABILITY, FITNESS FOR A
PARTICULAR PURPOSE AND NON-INFRINGEMENT; AND

(ii) IN NO EVENT WILL GOOGLE BE LIABLE FOR ANY LOST REVENUES, PROFIT OR DATA,
OR ANY DIRECT, INDIRECT, SPECIAL, CONSEQUENTIAL, INCIDENTAL OR PUNITIVE
DAMAGES, HOWEVER CAUSED AND REGARDLESS OF THE THEORY OF LIABILITY, EVEN IF
GOOGLE HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES, ARISING OUT OF
THE USE OR INABILITY TO USE, MODIFICATION OR DISTRIBUTION OF THIS CODE OR ITS
DERIVATIVES.
###########################################################################

This library contains functions to make process threading easier.
"""

import Queue
import threading


class Worker(threading.Thread):
  def __init__(self, thread_number, work_queue, metadata={}, function=None):
    threading.Thread.__init__(self)

    self.thread_number = thread_number
    self.work_queue = work_queue
    self.metadata = metadata
    self.function = function
    self.success = 0
    self.failure = 0

  def run(self):
    while True:
      item = self.work_queue.get()
      if self.function(metadata=self.metadata, item=item,
                       thread_number=self.thread_number):
        self.work_queue.task_done()
        self.success += 1
      else:
        self.work_queue.put(item)
        self.failure += 1

  def Report(self):
    print('Thread #%s:\n'
          '  Items attempted: %s\n'
          '    Successes: %s\n'
          '    Failures: %s\n' % (self.thread_number,
                                  self.success + self.failure,
                                  self.success, self.failure))


class Threading(object):
  def __init__(self, data_list, metadata={}, function=None, threads=10,
               debug_level=0):
    self.data_list = data_list
    self.metadata = metadata
    self.function = function
    self.threads = threads
    self.debug_level = debug_level

    self.work_queue = Queue.Queue()

    for item in data_list:
      self.work_queue.put(item)

    threads = []
    # Spawn a pool of threads to process auditing checks
    for thread_number in range(self.threads):
      thread = Worker(thread_number, self.work_queue, self.metadata,
                      self.function)
      thread.setDaemon(True)
      threads.append(thread)
      thread.start()

    # wait on the queue until everything has been processed
    self.work_queue.join()

    if self.debug_level > 0:
      for thread in threads:
        thread.Report()
