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


    def connectToDatabase(self):
        if self.connection == None:
            try:
                self.connection = sqlite3.connect("MG-DB")
                self.cursor = self.connection.cursor()

                self.cursor.execute("CREATE TABLE IF NOT EXISTS mathematician (id INTEGER PRIMARY KEY ASC ON CONFLICT REPLACE, name TEXT, university TEXT, year INTEGER, dissertation TEXT, descendants INTEGER)")    
                self.cursor.execute("CREATE TABLE IF NOT EXISTS advised (idAdvisor INTEGER UNIQUE ON CONFLICT IGNORE, idStudent INTEGER UNIQUE ON CONFLICT IGNORE, advisorOrder INTEGER)")
 
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
                grabber = grab.Grabber(id)
                [name, uni, year, advisors, students] = grabber.extractNodeInformation()
                print "ID: {0}  Name: {1}  University: {2}  Year: {3}".format(id, name, uni, year)
                self.updateByName(id, name, uni, year, advisors)
    
        else:
            print "There is no mathematician in the online-database with that entered last name."


    def naiveUpdate(self, id, name, uni, year, advisors):
        self.cursor.execute("INSERT OR REPLACE INTO mathematician VALUES (?, ?, ?, ?, ?, ?)",  (id, name, uni, year, None, None))
        
        for advID in advisors:
            self.cursor.execute("INSERT OR REPLACE INTO advised VALUES (?, ?, ?)",  (advID, id, None))
            self.connection.commit()


    def updateByName(self, id, name, uni, year, advisors):
        self.connectToDatabase()
        
        if self.naiveMode:
            self.naiveUpdate(id, name, uni, year, advisors)
            
        else:    
            self.cursor.execute("SELECT id from mathematician WHERE id=?", (id,))
            tempList = self.cursor.fetchall()

            if len(tempList) == 0:
                self.naiveUpdate(id, name, uni, year, advisors)


    def updateByID(self, id, ancestors, descendants):
        try:
            grabber = grab.Grabber(id)
            print "Grabbing record #%d" % (id)
            [name, uni, year, advisors, students] = grabber.extractNodeInformation()

        except ValueError:
            # The given id does not exist in the Math Genealogy Project's database.
            raise
        
        self.connectToDatabase()
        
        if self.naiveMode:
            self.naiveUpdate(id, name, uni, year, advisors)
            
        #else:
            
        

#self.cursor.execute("SELECT name from mathematician")
#for row in self.cursor:
#    print row