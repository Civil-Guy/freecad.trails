'''create a house lod2 a'''

## Haus
# @todo : make the house parametric
#
#

class house():
	pass


import FreeCAD
import Part
import math



#\cond
def viereck(le,wi,he,inlea=0,inleb=0,inwia=0,inwib=0):
	'''gugu'''
	liste=[
		(0+inlea,inwia,he),
		(le-inleb,inwia,he),
		(le-inleb,wi-inwib,he),
		(inlea,wi-inwib,he),
		(inlea,inwia,he)
		]
	return liste


#\endcond


#\cond
def gen_haus0(le,wi,hiall,hi,midx,wx,midy,wy):


	he=hiall
	he3=hi

	if wx==0: wx=0.0001
	if wy==0: wy=0.0001

	if midx<0.5:
		bix=le*midx
	else:
		bix=le*(1-midx)

	if midy<0.5:
		biy=wi*midy
	else:
		biy=wi*(1-midy)

	list1=viereck(le,wi,0)
	list2=viereck(le,wi,he)
	list3=viereck(le,wi,he3,
		le*midx-bix*wx,le-(le*midx+bix*wx),
		wi*midy-biy*wy,wi-(wi*midy+biy*wy),
	)

	poly1 = Part.makePolygon( list1)
	poly3 = Part.makePolygon( list3)
	face1 = Part.Face(poly1)
	face3 = Part.Face(poly3)
	faceListe=[face1,face3]

	for i in range(len(list1)-1):
		liste3=[list1[i],list1[i+1],list2[i+1],list2[i],list1[i]]
		poly=Part.makePolygon(liste3)
		face = Part.Face(poly)
		faceListe.append(face)

	for i in range(len(list2)-1):
		liste3=[list2[i],list2[i+1],list3[i+1],list3[i],list2[i]]
		poly=Part.makePolygon(liste3)
		face = Part.Face(poly)
		faceListe.append(face)

	myShell = Part.makeShell(faceListe)   
	mySolid = Part.makeSolid(myShell)
	return mySolid
#\endcond


## create a house as part
 
def gen_haus(le,wi,hiall,hi,ang,midx=0.7,wx=0.5,midy=0.5,wy=0):
	h=gen_haus0(le,wi,hiall,hi,midx,wx,midy,wy)
	Part.show(h)
	p=FreeCAD.ActiveDocument.ActiveObject
	p.Placement.Rotation.Angle=ang*math.pi/180
	return p


## Gui backend

class MyApp(object):

	## create a house
	def gen_house(self):
		le=float(self.root.ids['le'].text())
		wi=float(self.root.ids['wi'].text())
		hiall=float(self.root.ids['hiall'].text())
		hi=float(self.root.ids['hi'].text())
		midy=1-float(self.root.ids['midx'].value())/100
		midx=float(self.root.ids['midy'].value())/100
		wy=float(self.root.ids['wx'].value())/100
		wx=float(self.root.ids['wy'].value())/100

		s= gen_haus(le,wi,hiall,hi,90,midx,wx,midy,wy)
		s.ViewObject.ShapeColor=(1.0,0.0,0.0)


## the dialog to create a house
def mydialog():

	from freecad.trails.geomatics.guigeoimport import miki
	from freecad.trails.geomatics.guigeoimport.miki_createhouse import sdialog

	app=MyApp()
	miki=miki.Miki()
	miki.app=app
	app.root=miki

	miki.parse2(sdialog)
	miki.run(sdialog)
	return miki

## test start and hide the dialog
def runtest():
	m=mydialog()
	m.objects[0].hide()



def createHouse():
	mydialog()
