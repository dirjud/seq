import seq

def auto_dispatch(f):
    def wrapper(self, *args, **kw):
        # strip out the indent keyword if it is present
        if kw.has_key("indent"):
            indent = kw["indent"]
            del kw["indent"]
        else:
            indent = 0

        s = f(self, *args, **kw)
        s.extend(getattr(self, "_" + f.func_name)(*args, **kw))

        # now indent all lines
        ind = " " * indent * 2
        for i in range(len(s)):
            s[i] = ind + s[i]
        return s
    return wrapper

################################################################################
class Sequence(object):
    """A Sequence is an abstract class that provides a common interface
for a Sequencer to use to generate HDL that reprasents the desired
sequence functionality.  You should never instance this class directly
but should use one of the many derived classes available.
"""

    def __init__(self, **kw):
        """
:param name: A string name for this this sequence.  If no name is
provided, a unique name will be automatically assigned.

:param running: A seq.Signal (of width 1) that will become an
output of the Sequencer module that will go high when this sequence
is running

:param done: A seq.Signal (of width 1) that will become an output
of the Sequencer module that will go pulse high (one-shot) when this
sequence is done running

:param start: A seq.Signal (of width 1) that will become an output
of the Sequencer module that will go pulse high (one-shot) when this
sequence is started

:param subseqs: A list of Sequence's that is controlled by the
Sequence

:param dryrun: A seq.Signal (of width 1) that will cause the
Sequence to not adjust registers to the extent possible.  The Sequence
will go through the motions be not set anything.  Some Sequences have
to change the register values to complete (like a CountUp Sequence),
so these Sequences cannot honor the 'dryrun' state.  Sequences like
Set, Trigger, Stall, etc. will go through the motions and take the
same amount of time but not actually set the registers.
"""

        # validation keys in passed in the **kw dict
        valid_kws = ["name", "running", "subseqs", "done", "start", "dryrun", "extra" ]
        for key in kw:
            if not(key in valid_kws):
                raise Exception("Unknown argument %s" % key)

        # Process the 'name' kw or generate a unique name if no name is provided
        if kw.has_key("name"):
            self.name = kw["name"]
            if not(type(self.name) is str):
                raise Exception("'name' argument must be a string")
        else:
            self.name = Sequence.get_unique_name()

        # Generate internal variables all Sequences need
        self.start  = "seq_%s_start_" % self.name
        self.done   = "seq_%s_done_" % self.name
        self.running= "seq_%s_running_" % self.name
        self._unique_names = [ self.name ]

        # Process the 'running', 'done', and 'start' exports
        self._export_sigs = {}
        def process_export(obj, name):
            if not(type(obj) is seq.Signal):
                raise Exception("%s argument must be a Signal." % (obj,))
            if obj.width != 1:
                raise Exception("%s  Signal must be width 1 in sequence %s." % (obj.name, self))
            self._export_sigs[name] = obj
            
        if kw.has_key("running"):
            process_export(kw["running"], self.running)
        if kw.has_key("done"):
            process_export(kw["done"], self.done)
        if kw.has_key("start"):
            process_export(kw["start"], self.start)


        # Process the 'subseqs' kw
        if kw.has_key("subseqs"):
            self.subseqs = kw["subseqs"]
            if not(type(self.subseqs) in [ list, tuple ]):
                raise Exception("'subseqs' argument must be a list or tuple")
        else:
            self.subseqs = []
            

        if kw.has_key("dryrun"):
            self.dryrun = kw["dryrun"]
        else:
            self.dryrun = None

    unique_name_counter = 0
    @staticmethod
    def get_unique_name():
        Sequence.unique_name_counter += 1
        return "seq%04d" % (Sequence.unique_name_counter, )

    def __str__(self):
        return "<%s %s>" % (type(self), self.name)
    def __repr__(self):
        return "<%s %s>" % (type(self), self.name)

    def register_unique_names(self, names):
        """:param names: A dict keyed on strings of unique names.  Subclasses of this module should set the self._unique_names list so this function can register them.  If a unique name is already registered, then this function will raise and Exception.  Recursively calls this method on Children as well"""

        # register the unique names of this Sequence
        for n in self._unique_names:
            if(names.has_key(n)):
                raise Exception("Name %s is not unique.  It is required by ", str(self), "and", str(names[n]))
        
        # call register on sub-Sequences of this Sequence
        for subseq in self.subseqs:
            subseq.register_unique_names(names)

    def link(self, sequencer, parent, data):
        """:param data: A dict keyed on type(self) that each Sequence can
        use to register data it can use when generated logic that is shared
        between all Sequences of the same type"""
        self.sequencer = sequencer
        self.parent = parent
        if not data.has_key(type(self)):
            data[type(self)] = dict(insts = [])
        data[type(self)]["insts"].append(self)

        for sig in self._export_sigs.values():
            self.sequencer.register_port(seq.Port(sig, "output"))

        if self.dryrun is None:
            pass
        elif type(self.dryrun) is seq.Signal:
            if(self.dryrun.width != 1):
                raise Exception("Signal %s assigned to dryrun must be width = 1" % self.dryrun.name)
            self.sequencer.register_port(seq.Port(self.dryrun, "input"))
            self.dryrun = self.dryrun.name
        else:
            self.dryrun = str(self.dryrun)
            

    # The following vlog functions should not be overridden.  Rather, classes that extend this
    # base class should implement the same function prefixed with an '_'.  This base class will
    # then call that method and do any pre/post processing as necessary on the returned data (such
    # as indent it).

    @auto_dispatch
    def vlog_gen_declare(self):
        return []
    
    @auto_dispatch
    def vlog_gen_logic(self):
        s = []
        for name, sig in self._export_sigs.items():
            s.append("assign %s = %s;" % (sig.name, name,))
        return s

    @auto_dispatch
    def vlog_gen_reset(self):
        return []

    @auto_dispatch
    def vlog_gen_seq(self):
        return []

    @auto_dispatch
    def vlog_gen_start_wire(self, start):
        return []

    @auto_dispatch
    def vlog_gen_inactive(self):
        return []

    @auto_dispatch
    def vlog_gen_running(self):
        return []

    def vlog_gen_done(self):
        return self._vlog_gen_done()

    @staticmethod
    def vlog_gen_static_logic(data):
        return []

    # The following methods provide default implementations that can
    # be overridden as necessary
    def _vlog_gen_declare(self):
        return []
    
    def _vlog_gen_logic(self):
        return []

    def _vlog_gen_reset(self):
        return []

    def _vlog_gen_seq(self):
        return []

    def _vlog_gen_start_wire(self, start):
        s = [ "wire %s = %s;" % (self.start, start) ]
        for i, seq in enumerate(self.subseqs):
            s.extend(seq.vlog_gen_start_wire(start=start, indent=0))
        return s

    def _vlog_gen_inactive(self):
        s = [ ]
        for seq in self.subseqs:
            s.extend(seq.vlog_gen_inactive(indent=0))
        return s

    def _vlog_gen_running(self):
        return [ "if(%s) %s <= 1; else if(%s || start) %s <= 0;" % (self.start, self.running, self.done, self.running)]

    def find_reg(self, reg):
        """This will lookup the reg and return the Signal reference to it.
:param reg: str"""
        return self.sequencer.get_reg(reg)

    def use_reg(self, reg):
        """Like find_reg() but will also remove the reg from the output port list because
        it is an internal register only.  
:param reg: str"""
        r = self.find_reg(reg)
        del self.sequencer.ports[reg]
        return r
            
