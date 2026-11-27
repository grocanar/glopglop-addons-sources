#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2026  Eric Doutreleau
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

"""
Options of the GeneWeb plus export, shown as a "GeneWeb plus" page of the
Gramps preferences.

Gramps has no way for an addon to add a page to its preferences, so the
page is added by wrapping ConfigureDialog.__init__ when the dialog being
built is the Gramps preferences.
"""

from gramps.gen.const import GRAMPS_LOCALE as glocale
from gramps.gen.config import config as configman

_ = glocale.get_addon_translator(__file__).gettext

CONFIG_NAME = "ExportGenewebPlus"
INCLUDE_URLS = "options.include_urls"
INCLUDE_REPOSITORIES = "options.include_repositories"
BEAUTIFY = "options.beautify"
COMPRESS = "options.compress"
INCLUDE_WITNESSES = "options.include_witnesses"
GENEANET_PLACES = "options.geneanet_places"
EXCLUDE_PRIVATE = "options.exclude_private"
PLACE_AT_EVENT = "options.place_at_event"


def get_config():
    """
    The configuration of the export, kept in ExportGenewebPlus.ini in the
    Gramps plugins directory, shared by the preferences page and the export.
    """
    if configman.has_manager(CONFIG_NAME):
        return configman.get_manager(CONFIG_NAME)
    config = configman.register_manager(CONFIG_NAME)
    config.register(INCLUDE_URLS, True)
    config.register(INCLUDE_REPOSITORIES, True)
    config.register(BEAUTIFY, True)
    config.register(COMPRESS, False)
    config.register(INCLUDE_WITNESSES, True)
    config.register(GENEANET_PLACES, False)
    config.register(EXCLUDE_PRIVATE, True)
    config.register(PLACE_AT_EVENT, False)
    config.load()
    return config


def add_genewebplus_panel(configdialog):
    """The "GeneWeb plus" page of the Gramps preferences."""
    config = get_config()
    grid = configdialog.create_grid()

    grid.set_column_spacing(24)

    def save(_obj):
        config.save()

    def section(title, row, col):
        label = configdialog.add_text(grid, title, row, line_wrap=True,
                                      bold=True, start=col, stop=col + 1)
        if row:
            label.set_margin_top(10)

    def option(label, row, col, key):
        check = configdialog.add_checkbox(grid, label, row, key, start=col,
                                          stop=col + 1, config=config,
                                          extra_callback=save)
        check.get_child().set_line_wrap(True)
        check.get_child().set_max_width_chars(40)
        check.set_hexpand(True)
        return check

    # left column
    section(_("General"), 0, 0)
    option(_("Compress the exported file (zip)"), 1, 0, COMPRESS)
    option(_("Exclude private data"), 2, 0, EXCLUDE_PRIVATE)
    section(_("Sources"), 3, 0)
    option(_("Include URLs in sources"), 4, 0, INCLUDE_URLS)
    option(_("Include repository information in sources"), 5, 0,
           INCLUDE_REPOSITORIES)
    option(_("Beautify sources (one line per item, values in bold)"), 6, 0,
           BEAUTIFY)

    # right column
    section(_("Events"), 0, 1)
    option(_("Include witnesses"), 1, 1, INCLUDE_WITNESSES)
    section(_("Places"), 3, 1)
    geneanet = option(_("Geneanet place format ([ hamlet ] - Town, postal "
                        "code, County, State, Country)"), 4, 1,
                      GENEANET_PLACES)
    at_event = option(_("Add the name of the place at the date of the event "
                        "as a note"), 5, 1, PLACE_AT_EVENT)
    at_event.set_margin_start(20)

    # the places are written with their current name only in the Geneanet
    # format: the name at the date of the event has no use otherwise
    def update_sensitive(_obj=None):
        at_event.set_sensitive(geneanet.get_active())

    geneanet.connect("toggled", update_sensitive)
    update_sensitive()
    return _("GeneWeb plus"), grid


def load_on_reg(dbstate, uistate, plugin):
    """Add the page to the Gramps preferences (GUI only)."""
    if uistate is None:
        return []
    from gramps.gui.configure import ConfigureDialog, GrampsPreferences

    original_init = ConfigureDialog.__init__
    if getattr(original_init, "genewebplus", False):
        return []  # plugins reloaded: already done

    def init(self, uistate, dbstate, configure_page_funcs, configobj,
             *args, **kwargs):
        if (configobj is GrampsPreferences
                and isinstance(configure_page_funcs, (list, tuple))):
            configure_page_funcs = (tuple(configure_page_funcs)
                                    + (add_genewebplus_panel,))
        original_init(self, uistate, dbstate, configure_page_funcs, configobj,
                      *args, **kwargs)

    init.genewebplus = True
    ConfigureDialog.__init__ = init
    return []
