#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright 2019 Fedele Mantuano (https://www.linkedin.com/in/fmantuano/)

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

from datetime import date

import glob
import os
import shutil

from modules import (
    AbstractSpout,
    is_file_older_than,
    MAIL_PATH_OUTLOOK,
    MAIL_PATH,
    MailItem,
)


class IterFilesMailSpout(AbstractSpout):
    outputs = [
        'raw_mail',
        'mail_server',
        'mailbox',
        'priority',
        'trust',
        'mail_type',
        'headers'
    ]

    def initialize(self, stormconf, context):
        super(IterFilesMailSpout, self).initialize(stormconf, context)
        self._check_conf()
        self.mails = self.iter_mails()

    def _check_conf(self):
        self._fail_seconds = int(self.conf.get("fail.after.seconds", 60))
        self._what = self.conf["post_processing"].get("what", "remove").lower()
        self._where = self.conf["post_processing"].get("where", "/tmp/moved")
        if not os.path.exists(self._where):
            os.makedirs(self._where)
        self._where_failed = self.conf["post_processing"].get(
            "where.failed", "/tmp/failed")
        if not os.path.exists(self._where_failed):
            os.makedirs(self._where_failed)

    def iter_mails(self):
        for k, v in self.conf["mailboxes"].items():
            path = v["path_mails"]
            pattern = v["files_pattern"]
            mail_type = MAIL_PATH
            if v.get("outlook", False):
                mail_type = MAIL_PATH_OUTLOOK

            for mail in glob.iglob(os.path.join(path, pattern)):
                if mail.endswith(".processing"):
                    try:
                        self._fail_old_mails(mail)
                    except OSError:
                        # mail already deleted
                        pass
                else:
                    yield MailItem(
                        filename=mail,
                        mail_server=v["mail_server"],
                        mailbox=k,
                        priority=None,
                        trust=v["trust_string"],
                        mail_type=mail_type,
                        headers=v.get("headers", []))

    def next_tuple(self):
        try:
            # get the next mail
            mail = next(self.mails)
            mail_string = mail.filename.split("/")[-1]
            self.log("EMITTED - {!r}".format(mail_string))
            processing = mail.filename + ".processing"

            try:
                shutil.move(mail.filename, processing)
            except IOError:
                self.log("ALREADY EMITTED - {!r}".format(mail_string))
            else:
                self.emit([
                    processing,  # 0
                    mail.mail_server,  # 1
                    mail.mailbox,  # 2
                    mail.priority,  # 3
                    mail.trust,  # 4
                    mail.mail_type,  # 5
                    mail.headers],  # 6
                    tup_id=mail.filename)

        except StopIteration:
            # Reload general spout conf
            self._conf_loader()

            # Load new mails
            self.mails = self.iter_mails()

    def ack(self, tup_id):
        """Acknowledge tup_id, that is the path_mail. """

        mail_string = tup_id.split("/")[-1]
        self.log("ACKED - {!r}".format(mail_string))

        processing = tup_id + ".processing"

        if self._what == "remove":
            try:
                os.remove(processing)
            except Exception:
                self.log("Failed to remove {!r} mail".format(processing))
        else:
            try:
                now = str(date.today())
                mail_path = os.path.join(self._where, now)
                if not os.path.exists(mail_path):
                    os.makedirs(mail_path)
                # this chmod is useful to work under
                # nginx directory listing
                os.chmod(processing, 0o775)
                mail = os.path.join(mail_path, mail_string)
                shutil.move(processing, mail)
            except shutil.Error:
                os.remove(processing)

    def fail(self, tup_id):
        self._move_fail(tup_id)

    def _move_fail(self, src):
        mail_string = src.split("/")[-1]
        mail = os.path.join(self._where_failed, mail_string)
        processing = src + ".processing"

        try:
            os.chmod(processing, 0o775)
            shutil.move(processing, mail)
        finally:
            self.log("FAILED - {!r}".format(mail_string))

    def _fail_old_mails(self, process_mail):
        mail = process_mail.replace(".processing", "")
        mail_string = mail.split("/")[-1]
        if is_file_older_than(process_mail, self._fail_seconds):
            self.log("Mail {!r} older than {} seconds".format(
                mail_string, self._fail_seconds))
            self._move_fail(mail)