################################################################################

################################################################################
class Set(Sequence):
    """
The Set sequence is used to set register to either a static int
value or to a Signal passed in from a higher level (such as an I2C
register, for example).

:param set: A dict keyed off the register name.  The value is int or Signal
that the register will be set to.

Suppose your Sequencer has a registers named 'X', 'Y', and 'Z', then you can
set them as follows:
    Set(name="xyz", set=dict(X=1, Y=10, Z="4'b1010"))

You can also set them to Signals.  For example:
    zsig = seq.Signal(name="zsig", width=4, init=None)
    Set(name="z_on", set=dict(Z=zsig))
"""
    def __init__(self, set, **kw):
        self._set = set
        self.set_at_end=False # this can be overridden by other Derived classes
        if not(type(set) is dict):
            raise Exception("'set' argument must be a dict")
        Sequence.__init__(self, **kw)

    def link(self, sequencer, parent, data):
        Sequence.link(self, sequencer, parent, data)

        # create the signals in a mapping for easy lookup and
        # put Signals into the port list if they are setting
        # to a signal rather than a constant.
        self.mapping = {}
        self.inputs = {}
        for k,v in self._set.items():
            if not(self.sequencer.regs.has_key(k)):
                raise Exception("Parent does not have a register called %s in Sequence %s %s" % (k, self.name, self))

            if type(v) is seq.Signal:
                val = v.name
                self.sequencer.register_port(seq.Port(v, "input")) # create as in input port as it must be supplied externally
            else:
                val = v

            self.mapping[k] = str(val)

    def _vlog_gen_seq(self, set_at_end=False):
        if(self.mapping):
            s = []
            if(self.dryrun):
                s.append("if(!(%s)) begin" % self.dryrun)

            if self.set_at_end:
                s.append("if(%s) begin" % (self.done, ))
            else:
                s.append("if(%s) begin" % (self.start, ))

            for sig, val in self.mapping.iteritems():
                s.append("  %s <= %s;" % (sig, val))
            s.append("end")

            if(self.dryrun):
                s.append("end")
            return s
        else:
            return []
    
    def _vlog_gen_running(self):
        return [ "%s <= %s;" % (self.running, self.start,) ]

    def _vlog_gen_done(self):
        return self.running
################################################################################

################################################################################
class Reset(Set):
    """This Sequence extends the Set sequence.  It takes in no arguments
    and sets all the registers of the Sequencer to their init values.
    """
    def __init__(self, **kw):
        """See Sequence for available arguments."""
        # initially pass in an empty set dict.  we will fill in the
        # set dict after linking and we can access the complete regsiter
        # list in the parent sequencer
        Set.__init__(self, set={}, **kw)

    def link(self, sequencer, parent, data):
        # prior to calling link on the Set, we generate the set dict
        # for all registers in the sequencer with values specified
        # by the Signals init value
        for name, reg in sequencer.regs.items():
            self._set[name] = reg.init

        # now call the Set link method
        Set.link(self, sequencer, parent, data)
################################################################################

################################################################################
class Nop(Set):
    """Runs a one cycle sequence that does nothing.  This can be useful,
    for example, within a Select sequence when you want to Select
    between running a Sequence or doing nothing."""
    def __init__(self, **kw):
        """See Sequencer for available arguments."""
        Set.__init__(self, set={}, **kw)
################################################################################

