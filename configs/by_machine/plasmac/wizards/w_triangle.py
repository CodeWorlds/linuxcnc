#!/usr/bin/env python

'''
w_triangle.py

Copyright (C) 2019, 2020  Phillip A Carter

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
'''

import os
import gtk
import time
import math
import linuxcnc
import shutil
import hal
from subprocess import Popen,PIPE

class triangle_wiz:

    def __init__(self):
        self.i = linuxcnc.ini(os.environ['INI_FILE_NAME'])
        self.c = linuxcnc.command()
        self.s = linuxcnc.stat()
        self.gui = self.i.find('DISPLAY', 'DISPLAY').lower()
        self.configFile = '{}_wizards.cfg'.format(self.i.find('EMC', 'MACHINE').lower())

    def triangle_preview(self, event):
        self.s.poll()
        xPos = self.s.actual_position[0] - self.s.g5x_offset[0] - self.s.g92_offset[0]
        yPos = self.s.actual_position[1] - self.s.g5x_offset[1] - self.s.g92_offset[1]
        if self.xSEntry.get_text():
            xBPoint = float(self.xSEntry.get_text())
        else:
            xBPoint = xPos
        if self.ySEntry.get_text():
            yBPoint = float(self.ySEntry.get_text())
        else:
            yBPoint = yPos
        if self.angEntry.get_text():
            angle = math.radians(float(self.angEntry.get_text()))
        else:
            angle = 0.0
        if self.liEntry.get_text():
            leadInOffset = math.sin(math.radians(45)) * float(self.liEntry.get_text())
        else:
            leadInOffset = 0
        if self.loEntry.get_text():
            leadOutOffset = math.sin(math.radians(45)) * float(self.loEntry.get_text())
        else:
            leadOutOffset = 0
        done = False
        a = b = c = A = B = C = 0
        if self.aEntry.get_text():
            a = float(self.aEntry.get_text())
        if self.bEntry.get_text():
            b = float(self.bEntry.get_text())
        if self.cEntry.get_text():
            c = float(self.cEntry.get_text())
        if self.AEntry.get_text():
            A = math.radians(float(self.AEntry.get_text()))
        if self.BEntry.get_text():
            B = math.radians(float(self.BEntry.get_text()))
        if self.CEntry.get_text():
            C = math.radians(float(self.CEntry.get_text()))
        if a and b and c:
            B = math.acos((a ** 2 + c ** 2 - b ** 2) / (2 * a * c))
            done = True
        if not done and a and B and c:
            done = True
        if not done and a and b and C:
            c = math.sqrt((a ** 2 + b ** 2) - 2 * a * b * math.cos(C))
            B = math.acos((a ** 2 + c ** 2 - b ** 2) / (2 * a * c))
            done = True
        if not done and A and b and c:
            a = math.sqrt((b ** 2 + c ** 2) - 2 * b * c * math.cos(A))
            B = math.acos((a ** 2 + c ** 2 - b ** 2) / (2 * a * c))
            done = True
        if not done and A and B and C:
            if A + B + C == math.radians(180):
                if a:
                    c = a / math.sin(A) * math.sin(C)
                    done = True
                elif b:
                    a = b / math.sin(B) * math.sin(A)
                    c = b / math.sin(B) * math.sin(C)
                    done = True
                elif c:
                    a = c / math.sin(C) * math.sin(A)
                    done = True
        if done:
            xCPoint = xBPoint + a * math.cos(angle)
            yCPoint = yBPoint + a * math.sin(angle)
            xAPoint = xBPoint + c * math.cos(angle + B)
            yAPoint = yBPoint + c * math.sin(angle + B)
            xCentre = xBPoint + (a / 2) * math.cos(angle)
            yCentre = yBPoint + (a / 2) * math.sin(angle)
            right = math.radians(0)
            up = math.radians(90)
            left = math.radians(180)
            down = math.radians(270)
            if self.outside.get_active():
                dir = [down, right]
            else:
                dir = [up, left]
            outTmp = open(self.fTmp, 'w')
            outNgc = open(self.fNgc, 'w')
            inWiz = open(self.fNgcBkp, 'r')
            for line in inWiz:
                if '(new wizard)' in line:
                    outNgc.write('\n{} (preamble)\n'.format(self.preamble))
                    outNgc.write('f#<_hal[plasmac.cut-feed-rate]>\n')
                    break
                elif '(postamble)' in line:
                    break
                elif 'm2' in line.lower() or 'm30' in line.lower():
                    break
                outNgc.write(line)
            outTmp.write('\n(wizard triangle)\n')
            if leadInOffset > 0:
                xlCentre = xCentre + (leadInOffset * math.cos(angle + dir[0]))
                ylCentre = yCentre + (leadInOffset * math.sin(angle + dir[0]))
                xlStart = xlCentre + (leadInOffset * math.cos(angle + dir[1]))
                ylStart = ylCentre + (leadInOffset * math.sin(angle + dir[1]))
                outTmp.write('g0 x{:.6f} y{:.6f}\n'.format(xlStart, ylStart))
                if self.offset.get_active():
                    outTmp.write('g41.1 d#<_hal[plasmac_run.kerf-width-f]>\n')
                outTmp.write('m3 $0 s1\n')
                outTmp.write('g3 x{:.6f} y{:.6f} i{:.6f} j{:.6f}\n'.format(xCentre, yCentre , xlCentre - xlStart, ylCentre - ylStart))
            else:
                outTmp.write('g0 x{:.6f} y{:.6f}\n'.format(xCentre, yCentre))
                outTmp.write('m3 $0 s1\n')
            if self.outside.get_active():
                outTmp.write('g1 x{:.6f} y{:.6f}\n'.format(xBPoint , yBPoint))
                outTmp.write('g1 x{:.6f} y{:.6f}\n'.format(xAPoint , yAPoint))
                outTmp.write('g1 x{:.6f} y{:.6f}\n'.format(xCPoint , yCPoint))
            else:
                outTmp.write('g1 x{:.6f} y{:.6f}\n'.format(xCPoint , yCPoint))
                outTmp.write('g1 x{:.6f} y{:.6f}\n'.format(xAPoint , yAPoint))
                outTmp.write('g1 x{:.6f} y{:.6f}\n'.format(xBPoint , yBPoint))
            outTmp.write('g1 x{:.6f} y{:.6f}\n'.format(xCentre, yCentre))
            if leadOutOffset > 0:
                if self.outside.get_active():
                    dir = [down, left]
                else:
                    dir = [up, right]
                xlCentre = xCentre + (leadOutOffset * math.cos(angle + dir[0]))
                ylCentre = yCentre + (leadOutOffset * math.sin(angle + dir[0]))
                xlEnd = xlCentre + (leadOutOffset * math.cos(angle + dir[1]))
                ylEnd = ylCentre + (leadOutOffset * math.sin(angle + dir[1]))
                outTmp.write('g3 x{:.6f} y{:.6f} i{:.6f} j{:.6f}\n'.format(xlEnd, ylEnd , xlCentre - xCentre, ylCentre - yCentre))
            outTmp.write('g40\n')
            outTmp.write('m5\n')
            outTmp.close()
            outTmp = open(self.fTmp, 'r')
            for line in outTmp:
                outNgc.write(line)
            outTmp.close()
            outNgc.write('\n{} (postamble)\n'.format(self.postamble))
            outNgc.write('m2\n')
            outNgc.close()
            self.parent.preview.load(self.fNgc)
            self.add.set_sensitive(True)
            self.parent.xOrigin = self.xSEntry.get_text()
            self.parent.yOrigin = self.ySEntry.get_text()
        else:
            if A <> 0 and B <> 0 and C <> 0 and A + B + C <> math.radians(180):
                self.parent.dialog_error('TRIANGLE', 'A + B + C must equal 180')
            else:
                self.parent.dialog_error('TRIANGLE', 'Minimum requirements are:\n\n'\
                                         'a + b + c\n\n'\
                                         'or\n\n'\
                                         'a + b + C\n\n'\
                                         'or\n\n'\
                                         'a + B + c\n\n'\
                                         'or\n\n'\
                                         'A + b + c\n\n'\
                                         'or\n\n'\
                                         'A + B + C + (a or b or c)')

    def auto_preview(self, widget):
        if (self.AEntry.get_text() and self.BEntry.get_text() and self.CEntry.get_text() and \
           (self.aEntry.get_text() or self.bEntry.get_text() or self.cEntry.get_text())) or \
           (self.AEntry.get_text() and self.bEntry.get_text() and self.cEntry.get_text()) or \
           (self.aEntry.get_text() and self.BEntry.get_text() and self.cEntry.get_text()) or \
           (self.aEntry.get_text() and self.bEntry.get_text() and self.CEntry.get_text()) or \
           (self.aEntry.get_text() and self.bEntry.get_text() and self.cEntry.get_text()):
            self.triangle_preview('auto') 

    def entry_changed(self, widget):
        if not self.liEntry.get_text() or float(self.liEntry.get_text()) == 0:
            self.offset.set_sensitive(False)
        else:
            self.offset.set_sensitive(True)
        self.parent.entry_changed(widget)

    def triangle_show(self, parent, entries, fNgc, fNgcBkp, fTmp, rowS, xOrigin, yOrigin):
        entries.set_row_spacings(rowS)
        self.parent = parent
        for child in entries.get_children():
            entries.remove(child)
        self.fNgc = fNgc
        self.fNgcBkp = fNgcBkp
        self.fTmp = fTmp
        cutLabel = gtk.Label('Cut Type')
        cutLabel.set_alignment(0.95, 0.5)
        cutLabel.set_width_chars(8)
        entries.attach(cutLabel, 0, 1, 0, 1)
        self.outside = gtk.RadioButton(None, 'Outside')
        self.outside.connect('toggled', self.auto_preview)
        entries.attach(self.outside, 1, 2, 0, 1)
        inside = gtk.RadioButton(self.outside, 'Inside')
        entries.attach(inside, 2, 3, 0, 1)
        offsetLabel = gtk.Label('Offset')
        offsetLabel.set_alignment(0.95, 0.5)
        offsetLabel.set_width_chars(8)
        entries.attach(offsetLabel, 3, 4, 0, 1)
        self.offset = gtk.CheckButton('Kerf')
        self.offset.connect('toggled', self.auto_preview)
        entries.attach(self.offset, 4, 5, 0, 1)
        lLabel = gtk.Label('Lead In')
        lLabel.set_alignment(0.95, 0.5)
        lLabel.set_width_chars(8)
        entries.attach(lLabel, 0, 1, 1, 2)
        self.liEntry = gtk.Entry()
        self.liEntry.set_width_chars(8)
        self.liEntry.connect('activate', self.auto_preview)
        self.liEntry.connect('changed', self.entry_changed)
        entries.attach(self.liEntry, 1, 2, 1, 2)
        loLabel = gtk.Label('Lead Out')
        loLabel.set_alignment(0.95, 0.5)
        loLabel.set_width_chars(8)
        entries.attach(loLabel, 0, 1, 2, 3)
        self.loEntry = gtk.Entry()
        self.loEntry.set_width_chars(8)
        self.loEntry.connect('activate', self.auto_preview)
        self.loEntry.connect('changed', self.parent.entry_changed)
        entries.attach(self.loEntry, 1, 2, 2, 3)
        xSLabel = gtk.Label()
        xSLabel.set_markup('X <span foreground="red">origin</span>')
        xSLabel.set_alignment(0.95, 0.5)
        xSLabel.set_width_chars(8)
        entries.attach(xSLabel, 0, 1, 3, 4)
        self.xSEntry = gtk.Entry()
        self.xSEntry.set_width_chars(8)
        self.xSEntry.connect('activate', self.auto_preview)
        self.xSEntry.connect('changed', self.parent.entry_changed)
        entries.attach(self.xSEntry, 1, 2, 3, 4)
        ySLabel = gtk.Label()
        ySLabel.set_markup('Y <span foreground="red">origin</span>')
        ySLabel.set_alignment(0.95, 0.5)
        ySLabel.set_width_chars(8)
        entries.attach(ySLabel, 0, 1, 4, 5)
        self.ySEntry = gtk.Entry()
        self.ySEntry.set_width_chars(8)
        self.ySEntry.connect('activate', self.auto_preview)
        self.ySEntry.connect('changed', self.parent.entry_changed)
        entries.attach(self.ySEntry, 1, 2, 4, 5)
        ALabel = gtk.Label('A angle')
        ALabel.set_alignment(0.95, 0.5)
        ALabel.set_width_chars(8)
        entries.attach(ALabel, 0, 1, 5, 6)
        self.AEntry = gtk.Entry()
        self.AEntry.set_width_chars(8)
        self.AEntry.connect('activate', self.auto_preview)
        self.AEntry.connect('changed', self.parent.entry_changed)
        entries.attach(self.AEntry, 1, 2, 5, 6)
        BLabel = gtk.Label('B angle')
        BLabel.set_alignment(0.95, 0.5)
        BLabel.set_width_chars(8)
        entries.attach(BLabel, 0, 1, 6, 7)
        self.BEntry = gtk.Entry()
        self.BEntry.set_width_chars(8)
        self.BEntry.connect('activate', self.auto_preview)
        self.BEntry.connect('changed', self.parent.entry_changed)
        entries.attach(self.BEntry, 1, 2, 6, 7)
        CLabel = gtk.Label('C angle')
        CLabel.set_alignment(0.95, 0.5)
        CLabel.set_width_chars(8)
        entries.attach(CLabel, 0, 1, 7, 8)
        self.CEntry = gtk.Entry()
        self.CEntry.set_width_chars(8)
        self.CEntry.connect('activate', self.auto_preview)
        self.CEntry.connect('changed', self.parent.entry_changed)
        entries.attach(self.CEntry, 1, 2, 7, 8)
        aLabel = gtk.Label('a length')
        aLabel.set_alignment(0.95, 0.5)
        aLabel.set_width_chars(8)
        entries.attach(aLabel, 0, 1, 8, 9)
        self.aEntry = gtk.Entry()
        self.aEntry.set_width_chars(8)
        self.aEntry.connect('activate', self.auto_preview)
        self.aEntry.connect('changed', self.parent.entry_changed)
        entries.attach(self.aEntry, 1, 2, 8, 9)
        bLabel = gtk.Label('b length')
        bLabel.set_alignment(0.95, 0.5)
        bLabel.set_width_chars(8)
        entries.attach(bLabel, 0, 1, 9, 10)
        self.bEntry = gtk.Entry()
        self.bEntry.set_width_chars(8)
        self.bEntry.connect('activate', self.auto_preview)
        self.bEntry.connect('changed', self.parent.entry_changed)
        entries.attach(self.bEntry, 1, 2, 9, 10)
        cLabel = gtk.Label('c length')
        cLabel.set_alignment(0.95, 0.5)
        cLabel.set_width_chars(8)
        entries.attach(cLabel, 0, 1, 10, 11)
        self.cEntry = gtk.Entry()
        self.cEntry.set_width_chars(8)
        self.cEntry.connect('activate', self.auto_preview)
        self.cEntry.connect('changed', self.parent.entry_changed)
        entries.attach(self.cEntry, 1, 2, 10, 11)
        angLabel = gtk.Label('Angle')
        angLabel.set_alignment(0.95, 0.5)
        angLabel.set_width_chars(8)
        entries.attach(angLabel, 0, 1, 11, 12)
        self.angEntry = gtk.Entry()
        self.angEntry.set_width_chars(8)
        self.angEntry.set_text('0')
        self.angEntry.connect('activate', self.auto_preview)
        self.angEntry.connect('changed', self.parent.entry_changed)
        entries.attach(self.angEntry, 1, 2, 11, 12)
        preview = gtk.Button('Preview')
        preview.connect('pressed', self.triangle_preview)
        entries.attach(preview, 0, 1, 13, 14)
        self.add = gtk.Button('Add')
        self.add.set_sensitive(False)
        self.add.connect('pressed', self.parent.add_shape_to_file, self.add)
        entries.attach(self.add, 2, 3, 13, 14)
        undo = gtk.Button('Undo')
        undo.connect('pressed', self.parent.undo_shape, self.add)
        entries.attach(undo, 4, 5, 13, 14)
        pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(
                filename='./wizards/images/triangle.png', 
                width=240, 
                height=240)
        image = gtk.Image()
        image.set_from_pixbuf(pixbuf)
        entries.attach(image, 2, 5, 1, 9)
        if os.path.exists(self.configFile):
            f_in = open(self.configFile, 'r')
            for line in f_in:
                if line.startswith('preamble'):
                    self.preamble = line.strip().split('=')[1]
                elif line.startswith('postamble'):
                    self.postamble = line.strip().split('=')[1]
                elif line.startswith('lead-in'):
                    self.liEntry.set_text(line.strip().split('=')[1])
                elif line.startswith('lead-out'):
                    self.loEntry.set_text(line.strip().split('=')[1])
        self.xSEntry.set_text('{:0.3f}'.format(float(xOrigin)))
        self.ySEntry.set_text('{:0.3f}'.format(float(yOrigin)))
        if not self.liEntry.get_text() or float(self.liEntry.get_text()) == 0:
            self.offset.set_sensitive(False)
        self.parent.undo_shape(None, self.add)
        self.parent.W.show_all()
        self.AEntry.grab_focus()
