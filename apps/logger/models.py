#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

import django
from django.db import models
from reporters.models import PersistantConnection, PersistantBackend

class Message(models.Model):
    """A Message being logged"""
    # A new way of logging!  This feels cleaner than the separate
    # models below and makes it significantly easier to build 
    # views/applications on top of both incoming and outgoing 
    # messages.  The old classes are left as legacy
    
    connection = models.ForeignKey(PersistantConnection)
    is_incoming = models.BooleanField()
    text = models.CharField(max_length=160)
    date = models.DateTimeField(auto_now_add=True)
    
    @classmethod
    def outgoing(cls):
        """Gets a query set of outgoing messages"""
        return cls.objects.Filter(is_incoming=False)
    
    @classmethod
    def incoming(cls):
        """Gets a query set of incoming messages"""
        return cls.objects.Filter(is_incoming=True)
    
    @classmethod
    def from_outgoing(cls, outgoing):
        """Create a Message object from the IncomingMessage model"""
        return cls._from_old(outgoing, False)
    
    @classmethod
    def from_incoming(cls, incoming):
        """Create a Message object from the IncomingMessage model"""
        return cls._from_old(outgoing, False)
    
    @classmethod
    def from_incoming(cls, incoming):
        backend = PersistantBackend.objects.get(slug=incoming.backend)
        conn, created = PersistantConnection.objects.get_or_create(backend  = backend,
                                                                  identity = incoming.identity)
        if created:
            conn.save()
        to_return = Message(text=incoming.text, date=incoming.date, 
                            is_incoming=True, connection=conn)
        return to_return
    
    def __unicode__(self):
        return "%s: %s" % (self.connection, self.text)
    
    class Meta:
        get_latest_by = 'date'
        # the permission required for this tab to display in the UI
        permissions = (
            ("can_view", "Can view message logs"),
        )

class MessageBase(models.Model):
    text = models.CharField(max_length=140)
    # TODO save connection title rather than wacky object string?
    identity = models.CharField(max_length=150)
    backend = models.CharField(max_length=150)
    
    def __unicode__(self):
        return "%s (%s) %s" % (self.identity, self.backend, self.text)
    
    class Meta:
        abstract = True
    
    
    
class IncomingMessage(MessageBase):
    received = models.DateTimeField(auto_now_add=True)
    
    # Helper methods to allow this object to be treated similar
    # to the outgoing message, e.g. if they are in the same list
    # in a template
    @property
    def date(self):
        '''Same as received''' 
        return self.received
    
    def is_incoming(self):
        return True
    
    def __unicode__(self):
        return "%s %s" % (MessageBase.__unicode__(self), self.received)  

    class Meta:
        get_latest_by = 'received'
        
    
class OutgoingMessage(MessageBase):
    sent = models.DateTimeField(auto_now_add=True)
    
    @property
    def date(self):
        '''Same as sent''' 
        return self.sent
    
    def is_incoming(self):
        return False
    
    def __unicode__(self):
        return "%s %s" % (MessageBase.__unicode__(self), self.sent)  