################################################################################
class Stall(Set):
    """This stalls the current state until an internal counter reaches
    the provided stop_count signal value.  It uses a counter that is shared
    between all StallCount sequences.  The max_width static variable is
    used to figure out the biggest counter needed amongst all the
    instances of this class.

:param count: A seq.Signal that tells this sequence how many
    clock cycles to stall for.  It can also be an integer if the stop
    count should be hard coded.  If it is a str, then the Signal will
    be looked up in the regs list of the parent sequencer.  The stall
    duration does not include the 'start' one shot value.

:param set: A dict of signals and their value to be set for the
    duration of this stall state. See Set sequence for more
    information.

:param set_at_end: A bool that when True specifies that set should occur
    at the end of the stall period.  Otherwise it occurs at the beginning.
"""

    def __init__(self, count, set={}, set_at_end=False, **kw):
        Set.__init__(self, set, **kw)
        self.stop_count = count
        self.set_at_end = set_at_end

    def link(self, sequencer, parent, data):
        Set.link(self, sequencer, parent, data)
        if type(self.stop_count) is str: # replace string with reg Signal
            self.stop_count = self.use_reg(self.stop_count)
        elif type(self.stop_count) is int: # convert ints as a constant Signal
            self.stop_count = seq.Signal(str(self.stop_count), width=seq.calc_width(self.stop_count+1), init=0)
        elif type(self.stop_count) is seq.Signal: # add it to the port list
            self.sequencer.register_port(seq.Port(self.stop_count, "input"))
        else:
            raise Exception("Argument 'count' provided is not an int or Signal")

        if data[Stall].has_key("max_width"):
            if(data[Stall]["max_width"] < self.stop_count.width):
                data[Stall]["max_width"] = self.stop_count.width;
        else:
            data[Stall]["max_width"] = self.stop_count.width;


    def _vlog_gen_declare(self):
        s = Set._vlog_gen_declare(self)
        s.append("wire stall_done_%s_;" % (self.name, ))
        return s

    def _vlog_gen_done(self):
        return "%s & stall_done_%s_" % (self.running, self.name)

    def _vlog_gen_running(self):
        return [ "if(%s) %s <= 1; else if(%s || start) %s <= 0;" % (self.start, self.running, self.done, self.running)]

    @staticmethod
    def vlog_gen_static_logic(data):
        start = [inst.start for inst in data[Stall]["insts"]]

        
        s = ["  reg  [%d:0] stall_count_;" % (data[Stall]["max_width"]-1, ),
             "  wire start_stall_count_ = %s;" % (" || ".join(start)),
             "  wire [%d:0] next_stall_count_ = (start_stall_count_) ? 0 : (&stall_count_) ? stall_count_ : stall_count_ + 1;" % (data[Stall]["max_width"]-1, ),
             "  /* verilator lint_off WIDTH */", ]
        for inst in data[Stall]["insts"]:
            s.append("  assign stall_done_%s_ = stall_count_ >= (%s-%d'b1);" % (inst.name, inst.stop_count.name, inst.stop_count.width))
        s.append("  /* verilator lint_on WIDTH */" )
        s.extend(["  always @(posedge clk or negedge reset_n) begin",
                  "    if(!reset_n) begin",
                  "      stall_count_ <= 0;",
                  "    end else begin",
                  "      stall_count_ <= next_stall_count_;",
                  "    end",
                  "  end\n",
                  ])
        return s
################################################################################

################################################################################
class Trigger(Stall):
    """This Sequence emits a programmable length pulse or trigger
        signal.  'reg' must be the in the reg list of the parent
        Sequencer control this sequence.  The trigger is applied bit-wise,
        so if the reg is a bus, all bits get triggered.

        If this sequence is interrupted in the middle of operation
        then the trigger may not complete leaving the reg toggled.

:param reg: A seq.Signal or a string referencing the
seq.Signal name in the regs list of the parent Sequencer.

:param count: A seq.Signal, int, string, or None indicating 
how long the trigger pulse should be.  When None, the trigger is a
one-shot.  When an int, the trigger pulse is the specified number
of cycles.  When a string in the register list, the trigger pulse duration
specified by the value of the register.  When a seq.Signal, the pulse
duration is value of the Signal.

:param active_high: A bool indicating whether this trigger is active high pulse or
active low.

"""

    def __init__(self, reg, count=None, active_high=True, **kw):
        if count is None:
            self.stop_count = None
            Sequence.__init__(self, **kw)
        else:
            Stall.__init__(self, count=count, set={}, **kw)
        self.reg = reg;
        self.active_high=active_high
        if not(type(self.reg) in [seq.Signal, str]):
            raise Exception("'reg' argument must be a Signal or string. You provided a %s." % type(self.reg))

    def link(self, sequencer, parent, data):
        if self.stop_count is None:
            Sequence.link(self, sequencer, parent, data)
        else:
            # register this a type Stall so the static logic gets created
            if not data.has_key(Stall):
                data[Stall] = dict(insts = [])
            data[Stall]["insts"].append(self)
            Stall.link(self, sequencer, parent, data)
        if type(self.reg) is str: # do the register string replacement
            self.reg = self.find_reg(self.reg)


    def _vlog_gen_declare(self):
        if self.stop_count is None:
            return []
        else:
            return Stall._vlog_gen_declare(self)

    def _vlog_gen_seq(self):
        if not(self.stop_count is None):
            s = Stall._vlog_gen_seq(self)
        else:
            s = []
