/**
 * Built-in programs.
 *
 * Every Disp line is authored to fit the 16-column display without wrapping,
 * and every Menu( item stays under 14 characters so the "1:" prefix fits.
 * Labels are two characters, as on real hardware.
 */

export const PORTFOLIO = `ClrHome
Disp "****************"
Disp "*              *"
Disp "*   JASON'S    *"
Disp "*  PORTFOLIO   *"
Disp "*              *"
Disp "****************"
Disp "   UX / AI"
Pause
Lbl MM
ClrHome
Menu("PORTFOLIO","VIEW PROJECTS",PR,"ABOUT ME",AB,"CONTACT",CO,"EXIT",QT)
Lbl PR
ClrHome
Menu("PROJECTS","TURFKEY",P1,"MACHINE&MAKERS",P2,"MODEL DESIGN",P3,"BACK",MM)
Lbl P1
ClrHome
Disp "TURFKEY"
Disp "----------------"
Disp "AI TURF CARE"
Disp "PLATFORM FOR"
Disp "GROUNDS TEAMS."
Disp "ROLE: LEAD UX"
Disp "YEAR: 2024"
Pause
Goto PR
Lbl P2
ClrHome
Disp "MACHINE&MAKERS"
Disp "----------------"
Disp "DESIGN SYSTEM +"
Disp "BRAND FOR A MFG"
Disp "MARKETPLACE."
Disp "ROLE: PRODUCT"
Disp "YEAR: 2023"
Pause
Goto PR
Lbl P3
ClrHome
Disp "MODEL DESIGN"
Disp "----------------"
Disp "DESIGN PATTERNS"
Disp "FOR AI-NATIVE"
Disp "INTERFACES."
Disp "ROLE: RESEARCH"
Disp "YEAR: 2025"
Pause
Goto PR
Lbl AB
ClrHome
Disp "ABOUT ME"
Disp "----------------"
Disp "UX/AI DESIGNER"
Disp "~15 YRS EXP"
Disp "EDU: DESIGN BA"
Disp "BASED: ATLANTA"
Disp "NOW: AI TOOLING"
Pause
Goto MM
Lbl CO
ClrHome
Disp "CONTACT"
Disp "----------------"
Disp "PORTFOLIO:"
Disp "JASONJAMES"
Disp ".DESIGN"
Disp "EMAIL:"
Disp "HI@JASONJAMES"
Disp ".DESIGN"
Pause
Goto MM
Lbl QT
ClrHome
Disp "THANKS FOR"
Disp "VISITING."
Disp ""
Disp "JASONJAMES"
Disp ".DESIGN"
Stop`;

/** Quadratic solver — exercises Input, If/Then/Else and the math library. */
export const QUAD = `ClrHome
Disp "AX²+BX+C=0"
Input "A=",A
Input "B=",B
Input "C=",C
B²-4AC→D
ClrHome
If D<0
Then
Disp "NO REAL ROOTS"
Disp "DISC=",D
Else
Disp "X1=",(-B+√(D))/(2A)
Disp "X2=",(-B-√(D))/(2A)
End
Pause
Stop`;

/** Loop demo — exercises For/End with a negative step. */
export const COUNT = `ClrHome
Disp "COUNTDOWN"
Disp "----------------"
For(I,5,1,-1)
Disp I
End
Disp "LIFTOFF!"
Pause
Stop`;

export const DEFAULT_PROGRAMS = [
  { name: 'PORTFOLIO', source: PORTFOLIO },
  { name: 'QUAD', source: QUAD },
  { name: 'COUNT', source: COUNT },
];
