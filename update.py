import sqlite3
import grab
import urllib



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
        if self.connection == None:
            try:
                self.connection = sqlite3.connect("MG-DB")
                self.cursor = self.connection.cursor()

                self.cursor.execute("CREATE TABLE IF NOT EXISTS mathematician (id INTEGER PRIMARY KEY ASC ON CONFLICT REPLACE, name TEXT, university TEXT, year INTEGER, dissertation TEXT, descendants INTEGER)")    
                self.cursor.execute("CREATE TABLE IF NOT EXISTS advised (idAdvisor INTEGER, idStudent INTEGER, advisorOrder INTEGER, UNIQUE (idAdvisor, idStudent) ON CONFLICT IGNORE)")
 
                self.connection.commit()
    
            except sqlite3.Error:
                print "Can neither create local database nor connect with an existing one!"
                raise


    def findID(self, lastName):
        page = urllib.urlopen("http://genealogy.math.ndsu.nodak.edu/query-prep.php", urllib.urlencode({"family_name":lastName}))
        pagestr = page.read()
        pagestr = pagestr.decode("utf-8")

        # Split the page string at newline characters.
        psarray = pagestr.split("\n")

        for line in psarray:
            if 'a href=\"id.php?id=' in line:
                self.foundID = True
        
                # Extract ID of found mathematicians.
                id = int(line.split('a href=\"id.php?id=')[1].split('\">')[0])
                self.foundIDs.append(id)

        if self.foundID:
            for id in self.foundIDs:
                [name, uni, year, advisors, students, dissertation, numberOfDescendants] = self.grabNode(id)
                print "ID: {0}  Name: {1}  University: {2}  Year: {3}".format(id, name, uni, year)
                self.updateByName(id, name, uni, year, advisors, dissertation, numberOfDescendants)
    
        else:
            print "There is no mathematician in the online-database with that entered last name."


    def naiveUpdate(self, id, name, uni, year, advisors, dissertation, numberOfDescendants):
        self.cursor.execute("INSERT OR REPLACE INTO mathematician VALUES (?, ?, ?, ?, ?, ?)",  (id, name, uni, year, dissertation, numberOfDescendants))
        advOrder = 0
        
        for advID in advisors:
            advOrder += 1
            self.cursor.execute("INSERT OR REPLACE INTO advised VALUES (?, ?, ?)",  (advID, id, advOrder))
            self.connection.commit()


    def updateByName(self, id, name, uni, year, advisors, dissertation, numberOfDescendants):
        self.connectToDatabase()
        
        if self.naiveMode:
            self.naiveUpdate(id, name, uni, year, advisors, dissertation, numberOfDescendants)
            
        else:    
            self.cursor.execute("SELECT id from mathematician WHERE id=?", (id,))
            tempList = self.cursor.fetchall()

            if len(tempList) == 0:
                self.naiveUpdate(id, name, uni, year, advisors, dissertation, numberOfDescendants)


    def grabNode(self, id):
        try:
            grabber = grab.Grabber(id)

            if not self.foundID:
                print "Grabbing record #%d" % (id)
                
            [name, uni, year, advisors, students, dissertation, numberOfDescendants] = grabber.extractNodeInformation()

        except ValueError:
            # The given id does not exist in the Math Genealogy Project's database.
            raise
        
        return [name, uni, year, advisors, students, dissertation, numberOfDescendants]


    def recursiveAncestors(self, advisors):
        for advisor in advisors:
            [name, uni, year, nextAdvisors, nextStudents, dissertation, numberOfDescendants] = self.grabNode(advisor)
            self.currentAdvisorsGrab.append(advisor)
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
            self.naiveUpdate(student, name, uni, year, nextAdvisors, dissertation, numberOfDescendants)

            ungrabbedStudents = []

            if len(nextStudents) > 0:
                for nextStudent in nextStudents:
                    if nextStudent not in self.currentStudentsGrab:
                        ungrabbedStudents.append(nextStudent)
                        
                self.recursiveDescendants(ungrabbedStudents)


    def updateByID(self, ids, ancestors, descendants):
        self.connectToDatabase()
        
        for id in ids:
            [name, uni, year, advisors, students, dissertation, numberOfDescendants] = self.grabNode(id)
        
            if self.naiveMode:
                self.naiveUpdate(id, name, uni, year, advisors, dissertation, numberOfDescendants)
            
                if ancestors:
                    self.recursiveAncestors(advisors)
                    
                if descendants:
                    self.recursiveDescendants(students)
            
            #else:
                # Smart Update


#self.cursor.execute("SELECT name from mathematician")
#for row in self.cursor:
#    print row