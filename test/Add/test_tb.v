module test_tb();
   reg clk, reset_n, start, runA, runB, passing;
   reg [2:0] seq;
   wire running, running1, done1;
   reg [3:0]  a1, b1;
   wire [4:0] out1;
   reg [4:0]  out1_should_be;

   reg signed [3:0]  a2, b2;
   wire signed [4:0] out2;
   reg signed [4:0]  out2_should_be;

   wire [3:0] 	     out3;
   reg [3:0]  out3_should_be;

   wire [3:0] out4;
   reg [3:0]  out4_should_be;

   wire signed [2:0] out5;
   reg signed [2:0]  out5_should_be;

   wire signed [3:0] out6;
   reg signed [3:0]  out6_should_be;

   wire signed [19:0] out7;
   reg signed [19:0]  out7_should_be;


   assign running = running1; // || running2;
   
   always #1 clk = !clk;
   
   initial begin
      clk = 0;
      reset_n = 0;
      seq = 0;
      start = 0;
      passing = 1;
      a1 = 0;
      b1 = 0;
      
      //$dumpfile("test.vcd");
      //$dumpvars(0, test_tb);

      repeat(4) @(posedge clk);
      reset_n = 1;

      runA = 1;
      while(runA) begin
	 runB = 1;
	 while(runB) begin
	    doit();
	    out1_should_be = a1+b1;
	    out2_should_be = a2+b2;
	    out3_should_be = a1+b1;
	    out4_should_be = (a1+b1 > 15) ? 15 : a1+b1;
	    out5_should_be = (a2+b2 > 3)  ? 3  : 
			     (a2+b2 < -4) ? -4 : a2+b2;
	    out6_should_be = (a2+b2 > 7)  ? 7  : 
			     (a2+b2 < -8) ? -8 : a2+b2;
	    out7_should_be = a2+b2;
	    passing = (out1 == out1_should_be) && passing;
	    passing = (out2 == out2_should_be) && passing;
	    passing = (out3 == out3_should_be) && passing;	    
	    passing = (out4 == out4_should_be) && passing;	    
	    passing = (out5 == out5_should_be) && passing;	    
	    passing = (out6 == out6_should_be) && passing;	    
	    passing = (out7 == out7_should_be) && passing;	    
	    //$display("a1=%d b1=%d out1=%d (%d) a2=%d b2=%d out2=%d (%d) out3=%d (%d) out4=%d (%d) out5=%d, out6=%d out7=%d PASS=%d", a1, b1, out1, out1_should_be, a2, b2, out2, out2_should_be, out3, out3_should_be, out4, out4_should_be, out5, out6, out7, passing);

	    if(b1==15) runB=0;
	    b1=b1+1;
	 end
	 if(a1==15) runA=0;
	 a1=a1+1;
      end
      $display("ALL PASSED=%d", passing);
      $finish;
   end

   test1 test1
     (
      .clk				(clk),
      .reset_n				(reset_n),
      .a1				(a1),
      .b1				(b1),
      .a2				(a2),
      .b2				(b2),
      .seq				(seq),
      .start				(start),
      .out1				(out1),
      .out2				(out2),
      .out3				(out3),
      .out4				(out4),
      .out5				(out5),
      .out6				(out6),
      .out7				(out7),
      .running				(running1),
      .done				(done1)
      );
   
   task doit;
      begin
	 a2=$signed(a1);
	 b2=$signed(b1);

	 for(seq=0; seq<7; seq=seq+1) begin
            start <= 1;
            @(posedge clk) 
   	      start <= 0;
            @(posedge clk);
   
            while(running)
   	      @(posedge clk);
            @(posedge clk);
	 end
      end
   endtask
endmodule