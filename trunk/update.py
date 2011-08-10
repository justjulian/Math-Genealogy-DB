import sqlite3
import grab
import urllib.request, urllib.parse, urllib.error



class Updater:
    """
    Class for finding the ID of a mathematician and updating it 
    from the Mathematics Genealogy Project.
    """
    def __init__(self, naive):
        self.foundID = False
        self.foundIDs = []
        self.connection = None
        self.cursor = None
        self.naiveMode = naive
        self.currentAdvisorsGrab = []
        self.currentStudentsGrab = []


    def connectToDatabase(self):
        """
        Connect to the local database if not already connected.
        Create local database if it not already exists.
        """
        if self.connection == None:
            try:
                self.connection = sqlite3.connect("MG-DB")
                # Use sqlite3.Row to enable direct access to the stored data of the table.
                self.connection.row_factory = sqlite3.Row
                self.cursor = self.connection.cursor()

                self.cursor.execute("CREATE TABLE IF NOT EXISTS mathematician \
                                    (id INTEGER PRIMARY KEY ASC ON CONFLICT REPLACE, name TEXT, descendants INTEGER)")    
                self.cursor.execute("CREATE TABLE IF NOT EXISTS advised \
                                    (idAdvisor INTEGER, idStudent INTEGER, advisorOrder INTEGER, \
                                    UNIQUE (idAdvisor, idStudent, advisorOrder) ON CONFLICT IGNORE)")
                self.cursor.execute("CREATE TABLE IF NOT EXISTS dissertation \
                                    (id INTEGER, title TEXT, university TEXT, year TEXT, \
                                    UNIQUE (id, title) ON CONFLICT IGNORE)")
 
                self.connection.commit()
    
            except sqlite3.Error:
                print("Can neither create local database nor connect with an existing one!")
                raise


    def findID(self, lastName):
        """
        Find the corresponding ID of a mathematician listed in the
        Mathematics Genealogy Project. This ID is needed to run Update-by-ID.
        """
        page = urllib.request.urlopen("http://genealogy.math.ndsu.nodak.edu/query-prep.php", \
                                      urllib.parse.urlencode({"family_name":lastName}).encode())
        pagestr = page.read()
        pagestr = pagestr.decode("utf-8")

        # Split the page string at newline characters
        psarray = pagestr.split("\n")

        for line in psarray:
            if 'a href=\"id.php?id=' in line:
                # Store if there are mathematicians with that entered last name
                self.foundID = True
        
                # Extract ID of found mathematicians
                id = int(line.split('a href=\"id.php?id=')[1].split('\">')[0])
                self.foundIDs.append(id)

        if self.foundID:
            # Print every found mathematician and store them in the local database
            for id in self.foundIDs:
                [name, uni, year, advisors, students, dissertation, numberOfDescendants] = self.grabNode(id)
                print("ID: {}  Name: {}  University: {}  Year: {}".format(id, name, uni[0], year[0]))
                self.updateByName(id, name, uni, year, advisors, dissertation, numberOfDescendants)
    
        else:
            print("There is either no mathematician in the online-database with that entered last name or there are too many. \
                   You can check http://genealogy.math.ndsu.nodak.edu/search.php though and try to find the desired mathematician \
                   by using more search options. You can then use the ID of this mathematician to run Update-by-ID.")


    def naiveUpdate(self, id, name, unis, years, advisors, dissertations, numberOfDescendants):
        """
        Take the arguments and update all three tables of the local database.
        Replace existing entries.
        """
        self.cursor.execute("INSERT OR REPLACE INTO mathematician VALUES (?, ?, ?)",  (id, name, numberOfDescendants))
        self.connection.commit()
        
        advOrder = 0
        
        iterAdvisor = iter(advisors)
        
        for advID in iterAdvisor:
            # If advisors are separated by 0, then a new set of advisors starts
            # which means, that there is also another dissertation
            # Hence, the order must be reseted and the next advisors must be grabbed
            if advID == 0:
                advOrder = 0
                advID = next(iterAdvisor)
                
            advOrder += 1
            self.cursor.execute("INSERT OR REPLACE INTO advised VALUES (?, ?, ?)",  (advID, id, advOrder))
            self.connection.commit()    
            
        iterUni = iter(unis)
        iterYear = iter(years)    
        
        # Lists dissertation, uni and year have the same length. The items are either set or None.
        # Hence, iterating one of them is enough to avoid range errors.    
        for dissertation in dissertations:
            uni = next(iterUni)
            year = next(iterYear)
            
            self.cursor.execute("INSERT OR REPLACE INTO dissertation VALUES (?, ?, ?, ?)",  (id, dissertation, uni, year))
            self.connection.commit()


    def updateByName(self, id, name, uni, year, advisors, dissertation, numberOfDescendants):
        """
        Run naive update if naive mode is set.
        Check weather the entry already exists in the local database, if naive mode wasn't set.
        """
        self.connectToDatabase()
        
        if self.naiveMode:
            self.naiveUpdate(id, name, uni, year, advisors, dissertation, numberOfDescendants)
            
        else:    
            self.cursor.execute("SELECT id from mathematician WHERE id=?", (id,))
            tempList = self.cursor.fetchall()

            # If the returned list is empty, then the mathematician isn't in the local
            # database and it need to be updated.
            if len(tempList) == 0:
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
                print("Grabbing record #{}".format(id))
                
            [name, uni, year, advisors, students, dissertation, numberOfDescendants] = grabber.extractNodeInformation()

        except ValueError:
            # The given id does not exist in the Math Genealogy Project.
            raise
        
        return [name, uni, year, advisors, students, dissertation, numberOfDescendants]


    def recursiveAncestors(self, advisors):
        for advisor in advisors:
            if advisor == 0:
                continue
            
            [name, uni, year, nextAdvisors, nextStudents, dissertation, numberOfDescendants] = self.grabNode(advisor)
            self.currentAdvisorsGrab.append(advisor)
            
            # Not possible for ancestors as the number of all ancestors isn't stored.
            #self.cursor.execute("SELECT id, descendants from mathematician WHERE id=?", (advisor,))
            #tempList = self.cursor.fetchall()
            
            #if not self.naiveMode and len(tempList) == 1 and tempList[0]["descendants"] == numberOfDescendants:
            #    return
            
            self.naiveUpdate(advisor, name, uni, year, nextAdvisors, dissertation, numberOfDescendants)
            ungrabbedAdvisors = []

            if len(nextAdvisors) > 0:
                for nextAdvisor in nextAdvisors:
                    if nextAdvisor not in self.currentAdvisorsGrab:
                        ungrabbedAdvisors.append(nextAdvisor)
                        
                self.recursiveAncestors(ungrabbedAdvisors)


    def recursiveDescendants(self, students):
        for student in students:
            [name, uni, year, nextAdvisors, nextStudents, dissertation, numberOfDescendants] = self.grabNode(student)
            self.currentStudentsGrab.append(student)
            
            self.cursor.execute("SELECT id, descendants from mathematician WHERE id=?", (student,))
            tempList = self.cursor.fetchall()
            
            if not self.naiveMode and len(tempList) == 1 and tempList[0]["descendants"] == numberOfDescendants:
                return
            
            self.naiveUpdate(student, name, uni, year, nextAdvisors, dissertation, numberOfDescendants)
            ungrabbedStudents = []

            if len(nextStudents) > 0:
                for nextStudent in nextStudents:
                    if nextStudent not in self.currentStudentsGrab:
                        ungrabbedStudents.append(nextStudent)
                        
                self.recursiveDescendants(ungrabbedStudents)


    def updateByID(self, ids, ancestors, descendants):
        """
        Grab the given ID(s) and grab their ancestors and/or descendants.
        """
        self.connectToDatabase()
        
        for id in ids:
            [name, uni, year, advisors, students, dissertation, numberOfDescendants] = self.grabNode(id)
            self.naiveUpdate(id, name, uni, year, advisors, dissertation, numberOfDescendants)
            
            if ancestors:
                self.recursiveAncestors(advisors)
                    
            if descendants:
                self.recursiveDescendants(students)


#self.cursor.execute("SELECT name from mathematician")
#for row in self.cursor:
#    print row