#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

import rapidsms

from models import OutgoingMessage, IncomingMessage, Message
from reporters.models import PersistantConnection

class App(rapidsms.app.App):
    
    def configure (self, separated_format=False, flat_format=True, **kwargs):
        """Configure this app. Optionally you can set whether you want to
           log in the separated_format (incoming and outgoing messages are
           stored in different models) or the flat_format (everything saved
           in a single model)"""
        
        # This is overly complex because of the two types of formats.
        # TODO: just get rid of the old formats.
        self._separated_format = separated_format
        self._flat_format = flat_format
        
    def parse(self, message):
        # make and save messages on their way in
        if self._separated_format:
            self._save_incoming(message)
        if self._flat_format:
            self._save_flat(message, incoming=True)
            
    def outgoing(self, message):
        # make and save messages on their way out
        if self._separated_format:
            self._save_outgoing(message)
        if self._flat_format:
            self._save_flat(message, incoming=False)
        
    def _save_incoming(self, message):
        persistent_msg = IncomingMessage.objects.create(identity=message.connection.identity,
                                                        text=message.text,
                                                        backend=message.connection.backend.slug)
        self.debug(persistent_msg)
    
    def _save_outgoing(self, message):
        msg = OutgoingMessage.objects.create(identity=message.connection.identity, text=message.text, 
                                             backend=message.connection.backend.slug)
        self.debug(msg)
    
    def _save_flat(self, message, incoming):
        if not hasattr(message, "persistant_connection"):
            conn = PersistantConnection.from_message(message)
        else:
            conn = message.persistant_connection 
        
        
        persistent_msg = Message.objects.create(connection=conn,
                                                text=message.text,
                                                is_incoming=incoming)
        message.persistent_msg = persistent_msg
        self.debug(persistent_msg)
    
    