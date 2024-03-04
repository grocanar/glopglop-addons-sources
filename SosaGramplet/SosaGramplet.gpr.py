# File: Sosa.gpr.py
register(GRAMPLET,
	id='Sosa',
	name=_("Sosa Gramplet"),
	description = _("a gramplet that displays sosa of a person"),
	status = UNSTABLE, # not yet tested with python 3
	version = '1.0.31',
	fname="SosaGramplet.py",
    authors = ["Eric Doutreleau"],
    authors_email = ["eric@doutreleau.fr"],
	height = 200,
	gramplet = 'SosaGramplet',
	gramps_target_version = "5.2",
	gramplet_title = _("Sosa Gramplet"),
	help_url = "SosaGramplet",
	)
