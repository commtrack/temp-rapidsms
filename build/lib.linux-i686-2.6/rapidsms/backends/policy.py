""" A 'policy' can be used to check, modify, and/or deal with 
incoming or outgoing messages on a variety of different backends. 
Policies are implemented as decorators of the 'send' or 'receive'
function.

The driving use case for backend 'policies' is:
What to do when the system wants to send a text message > 160?
Sometimes you'll want to send it all, sometimes you'll want to
truncate the message, sometimes you'll want to split the message,
and sometimes you'll want to fail. (Some backends are smart, 
and don't need RapidSMS policies; others, less so). These
decorators provide a generic, easily swappable mechanism
for specifying the desired behaviour

Implement policies as decorators on the 'outgoing' function,
after @classmethod. For example:
    @classmethod
    @split_long_message
    def outgoing(klass, message):

CAUTION: Text messages with 1 single unicode character
(or more) can only be 70 characters long, when using a
gsm modem. 

"""
    
def fail_long_message(send):
    """ Fail if message.text is > 160 """
    def decorator(klass, message):
        if len(message.text)>160:
            raise Exception('Message too long to send!')
        send(klass, message)
    return decorator

def truncate_long_message(send):
    """ Truncate if message.text is > 160 to 160 """
    def decorator(klass, message):
        if len(message.text)>160:
            message.text = message.text[:160]
        send(klass, message)
    return decorator

def split_long_message(send):
    """ 
    If message.text is > 160, break into multiple messages
    of size 160 or less 
    """
    def decorator(klass, message):
        if len(message.text)>160:
            original_text = message.text
            start = 0
            message_texts = []
            while len(message.text[start:start+160])>0:
                # TODO - if we can break on a space, then do
                message_texts.append( message.text[start:start+160] )
                start = start + 160
            for m in message_texts:
                message.text = m
                send(klass, message)
            # return the original text back to the message
            # so that logging, etc. continue to work seamlessly
            message.text = original_text
        else:
            send(klass, message)
    return decorator

"""
UNTESTED - demo of how to check for non-gsm (==unicode) characters

def fail_long_message_gsm(send):
    # Fail if gsm message.text > 160, or ucs2 message.text > 70
    def decorator(klass, message):
        from pygsm import gsmcodecs
        try:
            message.text.encode('gsm')
            max_len = 160
        except Exception, e:
            max_len = 70
        if len(message.text) > max_len:
            raise Exception('Message too long to send!')
        send(klass, message)
    return decorator

"""