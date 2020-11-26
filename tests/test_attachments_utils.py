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

import simplejson as json
from context import attachments


base_path = os.path.realpath(os.path.dirname(__file__))
sample_zip = os.path.join(base_path, 'samples', 'test.zip')
sample_txt = os.path.join(base_path, 'samples', 'test.txt')
vt_report = os.path.join(base_path, 'samples', 'vt_report.json')

fingerprints = attachments.fingerprints
check_archive = attachments.check_archive
contenttype = attachments.contenttype
extension = attachments.extension
reformat_virustotal = attachments.reformat_virustotal

logging.getLogger().addHandler(logging.NullHandler())


class TestAttachmentsUtils(unittest.TestCase):

    def test_fingerprints(self):
        with open(sample_zip, 'rb') as f:
            payload = f.read()

        md5 = "7e3b1204f0131f412e3ad5430b7c7a2e"
        sha1 = "8760ff1422cf2922b649b796cfb58bfb0ccf7801"
        sha256 = ("0477d6173edb6450dcdd7e54e6d0b714aba4f"
                  "6744d96e48b101540eeeed8478f")
        sha512 = ("3eb34cb3abd8c7bbddd2987fdf2011d63fb42"
                  "010d4c0d35f8c1b6a7650d52cb6d166c94358"
                  "e95abca99de2d079db26abcaa271f7830b7f4"
                  "07f2682cf9d729063")
        ssdeep_ = ("3:vh9fSt//l7lRAM7yFXolHw7Y/tPSt//l/ly"
                   "tlHHcMXDdqHgt+lal/t:59m6M74XolQ7YECtJHcEqAt+lu1")

        hashes = fingerprints(payload)
        self.assertEqual(md5, hashes.md5)
        self.assertEqual(sha1, hashes.sha1)
        self.assertEqual(sha256, hashes.sha256)
        self.assertEqual(sha512, hashes.sha512)
        self.assertEqual(ssdeep_, hashes.ssdeep)

        # Test @lru_cache
        hashes = fingerprints(payload)
        self.assertEqual(md5, hashes.md5)
        self.assertEqual(sha1, hashes.sha1)
        self.assertEqual(sha256, hashes.sha256)
        self.assertEqual(sha512, hashes.sha512)
        self.assertEqual(ssdeep_, hashes.ssdeep)

    def test_check_archive(self):
        with open(sample_zip, 'rb') as f:
            payload = f.read()

        with open(sample_txt, 'rb') as f:
            payload_txt = f.read()

        flag, path = check_archive(payload)
        self.assertEqual(flag, True)
        self.assertEqual(path, None)
        self.assertIsInstance(
            check_archive(payload), tuple)

        flag, path = check_archive(payload, True)
        self.assertEqual(flag, True)
        self.assertNotEqual(path, None)
        self.assertIsInstance(
            check_archive(payload), tuple)

        flag, path = check_archive(payload_txt)
        self.assertEqual(flag, False)
        self.assertEqual(path, None)

        flag, path = check_archive(payload_txt, True)
        self.assertEqual(flag, False)
        self.assertNotEqual(path, None)

    def test_contenttype(self):
        with open(sample_zip, 'rb') as f:
            payload = f.read()

        with open(sample_txt, 'rb') as f:
            payload_txt = f.read()

        content_type = contenttype(payload)
        self.assertEqual("application/zip", content_type)

        content_type = contenttype(payload_txt)
        self.assertEqual("application/x-empty", content_type)

    def test_extension(self):
        filename = "test.zip"
        no_ext = "test"

        ext = extension(filename)
        self.assertEqual(ext, ".zip")

        ext = extension(no_ext)
        self.assertFalse(ext)

    def test_reformat_virustotal(self):
        with open(vt_report) as f:
            report = json.load(f)

        self.assertIsInstance(report["results"]["scans"], dict)
        for k, v in report["results"]["scans"].items():
            self.assertIn("detected", v)

        reformat_virustotal(report)
        self.assertIsInstance(report["results"]["scans"], list)
        for i in report["results"]["scans"]:
            self.assertNotIn("detected", i)

        report = {"key_1": "value_1", "key_2": "value_2"}
        report_copy = dict(report)
        reformat_virustotal(report)
        self.assertEqual(report, report_copy)

        report = {}
        reformat_virustotal(report)
        self.assertFalse(report)

    def test_get_urls_tika(self):
        pass


if __name__ == '__main__':
    unittest.main(verbosity=2)
