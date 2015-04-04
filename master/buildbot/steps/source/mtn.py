# This file is part of Buildbot.  Buildbot is free software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Copyright Buildbot Team Members

# Source step code for Monotone

from twisted.internet import defer
from twisted.internet import reactor
from twisted.python import log

from buildbot.config import ConfigErrors
from buildbot.interfaces import BuildSlaveTooOldError
from buildbot.process import buildstep
from buildbot.process import remotecommand
from buildbot.steps.source.base import Source


class Monotone(Source):

    """ Class for Monotone with all smarts """

    name = 'monotone'

    renderables = ['repourl']
    possible_methods = ('clobber', 'copy', 'fresh', 'clean')
    vccmd = ['mtn']

    def __init__(self, repourl=None, branch=None, progress=False, mode='incremental',
                 method=None, **kwargs):

        self.repourl = repourl
        self.method = method
        self.mode = mode
        self.branch = branch
        self.sourcedata = "%s?%s" % (self.repourl, self.branch)
        self.databasename = 'db.mtn'
        self.database = '../db.mtn'
        self.progress = progress
        Source.__init__(self, **kwargs)
        errors = []

        if not self._hasAttrGroupMember('mode', self.mode):
            errors.append("Monotone: mode %s is not one of %s." %
                          (self.mode, self._listAttrGroupMembers('mode')))
        if self.mode == 'incremental' and self.method:
            errors.append("Monotone: incremental mode does not require method.")

        if self.mode == 'full':
            if self.method is None:
                self.method = 'copy'
            elif self.method not in self.possible_methods:
                errors.append("Monotone: invalid method for mode == %s." %
                              (self.mode))

        if repourl is None:
            errors.append("Monotone: must provide repourl.")

        if branch is None:
            errors.append("Monotone: must provide branch.")

        if errors:
            raise ConfigErrors(errors)

    def startVC(self, branch, revision, patch):
        self.revision = revision
        self.stdio_log = self.addLogForRemoteCommands("stdio")

        d = self.checkMonotone()

        @d.addCallback
        def checkInstall(monotoneInstalled):
            if not monotoneInstalled:
                raise BuildSlaveTooOldError("Monotone is not installed on slave")
            return 0
        d.addCallback(lambda _: self._checkDb())
        d.addCallback(lambda _: self.sourcedirIsPatched())

        @d.addCallback
        def checkPatched(patched):
            if patched:
                return self.clean()
            else:
                return 0
        d.addCallback(self._getAttrGroupMember('mode', self.mode))

        if patch:
            d.addCallback(self.patch, patch)
        d.addCallback(self.parseGotRevision)
        d.addCallback(self.finish)
        d.addErrback(self.failed)
        return d

    @defer.inlineCallbacks
    def mode_full(self, _):
        if self.method == 'clobber':
            yield self.clobber()
            return
        elif self.method == 'copy':
            yield self.copy()
            return

        updatable = yield self._sourcedirIsUpdatable()
        if not updatable:
            yield self._retryClone()
            yield self._checkout()
        elif self.method == 'clean':
            yield self.clean()
            yield self._update()
        elif self.method == 'fresh':
            yield self.clean(False)
            yield self._update()
        else:
            raise ValueError("Unknown method, check your configuration")

    @defer.inlineCallbacks
    def mode_incremental(self, _):
        updatable = yield self._sourcedirIsUpdatable()
        if not updatable:
            yield self._retryClone()
            yield self._checkout()
        else:
            yield self._pull()
            yield self._update(dopull=False)

    def clobber(self):
        d = self.runRmdir(self.workdir)
        d.addCallback(lambda _: self.runRmdir(self.databasename))
        d.addCallback(lambda _: self._retryClone())
        d.addCallback(lambda _: self._checkout())
        return d

    def copy(self):
        cmd = remotecommand.RemoteCommand('rmdir', {'dir': self.workdir,
                                                    'logEnviron': self.logEnviron,
                                                    'timeout': self.timeout, })
        cmd.useLog(self.stdio_log, False)
        d = self.runCommand(cmd)

        self.workdir = 'source'
        d.addCallback(self.mode_incremental)

        @d.addCallback
        def copy(_):
            cmd = remotecommand.RemoteCommand('cpdir',
                                              {'fromdir': 'source',
                                               'todir': 'build',
                                               'logEnviron': self.logEnviron,
                                               'timeout': self.timeout, })
            cmd.useLog(self.stdio_log, False)
            d = self.runCommand(cmd)
            return d

        @d.addCallback
        def resetWorkdir(_):
            self.workdir = 'build'
            return 0
        return d

    def checkMonotone(self):
        cmd = remotecommand.RemoteShellCommand(self.workdir, ['mtn', '--version'],
                                               env=self.env,
                                               logEnviron=self.logEnviron,
                                               timeout=self.timeout)
        cmd.useLog(self.stdio_log, False)
        d = self.runCommand(cmd)

        @d.addCallback
        def evaluate(_):
            if cmd.rc != 0:
                return False
            return True
        return d

    @defer.inlineCallbacks
    def clean(self, ignore_ignored=True):
        files = []
        commands = [['ls', 'unknown']]
        if not ignore_ignored:
            commands.append(['ls', 'ignored'])
        for cmd in commands:
            stdout = yield self._dovccmd(cmd, collectStdout=True)
            if len(stdout) == 0:
                continue
            for filename in stdout.strip().split('\n'):
                filename = self.workdir + '/' + str(filename)
                files.append(filename)

        if len(files) == 0:
            rc = 0
        else:
            if self.slaveVersionIsOlderThan('rmdir', '2.14'):
                rc = yield self.removeFiles(files)
            else:
                rc = yield self.runRmdir(files, abandonOnFailure=False)

        if rc != 0:
            log.msg("Failed removing files")
            raise buildstep.BuildStepFailed()

    @defer.inlineCallbacks
    def removeFiles(self, files):
        for filename in files:
            res = yield self.runRmdir(filename, abandonOnFailure=False)
            if res:
                defer.returnValue(res)
                return
        defer.returnValue(0)

    def _clone(self, abandonOnFailure=False):
        command = ['db', 'init', '--db', self.database]
        d = self._dovccmd(command, abandonOnFailure=abandonOnFailure)
        d.addCallback(lambda _: self._pull())
        return d

    def _checkout(self, abandonOnFailure=False):
        command = ['checkout', '.', '--db=%s' % (self.database)]
        if self.revision:
            command.extend(['--revision', self.revision])
        command.extend(['--branch', self.branch])

        return self._dovccmd(command, abandonOnFailure=abandonOnFailure)

    def _update(self, dopull=True, abandonOnFailure=False):
        if dopull:
            d = self._pull()
        else:
            d = defer.succeed(0)
        command = ['update', '--db=%s' % (self.database)]
        if self.revision:
            command.extend(['--revision', self.revision])
        else:
            command.extend(["-r", "h:" + self.branch])
        command.extend(["-b", self.branch])

        d.addCallback(lambda _: self._dovccmd(command, abandonOnFailure=abandonOnFailure))
        return d

    def _pull(self, abandonOnFailure=False):
        command = ['pull', self.sourcedata,
                   '--db=%s' % (self.database)]
        if self.progress:
            command.extend(['--ticker=dot'])
        else:
            command.extend(['--ticker=none'])
        d = self._dovccmd(command, abandonOnFailure=abandonOnFailure)
        return d

    def _retryClone(self):
        if self.retry:
            abandonOnFailure = (self.retry[1] <= 0)
        else:
            abandonOnFailure = True

        d = self._clone(abandonOnFailure)

        def _retry(res):
            if self.stopped or res == 0:
                return res
            delay, repeats = self.retry
            if repeats > 0:
                log.msg("Checkout failed, trying %d more times after %d seconds"
                        % (repeats, delay))
                self.retry = (delay, repeats - 1)
                df = defer.Deferred()
                df.addCallback(lambda _: self.runRmdir(self.workdir))
                df.addCallback(lambda _: self.runRmdir(self.databasename))
                df.addCallback(lambda _: self._retryClone())
                reactor.callLater(delay, df.callback, None)
                return df
            return res

        if self.retry:
            d.addCallback(_retry)
        return d

    @defer.inlineCallbacks
    def parseGotRevision(self, _=None):
        stdout = yield self._dovccmd(['automate', 'select', 'w:'], collectStdout=True)
        revision = stdout.strip()
        if len(revision) != 40:
            raise buildstep.BuildStepFailed()
        log.msg("Got Monotone revision %s" % (revision, ))
        self.updateSourceProperty('got_revision', revision)
        defer.returnValue(0)

    def _checkDb(self):
        d = self._dovccmd(['db', 'info', '--db', self.database], collectStdout=True)

        @d.addCallback
        def checkInfo(stdout):
            if stdout.find("does not exist") > 0:
                log.msg("Database does not exist")
                return 0
            elif stdout.find("(migration needed)") > 0:
                log.msg("Older format database found, migrating it")
                return self._dovccmd(['db', 'migrate', '--db', self.database])
            elif stdout.find("(too new, cannot use)") > 0:
                log.msg("The database is of a newer format than mtn can handle...  Abort!")
                raise buildstep.BuildStepFailed()
            else:
                log.msg("Database exists and compatible")
                return 0
        return d

    def _sourcedirIsUpdatable(self):
        d = self.pathExists(self.build.path_module.join(self.workdir, '_MTN'))

        @d.addCallback
        def cont(res):
            if res:
                d.addCallback(lambda _: self.pathExists('db.mtn'))
            else:
                return False
        return d

    def finish(self, res):
        d = defer.succeed(res)

        @d.addCallback
        def _gotResults(results):
            self.setStatus(self.cmd, results)
            log.msg("Closing log, sending result of the command %s " %
                    (self.cmd))
            return results
        d.addCallback(self.finished)
        return d
