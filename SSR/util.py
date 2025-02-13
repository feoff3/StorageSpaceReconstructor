
# 가변 길이 bytes to int 변경
def big_endian_to_int(buf) :
	val = 0
	for i in range(0, buf.__len__()) :
		val *= 0x100
		val += buf[i]
	return val

def little_endian_to_int(buf) :
	val = 0
	for i in range(0, len(buf)):
		multi = 1
		for j in range(0,i):
			multi *= 256
		val += buf[i] * multi
	return val

def print_hex(buf):
        array_alpha = buf
        print (''.join('{:02x} '.format(x) for x in array_alpha))

def skip_disk_bytes(f , size, direct_mode):
        """ process empty block """
        if direct_mode == False:
            buf = b'\x00' * size
            f.write(buf)
        else:
            f.seek(size, 1)
