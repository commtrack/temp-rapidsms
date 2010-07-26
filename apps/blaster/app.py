from datetime import datetime

import rapidsms

from blaster.models import *

class App (rapidsms.app.App):
    """From the view, conduct a message blast.  Responses get collected
       with the blast.  Only one blast can be open at a given time."""
    
    # TODO: due to this app being developed for the Uganda Ministry of
    # Education project it is currently highly coupled with the schools
    # app.  Breaking out these dependencies is left as future work.
    
    def handle (self, message):
        """Add your main application logic in the handle phase."""
        if not message.reporter:
            # couldn't have been intended for us
            return
        
        latest = BlastedMessage.current(message.reporter)
        if latest:
            # if someone has registered to process these message blasts
            # then make sure we call them to determine whether it was 
            # processed successfully.
            success = True
            blast_msg = latest.blast.message
            if blast_msg.handling_app and blast_msg.handling_method:
                app = self.router.get_app(blast_msg.handling_app)
                if hasattr(app, blast_msg.handling_method):
                    success = getattr(app, blast_msg.handling_method)(message)
                    # make sure it's a valid boolean, in case they return nothing
                    # or some other object.  Django doesn't like populating 
                    # boolean fields with random data (obviously)
                    success = True if success else False
            response = BlastResponse.objects.create(message=latest,
                                                    text=message.text,
                                                    date=datetime.now(),
                                                    success=success)
            return True
        
