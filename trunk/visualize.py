import sqlite3



class Visualize:
    """
    Class for generating DOT-files to answer the search queries.
    """
    def __init__(self):
        try:
            self.connection = sqlite3.connect("MG-DB")
            self.connection.row_factory = sqlite3.Row
            self.cursor = self.connection.cursor()
    
        except sqlite3.Error:
            print("Can't connect with local database. Please run update first!")
            raise
        
        
    def generateDotFile(self, printIDs):
        edges = ""
        dotFile = ""
        dotFile += """digraph genealogy {
    graph [charset="utf-8"];
    node [shape=plaintext];
    edge [style=bold];\n\n"""
    
        for id in printIDs:
            self.cursor.execute("SELECT name from mathematician WHERE id=?", (id,))
            row = self.cursor.fetchone()
            name = row["name"]
            
            # Only data of one dissertation will be printed
            self.cursor.execute("SELECT university, year from dissertation WHERE id=?", (id,))
            row = self.cursor.fetchone()
            uni = row["university"]
            year = row["year"]
    
            nodeStr = "    {} [label=\"{} \n{} {}\"];".format(id, name, uni, year)
            dotFile += nodeStr
        
            self.cursor.execute("SELECT idStudent from advised WHERE idAdvisor=?", (id,))
            students = self.cursor.fetchall()
            
            for student in students:
                edgeStr = "\n    {} -> {};".format(id, student["idStudent"])
                edges += edgeStr
            
            dotFile += "\n"

        # Now print the connections between the nodes.
        dotFile += edges
        dotFile += "\n}\n"
        
        return dotfile