
def get_location_filter_params(req, prefix=""):
    """Get the various filters used by the blaster and school views from
       the request object.  These can be: region, district, and school.  
       The optional prefix allows you to tell the query how to prefix
       the parameters."""
    to_return = {}
    for param in req.GET:
        # these are hard-coded to assume the location is a school
        # it's parent is a district, and that district's parent is
        # a region.
        if param == "school":
            to_return["%sid" % prefix] = req.GET[param]
        if param == "district":
            to_return["%sparent__id" % prefix] = req.GET[param]
        if param == "region":
            to_return["%sparent__parent__id" % prefix] = req.GET[param]
    return to_return
