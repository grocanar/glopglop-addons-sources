register(IMPORT,
         id    = 'Import Geneanet format gwplus',
         name  = _('Import Geneanet format gwplus'),
         description =  _('Import gwplus from geneanet'),
         version = '0.0.19',
         gramps_target_version = "5.1",
         authors = ["Eric Doutreleau"],
         authors_email = ["eric@doutreleau.fr"],
         status = STABLE,
         fname = 'ImportGenewebPlus.py',
         import_function = 'importData',
         extension = "gwplus"
         )

