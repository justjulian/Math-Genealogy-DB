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
            # Get name
            self.cursor.execute("SELECT name from mathematician WHERE id=?", (id,))
            row = self.cursor.fetchone()
            name = row["name"]
            
            # Get dissertation, university and year
            # Only information of one dissertation will be printed
            self.cursor.execute("SELECT university, year from dissertation WHERE id=?", (id,))
            row = self.cursor.fetchone()
            uni = row["university"]
            year = row["year"]
    
            # Merge everything to a string and add to DOT-file
            nodeStr = "    {} [label=\"{} \n{} {}\"];".format(id, name, uni, year)
            dotFile += nodeStr
        
            # Get relationship and store it to add it at the end of the
            # DOT-file when exiting this loop.
            self.cursor.execute("SELECT idStudent from advised WHERE idAdvisor=?", (id,))
            students = self.cursor.fetchall()
            
            for student in students:
                # Merge everything to a string
                edgeStr = "\n    {} -> {};".format(id, student["idStudent"])
                edges += edgeStr
            
            dotFile += "\n"

        # Now print the connections between the nodes.
        dotFile += edges
        dotFile += "\n}\n"
        
        return dotfile