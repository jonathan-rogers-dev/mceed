#!/usr/bin/env python3

###
### Copyright 2014 - 2017 by taleden
###
### This work is licensed under a Creative Commons Attribution-ShareAlike 4.0 International License.
### http://creativecommons.org/licenses/by-sa/4.0/
###

import argparse
import itertools
import numpy
import pyopencl
import sys
import time


def javaInt32(val):
	return ((val + (1 << 31)) % (1 << 32)) - (1 << 31)
#javaInt32()


def javaInt64(val):
	return ((val + (1 << 63)) % (1 << 64)) - (1 << 63)
#javaInt64()


def javaRandomInts(seed, size, count=1):
	seed = javaInt64(seed ^ 0x5DEECE66D) & ((1 << 48) - 1)
	vals = list()
	while len(vals) < count:
		bits = 0
		vals.append(size)
		while javaInt32(bits - vals[-1] + size - 1) < 0:
			seed = javaInt64(seed * 0x5DEECE66D + 0xB) & ((1 << 48) - 1)
			bits = javaInt32(seed >> (48 - 31)) & ((1 << 31) - 1)
			vals[-1] = bits % size
	return vals
#javaRandomInts()


def javaRandomLongs(seed, count=1):
	seed = javaInt64(seed ^ 0x5DEECE66D) & ((1 << 48) - 1)
	vals = list()
	while len(vals) < count:
		seed = javaInt64(seed * 0x5DEECE66D + 0xB) & ((1 << 48) - 1)
		vals.append(javaInt32((seed >> (48 - 32)) & ((1 << (64 - 48 + 32)) - 1)) << 32)
		seed = javaInt64(seed * 0x5DEECE66D + 0xB) & ((1 << 48) - 1)
		vals[-1] = javaInt64(vals[-1] + javaInt32((seed >> (48 - 32)) & ((1 << (64 - 48 + 32)) - 1)))
	return vals
#javaRandomLongs()


def getSlimeChunkHash(worldseed, cx, cz): # alpha
	return javaInt64(worldseed + javaInt32(cx*cx*4987142) + javaInt32(cx*5947611) + javaInt64(cz*cz*4392871) + javaInt32(cz*389711))
#getSlimeChunkHash()


def isSlimeChunkOK(hash, cx, cz, magic=987234911): # alpha
	return (javaRandomInts(javaInt64(hash ^ magic), 10)[0] == 0)
#isSlimeChunkOK()