#        return [ "if(%s || %s) %s <= ~%s;" % (self.start, self.done, self.reg.name, self.reg.name) ] + s
        if(self.active_high): 
            hi = "{%d{1'b1}}" % self.reg.width
            lo = 0;
        else:
            hi = 0;
            lo = "{%d{1'b1}}" % self.reg.width

        if(self.dryrun):
            s.append("if(!(%s)) begin" % self.dryrun)
            
        if self.stop_count is None:
            s.append("if(%s) %s <= %s; else %s <= %s;" % (self.start, self.reg.name, hi, self.reg.name, lo) )
        else:
            s.append("if(%s) %s <= %s; else if(%s) %s <= %s;" % (self.start, self.reg.name, hi, self.done, self.reg.name, lo) )
        
        if(self.dryrun):
            s.append("end")

        return s
    
    def _vlog_gen_running(self):
        if self.stop_count is None:
            if(self.active_high):
                active = 1
            else:
                active = 0
            return [ "%s <= %s || (%s == %d);" % (self.running, self.start, self.reg.name, active) ]
        else:
            return Stall._vlog_gen_running(self)

    def _vlog_gen_done(self):
        if self.stop_count is None:
            if(self.active_high):
                active = 0
            else:
                active = 1
            return "%s && (%s == %d)" % (self.running, self.reg.name, active)
        else:
            return Stall._vlog_gen_done(self)
        
    @staticmethod
    def vlog_gen_static_logic(data):
        return []

################################################################################

################################################################################
class Toggle(Sequence):
    """This Sequence toggles the provided reg by inverting all the bits
        of the reg.  The reg must be the in the reg list of the
        parent Sequencer control this sequence.  

:param reg: A seq.Signal or a string of the seq.Signal name
        in the regs list of the parent Sequencer."""
    def __init__(self, reg, **kw):
        Sequence.__init__(self, **kw)
        self.reg = reg;

    def link(self, sequencer, parent, data):
        Sequence.link(self, sequencer, parent, data)
        if type(self.reg) is str:
            self.reg = self.find_reg(self.reg)
            
    def _vlog_gen_seq(self):
        s = []
        if(self.dryrun):
            s.append("if(!(%s)) begin" % self.dryrun)
        s.append("if(%s) %s <= ~%s;" % (self.start, self.reg.name, self.reg.name))
        if(self.dryrun):
            s.append("end")
        return s
    
    def _vlog_gen_running(self):
        return [ "%s <= %s;" % (self.running, self.start,) ]

    def _vlog_gen_done(self):
        return self.running
################################################################################


################################################################################
class Sync(Set):
    """This Sequencer will wait until all bits in the sync signal are
active.  You specify whether sync is active high or low.  This
overrides Set, you can use the **kw to set registers at the start of
this Sequence

:param sync: A seq.Signal on which this Sequence waits.  If it is a
    str, then the Signal will be looked up in the regs list of the
    parent sequencer.  

:param active_high: If True, then this Sequence waits until all bits in
sync are high.  Otherwise waits until they are all low.

:param set: A dict of signals and their value to be set for the
    duration of this stall state. See Set sequence for more
    information.
    """

    def __init__(self, sync, active_high=True, set={}, **kw):
        Set.__init__(self, set, **kw)
        self.sync = sync
        self.active_high = active_high

    def link(self, sequencer, parent, data):
        Set.link(self, sequencer, parent, data)
        # lookup sync in the reg list if it a string
        if type(self.sync) is str:
            self.sync = self.find_reg(self.sync)
        elif type(self.sync) is seq.Signal:
            self.sequencer.register_port(seq.Port(self.sync, "input"))
        else:
            raise Exception("'sync' argument must be a seq.Signal")

    def _vlog_gen_done(self):
        if(self.active_high):
            return "%s & (&%s)" % (self.running, self.sync.name)
        else:
            return "%s & (!(|%s))" % (self.running, self.sync.name)

    def _vlog_gen_running(self):
        return [ "if(%s) %s <= 1; else if(%s || start) %s <= 0;" % (self.start, self.running, self.done, self.running)]
################################################################################

################################################################################
class Child(Set):
    """A Child Sequence is used to start a Sequence in a child
Sequencer.  There are two variants availalbe.  When child_sequence is
a Signal, then the child Sequence to be executed is specified as an
input parameter.  When the child_sequence is a Sequence or a string,
then that sequence is executed.

:param set: You can pass in a dictionary of registers to set.  This
can be used, for example, with a child Select sequence to control
which sequence executes.

:param detach: When this is True, the child sequence will always run
detached.  This means that this Sequence will start the child and
immediately report done and not wait for the child the to finish.
When this is False, this sequence will wait until the child is done to
report done.  When this is a seq.Signal of width 1, then the signal
will be used to determine whether this sequence detaches.  If you run
detached, you can use the 'running' and 'done' signals to sync to
using a Sequence.Sync.  You must be careful when running in detached
mode because other start calls into the child sequencer will stop and
cancel the detached sequence causing its running flag with no done
signal being emitted.
"""

    def __init__(self, sequence, set={}, detach=False, **kw):
        """:param sequence: Can be a Sequence or string referenceing a
Sequence in sequencer or a seq.Signal if you want it
programmable"""
        Set.__init__(self, set=set, **kw)
