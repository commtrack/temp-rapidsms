#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import rapidsms

class App (rapidsms.app.App):
    """ Dummy app.py so router stops complaining """

    def handle(self, msg):
        pass

