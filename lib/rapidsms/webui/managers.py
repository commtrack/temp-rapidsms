#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django.db import models
from django.contrib.contenttypes.models import ContentType
import inspect, traceback
import settings

# if using the recursion helper this will somewhat arbitrarily
# cut off after this amount of loops.
MAX_ALLOWABLE_STACK_DEPTH = 100

class RecursiveManager(models.Manager):
    """Provides a method to flatten a recursive model (a model which has a ForeignKey field linked back
       to itself), in addition to the usual models.Manager methods. This Manager queries the database
       only once (unlike select_related), and sorts them in-memory. Obivously, this efficiency comes
       at the cost local inefficiency -- O(n^2) -- but that's still preferable to recursively querying
       the database."""
    
    def flatten(self, via_field="parent_id"):
        all_objects = list(self.all())
        
        def pluck(pk=None, depth=0):
            output = []
            
            for object in all_objects:
                if getattr(object, via_field) == pk:
                    output += [object] + pluck(object.pk, depth+1)
                    object.depth = depth
            
            return output
        return pluck()

class CustomManager(models.Manager):
    """Allows you to override the manager's get_query_set method via a 
       configured registered method defined in the settings.  If no such
       method is defined it will resolve to the default behavior of the 
       standard django manager.  The correct format for this from the
       .ini file is:
       [managers]
       modelclass=namespace.method_name
       
       The method should return a QuerySet if you don't want to confuse 
       people.  Also, you have to override the .objects of your model
       with an instance of a CustomManager for this to be picked up.
       """
    
    _model_method_cache = {}
    
    def get_query_set(self):
        method = self._get_method()
        # commented out recursion checker to place the burden on the
        # writer.
        if method: # and not self._recursion_issues():
            # if we find a custom method and there are no recursion
            # issues, go ahead and call it. 
            return method()
        # if not, return the default manager behavior
        return super(CustomManager, self).get_query_set()
        
    def _get_method(self):
        """Get the method bound to this model manager, if it exists"""
        
        # Note: for some reason everything gets lowercased going 
        # Into rapidsms config files, so be consistent with that.
        model_name =self.model.__name__.lower()  
        if model_name in self._model_method_cache:
            return self._model_method_cache[model_name]
        
        # try to get this out from the config
        overridden_methods = getattr(settings, "CUSTOM_MANAGERS", {})
        
        if overridden_methods and model_name in overridden_methods:
            full_method = overridden_methods[model_name]
            split = full_method.split(".")
            method = split.pop()
            module_name = ".".join(split)
            try:
                module = __import__(module_name, 
                                    fromlist=[''])
                method = getattr(module, method, None)
                self._model_method_cache[model_name] = method
                return method
            except ImportError, e:
                # we probably want to note that this threw an error
                # but for now we'll just have this quietly fall back 
                # to the default behavior
                pass
        
        # All the failure cases pass through here
        # Update the cache with a failure so we don't have to do all
        # this logic again
        self._model_method_cache[model_name] = None
        return None
    
    # CZUE: 
    def _recursion_issues(self):
        # This is some useful wackiness. Inspect the call stack
        # and if this is the _second_ or greater call to this 
        # model's .objects, we want to bypass the custom method
        # to avoid infinite loops.  However this is not even
        # close to perfectly safe.  It is meant only to help
        # aid with stack errors.
        # 
        # The better way to do this is to reference the objects
        # as follows:
        #
        # manager = models.Manager()
        # manager.contribute_to_class(Reporter, "Reporter")
        # reporters = manager.all()
        # 
        # This code is pretty terrible and we should actually
        # just let people fix recursion errors on their own
        # rather than promoting potentially bad practice.
        # So removing the call above and leaving this in for
        # legacy sake.  To be removed if not necessary
                
        stack = traceback.extract_stack()
        if len(stack) > MAX_ALLOWABLE_STACK_DEPTH: 
            return True
        model_name =self.model.__name__.lower()  
        objects_call = "%s.objects" % (model_name)
        found = False
        for stack_item in stack:
            # filename, line number, function name, text
            # the third item in the stack list is the line
            # of code that created the call.
            
            method_call = stack_item[3]
            if not method_call:
                # this can be null when inside the interpreter.
                # don't want to break in that case
                continue
            elif objects_call in method_call.lower():
                if found:
                    # Avoid infinite loop, it appeared in the stack
                    # at least twice.  We can be pretty sure its 
                    # coming back to us again and again
                    return True
                else:
                    found = True
        