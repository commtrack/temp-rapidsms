from StringIO import StringIO
import csv
from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse
from django.db import transaction
from django.db.models import Q

from rapidsms.webui.utils import render_to_response, paginated
from logger.models import *


@login_required
@permission_required("logger.can_view")
def index(req):
    template_name="logger/index_flat.html"
    columns = (("date", "Date"),
               ("connection__identity", "From/To"),
               ("connection__backend", "Backend"),
               ("is_incoming", "Direction"),
               ("text", "Message"))
    sort_column, sort_descending = _get_sort_info(req, default_sort_column="date", 
                                                  default_sort_descending=True)
    sort_desc_string = "-" if sort_descending else ""
    search_string = req.REQUEST.get("q", "")

    query = Message.objects.select_related("connection", "connection__backend"
            ).order_by("%s%s" % (sort_desc_string, sort_column))

    if search_string == "":
        query = query.all()

    else:
        query = query.filter(
           Q(text__icontains=search_string) |
           Q(connection__identity__icontains=search_string))

    messages = paginated(req, query)
    return render_to_response(req, template_name, {"columns": columns,
                                                   "messages": messages,
                                                   "sort_column": sort_column,
                                                   "sort_descending": sort_descending,
                                                   "search_string": search_string})

@login_required
@permission_required("logger.can_view")
def csv_export(req):
    headings = ["Id", "Date", "From/To", "Backend", "Direction", "Message"]
    search_string = req.REQUEST.get("q", "")
    messages = Message.objects.order_by("-date")
    
    if search_string:
        messages = messages.filter(
           Q(text__icontains=search_string) |
           Q(connection__identity__icontains=search_string))
        filename = "sms_export_%s_%s.csv" % (search_string, 
                                             str(datetime.now().date()))
    else:
        filename = "sms_export_%s.csv" % (str(datetime.now().date()))
    
    output = StringIO()
    w = csv.writer(output)
    w.writerow(headings)
    for message in messages:
        direction = "From Phone" if message.is_incoming else "To Phone"
        w.writerow([message.id, message.date, message.connection.identity, 
                    message.connection.backend, direction, message.text])
                    
    
    output.seek(0)
    response = HttpResponse(output.read(),
                        mimetype='application/ms-excel')
    response["content-disposition"] = "attachment; filename=%s" % filename
    return response    
    
    
@login_required
@permission_required("logger.can_view")
def migrate(req):
    
    def get(req):
        template_name="logger/migrate.html"
        incoming = IncomingMessage.objects.all()
        outgoing = OutgoingMessage.objects.all()
        return render_to_response(req, template_name, {"incoming": incoming,
                                                       "outgoing": outgoing})
    
    
    @transaction.commit_manually
    def post(req):
        # the UI for this leaves something to be desired, but it's pretty
        # much a one time function
        if "confirmed" in req.POST and req.POST["confirmed"]=="True":
            try:
                for incoming in IncomingMessage.objects.all():
                    msg = Message.from_incoming(incoming)
                    msg.save()
                for outgoing in OutgoingMessage.objects.all():
                    msg = Message.from_outgoing(outgoing)
                    msg.save()
                transaction.commit()
                return HttpResponse("Success!")
            except Exception, e:
                transaction.rollback()
                return HttpResponse("Error! %s" % e)
        else:
            return HttpResponse("Canceled!")

    # invoke the correct function...
    # this should be abstracted away
    if   req.method == "GET":  return get(req)
    elif req.method == "POST": return post(req)
    

def _get_sort_info(request, default_sort_column, default_sort_descending):
    sort_column = default_sort_column
    sort_descending = default_sort_descending
    if "sort_column" in request.GET:
        sort_column = request.GET["sort_column"]
    if "sort_descending" in request.GET:
        if request.GET["sort_descending"].startswith("f"):
            sort_descending = False
        else:
            sort_descending = True
    return (sort_column, sort_descending)

def _old_index(req):
    # Reference to the old view of the old tables.
    # Ordinarily I would delete this, but this log is still 
    # around in several deployments
    template_name="logger/index.html"
    incoming = IncomingMessage.objects.order_by('received')
    outgoing = OutgoingMessage.objects.order_by('sent')
    all = []
    [ all.append(msg) for msg in incoming ]
    [ all.append(msg) for msg in outgoing]
    # sort by date, descending
    all.sort(lambda x, y: cmp(y.date, x.date))
    return render_to_response(req, template_name, { "messages": all })
