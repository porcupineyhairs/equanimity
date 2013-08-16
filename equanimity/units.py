"""
units.py

Created by AFD on 2013-08-05.
Copyright (c) 2013 A. Frederick Dudley. All rights reserved.
"""
from stone import Stone
from const import ELEMENTS, E, F, I, W, ORTH, OPP
from datetime import datetime
#from weapons import Sword, Bow, Wand, Glove


class Unit(Stone):
    def __init__(self, element, comp, name=None, location=None, sex='female'):
        if not element in ELEMENTS:
            fmt = "Invalid element: {0}, valid elements are {1}"
            raise Exception(fmt.format(element, ELEMENTS))
        if comp[element] == 0:
            raise ValueError("Units' primary element must be greater than 0.")

        if comp[OPP[element]] != 0:
            raise ValueError("Units' opposite element must equal 0.")

        Stone.__init__(self, comp)
        now = datetime.utcnow()
        self.element = element
        if name is None:
            self.name = self.__hash__()
        self.name = name
        self.location = location
        self.container = None
        self.sex = sex
        self.DOB = now
        self.DOD = None
        self.fed_on = None
        self.val = self.value()
        self.id = id(self)

    def __repr__(self):
        return self.name

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
        return {'p': self.p, 'm': self.m, 'atk': self.atk, 'defe': self.defe,
                'pdef': self.pdef, 'patk': self.patk, 'mdef': self.mdef,
                'matk': self.matk, 'hp': self.hp}


class Scient(Unit):
    """A Scient (playable character) unit.

    Initializer takes element and comp:
      * element - this unit's element (E, F, I, or W) aka 'suit'
      * comp - dictionary of this unit's composition on (0..255) {E: earth,
      F: fire, I: ice, W: wind}
    """

    def equip(self, weapon):
        self.weapon = weapon

    def unequip(self):
        """removes weapon from scient, returns weapon."""
        weapon = self.weapon
        self.weapon = None
        return weapon

    def __init__(self, element, comp, name=None, weapon=None,
                 weapon_bonus=None, location=None, sex='female'):
        for orth in ORTH[element]:
            if comp[orth] > comp[element] / 2:
                raise ValueError("Scients' orthogonal elements cannot be "
                                 "more than half the primary element's "
                                 "value.")
        Unit.__init__(self, element, comp, name, location, sex)
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
        if comp[OPP[self.element]] == 0:
            for orth in ORTH[self.element]:
                if ((comp[orth] + self.comp[orth]) >
                        ((comp[self.element] + self.comp[self.element]) / 2)):
                    raise ValueError("Scients' orthogonal elements cannot be"
                                     "more than half the primary element's "
                                     "value.")
            Stone.imbue(self, stone)
        else:
            raise Exception("Primary element of stone must match that of "
                            "scient")


class Part(object):
    '''
    @property
    def pdef(self):
        return self.nescient.pdef
    '''

    def hp_fget(self):
        return self.nescient.hp

    def hp_fset(self, hp):
        self.nescient.hp = hp

    hp = property(hp_fget, hp_fset)

    def __init__(self, nescient, location=None):
        self.nescient = nescient
        self.location = location


class Nescient(Unit):
    """A non-playable unit."""

    def take_body(self, new_body):
        """Takes locations from new_body and applies them to body."""
        for part in new_body:
            new_body[part].nescient = self
            self.body = new_body

    def calcstats(self):
        Unit.calcstats(self)
        self.atk = (2 * (self.comp[F] + self.comp[I]) + self.comp[E] +
                    self.comp[W]) + (4 * self.value())
        self.hp = self.hp * 4  # This is an open question.

    def __init__(self, element, comp, name=None, weapon=None,
                 location=None, sex='female', facing=None,
                 body=None):
        if body is None:
            body = {'head':  None, 'left': None, 'right': None, 'tail': None}
        comp = Stone(comp)
        for orth in ORTH[element]:
            if comp[orth] != 0:
                if comp[OPP[orth]] != 0:
                    raise ValueError("Nescients' cannot have values greater "
                                     "than zero for both orthogonal elements.")
            elif comp[orth] > comp[element]:
                raise ValueError("Nescients' orthogonal value cannot exceed "
                                 "the primary element value.")

        Unit.__init__(self, element, comp, name, location, sex)
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
        self.location = location  # ...
        self.facing = facing
        self.weapon = self  # hack for attack logic.
