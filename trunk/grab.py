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


import urllib2
import time
import htmlentitydefs
import re


class Grabber:
	"""
	Class for grabbing and parsing mathematician information from
	Math Genealogy Project.
	"""
	def __init__(self, id):
		self.id = id
		self.pagestr = None
		self.name = None
		self.numberOfDescendants = None
		self.institution = []
		self.year = []
		self.dissertation = []
		self.advisors = []
		self.descendants = set()

		# Break to avoid the risk of being blocked.
		time.sleep(0.4)


	@staticmethod
	def unescape(s):
		"""
		Example: "ae" in html-code is displayed as "&auml;" This needs to be converted
				 back to "ae". That's the purpose of this function.
		"""
		return re.sub('&(%s);' % '|'.join(htmlentitydefs.name2codepoint),
					  lambda m: unichr(htmlentitydefs.name2codepoint[m.group(1)]), s)


	def getPage(self):
		"""
		Grab the page for self.id from the Math Genealogy Project.
		"""
		url = 'http://genealogy.math.ndsu.nodak.edu/id.php?id=' + str(self.id)
		page = urllib2.urlopen(url)
		self.pagestr = page.read()
		self.pagestr = self.pagestr.decode('utf-8')


	def extractNodeInformation(self):
		"""
		For the mathematician in this object, extract the list of
		advisor ids, the mathematician name, the mathematician
		institution, and the year of the mathematician's degree.
		Institution, year and dissertation are also lists as several
		dissertations per mathematician are possible.
		Year stores a text and not an integer as several years per
		dissertation are possible.
		"""
		self.getPage()

		errorCounter = 0

		# Split the page string at newline characters.
		psarray = self.pagestr.split('\n')

		while psarray[0].find("You have specified an ID that does not exist in the database.\
							  Please back up and try again.") > -1:
			errorCounter += 1
			time.sleep(5)
			self.getPage()
			psarray = self.pagestr.split('\n')

			if errorCounter == 15:
				# Then a bad URL (e.g., a bad record id) was given. Throw an exception.
				msg = "Invalid page address for id %d" % (self.id)
				raise ValueError(msg)

		lines = iter(psarray)

		for line in lines:
			# Get name
			if line.find('h2 style=') > -1:
				line = next(lines)
				self.name = self.unescape(line.split('</h2>')[0].strip())

			# Get year and university
			if '#006633; margin-left: 0.5em">' in line:
				inst_year = line.split('#006633; margin-left: 0.5em">')[1].split("</span>")[:2]
				self.institution.append(self.unescape(inst_year[0].strip()))
				self.year.append(self.unescape(inst_year[1].strip()))

				if len(self.institution[len(self.institution)-1]) == 0:
					self.institution[len(self.institution)-1] = None
				if len(self.year[len(self.year)-1]) == 0:
					self.year[len(self.year)-1] = None

			# Get dissertation title
			if line.find('thesisTitle') > -1:
				line = next(lines)
				line = next(lines)
				self.dissertation.append(self.unescape(line.split('</span></div>')[0].strip()))
				if len(self.dissertation[len(self.dissertation)-1]) == 0:
					self.dissertation[len(self.dissertation)-1] = None

			# Get all advisors
			if 'Advisor' in line:
				advisorLine = line

				# Mark next set of advisors
				if (len(self.institution) > 1) and ('a href=\"id.php?id=' in line):
					self.advisors.append(0)

				while 'Advisor' in advisorLine:
					if 'a href=\"id.php?id=' in line:
						# Extract link to advisor page.
						advisor_id = int(advisorLine.split('a href=\"id.php?id=')[1].split('\">')[0])
						self.advisors.append(advisor_id)
						# Split at advisor_id is unstable as advisorLine contains also numbers.
						advisorLine = advisorLine.split("id=" + str(advisor_id))[1]
					else:
						# We are done. Adjust string to break the loop.
						# (Without this records with no advisor enter an infinite loop.)
						advisorLine = ""

			# Get students
			if '<tr ' in line:
				descendant_id = int(line.split('a href=\"id.php?id=')[1].split('\">')[0])
				self.descendants.add(descendant_id)

			# Get number of descendants
			# Uses only '</a> and ' as search string and not '>students</a> and '
			# because 'students' can change to 'student' !
			if 'According to our current on-line database' in line:
				self.numberOfDescendants = int(line.split('</a> and ')[1].split(' <a href=')[0])

			if 'No students known.' in line:
				self.numberOfDescendants = 0

			if 'If you have additional information or' in line:
				break

		return [self.name, self.institution, self.year, self.advisors, self.descendants,
				self.dissertation, self.numberOfDescendants]