#        self.child_sequencer = sequencer
        self.child_seq = sequence
        self.detach = detach
        
    def link(self, sequencer, parent, data):
        Set.link(self, sequencer, parent, data)

        self.edeclare = []
        self.elogic = []

        if type(self.child_seq) is str:
            # When child_seq is a string, we lookup the child sequence to run
            try:
                self.child_sequencer = sequencer.get_child_sequencer(self.child_seq)
                self.assign = [ "child_%s_seq_ <= child_%s_%s_;" % (self.child_sequencer.name, self.child_sequencer.name, self.child_seq)]
                self.sequencer.add_child_start(self.child_sequencer.name, self.start)
                self.done_name = "child_%s_done_" % self.child_sequencer.name
            except KeyError:
                raise Exception("Cannot find requested child sequence by name %s in sequencer" % self.child_seq)
        elif issubclass(type(self.child_seq), Sequence):
            # When child_seq is a sequence, no need to lookup beceause have the sequence
            self.child_sequencer = self.child_seq.sequencer
            self.assign = [ "child_%s_seq_ <= child_%s_%s_;" % (self.child_sequencer.name, self.child_sequencer.name, self.child_seq.name)]
            self.sequencer.add_child_start(self.child_sequencer.name, self.start)
            self.done_name = "child_%s_done_" % self.child_sequencer.name

        elif type(self.child_seq) is seq.Signal:
            # When the child_seq is a Signal, that means the choice of
            # the is a being set from an input signal.  This gets
            # complicated when there is more than one possible child
            # to execute.  So what we do is give the MSBs of the input
            # Signal to be the child sequencer address and use the
            # LSBs and the child Sequence address.

            # First add the input port for the signal
            self.sequencer.register_port(seq.Port(self.child_seq, "input"))

            # calculate the Sequencer/Sequence address breakdown of the input signal
            if(len(sequencer.children) <= 1):
                sequencer_addr_width = 0
            else:
                sequencer_addr_width = seq.calc_width(len(sequencer.children))

            sequence_addr_width=1
            for child in sequencer.children:
                w = seq.calc_width(len(child.seqs))
                if(w > sequence_addr_width): sequence_addr_width = w
            sig_width = sequencer_addr_width + sequence_addr_width

            # now check that the provided Signal is right width
            if(sig_width != self.child_seq.width):
                raise Exception("Width of child sequence selection signal %s is not correct.  It should be %d (%d bits for Sequencer address and %d bits for Sequence address" % (self.child_seq.name, sig_width, sequencer_addr_width, sequence_addr_width))

            # now generate the extra logic for programmable state selection
            if(sequencer_addr_width == 0):
                self.child_sequencer = sequencer.children[0]
                self.assign = [ "child_%s_seq_ <= %s;" % (self.child_sequencer.name, self.child_seq.name)]
                self.sequencer.add_child_start(self.child_sequencer.name, self.start)
                self.done_name = "child_%s_done_" % self.child_sequencer.name

            else:
#                self.child_sequencer = sequencer.children[0]
                self.edeclare.append("wire [%d:0] seq_%s_child_sel_ = %s[%d:%d];" % ( sequencer_addr_width-1, self.name, self.child_seq.name, self.child_seq.width-1, self.child_seq.width-sequencer_addr_width,))
                self.edeclare.append("wire [%d:0] seq_%s_seq_sel_ = %s[%d:0];" % ( sequence_addr_width-1, self.name, self.child_seq.name, sequence_addr_width-1))
                self.edeclare.append("wire seq_%s_done_sel_;" % ( self.name, ))
                self.assign = ["case(seq_%s_child_sel_)" % (self.name,)]
                done = []
                for i, child in enumerate(sequencer.children):
                    self.assign.append("  %d: begin" % i)
                    self.assign.append("    child_%s_seq_ <= seq_%s_seq_sel_[%d:0];" % (child.name, self.name, seq.calc_width(len(child.seqs))-1))
                    self.assign.append("  end")
                    start = "%s%s_" % ( self.start, child.name, )
                    self.edeclare.append("wire %s;" % ( start,))
                    self.elogic.append("assign %s = %s & (%s[%d:%d] == %d);" % (start, self.start, self.child_seq.name, self.child_seq.width-1, self.child_seq.width-sequencer_addr_width, i))
                    done.append("(child_%s_done_ & (seq_%s_child_sel_ == %d))" % (child.name, self.name, i, ))
                    self.sequencer.add_child_start(child.name, start)
                self.elogic.append("assign seq_%s_done_sel_ = %s;" % (self.name, " || ".join(done)))
                self.done_name = "seq_%s_done_sel_" % self.name
                self.assign.append("endcase")

        else:
            raise Exception("Unknown object %s passed as argument 'child_sequence' to %s" % (self.child_seq, self, ))


        if type(self.detach) is str:
            self.detach = self.find_reg(self.detach)
        elif type(self.detach) is seq.Signal:
            self.sequencer.register_port(seq.Port(self.detach, "input"))
        elif type(self.detach) is bool:
            pass
        else:
            raise Exception("Unknown type passed as argument 'detach' to %s" % (self, ))
    
    def _vlog_gen_declare(self):
        return self.edeclare + Set._vlog_gen_declare(self)

    def _vlog_gen_logic(self):
        return self.elogic + Set._vlog_gen_logic(self)
                                       
    def _vlog_gen_done(self):
        not_detached_done =  "%s && %s" % (self.done_name, self.running,)
        if self.detach is True:
            return Set._vlog_gen_done(self)
        elif self.detach is False:
            return not_detached_done;
        else:
            return "(%s) ? (%s) : (%s)" % (self.detach.name, Set._vlog_gen_done(self), not_detached_done)

    def _vlog_gen_running(self):
        # override Set's running code with default Sequence code
        return Sequence._vlog_gen_running(self) 

    def _vlog_gen_seq(self):
        return self.assign + Set._vlog_gen_seq(self)
################################################################################

