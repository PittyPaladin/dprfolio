+++
title = "A driver for my Ublox M9: Introduction"
date = "2025-12-27"
description = "Article introducing my driver project with a commercial GNSS receiver."
tags = [
    "gnss",
    "ublox",
    "receiver",
    "driver"
]
+++


## Motivation
Even though I love my profession and quite like where I work, I (as many others) have always desired to create and own a product from scratch rather than be a piece of the Adam's division of labour (not criticizing that, we would go to the stone age otherwise). Something small and simple enough that 1 or 2 persons can manage it, but still advanced enough to add value to users and fulfil a necessity where other products haven't.

One day, in a coffee break, some colleagues and I were talking about this idea where beacons are implanted in the middle of crops to send soil quality telemetry to a central server. We researched the idea and found that a company already does that, [CropX](https://cropx.com/es/cropx-system/hardware/). I was looking for a project to do in my spare time, and thought that a cheapo version of it could be fun, specially if adding those sensors that I always wanted to play with but never had the excuse. I also thought that this project was ideal to team up with my friend [Daniel Béjar](https://github.com/dabecart), with whom I wanted to work together for months. 

So, with that in mind, we sat down and wrote the requirements our soil sensor would. I will not bore you with the technicalities, suffice to say that in broad terms we wanted it to have:
1. An NPK soil sensor.
2. A plastic housing that is a Commercial Off The Shelve (COTS) with minor modifications.
3. A battery, a recharging management system and a solar panel to recharge said battery.
4. A GPS receiver (GNSS is the actual term, since multiple constellations will be used) for easy sensor location.
5. A LoRAWAN emitter and receiver, capable to emit and receive telemetry, and forward other sensor's telemetry to reach a final endpoint.

It seemed something doable at the beginning, but wishful thinking caught us off guard. Again. There's no way 2 adults with a 9 to 5 job can do any of that in any sensible measure of time. Not even the programming, and that's without counting the PCB design, the mechanical design, and a fair amount of testing. So we decided to pick a "subsystem" from the one listed, the one we liked the most, and see how far we could go exploring the topic. That would be fun.

Daniel picked the LoRAWAN receiver/emitter. He plans to write a blog about his very interesting discoveries, full link when it's ready. I picked the GNSS receiver.

## The Ublox NEO-M9N

I had past experience with high end GNSS receivers from [Septentrio](https://www.septentrio.com/en), the [MosaicX5](https://www.septentrio.com/en/products/gnss-receivers/gnss-receiver-modules/mosaic-x5-devkit) in particular, and I always wanted to explore the products of its main competitor, [Ublox](https://www.u-blox.com/en). Not only that, but see how well a ~40€ low-end standard receiver would fare (as of today MosaicX5 are ~700€ and high-end Ublox F10 are ~250€, outside my budget). I started searching the wide range of low-cost positioning products Ublox has, and settled for the NEO-M9N. Mainly because of the fact that Sparkfun has made a decently priced [breakout board](https://www.sparkfun.com/sparkfun-gps-breakout-neo-m9n-sma-qwiic.html) for $70, thus liberating me from buying Ublox's expensive development kit and still having a ready-to-use SMA connection for the antenna and a USB-C to interface with the chip.

I'm going to be honest: I bought the NEO-M9N because it was the cheapest standard precision receiver that Sparkfun had in store with a plug-and-play USB-C. For a battery operated system the ultra-low power M10S would have ben a better option. I just wanted to get started talking to the receiver and figuring how it works. Which brings me to its Interface Control Document and Graphical User Interface.