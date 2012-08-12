#!/usr/bin/env python2.7
# ##### BEGIN AGPL LICENSE BLOCK #####
# This file is part of SimpleMMO.
#
# Copyright (C) 2012 Charles Nelson
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

VOWELS = "aeiouy"
CONSTS = "bcdfghjklmnpqrstvwxz"

def shift(message, shift):
    '''Shift a string by a number to produce a string resembling language.
    It pays attention to whether a letter is a vowel or a consonant, and
    shifts them separately.
    This means a vowel will never become a consonant, and neither vice versa.
    This also means that it will stay looking like a language because there
    will always be about enough vowels to be pronouncable/readable.

    Example:
        "This is a thing!"
        When shifted by 1 becomes:
        "Vjot ot e vjoph!"
        And when shifted by 2:
        "Wkuv uv i wkuqj!"
    '''
    # TODO: Randomize the VOWELS and CONSTS strings.
    new_message = ""
    for char in message:
        lowerchar = char.lower()
        for charlist in (VOWELS, CONSTS):
            if lowerchar in charlist:
                index = list(charlist).index(lowerchar)
                newindex = (index+shift)
                newchar = charlist[newindex % len(charlist)]

                if char.istitle():
                    newchar = newchar.title()

                new_message += newchar
                break
        else:
            new_message += char
    return new_message

if __name__ == "__main__":
    for i in xrange(26):
        print i, shift("This is a thing!", i)
