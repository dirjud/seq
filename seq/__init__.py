# Copyright (C) 2010 Lane Brooks
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
# 
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

class Signal(object):
    def __init__(self, name, width=1, init=0, signed=False):
        self.width = width
        self.name = name
        self.init = init
        self.signed=""
        if(signed):
            self.signed = "signed"

    def vlog_declaration(self, type, prefix="", suffix=""):
        """Returns a verilog declaration for this statement that of
        type 'type'.  e.g. if type can be input, output, reg, wire,
        etc."""
        if(self.width > 1):
            return "%s %s [%d:0] %s%s%s" % (type, self.signed, self.width-1, prefix, self.name, suffix)
        else:
            return "%s %s%s%s" % (type, prefix, self.name, suffix)

    def __str__(self):
        return "<Sequencer.Signal.Signal name=%s width=%d init=%d %s>" % (self.name, self.width, self.init, self.signed)


class Port(object):
    def __init__(self, sig, dir, reg=False):
        self.sig = sig
        self.dir = dir
        self.reg = reg

    def vlog_declaration(self):
        if(self.reg):
            type = self.dir + " reg"
        else:
            type = self.dir
        return self.sig.vlog_declaration(type)


def calc_width(num):
    if num <= 1:
        return 1
    import math
    width = int(math.ceil(math.log(num, 2)))
    return width
