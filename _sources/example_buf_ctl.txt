Detach Example
==============

This example shows how to use the ``detach`` keyword option an a child
sequence to allow it to run optionally in parallel to children from
other bins.  In this example we have a stream of data coming from a
data source that bursts a chunk of data that needs buffered for a read
source that runs at a slower burst rate. To deal with this we take a
chunk of memory and divide in two. Initially we give the lower half
to the capture device to burst data into. When it has filled the
lower half, we then want the read source to take over the lower half
and give the upper to the capture source to use. We want the option
of making memory access simultaneous or not. When the capture and
read source are done, we want to swap the buffers again and repeat
swapping buffers.

Here is the ``seq`` code that impliments this double buffer memory
access controller that contains an input port called ``detach`` that
controls whether memory access is simultaneously or not.

.. literalinclude:: ../../examples/example_buf_ctl/buf_ctl.py
   :linenos:

The hierarch for this controller is that the ``capture_buf`` and ``read_buf``
bin are children of the ``buf_ctl`` bin.::


               +---------------+
               |    buf_ctl    |
               +---------------+
                  /         \
                 /           \
      +---------------+  +---------------+
      |  capture_buf  |  |   read_buf    |
      +---------------+  +---------------+

Let's take a top down approach in explaining this example by starting
with the buf_ctrl bin as defined in lines 56-66. The buf_ctl bin does
not control any registers directly (line 58) but is in control of the
read and capture bins (line 59). It has one Serial sequence (lines 61)
that executes three child sequence: "capture", "sync_then_buf_swap",
and "read". This is a pretty good verbal description of what we want
to have happen. First we want to capture a buffer ("capture"), then we
want to wait for any read than might be occuring in parallel from the
previous capture ("sync"). Once we are sync'd, we can swap the buffer
pointers ("then_buf_swap"). With the buffer pointers swapped, we can
kick off a the read ("read"). 

Notice that the "read" instantiation on line 64 is uses the ``detach``
key word and hooks it up the the detach signal, which becomes an
import port. If detach is not low, then the "read" sequence will run
to completion, otherwise, the "read" sequence will get kicked off in
the background and the sequence will return immediately. If the
buf_ctl is run in a loop, then when detached, a "capture" sequence
will start up while the "read" sequence is still running. Then, if the
capture sequence is longer, the sync condition of the
"sync_then_buf_swap" will be true and there will be no waiting,
otherwise if the "read" is still occuring when the "capture"
completes, the "sync_then_buf_swap" will stall until the "read" is
complete. It will then swap buffer pointers and process with the
read. If the read was not detached, then the read will be complete
when entering the sync state and it will exit immediately. In this
way, the access to the memory can be controlled to be simultaneous or
not.

In order for two child processes to run simultaneous, they must
be in different bins. This is why the "capture" and "sync_then_buf_swap"
sequences are in a different bin than the "read" sequence. This allows
the "capture" and "sync_then_buf_swap" to run at the same time as the
"read" sequence.

Now let's look at the "capture_buf" bin (lines 17-38). This bin
controls 4 registers that get exported as outputs. The "write_ptr" and
"read_ptr" are single bit signals that tell the capture and read
modules which half of the memory they have access to. The "write_mode"
register is a signal to the capture device that it can write to the
buffer specified by write_ptr.  The "buf_swap" register gets turned
into a trigger that fires whenever the buffers swap. In this example
it is purely used for informational purposes.

The "capture_buf" bin has two sequences. The first is called "capture"
(lines 22-28). This serial sequence uses three embedded sequences that
set the "write_mode" high (line 24), then wait for the capture device
to send back the sync signal "write_done" (line 25), and then drops
the "write_mode" signal so that the write device can wait for its next
opportunity.

The "sync_then_buf_swap" is a also a serial sequence that first waits
for the read to stop running (line 31), then triggers the "buffers_swapped"
signal, then swaps the "read_ptr" and "write_ptr" and completes.

THe "read" bin contains a single "read" sequence which is identical in
nature to the "capture" sequence except that its "running" state is
exported to the "read_running" signal so that the "sync_then_buf_swap"
can know sync to it.

Here is a timing diamgram of this controller in action:

.. image:: _static/example_buf_ctl.png

The pink shaded portions show the "write_mode" and "read_mode" signals
when detach is low. You can see that access to the memory is
synchronized. When detach goes high as shown in the green shaded
portions, you can see that as soon as data is available to the read
device, that access to the memory is simultaneous. In this example,
the read device takes about two time longer than the capture device,
and as shown the capture device always waits for the read to finish
before buffers are swapped.

The top level test bench that was used to generate this simulation
is as follows:

.. literalinclude:: ../../examples/example_buf_ctl/buf_ctl_tb.v


