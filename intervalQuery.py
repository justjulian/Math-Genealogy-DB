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


class query:

	def __init__(self):

	#read two files in the constructer
		pkl_file1 = open('code.pkl', 'rb')
		self.code = pickle.load(pkl_file1)

		pkl_file2 = open('relation.pkl', 'rb')
		self.relation = pickle.load(pkl_file2)

		pkl_file1.close()
		pkl_file2.close()


	#------removerelation function------
	def removerelation(self, inputList):
		for x in inputList:
			parent = self.relation[x]
	
			for y in inputList:
				if parent == y:
					inputList.remove(x)
	
		return inputList     # after altering


	def LCA(self, inputList):
	
		inputList = self.removerelation(inputList)
		# first check whether there is ancestor-descendent relation of each pair of nodes
		N = []; D = []; PN=[]; PD=[]
	
		# obtain Farey fractions for node x: N/D is left bound, PN/PD is left bound of parent
		# (works for trees only; encoding already turned DAG into tree in previous steps)
		for x in inputList:
			N.append(self.code[x][0]); D.append(self.code[x][1])
			PN.append(self.code[x][2]); PD.append(self.code[x][3])
	
		FN=1; FD=0; path = []
	
		while True:

			#calculate one level of the path for every node
			p = []
			for i in range(len(inputList)):
				p.append(N[i]//D[i])
				temp = D[i]; D[i] = N[i]-D[i]*p[i]; N[i] = temp
			
			boolvalue = 1                #check all the elements in p[] is equal or not
			
			for i in range(len(p)-1):
				if p[i] != p[i+1]:
					boolvalue = 0
			
				# if all the elements in the p[] are the same, which means all the paths to nodes in the list are the same by now
			if boolvalue == 1:
				temp = p[0]
				path.append(temp)
			
				# if some of the elements in the p[] is different, which means the paths differ from now on, we find the LCA
			else:
				while len(path) > 0:
					q=path.pop()
					t=FD; FD=FN; FN=t
					FN=q*FD + FN
			
					# search for the name of the node has the interval [FN/FD,x]
					for x in self.code:
						if self.code[x][0] == FN and self.code[x][1] == FD:
							print(u"The LCA (of the LCSA tree) is {}".format(x).encode('utf-8'))
							return x