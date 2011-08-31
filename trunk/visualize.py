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


import databaseConnection



class Visualizer:
    """
    Class for generating DOT-files to answer the search queries.
    """
    def __init__(self):
        databaseConnector = databaseConnection.DatabaseConnector()
        connector = databaseConnector.connectToSQLite()
        self.connection = connector[0]
        self.cursor = connector[1]
        
        
    def generateDotFile(self, printIDs):
        printedIDs = []
        edges = ""
        dotFile = ""
        dotFile += """digraph genealogy {
    graph [charset="utf-8"];
    node [shape=plaintext];
    edge [style=bold];\n\n"""
    
        for id in printIDs:
            try:
                id = int(id)
                
            except ValueError:
                continue
            
            if id not in printedIDs:
                printedIDs.append(id)
            
                # Get name
                self.cursor.execute("SELECT name FROM person WHERE pid=?", (id,))
                row = self.cursor.fetchone()
                name = row["name"]
            
                # Get dissertation, university and year
                # Only information of one dissertation will be printed
                self.cursor.execute("SELECT university, year FROM dissertation WHERE did=?", (id,))
                row = self.cursor.fetchone()
                uni = row["university"]
                year = row["year"]
    
                # Merge everything to a string and add to DOT-file
                nodeStr = "    {} [label=\"{} \\n{} {}\"];".format(id, name, uni, year)
                dotFile += nodeStr
        
                # Get relationship and store it to add it at the end of the
                # DOT-file when exiting this loop.
                self.cursor.execute("SELECT student FROM advised WHERE advisor=?", (id,))
                students = self.cursor.fetchall()
            
                for student in students:
                    if str(student["student"]) in printIDs or student["student"] in printIDs:
                        # Merge everything to a string
                        edgeStr = "\n    {} -> {};".format(id, student["student"])
                        edges += edgeStr
            
                dotFile += "\n"

        # Now print the connections between the nodes.
        dotFile += edges
        dotFile += "\n}\n"
        
        self.cursor.close()
        self.connection.close()
        
        return dotFile