def getVillageChunkHash(worldseed, cx, cz, magic=10387312): # beta
	return javaInt64(worldseed + cx//32*341873128712 + cz//32*132897987541 + magic)
#getVillageChunkHash()


def isVillageChunkOK(hash, cx, cz): # beta
	vals = javaRandomInts(hash, 24, 2)
	return ((vals[0] == (cx % 32)) and (vals[1] == (cz % 32)))
#isVillageChunkOK()


def getFeatureChunkHash(worldseed, cx, cz, magic=14357617): # 1.3.1 (Desert/Jungle Temple), 1.4.2 (Witch Hut), 1.9 (Igloo)
	return javaInt64(worldseed + cx//32*341873128712 + cz//32*132897987541 + magic)
#getFeatureChunkHash()


def isFeatureChunkOK(hash, cx, cz): # 1.3.1 (Desert/Jungle Temple), 1.4.2 (Witch Hut), 1.9 (Igloo)
	vals = javaRandomInts(hash, 24, 2)
	return ((vals[0] == (cx % 32)) and (vals[1] == (cz % 32)))
#isFeatureChunkOK()


def getMonumentChunkHash(worldseed, cx, cz, magic=10387313): # 1.8
	return javaInt64(worldseed + cx//32*341873128712 + cz//32*132897987541 + magic)
#getMonumentChunkHash()


def isMonumentChunkOK(hash, cx, cz): # 1.8
	vals = javaRandomInts(hash, 27, 4)
	return ((int(float(vals[0] + vals[1]) / 2.0) == (cx % 32)) and (int(float(vals[2] + vals[3]) / 2.0) == (cz % 32)))
	# must also have DeepOcean at center, and [Deep|Frozen]<Ocean|River> in radius 29 from center
#isMonumentChunkOK()


def getEndCityChunkHash(worldseed, cx, cz, magic=10387313): # 1.9
	return javaInt64(worldseed + cx//20*341873128712 + cz//20*132897987541 + magic)
#getEndCityChunkHash()


def isEndCityChunkOK(hash, cx, cz): # 1.9
	vals = javaRandomInts(hash, 9, 4)
	return ((int(float(vals[0] + vals[1]) / 2.0) == (cx % 20)) and (int(float(vals[2] + vals[3]) / 2.0) == (cz % 20)))
	# must also have Island height 60+
#isEndCityChunkOK()


def getMansionChunkHash(worldseed, cx, cz, magic=10387319): # 1.11
	return javaInt64(worldseed + cx//80*341873128712 + cz//80*132897987541 + magic)
#getMansionChunkHash()


def isMansionChunkOK(hash, cx, cz): # 1.11
	vals = javaRandomInts(hash, 60, 4)
	return ((int(float(vals[0] + vals[1]) / 2.0) == (cx % 80)) and (int(float(vals[2] + vals[3]) / 2.0) == (cz % 80)))
#isMansionChunkOK()


def parseArgumentChunks(chunklist, blocklist):
	chunks = set()
	for chunk in chunklist:
		cx,cz = chunk.split(',')
		chunks.add( (int(cx),int(cz)) )
	for block in blocklist:
		bx,bz = block.split(',')
		chunks.add( (int(bx)//16,int(bz)//16) )
	return chunks
#parseArgumentChunks()


def timeToString(s):
	s,u = int(s),int(s*100)%100
	m,s = s//60,s%60
	h,m = m//60,m%60
	d,h = h//24,h%24
	str = ""
	if d:
		str += "%dd" % d
	if d or h:
		str += "%dh" % h
	if d or h or m:
		str += "%dm" % m
	str += "%d" % s
	if (not (d or h or m)) and (s < 10):
		str += ".%02d" % u
	str += "s"
	return str
#timeToString()


if __name__ == "__main__":
	# define usage and parse arguments
	parser = argparse.ArgumentParser(description="by taleden")
	parser.add_argument('--version', action='version', version='MCeed-A version 1.0 by taleden')
	parser.add_argument('--list-devices', action='store_true',
			help="list the OpenCL devices available on your computer"
	)
	parser.add_argument('--devices', type=int, metavar='index', nargs='+', action='append', default=[],
			help="the particular OpenCL device(s) to use for seed scanning, identified by their index from --list-devices (default: automatic)"
	)
	parser.add_argument('-w', '--world-seed', type=int, metavar='seed', nargs='+', action='append', default=[],
			help="world seed(s) for which to validate other provided feature locations"
	)
	parser.add_argument('--ss', '--seed-slime', type=int, metavar='seed', nargs='?', default=10387313, const=None,
			help="the custom Spigot seed-slime, or leave blank to derive it with the world seed and slime chunk locations"
	)
	parser.add_argument('--sv', '--seed-village', type=int, metavar='seed', nargs='?', default=10387312, const=None,
			help="the custom Spigot seed-village, or leave blank to derive it with the world seed and village locations"
	)
	parser.add_argument('--sf', '--seed-feature', type=int, metavar='seed', nargs='?', default=14357617, const=None,
			help="the custom Spigot seed-feature, or leave blank to derive it with the world seed and scattered feature locations"
	)
	parser.add_argument('--sm', '--seed-monument', type=int, metavar='seed', nargs='?', default=10387313, const=None,
			help="the custom Spigot seed-monument, or leave blank to derive it with the world seed and monument locations"
	)
	parser.add_argument('--se', '--seed-endcity', type=int, metavar='seed', nargs='?', default=10387313, const=None,
			help="the custom Spigot seed-endcity, or leave blank to derive it with the world seed and end city locations"
	)
	parser.add_argument('-s', '--sc', '--slime-chunk', type=str, metavar='cx,cz', nargs='+', action='append', default=[],
			help="comma-separated chunk coordinate(s) of slime spawning chunks",
	)
	parser.add_argument('-S', '--sb', '--slime-block', type=str, metavar='bx,bz', nargs='+', action='append', default=[],
			help="comma-separated block coordinate(s) of slime spawning chunks",
	)
	parser.add_argument('-v', '--vc', '--village-chunk', type=str, metavar='cx,cz', nargs='+', action='append', default=[],
			help="comma-separated chunk coordinate(s) of village wells",
	)
	parser.add_argument('-V', '--vb', '--village-block', type=str, metavar='bx,bz', nargs='+', action='append', default=[],
			help="comma-separated block coordinate(s) of village wells",
	)
	parser.add_argument('-f', '--fc', '--feature-chunk', type=str, metavar='cx,cz', nargs='+', action='append', default=[],
			help="comma-separated chunk coordinate(s) of scattered features (witch huts, desert/jungle temples, igloos)",
	)
	parser.add_argument('-F', '--fb', '--feature-block', type=str, metavar='bx,bz', nargs='+', action='append', default=[],
			help="comma-separated block coordinate(s) of scattered features (witch huts, desert/jungle temples, igloos)",
	)
	parser.add_argument('-m', '--mc', '--monument-chunk', type=str, metavar='cx,cz', nargs='+', action='append', default=[],
			help="comma-separated chunk coordinate(s) of ocean monuments",
	)
	parser.add_argument('-M', '--mb', '--monument-block', type=str, metavar='bx,bz', nargs='+', action='append', default=[],
			help="comma-separated block coordinate(s) of ocean monuments",
	)
	parser.add_argument('-e', '--ec', '--endcity-chunk', type=str, metavar='cx,cz', nargs='+', action='append', default=[],
			help="comma-separated chunk coordinate(s) of end cities",
	)
	parser.add_argument('-E', '--eb', '--endcity-block', type=str, metavar='bx,bz', nargs='+', action='append', default=[],
			help="comma-separated block coordinate(s) of end cities",
	)
	parser.add_argument('-a', '--ac', '--mansion-chunk', type=str, metavar='cx,cz', nargs='+', action='append', default=[],
			help="comma-separated chunk coordinate(s) of woodland mansions",
	)
	parser.add_argument('-A', '--ab', '--mansion-block', type=str, metavar='bx,bz', nargs='+', action='append', default=[],
			help="comma-separated block coordinate(s) of woodland mansions",
	)
	parser.add_argument('-r', '--resume', type=int, metavar='n', default=0,
			help="spot to resume a seed search that was stopped with Ctrl-C",
	)
	if len(sys.argv) <= 1:
		parser.print_usage()
		print("-h for more information")
		sys.exit(2)
	args = parser.parse_args()
	worldseeds = sorted(set(itertools.chain(*args.world_seed)))
	slimechunks = parseArgumentChunks(itertools.chain(*args.sc), itertools.chain(*args.sb))
	villagechunks = parseArgumentChunks(itertools.chain(*args.vc), itertools.chain(*args.vb))
	featurechunks = parseArgumentChunks(itertools.chain(*args.fc), itertools.chain(*args.fb))
	monumentchunks = parseArgumentChunks(itertools.chain(*args.mc), itertools.chain(*args.mb))
	endcitychunks = parseArgumentChunks(itertools.chain(*args.ec), itertools.chain(*args.eb))
	mansionchunks = parseArgumentChunks(itertools.chain(*args.ac), itertools.chain(*args.ab))
	
	# list OpenCL devices?
	if args.list_devices:
		d = 0
		print("Listing available OpenCL devices ...")
		for platform in pyopencl.get_platforms():
			for device in platform.get_devices():
				d += 1
				print("  #%d: %s on %s (%s)" % (d, platform.name, device.name, platform.version))
		print("... OK: %d devices" % (d,))
		sys.exit(0)
	#if list_devices
	
	# validate provided seeds?
	if len(worldseeds) > 0 and args.sv != None and args.sf != None and args.sm != None and args.ss != None:
		print("Validating provided world seeds and locations using Python logic ...")
		for s in worldseeds:
			out = ""
			if slimechunks:
				sNum = 0
				for cx,cz in slimechunks:
					if isSlimeChunkOK(getSlimeChunkHash(s, cx, cz), cx, cz, args.ss):
						sNum += 1
				out += "%s%d/%d slime chunks" % ((", " if out else ""),sNum,len(slimechunks))
			if villagechunks:
				vNum = 0
				for cx,cz in villagechunks:
					if isVillageChunkOK(getVillageChunkHash(s, cx, cz, args.sv), cx, cz):
						vNum += 1
				out += "%s%d/%d villages" % ((", " if out else ""),vNum,len(villagechunks))
			if featurechunks:
				fNum = 0
				for cx,cz in featurechunks:
					if isFeatureChunkOK(getFeatureChunkHash(s, cx, cz, args.sf), cx, cz):
						fNum += 1
				out += "%s%d/%d features" % ((", " if out else ""),fNum,len(featurechunks))
			if monumentchunks:
				mNum = 0
				for cx,cz in monumentchunks:
					if isMonumentChunkOK(getMonumentChunkHash(s, cx, cz, args.sm), cx, cz):
						mNum += 1
				out += "%s%d/%d monuments" % ((", " if out else ""),mNum,len(monumentchunks))
			if endcitychunks:
				fNum = 0
				for cx,cz in endcitychunks:
					if isEndCityChunkOK(getEndCityChunkHash(s, cx, cz, args.sm), cx, cz):
						fNum += 1
				out += "%s%d/%d end cities" % ((", " if out else ""),fNum,len(endcitychunks))
			if mansionchunks:
				mNum = 0
				for cx,cz in mansionchunks:
					if isMansionChunkOK(getMansionChunkHash(s, cx, cz), cx, cz):
						mNum += 1
				out += "%s%d/%d mansions" % ((", " if out else ""),mNum,len(mansionchunks))
			print("  %d matches %s" % (s,out))
		print("... OK")
	#if worldseeds
	
	# dynamically generate an OpenCL kernel function
	kernel = """
__kernel void test_seeds(
	const long seedbase,
	const char asTimestamp,
	__global volatile long *hits,
	__global volatile uint *count
) {
	long seed = seedbase + get_global_id(0);
	long rand;
	int bits, val, val2;
	
	/* DISABLED timestamp-derived scan; newer JDK uses System.nanoTime() and a secondary Uniquifier() which depends how many instances of Random() have ever been created
	if (asTimestamp != 0) {
		rand = (seed ^ 0x5deece66dL) & ((1L << 48) - 1);
		rand = (rand * 0x5deece66dL + 0xbL) & ((1L << 48) - 1);
		seed = (long)( (int)( (rand >> (48 - 32)) & ((1L << (64 - 48 + 32)) - 1) ) ) << 32;
		rand = (rand * 0x5deece66dL + 0xbL) & ((1L << 48) - 1);
		seed = seed + (int)( (rand >> (48 - 32)) & ((1L << (64 - 48 + 32)) - 1) );
	}
	*/
	
""" + "\n".join(("""
	rand = ((seed + %dL) ^ 0x5deece66dL) & ((1L << 48) - 1);
	do {
		rand = (rand * 0x5deece66dL + 0xbL) & ((1L << 48) - 1);
		bits = (int)((rand >> (48 - 31)) & ((1L << 31) - 1));
		val = bits %% 24;
	} while (bits - val + (24 - 1) < 0);
	if (val != %d)
		return;
	do {
		rand = (rand * 0x5deece66dL + 0xbL) & ((1L << 48) - 1);
		bits = (int)((rand >> (48 - 31)) & ((1L << 31) - 1));
		val = bits %% 24;
	} while (bits - val + (24 - 1) < 0);
	if (val != %d)
		return;
""" % (getVillageChunkHash(0,cx,cz,args.sv),cx%32,cz%32)) for cx,cz in villagechunks if (args.sv != None)) + """
	
""" + "\n".join(("""
	rand = ((seed + %dL) ^ 0x5deece66dL) & ((1L << 48) - 1);
	do {
		rand = (rand * 0x5deece66dL + 0xbL) & ((1L << 48) - 1);
		bits = (int)((rand >> (48 - 31)) & ((1L << 31) - 1));
		val = bits %% 24;
	} while (bits - val + (24 - 1) < 0);
	if (val != %d)
		return;
	do {
		rand = (rand * 0x5deece66dL + 0xbL) & ((1L << 48) - 1);
		bits = (int)((rand >> (48 - 31)) & ((1L << 31) - 1));
		val = bits %% 24;
	} while (bits - val + (24 - 1) < 0);
	if (val != %d)
		return;
""" % (getFeatureChunkHash(0,cx,cz,args.sf),cx%32,cz%32)) for cx,cz in featurechunks if (args.sf != None)) + """
	
""" + "\n".join(("""
	rand = ((seed + %dL) ^ 0x5deece66dL) & ((1L << 48) - 1);
	do {
		rand = (rand * 0x5deece66dL + 0xbL) & ((1L << 48) - 1);
		bits = (int)((rand >> (48 - 31)) & ((1L << 31) - 1));
		val = bits %% 27;
	} while (bits - val + (27 - 1) < 0);
	do {
		rand = (rand * 0x5deece66dL + 0xbL) & ((1L << 48) - 1);
		bits = (int)((rand >> (48 - 31)) & ((1L << 31) - 1));
		val2 = bits %% 27;
	} while (bits - val2 + (27 - 1) < 0);
	if ((val + val2) / 2 != %d)
		return;
	do {
		rand = (rand * 0x5deece66dL + 0xbL) & ((1L << 48) - 1);
		bits = (int)((rand >> (48 - 31)) & ((1L << 31) - 1));
		val = bits %% 27;
	} while (bits - val + (27 - 1) < 0);
	do {
		rand = (rand * 0x5deece66dL + 0xbL) & ((1L << 48) - 1);
		bits = (int)((rand >> (48 - 31)) & ((1L << 31) - 1));
		val2 = bits %% 27;
	} while (bits - val2 + (27 - 1) < 0);
	if ((val + val2) / 2 != %d)
		return;
""" % (getMonumentChunkHash(0,cx,cz,args.sm),cx%32,cz%32)) for cx,cz in monumentchunks if (args.sm != None)) + """
	
""" + "\n".join(("""
	rand = ((seed + %dL) ^ 0x5deece66dL) & ((1L << 48) - 1);
	do {
		rand = (rand * 0x5deece66dL + 0xbL) & ((1L << 48) - 1);
		bits = (int)((rand >> (48 - 31)) & ((1L << 31) - 1));
		val = bits %% 9;
	} while (bits - val + (9 - 1) < 0);
	do {
		rand = (rand * 0x5deece66dL + 0xbL) & ((1L << 48) - 1);
		bits = (int)((rand >> (48 - 31)) & ((1L << 31) - 1));
		val2 = bits %% 9;
	} while (bits - val2 + (9 - 1) < 0);
	if ((val + val2) / 2 != %d)
		return;
	do {
		rand = (rand * 0x5deece66dL + 0xbL) & ((1L << 48) - 1);
		bits = (int)((rand >> (48 - 31)) & ((1L << 31) - 1));
		val = bits %% 9;
	} while (bits - val + (9 - 1) < 0);
	do {
		rand = (rand * 0x5deece66dL + 0xbL) & ((1L << 48) - 1);
		bits = (int)((rand >> (48 - 31)) & ((1L << 31) - 1));
		val2 = bits %% 9;
	} while (bits - val2 + (9 - 1) < 0);
	if ((val + val2) / 2 != %d)
		return;
""" % (getEndCityChunkHash(0,cx,cz),cx%20,cz%20)) for cx,cz in endcitychunks) + """
	
""" + "\n".join(("""
	rand = ((seed + %dL) ^ 0x5deece66dL) & ((1L << 48) - 1);
	do {
		rand = (rand * 0x5deece66dL + 0xbL) & ((1L << 48) - 1);
		bits = (int)((rand >> (48 - 31)) & ((1L << 31) - 1));
		val = bits %% 60;
	} while (bits - val + (60 - 1) < 0);
	do {
		rand = (rand * 0x5deece66dL + 0xbL) & ((1L << 48) - 1);
		bits = (int)((rand >> (48 - 31)) & ((1L << 31) - 1));
		val2 = bits %% 60;
	} while (bits - val2 + (60 - 1) < 0);
	if ((val + val2) / 2 != %d)
		return;
	do {
		rand = (rand * 0x5deece66dL + 0xbL) & ((1L << 48) - 1);
		bits = (int)((rand >> (48 - 31)) & ((1L << 31) - 1));
		val = bits %% 60;
	} while (bits - val + (60 - 1) < 0);
	do {
		rand = (rand * 0x5deece66dL + 0xbL) & ((1L << 48) - 1);
		bits = (int)((rand >> (48 - 31)) & ((1L << 31) - 1));
		val2 = bits %% 60;
	} while (bits - val2 + (60 - 1) < 0);
	if ((val + val2) / 2 != %d)
		return;
""" % (getMansionChunkHash(0,cx,cz),cx%80,cz%80)) for cx,cz in mansionchunks) + """
	
""" + "\n".join(("""
	rand = ((seed + %dL) ^ %dL ^ 0x5deece66dL) & ((1L << 48) - 1);
	do {
		rand = (rand * 0x5deece66dL + 0xbL) & ((1L << 48) - 1);
		bits = (int)((rand >> (48 - 31)) & ((1L << 31) - 1));
		val = bits %% 10;
	} while (bits - val + (10 - 1) < 0);
	if (val != 0)
		return;
""" % (getSlimeChunkHash(0,cx,cz),args.ss)) for cx,cz in slimechunks if (args.ss != None)) + """
	
	val = (int) atomic_inc(count);
	if ((val >= 0 && val < 16)) {
		hits[val] = seed;
	} else {
		atomic_xchg(count, 16);
	}
}
"""
	
	# add kernel functions for slime/village/feature/monument seed search, if possible
	if len(worldseeds) == 1:
		
		#TODO slimes
		
		if args.sv == None:
			kernel += ("""
__kernel void test_villageseeds(
	const long magicbase,
	const char asTimestamp,
	__global volatile long *hits,
	__global volatile uint *count
) {
	long magic = magicbase + get_global_id(0);
	long rand;
	int bits, val, val2;
	
""") + "\n".join(("""
	rand = ((%dL + magic) ^ 0x5deece66dL) & ((1L << 48) - 1);
	do {
		rand = (rand * 0x5deece66dL + 0xbL) & ((1L << 48) - 1);
		bits = (int)((rand >> (48 - 31)) & ((1L << 31) - 1));
		val = bits %% 24;
	} while (bits - val + (24 - 1) < 0);
	if (val != %d)
		return;
	do {
		rand = (rand * 0x5deece66dL + 0xbL) & ((1L << 48) - 1);
		bits = (int)((rand >> (48 - 31)) & ((1L << 31) - 1));
		val = bits %% 24;
	} while (bits - val + (24 - 1) < 0);
	if (val != %d)
		return;
""" % (getVillageChunkHash(worldseeds[0],cx,cz,0),cx%32,cz%32)) for cx,cz in villagechunks) + ("""
	
	val = (int) atomic_inc(count);
	if ((val >= 0 && val < 16)) {
		hits[val] = magic;
	} else {
		atomic_xchg(count, 16);
	}
}
""")
		#if no sv
		
		if args.sf == None:
			kernel += ("""
__kernel void test_featureseeds(
	const long magicbase,
	const char asTimestamp,
	__global volatile long *hits,
	__global volatile uint *count
) {
	long magic = magicbase + get_global_id(0);
	long rand;
	int bits, val, val2;
	
""") + "\n".join(("""
	rand = ((%dL + magic) ^ 0x5deece66dL) & ((1L << 48) - 1);
	do {
		rand = (rand * 0x5deece66dL + 0xbL) & ((1L << 48) - 1);
		bits = (int)((rand >> (48 - 31)) & ((1L << 31) - 1));
		val = bits %% 24;
	} while (bits - val + (24 - 1) < 0);
	if (val != %d)
		return;
	do {
		rand = (rand * 0x5deece66dL + 0xbL) & ((1L << 48) - 1);
		bits = (int)((rand >> (48 - 31)) & ((1L << 31) - 1));
		val = bits %% 24;
	} while (bits - val + (24 - 1) < 0);
	if (val != %d)
		return;
""" % (getFeatureChunkHash(worldseeds[0],cx,cz,0),cx%32,cz%32)) for cx,cz in featurechunks) + ("""
	
	val = (int) atomic_inc(count);
	if ((val >= 0 && val < 16)) {
		hits[val] = magic;
	} else {
		atomic_xchg(count, 16);
	}
}
""")
		#if no sf
		
		if args.sm == None:
			kernel += ("""
__kernel void test_monumentseeds(
	const long magicbase,
	const char asTimestamp,
	__global volatile long *hits,
	__global volatile uint *count
) {
	long magic = magicbase + get_global_id(0);
	long rand;
	int bits, val, val2;
	
""") + "\n".join(("""
	rand = ((%dL + magic) ^ 0x5deece66dL) & ((1L << 48) - 1);
	do {
		rand = (rand * 0x5deece66dL + 0xbL) & ((1L << 48) - 1);
		bits = (int)((rand >> (48 - 31)) & ((1L << 31) - 1));
		val = bits %% 27;
	} while (bits - val + (27 - 1) < 0);
	do {
		rand = (rand * 0x5deece66dL + 0xbL) & ((1L << 48) - 1);
		bits = (int)((rand >> (48 - 31)) & ((1L << 31) - 1));
		val2 = bits %% 27;
	} while (bits - val2 + (27 - 1) < 0);
	if ((val + val2) / 2 != %d)
		return;
	do {
		rand = (rand * 0x5deece66dL + 0xbL) & ((1L << 48) - 1);
		bits = (int)((rand >> (48 - 31)) & ((1L << 31) - 1));
		val = bits %% 27;
	} while (bits - val + (27 - 1) < 0);
	do {
		rand = (rand * 0x5deece66dL + 0xbL) & ((1L << 48) - 1);
		bits = (int)((rand >> (48 - 31)) & ((1L << 31) - 1));
		val2 = bits %% 27;
	} while (bits - val2 + (27 - 1) < 0);
	if ((val + val2) / 2 != %d)
		return;
""" % (getMonumentChunkHash(worldseeds[0],cx,cz,0),cx%32,cz%32)) for cx,cz in monumentchunks) + ("""
	
	val = (int) atomic_inc(count);
	if ((val >= 0 && val < 16)) {
		hits[val] = magic;
	} else {
		atomic_xchg(count, 16);
	}
}
""")
		#if no sm
		
		if args.se == None:
			kernel += ("""
__kernel void test_endcityseeds(
	const long magicbase,
	const char asTimestamp,
	__global volatile long *hits,
	__global volatile uint *count
) {
	long magic = magicbase + get_global_id(0);
	long rand;
	int bits, val, val2;
	
""") + "\n".join(("""
	rand = ((%dL + magic) ^ 0x5deece66dL) & ((1L << 48) - 1);
	do {
		rand = (rand * 0x5deece66dL + 0xbL) & ((1L << 48) - 1);
		bits = (int)((rand >> (48 - 31)) & ((1L << 31) - 1));
		val = bits %% 9;
	} while (bits - val + (9 - 1) < 0);
	do {
		rand = (rand * 0x5deece66dL + 0xbL) & ((1L << 48) - 1);
		bits = (int)((rand >> (48 - 31)) & ((1L << 31) - 1));
		val2 = bits %% 9;
	} while (bits - val2 + (9 - 1) < 0);
	if ((val + val2) / 2 != %d)
		return;
	do {
		rand = (rand * 0x5deece66dL + 0xbL) & ((1L << 48) - 1);
		bits = (int)((rand >> (48 - 31)) & ((1L << 31) - 1));
		val = bits %% 9;
	} while (bits - val + (9 - 1) < 0);
	do {
		rand = (rand * 0x5deece66dL + 0xbL) & ((1L << 48) - 1);
		bits = (int)((rand >> (48 - 31)) & ((1L << 31) - 1));
		val2 = bits %% 9;
	} while (bits - val2 + (9 - 1) < 0);
	if ((val + val2) / 2 != %d)
		return;
""" % (getEndCityChunkHash(worldseeds[0],cx,cz,0),cx%20,cz%20)) for cx,cz in endcitychunks) + ("""
	
	val = (int) atomic_inc(count);
	if ((val >= 0 && val < 16)) {
		hits[val] = magic;
	} else {
		atomic_xchg(count, 16);
	}
}
""")
		#if no se
		
	#if 1 worldseed
	
	deviceIDs = set(itertools.chain(*args.devices))
	mydevices = list()
	if deviceIDs:
		d = 0
		for platform in pyopencl.get_platforms():
			for device in platform.get_devices():
				d += 1
				if d in deviceIDs:
					mydevices.append(device)
		if not mydevices:
			sys.exit("ERROR: The specified OpenCL device(s) were not found; refer to --list-devices")
		context = pyopencl.Context(devices=mydevices)
	else:
		context = pyopencl.create_some_context()
	queue = pyopencl.CommandQueue(context)
	program = pyopencl.Program(context, kernel).build()
	hits = numpy.zeros(16, dtype=numpy.int64)
	count = numpy.zeros(1, dtype=numpy.uint32)
	hitsBuf = pyopencl.Buffer(context, pyopencl.mem_flags.WRITE_ONLY | pyopencl.mem_flags.COPY_HOST_PTR, hostbuf=hits)
	countBuf = pyopencl.Buffer(context, pyopencl.mem_flags.READ_WRITE | pyopencl.mem_flags.COPY_HOST_PTR, hostbuf=count)
	
	if (args.ss == None) or (args.sv == None) or (args.sf == None) or (args.sm == None) or (args.se == None):
		
		# TODO slimes
		
		if args.sv == None:
			if len(worldseeds) != 1:
				sys.exit("ERROR: village seed search requires exactly one world seed")
			if not villagechunks:
				sys.exit("ERROR: village seed search requires at least one village location")
			print("Searching for 32-bit village seed with world seed %d ..." % (worldseeds[0],))
			results = set()
			t0 = time.time()
			for magicbase in [0, ((1<<17)-1)]:
				event = program.test_villageseeds(queue, (1<<31,), None, numpy.int64(magicbase*(1<<31)), numpy.int8(0), hitsBuf, countBuf)
				event.wait()
			pyopencl.enqueue_copy(queue, count, countBuf, is_blocking=True)
			if count[0]:
				pyopencl.enqueue_copy(queue, hits, hitsBuf, is_blocking=True)
				found = set(hits[h] for h in range(min(16,count[0])))
				for s in sorted(found):
					print("  Match: %d" % (s,))
				results.update(found)
				count[0] = 0
				pyopencl.enqueue_copy(queue, countBuf, count, is_blocking=True)
			t1 = time.time()
			print("... OK: Search completed in %s, found %d matches" % (timeToString(t1-t0),len(results)))
		#if village seed search
		
		if args.sf == None:
			if len(worldseeds) != 1:
				sys.exit("ERROR: feature seed search requires exactly one world seed")
			if not featurechunks:
				sys.exit("ERROR: feature seed search requires at least one feature location")
			print("Searching for 32-bit feature seed with world seed %d ..." % (worldseeds[0],))
			results = set()
			t0 = time.time()
			for magicbase in [0, ((1<<17)-1)]:
				event = program.test_featureseeds(queue, (1<<31,), None, numpy.int64(magicbase*(1<<31)), numpy.int8(0), hitsBuf, countBuf)
				event.wait()
			pyopencl.enqueue_copy(queue, count, countBuf, is_blocking=True)
			if count[0]:
				pyopencl.enqueue_copy(queue, hits, hitsBuf, is_blocking=True)
				found = set(hits[h] for h in range(min(16,count[0])))
				for s in sorted(found):
					print("  Match: %d" % (s,))
				results.update(found)
				count[0] = 0
				pyopencl.enqueue_copy(queue, countBuf, count, is_blocking=True)
			t1 = time.time()
			print("... OK: Search completed in %s, found %d matches" % (timeToString(t1-t0),len(results)))
		#if feature seed search
		
		if args.sm == None:
			if len(worldseeds) != 1:
				sys.exit("ERROR: monument seed search requires exactly one world seed")
			if not monumentchunks:
				sys.exit("ERROR: monument seed search requires at least one monument location")
			print("Searching for 32-bit monument seed with world seed %d ..." % (worldseeds[0],))
			results = set()
			t0 = time.time()
			for magicbase in [0, ((1<<17)-1)]:
				event = program.test_monumentseeds(queue, (1<<31,), None, numpy.int64(magicbase*(1<<31)), numpy.int8(0), hitsBuf, countBuf)
				event.wait()
			pyopencl.enqueue_copy(queue, count, countBuf, is_blocking=True)
			if count[0]:
				pyopencl.enqueue_copy(queue, hits, hitsBuf, is_blocking=True)
				found = set(hits[h] for h in range(min(16,count[0])))
				for s in sorted(found):
					print("  Match: %d" % (s,))
				results.update(found)
				count[0] = 0
				pyopencl.enqueue_copy(queue, countBuf, count, is_blocking=True)
			t1 = time.time()
			print("... OK: Search completed in %s, found %d matches" % (timeToString(t1-t0),len(results)))
		#if monument seed search
		
		if args.se == None:
			if len(worldseeds) != 1:
				sys.exit("ERROR: end city seed search requires exactly one world seed")
			if not endcitychunks:
				sys.exit("ERROR: end city seed search requires at least one end city location")
			print("Searching for 32-bit end city seed with world seed %d ..." % (worldseeds[0],))
			results = set()
			t0 = time.time()
			for magicbase in [0, ((1<<17)-1)]:
				event = program.test_endcityseeds(queue, (1<<31,), None, numpy.int64(magicbase*(1<<31)), numpy.int8(0), hitsBuf, countBuf)
				event.wait()
			pyopencl.enqueue_copy(queue, count, countBuf, is_blocking=True)
			if count[0]:
				pyopencl.enqueue_copy(queue, hits, hitsBuf, is_blocking=True)
				found = set(hits[h] for h in range(min(16,count[0])))
				for s in sorted(found):
					print("  Match: %d" % (s,))
				results.update(found)
				count[0] = 0
				pyopencl.enqueue_copy(queue, countBuf, count, is_blocking=True)
			t1 = time.time()
			print("... OK: Search completed in %s, found %d matches" % (timeToString(t1-t0),len(results)))
		#if endcity seed search
		
	elif worldseeds:
		
		print("Validating provided world seeds and locations using OpenCL logic ...")
		for s in worldseeds:
			event = program.test_seeds(queue, (1,), None, numpy.int64(s), numpy.int8(0), hitsBuf, countBuf)
			event.wait()
			pyopencl.enqueue_copy(queue, count, countBuf, is_blocking=True)
			if count[0]:
				pyopencl.enqueue_copy(queue, hits, hitsBuf, is_blocking=True)
				assert(count[0] == 1)
				assert(hits[0] == s)
				print("  %d matches all criteria" % (s,))
				count[0] = 0
				pyopencl.enqueue_copy(queue, countBuf, count, is_blocking=True)
			else:
				print("  %d does not match all criteria" % (s,))
		print("... OK")
		
	else:
		
		if not (slimechunks or villagechunks or monumentchunks or mansionchunks or featurechunks or endcitychunks):
			sys.exit("ERROR: world seed search requires at least one slime, village, monument, mansion, feature or end city location (preferably a dozen or more)")
		results = set()
		pct = -1
		
		if not args.resume:
			print("Searching for 32-bit (string-derived) world seed suffix ...")
			t0 = time.time()
			for seedbase in [0, ((1<<17)-1)]:
				event = program.test_seeds(queue, (1<<31,), None, numpy.int64(seedbase*(1<<31)), numpy.int8(0), hitsBuf, countBuf)
				event.wait()
			pyopencl.enqueue_copy(queue, count, countBuf, is_blocking=True)
			if count[0]:
				pyopencl.enqueue_copy(queue, hits, hitsBuf, is_blocking=True)
				found = set(hits[h] for h in range(min(16,count[0])))
				for s in sorted(found):
					print("  Match: %d" % (s,))
				results.update(found)
				count[0] = 0
				pyopencl.enqueue_copy(queue, countBuf, count, is_blocking=True)
			t1 = time.time()
			print("... OK: Search completed in %s, found %d matches so far" % (timeToString(t1-t0),len(results)))
			
			"""
DISABLED timestamp-derived scan; newer JDK uses System.nanoTime() and a secondary Uniquifier() which depends on how many instances of Random() have ever been created
			print("Searching for ~38-bit (timestamp-derived) world seed suffix ...")
			t0 = time.time()
			for seedbase in range(587, int((t0+60*60*24*10) * 1000 / (1<<31))+1): # milliseconds from 1970-01-01 to 2010-01-01 = 1262300400876 ~= 587.8 * 2^31
				event = program.test_seeds(queue, (1<<31,), None, numpy.int64(seedbase*(1<<31)), numpy.int8(1), hitsBuf, countBuf)
				event.wait()
			pyopencl.enqueue_copy(queue, count, countBuf, is_blocking=True)
			if count[0]:
				pyopencl.enqueue_copy(queue, hits, hitsBuf, is_blocking=True)
				found = set(hits[h] for h in range(min(16,count[0])))
				for s in sorted(found):
					print("  Match: %d" % (s,))
				results.update(found)
				count[0] = 0
				pyopencl.enqueue_copy(queue, countBuf, count, is_blocking=True)
			t1 = time.time()
			print("... OK: Search completed in %s, found %d matches so far" % (timeToString(t1-t0),len(results)))
"""
		#if not resume
		
		print("Searching for 48-bit world seed suffix (ctrl-c to stop) ...")
		t0 = time.time()
		pct = 1000 * args.resume // (1<<17)
		seedbase = args.resume or 1
		while seedbase < ((1<<17)-1):
			try:
				event = program.test_seeds(queue, (1<<31,), None, numpy.int64(seedbase*(1<<31)), numpy.int8(0), hitsBuf, countBuf)
				event.wait()
				if pct != 1000 * seedbase // (1<<17):
					pct = 1000 * seedbase // (1<<17)
					pyopencl.enqueue_copy(queue, count, countBuf, is_blocking=True)
					if count[0]:
						pyopencl.enqueue_copy(queue, hits, hitsBuf, is_blocking=True)
						found = set(hits[h] for h in range(min(16,count[0])))
						for s in sorted(found):
							print("  Match: %d" % (s,))
						results.update(found)
						count[0] = 0
						pyopencl.enqueue_copy(queue, countBuf, count, is_blocking=True)
					t1 = time.time()
					print("... %d result(s) after %s, %.1f%% complete, ~%s to go ..." % (
							len(results),
							timeToString(t1-t0),
							100.0*seedbase/(1<<17),
							timeToString(((float((1<<17) - args.resume) / (seedbase - args.resume)) * (t1 - t0)) - (t1 - t0))
					))
				seedbase += 1
				continue
			except KeyboardInterrupt:
				pass
			
			t1 = time.time()
			try:
				input("... PAUSED. Press ENTER to continue, or ctrl-c to exit.")
				t0 += (time.time() - t1)
				print("Resuming 48-bit world seed suffix search (ctrl-c to stop) ...")
				seedbase -= 1
				continue
			except (EOFError, KeyboardInterrupt) as e:
				pass
			
			try:
				print("\n... OK: Search aborted after %s, resume with --resume %d" % (timeToString(t1-t0), max(args.resume,seedbase-1)))
			except (EOFError, KeyboardInterrupt) as e:
				pass
			
			seedbase = -1
			break
		#while
		t1 = time.time()
		if seedbase >= 0:
			print("... OK: Search completed in %s" % (timeToString(t1-t0),))
		pyopencl.enqueue_copy(queue, count, countBuf, is_blocking=True)
		pyopencl.enqueue_copy(queue, hits, hitsBuf, is_blocking=True)
		results.update(hits[h] for h in range(min(16,count[0])))
		print("Final results:")
		for s in sorted(results):
			print("  %d" % (s,))
		print("... OK: %d matches" % (len(results),))
	#if worldseeds
	
#if __main__
