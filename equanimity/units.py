"""
units.py

Created by AFD on 2013-08-05.
Copyright (c) 2013 A. Frederick Dudley. All rights reserved.
"""
import transaction
import random
from datetime import datetime
from stone import Stone, Composition, rand_comp
from const import ELEMENTS, E, F, I, W, ORTH, OPP
from grid import Hex
from server import db
from helpers import validate_length, rand_string, rand_element


UNIT_NAME_LEN = dict(max=64, min=1)


class Unit(Stone):
    attrs = ['p', 'm', 'atk', 'defe', 'pdef', 'patk', 'mdef', 'matk', 'hp']

    def __init__(self, element, comp, name=None, sex='female'):
        if not element in ELEMENTS:
            fmt = "Invalid element: {0}, valid elements are {1}"
            raise Exception(fmt.format(element, ELEMENTS))
        if comp[element] == 0:
            raise ValueError("Units' primary element must be greater than 0.")

        if comp[OPP[element]] != 0:
            raise ValueError("Units' opposite element must equal 0.")

        super(Unit, self).__init__(comp)
        now = datetime.utcnow()
        self.element = element
        self.name = name
        self.location = Hex.null
        self.remove_from_container()
        self.sex = sex
        self.dob = now
        self.dod = None
        self.fed_on = None
        self.val = self.value()
        self.uid = db['unit_uid'].get_next_id()
        db['units'][self.uid] = self
        transaction.commit()

    def api_view(self):
        dod = self.dod
        if dod is not None:
            dod = dod.isoformat()
        return dict(comp=self.comp, element=self.element, name=self.name,
                    location=tuple(self.location), sex=self.sex,
                    dob=self.dob.isoformat(), dod=dod, uid=self.uid,
                    chosen_location=tuple(self.chosen_location))

    @classmethod
    def get(self, id):
        return db['units'].get(id)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        if name is None:
            name = rand_string()
        validate_length(name, **UNIT_NAME_LEN)
        self._name = name

    @property
    def chosen_location(self):
        return self._chosen_location

    @chosen_location.setter
    def chosen_location(self, loc):
        self._chosen_location = Hex._make(loc)

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, loc):
        self._location = Hex._make(loc)

    def calcstats(self):
        self.p = (2 * (self.comp[F] + self.comp[E]) + self.comp[I] +
                  self.comp[W])
        self.m = (2 * (self.comp[I] + self.comp[W]) + self.comp[F] +
                  self.comp[E])
        self.atk = (2 * (self.comp[F] + self.comp[I]) + self.comp[E] +
                    self.comp[W]) + (2 * self.value())
        self.defe = (2 * (self.comp[E] + self.comp[W]) + self.comp[F] +
                     self.comp[I])

        self.pdef = self.p + self.defe + (2 * self.comp[E])
        self.patk = self.p + self.atk + (2 * self.comp[F])
        self.matk = self.m + self.atk + (2 * self.comp[I])
        self.mdef = self.m + self.defe + (2 * self.comp[W])
        #does this make sense? It was wrong for a long time.
        self.hp = 4 * ((self.pdef + self.mdef) + self.value())

    def stats(self):
        return dict(zip(self.attrs, [getattr(self, s) for s in self.attrs]))

    def add_to_container(self, container, pos):
        self.container = container
        self.container_pos = pos
        # Reset out chosen location, since it is dependent on the context
        # of its container
        self.chosen_location = Hex.null

    def remove_from_container(self):
        self.container = None
        self.container_pos = None
        self.chosen_location = Hex.null

    def __repr__(self):
        return '<{0} "{1}">'.format(self.__class__.__name__, self.name)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return (self.uid == other.uid)
        return False

    def __ne__(self, other):
        return not self.__eq__(other)


