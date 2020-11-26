#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright 2016 Fedele Mantuano (https://www.linkedin.com/in/fmantuano/)

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

import base64
import logging
import copy
import datetime
import os
import time
import unittest
from operator import itemgetter
from collections import deque

from pyfaup.faup import Faup
import mailparser

from context import attachments, utils

MailAttachments = attachments.MailAttachments
fingerprints = attachments.fingerprints

base_path = os.path.realpath(os.path.dirname(__file__))
text_file = os.path.join(base_path, 'samples', 'lorem_ipsum.txt')
mail = os.path.join(base_path, 'samples', 'mail_thug')
mail_test_7 = os.path.join(base_path, 'samples', 'mail_test_7')
mail_test_11 = os.path.join(base_path, 'samples', 'mail_test_11')


logging.getLogger().addHandler(logging.NullHandler())


@utils.timeout(2)
def sleeping():
    time.sleep(30)


class TestUtils(unittest.TestCase):
    faup = Faup()

    def setUp(self):
        self.f = utils.reformat_output

        p = mailparser.parse_from_file(mail)
        self.mail_obj = p.mail
        self.mail_obj['analisys_date'] = datetime.datetime.utcnow().isoformat()

        self.attachments = MailAttachments.withhashes(p.attachments)
        self.attachments.run()

        self.parameters = {
            'elastic_index_mail': "spamscope_mails-",
            'elastic_type_mail': "spamscope",
            'elastic_index_attach': "spamscope_attachments-",
            'elastic_type_attach': "spamscope"}

    def test_mail_item(self):
        mail = utils.MailItem(
            filename=text_file,
            mail_server="test_mail_server",
            mailbox="test_mailbox",
            priority=1,
            trust="test_trust",
            mail_type=1,
            headers=["header1", "header2"])

        self.assertEqual(mail.filename, text_file)
        self.assertEqual(mail.mail_server, "test_mail_server")
        self.assertEqual(mail.mailbox, "test_mailbox")
        self.assertEqual(mail.priority, 1)
        self.assertEqual(mail.trust, "test_trust")
        self.assertIsInstance(mail.timestamp, float)
        self.assertEqual(mail.mail_type, 1)
        self.assertIsInstance(mail.headers, list)
        self.assertEqual(mail.headers, ["header1", "header2"])

        mail_1 = utils.MailItem(
            filename=text_file,
            mail_server="test_mail_server",
            mailbox="test_mailbox",
            priority=1,
            trust="test_trust")

        mail_2 = utils.MailItem(
            filename=text_file,
            mail_server="test_mail_server",
            mailbox="test_mailbox",
            priority=2,
            trust="test_trust")

        mail_3 = utils.MailItem(
            filename=text_file,
            mail_server="test_mail_server",
            mailbox="test_mailbox",
            priority=1,
            trust="test_trust")

        self.assertTrue(mail_1 < mail_2)
        self.assertFalse(mail_1 < mail_3)

    def test_load_conf(self):
        c = "conf/spamscope.example.yml"
        conf = utils.load_config(c)
        self.assertIsInstance(conf, dict)

        with self.assertRaises(RuntimeError):
            utils.load_config("conf/fake.yml")

    def test_write_payload(self):
        with open(text_file, 'rb') as f:
            payload = f.read()
        sha1_origin = fingerprints(payload).sha1

        file_path = utils.write_payload(base64.b64encode(payload), ".txt")
        self.assertEqual(os.path.splitext(file_path)[-1], ".txt")

        with open(file_path) as f:
            payload = f.read()
        sha1_clone = fingerprints(payload).sha1

        self.assertEqual(sha1_origin, sha1_clone)
        self.assertTrue(os.path.exists(file_path))

        os.remove(file_path)
        self.assertFalse(os.path.exists(file_path))

        p = mailparser.parse_from_file(mail_test_11)
        attachments = MailAttachments.withhashes(p.attachments)
        attachments.run()

        for i in attachments:
            temp = utils.write_payload(
                i["payload"],
                i["extension"],
                i["content_transfer_encoding"],
            )
            os.remove(temp)

    def test_search_words_in_text(self):
        with open(text_file) as f:
            text = f.read()

        keywords_1 = [
            "nomatch",
            "nomatch"]
        self.assertEqual(
            utils.search_words_in_text(text, keywords_1), False)

        keywords_2 = [
            "nomatch",
            "nomatch",
            "theophrastus rationibus"]
        self.assertEqual(
            utils.search_words_in_text(text, keywords_2), True)

        keywords_3 = [
            "nomatch",
            "theophrastus nomatch"]
        self.assertEqual(
            utils.search_words_in_text(text, keywords_3), False)

        keywords_4 = ["theophrastus quo vidit"]
        self.assertEqual(
            utils.search_words_in_text(text, keywords_4), True)

        keywords_5 = [12345678]
        self.assertEqual(
            utils.search_words_in_text(text, keywords_5), True)

        keywords_6 = [11111, 44444]
        self.assertEqual(
            utils.search_words_in_text(text, keywords_6), True)

    def test_reformat_output_first(self):

        with self.assertRaises(RuntimeError):
            self.f(mail=self.mail_obj)

        with self.assertRaises(KeyError):
            self.f(mail=self.mail_obj, bolt="output-elasticsearch")

        m, a = self.f(
            mail=self.mail_obj, bolt="output-elasticsearch", **self.parameters)

        # Attachments
        self.assertIsInstance(a, list)
        self.assertEqual(len(a), 1)
        self.assertIsInstance(a[0], dict)
        self.assertIn('@timestamp', m)
        self.assertIn('_index', a[0])
        self.assertIn('_type', a[0])
        self.assertIn('type', a[0])

        # Mail
        self.assertIsInstance(m, dict)
        self.assertIn('@timestamp', m)
        self.assertIn('_index', m)
        self.assertIn('_type', m)
        self.assertIn('type', m)

    def test_reformat_output_second(self):
        m = copy.deepcopy(self.mail_obj)
        m['attachments'] = list(self.attachments)

        m, a = self.f(
            mail=m, bolt="output-elasticsearch", **self.parameters)

        # Attachments
        self.assertIsInstance(a, list)
        self.assertEqual(len(a), 2)

        self.assertIsInstance(a[0], dict)
        self.assertIn('@timestamp', a[0])
        self.assertIn('_index', a[0])
        self.assertIn('_type', a[0])
        self.assertIn('type', a[0])
        self.assertIn('payload', a[0])
        self.assertEqual(a[0]['is_archived'], True)

        self.assertIsInstance(a[1], dict)
        self.assertIn('@timestamp', a[1])
        self.assertIn('_index', a[1])
        self.assertIn('_type', a[1])
        self.assertIn('type', a[1])
        self.assertIn('files', a[1])
        self.assertIn('payload', a[1])
        # self.assertIn('tika', a[1])
        self.assertNotIn('payload', a[1]['files'][0])
        self.assertEqual(a[1]['is_archived'], False)
        self.assertEqual(a[1]['is_archive'], True)

        # Mail
        self.assertIsInstance(m, dict)
        self.assertIn('@timestamp', m)

    def test_reformat_output_third(self):
        m = copy.deepcopy(self.mail_obj)
        m['attachments'] = list(self.attachments)

        m, a = self.f(mail=m, bolt="output-redis")

        # Attachments
        self.assertIsInstance(a, list)
        self.assertEqual(len(a), 2)

        self.assertIsInstance(a[0], dict)
        self.assertNotIn('@timestamp', a[0])
        self.assertNotIn('_index', a[0])
        self.assertNotIn('_type', a[0])
        self.assertNotIn('type', a[0])
        self.assertIn('payload', a[0])
        self.assertEqual(a[0]['is_archived'], True)

        self.assertIsInstance(a[1], dict)
        self.assertNotIn('@timestamp', a[1])
        self.assertNotIn('_index', a[1])
        self.assertNotIn('_type', a[1])
        self.assertNotIn('type', a[1])
        self.assertIn('files', a[1])
        self.assertIn('payload', a[1])
        # self.assertIn('tika', a[1])
        self.assertNotIn('payload', a[1]['files'][0])
        self.assertEqual(a[1]['is_archived'], False)
        self.assertEqual(a[1]['is_archive'], True)

        # Mail
        self.assertIsInstance(m, dict)
        self.assertNotIn('@timestamp', m)
        self.assertNotIn('_index', m)
        self.assertNotIn('_type', m)
        self.assertNotIn('type', m)

    def test_load_keywords_list(self):
        d = {"generic": "conf/keywords/subjects.example.yml",
             "custom": "conf/keywords/subjects_english.example.yml"}
        results = utils.load_keywords_list(d)
        self.assertIsInstance(results, set)
        self.assertIn("fattura", results)
        self.assertIn("conferma", results)
        self.assertIn("123456", results)
        self.assertNotIn(123456, results)

        with self.assertRaises(RuntimeError):
            d = {"generic": "conf/keywords/targets.example.yml"}
            results = utils.load_keywords_list(d)

    def test_load_keywords_dict(self):
        d = {"generic": "conf/keywords/targets.example.yml",
             "custom": "conf/keywords/targets_english.example.yml"}
        results = utils.load_keywords_dict(d)
        self.assertIsInstance(results, dict)
        self.assertIn("Banca Tizio", results)
        self.assertNotIn("banca tizio", results)
        self.assertIn("tizio", results["Banca Tizio"])
        self.assertIn("caio rossi", results["Banca Tizio"])
        self.assertNotIn(12345, results["Banca Tizio"])
        self.assertIn("12345", results["Banca Tizio"])
        self.assertNotIn("123", results["Banca Tizio"])
        self.assertNotIn(123, results["Banca Tizio"])
        self.assertIn("123 456", results["Banca Tizio"])

        with self.assertRaises(RuntimeError):
            d = {"generic": "conf/keywords/subjects.example.yml"}
            results = utils.load_keywords_dict(d)

    def test_urls_extractor(self):

        body = """
        bla bla https://tweetdeck.twitter.com/random bla bla
        http://kafka.apache.org/documentation.html
        http://kafka.apache.org/documentation1.html
        bla bla bla https://docs.python.org/2/library/re.html bla bla
        bla bla bla https://docs.python.org/2/library/re_2.html> bla bla
        <p>https://tweetdeck.twitter.com/random</p> bla bla
        <p>https://tweetdeck.twitter.com/random_2</p>
        """

        body_unicode_error = """
        Return-Path: <>
        Delivered-To: umaronly@poormail.com
        Received: (qmail 15482 invoked from network); 29 Nov 2015 12:28:40 -000
        Received: from unknown (HELO 112.149.154.61) (112.149.154.61)
        by smtp.customers.net with SMTP; 29 Nov 2015 12:28:40 -0000
        Received: from unknown (HELO localhost)
            (meghan3353839.5f10e@realiscape.com@110.68.103.81)
                by 112.149.154.61 with ESMTPA; Sun, 29 Nov 2015 21:29:24 +0900
                From: meghan3353839.5f10e@realiscape.com
                To: umaronly@poormail.com
                Subject: Gain your male attrctiveness

                Give satisfaction to your loved one
                http://contents.xn--90afavbplfx2a6a5b2a.xn--p1ai/
        """

        urls = utils.urls_extractor(body, self.faup)
        self.assertIsInstance(urls, dict)
        self.assertIn("apache.org", urls)
        self.assertIn("python.org", urls)
        self.assertIn("twitter.com", urls)

        for i in ("apache.org", "python.org", "twitter.com"):
            self.assertIsInstance(urls[i], list)
            self.assertEqual(len(urls[i]), 2)

        urls = utils.urls_extractor(body_unicode_error, self.faup)
        self.assertIsInstance(urls, dict)
        self.assertIn("xn--90afavbplfx2a6a5b2a.xn--p1ai", urls)
        self.assertEqual(len(urls["xn--90afavbplfx2a6a5b2a.xn--p1ai"]), 1)

    def test_load_whitelist(self):
        d = {"generic": {"path": "conf/whitelists/generic.example.yml"}}
        results = utils.load_whitelist(d)
        self.assertIsInstance(results, set)
        self.assertIn("google.com", results)
        self.assertIn("amazon.com", results)
        self.assertIn("facebook.com", results)

        d = {"generic": {
            "path": "conf/whitelists/generic.example.yml",
            "expiry": None}}
        results = utils.load_whitelist(d)
        self.assertIsInstance(results, set)
        self.assertIn("google.com", results)
        self.assertIn("amazon.com", results)
        self.assertIn("facebook.com", results)

        d = {"generic": {
            "path": "conf/whitelists/generic.example.yml",
            "expiry": "2016-06-28T12:33:00.000Z"}}
        results = utils.load_whitelist(d)
        self.assertIsInstance(results, set)
        self.assertEqual(len(results), 0)

    def test_text2urls_whitelisted(self):

        body = """
        bla bla https://tweetdeck.twitter.com/random bla bla
        http://kafka.apache.org/documentation.html
        http://kafka.apache.org/documentation1.html
        bla bla bla https://docs.python.org/2/library/re.html bla bla
        bla bla bla https://docs.python.org/2/library/re_2.html> bla bla
        <p>https://tweetdeck.twitter.com/random</p> bla bla
        <p>https://tweetdeck.twitter.com/random_2</p>
        """

        d = {"generic": {"path": "conf/whitelists/generic.example.yml"}}
        whitelist = utils.load_whitelist(d)
        urls = utils.text2urls_whitelisted(body, whitelist, self.faup)

        self.assertIsInstance(urls, dict)
        self.assertNotIn("apache.org", urls)
        self.assertIn("python.org", urls)
        self.assertIsInstance(urls["python.org"], list)
        self.assertIn("twitter.com", urls)
        self.assertIsInstance(urls["twitter.com"], list)

    def test_text2urls_whitelisted_nonetype_error(self):
        p = mailparser.parse_from_file(mail_test_7)
        body = p.body
        urls = utils.urls_extractor(body, self.faup)

        for k in urls:
            self.assertIsNotNone(k)

        d = {"generic": {"path": "conf/whitelists/generic.example.yml"}}
        whitelist = utils.load_whitelist(d)

        utils.text2urls_whitelisted(body, whitelist, self.faup)

    def test_reformat_urls(self):

        body = """
        bla bla https://tweetdeck.twitter.com/random bla bla
        http://kafka.apache.org/documentation.html
        http://kafka.apache.org/documentation1.html
        bla bla bla https://docs.python.org/2/library/re.html bla bla
        bla bla bla https://docs.python.org/2/library/re_2.html> bla bla
        <p>https://tweetdeck.twitter.com/random</p> bla bla
        <p>https://tweetdeck.twitter.com/random_2</p>
        """

        d = {"generic": {"path": "conf/whitelists/generic.example.yml"}}
        whitelist = utils.load_whitelist(d)
        urls = utils.text2urls_whitelisted(body, whitelist, self.faup)
        self.assertIsInstance(urls, dict)

        urls = utils.reformat_urls(urls)
        self.assertIsInstance(urls, list)

        with self.assertRaises(TypeError):
            utils.reformat_urls(dict)

    def test_timeout(self):
        with self.assertRaises(utils.TimeoutError):
            sleeping()

    def test_register_order(self):
        register = utils.register
        processors = set()

        @register(processors, priority=2)
        def number_two():
            pass

        @register(processors, priority=1)
        def number_one():
            pass

        @register(processors, priority=4)
        def number_four():
            pass

        @register(processors, priority=3)
        def number_three():
            pass

        processors = [i[0] for i in sorted(processors, key=itemgetter(1))]

        self.assertIs(processors[0], number_one)
        self.assertIs(processors[1], number_two)
        self.assertIs(processors[2], number_three)
        self.assertIs(processors[3], number_four)

    def test_is_file_older_than(self):
        r = utils.is_file_older_than(text_file, seconds=20)
        self.assertTrue(r)
        r = utils.is_file_older_than(text_file, seconds=3153600000)
        self.assertFalse(r)

    def test_dump_load(self):
        path = "/tmp/object.dump"
        d = deque(maxlen=5)
        d.append(1)
        d.append(2)
        self.assertIsInstance(d, deque)
        utils.dump_obj(path, d)
        d_dumped = utils.load_obj(path)
        self.assertIsInstance(d_dumped, deque)
        self.assertEqual(d, d_dumped)


if __name__ == '__main__':
    unittest.main(verbosity=2)
