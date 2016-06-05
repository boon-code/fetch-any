#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""
Version Control System Fetcher
"""

import sys
import re
import logging
import multiprocessing
import vcstools
import docopt

_DEFAULT_LOG_FORMAT = "%(name)s : %(threadName)s : %(levelname)s : %(message)s"
logging.basicConfig( stream = sys.stderr
                   , format = _DEFAULT_LOG_FORMAT
                   , level = logging.DEBUG
                   )


class FetcherApp(object):
    USAGE = """
Version Control System Fetcher

Usage:
  vcsf [-c <config>] [-j <jobs>]
  vcsf fetch [-j <jobs>] <repos>...
  vcsf -h | --help
  vcsf --version

Options:
  -h, --help                Show this screen.
  -j, --jobs=<jobs>         Number of parallel jobs [default: 1].
  --version                 Show version.
  -c, --config=<config>     Configuration file for fetching.

----
Examples:
  Load configuration file (configuration.yml) and check out:
  $ vcsf -c configuration.yml

  Load configuration file from standard input:
  $ vcsf -c - < configuration.yml
  or
  $ vcsf < configuration.yml

  Fetch from command line:
  $ vcsf fetch git://some.git.archive/repo.git;protocol=https svn://some.other.repo/project/trunk;protocol=https ...
"""
    _SPEC_RE = re.compile(r"\s*(?P<type>git|bzr|svn|hg|tar)://(?P<url>[^;^\s]+)(?P<opts>;.+)?")
    _OPTS_RE = re.compile(r"\s*(?P<key>[^=^\s]+)\s*=\s*(?P<value>.+)\s*")
    def __init__(self):
        self._log = logging.getLogger('Fetcher')
        self._jobs = 1
        self._strict = True

    def _addField(self, spec, key, value):
        t = spec['type']
        value_check = False
        if key in ('protocol', 'proto'):
            key = 'protocol' # normalize key
            allowed_values = ['http', 'https']
            if t in ('git', 'svn'):
                allowed_values.append(t)
            value_check = True
        elif key in ('revision', 'rev'):
            key = 'revision' # normalize key
        elif key in ('path', 'p'):
            key = 'path' # normalize key
        else:
            self._log.error("Unknown option '{0}'".format(key))
            return False

        if value_check and (not value in allowed_values):
            self._log.error("Option '{0}' is invalid: {1}".format(key, value))
            return False

        spec[key] = value
        return True

    def _defaultProtocol(self, spec):
        t = spec['type']
        if t in ('tar',):
            return 'https'
        else:
            return t
    
    def _parseOptions(self, spec):
        opts = spec['opts']
        if opts is None:
            opts = ""
        for i in opts.split(';'):
            m = self._OPTS_RE.match(i)
            if m is not None:
                k = m.group('key')
                v = m.group('value')
                ret = self._addField(spec, k, v)
                if self._strict and (not ret):
                    self._log.error("Skipping repository {type}://{url}'".format(**spec))
                    return False
        return True

    def fetch(self, repos):
        """ Fetch repositories based on list of textual specification

        :param repos: List of repository specifications (textual description
                      of source url and revision, branch, protocol, etc...
        """
        self._log.debug("Prepare fetching {0} repo-list: [{1}]".format(len(repos), ", ".join(repos)))
        parsed_repos = list()
        for i in repos:
            m = self._SPEC_RE.match(i)
            if m is None:
                self._log.warning("Skipping invalid repo specification: {0}".format(i))
            else:
                spec = m.groupdict()
                spec['protocol'] = self._defaultProtocol(spec)
                if self._parseOptions(spec):
                    self._log.debug("Spec: {0}".format(spec))
                    spec['fetch'] = "{protocol}://{url}".format(**spec)
                    parsed_repos.append(spec)
        if len(parsed_repos) > 0:
            self._log.info("Starting fetching {0} item(s) using {1} process(es)".format(len(parsed_repos), self._jobs))
            # TODO: Implement
            for i in parsed_repos:
                self._log.debug("Repo: type={type}, url={fetch}".format(**i))
        else:
            self._log.warning("No repositories have been fetched")

    def fetchFromFile(self, f):
        """ Fetch all repositories from text file

        :param f: File (-like) object that contains one repository per line
        """
        repos = list()
        lnum = 0
        for line in f:
            lnum += 1
            line = line.rstrip('\n\r')
            if self._SPEC_RE.match(line) is not None:
                repos.append(line)
            elif line != '':
                self._log.info("Skipping unknown repoistory specification (line {1}): '{0}'".format(line, lnum))
        return self.fetch(repos)

    def _run_command(self, p):
        self._log.debug(p)
        self._jobs = int(p.get('<jobs>', 1))
        if p.get('fetch', False):
            return self.fetch(p['<repos>'])
        elif p.get('-c', False) and p['config'] != '-':
            with open(p['<config>'], 'r') as f:
                return self.fetchFromFile(f)
        else:
            self.fetchFromFile(sys.stdin)

    def run(self, argv):
        try:
            p = docopt.docopt(self.USAGE, argv=argv)
        except docopt.DocoptExit:
            self._log.debug("Parsing arguments failed!")
            raise
        try:
            self._run_command(p)
        except Exception as e:
            self._log.critical("Exception: {0}".format(str(e)))


def main():
    multiprocessing.freeze_support()
    app = FetcherApp()
    app.run(sys.argv[1:])


if __name__ == '__main__':
    main()
