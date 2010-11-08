import seq
from seq import Bin, Sequence

ext_sync = seq.Signal(name="ext_sync", width=1)

example1 = Bin.Bin(
    name = "example1",
    seqs = [
        Sequence.Stall(count=10),
        Sequence.Sync(sync=ext_sync),
        ]
    )
    
example1.vlog_dump()
