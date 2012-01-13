# Copyright (c) 2011, Tianhong Song
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


import pickle


class coding:

	def __init__(self, connector):
		self.db = connector[0]
		self.c = connector[1]

		self.tree = []
		self.post = []
		self.marked = []
		self.relation = {}
		self.code = {}

  def mainfun(self):
		#find the source node of the sub dag 
		self.c.execute("SELECT author, advisor FROM advised, dissertation WHERE student = dID ")
		self.tree = self.c.fetchall()

		self.c.execute("SELECT author FROM dissertation EXCEPT SELECT author FROM advised, dissertation WHERE student = dID")
		temp = self.c.fetchall()

    #insert the NULL pair value
		previous = 1
		for x in temp:
			if x["author"] != previous:
				self.tree.insert(0,[x["author"],0])
			previous = x["author"]

    #add root node labeled "0"
		self.tree.insert(0,(0,'NULL'))

		self.node()

  #------selection function------
  def newselect(self,y,direction):
		result = []
      
    #select the children of a node
		if direction == 1:
			for x in self.tree:
				if x[1] != 'NULL' and x[1] == y:
					result.append(x[0])
    
    #select the parents of a node
		if direction == 0:
			for x in self.tree:
				if x[0] == y:
					result.append(x[1])

		return result

  #------removerelation function------
  def removerelation(self, List):
		for x in List:
			parent = self.relation[x]
			for y in List:
				if parent == y:
					List.remove(x)

		return List     #after altering

  def dfs(self, x):
		if x not in self.post:
			## print("now, the x is",x,"post is",post)
			self.marked.append(x)
			## print ("step:","marked:",marked)
			child = self.newselect(x,1)

			for y in child:
				self.dfs(y)

      #"post" contains the order of all the nodes
			self.post.append(self.marked.pop())


  def LCA(self, inputList):

		inputList = self.removerelation(inputList)
		# first check whether there is ans-des relation of each pair of nodes
		N = []; D = []; PN=[]; PD=[]

		for x in inputList:
			N.append(self.code[x][0]); D.append(self.code[x][1])
			PN.append(self.code[x][2]); PD.append(self.code[x][3])

		FN=1; FD=0
		flag = 0; path = []

		while flag == 0:
			p=[]
			for i in range(len(inputList)):
				p.append(N[i]//D[i])
				temp = D[i]; D[i] = N[i]-D[i]*p[i]; N[i] = temp

      boolvalue = 1                #check all the elements in p[] is equal or not

			for i in range(len(p)-1):
				if p[i] != p[i+1]:
					boolvalue = 0

      if boolvalue == 1:
				temp = p[0]
				path.append(temp)

      else:
				while len(path) > 0:
					q=path.pop()
					t=FD; FD=FN; FN=t
					FN=q*FD + FN

					for x in self.code:
						if self.code[x][0] == FN and self.code[x][1] == FD:
							return x


  #------for root node------
   def node(self):

    self.post.pop()
		self.relation[0] = 'NULL'
		self.code[0] = [2,1,1,0]

		#-------for other nodes--------

		flag = 0; count = 1
		self.dfs(0)
		#print(self.post)

		while len(self.post) != 0:

				workingnode = self.post.pop()
				parents = self.newselect(workingnode,0)
				parents = self.removerelation(parents)

        #if there is only one parent, we simple add an edge from the parent to the node
				if len(parents) == 1 or parents == [0,0]:
					LCAofparent = parents[0]

				else:
					LCAofparent = self.LCA(parents)

        #count the number of encoded children the LCAofparent has already haven
				nume = 1
				for x in self.relation:
					if self.relation[x] == LCAofparent:
						nume = nume+1

        #get the code of the LCAofparent
				num = self.code[LCAofparent]
				PPN = num[0] + num[2]; PPD = num[1] + num[3]; PN = num[0]; PD = num[1]

        #calculate the code of that node
				D = PPD + PD*nume
				N = PPN + PN*nume

        #insert the code [N, D, PN, PD] in the "code" dictinonary
				self.code[workingnode] = [N, D, PN, PD]
				self.relation[workingnode] = LCAofparent


    # write it to a pickle file
    #code contain the code of every node
		output1 = open('code.pkl', 'wb')
		pickle.dump(self.code, output1)
		output1.close()

    #relation contains all the edges in the tree
		output2 = open('relation.pkl', 'wb')
		pickle.dump(self.relation, output2)
		output2.close()

		self.db.commit()