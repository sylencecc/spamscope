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

import logging
import os
import unittest
import mailparser

try:
    from collections import ChainMap
except ImportError:
    from chainmap import ChainMap

from context import attachments, DEFAULTS

MailAttachments = attachments.MailAttachments

base_path = os.path.realpath(os.path.dirname(__file__))
mail = os.path.join(base_path, 'samples', 'mail_malformed_1')
mail_thug = os.path.join(base_path, 'samples', 'mail_thug')
mail_test_4 = os.path.join(base_path, 'samples', 'mail_test_4')
mail_test_9 = os.path.join(base_path, 'samples', 'mail_test_9')
mail_test_10 = os.path.join(base_path, 'samples', 'mail_test_10')

OPTIONS = ChainMap(os.environ, DEFAULTS)

logging.getLogger().addHandler(logging.NullHandler())


class TestPostProcessing(unittest.TestCase):

    def setUp(self):

        # Init

        p = mailparser.parse_from_file(mail)
        self.attachments = p.attachments

        p = mailparser.parse_from_file(mail_thug)
        self.attachments_thug = p.attachments

    @unittest.skipIf(OPTIONS["VIRUSTOTAL_ENABLED"].capitalize() == "False",
                     "VirusTotal test skipped: "
                     "set env variable 'VIRUSTOTAL_ENABLED' to True")
    def test_virustotal(self):
        """Test add VirusTotal processing."""

        from src.modules.attachments import virustotal

        conf = {"enabled": True,
                "api_key": OPTIONS["VIRUSTOTAL_APIKEY"],
                "whitelist_content_types": [
                    "application/octet-stream",
                    "application/x-dosexec",
                    "application/zip",
                ]}
        attachments = MailAttachments.withhashes(self.attachments)
        attachments(intelligence=False)
        virustotal(conf, attachments)

        # VirusTotal analysis
        for i in attachments:
            self.assertIn('virustotal', i)
            self.assertEqual(i['virustotal']['response_code'], 200)
            self.assertEqual(i['virustotal']['results']['sha1'],
                             '2a7cee8c214ac76ba6fdbc3031e73dbede95b803')
            self.assertIsInstance(i["virustotal"]["results"]["scans"], list)

            for j in i["files"]:
                self.assertIn('virustotal', j)
                self.assertEqual(j['virustotal']['response_code'], 200)
                self.assertEqual(j['virustotal']['results']['sha1'],
                                 'ed2e480e7ba7e37f77a85efbca4058d8c5f92664')
                self.assertIsInstance(
                    j["virustotal"]["results"]["scans"], list)

    @unittest.skipIf(OPTIONS["ZEMANA_ENABLED"].capitalize() == "False",
                     "Zemana test skipped: "
                     "set env variable 'ZEMANA_ENABLED' to True")
    def test_zemana(self):
        """Test add Zemana processing."""

        from src.modules.attachments import zemana

        conf = {"enabled": True,
                "PartnerId": OPTIONS["ZEMANA_PARTNERID"],
                "UserId": OPTIONS["ZEMANA_USERID"],
                "ApiKey": OPTIONS["ZEMANA_APIKEY"],
                "useragent": "SpamScope"}
        attachments = MailAttachments.withhashes(self.attachments)
        attachments(intelligence=False)
        zemana(conf, attachments)

        # Zemana analysis
        for i in attachments:
            self.assertIn("zemana", i)
            self.assertIn("type", i["zemana"])
            self.assertIn("aa", i["zemana"])
            self.assertIsInstance(i["zemana"]["aa"], list)

            for j in i["files"]:
                self.assertIn("zemana", j)
                self.assertIn("type", j["zemana"])
                self.assertIn("aa", j["zemana"])
                self.assertIsInstance(j["zemana"]["aa"], list)

    def test_tika(self):
        """Test add Tika processing."""

        from src.modules.attachments import tika

        # Complete parameters
        conf = {"enabled": True,
                "path_jar": OPTIONS["TIKA_APP_JAR"],
                "memory_allocation": None,
                "whitelist_content_types": ["application/zip"]}
        attachments = MailAttachments.withhashes(self.attachments)
        attachments(intelligence=False)
        tika(conf, attachments)

        for i in attachments:
            self.assertIn("tika", i)

        self.assertEqual(len(attachments[0]["tika"]), 2)
        self.assertEqual(
            int(attachments[0]["tika"][0]["Content-Length"]),
            attachments[0]["size"])

        # tika disabled
        conf["enabled"] = False
        attachments = MailAttachments.withhashes(self.attachments)
        attachments(intelligence=False)
        tika(conf, attachments)

        for i in attachments:
            self.assertNotIn("tika", i)

        conf["enabled"] = True

        # attachments without run()
        with self.assertRaises(KeyError):
            attachments = MailAttachments.withhashes(self.attachments)
            tika(conf, attachments)

        # attachments a key of conf
        conf_inner = {
            "enabled": True,
            "path_jar": OPTIONS["TIKA_APP_JAR"],
            "memory_allocation": None}
        attachments = MailAttachments.withhashes(self.attachments)
        tika(conf_inner, attachments)
        for i in attachments:
            self.assertNotIn("tika", i)

    def test_tika_bug_incorrect_padding(self):
        """Test add Tika processing."""

        from src.modules.attachments import tika

        # Complete parameters
        conf = {"enabled": True,
                "path_jar": OPTIONS["TIKA_APP_JAR"],
                "memory_allocation": None,
                "whitelist_content_types": ["application/zip"]}

        p = mailparser.parse_from_file(mail_test_4)
        attachments = MailAttachments.withhashes(p.attachments)
        attachments(intelligence=False)
        tika(conf, attachments)

        for i in attachments:
            self.assertIn("tika", i)

    def test_tika_uuencode(self):
        """Test Tika processing on an uuencoded archive."""

        from src.modules.attachments import tika

        # Complete parameters
        conf = {"enabled": True,
                "path_jar": OPTIONS["TIKA_APP_JAR"],
                "memory_allocation": None,
                "whitelist_content_types": [
                    "application/zip", "application/octet-stream"]}

        p = mailparser.parse_from_file(mail_test_10)
        attachments = MailAttachments.withhashes(p.attachments)
        attachments(intelligence=False)
        tika(conf, attachments)

        self.assertIn("tika", attachments[0])

    @unittest.skipIf(OPTIONS["THUG_ENABLED"].capitalize() == "False",
                     "Thug test skipped: "
                     "set env variable 'THUG_ENABLED' to True")
    def test_thug(self):
        """Test add Thug processing."""

        from src.modules.attachments import thug

        # Complete parameters
        conf = {"enabled": True,
                "extensions": [".html", ".js", ".jse"],
                "user_agents": ["win7ie90", "winxpie80"],
                "referer": "http://www.google.com/",
                "timeout": 300}
        attachments = MailAttachments.withhashes(self.attachments_thug)
        attachments(intelligence=False)

        first_attachment = attachments[0]
        self.assertNotIn('thug', first_attachment)

        thug(conf, attachments)

        # Thug attachment
        thug_attachment = first_attachment['files'][0]
        self.assertIn('thug', thug_attachment)

        thug_analysis = thug_attachment['thug']
        self.assertIsInstance(thug_analysis, list)
        self.assertEqual(len(thug_analysis), 2)

        first_thug_analysis = thug_analysis[0]
        self.assertIn('files', first_thug_analysis)
        self.assertIn('code', first_thug_analysis)
        self.assertIn('exploits', first_thug_analysis)
        self.assertIn('url', first_thug_analysis)
        self.assertIn('timestamp', first_thug_analysis)
        self.assertIn('locations', first_thug_analysis)
        self.assertIn('connections', first_thug_analysis)
        self.assertIn('logtype', first_thug_analysis)
        self.assertIn('behavior', first_thug_analysis)
        self.assertIn('thug', first_thug_analysis)
        self.assertIn('classifiers', first_thug_analysis)
        self.assertEqual(
            first_thug_analysis['thug']['personality']['useragent'],
            'win7ie90')
        self.assertEqual(
            first_thug_analysis['thug']['options']['referer'],
            'http://www.google.com/')

    def test_store_samples_unicode_error(self):
        from datetime import datetime
        import shutil
        from src.modules.attachments import store_samples

        # Complete parameters
        conf = {"enabled": True,
                "base_path": "/tmp"}

        p = mailparser.parse_from_file(mail_test_9)
        attachments = MailAttachments.withhashes(p.attachments)
        attachments(intelligence=False)
        store_samples(conf, attachments)

        now = str(datetime.utcnow().date())
        # Not an issue in py3, this extracts as expected
        sample = os.path.join(
            "/tmp",
            now,
            "43573896890da36e092039cf0b3a92f8_Swiftoutput·pdf.exe")
        self.assertTrue(os.path.exists(sample))
        shutil.rmtree(os.path.join("/tmp", now))

        p = mailparser.parse_from_file(mail_test_10)
        attachments = MailAttachments.withhashes(p.attachments)
        attachments(intelligence=False)
        store_samples(conf, attachments)
        sample = os.path.join(
            "/tmp",
            now,
            "30f0b27f89417fd363e7f44204512083_REQUEST FOR QUOTE.exe")
        self.assertTrue(os.path.exists(sample))
        shutil.rmtree(os.path.join("/tmp", now))

    def test_store_samples(self):
        """Test add store file system processing."""

        from datetime import datetime
        import shutil
        from src.modules.attachments import store_samples

        # Complete parameters
        conf = {"enabled": True,
                "base_path": "/tmp"}
        attachments = MailAttachments.withhashes(self.attachments)
        attachments(intelligence=False)
        store_samples(conf, attachments)

        now = str(datetime.utcnow().date())
        sample = os.path.join(
            "/tmp",
            now,
            "1e38e543279912d98cbfdc7b275a415e_20160523_916527.jpg_.zip")

        sample_child = os.path.join(
            "/tmp",
            now,
            "495315553b8af47daada4b279717f651_20160523_211439.jpg_.jpg.exe")

        self.assertFalse(os.path.exists(sample))
        self.assertTrue(os.path.exists(sample_child))
        shutil.rmtree(os.path.join("/tmp", now))


if __name__ == '__main__':
    unittest.main(verbosity=2)
