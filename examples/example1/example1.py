import seq
from seq import Sequencer, Sequence


ext_sync = seq.Signal(name="ext_sync", width=1)

example1 = Sequencer.Sequencer(
    name = "example1",
    seqs = [
        Sequence.Stall(name="stall",    count=10),
        Sequence.Sync( name="ext_sync", sync=ext_sync),
        ]
    )
    
example1.vlog_dump()
