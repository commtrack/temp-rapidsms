import urllib2

import rapidsms

from forwarder.models import ForwardLocation

class App (rapidsms.app.App):
    """The forwarder app allows you to check other rapidsms installations
       for message handling logic.  You define a configured list of servers
       to forward to, and this app will forward the message to all of them.
       
       It recommended that if you are doing any additional processing on your
       own server that this app be put _last_ in your list of apps, so that
       any messages that are handled by any of the other installed apps are
       not extraneously forwarded.
    """

    def start (self):
        """Configure your app in the start phase."""
        pass

    def parse (self, message):
        """Parse and annotate messages in the parse phase."""
        pass

    def handle (self, message):
        """Forward the messages to any configured URLs"""
        forward_urls = ForwardLocation.objects.filter(is_active=True)
        for url in forward_urls:
            formatted_url = url.url % {"message": urllib2.quote(message.text),
                                       "identity": urllib2.quote(message.peer) }
            response = urllib2.urlopen(formatted_url)
            

    def cleanup (self, message):
        """Perform any clean up after all handlers have run in the
           cleanup phase."""
        pass

    def outgoing (self, message):
        """Handle outgoing message notifications."""
        pass

    def stop (self):
        """Perform global app cleanup when the application is stopped."""
        pass
