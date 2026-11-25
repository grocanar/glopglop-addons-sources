#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2004  Martin Hawlisch
# Copyright (C) 2004-2006, 2008 Donald N. Allingham
# Copyright (C) 2008  Brian G. Matherly
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
# You should have received a copy of the GNU General Public License along
# with this program; if not, see <https://www.gnu.org/licenses/>.
#

"Export to GeneWeb gwplus format."

# -------------------------------------------------------------------------
#
# Standard Python Modules
#
# -------------------------------------------------------------------------
import re
import unicodedata
from collections import abc

# ------------------------------------------------------------------------
#
# Set up logging
#
# ------------------------------------------------------------------------
import logging

LOG = logging.getLogger(".ExportGenewebPlus")

# -------------------------------------------------------------------------
#
# Gramps modules
#
# -------------------------------------------------------------------------
from gramps.gen.const import GRAMPS_LOCALE as glocale

_ = glocale.get_addon_translator(__file__).gettext
from gramps.gen.config import config as configman
from gramps.gen.lib import (AttributeType, ChildRefType, Date, EventRoleType,
                            EventType, FamilyRelType, Person)
from gramps.gui.plug.export import WriterOptionBox
from gramps.gen.utils.alive import probably_alive
from gramps.gen.utils.string import conf_strings
from gramps.gen.datehandler import displayer as _dd
from gramps.gen.display.place import displayer as _pd

# -------------------------------------------------------------------------
#
# Mapping between Gramps and GeneWeb
# For the file format see bin/gwu/gwuLib.ml and bin/gwc/gwcomp.ml
# in the GeneWeb sources.
#
# -------------------------------------------------------------------------
PEVENTS_MAP = {
    EventType.BIRTH: "#birt",
    EventType.BAPTISM: "#bapt",
    EventType.CHRISTEN: "#bapt",
    EventType.ADULT_CHRISTEN: "#bapt",
    EventType.DEATH: "#deat",
    EventType.BURIAL: "#buri",
    EventType.CREMATION: "#crem",
    EventType.BAR_MITZVAH: "#barm",
    EventType.BAS_MITZVAH: "#basm",
    EventType.BLESS: "#bles",
    EventType.CENSUS: "#cens",
    EventType.CONFIRMATION: "#conf",
    EventType.DEGREE: "#degr",
    EventType.EDUCATION: "#educ",
    EventType.ELECTED: "#elec",
    EventType.EMIGRATION: "#emig",
    EventType.FIRST_COMMUN: "#fcom",
    EventType.GRADUATION: "#grad",
    EventType.IMMIGRATION: "#immi",
    EventType.MILITARY_SERV: "#mser",
    EventType.NATURALIZATION: "#natu",
    EventType.OCCUPATION: "#occu",
    EventType.ORDINATION: "#ordn",
    EventType.PROPERTY: "#prop",
    EventType.RESIDENCE: "#resi",
    EventType.RETIREMENT: "#reti",
    EventType.WILL: "#will",
}

# Custom event names created by ImportGenewebPlus
PEVENTS_CUSTOM_MAP = {
    "Accomplishment": "#acco",
    "Acquisition": "#acqu",
    "Adhesion": "#adhe",
    "Award": "#awar",
    "Change Name": "#chgn",
    "Circumcision": "#circ",
    "Military Demobilisation": "#demm",
    "Dotation": "#endl",
    "Excommunication": "#exco",
    "LDS Family Link": "#flkl",
    "Funeral": "#fune",
    "Hospitalisation": "#hosp",
    "Illness": "#illn",
    "List Passenger": "#lpas",
    "Military Distinction": "#mdis",
    "Militaty Mobilisation": "#mobm",
    "Military Mobilisation": "#mobm",
    "Military Promotion": "#mpro",
    "LDS Seal to child": "#slgc",
    "Sold property": "#vteb",
}

FEVENTS_MAP = {
    EventType.MARRIAGE: "#marr",
    EventType.ENGAGEMENT: "#enga",
    EventType.DIVORCE: "#div",
    EventType.ANNULMENT: "#anul",
    EventType.MARR_BANNS: "#marb",
    EventType.MARR_CONTR: "#marc",
    EventType.MARR_LIC: "#marl",
    EventType.RESIDENCE: "#resi",
}

FEVENTS_CUSTOM_MAP = {
    "No mention": "#nmen",
    "Separated": "#sep",
    "PACS": "#pacs",
}

