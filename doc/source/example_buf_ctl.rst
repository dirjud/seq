Detach Example
==============

This example shows how to use the ``detach`` keyword option an a child
sequence to allow it to run in parallel to children from other bins.
In this example we have a stream of data coming from an image sensor
that needs double buffered in an SDRAM. The SDRAM is divided into two
buffers. While the image stream is being captured into one buffer
(write buffer), the application can read the previous image from the
other buffer (read buffer). When both actions are complete, we
want to swap the read and write pointers and repeat the process.

.. literalinclude:: ../../examples/example_buf_ctl/buf_ctl.py

New in this example:
* detaching and using the running signal to sync
* vlog_dump_instance()
