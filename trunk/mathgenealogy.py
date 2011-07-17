from optparse import OptionParser
import string
import update



class Mathgenealogy:
    """
    A class for building Graphviz "dot" files for math genealogies
    extracted from the Mathematics Genealogy Project website.
    """
    def __init__(self):
        self.passedIDs = []
        self.passedName = None
        self.updateByID = False
        self.updateByName = False
        self.forceNaive = False
        self.ancestors = False
        self.descendants = False
        self.lca = False
        self.gss = False
        self.aa = False
        self.ad = False
        self.sp = False
        self.plot = False
        self.verbose = False
        self.writeFilename = None

    def parseInput(self):
        """
        Parse command-line information.
        """
        self.parser = OptionParser()

        self.parser.set_usage("%prog [options] LastName or IDs")
        self.parser.set_description("Update local database from the Mathematics Genealogy Project. Create a Graphviz dot-file for a mathematics genealogy by querying the locals database, where ID is a record identifier from the Mathematics Genealogy Project. Multiple IDs may be passed in case of search queries. Choose one update method OR one search method with the allowed options. You need online access for updates. You don't need online access for search queries.")
        
        self.parser.add_option("-i", "--update-by-ID", action="store_true", dest="updateByID", default=False,
                               help="Update method: Update the local database entries of the entered ID (and of the descendants and/or ancestors). INPUT: one ID")
        self.parser.add_option("-n", "--update-by-name", action="store_true", dest="updateByName", default=False,
                               help="Update method: Find the corresponding ID in the online database of a mathematician. Besides, the tool will also update the records of all found mathematicians. INPUT: last name of one mathematician")
        self.parser.add_option("-f", "--force", action="store_true", dest="forceNaive", default=False,
                               help="Force the tool to use naive update logic, which downloads all records of every mathematician you want to update without looking for any changes and stores every entry in the local database (replaces existing ones). Only available for update methods, not for search methods!")
        self.parser.add_option("-a", "--with-ancestors", action="store_true", dest="ancestors", default=False,
                               help="Retrieve ancestors of IDs and include in graph. Only available for update methods, not for search methods!")
        self.parser.add_option("-d", "--with-descendants", action="store_true", dest="descendants", default=False,
                               help="Retrieve descendants of IDs and include in graph. Only available for update methods, not for search methods!")
        
        self.parser.add_option("-L", "--least-common-advisor", action="store_true", dest="lca", default=False,
                               help="Search method: Search for the least common advisor of an arbitrary number of mathematicians. INPUT: IDs of the mathematicians separated by spaces")
        self.parser.add_option("-G", "--greatest-shared-student", action="store_true", dest="gss", default=False,
                               help="Search method: Search for the greatest shared student of an arbitrary number of mathematicians. INPUT: IDs of the mathematicians separated by spaces")
        self.parser.add_option("-A", "--all-ancestors", action="store_true", dest="aa", default=False,
                               help="Search method: Search for all ancestors of one mathematician. INPUT: ID of one mathematician")
        self.parser.add_option("-D", "--all-descendants", action="store_true", dest="ad", default=False,
                               help="Search method: Search for all descendants of one mathematician. INPUT: ID of one mathematician")
        self.parser.add_option("-P", "--shortest-path", action="store_true", dest="sp", default=False,
                               help="Search method: Search for the shortest path between two mathematicians with the additional option to include or exclude nodes. INPUT: Two IDs of the mathematicians to search for their shortest path. Then IDs of the mathematicians to include to the path. Finally IDs of the mathematicians to exclude from the path (enter a zero in front of the original ID without space). Every ID separated by spaces.")
        self.parser.add_option("-p", "--plot", action="store_true", dest="plot", default=False,
                               help="Generate dot-file and create plot of the result via Graphviz. Only available for search methods, not for update methods!")
        self.parser.add_option("-s", "--save-to-file", dest="filename", metavar="FILE", default=None,
                               help="Write output to a dot-file [default: stdout]. Only available for search methods, not for update methods!")
        
        self.parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False,
                               help="Print update messages and database messages.")
        self.parser.add_option( "-V", "--version", action="store_true", dest="print_version", default=False,
                               help="Print version and exit.")

        (options, args) = self.parser.parse_args()
        
        self.updateByID = options.updateByID
        self.updateByName = options.updateByName
        self.forceNaive = options.forceNaive
        self.ancestors = options.ancestors
        self.descendants = options.descendants
        self.lca = options.lca
        self.gss = options.gss
        self.aa = options.aa
        self.ad = options.ad
        self.sp = options.sp
        self.plot = options.plot
        self.verbose = options.verbose
        self.writeFilename = options.filename
        
        # Check for no arguments
        if len(args) == 0:
            raise SyntaxError("%s: error: no IDs or no last name passed" % (self.parser.get_prog_name()))
        
        # Check for the correct combination of options
        if (self.updateByName or self.updateByID or self.forceNaive or self.ancestors or self.descendants) and (self.lca or self.gss or self.aa or self.ad or self.sp or self.plot or (self.writeFilename is not None)):
            raise SyntaxError("%s: error: invalid combination of options" % (self.parser.get_prog_name()))
        
        if self.updateByName and self.updateByID:
            raise SyntaxError("%s: error: you can only choose one update method" % (self.parser.get_prog_name()))
        
        if self.lca and (self.gss or self.aa or self.ad or self.sp):
            raise SyntaxError("%s: error: you can only choose one search method" % (self.parser.get_prog_name()))
        
        if self.gss and (self.lca or self.aa or self.ad or self.sp):
            raise SyntaxError("%s: error: you can only choose one search method" % (self.parser.get_prog_name()))
        
        if self.aa and (self.gss or self.lca or self.ad or self.sp):
            raise SyntaxError("%s: error: you can only choose one search method" % (self.parser.get_prog_name()))
        
        if self.ad and (self.gss or self.aa or self.lca or self.sp):
            raise SyntaxError("%s: error: you can only choose one search method" % (self.parser.get_prog_name()))
        
        if self.sp and (self.gss or self.aa or self.ad or self.lca):
            raise SyntaxError("%s: error: you can only choose one search method" % (self.parser.get_prog_name()))
        
        if not (self.updateByName or self.updateByID or self.lca or self.gss or self.aa or self.ad or self.sp):
            raise SyntaxError("%s: error: you have to choose one update method or one search method" % (self.parser.get_prog_name()))
        
        # Check for the correct content (updateByName may contain anything)
        if not self.updateByName:
            for arg in args:
                if arg not in string.digits:
                    raise SyntaxError("%s: error: all arguments have to be numbers" % (self.parser.get_prog_name()))
        
        # Check for the correct number of arguments
        if self.updateByName or self.updateByID or self.aa or self.ad:
            if len(args) != 1:
                raise SyntaxError("%s: error: enter only one ID" % (self.parser.get_prog_name()))
            
        if self.sp:
            if len(args) < 2:
                raise SyntaxError("%s: error: you have to enter two IDs at least to search for a path" % (self.parser.get_prog_name()))
        
        # If no error occurred, then the options and arguments are correct. Hence, we can continue:
        # Read the arguments
        if self.updateByName:
            self.passedName = str(args[0])
            
        else:
            for arg in args:
                self.passedIDs.append(int(arg))
            
        # Execute the correct function depending on the options which have been set
        if options.print_version:
            print "Math-Genealogy-DB Version 1.0"
            self.parser.exit()
            
        if self.updateByName:
            updater = update.Updater(self.forceNaive)
            updater.findID(self.passedName)
        
        if self.updateByID:
            updater = update.Updater(self.forceNaive)
            updater.updateByID(self.passedIDs, self.ancestors, self.descendants)

        
