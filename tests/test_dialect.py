#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright 2018 Fedele Mantuano (https://www.linkedin.com/in/fmantuano/)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""


import logging
import unittest

from context import mails


logging.getLogger().addHandler(logging.NullHandler())


class TestDialect(unittest.TestCase):

    def setUp(self):
        self.messages = [
            ('server', '220 localhost ESMTP Postfix'),
            ('server', '250-ENHANCEDSTATUSCODES'),
            ('server', '250-localhost'),
            ('client', 'EHLO vip.90.com'),
            ('server', '250-PIPELINING'),
            ('server', '250-SIZE 10240000'),
            ('server', '250-ETRN'),
            ('server', '250 DSN'),
            ('server', '250-8BITMIME'),
            ('server', '250-VRFY'),
            ('client', 'MAIL FROM:<sywangwq@vip.90.com>'),
            ('server', '250 2.1.0 Ok'),
            ('client', 'RCPT TO:<pramood48in@test_mail.net>'),
            ('server', '250 2.1.5 Ok'),
            ('server', '354 End data with <CR><LF>.<CR><LF>'),
            ('client', 'DATA'),
            ('server', '250 2.0.0 Ok: queued as 319A8641319'),
            ('server', '221 2.0.0 Bye'),
            ('client', 'QUIT')]

    def test_multiple_communications(self):
        messages_mixed = [
            ('server', '220 localhost ESMTP Postfix'),
            ('server', '250-ENHANCEDSTATUSCODES'),
            ('server', '250-localhost'),
            ('client', 'EHLO vip.90.com'),
            ('server', '250-PIPELINING'),
            ('server', '250-SIZE 10240000'),
            ('client', 'EHLO mixed.90.com'),  # mixed
            ('server', '250-ETRN'),
            ('client', 'MAIL FROM:<test@vip.90.com>'),  # mixed
            ('server', '250 DSN'),
            ('server', '250-8BITMIME'),
            ('server', '250-VRFY'),
            ('client', 'MAIL FROM:<sywangwq@vip.90.com>'),
            ('client', 'RCPT TO:<mixed@test_mail.net>'),  # mixed
            ('server', '250 2.1.0 Ok'),
            ('client', 'RCPT TO:<pramood48in@test_mail.net>'),
            ('server', '250 2.1.5 Ok'),
            ('server', '354 End data with <CR><LF>.<CR><LF>'),
            ('client', 'DATA'),
            ('server', '250 2.0.0 Ok: queued as 319A8641319'),
            ('client', 'DATA'),
            ('client', 'QUIT'),
            ('server', '221 2.0.0 Bye'),
            ('client', 'QUIT')]

        dialect = ["EHLO ", "MAIL FROM:", "RCPT TO:", "DATA", "QUIT"]
        dialect_not_mixed = mails.get_dialect(self.messages)
        dialect_mixed = mails.get_dialect(messages_mixed)
        self.assertEqual(dialect_mixed, dialect_not_mixed)
        self.assertEqual(dialect, dialect_mixed)

    def test_get_elastic_indices(self):
        indices = mails.get_elastic_indices()
        self.assertIsInstance(indices, str)
        indices = indices.split(",")
        self.assertIsInstance(indices, list)
        self.assertEqual(len(indices), 2)

    def test_get_messages_str(self):
        messages_str = mails.get_messages_str(self.messages)
        self.assertIsInstance(messages_str, str)

    def test_get_dialect(self):
        dialect = ["EHLO ", "MAIL FROM:", "RCPT TO:", "DATA", "QUIT"]
        dialect_out = mails.get_dialect(self.messages)
        self.assertIsInstance(dialect_out, list)
        self.assertEqual(dialect_out, dialect)

    def test_get_dialect_str(self):
        dialect_str = "EHLO  MAIL FROM: RCPT TO: DATA QUIT"
        dialect = mails.get_dialect(self.messages)
        dialect_str_out = mails.get_dialect_str(dialect)
        self.assertIsInstance(dialect_str_out, str)
        self.assertEqual(dialect_str_out, dialect_str)

    def test_get_dialect_fingerprints(self):
        dialect = mails.get_dialect(self.messages)
        dialect_str = mails.get_dialect_str(dialect)
        hashes = mails.get_dialect_fingerprints(dialect_str)

        # Adding a space to a client command
        messages = [
            ('server', '220 localhost ESMTP Postfix'),
            ('server', '250-ENHANCEDSTATUSCODES'),
            ('server', '250-localhost'),
            ('client', 'EHLO  vip.90.com'),  # added a space
            ('server', '250-PIPELINING'),
            ('server', '250-SIZE 10240000'),
            ('server', '250-ETRN'),
            ('server', '250 DSN'),
            ('server', '250-8BITMIME'),
            ('server', '250-VRFY'),
            ('client', 'MAIL FROM:<sywangwq@vip.90.com>'),
            ('server', '250 2.1.0 Ok'),
            ('client', 'RCPT TO:<pramood48in@test_mail.net>'),
            ('server', '250 2.1.5 Ok'),
            ('server', '354 End data with <CR><LF>.<CR><LF>'),
            ('client', 'DATA'),
            ('server', '250 2.0.0 Ok: queued as 319A8641319'),
            ('server', '221 2.0.0 Bye'),
            ('client', 'QUIT')]

        dialect = mails.get_dialect(messages)
        dialect_str = mails.get_dialect_str(dialect)
        hashes_1 = mails.get_dialect_fingerprints(dialect_str)
        self.assertNotEqual(hashes.sha256, hashes_1.sha256)

        # Remove a client command line
        messages = [
            ('server', '220 localhost ESMTP Postfix'),
            ('server', '250-ENHANCEDSTATUSCODES'),
            ('server', '250-localhost'),
            # ('client', 'EHLO  vip.90.com'),  # line removed
            ('server', '250-PIPELINING'),
            ('server', '250-SIZE 10240000'),
            ('server', '250-ETRN'),
            ('server', '250 DSN'),
            ('server', '250-8BITMIME'),
            ('server', '250-VRFY'),
            ('client', 'MAIL FROM:<sywangwq@vip.90.com>'),
            ('server', '250 2.1.0 Ok'),
            ('client', 'RCPT TO:<pramood48in@test_mail.net>'),
            ('server', '250 2.1.5 Ok'),
            ('server', '354 End data with <CR><LF>.<CR><LF>'),
            ('client', 'DATA'),
            ('server', '250 2.0.0 Ok: queued as 319A8641319'),
            ('server', '221 2.0.0 Bye'),
            ('client', 'QUIT')]

        dialect = mails.get_dialect(messages)
        dialect_str = mails.get_dialect_str(dialect)
        hashes_2 = mails.get_dialect_fingerprints(dialect_str)
        self.assertNotEqual(hashes.sha256, hashes_2.sha256)

        # Lowercase a letter
        messages = [
            ('server', '220 localhost ESMTP Postfix'),
            ('server', '250-ENHANCEDSTATUSCODES'),
            ('server', '250-localhost'),
            ('client', 'EhLO  vip.90.com'),  # h lower
            ('server', '250-PIPELINING'),
            ('server', '250-SIZE 10240000'),
            ('server', '250-ETRN'),
            ('server', '250 DSN'),
            ('server', '250-8BITMIME'),
            ('server', '250-VRFY'),
            ('client', 'MAIL FROM:<sywangwq@vip.90.com>'),
            ('server', '250 2.1.0 Ok'),
            ('client', 'RCPT TO:<pramood48in@test_mail.net>'),
            ('server', '250 2.1.5 Ok'),
            ('server', '354 End data with <CR><LF>.<CR><LF>'),
            ('client', 'DATA'),
            ('server', '250 2.0.0 Ok: queued as 319A8641319'),
            ('server', '221 2.0.0 Bye'),
            ('client', 'QUIT')]

        dialect = mails.get_dialect(messages)
        dialect_str = mails.get_dialect_str(dialect)
        hashes_2 = mails.get_dialect_fingerprints(dialect_str)
        self.assertNotEqual(hashes.sha256, hashes_2.sha256)

        # Replace EHLO host. Must be equal
        messages = [
            ('server', '220 localhost ESMTP Postfix'),
            ('server', '250-ENHANCEDSTATUSCODES'),
            ('server', '250-localhost'),
            ('client', 'EHLO changed.90.com'),  # raplaced vip in changed
            ('server', '250-PIPELINING'),
            ('server', '250-SIZE 10240000'),
            ('server', '250-ETRN'),
            ('server', '250 DSN'),
            ('server', '250-8BITMIME'),
            ('server', '250-VRFY'),
            ('client', 'MAIL FROM:<sywangwq@vip.90.com>'),
            ('server', '250 2.1.0 Ok'),
            ('client', 'RCPT TO:<pramood48in@test_mail.net>'),
            ('server', '250 2.1.5 Ok'),
            ('server', '354 End data with <CR><LF>.<CR><LF>'),
            ('client', 'DATA'),
            ('server', '250 2.0.0 Ok: queued as 319A8641319'),
            ('server', '221 2.0.0 Bye'),
            ('client', 'QUIT')]

        dialect = mails.get_dialect(messages)
        dialect_str = mails.get_dialect_str(dialect)
        hashes_2 = mails.get_dialect_fingerprints(dialect_str)
        self.assertEqual(hashes.sha256, hashes_2.sha256)


if __name__ == '__main__':
    unittest.main(verbosity=2)