################################################################################
class Serial(Set):
    """Runs provided Sequences in list 'subseqs' in series.  Sets via the 'set' dict"""
    def __init__(self, subseqs, set={}, term=None, **kw):
        """:param subseqs: List of Sequences to run serially.

:param set: See Set

:param term: A Signal or None.  When a Signal, this Signal sets the
Sequence to stop on.  This can be useful when the subseqs are
programmable Child's and you want to change the number of Sequences
that get run.  If None, then all Sequences in the subseqs list will
always run unconditionally.  There is a 1 count offset on the term
number---e.g., when this is set to 0, only the first sequence will
run.  When set to 1, the first 2 Sequences will run, etc.
"""
        kw["subseqs"] = subseqs
        Set.__init__(self, set=set, **kw)
        self.addr = "%s_addr_" % self.name
        self.next_addr = "next_%s" % self.addr
        self.term = term

    def link(self, sequencer, parent, data):
        Set.link(self, sequencer, parent, data)
        if self.term:
            self.sequencer.register_port(seq.Port(self.term, "input"))


    def _vlog_gen_declare(self):
        s = []
        width = seq.calc_width(len(self.subseqs))
        s.append("reg  [%d:0] %s;" % (width-1, self.addr))
        s.append("wire [%d:0] %s;" % (width-1, self.next_addr))
        if(self.term):
            s.append("wire seq_%s_term_;" % self.name)
        return s + Set._vlog_gen_declare(self)

    def _vlog_gen_logic(self):
        if(len(self.subseqs)>1):
            s =  [ "assign %s = (%s) ? 0 : (%s) ? (%s + 1) : %s;" % (self.next_addr, self.start, " || ".join([x.start for x in self.subseqs[1:]]), self.addr, self.addr)]
        else:
            s = [ "assign %s = %s;" % (self.next_addr, self.addr) ]
        if self.term:
            s.append("assign seq_%s_term_ = %s >= %s;" % (self.name, self.addr, self.term.name,))
        return s + Set._vlog_gen_logic(self)
                    


    def _vlog_gen_reset(self):
        s = [ "%s <= 0;" % self.addr ]
        return s + Set._vlog_gen_reset(self)

    def _vlog_gen_start_wire(self, start):
        s = [ "wire %s = %s;" % (self.start, start) ]
        for i, seq in enumerate(self.subseqs):
            s.extend(seq.vlog_gen_start_wire(start=start, indent=0))
            if self.term:
                start = "%s & (%s==%d) & (!seq_%s_term_)" % (seq.done, self.addr, i, self.name)
            else:
                start = "%s & (%s==%d)" % (seq.done, self.addr, i)
        return s

    def _vlog_gen_seq(self):
        s = []
        s.append("%s <= %s;" % (self.addr, self.next_addr, ))
        s.append("case(%s)" % self.next_addr)
        for i, seq in enumerate(self.subseqs):
            s.append("  %d: begin" % (i,))  
            s.extend(seq.vlog_gen_seq(indent=2))
            s.append("  end\n")
        s.append("endcase")
        return Set._vlog_gen_seq(self) + s

    def _vlog_gen_done(self):
        if self.term:
            s = "%s && ((%s) && seq_%s_term_ || %s)" % (self.running,  " || ".join([ x.done for x in self.subseqs]), self.name, self.subseqs[-1].done)
        else:
            s = "%s && %s" % (self.subseqs[-1].done, self.running) 
        return s

    def _vlog_gen_running(self):
        return Sequence._vlog_gen_running(self)

    def _vlog_gen_inactive(self):
        s = [ "%s <= 0;" % self.addr ]
        for seq in self.subseqs:
            s.extend(seq.vlog_gen_inactive(indent=0))
        return s
################################################################################

################################################################################
class Parallel(Sequence):
    """Runs Sequences in list 'subseqs' in parallel"""
    def __init__(self, subseqs, **kw):
        kw["subseqs"] = subseqs
        Sequence.__init__(self, **kw)

#        # check for child sequencers crossing parallel boundaries
#        sequencers = []
#        for seq in subseqs:
#            childsequencers = self.getChildSequencers(seq)
#            for children1 in sequencers:
#                for children2 in childsequencers:
#                    if children2 in children1:
#                        raise Exception("Warning: Parallel Sequencer is not deisgned to control the same child Sequencer in parallel.  You are currently specify sequences to run in parallel that control the same child.  This will likely produce unexcepted results.  You should split the signals to control in parallel into separate child Sequencers.")
#            sequencers.append(childsequencers)
#        print sequencers
#
#    def getChildSequencers(self, seq):
#        if(seq.sequencer is self.sequencer):
#            sequencers = []
#        else:
#            sequencers = [ seq.sequencer ]
#        for seq in seq.subseqs:
#            sequencers.extend(self.getSequencers(seq.subseqs))
#        return sequencers


    def _vlog_gen_seq(self):
        s = []
        for i, seq in enumerate(self.subseqs):
            s.extend(seq.vlog_gen_seq(indent=0))
        return s

    def _vlog_gen_done(self):
        return "!(%s) & %s" % (" || ".join([x.running for x in self.subseqs]), self.running)

    def _vlog_gen_running(self):
        return [ "%s <= %s || %s;" % (self.running, self.start, " || ".join([x.running for x in self.subseqs]),)]
################################################################################

