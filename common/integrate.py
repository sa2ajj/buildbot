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
...
"""

from argparse import ArgumentParser

def main():
    """
    CLI interface
    """
    parser = ArgumentParser(description='Integrate a Buildbot pull request')

    parser.add_argument('--repository', default='buildbot/buildbot',
                        help='repository to integrate the pull request to '
                             '(default: %(default)s)')
    parser.add_argument('--branch', default='master',
                        help='branch to integrate to (default: %(default)s)')
    parser.add_argument('pr', type=int, help='pull request number',
                        metavar='PR')
    args = parser.parse_args()

# https://api.github.com/repos/buildbot/buildbot/issues/1949

if __name__ == '__main__':
    main()

# {
#   "url": "https://api.github.com/repos/buildbot/buildbot/issues/1949",
#   "repository_url": "https://api.github.com/repos/buildbot/buildbot",
#   "labels_url": "https://api.github.com/repos/buildbot/buildbot/issues/1949/labels{/name}",
#   "comments_url": "https://api.github.com/repos/buildbot/buildbot/issues/1949/comments",
#   "events_url": "https://api.github.com/repos/buildbot/buildbot/issues/1949/events",
#   "html_url": "https://github.com/buildbot/buildbot/pull/1949",
#   "id": 127040175,
#   "number": 1949,
#   "title": "convert data api spec to raml",
#   "user": {
#     "login": "tardyp",
#     "id": 109859,
#     "avatar_url": "https://avatars.githubusercontent.com/u/109859?v=3",
#     "gravatar_id": "",
#     "url": "https://api.github.com/users/tardyp",
#     "html_url": "https://github.com/tardyp",
#     "followers_url": "https://api.github.com/users/tardyp/followers",
#     "following_url": "https://api.github.com/users/tardyp/following{/other_user}",
#     "gists_url": "https://api.github.com/users/tardyp/gists{/gist_id}",
#     "starred_url": "https://api.github.com/users/tardyp/starred{/owner}{/repo}",
#     "subscriptions_url": "https://api.github.com/users/tardyp/subscriptions",
#     "organizations_url": "https://api.github.com/users/tardyp/orgs",
#     "repos_url": "https://api.github.com/users/tardyp/repos",
#     "events_url": "https://api.github.com/users/tardyp/events{/privacy}",
#     "received_events_url": "https://api.github.com/users/tardyp/received_events",
#     "type": "User",
#     "site_admin": false
#   },
#   "labels": [
#     {
#       "url": "https://api.github.com/repos/buildbot/buildbot/labels/needs%20work",
#       "name": "needs work",
#       "color": "f7c6c7"
#     },
#     {
#       "url": "https://api.github.com/repos/buildbot/buildbot/labels/please%20review",
#       "name": "please review",
#       "color": "bfe5bf"
#     }
#   ],
#   "state": "open",
#   "locked": false,
#   "assignee": null,
#   "milestone": null,
#   "comments": 9,
#   "created_at": "2016-01-16T17:33:39Z",
#   "updated_at": "2016-04-07T03:50:03Z",
#   "closed_at": null,
#   "pull_request": {
#     "url": "https://api.github.com/repos/buildbot/buildbot/pulls/1949",
#     "html_url": "https://github.com/buildbot/buildbot/pull/1949",
#     "diff_url": "https://github.com/buildbot/buildbot/pull/1949.diff",
#     "patch_url": "https://github.com/buildbot/buildbot/pull/1949.patch"
#   },
#   "body": "raml is a metalanguage to describe REST apis. http://raml.org/\r\n\r\nThe claim is to be the successor from swagger and blueprint, with focus being\r\non a easy to read source code.\r\n\r\nMy goal is is to evntually have all the rtype and most of data api doc\r\nwritten in raml, with a bunch of scripts to convert the raml into\r\n\r\n- sphinx doc for resource types and data api (regenerate the same doc as we currently have)\r\n- sphinx doc for rest api (we don't have that right now, and ask our users to manually derive it from data api)\r\n- sphinx doc for mq (which currently is mostly outdated, as it is derived from the rtype api http://trac.buildbot.net/ticket/3214)\r\n\r\nAll the raml file in this commit are purely derived from the typing metadata associated with endpoints declaration in the data api.\r\n\r\nThe goal is to enhance the raml files so that they include the rst doc we currently have in rtype-*.rst\r\nand to have a unit test to automatically verify coherency b/w raml doc, and data/*.py\r\n\r\nI dont think I want to rewrite the data validation stuff directly using raml, this can be an eventual goal, but not really needed at the moment\r\n\r\nAnother usage of this is also to generate metadata for the data-module, which currently hardcodes some stuff in the coffee.",
#   "closed_by": null
# }
