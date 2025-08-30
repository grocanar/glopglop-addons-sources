# ------------------------------------------------------------------------
#
# Register the report
#
# ------------------------------------------------------------------------

register(
    QUICKREPORT,
    id="RelationGraph",
    name=_("RelationGraph"),
    description=_("Create a relation graph with home person"),
    version = '0.0.1',
    gramps_target_version="6.0",
    status=STABLE,
    fname="RelationGraph.py",
    authors=["Eric Doutreleau"],
    category=CATEGORY_QR_PERSON,
    runfunc="run",
)
