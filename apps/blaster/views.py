from datetime import datetime
import httplib, urllib, urllib2
from threading import Thread
import re

from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.db import transaction

from blaster.models import *
from reporters.models import Reporter
from locations.models import LocationType, Location
from schools.models import School, SchoolGroup, SCHOOL_GROUP_TYPES

from rapidsms.webui.utils import render_to_response, paginated

def list(req, template_name="blaster/index.html"):
    all_blasts = MessageBlast.objects.order_by("-date")
    return render_to_response(req, template_name, {"blasts": all_blasts})

def single_blast(req, id, template_name="blaster/single.html"):
    blast = MessageBlast.objects.get(id=id)
    return render_to_response(req, template_name, {"blast": blast})
    
def new(req, template_name="blaster/new.html"):
    
    def get(req, template_name="blaster/new.html", errors=None):
        filter_params = get_location_filter_params(req, "location__")
        messages = BlastableMessage.objects.all()
        # TODO: genericize this out to only depend on reporters

        # filter out those not matching the type.
        if "type" in req.GET:
            
            filter_type = req.GET["type"]
        else:
            filter_type = None
        
        reporters = Reporter.objects.filter(**filter_params)
        # loop through and set some attributes on the reporters so we 
        # can display school specific information in the UI
        # TODO: this is horribly inefficient and could be optimized
        
        final_list = []
        #for reporter in reporters:
        for reporter in []:
            if reporter.location:
                try:
                    school = School.objects.get(id=reporter.location.id)
                    reporter.school = school
                    if filter_type:
                        try:
                            group = school.groups.get(type=filter_type)
                            if reporter in group.reporters.all():
                                reporter.school_role = group.member_title
                            else:
                                # they aren't part of the group we're filtering
                                # on so don't add them
                                continue
                        except SchoolGroup.DoesNotExist:
                            # if the school doesn't have a group then
                            # don't add them
                            continue
                    else:
                        # see if they belong to any known groups, and if so
                        # set those objects in the UI
                        groups = reporter.groups.all()
                        school_groups = []
                        for group in groups:
                            try:
                                school_groups.append(SchoolGroup.objects.get(id=group.id))
                            except SchoolGroup.DoesNotExist:
                                # wasn't a school group, just ignore it
                                pass
                        reporter.school_groups = school_groups
                        # list their roles
                        reporter.school_role = ",".join([grp.member_title() for grp in school_groups])
                except School.DoesNotExist:
                    reporter.school=None
            final_list.append(reporter)
        # sort by location, then role
        final_list.sort(lambda x, y: cmp("%s-%s" % (x.location,x.school_role),
                                         "%s-%s" % (y.location,y.school_role)))


        # wow! what a complete contradiction of the entire point of the
        # locations app. no matter, it's just for the demo.
        r = LocationType.objects.get(name="Region")
        regions = r.locations.all().order_by("name")

        d = LocationType.objects.get(name="District")
        districts = d.locations.all().order_by("parent__id", "name")

        s = LocationType.objects.get(name="School")
        schools = s.locations.all().order_by("parent__id", "parent__parent__id", "name")

        def _with_role(reporter):
            """
            Add a 'school_role' attribute (a comma-separated list of the
            'member_title' method of each linked SchoolGroup object) to
            *reporter* and return it.

            This is horribly, horribly inefficient, but there isn't a
            more direct way of finding the SchoolGroup names of each
            reporter, since every single School has its own roles (??).
            """

            groups = SchoolGroup.objects.filter(reporters=reporter)
            roles = ", ".join([g.member_title() for g in groups])
            roles = re.sub(r"\s+(Member|Leader)", "", roles)

            reporter.school_role = roles
            return reporter

        #people = [
        #    _with_role(person)
        #    for person in Reporter.objects.all()]

        all_people = Reporter.objects.all()[0:100]
        people = paginated(req, all_people, per_page=10, wrapper=_with_role)

        roles = [
            (key, vals[1])
            for key, vals in SCHOOL_GROUP_TYPES.items()]

        return render_to_response(req, template_name, {"messages": messages,
                                                       "reporters": final_list,
                                                       "errors": errors,

                                                       "regions": regions,
                                                       "districts": districts,
                                                       "schools": schools,
                                                       "people": people,
                                                       "roles": roles
                                                       } )    
    
    @transaction.commit_manually
    def post(req):
        try:
            message = req.POST["message"]
            errors = []
            if not message:
                errors.append("You must select a message!")
            elif message == "new":
                if not req.POST["new_question"]:
                    errors.append("You must fill in the new question text!")
                else:
                    question = BlastableMessage.objects.create(text=req.POST["new_question"])
                    question.save()
            else:
                question = BlastableMessage.objects.get(id=int(message))
    
            if "select_reporter" not in req.POST or not req.POST["select_reporter"]:
                errors.append("You must select at least one person to send to!")
            if errors:
                transaction.rollback()
                return get(req, template_name, errors="<br>".join(errors))
                
            # no errors
            reporter_ids = req.POST.getlist("select_reporter")
            now = datetime.now()
            blast = MessageBlast.objects.create(message=question,date=now)
            for id in reporter_ids:
                reporter = Reporter.objects.get(id=id)
                instance = BlastedMessage.objects.create(blast=blast, reporter=reporter)
                thread = Thread(target=_send_message,args=(req, reporter.id, question.text))
                thread.start()
                                    
            transaction.commit()
            return single_blast(req, blast.id)
        except Exception, e:
            transaction.rollback()
            raise e
        
    # invoke the correct function...
    # this should be abstracted away
    if   req.method == "GET":  return get(req, template_name)
    elif req.method == "POST": return post(req)
    
def _send_message(req, id, text):
    # also send the message, by hitting the ajax url of the messaging app
    data = {"uid":  id,
            "text": text
            }
    encoded = urllib.urlencode(data)
    headers = {"Content-type": "application/x-www-form-urlencoded",
               "Accept": "text/plain"}
    conn = httplib.HTTPConnection(req.META["HTTP_HOST"])
    conn.request("POST", "/ajax/messaging/send_message", encoded, headers)
    response = conn.getresponse()
    
