module example1_tb();
   reg clk, reset_n, ext_sync, seq, start, passing;
   reg [3:0] counter_auto, counter_manual;
   
   always begin // generate a clock
      #10 clk = !clk;
   end

   initial begin // run some sequences
      clk = 0;
      reset_n = 0;
      ext_sync = 0;
      seq = 0;
      start = 0;
      passing = 1;

      $dumpfile("example1.vcd");
      $dumpvars(0, example1_tb);
      
      #50 reset_n = 1;

      repeat(10) @(posedge clk); // wait ten clock cycles

      run_seq(0);       // run a seq=0 seqence
      if(counter_auto==10 && counter_manual==10) begin
	 $display("  PASS: result is correct.");
      end else begin
	 passing = 0;
	 $display("  FAIL: counters should match and equal 10.");
      end
      

      repeat(4) @(posedge clk); // wait some clock cycles
      run_seq(1); // run a seq=1 sequence
      if(counter_auto==15 && counter_manual==15) begin
	 $display("  PASS: result is correct.");
      end else begin
	 passing = 0;
	 $display("  FAIL: counters should match and equal 10.");
      end

      $display("ALL TESTS PASSING=%d", passing);

      repeat(4) @(posedge clk); // wait some clock cycles
      $finish;
      
   end

   reg [4:0] sync_count;
   always @(posedge clk) begin
      if(seq == 1) begin
	 if(start == 1) begin
	    sync_count <= 0;
	 end else begin
	    if(sync_count == 14) begin
	       ext_sync <= 1;
	    end else begin
	       sync_count <= sync_count + 1;
	    end
	 end
      end else begin
	 sync_count <= 0;
	 ext_sync <= 0;
      end
   end
      
   
   example1 example1
     (.clk				(clk),
      .reset_n				(reset_n),
      .ext_sync				(ext_sync),
      .seq				(seq),
      .start				(start),
      .running				(running_auto),
      .done				(done_auto));

   example1_manual example1_manual
     (.clk				(clk),
      .reset_n				(reset_n),
      .ext_sync				(ext_sync),
      .seq				(seq),
      .start				(start),
      .running				(running_manual),
      .done				(done_manual));
   

   task run_seq;
      input which;
      begin
	 seq   = which;
	 start = 1;
	 @(posedge clk);
	 start = 0;
	 counter_auto   = 0;
	 counter_manual = 0;
	 // wait until both sequencers finish and count the number of cycles
	 while(running_auto && running_manual) begin
	    @(posedge clk) begin
	       if(running_auto)   counter_auto   <= counter_auto + 1;
	       if(running_manual) counter_manual <= counter_manual + 1;
	    end
	 end
	 $display("seq=%d: counter_auto=%d  counter_manual=%d", seq, counter_auto, counter_manual);
      end
   endtask

endmodule