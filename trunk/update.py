import sqlite3
import grab

connection = sqlite3.connect("MGDB")
cursor = connection.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS mathematicians (id INTEGER, name TEXT, uni TEXT, year INTEGER)")
cursor.execute("CREATE TABLE IF NOT EXISTS relationship (advisorID INTEGER, studentID INTEGER)")

connection.commit()

for i in range(1, 22):

    ID = i
    grabber = grab.Grabber(ID)

    cursor.execute("SELECT id from mathematicians WHERE id=?", (ID, ))
    tempList = cursor.fetchall()

    if len(tempList) == 0:

        try:
            print "Grabbing record #%d" % (ID)
            [name, uni, year, advisors, students] = grabber.extractNodeInformation()
            cursor.execute("INSERT INTO mathematicians VALUES (?, ?, ?, ?)",  (id,  name,  uni,  year))
        
            for advID in advisors:
                cursor.execute("INSERT INTO relationship VALUES (?, ?)",  (advID,  ID))
                
            connection.commit()

        except ValueError:
            # The given id does not exist in the Math Genealogy Project's database.
            raise

cursor.execute("SELECT name from mathematicians")
for row in cursor:
    print row