# Gramps event role -> GeneWeb witness kind ("" = plain witness)
WITNESS_ROLES = {
    EventRoleType.WITNESS: "",
    EventRoleType.GODPARENT: "#godp",
    EventRoleType.CLERGY: "#reli",
    EventRoleType.CELEBRANT: "#reli",
    EventRoleType.OFFICIATOR: "#offi",
    EventRoleType.INFORMANT: "#info",
    EventRoleType.AIDE: "#atte",
    EventRoleType.FRIEND: "#othe",
    EventRoleType.NEIGHBOR: "#othe",
}

GODPARENT_NAMES = ("godparent", "godfather", "godmother", "parrain",
                   "marraine")

# Gramps child reference type -> GeneWeb relation type
CHILDREF_RELATIONS = {
    ChildRefType.ADOPTED: "adop",
    ChildRefType.FOSTER: "fost",
    ChildRefType.SPONSORED: "godp",
}

# Death event description -> GeneWeb death reason prefix
DEATH_REASONS = {
    "killed": "k", "tué": "k",
    "murdered": "m", "assassiné": "m",
    "executed": "e", "exécuté": "e",
    "disappeared": "s", "disparu": "s",
}

CALENDARS = {
    Date.CAL_GREGORIAN: "",
    Date.CAL_JULIAN: "J",
    Date.CAL_FRENCH: "F",
    Date.CAL_HEBREW: "H",
}

DATE_MODIFIERS = {
    Date.MOD_ABOUT: "~",
    Date.MOD_BEFORE: "<",
    Date.MOD_AFTER: ">",
    Date.MOD_TO: "<",
    Date.MOD_FROM: ">",
}


def _starting_char(s, no_num):
    """Same test as starting_char in gwuLib.ml (done on the UTF-8 byte)."""
    c = s[0]
    if c.isascii():
        if c.isalpha():
            return True
        if c.isdigit():
            return not no_num
        return s == "?"
    byte = c.encode("utf-8")[0]
    return 0xC0 <= byte <= 0xDD or 0xE0 <= byte <= 0xFD


def gw_string(s, no_num=False, no_colon=False, empty="_"):
    """Encode a string as a single GeneWeb token (gen_correct_string)."""
    s = " ".join((s or "").split())
    if not s:
        return empty
    out = [] if _starting_char(s, no_num) else ["_"]
    for c in s:
        if c == " ":
            out.append("_")
        elif c in "_\\":
            out.append("\\" + c)
        elif c == ":" and no_colon:
            out.append("\\\\:")
        elif ord(c) < 32:
            out.append("_")
        else:
            out.append(c)
    return "".join(out)


URL_RE = re.compile(r"(?:https?://|www\.)[^\s<>\"']+", re.I)


def linkify(text):
    """Turn the URLs of a text into HTML links, so that they can be
    clicked in GeneWeb. Texts already containing links are kept."""
    if "<a " in text.lower():
        return text

    def link(match):
        url = match.group(0).rstrip(".,;)")
        rest = match.group(0)[len(url):]
        href = url if "://" in url else "http://" + url
        return '<a href="%s">%s</a>%s' % (href, url, rest)

    return URL_RE.sub(link, text)


def name_key(s):
    """Coarser than GeneWeb's Name.lower, so that two persons GeneWeb
    would consider identical always get distinct occurrence numbers."""
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if c.isalnum())


# The choices of the export options are kept for the next export in
# ExportGenewebPlus.ini, in the Gramps plugins directory.
CONFIG = configman.register_manager("ExportGenewebPlus")
CONFIG.register("options.include_urls", True)
CONFIG.register("options.include_repositories", True)
CONFIG.load()


class GeneWebPlusOptionBox(WriterOptionBox):
    """The standard export options, plus what to put in the sources."""

    def __init__(self, person, dbstate, uistate, track=[], window=None):
        WriterOptionBox.__init__(
            self, person, dbstate, uistate, track=track, window=window
        )
        self.include_urls = CONFIG.get("options.include_urls")
        self.include_repositories = CONFIG.get("options.include_repositories")
        self.include_urls_check = None
        self.include_repositories_check = None

    def get_option_box(self):
        from gi.repository import Gtk

        option_box = WriterOptionBox.get_option_box(self)

        self.include_urls_check = Gtk.CheckButton(
            label=_("Include URLs in sources"))
        self.include_repositories_check = Gtk.CheckButton(
            label=_("Include repository information in sources"))
        self.include_urls_check.set_active(self.include_urls)
        self.include_repositories_check.set_active(self.include_repositories)
        option_box.pack_start(self.include_urls_check, False, True, 0)
        option_box.pack_start(self.include_repositories_check, False, True, 0)
        return option_box

    def parse_options(self):
        WriterOptionBox.parse_options(self)
        if self.include_urls_check:
            self.include_urls = self.include_urls_check.get_active()
            self.include_repositories = \
                self.include_repositories_check.get_active()
            CONFIG.set("options.include_urls", self.include_urls)
            CONFIG.set("options.include_repositories",
                       self.include_repositories)
            CONFIG.save()


