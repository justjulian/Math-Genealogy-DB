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


import visualize
import databaseConnection



class Searcher:
    """
    Class for several search methods.
    """
    def __init__(self, filename):
        self.paths = []
        self.lcaPath = []
        self.filename = filename
        self.maxPrefix = 0
        
        databaseConnector = databaseConnection.DatabaseConnector()
        connector = databaseConnector.connectToSQLite()
        self.connection = connector[0]
        self.cursor = connector[1]
        
        
    def generatePathOf(self, id):
        print("Updating path of #", id)
        allPaths = []
            
        self.cursor.execute("SELECT advisor FROM advised WHERE student=?", (id,))
        tempList = self.cursor.fetchall()
        nextAdvisors = []
            
        for row in tempList:
            nextAdvisors.append(row["advisor"])
            
        if len(nextAdvisors) > 0:
            self.recursiveAncestorsPath(nextAdvisors, str(id))
            
        else:
            self.paths.append(str(id) + ".")
            print(str(id) + ".")
            
        allPaths = self.paths
        self.paths = []
        
        return allPaths
        
        
    def lca(self, ids):
        id1 = ids[0]
        
        for i in range(len(ids)-1):
            if id1 == None:
                break
            
            else:
                id1 = self.recursiveLCA(id1, ids[i+1])
            
        if id1 == None:
            print("There is no LCA!")
        
        else:
            lca = id1
            splitLcaPath = []
            
            self.cursor.execute("SELECT name FROM person WHERE pid=?", (lca,))
            lcaName = self.cursor.fetchone()
            
            for path in self.lcaPath:
                tempPath = path.split(str(lca) + '.')
                
                if len(tempPath) > 1 and not tempPath[1] == "":
                    splitLcaPath += tempPath[1].split('.')
            
            lcaIDs = [str(lca)] + splitLcaPath
            
            print("The LCA with", self.maxPrefix, "common ancestors is", lca, ":", lcaName["name"])
        
            self.cursor.close()
            self.connection.close()
        
            visualizer = visualize.Visualizer()
            dotFile = visualizer.generateDotFile(lcaIDs)
            
            if self.filename is not None:
                lcaQuery = open(self.filename + ".dot", "w")
                print(dotFile, file=lcaQuery)
                lcaQuery.close()
                
            else:
                print(dotFile)
            
        
    def recursiveLCA(self, id1, id2):
        lca = None
        
        path1 = self.generatePathOf(id1)
        path2 = self.generatePathOf(id2)
        
        lcaPath1 = None
        lcaPath2 = None
        
        self.maxPrefix = 0
            
        for row1 in path1:
            splitPath1 = row1.split('.')
                
            for row2 in path2:                    
                prefix = 0
                splitPath2 = row2.split('.')
                    
                if len(splitPath1) >= len(splitPath2):
                    longPathIter = iter(splitPath1)
                    shortPathIter = iter(splitPath2)
                        
                else:
                    longPathIter = iter(splitPath2)
                    shortPathIter = iter(splitPath1)
                    
                for singlePathID1 in shortPathIter:
                    singlePathID2 = next(longPathIter)
                        
                    prefix += 1
                        
                    # DO NOT combine these two if statements to one
                    # because we only want to run the else part if the
                    # first condition isn't True.
                    if singlePathID1 == singlePathID2:
                        if prefix > self.maxPrefix:
                            lca = int(singlePathID1)
                            lcaPath1 = row1
                            lcaPath2 = row2
                            self.maxPrefix = prefix
                            
                    else:
                        break
        
        if not (lcaPath1 == None and lcaPath2 == None):            
            self.lcaPath.append(lcaPath1)
            self.lcaPath.append(lcaPath2)
        
        return lca
        
        
    def recursiveAncestorsPath(self, advisors, treeString):
        """
        Create all ancestors paths for the requested ID. Same IDs will be grabbed several times
        to ensure that all paths will be found.
        The paths will be created out of the advised-table. So, this part doesn't need online connectivity.
        """
        for advisor in advisors:
            self.cursor.execute("SELECT advisor FROM advised WHERE student=?", (advisor,))
            tempList = self.cursor.fetchall()
            nextAdvisors = []
            
            for row in tempList:
                nextAdvisors.append(row["advisor"])
            
            treeString = str(advisor) + "." + treeString

            if len(nextAdvisors) > 0:
                self.recursiveAncestorsPath(nextAdvisors, treeString)
                # We have to delete the last node from the string because we are following another path now
                treeString = treeString.split(".", 1)[1]
                
            else:
                # If we reach the highest ancestor, then store this string!
                self.paths.append(treeString + ".")
                print(treeString + ".")
                # We have to delete the last node from the string because we are following another path now
                treeString = treeString.split(".", 1)[1]
                
                
    def recursiveDescendantsPath(self, students, treeString):
        """
        Create all descendants paths for the requested ID. Same IDs will be grabbed several times
        to ensure that all paths will be found.
        The paths will be created out of the advised-table. So, this part doesn't need online connectivity.
        """
        for student in students:
            self.cursor.execute("SELECT student FROM advised WHERE advisor=?", (student,))
            tempList = self.cursor.fetchall()
            nextStudents = []
            
            for row in tempList:
                nextStudents.append(row["student"])
                
            treeString = treeString + "." + str(student)

            if len(nextStudents) > 0:
                self.recursiveDescendantsPath(nextStudents, treeString)
                # We have to delete the last node from the string because we are following another path now
                treeString = treeString.rsplit(".", 1)[0]
                
            else:
                # If we reach the highest ancestor, then store this string!
                self.paths.append(treeString + ".")
                print(treeString + ".")
                # We have to delete the last node from the string because we are following another path now
                treeString = treeString.rsplit(".", 1)[0]