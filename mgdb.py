import mathgenealogy



mgdb = mathgenealogy.Mathgenealogy()
try:
    mgdb.parseInput()
except SyntaxError, e:
    print mgdb.parser.get_usage()
    print e