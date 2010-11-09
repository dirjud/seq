module buf_ctl_tb();
   
   reg clk, reset_n, start, detach, read_done, write_done;
   wire read_ptr, write_ptr, read_mode, write_mode, buffers_swapped, running, done;
   always #1 clk = !clk;
   
   initial begin
      clk = 0;
      reset_n = 0;
      start = 0;
      detach = 0;
      write_done = 0;
      read_done = 0;

      $dumpfile("buf_ctl.vcd");
      $dumpvars(0, buf_ctl_tb);
      
      repeat(4) @(posedge clk);
      reset_n = 1;
      repeat(4) @(posedge clk);

      run();
      run();
      @(posedge clk) detach=1;
      @(posedge clk);
      run();
      run();
      run();
      $finish;
   end

   task run; // run a buffer through
      begin
	 @(posedge clk) start <= 1;
	 @(posedge clk) start <= 0;
	 @(posedge clk);
	 while(running) @(posedge clk);
      end
   endtask

   reg [7:0] mem[0:511]; //Shared memory buffer.

   /************************* A Capture Device ******************************/
   reg 	     capture_state;
   reg [8:0] capture_count;
   reg [7:0] capture_xin;
   always @(posedge clk or negedge reset_n) begin
      if(!reset_n) begin
	 capture_state <= 0;
	 capture_count <= 0;
	 write_done    <= 0;
      end else begin
	 case(capture_state)
	   0: begin
	      if(write_mode && !write_done) capture_state <= 1;
	      capture_count <= 0;
	      write_done    <= 0;
	   end

	   1: begin
	      if(capture_count == 255) begin
		 capture_state <= 0;
		 write_done <= 1;
	      end
	      capture_count <= capture_count + 1;
	      capture_xin = $random;
	      if(write_ptr) begin //when write_ptr is 1, we get top half of mem
		 mem[capture_count+256] <= capture_xin;
	      end else begin // otherwise we use the lower half of the mem
		 mem[capture_count+000] <= capture_xin;
	      end
	      $display("capture, val=%d, addr=%d, ptr=%d", capture_xin, capture_count, write_ptr);
	   end
	   
	 endcase
      end
   end
   /*************************************************************************/

   /************************* A Read Device ******************************/
   reg 	     read_state;
   reg [8:0] read_count;
   reg 	     randbit; // randomly controls when we can read. When high, we read, otherwise we wait. simulates a device that can randomly read from memory.
   always @(posedge clk or negedge reset_n) begin
      if(!reset_n) begin
	 read_state <= 0;
	 read_done  <= 0;
	 randbit    <= 0;
      end else begin
	 randbit <= $random;
	 case(read_state)
	   0: begin
	      if(read_mode && !read_done) read_state <= 1;
	      read_count <= 0;
	      read_done  <= 0;
	   end

	   1: begin
	      if(randbit) begin
		 if(read_count == 255) begin
		    read_state <= 0;
		    read_done <= 1;
		 end
		 
		 read_count <= read_count + 1;
		 if(read_ptr) begin //when read_ptr is 1, we get top half of mem
		    $display("read, val=%d, addr=%d, ptr=%d", mem[read_count+256], read_count, read_ptr);
		 end else begin // otherwise we use the lower half of the mem
		    $display("read, val=%d, addr=%d. ptr=%d", mem[read_count], read_count, read_ptr);
		 end
	      end
	   end
	 endcase
      end
   end
   /*************************************************************************/

   always @(posedge clk) begin
      if(buffers_swapped) begin
	 $display("buffered swapped");
      end
   end
   
   buf_ctl u_buf_ctl_
     (.clk(clk),
      .reset_n(reset_n),

      // inputs
      .start(start),
      .seq(1'b0),
      .detach(detach),
      .write_done(write_done),
      .read_done(read_done),

      // outputs
      .read_ptr(read_ptr),
      .write_ptr(write_ptr),
      .read_mode(read_mode),
      .write_mode(write_mode),
      .buffers_swapped(buffers_swapped),
      .read_running(),
      .running(running),
      .done(done)
     );

endmodule