#    def buildGraph(self):
#        """
#        Populate the graph member by grabbing the mathematician
#        pages and extracting relevant data.
#        """
#        leaf_grab_queue = list(self.leaf_ids)
#        ancestor_grab_queue = []
#        descendant_grab_queue = []
#
#        # Grab "leaf" nodes.
#        while len(leaf_grab_queue) != 0:
#            id = leaf_grab_queue.pop()
#            if not self.graph.hasNode(id):
#                # Then this information has not yet been grabbed.
#                grabber = grab.Grabber(id)
#                if self.verbose:
#                    print "Grabbing record #%d" % (id)
#                try:
#                    [name, institution, year, advisors, descendants] = grabber.extractNodeInformation()
#                except ValueError:
#                    # The given id does not exist in the Math Genealogy Project's database.
#                    raise
#                self.graph.addNode(name, institution, year, id, advisors, descendants, True)
#                if self.get_ancestors:
#                    ancestor_grab_queue += advisors
#                if self.get_descendants:
#                    descendant_grab_queue += descendants
#
#        # Grab ancestors of leaf nodes.
#        if self.get_ancestors:
#            while len(ancestor_grab_queue) != 0:
#                id = ancestor_grab_queue.pop()
#                if not self.graph.hasNode(id):
#                    # Then this information has not yet been grabbed.
#                    grabber = grab.Grabber(id)
#                    if self.verbose:
#                        print "Grabbing record #%d" % (id)
#                    try:
#                        [name, institution, year, advisors, descendants] = grabber.extractNodeInformation()
#                    except ValueError:
#                        # The given id does not exist in the Math Genealogy Project's database.
#                        raise
#                    self.graph.addNode(name, institution, year, id, advisors, descendants)
#                    ancestor_grab_queue += advisors
#                        
#        # Grab descendants of leaf nodes.
#        if self.get_descendants:
#            while len(descendant_grab_queue) != 0:
#                id = descendant_grab_queue.pop()
#                if not self.graph.hasNode(id):
#                    # Then this information has not yet been grabbed.
#                    grabber = grab.Grabber(id)
#                    if self.verbose:
#                        print "Grabbing record #%d" % (id)
#                    try:
#                        [name, institution, year, advisors, descendants] = grabber.extractNodeInformation()
#                    except ValueError:
#                        # The given id does not exist in the Math Genealogy Project's database.
#                        raise
#                    self.graph.addNode(name, institution, year, id, advisors, descendants)
#                    descendant_grab_queue += descendants
#                    
#    def generateDotFile(self):
#        dotfile = self.graph.generateDotFile(self.get_ancestors, self.get_descendants)
#        if self.write_filename is not None:
#            outfile = open(self.write_filename, "w")
#            outfile.write(dotfile)
#            outfile.close()
#        else:
#            print dotfile
        
        
#if __name__ == "__main__":
#    mgdb = Mathgenealogy()
#    try:
#        mgdb.parseInput()
#    except SyntaxError, e:
#        print mgdb.parser.get_usage()
#        print e