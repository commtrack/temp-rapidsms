#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

import unittest
from rapidsms.backends.policy import fail_long_message
from rapidsms.backends.policy import truncate_long_message
from rapidsms.backends.policy import split_long_message
from rapidsms.backends.backend import Backend
from rapidsms.message import Message
from rapidsms.person import Person

class TestBackendPolicy(unittest.TestCase):
    def setUp(self):
        self.sent = []
        p = Person()
        self.short_msg = Message(p, text="This is shorter than 160 characters.")
        self.long_msg = Message(p, text="This is longer than 160 characters. 123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901160 ENDS HEREBeginning of second text message.")
        
    def test_send_fail_short (self):
        self.send_fail(self.short_msg)
        self.assertEqual(self.sent[0], self.short_msg.text)
        self.assertEqual(len(self.sent), 1)

    def test_send_fail_long(self):
        try:
            self.send_fail(self.long_msg)
            self.fail("Send fail did not raise an exception")
        except Exception, e:
            if 'too long' in str(e):
                # We got the right exception
                pass
            else:
                raise

    def test_send_truncate_short(self):
        self.send_truncate(self.short_msg)
        self.assertEqual(self.sent[0], self.short_msg.text)
        self.assertEqual(len(self.sent), 1)
        
    def test_send_truncate_long(self):
        self.send_truncate(self.long_msg)
        self.assertEqual(self.sent[0], self.long_msg.text[:160])
        self.assertEqual(len(self.sent), 1)
        
        
    def test_send_split_short(self):
        self.send_split(self.short_msg)
        self.assertEqual(self.sent[0], self.short_msg.text)
        self.assertEqual(len(self.sent), 1)

    def test_send_split_long(self):
        self.send_split(self.long_msg)
        self.assertEqual(self.sent[0], self.long_msg.text[:160])
        self.assertEqual(self.sent[1], self.long_msg.text[160:])
        
    @fail_long_message
    def send_fail(self, message):
        self.sent.append( message.text )
    
    @truncate_long_message
    def send_truncate(self, message):
        self.sent.append( message.text )
    
    @split_long_message
    def send_split(self, message):
        self.sent.append( message.text )

if __name__ == "__main__":
    unittest.main()
