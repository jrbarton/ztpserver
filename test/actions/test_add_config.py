#!/usr/bin/env python
#
# Copyright (c) 2014, Arista Networks, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#  - Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#  - Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
#  - Neither the name of Arista Networks nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL ARISTA NETWORKS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

#pylint: disable=R0904,F0401,W0232,E1101,W0402

import os
import os.path
import unittest
import sys
from string import Template

sys.path.append('test/client')

from client_test_lib import debug    #pylint: disable=W0611
from client_test_lib import STARTUP_CONFIG
from client_test_lib import Bootstrap, ActionFailureTest
from client_test_lib import file_log, get_action, random_string
from client_test_lib import startup_config_action

class FailureTest(ActionFailureTest):

    def test_missing_url(self):
        self.basic_test('add_config', 1)

    def test_url_failure(self):
        self.basic_test('add_config', 2,
                        attributes={'url' :
                                    random_string()})

    def test_no_variable(self):
        bootstrap = Bootstrap(ztps_default_config=True)
        config = random_string()
        url = 'http://%s/%s' % (bootstrap.server, config)
        bootstrap.ztps.set_definition_response(
            actions=[{'action' : 'test_action'}],
            attributes={'url' : url})
        bootstrap.ztps.set_action_response('test_action',
                                           get_action('add_config'))
        contents = '%s $missing_variable %s' % (random_string(),
                                                 random_string())
        bootstrap.ztps.set_file_response(config, contents)
        bootstrap.start_test()

        try:
            self.failUnless(bootstrap.action_failure())
            msg = [x for x in bootstrap.output.split('\n') if x][-1]
            self.failUnless('return code 3' in msg)
        except AssertionError:
            raise
        finally:
            bootstrap.end_test()

    def test_one_missing_variable(self):
        bootstrap = Bootstrap(ztps_default_config=True)

        var_dict = {'a': 'new_a'}

        config = random_string()
        url = 'http://%s/%s' % (bootstrap.server, config)
        bootstrap.ztps.set_definition_response(
            actions=[{'action' : 'test_action'}],
            attributes={'url' : url,
                        'variables' : var_dict})
        bootstrap.ztps.set_action_response('test_action',
                                           get_action('add_config'))
        contents = '%s $missing_variable %s $a' % (random_string(),
                                                   random_string())
        bootstrap.ztps.set_file_response(config, contents)
        bootstrap.start_test()

        try:
            self.failUnless(bootstrap.action_failure())
            msg = [x for x in bootstrap.output.split('\n') if x][-1]
            self.failUnless('return code 3' in msg)
        except AssertionError:
            raise
        finally:
            bootstrap.end_test()

