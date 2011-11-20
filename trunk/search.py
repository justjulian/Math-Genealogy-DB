# Copyright (c) 2011 Julian Wintermayr
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


import visualize



class Searcher:
	"""
	Class for several search methods.
	"""
	def __init__(self, connector, filename, details):
		self.filename = filename
		self.noDetails = details
		self.maxPrefix = 0
		self.lcaMode = False

		self.ancestorSet = set()
		self.descendantSet = set()

		self.LCAset = set()
		self.paths = set()
		self.allLCApaths = set()

		self.connector = connector
		self.connection = connector[0]
		self.cursor = connector[1]


	def saveDotFile(self, queryName, rootID, blackSet, redSet=None):
		# Create DOT-file
		visualizer = visualize.Visualizer(self.connector, self.noDetails)
		dotFile = visualizer.generateDotFile(blackSet, redSet)

		# Print DOT-file to user defined file
		if self.filename is not None:
			query = open(self.filename + str(rootID) + queryName + ".dot", "w")
			query.write(dotFile)
			query.close()

		# Print DOT-file to std-out
		else:
			print(dotFile)


	def createAdvisorSet(self, id):
		# Get all advisors
		self.cursor.execute("SELECT advisor FROM advised, dissertation WHERE student=dID AND author=?", (id,))
		queryList = self.cursor.fetchall()

		# Store advisors in a set
		advisors = set()

		for row in queryList:
			advisors.add(row["advisor"])

		return advisors


	def createStudentSet(self, id):
		# Get all students
		self.cursor.execute("SELECT author FROM advised, dissertation WHERE student=dID AND advisor=?", (id,))
		queryList = self.cursor.fetchall()

		# Store students in a set
		students = set()

		for row in queryList:
			students.add(row["author"])

		return students


	def allAncestors(self, id):
		# 'id' is a list containing one item
		id = id[0]
		self.ancestorSet.add(id)

		advisors = self.createAdvisorSet(id)

		# Start grabbing ancestors recursively
		if len(advisors) > 0:
			self.recursiveAncestors(advisors)

		# Only create DOT-file if the user only searches for all ancestors and not for the LCA
		if not self.lcaMode:
			# If there is only the start node in the set, then there are no ancestors
			if len(self.ancestorSet) < 2:
				print("There are no ancestors!")

			# Create DOT-file
			else:
				self.ancestorSet.remove(id)
				print("The {} ancestor(s) of {} is/are {}".format(len(self.ancestorSet), id, self.ancestorSet))
				self.ancestorSet.add(id)
				self.saveDotFile("All-Ancestors", id, self.ancestorSet)

		# If searching for the LCA, then store this set
		else:
			self.LCAset = self.LCAset.union(self.ancestorSet)

		# Delete set!
		self.ancestorSet = set()


	def allDescendants(self, id):
		# 'id' is a list containing one item
		id = id[0]
		self.descendantSet.add(id)

		students = self.createStudentSet(id)

		# Start grabbing descendants recursively
		if len(students) > 0:
			self.recursiveDescendants(students)

		# Only create DOT-file if the user only searches for all descendants and not for the LCA
		if not self.lcaMode:
			# If there is only the start node in the set, then there are no descendants
			if len(self.descendantSet) < 2:
				print("There are no descendants!")

			# Create DOT-file
			else:
				self.descendantSet.remove(id)
				print("The {} descendant(s) of {} is/are {}".format(len(self.descendantSet), id, self.descendantSet))
				self.descendantSet.add(id)
				self.saveDotFile("All-Descendants", id, self.descendantSet)

		# If searching for the LCA, then store this set
		else:
			self.LCAset = self.LCAset.union(self.descendantSet)

		# Delete set!
		self.descendantSet = set()


	def allAncestorsDescendants(self, id):
		# 'id' is a list containing one item
		id = id[0]
		self.ancestorSet.add(id)
		self.descendantSet.add(id)

		advisors = self.createAdvisorSet(id)

		# Start grabbing ancestors recursively
		if len(advisors) > 0:
			self.recursiveAncestors(advisors)

		students = self.createStudentSet(id)

		# Start grabbing descendants recursively
		if len(students) > 0:
			self.recursiveDescendants(students)

		# If there is only the start node in the set, then there are no ancestors
		if len(self.ancestorSet) < 2:
			print("There are no ancestors!")

		else:
			self.ancestorSet.remove(id)
			print("The {} ancestor(s) of {} is/are {}".format(len(self.ancestorSet), id, self.ancestorSet))
			self.ancestorSet.add(id)

			print("")

		# If there is only the start node in the set, then there are no descendants
		if len(self.descendantSet) < 2:
			print("There are no descendants!")

		else:
			self.descendantSet.remove(id)
			print("The {} descendant(s) of {} is/are {}".format(len(self.descendantSet), id, self.descendantSet))
			self.descendantSet.add(id)

		# Create DOT-file
		if len(self.ancestorSet) > 1 or len(self.descendantSet) > 1:
			AncestorDescendantSet = self.ancestorSet.union(self.descendantSet)
			self.saveDotFile("All-Ancestors-Descendants", id, AncestorDescendantSet)

		# Delete sets!
		self.ancestorSet = set()
		self.descendantSet = set()


	def recursiveAncestors(self, advisors):
		for advisor in advisors:
			self.ancestorSet.add(advisor)

			nextAdvisors = self.createAdvisorSet(advisor)

			if len(nextAdvisors) > 0:
				self.recursiveAncestors(nextAdvisors.difference(self.ancestorSet))


	def recursiveDescendants(self, students):
		for student in students:
			self.descendantSet.add(student)

			nextStudents = self.createStudentSet(student)

			if len(nextStudents) > 0:
				self.recursiveDescendants(nextStudents.difference(self.descendantSet))


	# Used by 'update.py'
	def numberOfDescendants(self, students):
		self.recursiveDescendants(students)

		return len(self.descendantSet)


	def lca(self, ids):
		self.lcaMode = True

		id1 = [0, ids[0]]

		for i in range(len(ids)-1):
			if len(id1) < 1:
				break

			else:
				id1 = self.recursiveLCA(id1, ids[i+1])

		if len(id1) < 1:
			print("There is no LCA!")

		else:
			for id in ids:
				self.allAncestors([id])
				self.allDescendants([id])

			lca = id1
			redLCAset = set()

			for singleLCA in lca:
				redLCAset.add(singleLCA)

				for path in self.allLCApaths:
					splitPath = path.split(str(singleLCA) + '.')

					if len(splitPath) > 1 and not splitPath[1] == "":
						redIDlist = splitPath[1].split('.')

						for redID in redIDlist:
							try:
								intID = int(redID)

							except ValueError:
								continue

							redLCAset.add(intID)

				self.cursor.execute("SELECT name FROM person WHERE pID=?", (singleLCA,))
				lcaName = self.cursor.fetchone()
				print("The LCA with {} common ancestors is {}: {}".format(self.maxPrefix, singleLCA, lcaName["name"]))

			blackLCAset = self.LCAset.difference(redLCAset)

			rootIDs = "-"

			for id in ids:
				rootIDs += str(id) + "-"

			self.saveDotFile("LCA", rootIDs, blackLCAset, redLCAset)

		self.lcaMode = False


	def recursiveLCA(self, idSet, id2):
		path2 = self.generatePathOf(id2)
		lcaPath = set()
		self.maxPrefix = 0
		lca = []

		for id1 in idSet:
			if id1 == 0:
				continue

			path1 = self.generatePathOf(id1)

			for row1 in path1:
				splitPath1 = row1.split('.')

				for row2 in path2:
					prefix = 0
					splitPath2 = row2.split('.')

					if len(splitPath1) >= len(splitPath2):
						longPathIter = iter(splitPath1)
						shortPathIter = iter(splitPath2)

					else:
						longPathIter = iter(splitPath2)
						shortPathIter = iter(splitPath1)

					for singlePathID1 in shortPathIter:
						singlePathID2 = next(longPathIter)

						prefix += 1

						if singlePathID1 == singlePathID2:
							if prefix == self.maxPrefix:
								if int(singlePathID1) not in lca:
									lca.append(int(singlePathID1))

								lcaPath.add(row1)
								lcaPath.add(row2)

							if prefix > self.maxPrefix:
								lca = []
								lcaPath = set()

								lca.append(int(singlePathID1))
								lcaPath.add(row1)
								lcaPath.add(row2)
								self.maxPrefix = prefix

						else:
							break

		for row in lcaPath:
			self.allLCApaths.add(row)

		return lca


	def generatePathOf(self, id):
		print("Updating path of #{}".format(id))
		nextAdvisors = self.createAdvisorSet(id)

		if len(nextAdvisors) > 0:
			self.recursiveAncestorsPath(nextAdvisors, str(id))

		else:
			self.paths.add(str(id) + ".")
			print(str(id) + ".")

		allPaths = self.paths
		self.paths = set()

		return allPaths


	def recursiveAncestorsPath(self, advisors, treeString):
		"""
		Create all ancestors paths for the requested ID. Same IDs will be grabbed several times
		to ensure that all paths will be found.
		The paths will be created out of the advised-table. So, this part doesn't need online connectivity.
		"""
		for advisor in advisors:
			nextAdvisors = self.createAdvisorSet(advisor)

			treeString = str(advisor) + "." + treeString

			if len(nextAdvisors) > 0:
				self.recursiveAncestorsPath(nextAdvisors, treeString)

				# We have to delete the last node from the string because we are following another path now
				treeString = treeString.split(".", 1)[1]

			else:
				# If we reach the highest ancestor, then store this string!
				self.paths.add(treeString + ".")
				print(treeString + ".")

				# We have to delete the last node from the string because we are following another path now
				treeString = treeString.split(".", 1)[1]


	def recursiveDescendantsPath(self, students, treeString):
		"""
		Create all descendants paths for the requested ID. Same IDs will be grabbed several times
		to ensure that all paths will be found.
		The paths will be created out of the advised-table. So, this part doesn't need online connectivity.
		"""
		for student in students:
			nextStudents = self.createStudentSet(student)

			treeString = treeString + "." + str(student)

			if len(nextStudents) > 0:
				self.recursiveDescendantsPath(nextStudents, treeString)

				# We have to delete the last node from the string because we are following another path now
				treeString = treeString.rsplit(".", 1)[0]

			else:
				# If we reach the highest ancestor, then store this string!
				self.paths.add(treeString + ".")
				print(treeString + ".")

				# We have to delete the last node from the string because we are following another path now
				treeString = treeString.rsplit(".", 1)[0]