################################################################################
class Select(Sequence):
    def __init__(self, subseqs, sel, **kw):
        """:param subseqs: A list of Sequences
:param sel: A seq.Signal that indexes into the subseqs list to selectq which Sequence to execute
"""
        kw["subseqs"] = subseqs
        Sequence.__init__(self, **kw)
        self.sel = sel
        

    def link(self, sequencer, parent, data):
        Sequence.link(self, sequencer, parent, data)
        self.sequencer.register_port(seq.Port(self.sel, "input"))

    def _vlog_gen_declare(self):
        s = ["wire select_%s_done_;" % self.name]
        return s

    def _vlog_gen_logic(self):
        s = ["assign select_%s_done_ =" % (self.name,) ]
        for j, seq in enumerate(self.subseqs[:-1]):
            s.append(" "*10+"(%s==%d) ? %s :" % (self.sel.name, j, seq.done))
        s.append(" "*10+"%s;" % (self.subseqs[-1].done,))
        return s
        
    def _vlog_gen_start_wire(self, start):
        s = [ "wire %s = %s;" % (self.start, start) ]
        for i, seq in enumerate(self.subseqs):
            s.extend(seq.vlog_gen_start_wire(start="%s & (%s==%d)" % (start, self.sel.name, i), indent=0))
        return s

    def _vlog_gen_seq(self):
        s = [ "case(%s)" % self.sel.name, ]
        for i, seq in enumerate(self.subseqs):
            s.append("  %d: begin" % i)
            s.extend(seq.vlog_gen_seq(indent=2))
            s.append("  end\n")
        s.append("endcase")
        return s

    def _vlog_gen_done(self):
        return "%s & select_%s_done_" % (self.running, self.name)
################################################################################

################################################################################
class Repeat(Sequence):
    """A Sequence that runs the specified sequence a specified number of times"""
    def __init__(self, subseq, count, counter=None, **kw):
        """:param subseq: The Sequence or string referring to child sequence to repeat.
:param count: A seq.Signal that tells this sequence how many tims
    to execute 'subseq' Sequence.  It can also be an integer if the
    number of repeats can be hard coded.  If it is a str, then the
    Signal will be looked up in the regs list of the parent sequencer.
    A value of '0' is not valid and will cause the subseq to be run the
    max number of times.

:param counter: A seq.Signal that is not in the reg list of the parent
sequencer that will be assigned to the current loop number.  If None, then 
current loop number is not exported and kept internal.
"""
        kw["subseqs"] = [subseq]
        self.count = count
        self.output = counter

        Sequence.__init__(self, **kw)

    def link(self, sequencer, parent, data):
        Sequence.link(self, sequencer, parent, data)

        if type(self.count) is str: # replace string with reg Signal
            self.count = self.use_reg(self.count)
        elif type(self.count) is int: # convert ints as a constant Signal
            self.count = seq.Signal(str(self.count), width=seq.calc_width(self.count+1), init=0)
        elif type(self.count) is seq.Signal: # add it to the port list
            self.sequencer.register_port(seq.Port(self.count, "input"))
        else:
            raise Exception("Argument 'count' provided is not an int or Signal or str in the reg list")

        if self.output:
            sequencer.register_port(seq.Port(self.output, "output"))

        self.counter = seq.Signal(name="seq_%s_counter_"% (self.name,), width=self.count.width)
            

    def _vlog_gen_declare(self):
        s = ["reg [%d:0] %s;" % (self.counter.width-1, self.counter.name,),
             "wire repeat_%s_done_;" % self.name, ]
        return s

    def _vlog_gen_logic(self):
        s = ["assign repeat_%s_done_ = %s && (%s >= (%s-%d'd1));" % (self.name, self.subseqs[0].done, self.counter.name, self.count.name, self.count.width) ]
        if(self.output):
            s.append(["assign %s = %s;" % (self.output.name, self.counter.name,)])
        return s
        
    def _vlog_gen_start_wire(self, start):
        s = [ "wire %s = %s;" % (self.start, start) ]
        s.extend(self.subseqs[0].vlog_gen_start_wire(start = "%s || (%s && !%s)" % (self.start, self.subseqs[0].done, self.done)))
        return s

    def _vlog_gen_reset(self):
        return [ "%s <= 0;" % self.counter.name ]

    def _vlog_gen_seq(self):
        s = [ "if(%s) begin" % self.start,
              "  %s <= 0;" % self.counter.name,
              "end else if(%s) begin" % self.subseqs[0].done,
              "  %s <= %s+1;" % (self.counter.name, self.counter.name, ),
              "end" ]

        return s + self.subseqs[0].vlog_gen_seq(indent=0)

    def _vlog_gen_done(self):
        return "%s & repeat_%s_done_" % (self.running, self.name)



