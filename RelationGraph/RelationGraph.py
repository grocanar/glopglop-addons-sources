#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2017       Eric Doutreleau²
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
#
"""
Create relation graph with home person
"""
#-------------------------------------------------
#
# python modules
#
#-------------------------------------------------
import time
import os

#------------------------------------------------------------------------
#
# Internationalisation
#
#------------------------------------------------------------------------
from gramps.gen.const import GRAMPS_LOCALE as glocale
try:
    trans = glocale.get_addon_translator(__file__)
except ValueError:
    trans = glocale.translation
_ = trans.gettext
ngettext = trans.ngettext

#-------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------
from gramps.gui.utils import ProgressMeter
import igraph as ig


def run(database, document, person):
    """
    Output a graph relation with home person for active person
    """

    maxdepth=30
    maxanc=maxdepth + 5
    layout_style="sugiyama"
    dotfile= "example.dot"
    g = ig.Graph(directed=True)
    progress = ProgressMeter(_('Convert People'), can_cancel=False)
    length = database.get_number_of_people()
    progress.set_pass(_('Convert People'),length)
    HAND = {}
    ind=0
    start_time = time.perf_counter()
    home_person = database.get_default_person()
    for person_handle in database.get_person_handles():
        progress.step()
        pers = database.get_person_from_handle(person_handle)
        full_name = pers.get_primary_name().get_regular_name()
        HAND[person_handle]=ind
        g.add_vertex(handle=person_handle, name=full_name)
        ind = ind + 1
    progress.close()
    RES=[]
    person_time = time.perf_counter()
    print(" PERSON TIME ",person_time - start_time)
    length = database.get_number_of_families()
    progress = ProgressMeter(_('Convert Families'))
    progress.set_pass(_('Convert Families'),length)
    for family_handle in database.get_family_handles():
        progress.step()
        family = database.get_family_from_handle(family_handle)
        father_handle = family.get_father_handle()
        mother_handle = family.get_mother_handle()
        children_handles = family.get_child_ref_list()
        if father_handle:
            for child_ref in children_handles:
                child_handle = child_ref.ref
                RES.append((HAND[father_handle], HAND[child_handle]))
        if mother_handle:
            for child_ref in children_handles:
                child_handle = child_ref.ref
                RES.append((HAND[mother_handle], HAND[child_handle]))
    progress.close()
    g.add_edges(RES)
    family_time = time.perf_counter()
    print(" FAMILY TIME ",family_time - start_time)
# End of initialisation od graph       
    node=g.vs.find(handle=home_person.handle)
    node2=g.vs.find(handle=person.handle)
    anct1=g.neighborhood(vertices=node, order=maxanc,mode='in')
    anc1=g.neighborhood(vertices=node, order=maxdepth, mode='in')
    anct2=g.neighborhood(vertices=node2, order=maxanc, mode='in')
    anc2=g.neighborhood(vertices=node2, order=maxdepth, mode='in')
    search=[node.index,node2.index]
    union = set(anc1 + anc2 + search)
    inter = set(anc1) & set(anc2)
    anconlyg1 = union-set(anc2)
    anconlyg2 = union-set(anc1)
    extract_time = time.perf_counter()
    print(" EXTRACT TIME ",extract_time )
    res=[]
    for elem in inter:
        mrca=0
        g1only=0
        g2only=0
        name=g.vs[elem]["name"]
        for child in g.neighbors(g.vs[elem], mode='out'):
            if child in anct1 and child not in anct2:
                childname=g.vs[child]["name"]
                g1only=1
            if child in anct2 and child not in anct1:
                childname=g.vs[child]["name"]
                g2only=1
        if g1only and g2only:
             res.append(elem)
    RES=[]
    print("liste des MRCA")
    for elem in res:
        cible=g.vs[elem]
        print(g.vs[elem]["name"])
        chemins1 = g.get_all_simple_paths(node, cutoff=maxdepth , to=cible,mode='in')
        for chem in chemins1:
            RES.extend(chem)
        chemins2 = g.get_all_simple_paths(node2, cutoff=maxdepth , to=cible,mode='in')
        for chem in chemins2:
            RES.extend(chem)
    rest=set(RES)
    for elem in rest:
        hdl=g.vs[elem]["handle"]
        person = database.get_person_from_handle(hdl)
        if person.get_privacy():
            g.vs[elem]["name"] = "Privé"
        g.vs[elem]["style"]='filled'
        if elem in anconlyg1:
            g.vs[elem]["color"]="blue"
        elif elem in anconlyg2:
            g.vs[elem]["color"]="red"
        else:
            g.vs[elem]["color"]="green"
    gresult=g.induced_subgraph(rest,"auto")
    total_width = 4000
    total_height = 4000
    layout = gresult.layout(layout_style)
    gresult.vs["label"] = gresult.vs["name"]
    gresult.write_dot(dotfile)
    fin_time = time.perf_counter()
    print(" FIN TIME ",fin_time - start_time)







