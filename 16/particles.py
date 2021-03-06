import random as rd
import numpy as np
from numpy.random import default_rng
import math as math
import time
import matplotlib.pyplot as plt
from heap import heap

# Binary tree
class Cell:

    def __init__(self, dimension, left, right, particles, boundA, boundB):
        self.left = left
        self.right = right
        self.boundA = boundA
        self.boundB = boundB
        # posX, posY, mass  
        self.particles = particles
        self.dimension = dimension
        self.isLeaf = False
        self.splitPosition = 0

        if (self.right - self.left > 8):
            self.partition()
        else:
            self.isLeaf = True
            # Determine radius, distance from center to particle furthest away
            self.radius = 0
            for particle in self.particles[self.left : self.right]:
                self.radius = max(self.radius, self.dist(self.center(), particle[0:2]))

    # O(n*log(n)), when executed on root
    def partition(self):
        # random initial guess
        guess = (self.boundB[self.dimension] + self.boundA[self.dimension]) / 2
        step = guess - self.boundA[self.dimension] 
        count = self.right - self.left
        halfCount = round(count / 2)

        # binary search over float, 64bit, with start optimization
        for i in range(math.floor(math.log2(1/step)) + 1, 64, 1):
            nLeft = 0
            for j in range(self.left, self.right):
                # branchless counting
                nLeft += (self.particles[j, self.dimension] < guess)
                #print(self.particles[j, self.dimension], self.particles[j, self.dimension] < guess, guess)

            # Break condtion for even and odd numbers of particles
            if abs(nLeft - halfCount) == 0 or (count % 2 == 1 and abs(nLeft - halfCount) == 1):
                break

            # guess improvement
            if nLeft < halfCount:
                guess += 1/(1<<i)
            else:
                guess -= 1/(1<<i)

        #print(nLeft, guess)
        
        # single iteration of quicksort, O(n)
        i = 0
        j = count - 1
        while(i < halfCount and j >= halfCount):
            if (self.particles[self.left + i, self.dimension] >= guess):
                tmp = np.array(self.particles[self.left + j, :], copy=True)
                self.particles[self.left + j, :] = self.particles[self.left + i, :]
                self.particles[self.left + i, :] = tmp            
                j -= 1
            else:
                i += 1

        self.splitPosition = guess

        newBoundA = self.boundA.copy()
        newBoundB = self.boundB.copy()
        newBoundA[self.dimension] = self.splitPosition
        newBoundB[self.dimension] = self.splitPosition
        self.childA = Cell(1-self.dimension, self.left, self.left + halfCount, self.particles, self.boundA, newBoundB)
        self.childB = Cell(1-self.dimension, self.left + halfCount, self.right, self.particles, newBoundA, self.boundB)

        # Compute radius of non leaf cell
        center = self.center()
        centerA = self.childA.center()
        centerB = self.childB.center()
        self.radius = max(self.dist(center, centerA) + self.childA.radius, self.dist(center, centerB) + self.childB.radius)

    # Get center of cell, in this case center of square, not average of particles
    def center(self):
        return [(self.boundA[0] + self.boundB[0]) / 2, (self.boundA[1] + self.boundB[1]) / 2]

    def draw(self, ax):
        if self.isLeaf:
            ax.scatter(self.particles[self.left: self.right, 0], self.particles[self.left: self.right, 1], s=2)
            ax.plot([self.boundA[0],self.boundB[0], self.boundB[0],self.boundA[0], self.boundA[0]],\
                 [self.boundA[1],self.boundA[1],self.boundB[1],self.boundB[1],self.boundA[1]], alpha = 0.8, linestyle="solid")

            #for i in range(self.left, self.right):
            #    ax.annotate(i, (self.particles[i,0], self.particles[i,1]))
        else:
            self.childA.draw(ax)
            self.childB.draw(ax)

    # Distance function
    # In this case using a circle, not a box
    def dist(self, a, b):
        x = abs(a[0] - b[0])
        y = abs(a[1] - b[1])
        # Periodic boundaries
        x = min(x, 1-x)
        y = min(y, 1-y)
        return math.sqrt(x * x + y * y)

    def kNearest(self, position, queue):
        if self.isLeaf:
            for i in range(self.left, self.right):
                d = self.dist(self.particles[i,0:2], position)
                if d < queue.getMax():
                    queue.replaceHead(d, self.particles[i,0:3])

        else:
            # Min distances from position to outermost particles from child cells
            distA = self.dist(position, self.childA.center()) - self.radius
            distB = self.dist(position, self.childB.center()) - self.radius
            if distA < distB:
                if distA < queue.getMax():
                    self.childA.kNearest(position, queue)
                if distB < queue.getMax():
                    self.childB.kNearest(position, queue)
            else:
                if distB < queue.getMax():
                    self.childB.kNearest(position, queue)
                if distA < queue.getMax():
                    self.childA.kNearest(position, queue)

num = 1 << 10
print("Number of particles:", num)

rg = np.random.default_rng()
particles = np.zeros((num, 5))
particles[:,2] = np.ones(num)
particles[:,0:2] = rg.random((num,2))
#plt.hist(particles[:,0])
root = Cell(0, 0, num, particles[:,0:3], [0,0], [1,1])
fig, axes = plt.subplots(1,2)

for particle in particles:
    maxHeap = heap(32)
    root.kNearest(particle[0:2], maxHeap)

    # Monohan factor
    factor = (40 / (7*math.pi)) / (maxHeap.getMax() ** 2)

    sumMass = 0
    sumMassMonohan = 0
    for i in range(maxHeap.size):
        mass = maxHeap.data[i][2]
        sumMass += mass
        h = maxHeap.getMax()
        r = maxHeap.values[i]
        if r > 0 and r / h < 0.5:
            sumMassMonohan += mass * (6 * (r / h) ** 3 - 6 * (r / h) ** 2 + 1)
        elif r/h >= 0.5 and r / h <= 1:
            sumMassMonohan += mass * (2 * (1-(r / h) ) ** 3)
        
    
    # Top hat
    particle[3] = sumMass / ( math.pi * maxHeap.getMax() ** 2)
    
    particle[4] = sumMassMonohan

axes[1].set_title("Top hat density of 32 nearest")
scatter = axes[1].scatter(particles[:,0], particles[:,1], c = particles[:,3])
scatter = axes[0].scatter(particles[:,0], particles[:,1], c = particles[:,4])
fig.colorbar(scatter, ax = axes[1])
plt.show()

