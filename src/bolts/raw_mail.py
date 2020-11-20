#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright 2017 Fedele Mantuano (https://www.linkedin.com/in/fmantuano/)

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


from modules import AbstractBolt
from modules.mails import processors
from operator import itemgetter

p_ordered = [i[0] for i in sorted(processors, key=itemgetter(1))]


class RawMail(AbstractBolt):
    """
    Post processing raw mails with third party tools
    """

    outputs = ['sha256_random', 'results', 'is_filtered']

    def process(self, tup):
        sha256_random = tup.values[0]
        sha256 = sha256_random.split("_")[0]
        self.log("Processing started: {}".format(sha256))
        raw_mail = tup.values[1]
        mail_type = tup.values[2]
        is_filtered = tup.values[3]

        results = {}

        if not is_filtered:
            for p in p_ordered:
                try:
                    p(self.conf[p.__name__], raw_mail, mail_type, results)
                except KeyError:
                    self.log("KeyError: {!r} doesn't exist in conf".format(
                        p.__name__), "error")

        self.emit([sha256_random, results, is_filtered])
