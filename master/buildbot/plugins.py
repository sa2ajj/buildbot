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

"""
Plugin infrastructure support for Buildbot
"""

from pkg_resources import iter_entry_points
from zope.interface import Interface


# Base for Buildbot specific plugins
_NAMESPACE_BASE = 'buildbot'


class _Plugins(object):
    """
    represent plugins within a namespace
    """
    def __init__(self, namespace, interface=None, check_extras=True):
        if interface is not None:
            assert issubclass(interface, Interface)

        self._group = '%s.%s' % (_NAMESPACE_BASE, namespace)
        self._interface = interface
        self._check_extras = check_extras

        self._entries = None
        self._plugins = dict()

    @property
    def available(self):
        """
        names of available plugins within this namespace
        """
        if self._entries is None:
            self._entries = dict()

            for entry in iter_entry_points(self._group):
                name = entry.name

                if name in self._entries:
                    raise RuntimeError('Duplicate entry point for "%s:%s".\n'
                                       '  Previous definition %s\n'
                                       '  This definition %s' %
                                       (self._group, name,
                                        self._entries[name].dist,
                                        entry.dist))
                self._entries[name] = entry

        return self._entries.keys()

    def info(self, name):
        """
        get information about plugins known in this namespace
        """
        if name not in self:
            raise RuntimeError('Unknown plugin %s:%s' % (self._group, name))

        dist = self._entries[name].dist
        return (dist.project_name, dist.version)

    @property
    def info_all(self):
        """
        get information about plugins known in this namespace
        """
        return dict(
            (name, self.info(name)) for name in self.available
        )

    def __contains__(self, name):
        """
        check if the given name is available as a plugin
        """
        return name in self.available

    def __getitem__(self, name):
        """
        get an instance of the plugin with the given name
        """
        if name not in self.available:
            raise RuntimeError('Plugin "%s:%s" does not exist' %
                               (self._group, name))

        plugin = self._plugins.get(name, None)
        if plugin is None:
            entry = self._entries[name]
            if self._check_extras:
                entry.require()
            tempo = entry.load()
            if self._interface:
                if not self._interface.providedBy(tempo):
                    raise RuntimeError('Plugin %s:%s does not implement %s' %
                                       (self._group, name,
                                        self._interface.__name__))
            self._plugins[name] = tempo
        return plugin

    def call(self, name, *args, **kwargs):
        """
        get an instance of the plugin with the given name and call it with the
        provided arguments
        """
        return self[name](*args, **kwargs)


class _PluginDB(object):
    """
    Plugin infrastructre support for Buildbot
    """
    _namespaces = None

    def __init__(self):
        assert self._namespaces is None, ('Only one instance of _PluginDB is '
                                          'allowed')
        self._namespaces = dict()

    def add_namespace(self, namespace, interface=None, check_extras=True,
                      load_now=False):
        """
        register given namespace in global database of plugins

        in case it's already registered, return the registration
        """
        if namespace in self._namespaces:
            tempo = self._namespaces[namespace]
        else:
            tempo = _Plugins(namespace, interface, check_extras)

            if load_now:
                for name in tempo.available:
                    tempo[name]

            self._namespaces[namespace] = tempo
        return tempo

    @property
    def namespaces(self):
        """
        get a list of registered namespaces
        """
        return self._namespaces.keys()

    @property
    def info(self):
        """
        get information about all plugins in registered namespaces
        """
        result = dict()
        for name, namespace in self._namespaces.items():
            result[name] = namespace.info_all
        return result


_DB = _PluginDB()


def info():
    """
    provide information about all known plugins outside

    format of the output:

    {<namespace>, {
        {<plugin-name>: (<package-name>, <package-version),
         ...},
        ...
    }
    """
    return _DB.info


def plugin_loader(namespace, interface=None, check_extras=True,
                  load_now=False):
    """
    helper to produce :func:`plugin` function in corresponding modules
    """
    plugin = _DB.add_namespace(namespace, interface, check_extras, load_now)

    return plugin.call


def get_plugins(namespace, interface=None, check_extras=True, load_now=False):
    """
    helper to get a direct interface to _Plugins
    """
    return _DB.add_namespace(namespace, interface, check_extras, load_now)
