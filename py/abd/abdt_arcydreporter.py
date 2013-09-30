"""Report the state of arcyd as it updates repositories."""
# =============================================================================
# CONTENTS
# -----------------------------------------------------------------------------
# abdt_arcydreporter
#
# Public Classes:
#   SharedFileDictOutput
#    .write
#   SharedDictOutput
#    .write
#   ArcydReporter
#    .start_sleep
#    .update_sleep
#    .finish_sleep
#    .start_repo
#    .fail_repo
#    .finish_repo
#    .close
#
# Public Assignments:
#   ARCYD_STATUS
#   ARCYD_CURRENT_REPO
#   ARCYD_REPOS
#   ARCYD_STATISTICS
#   ARCYD_LIST_ATTRIB
#   ARCYD_STATUS_STARTING
#   ARCYD_STATUS_UPDATING
#   ARCYD_STATUS_SLEEPING
#   ARCYD_STATUS_STOPPED
#   ARCYD_STATUS_IDLE
#   ARCYD_LIST_STATUS
#   REPO_ATTRIB_NAME
#   REPO_ATTRIB_HUMAN_NAME
#   REPO_ATTRIB_STATUS
#   REPO_LIST_ATTRIB
#   REPO_STATUS_UPDATING
#   REPO_STATUS_FAILED
#   REPO_STATUS_OK
#   REPO_STATUSES
#   ARCYD_STAT_CURRENT_CYCLE_TIME
#   ARCYD_STAT_LAST_CYCLE_TIME
#   ARCYD_LIST_STATISTICS
#
# -----------------------------------------------------------------------------
# (this contents block is generated, edits will be lost)
# =============================================================================

from __future__ import absolute_import

import datetime
import json

import phlsys_fs

ARCYD_STATUS = 'status'
ARCYD_CURRENT_REPO = 'current-repo'
ARCYD_REPOS = 'repos'
ARCYD_STATISTICS = 'statistics'

ARCYD_LIST_ATTRIB = [
    ARCYD_CURRENT_REPO,
    ARCYD_STATUS,
    ARCYD_REPOS,
    ARCYD_STATISTICS,
]

ARCYD_STATUS_STARTING = 'starting'
ARCYD_STATUS_UPDATING = 'updating'
ARCYD_STATUS_SLEEPING = 'sleeping'
ARCYD_STATUS_STOPPED = 'stopped'
ARCYD_STATUS_IDLE = 'idle'

ARCYD_LIST_STATUS = [
    ARCYD_STATUS_UPDATING,
    ARCYD_STATUS_SLEEPING,
    ARCYD_STATUS_STARTING,
    ARCYD_STATUS_STOPPED,
    ARCYD_STATUS_IDLE,
]

REPO_ATTRIB_NAME = 'name'
REPO_ATTRIB_HUMAN_NAME = 'human-name'
REPO_ATTRIB_STATUS = 'status'

REPO_LIST_ATTRIB = [
    REPO_ATTRIB_NAME,
    REPO_ATTRIB_HUMAN_NAME,
    REPO_ATTRIB_STATUS,
]

REPO_STATUS_UPDATING = 'updating'
REPO_STATUS_FAILED = 'failed'
REPO_STATUS_OK = 'ok'

REPO_STATUSES = [
    REPO_STATUS_UPDATING,
    REPO_STATUS_FAILED,
    REPO_STATUS_OK,
]

ARCYD_STAT_CURRENT_CYCLE_TIME = 'current-cycle-time'
ARCYD_STAT_LAST_CYCLE_TIME = 'last-cycle-time'

ARCYD_LIST_STATISTICS = [
    ARCYD_STAT_CURRENT_CYCLE_TIME,
    ARCYD_STAT_LAST_CYCLE_TIME,
]


class SharedFileDictOutput(object):

    def __init__(self, filename):
        super(SharedFileDictOutput, self).__init__()
        self._filename = filename

    def write(self, d):
        assert isinstance(d, dict)
        with phlsys_fs.write_file_lock_context(self._filename) as f:
            f.write(json.dumps(d))


class SharedDictOutput(object):

    def __init__(self, shared_d):
        super(SharedDictOutput, self).__init__()
        self._shared_d = shared_d
        assert isinstance(self._shared_d, dict)

    def write(self, d):
        assert isinstance(d, dict)
        # copy contents to other dict
        self._shared_d.clear()
        self._shared_d.update(d)


class _CycleTimer(object):

    def __init__(self):
        self._current_start = None
        self._last_duration = None

    def start_cycle(self):
        self._current_start = datetime.datetime.utcnow()

    def stop_cycle(self):
        self._last_duration = self.current_duration()
        self._current_start = None

    def current_duration(self):
        if self._current_start is None:
            return None
        duration = datetime.datetime.utcnow() - self._current_start
        return duration.total_seconds()

    @property
    def last_duration(self):
        return self._last_duration


class ArcydReporter(object):

    def __init__(self, output):
        """Initialise a new reporter to report to the specified outputs.

        :output: output to write status to

        """
        super(ArcydReporter, self).__init__()
        self._output = output

        assert self._output

        self._repos = []
        self._repo = None

        self._cycle_timer = _CycleTimer()

        self._write_status(ARCYD_STATUS_STARTING)

    def start_sleep(self, duration):
        _ = duration  # NOQA
        self._cycle_timer.stop_cycle()
        self._write_status(ARCYD_STATUS_SLEEPING)

    def update_sleep(self, duration):
        _ = duration  # NOQA
        self._write_status(ARCYD_STATUS_SLEEPING)

    def finish_sleep(self):
        self._write_status(ARCYD_STATUS_IDLE)
        self._cycle_timer.start_cycle()

    def start_repo(self, name, human_name):
        self._repo = {
            REPO_ATTRIB_NAME: name,
            REPO_ATTRIB_HUMAN_NAME: human_name,
            REPO_ATTRIB_STATUS: REPO_STATUS_UPDATING,
        }
        self._write_status(ARCYD_STATUS_UPDATING)

    def fail_repo(self):
        self._repo[REPO_ATTRIB_STATUS] = REPO_STATUS_FAILED
        self._repos.append(self._repo)
        self._repo = None
        self._write_status(ARCYD_STATUS_UPDATING)

    def finish_repo(self):
        self._repo[REPO_ATTRIB_STATUS] = REPO_STATUS_OK
        self._repos.append(self._repo)
        self._repo = None
        self._write_status(ARCYD_STATUS_IDLE)

    def _write_status(self, status):
        timer = self._cycle_timer
        statistics = {
            ARCYD_STAT_CURRENT_CYCLE_TIME: timer.current_duration(),
            ARCYD_STAT_LAST_CYCLE_TIME: timer.last_duration,
        }
        d = {
            ARCYD_STATUS: status,
            ARCYD_CURRENT_REPO: self._repo,
            ARCYD_REPOS: self._repos,
            ARCYD_STATISTICS: statistics,
        }
        assert set(d.keys()) == set(ARCYD_LIST_ATTRIB)
        self._output.write(d)

    def close(self):
        self._write_status(ARCYD_STATUS_STOPPED)


#------------------------------------------------------------------------------
# Copyright (C) 2012 Bloomberg L.P.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
#------------------------------- END-OF-FILE ----------------------------------