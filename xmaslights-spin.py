# Here are the libraries I am currently using:
import time
import board
import neopixel

import numpy as np

'''
With numpy array broadcasting on the np.exp function, I hope
this function will be quite performant.

sigmoid is... a sigmoid function.

It may be used as a heavy side function (replacing if statements)
by setting characteristicWidth very small. With larger width,
it can create a nice gradient effect.

x - the actual input variable

startVal - the lower (upper) bound of the function. This is what you
would get if you send in x=-inf

endVal - the upper (lower) bound of the function. This is what you
would get if you send in x=inf

middlePoint - this is the point where it "switches" from lower
values to higher values. In general, when x=middlePoint, the
function returns the average of startVal and endVal.

characteristicWidth - roughly the width through which the function
switches from startVal to endVal. Set to very small to approximate
a heavy side function, and set to relatively large to
get a nice gradient.
'''
def sigmoid(x, startVal, endVal, middlePoint, characteristicWidth):
	z = np.exp((x-middlePoint)/characteristicWidth)
	return startVal + (endVal - startVal) * z / (1 + z)

class XmasTree:
	'''
	XmasTree holds a "roamingPoint" which moves around the interior
	of the christmas tree (bounds defined later), and bounces off
	of the bounding surfaces of the tree.
	'''

	def __init__(self):
		# IMPORT THE COORDINATES (please don't break this bit)
		'''
		I might have broken this part :)
		I changed it to not use regular expression because gross.
		Also I put the coords in a numpy array because fast.
		'''
		
		coordfilename = "coords.txt"
		
		fin = open(coordfilename,'r')
		coords_raw = fin.readlines()
		
		self.coords = [line[1:-2].split(",") for line in coords_raw]
		for stringVector in self.coords:
			for i in range(len(stringVector)):
				stringVector[i] = int(stringVector[i])

		self.coords = np.array(self.coords)

		#set up the pixels (AKA 'LEDs')
		self.PIXEL_COUNT = len(self.coords) # this should be 500
		
#-------------------------untested------------------------------#
		self.pixels = neopixel.NeoPixel(
			board.D18, self.PIXEL_COUNT, auto_write=False)
#---------------------------------------------------------------#

		'''
		The "christmas tree" is defined to be a cone
		with peak height 600, slope (-dz/dr) 3.5,
		and lowest point (lower bound z) of -450.

		There may be issues with the point roaming outside of
		the christmas tree, if so then reduce the bounding surfaces.
		(Decrease self.peak and increase self.bottom)
		'''

		self.peak = 600.
		self.slope = 3.5
		self.bottom = -450

		'''
		There is a point which roams around the interior
		of the tree. It is used as a center point for the
		lighting effects. These numbers can be fiddled with
		to get a nice bouncing pattern.
		'''

		self.roamingPoint = np.array([0,-100.,self.bottom + 1])
		self.roamingVelocity = np.array([1,0.,1])*60
		
		self.t = time.time()
		self.timeElapsed = 0.

		#time in seconds to pause in between updates.
		#I hear the cpu is slow and this should be set to zero :)
		self.intermittentDownTime = 0.

	'''
	The red blue green functions do what they say. They give
	the color an led should be set to given the distance that
	led is to the roamingPoint. These functions are where the
	sigmoid function comes in. Again, the numbers here can
	be fiddled with to get nice lighting effects.

	(As requested, the leds are not set to max output. Bright
	versions are commented out.)
	The half integer startVal and endVal are used to
	get a proper distribution after np.floor is used.

	---------------------------------------------
	NOTE: np.floor RETURNS A FLOAT TYPE VALUE
	AND NEVER GETS CAST TO INT HERE
	---------------------------------------------
	I don't expect the type casting to be an issue,
	but I wanted this known in case an error gets thrown.
	'''

	def red(self, distances):
		# return np.floor(sigmoid(distances,
		# 	255.5, 0.5, 100, 10))
		return np.floor(sigmoid(distances,
			55.5, 0.5, 100, 10))

	def blue(self, distances):
		# return np.floor(sigmoid(distances,
		# 	0.5, 100.5, 450, 200))
		return np.floor(sigmoid(distances,
			0.5, 20.5, 450, 200))

	def green(self, distances):
		# return np.floor(sigmoid(np.abs(distances - 200),
		# 	100.5, 0.5, 100, 50))
		return np.floor(sigmoid(np.abs(distances - 200),
			20.5, 0.5, 100, 50))
		# return np.floor(distances / 1500+.001)#returns all zeros

	def pixelDistancesToPoint(self, pointCoord):
		return np.sqrt(np.sum((self.coords - pointCoord)**2, axis=1))

	#Does what it says on the tin
	def updateColors(self):
		'''
		Each led is colored according to the distance it is
		from self.roamingPoint
		'''
		distances = self.pixelDistancesToPoint(
			np.array([130, 0, 0]))
		newColors = zip(
			range(self.PIXEL_COUNT),
			self.green(distances),
			self.red(distances),
			self.blue(distances))

#-------------------------untested------------------------------#
		for i, g, r, b in newColors:
			self.pixels[i] = [g, r, b]

		pixels.show()
#---------------------------------------------------------------#

	'''
	Move the point, do boundary checking, and "bounce" the point.
	This doesn't involve looping through all led's, so can
	be a bit less optimized.
	'''
	def updateRoamingPoint(self):
		self.roamingPoint += self.timeElapsed * self.roamingVelocity
		if self.roamingPoint[2] < self.bottom:
			self.roamingPoint[2] = self.bottom + 0.01
			self.roamingVelocity[2] *= -1

		x = self.roamingPoint[0]
		y = self.roamingPoint[1]
		r = np.sqrt(x**2 + y**2)
		coneZ = self.peak - self.slope * r

		if self.roamingPoint[2] > coneZ:
			#I did some geometry for this, hope it was right
			z = r/self.slope
			norm = np.sqrt(x**2 + y**2 + z**2)
			normalVector = np.array([x/norm, y/norm, z/norm])

			distanceToCone = (self.roamingPoint[2] - coneZ)\
				/ np.sqrt(1 + self.slope**2)

			self.roamingPoint -= (distanceToCone + 0.01) * normalVector

			velocityComponentExitingCone = np.dot(
				normalVector, self.roamingVelocity)
			self.roamingVelocity -=\
				2 * velocityComponentExitingCone * normalVector

	#Calling this enters an indefinite loop.
	def run(self):
		while True:
			t0 = self.t
			self.updateRoamingPoint()
			self.updateColors()
			time.sleep(self.intermittentDownTime)
			self.t = time.time()
			self.timeElapsed = self.t - t0

# its one line, you heathen
if __name__ == "__main__":
	xmasTree = XmasTree()
	xmasTree.run()
