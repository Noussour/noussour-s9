dtmc

// Parametres pedagogiques : p >= 0, f >= 0, p+f <= 1.
const double p = 0.70;
const double f = 0.05;

module reservation
  // 0 : en attente ; 1 : confirmee ; 2 : defaillance terminale
  s : [0..2] init 0;
  [] s=0 -> p:(s'=1) + f:(s'=2) + (1-p-f):(s'=0);
  [] s=1 -> (s'=1);
  [] s=2 -> (s'=2);
endmodule

label "confirmee" = s=1;
label "defaillance" = s=2;
label "attente" = s=0;
