Writing a New Sequence
======================

This section is a guide on how to write a new Sequence.

To write a new Sequence, you must extend seq.Sequence.Sequence or one
of its derived classes. If you only want to modify the behavior of an
existing Sequence, then you may just need to extend that Sequence and
override the appropriate functions.

By extending Sequence you only have to fill in a few methods that
implement the verilog generation. The verilog generation is broken
up into the following methods:

__init__(self, ..., **kw)
    For the __init__() method you can specify any custom arguments that
    your Sequence will need, but you will also need to add the **kw
    argument to pass to the base Sequence class. 

link(self, sequencer, parent, data)
    Testing  
   
_vlog_gen_declare(self)
    Testing  

_vlog_gen_logic(self)
    Testing  

_vlog_gen_reset(self)
    Testing  

_vlog_gen_seq(self)
    Testing  

_vlog_gen_start_wire(self, start)
    Testing  

_vlog_gen_inactive(self)
    Testing  

_vlog_gen_running(self)
    Testing  




Example of Set Sequence
-----------------------

Here is an example of the Set Sequence. The Set Sequence 
simply sets the provides dictionary of registers to the
supplied value and returns immediately.  The implementation
is as follows::

    class Set(Sequence):
        def __init__(self, set, **kw):
            self._set = set
            if not(type(set) is dict):
                raise Exception("'set' argument must be a dict")
            Sequence.__init__(self, **kw)
    
        def link(self, sequencer, parent, data):
            Sequence.link(self, sequencer, parent, data)
            self.mapping = {}
            self.inputs = {}
            for k,v in self._set.items():
                if not(self.sequencer.regs.has_key(k)):
                    raise Exception("Parent does not have a register called %s in Sequence %s %s" % (k, self.name, self))
    
                if type(v) is seq.Signal:
                    val = v.name
                    self.sequencer.register_port(seq.Port(v, "input"))
                else:
                    val = v
    		self.mapping[k] = str(val)
    
        def _vlog_gen_seq(self, set_at_end=False):
            s = [ "if(%s) begin" % (self.start, )", ]
            for sig, val in self.mapping.iteritems():
                s.append("  %s <= %s;" % (sig, val))
            s.append("end")
            return s
        
        def _vlog_gen_running(self):
            return [ "%s <= %s;" % (self.running, self.start,) ]
    
        def _vlog_gen_done(self):
            return self.running




