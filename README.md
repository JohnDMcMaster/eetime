# eetime
EPROM Erasure Time: a suite for characterizing EPROMs

High level requirements:
  * Linux
    * MacOS might work but is untested and I don't have instructions
  * TL866 (minipro) family of USB programmer
  * Can expose chip to UV while in the EPROM programmer

Refernece setup:
  * Ubuntu 20.04
  * Original TL866
  * Spectronics PE-140T EPROM eraser
  * 3D printed adapter
  * See: https://twitter.com/johndmcmaster/status/1505276794156376066

More detailed requirements:
*  You'll need to run the EPROM programmer while the UV source is on
    * WARNING: UV light is harmful to eyes and skin
    * Take all necessary safety precautions, especially if you modify hardware
    * TL866 is compact and may fit into some erasers
    * Socket extension cable might work
*  EPROM isn't sensitive to optical fault injection from your UV source
  *  If your light source is too strong it will glitch the chip
  *  Shouldn't be the case for commodity EPROM erasers


## Installation

Install minipro software: https://gitlab.com/DavidGriffith/minipro

For basic data collection there are currently no additional python dependencies. However if you want to graph you'll also need a bunch more stuff (WIP)

```
numpy
matplotlib
```

## Usage

Use minipro -l to find your device. Example:

```
$ minipro -l |grep 27C256
27C256 @DIP28
27C256 @DIP28 #2
27C256 @DIP28 #3
27C256 @PLCC32
...
```

I'm using Intel D27C256 which doens't appear in the list, so I'll use the closest match (generic "27C256 @DIP28")

Start by seeing if you can talk to minipro using check.py. For example:

```
$ ./check.py --verbose --device "27C256 @DIP28"
```

If all goes ok it should report whether or not your EPROM is currently blank.


### Fully automated collection

Requirements:
* Slow EPROM erase vs programming time
  * Can program the EPROM w/o affecting erase time too much

Example:

```
$ ./collect.py --device '27C256 @DIP28' --verbose --passes 10 --write-init --postfix intel_d27c256
```

### Manual collection

This is intended for high intensity sources.

First zero out the EPROM:

```
$ ./zero.py --device '27C256 @DIP28' --verbose
```

Now turn on your UV source and immediately run:

```
$ ./collect.py --device '27C256 @DIP28' --verbose --postfix intel_d27c256
```

### Plotting

Either filenames or a single directory can be given. Examples:

```
$ ./plot.py log/2022-03-19_01_intel_d27c256
$ ./plot.py log/2022-03-19_01_intel_d27c256/*.jl log/2022-03-19_02_intel_d27c256/*.jl
```
