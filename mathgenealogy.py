# Copyright (c) 2008, 2009 David Alber
# 
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
#
# Modified 2011 by Julian Wintermayr


from optparse import OptionParser
import string
import update
import search
import databaseConnection



class Mathgenealogy:
	"""
	A class for parsing the command-line information and checking them. Use this
	information to call the correct function.
	"""
	def __init__(self):
		self.passedIDs = []
		self.passedName = None
		self.updateByID = False
		self.updateByName = False
		self.forceNaive = False
		self.ancestors = False
		self.descendants = False
		self.lca = False
		self.aa = False
		self.ad = False
		self.web = False
		self.verbose = False
		self.writeFilename = None
		self.noDetails = False
		self.database = ""


	def parseInput(self):
		"""
		Parse command-line information.
		"""
		self.parser = OptionParser()

		self.parser.set_usage("%prog [options] LastName or IDs")
		self.parser.set_description("Update local database from the Mathematics Genealogy Project. Create a \
									Graphvizdot-file for a mathematics genealogy by querying the locals database, \
									where ID is a record identifier from the Mathematics Genealogy Project. Multiple \
									IDs may be passed in case of search queries. Choose one update method OR one \
									search method with the allowed options. You need online access for updates. You \
									don't need online access for search queries.")

		self.parser.add_option("-i", "--update-by-ID", action="store_true", dest="updateByID", default=False,
							   help="Update method: Update the local database entries of the entered ID (and of the \
							   descendants and/or ancestors). INPUT: one ID")

		self.parser.add_option("-n", "--update-by-name", action="store_true", dest="updateByName", default=False,
							   help="Update method: Find the corresponding ID in the online database of a \
							   mathematician. Besides, the tool will also update the records of all found \
							   mathematicians. INPUT: last name of one mathematician")

		self.parser.add_option("-f", "--force", action="store_true", dest="forceNaive", default=False,
							   help="Force the tool to use naive update logic, which downloads all records of every \
							   mathematician you want to update without looking for any changes and stores every \
							   entry in the local database (replaces existing ones). Only available for update \
							   methods,not for search methods!")

		self.parser.add_option("-a", "--with-ancestors", action="store_true", dest="ancestors", default=False,
							   help="Retrieve ancestors of IDs and include in graph. Only available for update-by-ID!")

		self.parser.add_option("-d", "--with-descendants", action="store_true", dest="descendants", default=False,
							   help="Retrieve descendants of IDs and include in graph. Only available for update-by-ID!")

		self.parser.add_option("-w", "--web-front-end", action="store_true", dest="web",
		                       default=False, help="Don't use! Needed for web front-end")


		self.parser.add_option("-L", "--least-common-advisor", action="store_true", dest="lca", default=False,
							   help="Search method: Search for the lowest common advisor of an arbitrary number of \
							   mathematicians. INPUT: IDs of the mathematicians separated by spaces")

		self.parser.add_option("-A", "--all-ancestors", action="store_true", dest="aa", default=False,
							   help="Search method: Search for all ancestors of one mathematician. INPUT: ID of one \
							   mathematician")

		self.parser.add_option("-D", "--all-descendants", action="store_true", dest="ad", default=False,
							   help="Search method: Search for all descendants of one mathematician. INPUT: ID of one \
							   mathematician")


		self.parser.add_option("-s", "--save-to-file", dest="filename", metavar="FILE", default=None,
							   help="Write output to a dot-file [default: stdout]. Only available for search methods, \
							   not for update methods!")

		self.parser.add_option("-b", "--use-different-database", action="store", type="string", dest="database",
		                       default="MGDB",
							   help="Define the SQLite database name. This database will be created, \
							   updated or queried.")


		self.parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False,
							   help="Print update messages and database messages.")

		self.parser.add_option("-u", "--no-details", action="store_true", dest="noDetails", default=False,
							   help="Don't add university for each mathematician to the DOT-file.")

		self.parser.add_option( "-V", "--version", action="store_true", dest="print_version", default=False,
							   help="Print version and exit.")


		(options, args) = self.parser.parse_args()

		self.updateByID = options.updateByID
		self.updateByName = options.updateByName
		self.forceNaive = options.forceNaive
		self.ancestors = options.ancestors
		self.descendants = options.descendants
		self.lca = options.lca
		self.aa = options.aa
		self.ad = options.ad
		self.web = options.web
		self.verbose = options.verbose
		self.writeFilename = options.filename
		self.noDetails = options.noDetails
		self.database = options.database

		if options.print_version:
			print("Math-Genealogy-DB Version 1.0")
			self.parser.exit()

		# Check for no arguments
		if len(args) == 0:
			raise SyntaxError("%s: error: no IDs or no last name passed" % (self.parser.get_prog_name()))

		# Check for the correct combination of options
		if (self.updateByName or self.updateByID or self.forceNaive or self.ancestors or self.descendants) and\
		   (self.lca or self.aa or self.ad or (self.writeFilename is not None)):
			raise SyntaxError("%s: error: invalid combination of options" % (self.parser.get_prog_name()))

		if self.updateByName and (self.ancestors or self.descendants):
			raise SyntaxError("%s: error: invalid combination of options" % (self.parser.get_prog_name()))

		if self.updateByName and self.updateByID:
			raise SyntaxError("%s: error: you can only choose one update method" % (self.parser.get_prog_name()))

		if self.lca and (self.aa or self.ad):
			raise SyntaxError("%s: error: you can only choose one search method" % (self.parser.get_prog_name()))

		if not (self.updateByName or self.updateByID or self.lca or self.aa or self.ad):
			raise SyntaxError("%s: error: you have to choose one update method or one search method"
			% (self.parser.get_prog_name()))

		# Check for the correct content (updateByName may contain anything)
		if not self.updateByName:
			for arg in args:
				for digit in arg:
					if digit not in string.digits:
						raise SyntaxError("%s: error: all arguments have to be numbers" % (self.parser.get_prog_name()))

		# Check for the correct number of arguments
		if self.aa or self.ad:
			if len(args) != 1:
				raise SyntaxError("%s: error: enter only one ID" % (self.parser.get_prog_name()))

		if self.updateByName:
			if len(args) != 1:
				raise SyntaxError("%s: error: enter only one Name" % (self.parser.get_prog_name()))

		if self.updateByID:
			if len(args) < 1:
				raise SyntaxError("%s: error: you have to enter at least one ID" % (self.parser.get_prog_name()))

		if self.lca:
			if len(args) < 2:
				raise SyntaxError("%s: error: you have to enter at least two IDs to execute this search method"
				% (self.parser.get_prog_name()))

		# If no error occurred, then the options and arguments are correct. Hence, we can continue:
		# Read the arguments
		if self.updateByName:
			self.passedName = str(args[0])

		else:
			for arg in args:
				self.passedIDs.append(int(arg))

		databaseConnector = databaseConnection.DatabaseConnector()
		connector = databaseConnector.connectToSQLite(self.database)

		# Call the correct function depending on the options which have been passed
		if self.updateByName:
			updater = update.Updater(connector, self.forceNaive, self.web)
			updater.findID(self.passedName)

		if self.updateByID:
			updater = update.Updater(connector, self.forceNaive, self.web)
			updater.updateByID(self.passedIDs, self.ancestors, self.descendants)

		if self.lca:
			searcher = search.Searcher(connector, self.writeFilename, self.noDetails)
			searcher.lca(self.passedIDs)

		if self.aa and not self.ad:
			searcher = search.Searcher(connector, self.writeFilename, self.noDetails)
			searcher.allAncestors(self.passedIDs)

		if self.ad and not self.aa:
			searcher = search.Searcher(connector, self.writeFilename, self.noDetails)
			searcher.allDescendants(self.passedIDs)

		if self.aa and self.ad:
			searcher = search.Searcher(connector, self.writeFilename, self.noDetails)
			searcher.allAncestorsDescendants(self.passedIDs)


		connection = connector[0]
		cursor = connector[1]

		cursor.close()
		connection.close()