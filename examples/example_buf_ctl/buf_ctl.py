import seq
from seq import Bin, Sequence as Seq

# inputs
detach       = seq.Signal(name="detach",          width=1)
read_running = seq.Signal(name="read_running",    width=1)
read_done    = seq.Signal(name="read_done",       width=1)
write_done   = seq.Signal(name="write_done",      width=1)

# output registers
write_ptr    = seq.Signal(name="write_ptr",       width=1, init=0)
read_ptr     = seq.Signal(name="read_ptr",        width=1, init=0)
write_mode   = seq.Signal(name="write_mode",      width=1, init=0)
read_mode    = seq.Signal(name="read_mode",       width=1, init=0)
buf_swap     = seq.Signal(name="buffers_swapped", width=1, init=0)

capture= Bin.Bin(
    name = "capture_buf",
    regs = [ write_ptr, read_ptr, write_mode, buf_swap ],
    children = [],
    seqs = [
        Seq.Serial(
            name="capture",
            subseqs = [ Seq.Set(set=dict(write_mode=1)),
                        Seq.Sync(sync=write_done),
                        Seq.Set(set=dict(write_mode=0)),
                        ]
                   ),
        Seq.Serial(
            name="sync_then_buf_swap",
            subseqs = [ Seq.Sync(sync=read_running, active_high=False),
                        Seq.Trigger(reg="buffers_swapped"),
                        Seq.Serial(subseqs=[Seq.Set(set=dict(read_ptr=write_ptr)),
                                            Seq.Toggle(reg="write_ptr"),]),
                        ]
            )
        ]
    )

read= Bin.Bin(
    name = "read_buf",
    register_done=True,
    regs = [ read_mode, ],
    children = [],
    seqs = [
        Seq.Serial(name="read", 
                   subseqs=[ Seq.Set(set=dict(read_mode=1)),
                             Seq.Sync(sync=read_done),
                             Seq.Set(set=dict(read_mode=0)),
                             ],
                   running=read_running, # export running signal as the sync
                   ),
        ],
    )

buf = Bin.Bin(
    name = "buf_ctl",
    regs = [],
    children = [read, capture,],
    seqs = [
        Seq.Serial(name="buf", 
                   subseqs=[ "capture", 
                             "sync_then_buf_swap", 
                             Seq.Child(sequence="read", detach=detach), ]),
        ],
    )

buf.vlog_dump(recurse=True) # create verilog
buf.vlog_gen_instance()     # create a verilog instantatiation