class SuccessTest(unittest.TestCase):

    def test_success(self):
        bootstrap = Bootstrap(ztps_default_config=True)
        config = random_string()
        url = 'http://%s/%s' % (bootstrap.server, config)
        bootstrap.ztps.set_definition_response(
            actions=[{'action' : 'test_action'}],
            attributes={'url' : url})
        bootstrap.ztps.set_action_response('test_action',
                                           get_action('add_config'))
        contents = random_string()
        bootstrap.ztps.set_file_response(config, contents)
        bootstrap.start_test()

        try:
            self.failUnless(os.path.isfile(STARTUP_CONFIG))
            self.failUnless(contents.split() == file_log(STARTUP_CONFIG))
            self.failUnless(bootstrap.success())
        except AssertionError:
            raise
        finally:
            bootstrap.end_test()

    def test_url_replacement(self):
        bootstrap = Bootstrap(ztps_default_config=True)
        config = random_string()
        ztps_server = 'http://%s' % bootstrap.server
        bootstrap.ztps.set_definition_response(
            actions=[{'action' : 'test_action'}],
            attributes={'url' : config,
                        'ztps_server': ztps_server})
        bootstrap.ztps.set_action_response('test_action',
                                           get_action('add_config'))
        contents = random_string()
        bootstrap.ztps.set_file_response(config, contents)
        bootstrap.start_test()

        try:
            self.failUnless(os.path.isfile(STARTUP_CONFIG))
            self.failUnless(contents.split() == file_log(STARTUP_CONFIG))
            self.failUnless(bootstrap.success())
        except AssertionError:
            raise
        finally:
            bootstrap.end_test()

    def test_append(self):
        bootstrap = Bootstrap(ztps_default_config=True)
        config = random_string()
        url = 'http://%s/%s' % (bootstrap.server, config)
        bootstrap.ztps.set_definition_response(
            actions=[{'action' : 'startup_config_action'},
                     {'action' : 'test_action'}],
            attributes={'url' : url})
        bootstrap.ztps.set_action_response('test_action',
                                           get_action('add_config'))

        startup_config_text = random_string()
        bootstrap.ztps.set_action_response(
            'startup_config_action',
            startup_config_action(lines=[startup_config_text]))
        contents = random_string()
        bootstrap.ztps.set_file_response(config, contents)
        bootstrap.start_test()

        try:
            self.failUnless(os.path.isfile(STARTUP_CONFIG))
            log = file_log(STARTUP_CONFIG)
            self.failUnless(contents in log)
            self.failUnless(startup_config_text in log)
            self.failUnless(bootstrap.success())
        except AssertionError:
            raise
        finally:
            bootstrap.end_test()

    def test_multi_lines(self):
        bootstrap = Bootstrap(ztps_default_config=True)
        config = random_string()
        url = 'http://%s/%s' % (bootstrap.server, config)
        bootstrap.ztps.set_definition_response(
            actions=[{'action' : 'startup_config_action'},
                     {'action' : 'test_action'}],
            attributes={'url' : url})
        bootstrap.ztps.set_action_response('test_action',
                                           get_action('add_config'))

        startup_config_lines = [random_string(), random_string(),
                                random_string(), random_string()]
        bootstrap.ztps.set_action_response(
            'startup_config_action',
            startup_config_action(lines=startup_config_lines))
        contents = '\n'.join([random_string(), random_string(),
                              random_string(), random_string(),
                              random_string(), random_string()])
        bootstrap.ztps.set_file_response(config, contents)
        bootstrap.start_test()

        try:
            self.failUnless(os.path.isfile(STARTUP_CONFIG))
            log = file_log(STARTUP_CONFIG)
            all_lines = startup_config_lines + contents.split()
            for line in all_lines:
                self.failUnless(line in log)
            self.failUnless(bootstrap.success())
        except AssertionError:
            raise
        finally:
            bootstrap.end_test()

    def variables_test(self, var_dict, contents):
        bootstrap = Bootstrap(ztps_default_config=True)

        config = random_string()
        url = 'http://%s/%s' % (bootstrap.server, config)
        bootstrap.ztps.set_definition_response(
            actions=[{'action' : 'test_action'}],
            attributes={'url' : url,
                        'variables':
                            var_dict})
        bootstrap.ztps.set_action_response('test_action',
                                           get_action('add_config'))
        bootstrap.ztps.set_file_response(config, contents)
        bootstrap.start_test()

        try:
            self.failUnless(os.path.isfile(STARTUP_CONFIG))
            contents = Template(contents).substitute(var_dict)
            self.failUnless([x.strip() for x in contents.split('\n')] ==
                            file_log(STARTUP_CONFIG))
            self.failUnless(bootstrap.success())
        except AssertionError:
            raise
        finally:
            bootstrap.end_test()

    def test_variable(self):
        var_dict = {'test_variable': 'test_new_variable'}
        contents = '%s $test_variable %s' % (random_string(),
                                                 random_string())
        self.variables_test(var_dict, contents)

    def test_variables(self):
        var_dict = {'a': 'new_a',
                    'b': 'new_b',
                    'c': 'new_c'}
        contents = '%s $a\n%s $b %s \n$c %s' % (random_string(),
                                                random_string(),
                                                random_string(),
                                                random_string())
        self.variables_test(var_dict, contents)

if __name__ == '__main__':
    unittest.main()
