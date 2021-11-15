# MCeed-A

## Summary

This tool performs the first phase of a brute-force search to reverse engineer a Minecraft world seed using a set of known feature or structure coordinates. This first phase identifies only the lower 48 bits of the 64-bit world seed, which govern the placement of various structures and features. The results of this search then allow for a second phase search to identify the upper 16 bits of the seed which govern biomes, terrain and everything else.

## Theory

Minecraft world seeds are 64-bit numbers, which means there are 2<sup>64</sup> (over 18 quintillion) possible values. When this tool was originally developed in early 2014, it could test about 10 billion seed values per second on a GTX 460; a GTX 760 could do ~20 billion values per second, and today a GTX 1070 (or other similar modern GPU) can test about 40 billion seed values per second. That means even with GPUs continuing to get faster and faster, it still *should* take over 14 years to reverse engineer a Minecraft world seed by trying all 18 quintillion possible values.

But there's a catch.

Minecraft only uses the full 64 bits of the world seed for biome and terrain generation. When choosing locations to put villages, temples and other such features, Minecraft uses the random number generator that comes with the Java language, and that only uses the lower 48 bits of the seed value. That reduces the search space by a factor of over 65 thousand (2<sup>64</sup> / 2<sup>48</sup> = 2<sup>16</sup> = 65536), which reduces the search time from 14 years to about 2 hours.

This faster search can only find the lower 48 bits of the seed value, but once that is known, the remaining 16 bits are relatively easy to find since there are only 65 thousand (2<sup>16</sup>) possibilities.

## History

