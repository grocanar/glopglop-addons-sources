# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2007-2009  Douglas S. Blank <doug.blank@gmail.com>
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

#------------------------------------------------------------------------
#
# Python modules
#
#------------------------------------------------------------------------
import posixpath

#------------------------------------------------------------------------
#
# GRAMPS modules
#
#------------------------------------------------------------------------
from gramps.gen.plug import Gramplet
from gramps.gen.const import GRAMPS_LOCALE as glocale
_ = glocale.translation.sgettext
from gramps.gen.utils.file import media_path_full
from gramps.gen.datehandler import get_date
from gramps.gen.lib import Person
from collections import defaultdict
from gramps.gen.relationship import get_relationship_calculator

#------------------------------------------------------------------------
#
# Constants
#
#------------------------------------------------------------------------

_YIELD_INTERVAL = 200

#------------------------------------------------------------------------
#
# StatsGramplet class
#
#------------------------------------------------------------------------
class SosaGramplet(Gramplet):
    def init(self):
        self.set_text(_("Sosa"))

#    def post_init(self):
#        self.disconnect("active-changed")

    def db_changed(self):
        self.dbstate.db.connect('person-add', self.update)
        self.dbstate.db.connect('person-edit', self.update)
        self.dbstate.db.connect('person-delete', self.update)
        self.dbstate.db.connect('person-rebuild', self.update)

    def main(self):
        self.set_text(_("Sosa..."))
        self.rel_class = get_relationship_calculator(glocale)
        database = self.dbstate.db
        home_person = database.get_default_person()
        if not home_person:
            print("GROSS PROBLEM")
            result = "Not Related"
        active_handle = self.get_active('Person')
        if active_handle:
            active = database.get_person_from_handle(active_handle)
            common, self.msg_list = self.rel_class.get_relationship_distance_new(
                    database, active, home_person,
                    all_families=True,
                    all_dist=True,
                    only_birth=False)
            if (not common or common[0][0]== -1):
                result = "Not Related"
            else:
                result=str(common[0][4])
        else:
            result = "Not Related"


        self.append_text("\nSosa %s\n" % result)
