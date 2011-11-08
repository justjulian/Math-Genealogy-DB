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
import databaseConnection



class Searcher:
	"""
	Class for several search methods.
	"""
	def __init__(self, filename, details):
		self.paths = []
		self.lcaPath = []
		self.filename = filename
		self.noDetails = details
		self.maxPrefix = 0
		self.lcaMode = False

		self.descendantsSet = set()
		self.descendantsList = []

		self.ancestorsSet = set()
		self.ancestorsList = []

		self.completeLCAList = []

		databaseConnector = databaseConnection.DatabaseConnector()
		connector = databaseConnector.connectToSQLite()
		self.connection = connector[0]
		self.cursor = connector[1]


	def saveDotFile(self, queryName, rootID, visList):
		self.cursor.close()
		self.connection.close()

		visualizer = visualize.Visualizer(self.noDetails)
		dotFile = visualizer.generateDotFile(visList)

		if self.filename is not None:
			id = str(rootID)
			query = open(self.filename + id + queryName + ".dot", "w")
			print(dotFile, file=query)
			query.close()

		else:
			print(dotFile)

		databaseConnector = databaseConnection.DatabaseConnector()
		connector = databaseConnector.connectToSQLite()
		self.connection = connector[0]
		self.cursor = connector[1]


	def allAncestors(self, id):
		id = id[0]
		self.ancestorsList.append(id)

		self.cursor.execute("SELECT advisor FROM advised WHERE student=?", (id,))
		tempList = self.cursor.fetchall()
		advisors = []

		for row in tempList:
			advisors.append(row["advisor"])

		if len(advisors) > 0:
			self.recursiveAncestors(False, advisors)

		if not self.lcaMode:
			if len(self.ancestorsList) < 2:
				print("There are no ancestors!")

			else:
				print("The ancestors of", id, "are", self.ancestorsList)
				self.ancestorsList = [self.ancestorsList]
				self.saveDotFile("AllAncestors", id, self.ancestorsList)

		else:
			self.completeLCAList.append(self.ancestorsList)

		self.ancestorsSet = set()
		self.ancestorsList = []


	def allDescendants(self, id):
		id = id[0]
		self.descendantsList.append(id)

		self.cursor.execute("SELECT student FROM advised WHERE advisor=?", (id,))
		tempList = self.cursor.fetchall()
		students = []

		for row in tempList:
			students.append(row["student"])

		if len(students) > 0:
			self.recursiveDescendants(False, students)

		if not self.lcaMode:
			if len(self.descendantsList) < 2:
				print("There are no descendants!")

			else:
				print("The descendants of", id, "are", self.descendantsList)
				self.descendantsList = [self.descendantsList]
				self.saveDotFile("AllDescendants", id, self.descendantsList)

		else:
			self.completeLCAList.append(self.descendantsList)

		self.descendantsSet = set()
		self.descendantsList = []


	def recursiveAncestors(self, useSet, advisors):
		for advisor in advisors:
			if useSet:
				# Sets don't allow double entries and are faster than lists but can't iterate.
				self.ancestorsSet.add(advisor)

			else:
				# Used for search method "all ancestors". In this mode we don't need to
				# worry about double entries as the visualization module deletes them anyway.
				self.ancestorsList.append(advisor)

			self.cursor.execute("SELECT advisor FROM advised WHERE student=?", (advisor,))
			tempList = self.cursor.fetchall()
			nextAdvisors = []

			for row in tempList:
				nextAdvisors.append(row["advisor"])

			ungrabbedAdvisors = []

			if len(nextAdvisors) > 0:
				for nextAdvisor in nextAdvisors:
					if useSet:
						if nextAdvisor not in self.ancestorsSet:
							ungrabbedAdvisors.append(nextAdvisor)

					else:
						if nextAdvisor not in self.ancestorsList:
							ungrabbedAdvisors.append(nextAdvisor)

				self.recursiveAncestors(useSet, ungrabbedAdvisors)


	def numberOfDescendants(self, students):
		self.recursiveDescendants(True, students)

		return len(self.descendantsSet)


	def recursiveDescendants(self, useSet, students):
		for student in students:
			if useSet:
				# Sets don't allow double entries and are faster than lists but can't iterate.
				self.descendantsSet.add(student)

			else:
				# Used for search method "all descendants". In this mode we don't need to
				# worry about double entries as the visualization module deletes them anyway.
				self.descendantsList.append(student)

			self.cursor.execute("SELECT student FROM advised WHERE advisor=?", (student,))
			tempList = self.cursor.fetchall()
			nextStudents = []

			for row in tempList:
				nextStudents.append(row["student"])

			ungrabbedStudents = []

			if len(nextStudents) > 0:
				for nextStudent in nextStudents:
					if useSet:
						if nextStudent not in self.descendantsSet:
							ungrabbedStudents.append(nextStudent)

					else:
						if nextStudent not in self.descendantsList:
							ungrabbedStudents.append(nextStudent)

				self.recursiveDescendants(useSet, ungrabbedStudents)


	def generatePathOf(self, id):
		print("Updating path of #", id)

		self.cursor.execute("SELECT advisor FROM advised WHERE student=?", (id,))
		tempList = self.cursor.fetchall()
		nextAdvisors = []

		for row in tempList:
			nextAdvisors.append(row["advisor"])

		if len(nextAdvisors) > 0:
			self.recursiveAncestorsPath(nextAdvisors, str(id))

		else:
			self.paths.append(str(id) + ".")
			print(str(id) + ".")

		allPaths = self.paths
		self.paths = []

		return allPaths


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
			lca = id1
			splitLcaPath = []

			for singleLCA in lca:
				for path in self.lcaPath:
					tempPath = path.split(str(singleLCA) + '.')

					if len(tempPath) > 1 and not tempPath[1] == "":
						splitLcaPath += tempPath[1].split('.')

			for id in ids:
				self.allAncestors([id])
				self.allDescendants([id])

			coloredList = []
			coloredList.append(['red'])
			coloredList.append(lca)
			coloredList.append(splitLcaPath)
			coloredList.append(['black'])

			for singleList in self.completeLCAList:
				coloredList.append(singleList)

			for singleLCA in lca:
				self.cursor.execute("SELECT name FROM person WHERE pid=?", (singleLCA,))
				lcaName = self.cursor.fetchone()
				print("The LCA with", self.maxPrefix, "common ancestors is", singleLCA, ":", lcaName["name"])

			self.saveDotFile("LCA", lca[0], coloredList)

		self.lcaMode = False


	def recursiveLCA(self, idSet, id2):
		path2 = self.generatePathOf(id2)
		templcaPath = []
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

								templcaPath.append(row1)
								templcaPath.append(row2)

							if prefix > self.maxPrefix:
								lca = []
								templcaPath = []

								lca.append(int(singlePathID1))
								templcaPath.append(row1)
								templcaPath.append(row2)
								self.maxPrefix = prefix

						else:
							break

		for row in templcaPath:
			self.lcaPath.append(row)

		return lca


	def recursiveAncestorsPath(self, advisors, treeString):
		"""
		Create all ancestors paths for the requested ID. Same IDs will be grabbed several times
		to ensure that all paths will be found.
		The paths will be created out of the advised-table. So, this part doesn't need online connectivity.
		"""
		for advisor in advisors:
			self.cursor.execute("SELECT advisor FROM advised WHERE student=?", (advisor,))
			tempList = self.cursor.fetchall()
			nextAdvisors = []

			for row in tempList:
				nextAdvisors.append(row["advisor"])

			treeString = str(advisor) + "." + treeString

			if len(nextAdvisors) > 0:
				self.recursiveAncestorsPath(nextAdvisors, treeString)
				# We have to delete the last node from the string because we are following another path now
				treeString = treeString.split(".", 1)[1]

			else:
				# If we reach the highest ancestor, then store this string!
				self.paths.append(treeString + ".")
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
			self.cursor.execute("SELECT student FROM advised WHERE advisor=?", (student,))
			tempList = self.cursor.fetchall()
			nextStudents = []

			for row in tempList:
				nextStudents.append(row["student"])

			treeString = treeString + "." + str(student)

			if len(nextStudents) > 0:
				self.recursiveDescendantsPath(nextStudents, treeString)
				# We have to delete the last node from the string because we are following another path now
				treeString = treeString.rsplit(".", 1)[0]

			else:
				# If we reach the highest ancestor, then store this string!
				self.paths.append(treeString + ".")
				print(treeString + ".")
				# We have to delete the last node from the string because we are following another path now
				treeString = treeString.rsplit(".", 1)[0]