Minecraft forum user "mellamokb" posted what may be [the earliest version of this attack](http://www.minecraftforum.net/forums/minecraft-java-edition/survival-mode/288285-would-it-be-possible-to-reverse-engineer-a-seed?comment=15) way back in November 2012, which [I came across](http://www.minecraftforum.net/forums/minecraft-java-edition/survival-mode/288285-would-it-be-possible-to-reverse-engineer-a-seed?comment=26) in April 2013. After porting the algorithm to OpenCL to leverage parallel GPU computing and bringing the search time down to a matter of hours, I posted warnings on [the Minecraft forums](http://www.minecraftforum.net/forums/support/server-support/server-administration/2106483-world-seeds-can-be-reverse-engineered) and [reddit](https://www.reddit.com/r/Minecraft/comments/27vwye/world_seeds_can_be_reverseengineered/) in June 2014 with the goal of generating enough attention to convince Mojang to address the issue.

Unfortunately that was unsuccessful; Mojang closed my bug report because they did not consider it a bug. Next I appealed to Bukkit to [implement countermeasures](https://bukkit.org/threads/allow-servers-to-prevent-reverse-engineering-of-world-seeds.278424/), but that also went nowhere. A month later, [md_5 added suitable countermeasures to Spigot](http://www.minecraftforum.net/forums/support/server-support/server-administration/2133175-server-ops-anyone-can-discover-your-world-seeds), but then the entire Spigot project got into a DMCA/licensing mess shortly after that.

I didn't want to release the code until server operators had ample opportunity to protect their servers, so I waited for the Spigot situation to stabilize. Later, ocean monuments were added to the game and became an additional vector for this same attack, so I [suggested that they also be added to the Spigot seed configuration options](https://hub.spigotmc.org/jira/browse/SPIGOT-3036) and again waited for that change to have plenty of time to propagate to all interested server operators.

I am releasing this code now in June 2018 because it has been over three years since the vulnerability was first revealed, and one year since Spigot was last updated to include countermeasures against it. There have also been several other recent attempts to do this, some of which appear (or at least claim) to have been successful:

* github user "pruby" [posted a tool using slime chunks](https://github.com/pruby/slime-seed) as early as October 2014
* reddit user "Legertje64" [claimed success using terrain generation](https://www.reddit.com/r/technicalminecraft/comments/5hysni/finding_a_puplic_server_seed/dbozgcz/) in December 2016
* reddit and github user "Badel2" [posted code using slime chunks](https://github.com/Badel2/slime_seed_finder) in December 2017
* reddit user "osmotischen" [posted code using ocean monuments](https://www.reddit.com/r/technicalminecraft/comments/7idgzx/seed_reverse_engineering_survey_of_approaches_and/) in December 2017
* reddit user "Eta740" [found and re-posted Legertje64's java tool](https://www.reddit.com/r/technicalminecraft/comments/8pmqq7/legerts_l64_fast_seed_cracker_reverse_seed_finding/) in June 2018

There is therefore little point in continuing to keep this tool private; working code to perform the same attack is already available in the wild, and even more such tools are likely to be developed and released before long.

## Requirements

MCeed-A requires [Python 3](https://www.python.org/) with the [numpy](http://www.numpy.org/) and [pyopencl](https://pypi.python.org/pypi/pyopencl) packages.

## Usage

For the world whose seed you wish to discover, you must first gather a list of coordinates at which certain kinds of structures or features have spawned. These currently include:
* slime spawning chunk
* village (well)
* witch hut
* desert temple (center peak)
* jungle temple
* igloo
* ocean monument (center peak)
* end city (base entrance)

For things which extend beyond a single chunk, it is important to specifically identify their spawning chunk; for villages this is the well (of which there will be only one), for temples and monuments it is the center, and for end cities it is the ground-level entrance. Nether fortresses are not useful for this purpose because they begin spawning from a non-unique structure component (walkway intersection), making it impossible to reliably determine which chunk was the "origin" from which the rest of the structure was generated.

These locations can be provided to the tool using either block coordinates (as you'd see in the F3 screen, for example) or chunk coordinates (which are block coordinates divided by 16, but offset by one for negative values). To keep the number of possible solutions low, it is recommended to provide ~20 such locations in any combination (except slime spawning chunks, which are much more common; each counts for only about half the "value" of another type of location).

With a suitable number of provided locations, the seed search requires only time (about 2 hours on a GTX 1070). When it finishes, assuming you provided a sufficient number of known locations, you should have no more than a dozen possible seed "suffixes", meaning the lower 48 bits of the complete world seed. These candidate suffixes must then be provided to the second phase tool (MCeed-B) to identify the upper 16 bits and yield the complete 64-bit world seed.

## Examples

### Finding a World Seed

To find a world seed, we need a set of known locations. For this example we'll use locations for seed #6543210123456 copied directly from AMIDST; note that because of the way command line arguments are processed, locations with a negative X must be specified one-per-argument with the "--argument=value" format rather than the "--argument value1 value2 ..." format.

`python MCeed-A.py --vb 1268,292 756,2228 324,2404 2084,-268 1604,-796 --fb 1672,1864 2648,1768 4456,-2536 3160,-6872 120,824 --mb 3384,-1480 4392,712 4808,568 4616,2760 4152,3352 --eb 1304,72 1704,-536 1032,-1528 --eb=-600,-1880 --eb=-920,1048`

Since this seed is close to the beginning of the search space (6543210123456 / 2<sup>48</sup> ~= 0.023), it should be found within a few minutes:

```
Searching for 32-bit (string-derived) world seed suffix ...
... OK: Search completed in 0.12s, found 0 matches so far
Searching for 48-bit world seed suffix (ctrl-c to stop) ...
... 0 result(s) after 6.84s, 0.1% complete, ~1h57m26s to go ...
... 0 result(s) after 13s, 0.2% complete, ~1h57m19s to go ...
... 0 result(s) after 20s, 0.3% complete, ~1h57m12s to go ...
... (a few minutes) ...
... 0 result(s) after 2m35s, 2.2% complete, ~1h54m57s to go ...
... 0 result(s) after 2m42s, 2.3% complete, ~1h54m50s to go ...
  Match: 6543210123456
... 1 result(s) after 2m49s, 2.4% complete, ~1h54m43s to go ...
```

If we let the search run to completion it may find additional matches that satisfy all of the same feature locations; the more locations that are provided (and the more different kinds of locations), the less likely that is.

### Validating Feature Locations

If you think you know the world seed (or at least its lower 48-bit suffix), you can provide it along with the feature locations to validate whether they match. Here we'll validate the same list of locations for seed #6543210123456 and #288018186834112 (6543210123456 + 2<sup>48</sup>), to demonstrate that seeds which differ by a multiple of 2<sup>48</sup> will have the same potential feature locations:

`python MCeed-A.py --world-seed 6543210123456 288018186834112 --vb 1268,292 756,2228 324,2404 2084,-268 1604,-796 --fb 1672,1864 2648,1768 4456,-2536 3160,-6872 120,824 --mb 3384,-1480 4392,712 4808,568 4616,2760 4152,3352 --eb 1304,72 1704,-536 1032,-1528 --eb=-600,-1880 --eb=-920,1048`

```
Validating provided world seeds and locations using Python logic ...
  6543210123456 matches 5/5 villages, 5/5 features, 5/5 monuments, 5/5 end cities
  288018186834112 matches 5/5 villages, 5/5 features, 5/5 monuments, 5/5 end cities
... OK
Validating provided world seeds and locations using OpenCL logic ...
  6543210123456 matches all criteria
  288018186834112 matches all criteria
... OK
```

The validation is done using two separate code paths (one in pure Python, the other using OpenCL) as a sanity check; the results should be the same, except that the OpenCL variant can't identify which individual locations passed or failed, only whether they all passed or any failed.

### Specifying Feature Seeds

In response to my warnings about the existence of this kind of tool, Spigot added [options for multiplayer servers](https://www.spigotmc.org/wiki/spigot-configuration/#per-world-settings) to change the "magic numbers" which are combined with the world seed to govern feature spawning locations for multiplayer worlds. MCeed-A usually assumes default values for these settings, but if you know that they've been changed for the multiplayer world you're targeting, you can specify them:

`python MCeed-A.py --seed-slime 123 --seed-village 321 --seed-feature 456 --seed-monument 654 --village-block ...`

### Finding Feature Seeds

If you know the world's seed and feature locations but you don't know the altered feature spawning "magic numbers", MCeed-A can search for them for you:

`python MCeed-A.py --seed-village --seed-feature --seed-monument --seed-endcity --world-seed 6543210123456 --vb 1268,292 756,2228 324,2404 2084,-268 1604,-796 --fb 1672,1864 2648,1768 4456,-2536 3160,-6872 120,824 --mb 3384,-1480 4392,712 4808,568 4616,2760 4152,3352 --eb 1304,72 1704,-536 1032,-1528 --eb=-600,-1880 --eb=-920,1048`

In this case we only have 5 locations for each feature type, so we should expect multiple possible matches:

```
Searching for 32-bit village seed with world seed 6543210123456 ...
  Match: 10387312
  Match: 281472833322864
... OK: Search completed in 0.13s, found 2 matches
Searching for 32-bit feature seed with world seed 6543210123456 ...
  Match: 14357617
... OK: Search completed in 0.12s, found 1 matches
Searching for 32-bit monument seed with world seed 6543210123456 ...
  Match: 10387313
... OK: Search completed in 0.22s, found 1 matches
Searching for 32-bit end city seed with world seed 6543210123456 ...
  Match: 10387313
  Match: 115674287
  Match: 321210474
  Match: 543813435
  Match: 645192585
  Match: 699986341
  Match: 884030725
  Match: 1550714573
  Match: 1913251618
  Match: 1922426320
  Match: 1999078113
  Match: 2060959718
  Match: 281473285275274
  Match: 281474152723841
  Match: 281474406457055
  Match: 281474602655846
... OK: Search completed in 0.26s, found 16 matches
```

Since the magic numbers are only 32 bits, this search is very fast; in less than a second we have all four default values (10387312 for villages, 14357617 for scattered features, 10387313 for both monuments and end cities), plus some extraneous matches which could be avoided if we specified more locations of each type.

## Countermeasures

It is possible to prevent this tool from easily finding the seed of your multiplayer world. For new worlds that you are about to generate, the process is now relatively easy as long as you're using Spigot; to protect an existing world, however, is much more difficult.

### New Worlds

Install Spigot, open your *spigot.yml* file, and locate (or add) these lines (where "default" could also be a single specific world on the server):

```
world-settings:
  default:
    seed-village: 10387312
    seed-feature: 14357617
    seed-monument: 10387313
	seed-slime: 10387313
```

The numbers shown above (which Spigot uses by default) are Minecraft's default values, so you must **change them**. For each setting, pick a different random 32-bit integer (between -2147483648 and 2147483647), or use an online tool to generate some for you. It's best to choose prime numbers for this purpose which may seem restrictive, but there are in fact over 200 million 32-bit prime numbers.

By changing these magic numbers, an MCeed-A search assuming the default values will fail to identify the correct world seed. It would still theoretically be possible to search for your new magic numbers while searching for the world seed, but that would increase the search space to 80 bits which would take several billion years (even assuming a prime magic number as suggested above, the search would take thousands of years).

### Existing Worlds

For an existing world, you should still start by making the above change to *spigot.yml* to cause newly visited chunks of your world to spawn structures in different locations, but you will still have lots of existing features that were already generated with the default magic numbers. The locations of those existing features can be used to find your world seed, so you must **move or destroy them**.

This means you must identify and visit every single village, witch hut, desert temple, jungle temple, igloo, ocean monument, end city and woodland mansion that exists anywhere in your current world; since you already know your own world seed, you can use AMIDST to locate all of these features. For each one, you must make it impossible to determine which chunk it originally spawned in. You could do this by completely destroying all traces of the structure, or using some kind of world editing tool to shift the structure over by at least one chunk in any direction (but make it a different random direction for each structure).

Whatever your method, the important part is to make sure there's no way to tell where the structure used to be. This means, for example, that simply destroying the village's well is not sufficient because it would still be easy to tell where the well used to be (it will always be a crossroads intersection).

## License

MCeed-A was conceived and developed by taleden, and is licensed under a <a rel="license" href="http://creativecommons.org/licenses/by-sa/4.0/">Creative Commons Attribution-ShareAlike 4.0 International License. <img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by-sa/4.0/80x15.png" /></a>
