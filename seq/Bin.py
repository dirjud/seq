import seq
import Sequence

class Bin(object):
    """A 'Bin' reprasents a state machine that serially executes
'Sequences'.  The state machine that can be generated from this class
from a 'Writer' generates HDL with a bin interface.  This interface
has two inputs that are HDL signals called 'start' and 'seq'.  The
user sets the 'seq' input to the desired sequence number and then pulses
the 'start' signal.  After receiving the 'start' signal, the bin
will assert its 'running' output to high and will hold it high until
the sequence has been executed to completion.  Upon completion, the
bin will also issue a one-shot 'done' pulse.  The user must
hold the 'seq' input constant while the sequener is 'running'.  If
the user issues a 'start' again while the bin is 'running', it
immediately terminates the running sequence and starts the sequence
specified by the input 'seq'.

'done' and 'running' may not be registered to provide the quickest
possible turnaround time.  The user should register these as
necessary.  The 'done' signal can be registered and sent back in if
the user want to run sequences back to back.  This means there is at
least one cycle 'wasted' time required to change when
starting/completing sequences.  You can implement custom Sequences,
however, to get around this in a critical section.

Bins execute a series of 'Sequences'.  Sequences must implement
the Sequence interface and can be things like ChildSequence, ...

"""
    
    def __init__(self, name, seqs, regs=[], children=[], register_done=True, reset_n="reset_n"):
        """
:param name : A string name for this bin.  The HDL writer will create a module with this name in a file with this name.  Think carefully about uniqueness.
:param seqs : A list of Sequences that this Bin controls.  The index number of each sequence becomes the 'seq' code used by the HDL
:param regs : A list of Signals that are the registers overwhich this Bin has control.  Any register in this list can be controlled by Sequences such as Set, Trigger, Toggle.
:param children : A list of children Bins that this Bin controls.  Make it an empty list if this is a base Bin with no children.
:param register_done: A boolean indicating whether the done signal from this bin is registered.  False will make the transition of child sequences faster but incure longer logic paths.  The logic can get quite long as hierarchy gets larger.  An occasional registering of the done signal can significantly reduce logic paths if the hierarchy of bins is deep.  Leave low level paths un-registered and register higher level sequences where an extra cycle delay in the transition is not critical.
"""
        self.name = name
        self.seqs = seqs
        self.children = children
        self._child_seqs = {}
        self.register_done = register_done
        self.reset_n = reset_n

        self.regs = {}
        self.ports = {}
        self._children_starts = {}

        for reg in regs:
            self.regs[reg.name] = reg
            self.ports[reg.name] = seq.Port(reg, "output", reg=True)

        # merge ports from child Bins in and remove any 'reg' qualifiers
        for child in self.children:
            for port in child.ports.values():
                # Check if this port is in our register list.  If so, we terminate
                # it at this level.  If not, then we propigate it up to the next level
                if self.regs.has_key(port.sig.name):
                    del self.ports[port.sig.name] # remove this reg from the output list
                else:
                    self.register_port(seq.Port(port.sig, port.dir, reg=False)) # add this signal to the output list and downgrade it from reg status

            for child_seq in child.seqs:
                if self._child_seqs.has_key(child_seq.name):
                    raise Exception("Sequence names must be unique.  %s is a duplicate" % child_seq.name)
                self._child_seqs[child_seq.name] = child_seq

            self._children_starts[child.name] = []

        # The self.allseqs a is flatten dict of all Sequences under
        # control of this Bin keyed off the name of each Sequence
        self.allseqs = dict()

        # Some Sequences need to share static data between all Sequences
        # of the same type.  This dict allows each Sequence to register
        # such static data however it likes.  The dict is keyed on type(seq)
        self._seqdata = {}

        # Link the bins
        self.link(self, self.seqs)

        # Now go through the seqs and generate several useful dictionaries
        # for easy access to the data.

        # The self.names dict is keyed on names that need to stay
        # unique in this HDL module.  Each seq registers any names it
        # needs in the self.names dictionary.
        self.names = {self.name : self}

        for seq_ in seqs:
            seq_.register_unique_names(self.names)

    def add_child_start(self, child_bin_name, start_sig_name):
        self._children_starts[child_bin_name].append(start_sig_name)
        
    def register_port(self, port):
        if(not(self.ports.has_key(port.sig.name)) or (port.dir == "output") or (self.ports[port.sig.name].dir == "input")):
            self.ports[port.sig.name] = port
            return True
        else:
            return False

    def __str__(self):
        return "<%s %s>" % (type(self), self.name)

    def link(self, parent, seqs):
        """:param allseqs: A dict keyed on Sequence names.  This module will
register himself in the allseqs dict and then register call this
method on his sub-Sequences.
:param child_seqs: 
"""
        for i,seq_ in enumerate(seqs):
            if type(seq_) is str:
                # Any strings in the self.seqs list will be assumed to be
                # Child Sequences and thus automatically replaced as such.
                seq_ = Sequence.Child(self._child_seqs[seq_])
                seqs[i] = seq_

            elif type(seq_) is seq.Signal:
                # Any signals will be assumed to be programmable Child Sequences
                seq_ = Sequence.Child(seq_)
                seqs[i] = seq_

            # register this sequence in the allseqs dict
            if self.allseqs.has_key(seq_.name):
                raise Exception("Name for Sequence %s is not unique" % seq_.name)
            self.allseqs[seq_.name] = seq_

            # link the bin to the sequence
            seq_.link(self, parent, self._seqdata)

            # link all subseqs of this seq
            self.link(seq_, seq_.subseqs)

    def get_reg(self, name):
        try:
            return self.regs[name]
        except KeyError:
            raise Exception("Requested register %s is not available in the bin. Did you forget to add it to the register list?" % name)

    def get_child_bin(self, seq_name):
        return self._child_seqs[seq_name].bin

    def _vlog_gen_done(self):
        s = []
        if(self.register_done):
            s.extend(["  reg done_reg;",
                      "  assign done = done_reg;",
                      "  always @(posedge clk or negedge reset_n) begin",
                      "    if(!reset_n) begin",
                      "      done_reg <= 0;",
                      "    end else begin",
                      "      done_reg <= done_;",
                      "    end",
                      "  end",
                      ])
        else:
            s.append("  assign done = done_;")
        return s


    def _vlog_gen_running(self):
        s = [ "  reg running_reg;",
              "  assign running = running_reg;",
              "  always @(posedge clk or negedge reset_n) begin",
              "    if(!reset_n) begin",
              "      running_reg <= 0;",
              "    end else begin",
              "      if(start) begin",
              "        running_reg <= 1;",
              "      end else if(done_) begin",
              "        running_reg <= 0;",
              "      end",
              "    end",
              "  end",  ]
        return s

    def vlog_dump(self, outdir="", filename=None, recurse=False):
        """Creates a verilog implementation of this Bin.

:param outdir: path to dump file in. Should include trailing path deliminter.
:param filename: If None, then the file will be called 'name'.v, where name is the name provided when you created this function.  Otherwise, the filename will be that specified by this parameter.
:param recurse: If True, then recursively dump verilog for all children.  filename cannot be specified for children when using this method
Example:
    seq_.vlog_dump("rtl_auto/")
"""
        if recurse:
            for child in self.children:
                child.vlog_dump(outdir, recurse=True)

        s = []
        
        # Print up the module header with the port assignments
        s = [ "module %s(" % self.name ]
        s.append("  input clk,")
        s.append("  input reset_n,")
        
        for port in self.ports.values():
            s.append("  %s," % (port.vlog_declaration(), ))
    
        s.append("\n  // control")
        width = seq.calc_width(len(self.seqs))
        s.append("  input [%d:0] seq," % (width-1, ))
        s.append("  input start,")
        s.append("  output running,")
        s.append("  output done);\n")

        s.append("  wire done_;")

        s.extend(self._vlog_gen_done())
        s.extend(self._vlog_gen_running())

        # create parameters for each state
        s.extend(self.vlog_gen_seq_params())
        for child in self.children:
            s.extend(child.vlog_gen_seq_params(prefix="child_%s" % child.name))

        for child in self.children:
            s.append("  wire child_%s_done_, child_%s_running_;" % (child.name, child.name, ))
            width = seq.calc_width(len(child.seqs))
            s.append("  reg [%d:0] child_%s_seq_;" % (width-1, child.name))
            s.append("  reg child_%s_start_;" % (child.name, ))
        s.append("")

        for reg in self.regs:
            if not(reg in self.ports.keys()):
                s.append("  %s;" % (self.regs[reg].vlog_declaration("reg")))


        # create subseq declaration logic
        for seq_ in self.allseqs.values():
            s.extend(seq_.vlog_gen_declare(indent=1))
        s.append("")

        # create done and running signal for all seqs
        for seq_ in self.allseqs.values():
            s.append("  wire %s;" % (seq_.done, ))
            s.append("  reg %s;"  % (seq_.running, ))
        s.append("")


        # start_reg wire
        for i, seq_ in enumerate(self.seqs):
            s.extend(seq_.vlog_gen_start_wire(start="start && (seq==%d)" % i, indent=1))
        s.append("")

        # Create the done logic for each seq
