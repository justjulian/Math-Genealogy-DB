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


import sqlite3



class DatabaseConnector:
	"""
	Class for connecting with a database.
	"""
	def __init__(self):
		self.connection = None
		self.cursor = None


	def connectToSQLite(self, name):
		"""
		Connect to the local SQLite-database if not already connected.
		Create local database if it not already exists.
		"""
		if self.connection == None:
			try:
				self.connection = sqlite3.connect(name)

				# Use sqlite3.Row to enable direct access to the stored data of the table.
				self.connection.row_factory = sqlite3.Row
				self.cursor = self.connection.cursor()

				self.cursor.execute("CREATE TABLE IF NOT EXISTS person (\
									pID INTEGER PRIMARY KEY ON CONFLICT REPLACE, \
									name VARCHAR(255), \
									onlineDescendants INTEGER)")

				self.cursor.execute("CREATE TABLE IF NOT EXISTS dissertation (\
									dID INTEGER PRIMARY KEY ON CONFLICT REPLACE AUTOINCREMENT, \
									author INTEGER REFERENCES person ON DELETE SET NULL ON UPDATE CASCADE, \
									title TEXT, \
									university TEXT, \
									year VARCHAR(255))")

				self.cursor.execute("CREATE TABLE IF NOT EXISTS advised (\
									student INTEGER REFERENCES dissertation ON DELETE CASCADE ON UPDATE CASCADE, \
									advisorOrder INTEGER CHECK (advisorOrder > 0), \
					                advisor INTEGER REFERENCES person ON DELETE CASCADE ON UPDATE CASCADE, \
									PRIMARY KEY (student, advisor) ON CONFLICT REPLACE)")

				self.cursor.execute("CREATE TRIGGER IF NOT EXISTS delPerson AFTER DELETE ON dissertation FOR EACH ROW \
									BEGIN \
										DELETE FROM person WHERE OLD.author = pID; \
									END")

				self.connection.commit()

			except sqlite3.Error:
				print(u"Can neither create local database nor connect with an existing one!".encode('utf-8'))
				raise

		connector = [self.connection, self.cursor]
		return connector