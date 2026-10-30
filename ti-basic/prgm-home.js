// prgmHOME — the menu home screen this page runs. Plain TI-BASIC source.
(function (global) {
  global.PRGM_HOME = String.raw`:ClrHome
:Lbl 0
:Menu("PLAYGROUND OS","ABOUT",A,"DICE",B,"COUNTER",C,"GUESS 1-100",D,"KEY CODES",E,"QUIT",Q)
:Lbl A
:ClrHome
:Disp "THIS PAGE RUNS","A TI-BASIC","PROGRAM IN YOUR","BROWSER.",""
:Disp "EDIT IT, THEN","PRESS RUN."
:Output(8,1,"[ENTER] MENU")
:Pause
:Goto 0
:Lbl B
:ClrHome
:Output(1,1,"DICE")
:Output(7,1,"[ENTER] ROLL")
:Output(8,1,"[CLEAR] MENU")
:105→K
:Repeat K=45
:If K=105
:Then
:randInt(1,6)→A
:randInt(1,6)→B
:Output(4,1,"                ")
:Output(4,3,A)
:Output(4,5,"+")
:Output(4,7,B)
:Output(4,9,"=")
:Output(4,11,A+B)
:End
:Repeat K:getKey→K:End
:End
:Goto 0
:Lbl C
:ClrHome
:Output(1,1,"COUNTER")
:Output(7,1,"[UP/DN] COUNT")
:Output(8,1,"[CLEAR] MENU")
:0→N
:Repeat K=45
:Output(4,1,"                ")
:Output(4,8,N)
:Repeat K:getKey→K:End
:N+(K=25)-(K=34)→N
:End
:Goto 0
:Lbl D
:ClrHome
:randInt(1,100)→X
:0→T
:Disp "I'M THINKING OF","A NUMBER 1-100."
:Repeat G=X
:Input "GUESS? ",G
:T+1→T
:If G<X
:Then
:Disp "  HIGHER..."
:Else
:If G>X
:Disp "  LOWER..."
:End
:End
:Disp "GOT IT! TRIES:",T
:Pause
:Goto 0
:Lbl E
:ClrHome
:Output(1,1,"KEY CODES")
:Output(3,1,"PRESS ANY KEY")
:Output(8,1,"[CLEAR] MENU")
:Repeat K=45
:Repeat K:getKey→K:End
:Output(5,1,"CODE:")
:Output(5,7,"   ")
:Output(5,7,K)
:End
:Goto 0
:Lbl Q
:ClrHome
:Disp "SEE YOU LATER!"
`;
})(typeof window !== 'undefined' ? window : globalThis);