#        for i,seq in enumerate(self.seqs):
#            s.extend(seq_.vlog_gen_done(done="(seq==%d)" % i, indent=1))
        for seq_ in self.allseqs.values():
            s.append("  assign %s = %s;" % (seq_.done, seq_.vlog_gen_done()))
        s.append("")

        s.append("\n  assign done_ = (start || !running) ? 0 : ")
        for seq_ in self.seqs:
            s.append("              (seq == seq_%s_) ? %s :" % (seq_.name, seq_.done, ))
        s.append("              1;\n // default to 1 to prevent deadlocking when this bin is addressed out of range")

        # create subseq logic
        for seq_ in self.allseqs.values():
            s.extend(seq_.vlog_gen_logic(indent=1))
        s.append("")

        # Create the seq state machine
        s.append("  always @(posedge clk or negedge reset_n) begin")
        s.append("    if(!reset_n) begin")
        for child in self.children:
#            s.append("      child_%s_start_   <= 0;" % (child.name, ))
            s.append("      child_%s_seq_     <= 0;" % (child.name, ))
        for name, reg in self.regs.items():
            s.append("      %s <= %s;" % (name, str(reg.init)))
        for seq_ in self.allseqs.values():
            s.append("      %s <= 0;" % (seq_.running, ))
            s.extend(seq_.vlog_gen_reset(indent=3))
        s.append("")
        s.append("    end else begin")

        for seq_ in self.allseqs.values():
            s.extend(seq_.vlog_gen_running(indent=3))
        s.append("")
        
        s.append("      case(seq)")
        for seq_ in self.seqs:
            s.append("        seq_%s_: begin" % (seq_.name, ))
            s.extend(seq_.vlog_gen_seq(indent=5))
            s.append("")
            for seq_inactive in self.seqs:
                if not(seq_ is seq_inactive):
                    s.extend(seq_inactive.vlog_gen_inactive(indent=5))
            s.append("        end\n")
        s.append("      endcase\n")
        s.append("    end")
        s.append("  end\n")

        for seqtype, data in self._seqdata.items():
            s.extend(getattr(seqtype, "vlog_gen_static_logic")(self._seqdata))
        s.append("")

        s.append("  always @(posedge clk or negedge reset_n) begin")
        s.append("    if(!reset_n) begin")
        for name in self._children_starts:
            s.append("      child_%s_start_ <= 0;" % (name, ))
        s.append("    end else begin")
        for name, start in self._children_starts.items():
            s.append("      child_%s_start_ <= %s;" % (name, " || ".join(start), ))
        s.append("    end")
        s.append("  end\n")
        
        # Creates verilog instances of the children Bins
        for child in self.children:
            s.append
            s.append("  %s u_%s_(" % (child.name, child.name, ))
            s.append("    .clk(clk),")
            s.append("    .reset_n(reset_n),")
            for name, port in child.ports.items():
                s.append("    .%s(%s)," % (name, name, ))

            s.append("    .seq(child_%s_seq_)," % child.name)
            s.append("    .start(child_%s_start_)," % child.name)
            s.append("    .running(child_%s_running_)," % child.name)
            s.append("    .done(child_%s_done_)" % child.name)
            s.append("  );\n")

        s.append("endmodule\n")

        if not filename:
            filename = self.name + ".v"
        dump_file(outdir + filename, s, comment="//")

    def gen_param_mapping(self, outdir="", recurse=False):
        """Dumps a parameter mapping file useful for debugging in a
        wave viewer like simvision or gtkwaves"""
        if recurse:
            for child in self.children:
                child.gen_param_mapping(outdir, recurse=True)

        f=open(outdir + self.name + ".map", "w")
        for i, seq_ in enumerate(self.seqs):
            f.write("%d %s\n" % (i, seq_.name, )) # decimal representation
