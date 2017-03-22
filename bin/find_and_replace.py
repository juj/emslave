# Small utility for command-line search-and-replace of a file:
# usage: python find_and_replace.py filename regex_pattern_to_search string_to_replace_with

import sys, re, os

filename = sys.argv[1]
find = sys.argv[2]
replace = os.path.expandvars(sys.argv[3])

print "Filename: '" + filename + "'"
print "find: '" + find + "'"
print "replace: '" + replace + "'"

try:
	text = open(filename, 'r').read()
	print 'before:'
	print text
	text = re.sub(find, replace, text)
	print 'after:'
	print text

	open(filename, 'w').write(text)
except Exception, e:
	print 'Failed to search-replace, error: ' + str(e)
	print '(ignoring this error)'
