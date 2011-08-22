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


import grab
import databaseConnection
import urllib.request, urllib.parse, urllib.error



class Updater:
    """
    Class for finding the ID of a mathematician and updating it 
    from the Mathematics Genealogy Project.
    """
    def __init__(self, naive):
        self.foundID = False
        self.foundIDs = []
        self.naiveMode = naive
        self.currentAdvisorsGrab = []
        self.currentStudentsGrab = []
        
        databaseConnector = databaseConnection.DatabaseConnector()
        connector = databaseConnector.connectToSQLite()
        self.connection = connector[0]
        self.cursor = connector[1]


    def findID(self, lastName):
        """
        Find the corresponding ID of a mathematician listed in the
        Mathematics Genealogy Project. This ID is needed to run in Update-by-ID.
        """
        # Get the raw data of this site. Return an object of class 'http.client.HTTPResponse'
        page = urllib.request.urlopen("http://genealogy.math.ndsu.nodak.edu/query-prep.php", \
                                      urllib.parse.urlencode({"family_name":lastName}).encode())
        # Read the raw data and return an object of class 'bytes' (html-code)
        pagestr = page.read()
        # Convert bytes-string to readable UTF-8 html-code of class 'str'
        pagestr = pagestr.decode("utf-8")

        # Split the page string at newline characters to get single lines.
        psarray = pagestr.split("\n")

        # Iterate through every line of the html-code.
        for line in psarray:
            if 'a href=\"id.php?id=' in line:
                # Store if there are mathematicians with that entered last name.
                self.foundID = True
        
                # Extract ID of found mathematicians.
                id = int(line.split('a href=\"id.php?id=')[1].split('\">')[0])
                self.foundIDs.append(id)

        if self.foundID:
            # Print every found mathematician and store them in the local database.
            for id in self.foundIDs:
                [name, uni, year, advisors, students, dissertation, numberOfDescendants] = self.grabNode(id)
                print("ID: {}  Name: {}  University: {}  Year: {}".format(id, name, uni[0], year[0]))
                self.updateByName(id, name, uni, year, advisors, dissertation, numberOfDescendants)
    
        else:
            print("There is either no mathematician in the online-database with that entered last name or there are too many. \
                   You can check http://genealogy.math.ndsu.nodak.edu/search.php though and try to find the desired mathematician \
                   by using more search options. You can then use the ID of this mathematician to run Update-by-ID.")
            
        self.cursor.close()
        self.connection.close()


    def naiveUpdate(self, id, name, unis, years, advisors, dissertations, numberOfDescendants):
        """
        Take the arguments and update or create the tables mathematicians, advised and dissertation
        of the local database.
        Replace existing mathematician.
        """
        self.cursor.execute("INSERT INTO person VALUES (?, ?, ?)",  (id, name, numberOfDescendants))
        
        advOrder = 0
        
        # Create iterator to be able to use "advID = next(iterAdvisor)".
        iterAdvisor = iter(advisors)
        
        for advID in iterAdvisor:
            # If advisors are separated by 0, then a new set of advisors starts
            # which means, that there is also another dissertation.
            # Hence, the order must be reseted and the next advisors must be grabbed.
            if advID == 0:
                advOrder = 0
                advID = next(iterAdvisor)
                
            advOrder += 1
            self.cursor.execute("INSERT INTO advised VALUES (?, ?, ?)",  (id, advOrder, advID))
        
        # Create iterators again.    
        iterUni = iter(unis)
        iterYear = iter(years)    
        
        # Lists dissertation, uni and year have the same length. The items are either set or None.
        # Hence, iterating one of them is enough to avoid range errors.    
        for dissertation in dissertations:
            uni = next(iterUni)
            year = next(iterYear)
            
            self.cursor.execute("INSERT INTO dissertation VALUES (?, ?, ?, ?)",  (id, dissertation, uni, year))
            
        self.connection.commit()


    def updateByName(self, id, name, uni, year, advisors, dissertation, numberOfDescendants):
        """
        Update or replace existing entries, depending on the "naive-mode".
        """
        if self.naiveMode:
            # Replace existing mathematician, delete the corresponding entries in the other tables
            # and store the new data.
            self.deleteRows(id)
            self.naiveUpdate(id, name, uni, year, advisors, dissertation, numberOfDescendants)
            
        else:
            # Replace existing mathematician and update the other tables but don't delete anything.
            self.naiveUpdate(id, name, uni, year, advisors, dissertation, numberOfDescendants)


    def grabNode(self, id):
        """
        Use the Grabber class to grab all stored information of a mathematician from
        the Mathematics Genealogy Project and return them.
        """
        try:
            grabber = grab.Grabber(id)

            # foundID indicates that the program runs in Update-by-Name mode. Following output
            # is disturbing in this mode.
            if not self.foundID:
                print("Grabbing record #", id)
                
            [name, uni, year, advisors, students, dissertation, numberOfDescendants] = grabber.extractNodeInformation()

        except ValueError:
            # The given id does not exist in the Math Genealogy Project.
            raise
        
        return [name, uni, year, advisors, students, dissertation, numberOfDescendants]


    def recursiveAncestors(self, advisors):
        """
        Take the advisor list and grab them recursively.
        Grabbed advisors will be stored in a separate list to avoid grabbing the same ID several times.
        """
        for advisor in advisors:
            # ID=0 just indicates that a new set of advisors begins here. ID=0 shouldn't be grabbed.
            if advisor == 0:
                continue
            
            [name, uni, year, nextAdvisors, nextStudents, dissertation, numberOfDescendants] = self.grabNode(advisor)
            self.currentAdvisorsGrab.append(advisor)
            
            # Smart update not possible for ancestors as the number of all ancestors isn't stored online.
            
            if self.naiveMode:
                self.deleteRows(advisor)
            
            self.naiveUpdate(advisor, name, uni, year, nextAdvisors, dissertation, numberOfDescendants)
            ungrabbedAdvisors = []

            if len(nextAdvisors) > 0:
                for nextAdvisor in nextAdvisors:
                    if nextAdvisor not in self.currentAdvisorsGrab:
                        ungrabbedAdvisors.append(nextAdvisor)
                        
                self.recursiveAncestors(ungrabbedAdvisors)


    def recursiveDescendants(self, students):
        """
        Take the student list and grab them recursively.
        Grabbed students will be stored in a separate list to avoid grabbing the same ID several times.
        """
        for student in students:
            [name, uni, year, nextAdvisors, nextStudents, dissertation, numberOfDescendants] = self.grabNode(student)
            self.currentStudentsGrab.append(student)
            
            # -----------------------------------------------------------------------------------------------------
            # TO-DO
            # Now: Compare local stored number of descendants with online stored number of descendants.
            # Should be: Compare online stored number of descendants with calculated number of descendants
            # given by the tables. First need smart way to calculate this number.
            # If numbers are equal, no mathematician has been added and no update is needed.
            self.cursor.execute("SELECT descendants FROM person WHERE pid=?", (student,))
            tempList = self.cursor.fetchall()
            
            if not self.naiveMode and len(tempList) == 1 and tempList[0]["descendants"] == numberOfDescendants:
                return
            # -----------------------------------------------------------------------------------------------------
            
            if self.naiveMode:
                self.deleteRows(student)
            
            self.naiveUpdate(student, name, uni, year, nextAdvisors, dissertation, numberOfDescendants)
            ungrabbedStudents = []

            if len(nextStudents) > 0:
                for nextStudent in nextStudents:
                    if nextStudent not in self.currentStudentsGrab:
                        ungrabbedStudents.append(nextStudent)
                        
                self.recursiveDescendants(ungrabbedStudents)


    def updateByID(self, ids, ancestors, descendants):
        """
        Grab the given ID(s) and grab their ancestors and/or descendants and update their paths.
        """
        for id in ids:
            if self.naiveMode:
                self.deleteRows(id)
            
            [name, uni, year, advisors, students, dissertation, numberOfDescendants] = self.grabNode(id)
            self.naiveUpdate(id, name, uni, year, advisors, dissertation, numberOfDescendants)
            
            if ancestors:
                self.recursiveAncestors(advisors)
                    
            if descendants:
                self.recursiveDescendants(students)
                
        self.cursor.close()
        self.connection.close()
        
        
    def deleteRows(self, id):
        self.cursor.execute("DELETE FROM person WHERE pid=?", (id,))
        self.cursor.execute("DELETE FROM advised WHERE student=?", (id,))
        self.cursor.execute("DELETE FROM dissertation WHERE did=?", (id,))
                
        self.connection.commit()