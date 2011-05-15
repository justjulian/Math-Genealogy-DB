import sqlite3
import grab

connection = sqlite3.connect("MGDB")
cursor = connection.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS mathematicians (mathID INTEGER, mathName TEXT, mathUni TEXT, mathYear INTEGER)")
cursor.execute("CREATE TABLE IF NOT EXISTS relationship (advisorID INTEGER, studentID INTEGER)")

connection.commit()

for i in range(1, 22):

    id = i
    grabber = grab.Grabber(id)

    cursor.execute("SELECT mathID from mathematicians WHERE mathID=?", (id, ))
    tempList = cursor.fetchall()

    if len(tempList) == 0:

        try:
            print "Grabbing record #%d" % (id)
            [name, uni, year, advisors, students] = grabber.extractNodeInformation()
            cursor.execute("INSERT INTO mathematicians VALUES (?, ?, ?, ?)",  (id,  name,  uni,  year))
        
            for advID in advisors:
                cursor.execute("INSERT INTO relationship VALUES (?, ?)",  (advID,  id))
                
            connection.commit()

        except ValueError:
            # The given id does not exist in the Math Genealogy Project's database.
            raise

cursor.execute("SELECT mathName from mathematicians")
for row in cursor:
    print row
