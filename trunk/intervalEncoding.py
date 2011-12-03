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
		#find the source node of the sub dag, and insert the NULL pair value
		self.c.execute("SELECT author, advisor FROM advised, dissertation WHERE student = dID ")
		self.tree = self.c.fetchall()

		self.c.execute("SELECT author FROM dissertation EXCEPT SELECT author FROM advised, dissertation WHERE student = dID")
		temp = self.c.fetchall()

		previous = 1
		for x in temp:
			if x != previous:
				self.tree.insert(0,((int(str(x)[1:-2])),0))
			previous = x

		self.tree.insert(0,(0,'NULL'))

		self.node()

	#------selection function------
	def selection(self, clause, table, condition):
			result = []
			querystring = 'select ' + clause + ' from ' + table + ' where ' + condition
			self.c.execute(querystring)
			temp = self.c.fetchall()
			for x in range(len(temp)):
					result.append(str(temp[x])[1:-2])
			return result

	def newselect(self,y,direction):
		result = []
		if direction == 1:
				for x in self.tree:
					if x[1] == y:
						result.append(x[0])

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

			self.post.append(self.marked.pop())

	#------LCA function for mutiple nodes------

	def LCA(self, List):

			# first check whether there is ans-des relation of each pair of nodes
			N = []; D = []; PN=[]; PD=[]; p=[]


			for x in List:
					N.append(self.code[x][0]); D.append(self.code[x][1])
					PN.append(self.code[x][2]); PD.append(self.code[x][3])

			FN=1; FD=0
			flag = 0; path = []

			while flag == 0:
					p=[]
					for i in range(len(List)):
							p.append(N[i]//D[i])
							temp = D[i]; D[i] = N[i]-D[i]*p[i]; N[i] = temp

					boolvalue = 1                #check all the elements in p[] is equal or not

	##                for x in p:
	##                        print("p value:",x)

					for i in range(len(p)-1):
							if p[i] != p[i+1]:
									boolvalue = 0


					if boolvalue == 1:
							temp = p[0]
							path.append(temp)
	##                        for x in path:
	##                                print("path: ",x)

					else:
							while len(path) > 0:
									q=path.pop()
									t=FD; FD=FN; FN=t
									FN=q*FD + FN

	##                        print ("found", FN,FD)

							for x in self.code:
								if self.code[x][0] == FN and self.code[x][1] == FD:
									return x


	#------for root node------
	def node(self):

		self.relation[0] = 'NULL'
		self.code[0] = [2,1,1,0]

		#-------for other nodes--------

		flag = 0; count = 1
		self.dfs(0)
		print(self.post)
		self.post.pop()
		while flag == 0:

				if len(self.post) != 0:
						workingnode = self.post.pop()




						parents = self.newselect(workingnode,0)
		##
		##                                print('step: ',count)
		##                                print('node:',name[j])
		##                                for x in parents:
		##                                        print('parent:', x)

						parents = self.removerelation(parents)

						if len(parents) == 1 or parents == [0,0]:
								LCAofparent = parents[0]
		##                                        print(name[j], " didn't called LCA", LCAofparent)


						else:
##                            print(workingnode, " called LCA")
##                            for x in parents:
##                                print('with', x)
								LCAofparent = self.LCA (parents)
		##                                        print('return', LCAofparent)


						nume = 1
						for x in self.relation:
							if self.relation[x] == LCAofparent:
								nume = nume+1

						num = self.code[LCAofparent]
						PPN = num[0] + num[2]; PPD = num[1] + num[3]; PN = num[0]; PD = num[1]


						D = PPD + PD*nume
						N = PPN + PN*nume

						# print('actual value', N,D,PN,PD)
						# print()

						self.code[workingnode] = [N, D, PN, PD]
						self.relation[workingnode] = LCAofparent



				else:
						flag = 1

		print("LSAtree After encoding:")
		print(self.code)
		print
		self.main2()

	#------main(query)------

	def main2(self):
		print("Running LCSA query of mutiple nodes, please enter node IDs")
		flag = 0; num = 1; inputlist = []; nodelist = ''; count = 0

		while flag == 0:
			promp ="node ID #" +str(num) +" or (E)nd:"
			getin = input(promp)

			if getin == 0:
				if count == 0 or count == 1:
					print("please enter at least two nodes")
				else:
					flag = 1
					inputlist = self.removerelation(inputlist)
					if len(inputlist) == 1:
							LCSA = inputlist[0]
					else:
							LCSA = self.LCA(inputlist)

					for x in inputlist:
							nodelist = nodelist + str(x) +" "
					print ("The LCSA of node",nodelist, "is node",LCSA)

					return LCSA

			else:
				if int(getin) in self.relation:
					inputlist.append(int(getin))
					num = num +1
					count = count +1
				else:
					print(getin, "is not a valid ID, please enter another one")


		self.db.commit()