#            f.write("%x %s\n" % (i, state.name, )) # hex 
        f.close()



    def vlog_gen_seq_params(self, prefix="seq"):
        """Prints up a unique parameter and name associated with each
        of the possible states in this module.  The prefix parameter gets
        appended to the front of each parameter name.
        """
        s = []
        for i, seq_ in enumerate(self.seqs):
            s.append("  parameter %s_%s_ = %d;" % (prefix, seq_.name, i, ))
        s[-1] += "\n"
        return s




    def vlog_gen_instance(self, outdir="", wires_filename=None, inst_filename=None):
        """Creates a verilog file instancing self (useful only for the top
level)"""
        s = []
        for name, port in self.ports.iteritems():
            if(port.dir == "output"):
                sig = port.sig
                if(sig.width==1):
                    s.append("  wire %s;" % (name, ))
                else:
                    s.append("  wire [%d:0] %s;" % (sig.width-1, name))

        s.append("  wire %s_running, %s_done;" % (self.name, self.name,))
        if not wires_filename:
            wires_filename = self.name + "_wires.v"
        dump_file(outdir + wires_filename, s)

        s = []
        s.append("  %s u_%s_(" % (self.name, self.name, ))
        s.append("    .clk(clk),")
        s.append("    .reset_n(%s)," % self.reset_n)
        for name, port in self.ports.items():
            s.append("    .%s(%s)," % (name, name, ))
        s.append("    .seq(%s_seq)," % self.name)
        s.append("    .start(%s_start)," % self.name)
        s.append("    .running(%s_running)," % self.name)
        s.append("    .done(%s_done)" % self.name)
        s.append("  );\n")


        if not inst_filename:
            inst_filename = self.name + "_instance.v"
        dump_file(outdir + inst_filename, s)



