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
import os
import sys
import unittest

base_path = os.path.realpath(os.path.dirname(__file__))
root = os.path.join(base_path, '..')
sys.path.append(root)

from src.modules.redis_client import Redis, RedisConnectionFailed

logging.getLogger().addHandler(logging.NullHandler())


class TestRedis(unittest.TestCase):

    def test_init(self):
        redis = Redis()

        self.assertEqual(redis.hosts, ["127.0.0.1"])
        self.assertEqual(redis.shuffle_hosts, True)
        self.assertEqual(redis.port, 6379)
        self.assertEqual(redis.db, 0)
        self.assertEqual(redis.password, None)
        self.assertEqual(redis.reconnect_interval, 1)
        self.assertEqual(redis.max_retry, 60)

        redis.max_retry = 0
        self.assertEqual(redis.max_retry, 0)

        with self.assertRaises(RuntimeError):
            redis = Redis(hosts=1)

    def test_push_message(self):
        redis = Redis(max_retry=0)

        with self.assertRaises(RuntimeError):
            redis.push_messages()

        with self.assertRaises(RedisConnectionFailed):
            redis.push_messages(queue="test", messages="Test message")


if __name__ == '__main__':
    unittest.main(verbosity=2)