################################################################################

            
################################################################################
class CountDown(Sequence):
    """Takes 'sig' and counts it down until the 'stop' param has been
reached.  The decrement value is 'skip'.  Overflow is watched and
accounted for, so it is safe to set the stop param to zero."""

    def __init__(self, reg, stop, skip, **kw):
        """:param reg: A seq.Signal or string in the parent sequencer reg list.
:param stop: A seq.Signal or int value corresponding to the value at which the counter should stop decrementing
:param skip: A seq.Signal or int value corresponding to the decrement amount.
"""
        Sequence.__init__(self, **kw)
        self.reg = reg
        self.stop = stop
        self.skip = skip

    def link(self, sequencer, parent, data):
        Sequence.link(self, sequencer, parent, data)
        # lookup the reg in the reg list if it a string
        if type(self.reg) is str:
            self.reg = self.find_reg(self.reg)
        else:
            raise Exception("reg must be string reference to register that is part of the parent sequencer in %s" % (self, ))

        # expand stop and skip if they are ints
        if type(self.stop) is int:
            self.stop = seq.Signal(str(self.stop), width=seq.calc_width(self.stop+1), init=0)
        elif type(self.stop) is str:
            self.stop = self.use_reg(self.stop)
        elif type(self.stop) is seq.Signal:
            self.sequencer.register_port(seq.Port(self.stop, "input"))
        else:
            raise Exception("Unknown stop_type in %s" % (self, ))

        if type(self.skip) is int:
            self.skip = seq.Signal(str(self.skip), width=seq.calc_width(self.skip+1), init=0)
        elif type(self.skip) is seq.Signal:
            self.sequencer.register_port(seq.Port(self.skip, "input"))
        else:
            raise Exception("Unknown skip type in %s" % (self, ))

    def _vlog_gen_declare(self):
        return ["wire [%d:0] count_down_%s_next_pre_;" % (self.reg.width, self.name, ),
                "wire [%d:0] count_down_%s_next_;" % (self.reg.width-1, self.name, ), ]

    def _vlog_gen_logic(self):
        s = [ "/* verilator lint_off WIDTH */", 
              "assign count_down_%s_next_pre_ = %s - %s;" % (self.name, self.reg.name, self.skip.name),
              "/* verilator lint_on WIDTH */",
              "assign count_down_%s_next_ = (count_down_%s_next_pre_[%d]) ? 0 : count_down_%s_next_pre_[%d:0];" % (self.name, self.name, self.reg.width, self.name, self.reg.width-1, ), ]
        # prevent overflow
        return s

    def _vlog_gen_seq(self):
        s = [ "if(%s && (count_down_%s_next_ >= %s)) %s <= count_down_%s_next_;" % (self.running, self.name, self.stop.name, self.reg.name, self.name) ]
        return s

    def _vlog_gen_done(self):
        return "%s & count_down_%s_next_ <= %s" % (self.running, self.name, self.stop.name, )
################################################################################

################################################################################
class CountUp(CountDown):
    """Takes 'sig' and counts it down until the 'stop' param has been
reached.  The increment value is 'skip'.  Overflow is watched and
accounted for, so it is safe to set the stop param to max value."""

    def _vlog_gen_declare(self):
        return ["wire [%d:0] count_up_%s_next_pre_;" % (self.reg.width, self.name, ),
                "wire [%d:0] count_up_%s_next_;" % (self.reg.width-1, self.name, ), ]

    def _vlog_gen_logic(self):
        s = [  "/* verilator lint_off WIDTH */", 
               "assign count_up_%s_next_pre_ = %s + %s;" % (self.name, self.reg.name, self.skip.name),
               "/* verilator lint_on WIDTH */", 
              "assign count_up_%s_next_ = (count_up_%s_next_pre_[%d]) ? {%d{1'b1}} : count_up_%s_next_pre_[%d:0];" % (self.name, self.name, self.reg.width, self.reg.width, self.name, self.reg.width-1, ), ]
        # prevent overflow
        return s

    def _vlog_gen_seq(self):
        s = [ "if(%s && (count_up_%s_next_ <= %s)) %s <= count_up_%s_next_;" % (self.running, self.name, self.stop.name, self.reg.name, self.name) ]
        return s

    def _vlog_gen_done(self):
        return "%s & count_up_%s_next_ >= %s" % (self.running, self.name, self.stop.name, )
################################################################################

################################################################################
class SerialMultiply(Sequence):
    """
The SerialMultiply sequence will multiply two signals together using an
adder/shifter in the same way people do long multiplication by hand. 
Signal 'a' is multiplied with signal 'b'. It will take as many clock
cycles as the width of the signal 'b'. The signal 'out' updated
when done.

:param a: Signal or int that is the first input to be multiplied.
:param b: Signal or int that is the second input to be multiplied.
:param out: reg (signal or string) to save the result in.

Example: Suppose your Sequencer has a registers named 'X', 'Y', and
'Z', then you can set them as follows:
  
  SerialMultiply(a=X, b=Y, out=Z)

"""
    def __init__(self, a, b, out, **kw):
        self.ab = [a,b]
        self.out = out
        Sequence.__init__(self, **kw)

    def link(self, sequencer, parent, data):
        Sequence.link(self, sequencer, parent, data)

        # create the signals in a mapping for easy lookup and
        # put Signals into the port list if they are setting
        # to a signal rather than a constant.
        self.mapping = {}
        self.inputs = {}
        for i,ab in self.ab:
            if type(ab) is str: # replace string with reg Signal
                self.ab[i] = self.use_reg(ab)
            elif(type(ab) is int):
                self.ab[i] = seq.Signal(str(self.stop_count), width=seq.calc_width(self.stop_count+1), init=0)

            if not(self.sequencer.regs.has_key(k)):
                raise Exception("Parent does not have a register called %s in Sequence %s %s" % (k, self.name, self))

            if type(v) is seq.Signal:
                val = v.name
                self.sequencer.register_port(seq.Port(v, "input")) # create as in input port as it must be supplied externally
            else:
                val = v

            self.mapping[k] = str(val)

    def _vlog_gen_seq(self, set_at_end=False):
        if(self.mapping):
            s = []
            if(self.dryrun):
                s.append("if(!(%s)) begin" % self.dryrun)

            if self.set_at_end:
                s.append("if(%s) begin" % (self.done, ))
            else:
                s.append("if(%s) begin" % (self.start, ))

            for sig, val in self.mapping.iteritems():
                s.append("  %s <= %s;" % (sig, val))
            s.append("end")

            if(self.dryrun):
                s.append("end")
            return s
        else:
            return []
    
    def _vlog_gen_running(self):
        return [ "%s <= %s;" % (self.running, self.start,) ]

    def _vlog_gen_done(self):
        return self.running
################################################################################
