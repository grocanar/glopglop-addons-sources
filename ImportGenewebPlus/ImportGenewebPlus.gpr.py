from gramps.version import major_version

register(IMPORT,
         id    = 'Import Geneanet format gwplus',
         name  = _('Import Geneanet format gwplus'),
         description =  _('Import gwplus from geneanet'),
         version = '0.0.20',
         gramps_target_version = major_version,
         authors = ["Eric Doutreleau"],
         authors_email = ["eric@doutreleau.fr"],
         status = STABLE,
         fname = 'ImportGenewebPlus.py',
         import_function = 'importData',
         extension = "gwplus"
         )

