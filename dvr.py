import threading
# import dictionary for routersGraph
from collections import defaultdict
import sys
import time
import math
from threading import Thread, Lock

mutex = Lock()

routerVersions = {}

currrouter = 0

no_of_routers = 0

no_of_iterations = 4

positive_infnity = math.inf#float('inf')

Queue = {}

router_names = []

routersGraph = {}

def Bellman_Ford(routingTable,neighbors,neighborRoutingTables,RId,RtrNameList):
    for i in range(no_of_routers):
        if i != RId:
            cost = routingTable[RtrNameList[i]]
            j = 0
            for neighbor in neighbors:
                table = neighborRoutingTables[j]
                val = neighbors[neighbor] + table[RtrNameList[i]]
                cost = min(val, cost)
                j = j + 1

            routingTable[RtrNameList[i]] = cost
    return routingTable

def printQueue():
    global Queue
    print(Queue)

def ExtractData(lines):
    line1 = lines[0]
    n = line1.split()
    global no_of_routers
    no_of_routers = int(n[0])

    line2 = lines[1]
    global router_names
    router_names = line2.split()
    i = 2

    global routersGraph
    while lines[i] != "EOF":
        line = lines[i]
        word = line.split(" ")
        src = word[0]
        dest = word[1]
        cost = int(word[2])
        if src in routersGraph:
            dct = routersGraph[src]
            dct[dest] = cost
            if dest in routersGraph:
                temp = routersGraph[dest]
                temp[src] = cost
            else:
                temp = {}
                temp[src] = cost
                routersGraph[dest] = temp
        else:
            dct = {}
            dct[dest] = cost
            routersGraph[src] = dct
            if dest in routersGraph:
                temp = routersGraph[dest]
                temp[src] = cost
            else:
                temp = {}
                temp[src] = cost
                routersGraph[dest] = temp
        i = i + 1


# Create your dictionary class
class RoutingTable(dict):
  # __init__ function
    def __init__(self):
        self = dict()
          
    # Function to add key:value
    def add(self, key, value):
        self[key] = value


class Router(threading.Thread):
    def __init__(self, RID, Rname, RtrNameList):
        threading.Thread.__init__(self)
        self.RId = RID
        self.RName = Rname
        self.RoutingTable = RoutingTable()
        self.neighbors = routersGraph[Rname]

        for dst in RtrNameList:
            if dst==self.RName:
                self.RoutingTable.add(dst,0)            #adding dest and cost
            elif dst in self.neighbors.keys():
                self.RoutingTable.add(dst,self.neighbors[dst])
            else:
                self.RoutingTable.add(dst,positive_infnity)
        
        self.neighborRoutingTables = []
        self.printRoutingTable()
        #storing the version of router before updating
        global routerVersions
        routerVersions[self.RName] = self.RoutingTable.copy()

    def printRoutingTable(self):
        print("{}                   {}                      {}                   {}".format(0, self.RId, self.RName, self.RoutingTable))
        print('-------------------------------------------------------------------------------------------------------')

    def updateRoutingTable(self, dst, cost):
        self.RoutingTable[dst] = cost

    def setRoutingTable(self):
            for neighbor in self.neighbors:
                cost = self.neighbors[neighbor]
                self.updateRoutingTable(neighbor, cost)
            
    def Sending(self):
        global Queue
        mutex.acquire()
        Queue[self.RName] = self.RoutingTable.copy()
        mutex.release()

    def ComputeDVs(self):                        #compute bellman for and update RT
        global router_names
        self.RoutingTable = Bellman_Ford(self.RoutingTable, self.neighbors, self.neighborRoutingTables, self.RId, router_names)
        #print("Routing Table updated ready to upload!")

    def Receiving(self):                                #receive neighbors RTs   
        global Queue
        self.neighborRoutingTables = []
        for i in self.neighbors:
            self.neighborRoutingTables.append(Queue[i])
        self.ComputeDVs()

    def run(self):
        global Queue
        #sending own RT to the queue for the first time
        self.Sending()
        status = True
        #wait for the queue to be full
        while status:
            if len(Queue) == no_of_routers:
                status = False
                
        for iteration in range(no_of_iterations):

            #start taking neighbor routers routing tables and updating current router's Routing Table
            self.Receiving()

            #wait for 2 seconds and then send the updated RT
            time.sleep(2)

            global routerVersions
            global currrouter

            mutex.acquire()
            currrouter = currrouter + 1
            mutex.release()
            status = True
            #wait until all routers are done
            while status:
                if currrouter == (iteration+1) * no_of_routers:
                    status = False
            #if all are done then all routers will send their updated RT to the queue one by one
            
            self.Sending()

            #as accessing routerVersions acquire lock
            mutex.acquire()
            lastVersion = routerVersions[self.RName]
            #matching if version before updating is equal to current version
            modified = "*"
            if lastVersion == self.RoutingTable:
                modified = ""
            
            routerVersions[self.RName] = self.RoutingTable.copy()
            print("{}                   {}                      {}                   {} {}".format(iteration+1, self.RId, self.RName, self.RoutingTable, modified))
            mutex.release()
            print('-------------------------------------------------------------------------------------------------------')


print("Enter the name of the input file: ", end="")
f_name = input()
file = open(f_name, "r")
lines = file.readlines()
ExtractData(lines)

for j in router_names:
    if j not in routersGraph:
        routersGraph[j] = {}
print('Routers graph: ',routersGraph)
print('Router names: ',router_names)
print('Router count: ',no_of_routers)
routers = []

print("---------------------------------------------------------------------------------------------------------------")
print("Iteration          Router ID               Router Name          Router-Table ")
print("---------------------------------------------------------------------------------------------------------------")

for j in range(no_of_routers):
    name = router_names[j]
    routers.append(Router(j, name, router_names))
    routers[len(routers)-1].start()

for router in routers:
    router.join()


'''
   A
2 / \ 3
 /   \
B     C
 \   /
4 \ / 5
   D
'''