# ##### BEGIN AGPL LICENSE BLOCK #####
# This file is part of SimpleMMO.
#
# Copyright (C) 2011, 2012  Charles Nelson
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ##### END AGPL LICENSE BLOCK #####

def coord_dictify(*listitems):

    '''Turns a list of items that correspond to coordinates like:
        >>> x = [1, 2, 3]

        And turns it into something like:
        >>> d = coord_dictify(*x)
        >>> d['x']
        1
        >>> d['z']
        3

        Or in whole: {'x': 1, 'y': 2, 'z': 3}

        If there are more than three entries, it uses more letters of the alphabet backwards.
        >>> d = coord_dictify(1, 2, 3, 4, 5)
        >>> d['x']
        1
        >>> d['v']
        5

        Or in whole: {'x': 1, 'y': 2, 'z': 3, 'w': 4, 'v': 5}
    '''
    letters = ["x", "y", "z"]
    import string
    otherletters = list(reversed(list(string.ascii_lowercase)))
    for l in letters:
        otherletters.remove(l)
    letters.extend(otherletters)

    newdict = dict()
    newdict.update(zip(letters, listitems))
    return newdict

if __name__ == "__main__":
    import doctest
    doctest.testmod()
