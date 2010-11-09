import seq
from seq import Bin, Sequence as Seq

read_running = seq.Signal(name="read_running", width=1)
read_done    = seq.Signal(name="read_done",    width=1)
dev_done     = seq.Signal(name="dev_done",     width=1)
write_ptr    = seq.Signal(name="write_ptr",    width=1, init=0)
read_ptr     = seq.Signal(name="read_ptr",     width=1, init=0)

capture= Bin.Bin(
    name = "capture_buf",
    regs = [ write_ptr,
             read_ptr,
             seq.Signal(name="dev_write_mode", width=1, init=0),
             seq.Signal(name="buffers_swapped", width=1, init=0),
             ],
    children = [],
    seqs = [
        Seq.Serial(
            name="capture",
            subseqs = [ Seq.Set(set=dict(dev_write_mode=0)), # just in case, send low first
                        Seq.Set(set=dict(dev_write_mode=1)),
                        Seq.Sync(sync=dev_done, active_high=False),
                        Seq.Sync(sync=dev_done),
                        Seq.Set(set=dict(dev_write_mode=0)),
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
    regs = [ seq.Signal(name="sdram_read_mode", width=1, init=0),
             ],
    children = [],
    seqs = [
        Seq.Serial(name="read", 
                   subseqs=[ Seq.Set(set=dict(sdram_read_mode=1)),
                             Seq.Sync(sync=read_done),
                             Seq.Set(set=dict(sdram_read_mode=0)),
                             ],
                   running=read_running,
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
                             Seq.Child(sequence="read", detach=True), ]),
        ],
    reset_n = "buf_ctl_reset_n"
    )

# create verilog
buf.vlog_dump(recurse=True)
buf.vlog_gen_instance()
