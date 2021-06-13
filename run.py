'''

	just added:
	stored frame details - extended pixbuf and iterator classes to add a hashed version of each
	pixbuf's hex pixel array. now uses that hash to determine what frames still need to be loaded in

	now also passing in window positioning + file name
	creating multiple frame instances now = render multiple animations and arrange around screen

	TODO:
	- differentiate between still images and animation (good on this i think)
	- cairo blend modes with goal of semi-transparency https://www.cairographics.org/operators/
	- threads https://www.cairographics.org/threaded_animation_with_cairo/ (ooh)
	- figure out how to use one window for everything! (i dont think this is possible)

'''

# TODO do i need to add some way to cut out transparent gaps? I thought this was supported already

import sys

import cairo
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib

from os import _exit as byebye

from hashlib import md5



# creates a hash of pixel array when it instantiates
class MyPixbuf(GdkPixbuf.Pixbuf):
	def __init__(self,pixbuf):
		super().__init__()
		self.pixbuf = pixbuf
		self.pixel_hash = md5(self.pixbuf.get_pixels())

# to use augmented pixbuf
class MyIter(GdkPixbuf.PixbufAnimationIter):
	def __init__(self,iter,win):
		super().__init__()
		self.iter = iter
		self.win = win
		self.current_pixbuf = MyPixbuf(self.iter.get_pixbuf())
		self.frames = {}

	def get_pixbuf(self):
		return MyPixbuf(self.iter.get_pixbuf())

	def get_frame(self):
		self.current_pixbuf = current = MyPixbuf(self.iter.get_pixbuf())

		if current.pixel_hash not in self.frames: # set up cairo region + surface for this new frame
			surface = Gdk.cairo_surface_create_from_pixbuf(current.pixbuf, 0, self.win.get_window())
			region = Gdk.cairo_region_create_from_surface(surface)
			self.frames[current.pixel_hash] = {"surface": surface, "region": region}

		return self.frames[current.pixel_hash]

	def get_delay_time(self):
		return self.iter.get_delay_time()

	def advance(self):
		return self.iter.advance()

# TODO split out static and animated
class GtkSprite:
	def __init__(self,pos=False, x=0, y=0, animated=True, movable=True, sprite_name="marisa.gif"):

		self.sprite_name = sprite_name
		self.animated = animated
		self.movable = movable
		self.boring_setup(pos, x, y)

		# set up everything for the first frame using its pixbuf:
		pixbuf = MyPixbuf(self.iter.get_pixbuf())
		frame = self.iter.get_frame()
		self.surface = frame["surface"]  # canvas, where pixbuf is like the paint
		self.context = cairo.Context(self.surface) # gdkwindow is to gtkwindow as cairo context is to cairo surface/other cairo widgets? maybe???
		region = Gdk.cairo_region_create_from_surface(self.surface) # seems to control the window mask

		# adds timeout so expose() is called according to gif frame delay
		try:
			GLib.timeout_add(self.iter.get_delay_time(), self.expose, self.win, self.context)
		except OverflowError:
			pass

		self.win.shape_combine_region(region) # apply window shape
		self.context.set_source_surface(self.surface) # apply image
		self.context.paint()
	

		self.win.show()


	def button_press(self, widget, event):
		# allows clicking and dragging
		self.win.begin_move_drag(event.button, event.x_root, event.y_root, 0)


	def boring_setup(self, pos=False, x=0, y=0):

		# configure animation (do this first to make details of the animation available to the window)
		self.pixbuf_animation = GdkPixbuf.PixbufAnimation.new_from_file("./images/%s" % self.sprite_name)

		# configure window
		self.win = Gtk.Window()
		self.win.connect("delete_event", self.close_application) # handle exit event

		self.win.set_decorated(0) # no window decs
		self.win.set_app_paintable(1) # transparent

		self.win.set_can_focus(False) # i dont know what this does

		self.win.valign = Gtk.Align.CENTER # learn how to control this next (unless move() already does everything i need it to)
		self.win.halign = Gtk.Align.CENTER

		self.w = self.pixbuf_animation.get_width()
		self.h = self.pixbuf_animation.get_height()

		self.win.set_default_size(self.w, self.h) # apply image dimensions to window (do this just once, at size of bounding box)

		self.iter = MyIter(self.pixbuf_animation.get_iter(), self.win) # iterator will advance in expose() calls, timed to match gif frame delay
		self.win.connect("draw", self.expose) # connect window draw events to the expose_anim function, where future frames will be dealt with

		if pos: # if window position has been specified
			self.win.move(x, y)

		if self.movable: # it's not this
			self.win.connect("button-press-event", self.button_press) # on-click

		
		self.win.show()


	def close_application(self, widget, event, data=None): # err did i forget something here??
		Gtk.main_quit()

	# called on each refresh (for animation)
	def expose(self, window, context):

		if self.iter.advance(): # if iterator has a new frame,
		# load in frame delay time from animation file
			try:
		
				GLib.timeout_add(self.iter.get_delay_time(), self.expose, window, context) # reapply timeout
	
			except OverflowError:
				context.set_source_surface(self.surface)
				context.paint()
				window.show()
				return # image is not animated
			else:

				frame = self.iter.get_frame()
				self.pixbuf = self.iter.get_pixbuf()
				self.surface = frame["surface"]
				# apply corresponding region any time iterator advances
				region = frame["region"]
				window.shape_combine_region(region)

			# apply surface to context and repaint, whether or not iterator advances
		context.set_source_surface(self.surface)
		context.paint()
		window.show()
try:	
	GtkSprite(pos=True,x=50,y=0, sprite_name="lod.gif")
	GtkSprite(pos=True,x=750,y=125, sprite_name="rsx.gif")
	GtkSprite(pos=True,x=0,y=1000, sprite_name="digivice.gif")
	GtkSprite(pos=True,x=25,y=25, sprite_name="tsunemon.gif")
	GtkSprite(pos=True,x=20,y=400, sprite_name="greymon-sm.gif")	
	GtkSprite(pos=True,x=650,y=70, sprite_name="digi6.png")
	Gtk.main()
except KeyboardInterrupt:
	exit()