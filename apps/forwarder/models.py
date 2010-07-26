from django.db import models

# Create your Django models here, if you need them.


class ForwardLocation(models.Model):
    """A location to forward to.  Define a url with the following
       REQUIRED format strings somewhere.  %(message)s and %(identity)s
       for example: 
       http://myrapidsmsserver.com/%(identity)s/%(message)s
       http://myrapidsmsserver.com/?phone=%(identity)s&msg=%(message)s
       
       These will be replaced by the actual identity and message parts
       (urlencoded).
       
       For now this only supports simple HTTP GET's, but could be 
       easily extended for POSTs or other forwarding logic.
    """ 
    
    url = models.CharField(max_length=300,help_text=\
         """use the %(message)s and %(identity)s keywords for where to 
            put the two parameters, for example:
            http://myrapidsmsserver.com/?phone=%(identity)s&msg=%(message)s""")
    
    is_active = models.BooleanField(default=True, help_text=\
                                    "Controls whether to forward to this url")
    
    