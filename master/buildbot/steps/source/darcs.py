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

# Source step code for darcs

from twisted.internet import defer
from twisted.internet import reactor
from twisted.python import log

from buildbot.config import ConfigErrors
from buildbot.interfaces import BuildSlaveTooOldError
from buildbot.process import buildstep
from buildbot.process import remotecommand
from buildbot.process import remotetransfer
from buildbot.steps.source.base import Source


class Darcs(Source):

    """ Class for Darcs with all smarts """

    name = 'darcs'

    renderables = ['repourl']
    possible_methods = ('clobber', 'copy')
    vccmd = ['darcs']

    def __init__(self, repourl=None, mode='incremental',
                 method=None, **kwargs):

        self.repourl = repourl
        self.method = method
        self.mode = mode
        Source.__init__(self, **kwargs)
        errors = []

        if not self._hasAttrGroupMember('mode', self.mode):
            errors.append("Darcs: mode %s is not one of %s." %
                          (self.mode, self._listAttrGroupMembers('mode')))
        if self.mode == 'incremental' and self.method:
            errors.append("Darcs: incremental mode does not require method.")

        if self.mode == 'full':
            if self.method is None:
                self.method = 'copy'
            elif self.method not in self.possible_methods:
                errors.append("Darcs: invalid method for mode == %s." %
                              (self.mode))

        if repourl is None:
            errors.append("Darcs: must provide repourl.")

        if errors:
            raise ConfigErrors(errors)

    def startVC(self, branch, revision, patch):
        self.revision = revision
        self.stdio_log = self.addLogForRemoteCommands("stdio")

        d = self.checkDarcs()

        @d.addCallback
        def checkInstall(darcsInstalled):
            if not darcsInstalled:
                raise BuildSlaveTooOldError("Darcs is not installed on slave")
            return 0
        d.addCallback(lambda _: self.sourcedirIsPatched())

        @d.addCallback
        def checkPatched(patched):
            if patched:
                return self.copy()
            else:
                return 0

        d.addCallback(self._getAttrGroupMember('mode', self.mode))

        if patch:
            d.addCallback(self.patch, patch)
        d.addCallback(self.parseGotRevision)
        d.addCallback(self.finish)
        d.addErrback(self.failed)
        return d

    def checkDarcs(self):
        cmd = remotecommand.RemoteShellCommand(self.workdir, ['darcs', '--version'],
                                               env=self.env,
                                               logEnviron=self.logEnviron,
                                               timeout=self.timeout)
        cmd.useLog(self.stdio_log, False)
        d = self.runCommand(cmd)

        @d.addCallback
        def evaluate(_):
            return cmd.rc == 0
        return d

    @defer.inlineCallbacks
    def mode_full(self, _):
        if self.method == 'clobber':
            yield self.clobber()
            return
        elif self.method == 'copy':
            yield self.copy()
            return

    @defer.inlineCallbacks
    def mode_incremental(self, _):
        updatable = yield self._sourcedirIsUpdatable()
        if not updatable:
            yield self._checkout()
        else:
            command = ['pull', '--all', '--verbose']
            yield self._dovccmd(command)

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

    def clobber(self):
        d = self.runRmdir(self.workdir)
        d.addCallback(lambda _: self._checkout())
        return d

    def _clone(self, abandonOnFailure=False):
        command = ['get', '--verbose', '--lazy', '--repo-name', self.workdir]
        d = defer.succeed(0)
        if self.revision:
            d.addCallback(lambda _: self._downloadFile(self.revision, '.darcs-context'))
            command.append('--context')
            command.append('.darcs-context')

        command.append(self.repourl)
        d.addCallback(lambda _: self._dovccmd(command, abandonOnFailure=abandonOnFailure,
                                              workdir='.'))

        return d

    def _checkout(self):

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
                df.addCallback(lambda _: self._checkout())
                reactor.callLater(delay, df.callback, None)
                return df
            return res

        if self.retry:
            d.addCallback(_retry)
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

    @defer.inlineCallbacks
    def parseGotRevision(self, _):
        revision = yield self._dovccmd(['changes', '--max-count=1'], collectStdout=True)
        self.updateSourceProperty('got_revision', revision)
        defer.returnValue(0)

    def _sourcedirIsUpdatable(self):
        return self.pathExists(self.build.path_module.join(self.workdir, '_darcs'))

    def _downloadFile(self, buf, filename):
        filereader = remotetransfer.StringFileReader(buf)
        args = {
            'slavedest': filename,
            'maxsize': None,
            'reader': filereader,
            'blocksize': 16 * 1024,
            'workdir': self.workdir,
            'mode': None
        }
        cmd = remotecommand.RemoteCommand('downloadFile', args)
        cmd.useLog(self.stdio_log, False)
        log.msg("Downloading file: %s" % (filename))
        d = self.runCommand(cmd)

        @d.addCallback
        def evaluateCommand(_):
            if cmd.didFail():
                raise buildstep.BuildStepFailed()
            return cmd.rc
        return d