class Scient(Unit):
    """A Scient (playable character) unit.

    Initializer takes element and comp:
      * element - this unit's element (E, F, I, or W) aka 'suit'
      * comp - dictionary of this unit's composition on (0..255) {E: earth,
      F: fire, I: ice, W: wind}
    """

    def __init__(self, element, comp, name=None, weapon=None,
                 weapon_bonus=None, sex='female'):
        comp = Composition.create(comp)
        for o in comp.orth(element):
            if o > comp[element] / 2:
                raise ValueError("Scients' orthogonal elements cannot be "
                                 "more than half the primary element's "
                                 "value.")
        super(Scient, self).__init__(element, comp, name=name, sex=sex)
        self.size = 1
        self.move = 4
        self.weapon = weapon
        if weapon_bonus is None:
            self.weapon_bonus = Stone()
        else:
            self.weapon_bonus = weapon_bonus
        self.equip_limit = Stone({E: 1, F: 1, I: 1, W: 1})
        for element in ELEMENTS:
            self.equip_limit.limit[element] = 256
        for i in self.equip_limit:
            self.equip_limit[i] = (self.equip_limit[i] + self.comp[i] +
                                   self.weapon_bonus[i])
        self.calcstats()

        #equiping weapons should be done someplace else.
        self.equip(self.weapon)

    def imbue(self, stone):
        """add stone to scient's comp, if legal"""
        comp = stone.comp
        if comp[OPP[self.element]] != 0:
            raise Exception("Primary element of stone must match that of "
                            "scient")
        for orth in ORTH[self.element]:
            if (comp[orth] + self.comp[orth] >
                    comp[self.element] + (self.comp[self.element] / 2)):
                raise ValueError("Scients' orthogonal elements cannot be"
                                 "more than half the primary element's "
                                 "value.")
        return super(Scient, self).imbue(stone)

    def equip(self, weapon):
        self.weapon = weapon

    def unequip(self):
        """removes weapon from scient, returns weapon."""
        weapon = self.weapon
        self.weapon = None
        return weapon

    def api_view(self):
        data = super(Scient, self).api_view()
        weapon = self.weapon
        if weapon is not None:
            weapon = weapon.api_view()
        more = dict(weapon=weapon, weapon_bonus=self.weapon_bonus.comp,
                    equip_limit=self.equip_limit.comp,
                    size=self.size, move=self.move)
        data.update(more)
        return data


class Nescient(Unit):
    """A non-playable unit."""

    def __init__(self, element, comp, name=None, weapon=None, sex='female',
                 facing=None, body=None):
        if body is None:
            body = {'head':  None, 'left': None, 'right': None, 'tail': None}
        comp = Stone(comp)
        orth = comp.orth(element)
        if all(orth):
            raise ValueError("Nescients' cannot have values greater than zero "
                             "for both orthogonal elements.")
        for o in orth:
            if o > comp[element]:
                raise ValueError("Nescients' orthogonal value cannot exceed "
                                 "the primary element value.")

        super(Nescient, self).__init__(element, comp, name=name, sex=sex)
        self.size = 2
        self.move = 4
        #Set nescient type.
        if self.element == 'Earth':
            self.kind = 'p'
            if self.comp[F] == 0:
                self.type = 'Avalanche'  # AOE Full
            else:
                self.type = 'Magma'  # ranged Full

        elif self.element == 'Fire':
            self.kind = 'p'
            if self.comp[E] == 0:
                self.type = 'Firestorm'  # ranged DOT
                self.time = 3
            else:
                self.type = 'Forestfire'  # ranged Full

        elif self.element == 'Ice':
            self.kind = 'm'
            if self.comp[E] == 0:
                self.type = 'Icestorm'  # AOE DOT
                self.time = 3
            else:
                self.type = 'Permafrost'  # AOE Full
        else:  # Wind
            self.kind = 'm'
            self.time = 3
            if self.comp[F] == 0:
                self.type = 'Blizzard'  # AOE DOT
            else:
                self.type = 'Pyrocumulus'  # ranged DOT

        self.calcstats()
        for part in body:  # MESSY!!!!
            body[part] = Part(self)
        self.body = body
        self.facing = facing
        self.weapon = self  # hack for attack logic.

    def take_body(self, new_body):
        """Takes locations from new_body and applies them to body."""
        for part in new_body:
            new_body[part].nescient = self
            self.body = new_body

    def calcstats(self):
        super(Nescient, self).calcstats()
        self.atk = (2 * (self.comp[F] + self.comp[I]) + self.comp[E] +
                    self.comp[W]) + (4 * self.value())
        self.hp = self.hp * 4  # This is an open question.


class Part(object):

    def __init__(self, nescient, location=None):
        self.nescient = nescient
        self.location = location

    @property
    def hp(self):
        return self.nescient.hp

    @hp.setter
    def hp(self, hp):
        self.nescient.hp = hp

    def __repr__(self):
        s = '<{0}: {1} [{2}]>'
        return s.format(self.__class__.__name__, self.location, self.nescient)


""" Unit helpers """


def rand_unit(suit=None, kind='Scient'):
    """Returns a random Scient of suit. Random suit used if none given."""
    kinds = ('Scient', 'Nescient')
    if not kind in kinds:
        kind = random.choice(kinds)

    if not suit in ELEMENTS:
        suit = rand_element()
        comp = rand_comp(suit, kind)
    else:
        comp = rand_comp(suit, kind)

    if kind == 'Scient':
        return Scient(suit, comp, rand_string())
    else:
        return Nescient(suit, rand_comp(suit, 'Nescient'), rand_string())


def stats(unit):
    print unit.name + ": " + str(unit.comp)
    print "Physical: " + str(unit.p)
    print "Magical: " + str(unit.m)
    print "Attack: " + str(unit.atk)
    print "Defense: " + str(unit.defe)
    print "P ATK: " + str(unit.patk)
    print "P DEF: " + str(unit.pdef)
    print "M ATK: " + str(unit.matk)
    print "M DEF: " + str(unit.mdef)
