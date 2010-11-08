module example1_manual
  (
   input clk,
   input reset_n,
   input ext_sync,     // external sync
   input seq,          // controls which sequence is executed
   input start,        // starts the sequence
   output reg running, // indicates sequence is running
   output reg done     // indicates sequence is done
   );

   reg [3:0] stall_count;
   
   always @(posedge clk or negedge reset_n) begin
      if(!reset_n) begin
	 running     <= 0;
	 done        <= 0;
	 stall_count <= 0;
      end else begin

	 if(start) begin
	    running <= 1;
	    done    <= 0;
	 end else if(done) begin
	    done    <= 0;
	 end else if(running) begin
	    case(seq)

	      0: begin // in this state just stall 10 cycles
		 stall_count <= stall_count + 1;
		 if(stall_count >= 10) begin
		    running <= 0;
		    done <= 1;
		 end 
	      end
	      
	      1: begin // in that state wait for external sync
		 if(ext_sync) begin
		    running <= 0;
		    done <= 1;
		 end
	      end
	      endcase
	 end else begin
	    done <= 0;
	 end

      end
   end
endmodule