class Len1Bin(Bin):
    """A 'Len1Bin' extends Bin but must only be used with
Sequences that are guarenteed to only take a single clock cycle to
complete.  Because a Len1Bin assumes each of its Sequences will
complete in a single clock cycle, can export its done and running
signal without any logical dependance on its member Sequences, thus
realizing hardware savings.  So this Bin realizes logic savings
can produce a registered done output in a single clock cycle, which is
not possible with the more general Bin.  Therefore, with this
bin, the 'registered_done' condition is realized in a single
clock cycle regardless.

The onerous is upon the user to ensure the member Sequences assign to
this bin are of length 1.  Unknown and unpredictable results
will occur if that is not the case.

Debugging hint: One way to check that all the member Sequences are
indeed length 1 sequences is to compare the 'done' output signal with
the 'done_' internal signal.  The internal 'done_' signal is still
generated based on the done condition of the member Sequences, but it
is ignored by this Bin and assumed to occur immediately.
Therefore, this Sequncer generates its output done condition by simply
sampling the start input.  If the internal 'done_' signal, however is
not following the output 'done' signal, then it means this assumption
is not valid and you are going to get unknown results.  Some Sequences
may behave just fine if they cut short while others may not.
"""

    def _vlog_gen_done(self):
        """Here we ignore the state of self.register_done and just produce a registered
           done output that just samples the start signal.  This effectively ignores
           the done logic of all the member Sequences, so while the internal done_ signal
           will still be generated, it should get optimized away by synthesis tools.  Simulation
           tools will keep the done_ signal, which can be useful to verify that all the 
           member Sequences are indeed length 1.
           """
        s = []
        s.extend(["  reg done_reg;",
                  "  assign done = done_reg;",
                  "  always @(posedge clk or negedge reset_n) begin",
                  "    if(!reset_n) begin",
                  "      done_reg <= 0;",
                  "    end else begin",
                  "      done_reg <= start;",
                  "    end",
                  "  end",
                  ])
        return s


    def _vlog_gen_running(self):
        """running and done are the same for this Bin."""
        return  [ "  assign running = done_reg;", ]


def dump_file(filename, s, comment="//"):
    f = open(filename, "w")
    from datetime import datetime
    import os
    f.write("%s %s\n" % (comment, "*"*70))
    f.write("%s This file was automatically generated on %s by %s.\n" % (comment, datetime.now().strftime("%b %d, %Y at %H:%M"), os.environ["USER"]));
    f.write("%s DO NOT EDIT THIS FILE BY HAND!!!!  Your changes will be overwritten\n" % (comment, ));
    f.write("%s %s\n" % (comment, "*"*70))
    for l in s:
        f.write(l)
        f.write("\n")
    f.close()
    

