from __future__ import absolute_import

from xml.etree import ElementTree
from xml.etree.ElementTree import Element, SubElement

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rapidsms.webui.utils import render_to_response

from schools.models import *
from schools.utils import get_location_filter_params
from blaster.models import *

def dashboard(req, template_name="schools/dashboard.html"):
    context = {}
    recent_blasts = MessageBlast.objects.order_by("-date")[:5]
    context["recent_blasts"] = recent_blasts
    if recent_blasts:
        last_blast = recent_blasts[0]
        context["last_blast"] = last_blast
        context["last_blast_recipients"] = last_blast.recipients.all()[:5]
    # set the problem and feature lists to match up with the xml, but 
    # only include a max of 5
    problems = []
    highlights = []
    for school in School.objects.all():
        if school.problems:
            problems.append("%s at %s" %(school.problems[0], school.name))
        elif school.highlights:
            highlights.append("%s at %s" %(school.highlights[0], school.name))
    context["problems"] = problems[:5]
    context["highlights"] = highlights[:5]
    return render_to_response(req, template_name, context) 


def schools(req, template_name="schools/school_list.html"):
    regions = Location.objects.filter(type__name="Region")
    districts = None
    region = None
    district = None
    
    filter_params = get_location_filter_params(req)
    print filter_params
    schools = School.objects.filter(**filter_params)
    
    
    if "region" in req.GET:
        region = Location.objects.get(id=req.GET["region"])
    elif "district" in req.GET:
        district = Location.objects.get(id=req.GET["district"])
        region = district.parent
    if region:
        districts = region.children.filter(type__name="District")
    else:
        schools = School.objects.all()
    return render_to_response(req, template_name, {"regions": regions,
                                                   "districts": districts,
                                                   "selected_region" : region,
                                                   "selected_district" : district,
                                                   "schools": schools })


def map(req, template_name="schools/school_map.html"):
    """Display a map with school data on it"""
    return render_to_response(req, template_name, {})

def xml(req):
    """Get some basic xml data for populating the map."""
    all_schools = School.objects.all()
    root = Element("root")
    for school in all_schools:
        # for now automatically set the problems and highlights as custom
        # attributes.  If a school has both highlights and problems the 
        # problems win
        if school.problems:
            # TODO: should we show more than one?
            school.custom = 0
            school.custom_text = school.problems[0]
        elif school.highlights:
            # TODO: should we show more than one?
            school.custom = 100
            school.custom_text = school.highlights[0]
        school_elem = school.to_element()
        root.append(school_elem)
    return HttpResponse(ElementTree.tostring(root), mimetype="text/xml")

def single_school(req, id, template_name="schools/single_school.html"):
    """View of a single school."""
    school = get_object_or_404(School, id=id)
    xml_location = "/schools/%s/xml" % id
    return render_to_response(req, template_name, {"school": school,
                                                   "xml_location": xml_location })

def single_school_xml(req, id):
    """XML file for a single school, consumed by the single school map"""
    school = get_object_or_404(School, id=id)
    root = Element("root")
    root.append(school.to_element())
    return HttpResponse(ElementTree.tostring(root), mimetype="text/xml")

def message(req, id, template_name="schools/message.html"):
    head = get_object_or_404(Reporter, id=id)
    return render_to_response(req, template_name, { "reporter": head })

def headmasters(req, template_name="schools/headmasters.html"):
    # TODO: fix this to be only headmasters again.
    # currently this view is not used.
    all = Reporter.objects.all()
    return render_to_response(req, template_name, { "headmasters": all})