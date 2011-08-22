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
    """
    def __init__(self):
        self.paths = []
        
        databaseConnector = databaseConnection.DatabaseConnector()
        connector = databaseConnector.connectToSQLite()
        self.connection = connector[0]
        self.cursor = connector[1]
        
        
    def lca(self, ids):
        allPaths = []
        lcaList = []
        
        for id in ids:
            print("Updating path of #", id)
            
            self.cursor.execute("SELECT advisor FROM advised WHERE student=?", (id,))
            tempList = self.cursor.fetchall()
            nextAdvisors = []
            
            for row in tempList:
                nextAdvisors.append(row["advisor"])
            
            if len(nextAdvisors) > 0:
                self.recursiveAncestorsPath(nextAdvisors, str(id))
            
                for row in self.paths:
                    row = [id] + [row]
                    allPaths.append(row)

            self.paths = []
            
        
        for i in range(len(ids)-1):
            id1 = ids[i]
            id2 = ids[i+1]
            
            maxPrefix = 0
            
            row1Iter = iter(allPaths)
            firstRunLoop1 = True
            
            for row1 in row1Iter:
                if firstRunLoop1:
                    firstRunLoop1 = False
                    
                    while not id1 == row1[0]:
                        row1 = next(row1Iter)
                        
                if not id1 == row1[0]:
                    break
                
                firstRunLoop2 = True
                row2Iter = iter(allPaths)    
                
                splitPath1 = row1[1].split('.')
                
                for row2 in row2Iter:
                    if firstRunLoop2:
                        firstRunLoop2 = False
                        
                        while not id2 == row2[0]:
                            row2 = next(row2Iter)
                            
                    if not id2 == row2[0]:
                        break
                    
                    prefix = 0
                    splitPath2 = row2[1].split('.')
                    
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
                            if prefix > maxPrefix:
                                lca = int(singlePathID1)
                                lcaPath1 = row1[1]
                                lcaPath2 = row2[1]
                                maxPrefix = prefix
                            
                        else:
                            break
                    
            lcaList.append(lca)
        
        
        if len(lcaList) == 0:
            finalLCA = None
        
        elif len(lcaList) == 1:
            finalLCA = lcaList[0]
        
        else:
            finalLCA = lcaList[0]
            
            for item in lcaList[1:]:
                if not finalLCA == item:
                    finalLCA = None
                    break
        
        if not finalLCA == None:
            self.cursor.execute("SELECT name FROM person WHERE pid=?", (finalLCA,))
            lcaName = self.cursor.fetchone()
            
            splitLcaPath1 = lcaPath1.split(str(finalLCA) + '.')[1].split('.')
            splitLcaPath2 = lcaPath2.split(str(finalLCA) + '.')[1].split('.')
            lcaIDs = [str(finalLCA)] + splitLcaPath1 + splitLcaPath2
            
            print("The LCA is", finalLCA, ":", lcaName["name"])
        
            self.cursor.close()
            self.connection.close()
        
            visualizer = visualize.Visualizer()
            dotFile = visualizer.generateDotFile(lcaIDs)
            
            lcaQuery = open("lcaQuery.dot", "w")
            print(dotFile, file=lcaQuery)
            lcaQuery.close()
        
        else:
            print("There is no LCA!")
        
        
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
                self.paths.append(treeString)
                print(treeString)
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
                self.paths.append(treeString)
                # We have to delete the last node from the string because we are following another path now
                treeString = treeString.rsplit(".", 1)[0]