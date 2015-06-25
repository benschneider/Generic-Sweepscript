(Currenly uploaded and intended for myself)
Note: As I use the script I will improve it.

This little script sweeps both a Yokogawa Voltage source and a VNA in CW mode,
most setting on the VNA still have to be set by hand first.
(This is more of a quick and dirty measurement)
The data is then stored into an *.mtx file format (1st 2 lines is the header (sizes, limits e.t.c), rest of the file is a 3d numpy data array in binary).
This file can then be quickly opened with a program called 'spyview'

-Cheers,
Ben