class GeneWebPlusWriter:
    def __init__(self, database, filename, user, option_box=None):
        self.db = database
        self.filename = filename
        self.user = user
        self.option_box = option_box
        if isinstance(self.user.callback, abc.Callable):  # is really callable
            self.update = self.update_real
        else:
            self.update = self.update_empty

        if option_box:
            self.option_box.parse_options()
            self.db = option_box.get_filtered_database(self.db)
        # also used with the plain WriterOptionBox (command line)
        self.include_urls = getattr(option_box, "include_urls", True)
        self.include_repositories = getattr(option_box,
                                            "include_repositories", True)

        self.names = {}          # person handle -> (surname, firstname)
        self.occ = {}            # person handle -> occurrence number
        self.main_family = {}    # person handle -> family handle as child
        self.defined = set()     # persons whose data has been written
        self.witnesses = {}      # event handle -> [(person handle, kind)]
        self.relations = {}      # person handle -> [relation lines]
        self.source_texts = {}   # source handle -> text
        self.citation_texts = {} # citation handle -> text

    def update_empty(self):
        pass

    def update_real(self):
        self.count += 1
        newval = int(100 * self.count / self.total)
        if newval != self.oldval:
            self.user.callback(newval)
            self.oldval = newval

    def writeln(self, text=""):
        self.g.write(text + "\n")

    # ---------------------------------------------------------------------
    # Export
    # ---------------------------------------------------------------------
    def export_data(self):
        try:
            with open(self.filename, "w", encoding="utf-8",
                      newline="\n") as self.g:
                self.prepare()
                families = sorted(self.families.values(),
                                  key=lambda f: f.get_gramps_id())
                isolated = [p for p in self.persons if self.is_isolated(p)]

                self.count = 0
                self.oldval = 0
                self.total = max(len(families) + len(isolated), 1)

                self.writeln("encoding: utf-8")
                self.writeln("gwplus")
                self.writeln()
                # Isolated persons first, so that they are defined before
                # being referenced as witnesses.
                for person in isolated:
                    self.update()
                    self.write_isolated(person)
                for family in families:
                    self.update()
                    self.write_family(family)
                self.write_relations()
                return True
        except IOError as msg:
            msg2 = _("Could not create %s") % self.filename
            self.user.notify_error(msg2, str(msg))
            return False

    def prepare(self):
        """Compute names, occurrence numbers, main parent families,
        witnesses and relations before writing anything."""
        # Each person and family is read only once: through the living
        # people filter (LivingProxyDb), every read computes again whether
        # the person is alive, which is very slow on a large tree.
        self.persons = sorted(self.db.iter_people(),
                              key=lambda p: p.get_gramps_id())
        self.people = {p.get_handle(): p for p in self.persons}
        self.families = {f.get_handle(): f for f in self.db.iter_families()}
        used = {}
        for person in self.persons:
            handle = person.get_handle()
            name = person.get_primary_name()
            surname = " ".join(
                " ".join(part for part in (s.get_prefix(), s.get_surname(),
                                           s.get_connector()) if part)
                for s in name.get_surname_list()).strip() or "?"
            firstname = name.get_first_name().strip() or "?"
            self.names[handle] = (surname, firstname)
            key = name_key(firstname) + "#@#" + name_key(surname)
            self.occ[handle] = used.get(key, 0)
            used[key] = self.occ[handle] + 1

            for fam_handle in person.get_parent_family_handle_list():
                if fam_handle in self.families:
                    self.main_family[handle] = fam_handle
                    break

            for event_ref in person.get_event_ref_list():
                kind = self.witness_kind(event_ref.get_role())
                if kind is not None:
                    self.witnesses.setdefault(event_ref.ref, []).append(
                        (handle, kind))

        for person in self.persons:
            for person_ref in person.get_person_ref_list():
                if person_ref.get_relation().strip().lower() \
                        in GODPARENT_NAMES:
                    godparent = self.get_person(person_ref.ref)
                    if godparent and not self.is_bogus(godparent):
                        self.add_relation(person, "godp", godparent)

        # Children also linked to a family which is not their main one
        # (GeneWeb allows only one): exported as relations.
        for family in self.families.values():
            fam_handle = family.get_handle()
            father = self.get_person(family.get_father_handle())
            mother = self.get_person(family.get_mother_handle())
            for child_ref in family.get_child_ref_list():
                if self.main_family.get(child_ref.ref) == fam_handle:
                    continue
                child = self.get_person(child_ref.ref)
                if not child:
                    continue
                frel = CHILDREF_RELATIONS.get(int(child_ref.get_father_relation()))
                mrel = CHILDREF_RELATIONS.get(int(child_ref.get_mother_relation()))
                if father and mother and frel and frel == mrel \
                        and not self.is_bogus(father) \
                        and not self.is_bogus(mother):
                    self.add_relation(child, frel, father, mother)
                    continue
                if father and frel and not self.is_bogus(father):
                    self.add_relation(child, frel, father)
                if mother and mrel and not self.is_bogus(mother):
                    self.add_relation(child, mrel, mother)
                if not frel and not mrel:
                    LOG.warning("%s is a child of several families, "
                                "only kept in %s",
                                child.get_gramps_id(),
                                self.families[
                                    self.main_family[child_ref.ref]
                                ].get_gramps_id())

    def get_person(self, handle):
        return self.people.get(handle)

    def is_bogus(self, person):
        surname, firstname = self.names[person.get_handle()]
        return surname == "?" or firstname == "?"

    def is_isolated(self, person):
        if person.get_handle() in self.main_family:
            return False
        for fam_handle in person.get_family_handle_list():
            if fam_handle in self.families:
                return False
        return True

    @staticmethod
    def witness_kind(role):
        """Return the GeneWeb witness kind of an event role, or None if
        the role is not a witness."""
        if role.is_custom():
            text = str(role).strip().lower()
            if text in GODPARENT_NAMES:
                return "#godp"
            return "#othe"
        return WITNESS_ROLES.get(int(role))

    # ---------------------------------------------------------------------
    # Persons
    # ---------------------------------------------------------------------
    def ref_name(self, person):
        """Key of a person: Surname Firstname[.occ]"""
        surname, firstname = self.names[person.get_handle()]
        return "%s %s%s" % (gw_string(surname), gw_string(firstname),
                            self.occ_suffix(person))

    def occ_suffix(self, person):
        surname, firstname = self.names[person.get_handle()]
        occ = self.occ[person.get_handle()]
        if occ == 0 or (surname == "?" and firstname == "?"):
            return ""
        return ".%d" % occ

    def get_primary_events(self, person):
        """Events of a person where he is the main participant."""
        events = []
        for event_ref in person.get_event_ref_list():
            if event_ref.get_role() != EventRoleType.PRIMARY:
                continue
            event = self.db.get_event_from_handle(event_ref.ref)
            if event:
                events.append(event)
        return events

    def find_event(self, events, types):
        for event in events:
            if event.get_type() in types:
                return event
        return None

    def person_infos(self, person, is_child=False):
        """Data written on the line defining a person, in the order of
        print_infos in gwuLib.ml."""
        infos = []
        primary = person.get_primary_name()
        surname, firstname = self.names[person.get_handle()]

        # gwcomp reads these fields in a strict order (set_infos):
        # {first name aliases} #salias (public name) #image #nick #alias
        first_aliases, surname_aliases, aliases = [], [], []
        for name in person.get_alternate_names():
            alt_first = name.get_first_name().strip()
            alt_sur = name.get_surname().strip()
            if not alt_first and not alt_sur:
                continue
            if alt_sur in ("", surname) and alt_first not in ("", firstname):
                first_aliases.append("{%s}" % gw_string(alt_first))
            elif alt_first in ("", firstname) and alt_sur not in ("", surname):
                surname_aliases.append("#salias %s" % gw_string(alt_sur))
            elif (alt_first, alt_sur) != (firstname, surname):
                aliases.append("#alias %s" % gw_string(
                    "%s %s" % (alt_first, alt_sur)))

        nicks = [primary.get_nick_name()]
        nicks += [attr.get_value() for attr in person.get_attribute_list()
                  if attr.get_type() == AttributeType.NICKNAME]
        nicks = ["#nick %s" % gw_string(nick)
                 for nick in dict.fromkeys(n.strip() for n in nicks
                                           if n.strip())]

        for group in (first_aliases, surname_aliases, nicks, aliases):
            infos.extend(dict.fromkeys(group))

        events = self.get_primary_events(person)
        for event in events:
            if event.get_type() == EventType.NOB_TITLE:
                infos.append(self.title(event))

        if person.get_privacy():
            infos.append("#apriv")

        occupations = [e.get_description().strip() for e in events
                       if e.get_type() == EventType.OCCUPATION]
        occupations = [o for o in dict.fromkeys(occupations) if o]
        if occupations:
            infos.append("#occu %s" % gw_string(", ".join(occupations)))

        self.add_source(infos, "#src", person.get_citation_list())

        # The birth and death references are not always set (CSV import
        # for instance): then use the first birth or death event.
        birth = None
        birth_ref = person.get_birth_ref()
        if birth_ref:
            birth = self.db.get_event_from_handle(birth_ref.ref)
        if not birth:
            birth = self.find_event(events, (EventType.BIRTH,))
        bapt = self.find_event(events, (EventType.BAPTISM, EventType.CHRISTEN,
                                        EventType.ADULT_CHRISTEN))
        death = None
        death_ref = person.get_death_ref()
        if death_ref:
            death = self.db.get_event_from_handle(death_ref.ref)
        if not death:
            death = self.find_event(events, (EventType.DEATH,))
        burial = self.find_event(events, (EventType.BURIAL,
                                          EventType.CREMATION))

        b_date = self.format_date(birth.get_date_object()) if birth else ""
        p_date = self.format_date(bapt.get_date_object()) if bapt else ""
        d_token = self.death_token(person, death, b_date or p_date)

        if b_date:
            infos.append(b_date)
        elif d_token and not p_date:
            # the death date would otherwise be read as the birth date
            infos.append("0")
        if birth:
            self.add_place(infos, "#bp", birth)
            self.add_source(infos, "#bs", birth.get_citation_list())

        if p_date:
            infos.append("!" + p_date)
        if bapt:
            self.add_place(infos, "#pp", bapt)
            self.add_source(infos, "#ps", bapt.get_citation_list())

        if d_token:
            infos.append(d_token)
        if death:
            self.add_place(infos, "#dp", death)
            self.add_source(infos, "#ds", death.get_citation_list())

        if burial:
            if burial.get_type() == EventType.BURIAL:
                infos.append("#buri")
            else:
                infos.append("#crem")
            r_date = self.format_date(burial.get_date_object())
            if r_date:
                infos.append(r_date)
            self.add_place(infos, "#rp", burial)
            self.add_source(infos, "#rs", burial.get_citation_list())

        if not infos and not is_child and not self.is_bogus(person):
            # a parent without data must be defined with a 0
            infos.append("0")
        return infos

    def death_token(self, person, death, has_birth):
        if death:
            date = self.format_date(death.get_date_object())
            if not date:
                return "0"
            reason = DEATH_REASONS.get(
                death.get_description().strip().lower(), "")
            return reason + date
        if probably_alive(person, self.db):
            # don't know if dead, written only when there is a birth date
            return "?" if has_birth else ""
        return "od"

    def title(self, event):
        """Nobility title: [name:title:place:start:end]"""
        title = "[:%s:%s" % (
            gw_string(event.get_description(), no_colon=True, empty=""),
            gw_string(self.place(event), no_colon=True, empty=""))
        date = self.format_date(event.get_date_object(), no_colon=True)
        if date:
            title += ":" + date
        return title + "]"

    def write_isolated(self, person):
        """A person without any family: written as the child of an empty
        family, like gwu does."""
        self.writeln("fam ? ?.0 + #noment ? ?.0")
        self.writeln("beg")
        self.write_child(person, "?")
        self.writeln("end")
        self.write_person_blocks([person])
        self.writeln()

    # ---------------------------------------------------------------------
    # Families
    # ---------------------------------------------------------------------
    def write_family(self, family):
        fam_handle = family.get_handle()
        father = self.get_person(family.get_father_handle())
        mother = self.get_person(family.get_mother_handle())
        # dict.fromkeys: a child referenced twice in the same family
        # would be defined twice, which gwc refuses
        children = [self.get_person(handle)
                    for handle in dict.fromkeys(
                        ref.ref for ref in family.get_child_ref_list())
                    if self.main_family.get(handle) == fam_handle]
        children = [c for c in children if c]
        if not father and not mother and not children:
            return

        new_persons = []
        fam_events = self.get_family_events(family)
        line = ["fam", self.parent(father, new_persons)]
        line += self.wedding(family, father, mother, fam_events)
        line.append(self.parent(mother, new_persons))
        self.writeln(" ".join(line))

        sources = []
        self.add_source(sources, "src", family.get_citation_list())
        if sources:
            self.writeln(" ".join(sources))

        comment = " ".join(" ".join(note.get().split())
                           for note in self.get_notes(family))
        if comment:
            self.writeln("comm %s" % comment)

        if fam_events:
            self.writeln("fevt")
            for event in fam_events:
                self.write_event(self.fevent_tag(event), event)
            self.writeln("end fevt")

        if children:
            fam_surname = self.names[father.get_handle()][0] if father \
                else "?"
            self.writeln("beg")
            for child in children:
                self.write_child(child, fam_surname)
                new_persons.append(child)
            self.writeln("end")

        self.write_person_blocks(new_persons)
        self.writeln()

    def parent(self, person, new_persons):
        if not person:
            return "? ?"
        text = self.ref_name(person)
        handle = person.get_handle()
        if handle not in self.defined and handle not in self.main_family:
            self.defined.add(handle)
            new_persons.append(person)
            infos = self.person_infos(person)
            if infos:
                text += " " + " ".join(infos)
        return text

    def write_child(self, child, fam_surname):
        handle = child.get_handle()
        self.defined.add(handle)
        surname, firstname = self.names[handle]
        line = ["-"]
        if child.get_gender() == Person.MALE:
            line.append("h")
        elif child.get_gender() == Person.FEMALE:
            line.append("f")
        line.append(gw_string(firstname) + self.occ_suffix(child))
        if surname != fam_surname:
            line.append(gw_string(surname, no_num=True))
        line += self.person_infos(child, is_child=True)
        self.writeln(" ".join(line))

    def get_family_events(self, family):
        events = []
        for event_ref in family.get_event_ref_list():
            if event_ref.get_role() not in (EventRoleType.FAMILY,
                                            EventRoleType.PRIMARY):
                continue
            event = self.db.get_event_from_handle(event_ref.ref)
            if event:
                events.append(event)
        return events

    def wedding(self, family, father, mother, events):
        """Relation, marriage and divorce data of the fam line."""
        line = []
        marriage = self.find_event(events, (EventType.MARRIAGE,))
        date = self.format_date(marriage.get_date_object()) \
            if marriage else ""
        line.append("+" + date)

        def sexes(token):
            def sex(person):
                if person and person.get_gender() == Person.MALE:
                    return "m"
                if person and person.get_gender() == Person.FEMALE:
                    return "f"
                return "?"
            line.extend([token, sex(father) + sex(mother)])

        standard_sexes = (
            (not father or father.get_gender() != Person.FEMALE)
            and (not mother or mother.get_gender() != Person.MALE))
        reltype = int(family.get_relationship())
        if reltype == FamilyRelType.UNMARRIED:
            if standard_sexes:
                line.append("#nm")
            else:
                sexes("#nsck")
        elif reltype == FamilyRelType.CIVIL_UNION:
            sexes("#pacs")
        elif reltype == FamilyRelType.UNKNOWN and not marriage:
            sexes("#noment")
        elif not standard_sexes:
            sexes("#nsckm")

        if marriage:
            self.add_place(line, "#mp", marriage)
            self.add_source(line, "#ms", marriage.get_citation_list())

        divorce = self.find_event(events, (EventType.DIVORCE,))
        if divorce:
            line.append("-" + self.format_date(divorce.get_date_object()))
        elif any(self.fevent_tag(e) == "#sep" for e in events):
            line.append("#sep")
        return line

    def fevent_tag(self, event):
        etype = event.get_type()
        if int(etype) in FEVENTS_MAP:
            return FEVENTS_MAP[int(etype)]
        return self.custom_tag(etype, FEVENTS_CUSTOM_MAP)

    def pevent_tag(self, event):
        etype = event.get_type()
        if int(etype) in PEVENTS_MAP:
            return PEVENTS_MAP[int(etype)]
        return self.custom_tag(etype, PEVENTS_CUSTOM_MAP)

    @staticmethod
    def custom_tag(etype, custom_map):
        name = etype.xml_str()
        for english, tag in custom_map.items():
            if name in (english, _(english)):
                return tag
        return "#" + gw_string(name)

    # ---------------------------------------------------------------------
    # Notes and events blocks of persons
    # ---------------------------------------------------------------------
    def write_person_blocks(self, persons):
        for person in persons:
            if self.is_bogus(person):
                # GeneWeb can't reference persons named "?"
                continue
            self.write_person_notes(person)
        for person in persons:
            if self.is_bogus(person):
                continue
            self.write_person_events(person)

    def write_person_notes(self, person):
        text = "\n".join(note.get() for note in self.get_notes(person))
        lines = [" " + l if l.strip() == "end notes" else l.rstrip()
                 for l in text.strip().splitlines()]
        if not lines:
            return
        self.writeln()
        self.writeln("notes %s" % self.ref_name(person))
        self.writeln("beg")
        for line in lines:
            self.writeln(line)
        self.writeln("end notes")

    def write_person_events(self, person):
        events = [e for e in self.get_primary_events(person)
                  if e.get_type() != EventType.NOB_TITLE]
        if not events:
            return
        self.writeln()
        self.writeln("pevt %s" % self.ref_name(person))
        for event in events:
            self.write_event(self.pevent_tag(event), event)
        self.writeln("end pevt")

    def write_event(self, tag, event):
        line = [tag]
        date = self.format_date(event.get_date_object())
        if date:
            line.append(date)
        self.add_place(line, "#p", event)
        self.add_source(line, "#s", event.get_citation_list())
        self.writeln(" ".join(line))

        for handle, kind in self.witnesses.get(event.get_handle(), []):
            witness = self.get_person(handle)
            if not witness or self.is_bogus(witness):
                continue
            wit = "wit"
            if witness.get_gender() == Person.MALE:
                wit += " m"
            elif witness.get_gender() == Person.FEMALE:
                wit += " f"
            wit += ":"
            if kind:
                wit += " " + kind
            self.writeln("%s %s" % (wit, self.ref_name(witness)))

        notes = []
        if event.get_type() == EventType.OCCUPATION \
                and event.get_description().strip():
            notes.append(event.get_description().strip())
        notes += [note.get() for note in self.get_notes(event)]
        for line in "\n".join(notes).strip().splitlines():
            line = line.rstrip()
            self.writeln("note " + line if line else "note")

    # ---------------------------------------------------------------------
    # Relations (adoption, godparents...)
    # ---------------------------------------------------------------------
    def add_relation(self, person, rtype, parent1, parent2=None):
        if parent2:
            # GeneWeb wants the father first
            if parent1.get_gender() == Person.FEMALE \
                    and parent2.get_gender() == Person.MALE:
                parent1, parent2 = parent2, parent1
            text = "- %s: %s + %s" % (rtype, self.ref_name(parent1),
                                       self.ref_name(parent2))
        else:
            side = "fath" if parent1.get_gender() == Person.MALE else "moth"
            text = "- %s %s: %s" % (rtype, side, self.ref_name(parent1))
        self.relations.setdefault(person.get_handle(), []).append(text)

    def write_relations(self):
        for person in self.persons:
            lines = self.relations.get(person.get_handle())
            if not lines or self.is_bogus(person):
                continue
            self.writeln("rel %s" % self.ref_name(person))
            self.writeln("beg")
            for line in dict.fromkeys(lines):
                self.writeln(line)
            self.writeln("end")
            self.writeln()

    # ---------------------------------------------------------------------
    # Utilities
    # ---------------------------------------------------------------------
    def get_notes(self, obj):
        notes = []
        for handle in obj.get_note_list():
            note = self.db.get_note_from_handle(handle)
            if note:
                notes.append(note)
        return notes

    def place(self, event):
        if not event.get_place_handle():
            return ""
        return _pd.display_event(self.db, event)

    def add_place(self, line, label, event):
        place = self.place(event)
        if place:
            line.extend([label, gw_string(place)])

    def add_source(self, line, label, citation_list):
        sources = [self.citation_text(handle) for handle in citation_list]
        sources = [text for text in dict.fromkeys(sources) if text]
        if sources:
            line.extend([label, gw_string(" ; ".join(sources))])

    def notes_text(self, obj):
        return " ".join(" ".join(note.get().split())
                        for note in self.get_notes(obj))

    def attributes_parts(self, obj):
        return ["%s: %s" % (attr.get_type(), attr.get_value().strip())
                for attr in obj.get_attribute_list()
                if attr.get_value().strip()
                and (self.include_urls
                     or not URL_RE.search(attr.get_value()))]

    def join_parts(self, parts):
        if self.include_urls:
            parts = [linkify(part) for part in parts]
        return " - ".join(part for part in parts if part)

    def citation_text(self, handle):
        """Everything known about a citation, its source and the
        repositories of the source, as one line."""
        if handle in self.citation_texts:
            return self.citation_texts[handle]
        citation = self.db.get_citation_from_handle(handle)
        text = ""
        if citation:
            parts = [self.source_text(citation.get_reference_handle()),
                     citation.get_page().strip()]
            date = _dd.display(citation.get_date_object())
            if date:
                parts.append("%s: %s" % (_("Date"), date))
            if citation.get_confidence_level() != citation.CONF_NORMAL:
                parts.append("%s: %s" % (
                    _("Confidence"),
                    _(conf_strings[citation.get_confidence_level()])))
            parts += self.attributes_parts(citation)
            note = self.notes_text(citation)
            if note:
                parts.append("%s: %s" % (_("Note"), note))
            text = self.join_parts(parts)
        self.citation_texts[handle] = text
        return text

    def source_text(self, handle):
        if handle in self.source_texts:
            return self.source_texts[handle]
        source = self.db.get_source_from_handle(handle)
        parts = []
        if source:
            parts.append(source.get_title().strip())
            for label, value in ((_("Author"), source.get_author()),
                                 (_("Publication"),
                                  source.get_publication_info()),
                                 (_("Abbreviation"),
                                  source.get_abbreviation())):
                if value.strip():
                    parts.append("%s: %s" % (label, value.strip()))
            parts += self.attributes_parts(source)
            note = self.notes_text(source)
            if note:
                parts.append("%s: %s" % (_("Note"), note))
            if self.include_repositories:
                for reporef in source.get_reporef_list():
                    parts += self.repository_parts(reporef)
        text = self.join_parts(parts)
        self.source_texts[handle] = text
        return text

    def repository_parts(self, reporef):
        repo = self.db.get_repository_from_handle(reporef.ref)
        if not repo:
            return []
        parts = ["%s: %s" % (_("Repository"), repo.get_name().strip())]
        if reporef.get_call_number().strip():
            parts.append("%s: %s" % (_("Call Number"),
                                     reporef.get_call_number().strip()))
        note = self.notes_text(reporef)
        if note:
            parts.append("%s: %s" % (_("Note"), note))
        for address in repo.get_address_list():
            fields = [address.get_street(), address.get_locality(),
                      address.get_city(), address.get_postal_code(),
                      address.get_county(), address.get_state(),
                      address.get_country(), address.get_phone()]
            fields = [f.strip() for f in fields if f.strip()]
            if fields:
                parts.append("%s: %s" % (_("Address"), ", ".join(fields)))
        for url in repo.get_url_list() if self.include_urls else []:
            if url.get_path().strip():
                parts.append(" ".join(filter(None, (
                    url.get_description().strip(), url.get_path().strip()))))
        note = self.notes_text(repo)
        if note:
            parts.append("%s: %s" % (_("Note"), note))
        return parts

    def format_date(self, date, no_colon=False):
        """Date in GeneWeb format, "" if empty."""
        if date is None:
            return ""
        if date.get_modifier() == Date.MOD_TEXTONLY:
            text = gw_string(date.get_text(), no_colon=no_colon, empty="")
            return "0(%s)" % text if text else ""
        if date.is_empty():
            return ""
        if date.get_calendar() not in CALENDARS:
            date = date.to_calendar("gregorian")
        start = date.get_start_date()
        if start[2] == 0:
            # GeneWeb needs a year: keep the date as a text
            text = gw_string(_dd.display(date), no_colon=no_colon, empty="")
            return "0(%s)" % text if text else ""
        mod = date.get_modifier()
        retval = DATE_MODIFIERS.get(mod, "") + self.dmy(start)
        if mod in (Date.MOD_RANGE, Date.MOD_SPAN):
            stop = date.get_stop_date()
            if stop[2] != 0:
                retval += ".." + self.dmy(stop)
        return retval + CALENDARS[date.get_calendar()]

    @staticmethod
    def dmy(subdate):
        day, month, year = subdate[0], subdate[1], subdate[2]
        year = "-0" if year == 0 else str(year)
        if month == 0:
            return year
        if day == 0:
            return "%d/%s" % (month, year)
        return "%d/%d/%s" % (day, month, year)


# -------------------------------------------------------------------------
#
#
#
# -------------------------------------------------------------------------
def exportData(database, filename, user, option_box=None):
    gw = GeneWebPlusWriter(database, filename, user, option_box)
    return gw.export_data()
