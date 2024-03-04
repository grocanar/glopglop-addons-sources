# File: Sosa.gpr.py
register(GRAMPLET,
	id='Sosa',
	name=_("Sosa Gramplet"),
	description = _("a gramplet that displays sosa of a person"),
	status = STABLE, # not yet tested with python 3
	version = '1.0.29',
	fname="SosaGramplet.py",
	height = 200,
	gramplet = 'SosaGramplet',
	gramps_target_version = "5.1",
	gramplet_title = _("Sosa Gramplet"),
	help_url = "SosaGramplet",
	)
