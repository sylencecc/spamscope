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

import logging

try:
    from modules import register
except ImportError:
    from ...modules import register

try:
    from modules import MAIL_PATH, MAIL_STRING
except ImportError:
    from ...modules import MAIL_PATH, MAIL_STRING


# The processors is a set of tuples (function, priority)
# You can use it to sort the post processing analysis
# Example:
#
# from operator import itemgetter
# p_ordered = [i[0] for i in sorted(processors, key=itemgetter(1))]

processors = set()


log = logging.getLogger(__name__)


"""
This module contains all post processors for raw mails
(i.e.: SpamAssassin, etc.).

The skeleton of function must be like this:

    @register(processors, active=True)
    def processor(conf, raw_mail, mail_type, results):
        if conf["enabled"]:
            from module_x import y # import custom object for this processor
            ...
        results["processor"] = report

The function must be have the same name of configuration section in
conf/spamscope.yml --> raw_mail --> processor

The results will be added on dict given as input.

Don't forget decorator @register()

You don't need anything else.
"""


@register(processors, active=True)
def spamassassin(conf, raw_mail, mail_type, results):
    """This method updates the mail results
    with the SpamAssassin report.

    Args:
        conf (dict): dict of configuration
        raw_mail (string): raw mail
        mail_type (string): type of mail (mail path, mail string, ...)
        results (dict): dict where will put the results

    Returns:
        This method updates the results dict given
    """

    if conf["enabled"]:
        from .spamassassin_analysis import report_from_file, report_from_string

        spamassassin = {
            MAIL_PATH: report_from_file,
            MAIL_STRING: report_from_string}

        results["spamassassin"] = spamassassin[mail_type](raw_mail)


@register(processors, active=True)
def dialect(conf, raw_mail, mail_type, results):
    """This method updates the mail results
    with the dialect report.

    Args:
        conf (dict): dict of configuration
        raw_mail (string): raw mail
        mail_type (string): type of mail (mail path, mail string, ...)
        results (dict): dict where will put the results

    Returns:
        This method updates the results dict given
    """

    if conf["enabled"]:
        import mailparser
        from .dialects import make_dialect_report

        parser = {
            MAIL_PATH: mailparser.parse_from_file,
            MAIL_STRING: mailparser.parse_from_string}

        message_id = parser[mail_type](raw_mail).message_id
        elastic_server = conf["elasticsearch"]["hosts"]
        index_prefix = conf["elasticsearch"]["index.prefix.postfix"]

        report = make_dialect_report(
            message_id, elastic_server, index_prefix)

        if report:
            results["dialect"] = report
