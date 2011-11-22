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



class Visualizer:
	"""
	Class for generating DOT-files to answer the search queries.
	"""
	def __init__(self, connector, details):
		self.connection = connector[0]
		self.cursor = connector[1]

		self.noDetails = details


	def createNodeStr(self, color, id):
		# Get name
		self.cursor.execute("SELECT name FROM person WHERE pID=?", (id,))
		row = self.cursor.fetchone()
		name = row["name"]
		name = name.replace("\"","\'")

		# Get dissertation, university and year
		# Only information of one dissertation will be printed
		self.cursor.execute("SELECT university, year FROM dissertation WHERE author=?", (id,))
		row = self.cursor.fetchone()
		uni = row["university"]
		year = row["year"]

		# Merge everything to a string and add to DOT-file
		if self.noDetails:
			nodeStr = u"    {} [label=\"{} ({})\", fontcolor={}, URL=\"http://www.google.com/#q={}\"];"\
			.format(id, name, year, color, name).encode('utf-8')

		else:
			nodeStr = u"    {} [label=\"{} \\n{} {}\", fontcolor={}, URL=\"http://www.google.com/#q={}\"];"\
			.format(id, name, uni, year, color, name).encode('utf-8')

		return nodeStr


	def createEdgeStr(self, color, id, blackSet, redSet):
		# Get relationship and store it to add it at the end of the
		# DOT-file when exiting this loop.
		self.cursor.execute("SELECT author FROM advised, dissertation WHERE student=dID AND advisor=?", (id,))
		students = self.cursor.fetchall()

		edges = ""

		for student in students:
			if redSet is not None and student["author"] in redSet:
				edgeStr = "\n    {} -> {} [color={}];".format(id, student["author"], color)
				edges += edgeStr

			elif blackSet is not None and student["author"] in blackSet:
				edgeStr = "\n    {} -> {} [color=black];".format(id, student["author"])
				edges += edgeStr

		return edges


	def generateDotFile(self, blackSet, redSet=None):
		edges = ""
		dotFile = ""
		dotFile += """digraph genealogy {
	graph [charset="utf-8"];
	node [shape=plaintext];
	edge [style=bold];\n\n"""

		if blackSet is not None:
			for id in blackSet:
				dotFile += self.createNodeStr("black", id)
				edge = self.createEdgeStr("black", id, blackSet, redSet)

				if edge != "":
					edges += edge

				dotFile += "\n"

		if redSet is not None:
			for id in redSet:
				dotFile += self.createNodeStr("red", id)
				edge = self.createEdgeStr("red", id, blackSet, redSet)

				if edge != "":
					edges += edge

				dotFile += "\n"

		# Now print the connections between the nodes.
		dotFile += edges
		dotFile += "\n}\n"

		return dotFile