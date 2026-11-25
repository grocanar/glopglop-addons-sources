from gramps.version import major_version

register(EXPORT,
         id    = 'Export GenewebPlus',
         name  = _('GeneWeb plus (gwplus)'),
         name_accell = _('GeneWeb _plus (gwplus)'),
         description =  _('Export to GeneWeb gwplus format (GeneWeb 7, Geneanet)'),
         version = '0.0.1',
         gramps_target_version = major_version,
         authors = ["Eric Doutreleau"],
         authors_email = ["eric@doutreleau.fr"],
         status = STABLE,
         fname = 'ExportGenewebPlus.py',
         export_function = 'exportData',
         export_options = 'GeneWebPlusOptionBox',
         export_options_title = _('GeneWeb plus export options'),
         extension = "gwplus.gw"
         )
