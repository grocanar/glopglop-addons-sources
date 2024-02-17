#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2023  Eric Doutreleau
# Copyright (C) 2012  Doug Blank <doug.blank@gmail.com>
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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

# $Id: $

"""
External librar for exporting Gedcom to Geneanet
"""
#-------------------------------------------------------------------------
#
# Standard Python Modules
#
#-------------------------------------------------------------------------

from collections import defaultdict
#------------------------------------------------------------------------
#
# GTK modules
#
#------------------------------------------------------------------------

class Extobj():
    
    def __init__(self):
        self.rec_file = defaultdict(str)

    def run(self,filename,database,WikiName):

        self.database = database
        self.WikiName = WikiName


