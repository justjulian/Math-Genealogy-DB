#!/usr/bin/python3

import mathgenealogy



mgdb = mathgenealogy.Mathgenealogy()

try:
    mgdb.parseInput()
except SyntaxError as e:
    print(e)
    print(mgdb.parser.get_usage())