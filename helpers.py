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
