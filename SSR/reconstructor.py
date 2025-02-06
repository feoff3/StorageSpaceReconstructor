"""
@author:    Junho Kim
@license:   None
@contact:   rlawnsgh92(at)korea(dot)ac(dot)kr
"""
import os
import struct

from SSR.disk import Disk
from SSR.util import *
from SSR.define import Define

class Reconstructor:

    def __init__(self, version, level):
        self.version = version
        self.level = level
        self.disk_list = []

        """ physical disks, virtual disks, """
        self.parsed_disks = []

    def __del__(self):
        pass

    def __repr__(self):
        return "Reconstructor"

    def add_disk(self, disk):
        print("[*] Disk Added.")
        self.disk_list.append(disk)

    """ parse_metadata """
    def parse_metadata(self):  # 여기서 메타데이터들을 읽고 디스크들 재구성하기.
        """ Init parsed disks """
        #parsed_disks_size = len(self.disk_list[0].sdbb_entry_type2) + len(self.disk_list[0].sdbb_entry_type3)
        #for i in range(0, parsed_disks_size + 1):  # +1은 Offset이 0부터 시작해서 1개가 부족하니까 추가.
        for i in range(0, 1000):  # 위 처럼 하니까 windows 10을 커버하지 못함. 혹시 id가 커질 수 있으니 1000개 넣자.
            self.parsed_disks.append(None)

        if self._parse_entry_type1() == False:
            return False

        if self._parse_entry_type2() == False:
            return False

        if self._parse_entry_type3() == False:
            return False

        if self._parse_entry_type4() == False:
            return False

        return True

    def _parse_entry_type1(self):
        """type1 entry contains data regarding physical disks to storage pool association"""
        for disk in self.disk_list:
            temp_offset = 0

            for i in range(0, len(disk.sdbb_entry_type1)):
                # I fail to understand how it works...
                temp_offset += disk.sdbb_entry_type1[i][temp_offset] + 1
                temp_offset += disk.sdbb_entry_type1[i][temp_offset] + 1
                storage_pool_uuid = disk.sdbb_entry_type1[i][temp_offset : temp_offset + 0x10]

                if storage_pool_uuid != disk.storage_pool_uuid:
                    print("[*] This disk is not member for storage pool")
                    return False

                break

        return True

    def _parse_entry_type2(self):
        """type2 contains info about physical disks"""
        temp_disk = None
        for disk in self.disk_list:
            if len(disk.sdbb_entry_type2) == 0:
                continue
            else:
                temp_disk = disk
        for i in range(0, len(temp_disk.sdbb_entry_type2)):
            disk = Disk()
            temp_offset = 0
            #print_hex(temp_disk.sdbb_entry_type2[i])
            data_record_len = temp_disk.sdbb_entry_type2[i][temp_offset]
            physical_disk_id = big_endian_to_int(temp_disk.sdbb_entry_type2[i][temp_offset + 1: temp_offset + 1 + data_record_len])
            
            temp_offset += temp_disk.sdbb_entry_type2[i][temp_offset] + 1
            temp_offset += temp_disk.sdbb_entry_type2[i][temp_offset] + 1
            physical_disk_uuid = temp_disk.sdbb_entry_type2[i][temp_offset: temp_offset + 0x10]
            temp_offset += 0x10
            if self.version == Define.WINDOWS_SERVER_2019:
                # NOTE: maybe structure changed in Win2019... 
                # Some more data (mostly nulls) were added before the disk name, and some added after
                temp_offset += 0x08
                #temp_offset += temp_disk.sdbb_entry_type2[i][temp_offset] + 1
                #print(str(temp_offset))
                #print_hex(temp_disk.sdbb_entry_type2[i][temp_offset:])
                mfg_name_length = temp_disk.sdbb_entry_type2[i][temp_offset]
                physical_disk_name = b''
                temp_mfg_name = temp_disk.sdbb_entry_type2[i][temp_offset: temp_offset + mfg_name_length * 2]
                temp_offset += (mfg_name_length + 1) * 2 
                #print(str(temp_offset))
                model_name_length = temp_disk.sdbb_entry_type2[i][temp_offset]
                temp_offset += 1
                temp_model_name = temp_disk.sdbb_entry_type2[i][temp_offset: temp_offset + model_name_length * 2]
                temp_offset += (model_name_length + 1) * 2
                #print(str(temp_offset))
                for j in range(0, model_name_length * 2, 2):
                    physical_disk_name += temp_model_name[j + 1 : j + 2]
                    physical_disk_name += temp_model_name[j : j + 1]
                #print(str(physical_disk_name))
                temp_offset += 6
                #print_hex(temp_disk.sdbb_entry_type2[i][temp_offset:])
                #print(str(temp_offset))
                temp_offset += 30
                #print_hex(temp_disk.sdbb_entry_type2[i][temp_offset:])
                #print(str(temp_offset))
                data_record_len = temp_disk.sdbb_entry_type2[i][temp_offset]
                physical_disk_total_size = big_endian_to_int(temp_disk.sdbb_entry_type2[i][temp_offset + 1 : temp_offset + 1 + data_record_len])
                temp_offset += temp_disk.sdbb_entry_type2[i][temp_offset] + 1
                data_record_len = temp_disk.sdbb_entry_type2[i][temp_offset]
                physical_disk_usable_size = big_endian_to_int(temp_disk.sdbb_entry_type2[i][temp_offset + 1 : temp_offset + 1 + data_record_len])
                print("Total: " + str(physical_disk_total_size) + " B , Usable: " + str(physical_disk_usable_size) + " B")
                physical_disk_block_number = int(physical_disk_usable_size / 0x10000000) #TODO: check if block number is expected to be this, maybe we have to reduce the size by two 256MB blocks and 16MB partition offset  
                #TODO: If possible, check on Win2016 
            else:
                physical_disk_name_length = struct.unpack('>H', temp_disk.sdbb_entry_type2[i][temp_offset: temp_offset + 0x02])[0]
                temp_offset += 0x02
                physical_disk_name = b''
                temp_physical_disk_name = temp_disk.sdbb_entry_type2[i][temp_offset: temp_offset + physical_disk_name_length * 2]
                temp_offset += physical_disk_name_length * 2
                for j in range(0, physical_disk_name_length * 2, 2):
                    physical_disk_name += temp_physical_disk_name[j + 1 : j + 2]
                    physical_disk_name += temp_physical_disk_name[j : j + 1]
                temp_offset += 6
                data_record_len = temp_disk.sdbb_entry_type2[i][temp_offset]
                physical_disk_block_number = big_endian_to_int(temp_disk.sdbb_entry_type2[i][temp_offset + 1 : temp_offset + 1 + data_record_len])
            disk.id = physical_disk_id
            disk.uuid = physical_disk_uuid
            disk.name = physical_disk_name
            disk.block_number = physical_disk_block_number
            print("PD: " + str(disk.id) + " blocks " + str(disk.block_number))
            print_hex(disk.uuid)
            for disk_member in self.disk_list:
                if disk.uuid == disk_member.physical_disk_uuid:
                    disk.dp = disk_member
                    self.parsed_disks[physical_disk_id] = disk
                    break

        return True

    def _parse_entry_type3(self):
        """type3 contains info about virt disks"""
        temp_disk = None
        for disk in self.disk_list:
            if len(disk.sdbb_entry_type3) == 0:
                continue
            else:
                temp_disk = disk
        for i in range(0, len(temp_disk.sdbb_entry_type3)):
            disk = Disk()
            temp_offset = 0
            print_hex(temp_disk.sdbb_entry_type3[i])
            data_record_len = temp_disk.sdbb_entry_type3[i][temp_offset]
            virtual_disk_id = big_endian_to_int(temp_disk.sdbb_entry_type3[i][temp_offset + 1: temp_offset + 1 + data_record_len])
            print("VD# " + str(virtual_disk_id))
            temp_offset += data_record_len + 1
            virtual_disk_block_number = 0
            if self.version == Define.WINDOWS_SERVER_2019:
                # NOTE: maybe structure changed in Win2019...
                temp_offset += temp_disk.sdbb_entry_type3[i][temp_offset] + 1
                virtual_disk_uuid = temp_disk.sdbb_entry_type3[i][temp_offset: temp_offset + 0x10]
                temp_offset += 0x10
                #print(str(temp_offset))
                virtual_disk_name_length = struct.unpack('>H', temp_disk.sdbb_entry_type3[i][temp_offset: temp_offset + 0x02])[0]
                temp_offset += 0x02

                virtual_disk_name = b''
                temp_virtual_disk_name = temp_disk.sdbb_entry_type3[i][temp_offset: temp_offset + virtual_disk_name_length * 2]
                temp_offset += virtual_disk_name_length * 2
                for j in range(0, virtual_disk_name_length * 2, 2):
                    virtual_disk_name += temp_virtual_disk_name[j + 1 : j + 2]
                    virtual_disk_name += temp_virtual_disk_name[j : j + 1]
                #print(str(temp_offset))
                #print(virtual_disk_name)
                disk_description_length = struct.unpack('>H', temp_disk.sdbb_entry_type3[i][temp_offset: temp_offset + 0x02])[0]
                temp_offset += 0x02

                disk_description = b''
                temp_disk_description = temp_disk.sdbb_entry_type3[i][temp_offset: temp_offset + disk_description_length * 2]
                temp_offset += disk_description_length * 2
                for j in range(0, disk_description_length * 2, 2):
                    disk_description += temp_disk_description[j + 1: j + 2]
                    disk_description += temp_disk_description[j: j + 1]

                temp_offset += 3
                #print_hex(temp_disk.sdbb_entry_type3[i][temp_offset:])
                if self.version == Define.WINDOWS_SERVER_2019 or self.version == Define.WINDOWS_10:
                    data_record_len = temp_disk.sdbb_entry_type3[i][temp_offset]
                    virtual_disk_bytes = int(big_endian_to_int(
                        temp_disk.sdbb_entry_type3[i][temp_offset + 1: temp_offset + 1 + data_record_len]))
                    virtual_disk_block_number = int(virtual_disk_bytes / 0x10000000) # TODO: use allocation unit here (256MB is default but it may be different)
                if virtual_disk_block_number == 0:
                    data_record_len = temp_disk.sdbb_entry_type3[i][temp_offset]
                    virtual_disk_block_number = big_endian_to_int(temp_disk.sdbb_entry_type3[i][temp_offset + 1: temp_offset + 1 + data_record_len])
            else:
                temp_offset += temp_disk.sdbb_entry_type3[i][temp_offset] + 1
                virtual_disk_uuid = temp_disk.sdbb_entry_type3[i][temp_offset: temp_offset + 0x10]
                temp_offset += 0x10
                print("UUID:",)
                print_hex(virtual_disk_uuid)
                
                virtual_disk_name_length = struct.unpack('>H', temp_disk.sdbb_entry_type3[i][temp_offset: temp_offset + 0x02])[0]
                temp_offset += 0x02
                print_hex(temp_disk.sdbb_entry_type3[temp_offset:])
                virtual_disk_name = b''
                temp_virtual_disk_name = temp_disk.sdbb_entry_type3[i][temp_offset: temp_offset + virtual_disk_name_length * 2]
                temp_offset += virtual_disk_name_length * 2
                for j in range(0, virtual_disk_name_length * 2, 2):
                    virtual_disk_name += temp_virtual_disk_name[j + 1 : j + 2]
                    virtual_disk_name += temp_virtual_disk_name[j : j + 1]
                print(str(temp_offset))
                disk_description_length = struct.unpack('>H', temp_disk.sdbb_entry_type3[i][temp_offset: temp_offset + 0x02])[0]
                temp_offset += 0x02

                disk_description = b''
                temp_disk_description = temp_disk.sdbb_entry_type3[i][temp_offset: temp_offset + disk_description_length * 2]
                temp_offset += disk_description_length * 2
                for j in range(0, disk_description_length * 2, 2):
                    disk_description += temp_disk_description[j + 1: j + 2]
                    disk_description += temp_disk_description[j: j + 1]

                # if self.version == Define.WINDOWS_SERVER_2012:
                #     temp_offset += temp_disk.sdbb_entry_type3[i][temp_offset] + 1
                #     temp_offset += temp_disk.sdbb_entry_type3[i][temp_offset] + 1
                #     temp_offset += temp_disk.sdbb_entry_type3[i][temp_offset] + 1
                #     temp_offset += temp_disk.sdbb_entry_type3[i][temp_offset] + 1
                #     temp_offset += temp_disk.sdbb_entry_type3[i][temp_offset] + 1
                #     temp_offset += temp_disk.sdbb_entry_type3[i][temp_offset] + 1
                #     temp_offset += 1
                # else:
                #    temp_offset += 3
                temp_offset += 3

                if self.version == Define.WINDOWS_SERVER_2019 or self.version == Define.WINDOWS_10:
                    data_record_len = temp_disk.sdbb_entry_type3[i][temp_offset]
                    data_record_len -= 3
                    virtual_disk_block_number = int(big_endian_to_int(
                        temp_disk.sdbb_entry_type3[i][temp_offset + 1: temp_offset + 1 + data_record_len]) / 0x10)
                if virtual_disk_block_number == 0:
                    data_record_len = temp_disk.sdbb_entry_type3[i][temp_offset]
                    virtual_disk_block_number = big_endian_to_int(temp_disk.sdbb_entry_type3[i][temp_offset + 1: temp_offset + 1 + data_record_len])


            disk.id = virtual_disk_id
            disk.uuid = virtual_disk_uuid
            disk.name = virtual_disk_name
            disk.block_number = virtual_disk_block_number
            print("VD #"+str(disk.id) + " " + str(disk.name.decode('utf-16')) + " blocks " + str(disk.block_number))

            self.parsed_disks[virtual_disk_id] = disk

        return True

    def _parse_entry_type4(self):
        temp_disk = None
        blocks_allocated = 0
        for disk in self.disk_list:
            if len(disk.sdbb_entry_type4) == 0:
                continue
            else:
                temp_disk = disk
        if self.version == Define.WINDOWS_8 or self.version == Define.WINDOWS_SERVER_2012:
            for i in range(0, len(temp_disk.sdbb_entry_type4)):
                sdbb_entry_type4_data = {}
                sdbb_entry_type4_data['virtual_disk_id'] = None
                sdbb_entry_type4_data['virtual_disk_block_number'] = None
                sdbb_entry_type4_data['sequence_number'] = None
                sdbb_entry_type4_data['physical_disk_id'] = None
                sdbb_entry_type4_data['physical_disk_block_number'] = None
                temp_offset = 0

                temp_offset += temp_disk.sdbb_entry_type4[i][temp_offset] + 1
                temp_offset += temp_disk.sdbb_entry_type4[i][temp_offset] + 1
                temp_offset += temp_disk.sdbb_entry_type4[i][temp_offset] + 1

                data_record_len = temp_disk.sdbb_entry_type4[i][temp_offset]
                sdbb_entry_type4_data['virtual_disk_id'] = big_endian_to_int(
                    temp_disk.sdbb_entry_type4[i][temp_offset + 1: temp_offset + 1 + data_record_len])
                temp_offset += temp_disk.sdbb_entry_type4[i][temp_offset] + 1

                data_record_len = temp_disk.sdbb_entry_type4[i][temp_offset]
                sdbb_entry_type4_data['virtual_disk_block_number'] = big_endian_to_int(
                    temp_disk.sdbb_entry_type4[i][temp_offset + 1: temp_offset + 1 + data_record_len])
                temp_offset += temp_disk.sdbb_entry_type4[i][temp_offset] + 1

                data_record_len = temp_disk.sdbb_entry_type4[i][temp_offset]
                sdbb_entry_type4_data['sequence_number'] = big_endian_to_int(
                    temp_disk.sdbb_entry_type4[i][temp_offset + 1: temp_offset + 1 + data_record_len])
                temp_offset += temp_disk.sdbb_entry_type4[i][temp_offset] + 1

                data_record_len = temp_disk.sdbb_entry_type4[i][temp_offset]
                sdbb_entry_type4_data['physical_disk_id'] = big_endian_to_int(
                    temp_disk.sdbb_entry_type4[i][temp_offset + 1: temp_offset + 1 + data_record_len])
                temp_offset += temp_disk.sdbb_entry_type4[i][temp_offset] + 1

                data_record_len = temp_disk.sdbb_entry_type4[i][temp_offset]
                sdbb_entry_type4_data['physical_disk_block_number'] = big_endian_to_int(
                    temp_disk.sdbb_entry_type4[i][temp_offset + 1: temp_offset + 1 + data_record_len])
                temp_offset += temp_disk.sdbb_entry_type4[i][temp_offset] + 1

                self.parsed_disks[sdbb_entry_type4_data['virtual_disk_id']].sdbb_entry_type4.append(sdbb_entry_type4_data)

        elif self.version == Define.WINDOWS_10 or self.version == Define.WINDOWS_SERVER_2016 or self.version == Define.WINDOWS_SERVER_2019:
            for i in range(0, len(temp_disk.sdbb_entry_type4)):
                sdbb_entry_type4_data = {}
                sdbb_entry_type4_data['virtual_disk_id'] = None
                sdbb_entry_type4_data['virtual_disk_block_number'] = None
                sdbb_entry_type4_data['parity_sequence_number'] = None
                sdbb_entry_type4_data['mirror_sequence_number'] = None
                sdbb_entry_type4_data['physical_disk_id'] = None
                sdbb_entry_type4_data['physical_disk_block_number'] = None
                sdbb_entry_type4_data['flag'] = None
                temp_offset = 0
                #print(i)
                if self.version == Define.WINDOWS_SERVER_2019:
                    temp_offset += 8  # the value varies from computer to computer
                    # TODO: learn how to fix that
                else:
                    temp_offset += 9  # the value varies from computer to computer
                    # TODO: learn how to fix that
                    #temp_offset += temp_disk.sdbb_entry_type4[i][temp_offset] + 1
                    #temp_offset += temp_disk.sdbb_entry_type4[i][temp_offset] + 1
                    #temp_offset += temp_disk.sdbb_entry_type4[i][temp_offset] + 1
                    #temp_offset += temp_disk.sdbb_entry_type4[i][temp_offset] + 1
                    #temp_offset += temp_disk.sdbb_entry_type4[i][temp_offset] + 1
                sdbb_entry_type4_data['flag'] = temp_disk.sdbb_entry_type4[i][6]
                #print_hex(temp_disk.sdbb_entry_type4[i][temp_offset:])
                data_record_len = temp_disk.sdbb_entry_type4[i][temp_offset]
                sdbb_entry_type4_data['virtual_disk_id'] = big_endian_to_int(
                    temp_disk.sdbb_entry_type4[i][temp_offset + 1: temp_offset + 1 + data_record_len])
                temp_offset += temp_disk.sdbb_entry_type4[i][temp_offset] + 1
                #print("VD: " + str(sdbb_entry_type4_data['virtual_disk_id']))
                #print_hex(temp_disk.sdbb_entry_type4[i][temp_offset:])
                data_record_len = temp_disk.sdbb_entry_type4[i][temp_offset]
                sdbb_entry_type4_data['virtual_disk_block_number'] = big_endian_to_int(
                    temp_disk.sdbb_entry_type4[i][temp_offset + 1: temp_offset + 1 + data_record_len])
                temp_offset += temp_disk.sdbb_entry_type4[i][temp_offset] + 1

                data_record_len = temp_disk.sdbb_entry_type4[i][temp_offset]
                sdbb_entry_type4_data['parity_sequence_number'] = big_endian_to_int(
                    temp_disk.sdbb_entry_type4[i][temp_offset + 1: temp_offset + 1 + data_record_len])
                temp_offset += temp_disk.sdbb_entry_type4[i][temp_offset] + 1

                data_record_len = temp_disk.sdbb_entry_type4[i][temp_offset]
                sdbb_entry_type4_data['mirror_sequence_number'] = big_endian_to_int(
                    temp_disk.sdbb_entry_type4[i][temp_offset + 1: temp_offset + 1 + data_record_len])
                temp_offset += temp_disk.sdbb_entry_type4[i][temp_offset] + 1

                temp_offset += temp_disk.sdbb_entry_type4[i][temp_offset] + 1

                data_record_len = temp_disk.sdbb_entry_type4[i][temp_offset]
                sdbb_entry_type4_data['physical_disk_id'] = big_endian_to_int(
                    temp_disk.sdbb_entry_type4[i][temp_offset + 1: temp_offset + 1 + data_record_len])
                temp_offset += temp_disk.sdbb_entry_type4[i][temp_offset] + 1

                data_record_len = temp_disk.sdbb_entry_type4[i][temp_offset]
                sdbb_entry_type4_data['physical_disk_block_number'] = big_endian_to_int(
                    temp_disk.sdbb_entry_type4[i][temp_offset + 1: temp_offset + 1 + data_record_len])
                temp_offset += temp_disk.sdbb_entry_type4[i][temp_offset] + 1

                if sdbb_entry_type4_data['virtual_disk_block_number'] == 0xBB5:
                    print("0xBB5: disk #"+str(sdbb_entry_type4_data['physical_disk_id']) + " mirror seq " + str(sdbb_entry_type4_data['mirror_sequence_number']))
                    print_hex(temp_disk.sdbb_entry_type4[i])

                if self.parsed_disks[sdbb_entry_type4_data['virtual_disk_id']] != None:
                    self.parsed_disks[sdbb_entry_type4_data['virtual_disk_id']].sdbb_entry_type4.append(
                        sdbb_entry_type4_data)
                    blocks_allocated += 1
        print("Blocks allocated: " + str(blocks_allocated))


    def _open_output_disk(self, virt_disk_name , output_path , direct_mode = False , dump_only_mode = False):
        """ create a disk based on path """
        if direct_mode == False:
            postfix = ".dd"
            if dump_only_mode:
                postfix=".txt"
            return open(output_path + "\\" + virt_disk_name + postfix, 'wb')
        else:
            """ interprets output_path as a collection of  """
            virt_phys_map = eval(output_path)
            if isinstance(virt_phys_map, str):
                return open(virt_phys_map, 'r+b')
            if isinstance(virt_phys_map, dict):
                if not virt_disk_name in virt_phys_map:
                    print("Failed to find mapping between " + virt_disk_name + " and target disk")
                    return None
                mapped_name = virt_phys_map[virt_disk_name]
                return open(mapped_name, 'r+b')
            else:
                print("Failed to read disk map: " + str(output_path))
                print("it must be string or python dict")
                return None
            return open(output_path, 'wb')


    """ restore disks """
    def restore_virtual_disk(self, output_path=None, modes=dict()):
        direct_mode = False
        list_only_mode = False
        dump_only_mode = False
        if "direct_output" in modes:
            direct_mode = modes["direct_output"]
        if "list_only" in modes:
            list_only_mode = modes["list_only"]
        if "dump_only" in modes:
            dump_only_mode = modes["dump_only"]
        for disk in self.parsed_disks:
            if disk == None:  # None skip
                continue

            if repr(disk.dp) == "Storage Space":  # physical disk skip
                continue

            elif disk.dp == None:
                
                #if disk.name == b'':  # Metadata Area(SPACEDB, SDBC, SDBB) skip
                #    continue

                if list_only_mode:
                    print("Virtual disk found: " + repr(disk.__dict__))
                    continue

                if output_path == None:# or os.path.exists(output_path) == False:
                    print("[Error] check output_path (" + output_path + ")")
                    return False
                if direct_mode == False and os.path.exists(output_path) == False:
                    print("[Error] please make the output_path (" + output_path + ")")
                    return False

                print("[*] Start Reconstruction.")
                if disk.name:
                    virt_disk_name = disk.name[:-2].decode('utf-16')
                else:
                    virt_disk_name = "aux" + disk.uuid.hex()
                disk.dp = self._open_output_disk(virt_disk_name , output_path, direct_mode, dump_only_mode)
                if disk.dp == None:
                    print("Failed to open output disk/file for virt disk " + virt_disk_name)
                    continue
                if dump_only_mode:
                    disk.dp.write(repr(disk.__dict__).replace('{','\n{').encode())
                    continue
                if self.version == Define.WINDOWS_8:
                    """ Simple, Mirror """
                    if self.level == Define.RAID_LEVEL_SIMPLE or self.level == Define.RAID_LEVEL_2MIRROR or \
                            self.level == Define.RAID_LEVEL_3MIRROR :

                        for i in range(0, disk.block_number):
                            is_exist_disk_block = False
                            for j in range(0, len(disk.sdbb_entry_type4)):
                                if disk.sdbb_entry_type4[j]['virtual_disk_block_number'] == i:
                                    partition_start_offset = self.parsed_disks[disk.sdbb_entry_type4[j]['physical_disk_id']].dp.partition_start_offset
                                    self.parsed_disks[disk.sdbb_entry_type4[j]['physical_disk_id']].dp.dp.seek((disk.sdbb_entry_type4[j]['physical_disk_block_number'] + 2) * 0x10000000 + partition_start_offset)  # SPACEDB 시작 offset을 더해줘야함
                                    disk.dp.write(self.parsed_disks[disk.sdbb_entry_type4[j]['physical_disk_id']].dp.dp.read(0x10000000))
                                    is_exist_disk_block = True
                                    break

                            if is_exist_disk_block == False:
                               skip_disk_bytes (disk.dp, 0x10000000, direct_mode)

                    """ Parity """
                    if self.level == Define.RAID_LEVEL_PARITY :
                        for i in range(0, disk.block_number, 2):
                            is_exist_disk_block = False

                            temp_entry_type4_0 = None  # Sequence 0
                            temp_entry_type4_1 = None  # Sequence 1
                            temp_entry_type4_2 = None  # Sequence 2

                            """ Search Sequence Number """
                            for j in range(0, len(disk.sdbb_entry_type4)):
                                if disk.sdbb_entry_type4[j]['virtual_disk_block_number'] == i:
                                    if disk.sdbb_entry_type4[j]['sequence_number'] == 0:
                                        temp_entry_type4_0 = disk.sdbb_entry_type4[j]
                                        is_exist_disk_block = True
                                    elif disk.sdbb_entry_type4[j]['sequence_number'] == 1:
                                        temp_entry_type4_1 = disk.sdbb_entry_type4[j]
                                        is_exist_disk_block = True
                                    elif disk.sdbb_entry_type4[j]['sequence_number'] == 2:
                                        temp_entry_type4_2 = disk.sdbb_entry_type4[j]
                                        is_exist_disk_block = True

                            if is_exist_disk_block == False:
                                skip_disk_bytes (disk.dp, 0x20000000, direct_mode)
                                continue

                            partition_start_offset_0 = self.parsed_disks[temp_entry_type4_0['physical_disk_id']].dp.partition_start_offset
                            partition_start_offset_1 = self.parsed_disks[temp_entry_type4_1['physical_disk_id']].dp.partition_start_offset
                            partition_start_offset_2 = self.parsed_disks[temp_entry_type4_2['physical_disk_id']].dp.partition_start_offset
                            self.parsed_disks[temp_entry_type4_0['physical_disk_id']].dp.dp.seek((temp_entry_type4_0[
                                                                                                      'physical_disk_block_number'] + 2) * 0x10000000 + partition_start_offset_0)  # SPACEDB 시작 offset을 더해줘야함
                            self.parsed_disks[temp_entry_type4_1['physical_disk_id']].dp.dp.seek((temp_entry_type4_1[
                                                                                                      'physical_disk_block_number'] + 2) * 0x10000000 + partition_start_offset_1)  # SPACEDB 시작 offset을 더해줘야함
                            self.parsed_disks[temp_entry_type4_2['physical_disk_id']].dp.dp.seek((temp_entry_type4_2[
                                                                                                      'physical_disk_block_number'] + 2) * 0x10000000 + partition_start_offset_2)  # SPACEDB 시작 offset을 더해줘야함

                            for j in range(0, 0x400):
                                if j % 3 == 0:
                                    disk.dp.write(self.parsed_disks[temp_entry_type4_0['physical_disk_id']].dp.dp.read(0x40000))
                                    disk.dp.write(self.parsed_disks[temp_entry_type4_1['physical_disk_id']].dp.dp.read(0x40000))
                                    self.parsed_disks[temp_entry_type4_2['physical_disk_id']].dp.dp.seek(0x40000, os.SEEK_CUR)
                                if j % 3 == 1:
                                    disk.dp.write(self.parsed_disks[temp_entry_type4_2['physical_disk_id']].dp.dp.read(0x40000))
                                    disk.dp.write(self.parsed_disks[temp_entry_type4_0['physical_disk_id']].dp.dp.read(0x40000))
                                    self.parsed_disks[temp_entry_type4_1['physical_disk_id']].dp.dp.seek(0x40000,os.SEEK_CUR)
                                if j % 3 == 2:
                                    disk.dp.write(self.parsed_disks[temp_entry_type4_1['physical_disk_id']].dp.dp.read(0x40000))
                                    disk.dp.write(self.parsed_disks[temp_entry_type4_2['physical_disk_id']].dp.dp.read(0x40000))
                                    self.parsed_disks[temp_entry_type4_0['physical_disk_id']].dp.dp.seek(0x40000, os.SEEK_CUR)

                elif self.version == Define.WINDOWS_SERVER_2012:
                    """ Mirror """
                    if self.level == Define.RAID_LEVEL_2MIRROR or self.level == Define.RAID_LEVEL_3MIRROR:
                        for i in range(0, disk.block_number, 4):  # Block Size : 1GB
                            is_exist_disk_block = False
                            for j in range(0, len(disk.sdbb_entry_type4)):
                                if disk.sdbb_entry_type4[j]['virtual_disk_block_number'] == i:
                                    partition_start_offset = self.parsed_disks[disk.sdbb_entry_type4[j]['physical_disk_id']].dp.partition_start_offset
                                    self.parsed_disks[disk.sdbb_entry_type4[j]['physical_disk_id']].dp.dp.seek((disk.sdbb_entry_type4[j]['physical_disk_block_number'] + 2) * 0x10000000 + partition_start_offset)  # SPACEDB 시작 offset을 더해줘야함
                                    disk.dp.write(self.parsed_disks[disk.sdbb_entry_type4[j]['physical_disk_id']].dp.dp.read(0x40000000))
                                    is_exist_disk_block = True
                                    break

                            if is_exist_disk_block == False:
                                skip_disk_bytes (disk.dp, 0x40000000, direct_mode)

                    elif self.level == Define.RAID_LEVEL_SIMPLE:
                        for i in range(0, disk.block_number, 12):
                                is_exist_disk_block = False

                                temp_entry_type4_0 = None  # Sequence 0
                                temp_entry_type4_1 = None  # Sequence 1
                                temp_entry_type4_2 = None  # Sequence 2

                                """ Search Sequence Number """
                                for j in range(0, len(disk.sdbb_entry_type4)):
                                    if disk.sdbb_entry_type4[j]['virtual_disk_block_number'] == i:
                                        if disk.sdbb_entry_type4[j]['sequence_number'] == 0:
                                            temp_entry_type4_0 = disk.sdbb_entry_type4[j]
                                            is_exist_disk_block = True
                                        elif disk.sdbb_entry_type4[j]['sequence_number'] == 1:
                                            temp_entry_type4_1 = disk.sdbb_entry_type4[j]
                                            is_exist_disk_block = True
                                        elif disk.sdbb_entry_type4[j]['sequence_number'] == 2:
                                            temp_entry_type4_2 = disk.sdbb_entry_type4[j]
                                            is_exist_disk_block = True

                                if is_exist_disk_block == False:
                                    skip_disk_bytes (disk.dp, 0xC0000000, direct_mode)
                                    continue

                                partition_start_offset_0 = self.parsed_disks[temp_entry_type4_0['physical_disk_id']].dp.partition_start_offset
                                partition_start_offset_1 = self.parsed_disks[temp_entry_type4_1['physical_disk_id']].dp.partition_start_offset
                                partition_start_offset_2 = self.parsed_disks[temp_entry_type4_2['physical_disk_id']].dp.partition_start_offset
                                self.parsed_disks[temp_entry_type4_0['physical_disk_id']].dp.dp.seek((temp_entry_type4_0['physical_disk_block_number'] + 2) * 0x10000000 + partition_start_offset_0)
                                self.parsed_disks[temp_entry_type4_1['physical_disk_id']].dp.dp.seek((temp_entry_type4_1['physical_disk_block_number'] + 2) * 0x10000000 + partition_start_offset_1)  # SPACEDB 시작 offset을 더해줘야함
                                self.parsed_disks[temp_entry_type4_2['physical_disk_id']].dp.dp.seek((temp_entry_type4_2['physical_disk_block_number'] + 2) * 0x10000000 + partition_start_offset_2)  # SPACEDB 시작 offset을 더해줘야함
                                for j in range(0, 0x1000):
                                    disk.dp.write(self.parsed_disks[temp_entry_type4_0['physical_disk_id']].dp.dp.read(0x40000))
                                    disk.dp.write(self.parsed_disks[temp_entry_type4_1['physical_disk_id']].dp.dp.read(0x40000))
                                    disk.dp.write(self.parsed_disks[temp_entry_type4_2['physical_disk_id']].dp.dp.read(0x40000))

                    elif self.level == Define.RAID_LEVEL_PARITY:
                        for i in range(0, disk.block_number, 12):
                                is_exist_disk_block = False

                                temp_entry_type4_0 = None  # Sequence 0
                                temp_entry_type4_1 = None  # Sequence 1
                                temp_entry_type4_2 = None  # Sequence 2
                                temp_entry_type4_3 = None  # Sequence 3

                                """ Search Sequence Number """
                                for j in range(0, len(disk.sdbb_entry_type4)):
                                    if disk.sdbb_entry_type4[j]['virtual_disk_block_number'] == i:
                                        if disk.sdbb_entry_type4[j]['sequence_number'] == 0:
                                            temp_entry_type4_0 = disk.sdbb_entry_type4[j]
                                            is_exist_disk_block = True
                                        elif disk.sdbb_entry_type4[j]['sequence_number'] == 1:
                                            temp_entry_type4_1 = disk.sdbb_entry_type4[j]
                                            is_exist_disk_block = True
                                        elif disk.sdbb_entry_type4[j]['sequence_number'] == 2:
                                            temp_entry_type4_2 = disk.sdbb_entry_type4[j]
                                            is_exist_disk_block = True
                                        elif disk.sdbb_entry_type4[j]['sequence_number'] == 3:
                                            temp_entry_type4_3 = disk.sdbb_entry_type4[j]
                                            is_exist_disk_block = True

                                if is_exist_disk_block == False:
                                    skip_disk_bytes (disk.dp, 0xC0000000, direct_mode)
                                    continue

                                partition_start_offset_0 = self.parsed_disks[temp_entry_type4_0['physical_disk_id']].dp.partition_start_offset
                                partition_start_offset_1 = self.parsed_disks[temp_entry_type4_1['physical_disk_id']].dp.partition_start_offset
                                partition_start_offset_2 = self.parsed_disks[temp_entry_type4_2['physical_disk_id']].dp.partition_start_offset
                                partition_start_offset_3 = self.parsed_disks[temp_entry_type4_3['physical_disk_id']].dp.partition_start_offset
                                self.parsed_disks[temp_entry_type4_0['physical_disk_id']].dp.dp.seek((temp_entry_type4_0['physical_disk_block_number'] + 2) * 0x10000000 + partition_start_offset_0)
                                self.parsed_disks[temp_entry_type4_1['physical_disk_id']].dp.dp.seek((temp_entry_type4_1['physical_disk_block_number'] + 2) * 0x10000000 + partition_start_offset_1)  # SPACEDB 시작 offset을 더해줘야함
                                self.parsed_disks[temp_entry_type4_2['physical_disk_id']].dp.dp.seek((temp_entry_type4_2['physical_disk_block_number'] + 2) * 0x10000000 + partition_start_offset_2)  # SPACEDB 시작 offset을 더해줘야함
                                self.parsed_disks[temp_entry_type4_3['physical_disk_id']].dp.dp.seek((temp_entry_type4_3['physical_disk_block_number'] + 2) * 0x10000000 + partition_start_offset_3)  # SPACEDB 시작 offset을 더해줘야함

                                for j in range(0, 0x1000):
                                    if j % 4 == 0:
                                        disk.dp.write(self.parsed_disks[temp_entry_type4_0['physical_disk_id']].dp.dp.read(0x40000))
                                        disk.dp.write(self.parsed_disks[temp_entry_type4_1['physical_disk_id']].dp.dp.read(0x40000))
                                        disk.dp.write(self.parsed_disks[temp_entry_type4_2['physical_disk_id']].dp.dp.read(0x40000))
                                        self.parsed_disks[temp_entry_type4_3['physical_disk_id']].dp.dp.seek(0x40000, os.SEEK_CUR)
                                    elif j % 4 == 1:
                                        disk.dp.write(self.parsed_disks[temp_entry_type4_3['physical_disk_id']].dp.dp.read(0x40000))
                                        disk.dp.write(self.parsed_disks[temp_entry_type4_0['physical_disk_id']].dp.dp.read(0x40000))
                                        disk.dp.write(self.parsed_disks[temp_entry_type4_1['physical_disk_id']].dp.dp.read(0x40000))
                                        self.parsed_disks[temp_entry_type4_2['physical_disk_id']].dp.dp.seek(0x40000, os.SEEK_CUR)
                                    elif j % 4 == 2:
                                        disk.dp.write(self.parsed_disks[temp_entry_type4_2['physical_disk_id']].dp.dp.read(0x40000))
                                        disk.dp.write(self.parsed_disks[temp_entry_type4_3['physical_disk_id']].dp.dp.read(0x40000))
                                        disk.dp.write(self.parsed_disks[temp_entry_type4_0['physical_disk_id']].dp.dp.read(0x40000))
                                        self.parsed_disks[temp_entry_type4_1['physical_disk_id']].dp.dp.seek(0x40000, os.SEEK_CUR)
                                    elif j % 4 == 3:
                                        disk.dp.write(self.parsed_disks[temp_entry_type4_1['physical_disk_id']].dp.dp.read(0x40000))
                                        disk.dp.write(self.parsed_disks[temp_entry_type4_2['physical_disk_id']].dp.dp.read(0x40000))
                                        disk.dp.write(self.parsed_disks[temp_entry_type4_3['physical_disk_id']].dp.dp.read(0x40000))
                                        self.parsed_disks[temp_entry_type4_0['physical_disk_id']].dp.dp.seek(0x40000, os.SEEK_CUR)

                elif self.version == Define.WINDOWS_10 or self.version == Define.WINDOWS_SERVER_2016:
                    """ Simple, Mirror """
                    if self.level == Define.RAID_LEVEL_SIMPLE or self.level == Define.RAID_LEVEL_2MIRROR or \
                            self.level == Define.RAID_LEVEL_3MIRROR:
                        total_size = 0
                        for i in range(0, disk.block_number):
                            is_exist_disk_block = False
                            for j in range(0, len(disk.sdbb_entry_type4)):
                                if disk.sdbb_entry_type4[j]['virtual_disk_block_number'] == i:
                                    partition_start_offset = self.parsed_disks[disk.sdbb_entry_type4[j]['physical_disk_id']].dp.partition_start_offset
                                    self.parsed_disks[disk.sdbb_entry_type4[j]['physical_disk_id']].dp.dp.seek((disk.sdbb_entry_type4[j]['physical_disk_block_number'] + 2) * 0x10000000 + partition_start_offset)  # SPACEDB 시작 offset을 더해줘야함
                                    disk.dp.write(self.parsed_disks[disk.sdbb_entry_type4[j]['physical_disk_id']].dp.dp.read(0x10000000))
                                    is_exist_disk_block = True
                                    break

                            if is_exist_disk_block == False:
                                skip_disk_bytes (disk.dp, 0x10000000, direct_mode)
                            else:
                                total_size += 0x10000000


                    """ Parity """
                    if self.level == Define.RAID_LEVEL_PARITY:
                        for i in range(0, disk.block_number, 2):
                            is_exist_disk_block = False

                            temp_entry_type4_0 = None  # Sequence 0
                            temp_entry_type4_1 = None  # Sequence 1
                            temp_entry_type4_2 = None  # Sequence 2

                            """ Search Sequence Number """
                            for j in range(0, len(disk.sdbb_entry_type4)):
                                if disk.sdbb_entry_type4[j]['virtual_disk_block_number'] == i:
                                    if disk.sdbb_entry_type4[j]['parity_sequence_number'] == 0:
                                        temp_entry_type4_0 = disk.sdbb_entry_type4[j]
                                        is_exist_disk_block = True
                                    elif disk.sdbb_entry_type4[j]['parity_sequence_number'] == 1:
                                        temp_entry_type4_1 = disk.sdbb_entry_type4[j]
                                        is_exist_disk_block = True
                                    elif disk.sdbb_entry_type4[j]['parity_sequence_number'] == 2:
                                        temp_entry_type4_2 = disk.sdbb_entry_type4[j]
                                        is_exist_disk_block = True

                            if is_exist_disk_block == False:
                                skip_disk_bytes (disk.dp, 0x20000000, direct_mode)
                                continue

                            partition_start_offset_0 = self.parsed_disks[temp_entry_type4_0['physical_disk_id']].dp.partition_start_offset
                            partition_start_offset_1 = self.parsed_disks[temp_entry_type4_1['physical_disk_id']].dp.partition_start_offset
                            partition_start_offset_2 = self.parsed_disks[temp_entry_type4_2['physical_disk_id']].dp.partition_start_offset
                            self.parsed_disks[temp_entry_type4_0['physical_disk_id']].dp.dp.seek((temp_entry_type4_0[
                                                                                                      'physical_disk_block_number'] + 2) * 0x10000000 + partition_start_offset_0)  # SPACEDB 시작 offset을 더해줘야함
                            self.parsed_disks[temp_entry_type4_1['physical_disk_id']].dp.dp.seek((temp_entry_type4_1[
                                                                                                      'physical_disk_block_number'] + 2) * 0x10000000 + partition_start_offset_1)  # SPACEDB 시작 offset을 더해줘야함
                            self.parsed_disks[temp_entry_type4_2['physical_disk_id']].dp.dp.seek((temp_entry_type4_2[
                                                                                                      'physical_disk_block_number'] + 2) * 0x10000000 + partition_start_offset_2)  # SPACEDB 시작 offset을 더해줘야함

                            for j in range(0, 0x400):
                                if j % 3 == 0:
                                    disk.dp.write(self.parsed_disks[temp_entry_type4_0['physical_disk_id']].dp.dp.read(0x40000))
                                    disk.dp.write(self.parsed_disks[temp_entry_type4_1['physical_disk_id']].dp.dp.read(0x40000))
                                    self.parsed_disks[temp_entry_type4_2['physical_disk_id']].dp.dp.seek(0x40000, os.SEEK_CUR)
                                if j % 3 == 1:
                                    disk.dp.write(self.parsed_disks[temp_entry_type4_2['physical_disk_id']].dp.dp.read(0x40000))
                                    disk.dp.write(self.parsed_disks[temp_entry_type4_0['physical_disk_id']].dp.dp.read(0x40000))
                                    self.parsed_disks[temp_entry_type4_1['physical_disk_id']].dp.dp.seek(0x40000,os.SEEK_CUR)
                                if j % 3 == 2:
                                    disk.dp.write(self.parsed_disks[temp_entry_type4_1['physical_disk_id']].dp.dp.read(0x40000))
                                    disk.dp.write(self.parsed_disks[temp_entry_type4_2['physical_disk_id']].dp.dp.read(0x40000))
                                    self.parsed_disks[temp_entry_type4_0['physical_disk_id']].dp.dp.seek(0x40000, os.SEEK_CUR)

                    """ Dual Parity """
                    if self.level == Define.RAID_LEVEL_2PARITY:
                        for i in range(0, disk.block_number, 16):
                            is_exist_disk_block = False

                            temp_entry_type4_0 = None  # Sequence 0
                            temp_entry_type4_1 = None  # Sequence 1
                            temp_entry_type4_2 = None  # Sequence 2
                            temp_entry_type4_3 = None  # Sequence 3
                            temp_entry_type4_4 = None  # Sequence 4
                            temp_entry_type4_5 = None  # Sequence 5

                            """ Search Sequence Number """
                            for j in range(0, len(disk.sdbb_entry_type4)):
                                if disk.sdbb_entry_type4[j]['virtual_disk_block_number'] == i:
                                    if disk.sdbb_entry_type4[j]['parity_sequence_number'] == 0:
                                        temp_entry_type4_0 = disk.sdbb_entry_type4[j]
                                        is_exist_disk_block = True
                                    elif disk.sdbb_entry_type4[j]['parity_sequence_number'] == 1:
                                        temp_entry_type4_1 = disk.sdbb_entry_type4[j]
                                        is_exist_disk_block = True
                                    elif disk.sdbb_entry_type4[j]['parity_sequence_number'] == 2:
                                        temp_entry_type4_2 = disk.sdbb_entry_type4[j]
                                        is_exist_disk_block = True
                                    elif disk.sdbb_entry_type4[j]['parity_sequence_number'] == 3:
                                        temp_entry_type4_3 = disk.sdbb_entry_type4[j]
                                        is_exist_disk_block = True
                                    elif disk.sdbb_entry_type4[j]['parity_sequence_number'] == 4:
                                        temp_entry_type4_4 = disk.sdbb_entry_type4[j]
                                        is_exist_disk_block = True
                                    elif disk.sdbb_entry_type4[j]['parity_sequence_number'] == 5:
                                        temp_entry_type4_5 = disk.sdbb_entry_type4[j]
                                        is_exist_disk_block = True

                            if is_exist_disk_block == False:
                                skip_disk_bytes (disk.dp, 0x100000000, direct_mode)
                                continue

                            partition_start_offset_0 = self.parsed_disks[temp_entry_type4_0['physical_disk_id']].dp.partition_start_offset
                            partition_start_offset_1 = self.parsed_disks[temp_entry_type4_1['physical_disk_id']].dp.partition_start_offset
                            partition_start_offset_2 = self.parsed_disks[temp_entry_type4_2['physical_disk_id']].dp.partition_start_offset
                            partition_start_offset_3 = self.parsed_disks[temp_entry_type4_3['physical_disk_id']].dp.partition_start_offset
                            partition_start_offset_4 = self.parsed_disks[temp_entry_type4_4['physical_disk_id']].dp.partition_start_offset
                            partition_start_offset_5 = self.parsed_disks[temp_entry_type4_5['physical_disk_id']].dp.partition_start_offset
                            self.parsed_disks[temp_entry_type4_0['physical_disk_id']].dp.dp.seek((temp_entry_type4_0[
                                                                                                      'physical_disk_block_number'] + 2) * 0x10000000 + partition_start_offset_0)  # SPACEDB 시작 offset을 더해줘야함
                            self.parsed_disks[temp_entry_type4_1['physical_disk_id']].dp.dp.seek((temp_entry_type4_1[
                                                                                                      'physical_disk_block_number'] + 2) * 0x10000000 + partition_start_offset_1)  # SPACEDB 시작 offset을 더해줘야함
                            self.parsed_disks[temp_entry_type4_2['physical_disk_id']].dp.dp.seek((temp_entry_type4_2[
                                                                                                      'physical_disk_block_number'] + 2) * 0x10000000 + partition_start_offset_2)  # SPACEDB 시작 offset을 더해줘야함
                            self.parsed_disks[temp_entry_type4_3['physical_disk_id']].dp.dp.seek((temp_entry_type4_3[
                                                                                                      'physical_disk_block_number'] + 2) * 0x10000000 + partition_start_offset_3)  # SPACEDB 시작 offset을 더해줘야함
                            self.parsed_disks[temp_entry_type4_4['physical_disk_id']].dp.dp.seek((temp_entry_type4_4[
                                                                                                      'physical_disk_block_number'] + 2) * 0x10000000 + partition_start_offset_4)  # SPACEDB 시작 offset을 더해줘야함
                            self.parsed_disks[temp_entry_type4_5['physical_disk_id']].dp.dp.seek((temp_entry_type4_5[
                                                                                                      'physical_disk_block_number'] + 2) * 0x10000000 + partition_start_offset_5)  # SPACEDB 시작 offset을 더해줘야함

                            for j in range(0, 0x1000):
                                if j % 3 == 0:
                                    disk.dp.write(self.parsed_disks[temp_entry_type4_0['physical_disk_id']].dp.dp.read(0x40000))
                                    disk.dp.write(self.parsed_disks[temp_entry_type4_1['physical_disk_id']].dp.dp.read(0x40000))
                                    disk.dp.write(self.parsed_disks[temp_entry_type4_2['physical_disk_id']].dp.dp.read(0x40000))
                                    disk.dp.write(self.parsed_disks[temp_entry_type4_3['physical_disk_id']].dp.dp.read(0x40000))
                                    self.parsed_disks[temp_entry_type4_4['physical_disk_id']].dp.dp.seek(0x40000, os.SEEK_CUR)
                                    self.parsed_disks[temp_entry_type4_5['physical_disk_id']].dp.dp.seek(0x40000, os.SEEK_CUR)
                                if j % 3 == 1:
                                    disk.dp.write(self.parsed_disks[temp_entry_type4_4['physical_disk_id']].dp.dp.read(0x40000))
                                    disk.dp.write(self.parsed_disks[temp_entry_type4_5['physical_disk_id']].dp.dp.read(0x40000))
                                    disk.dp.write(self.parsed_disks[temp_entry_type4_0['physical_disk_id']].dp.dp.read(0x40000))
                                    disk.dp.write(self.parsed_disks[temp_entry_type4_1['physical_disk_id']].dp.dp.read(0x40000))
                                    self.parsed_disks[temp_entry_type4_2['physical_disk_id']].dp.dp.seek(0x40000, os.SEEK_CUR)
                                    self.parsed_disks[temp_entry_type4_3['physical_disk_id']].dp.dp.seek(0x40000, os.SEEK_CUR)
                                if j % 3 == 2:
                                    disk.dp.write(self.parsed_disks[temp_entry_type4_2['physical_disk_id']].dp.dp.read(0x40000))
                                    disk.dp.write(self.parsed_disks[temp_entry_type4_3['physical_disk_id']].dp.dp.read(0x40000))
                                    disk.dp.write(self.parsed_disks[temp_entry_type4_4['physical_disk_id']].dp.dp.read(0x40000))
                                    disk.dp.write(self.parsed_disks[temp_entry_type4_5['physical_disk_id']].dp.dp.read(0x40000))
                                    self.parsed_disks[temp_entry_type4_0['physical_disk_id']].dp.dp.seek(0x40000, os.SEEK_CUR)
                                    self.parsed_disks[temp_entry_type4_1['physical_disk_id']].dp.dp.seek(0x40000, os.SEEK_CUR)

                elif self.version == Define.WINDOWS_SERVER_2019:
                    """ Mirror """
                    if self.level == Define.RAID_LEVEL_2MIRROR or self.level == Define.RAID_LEVEL_3MIRROR:
                        for i in range(0, disk.block_number, 4):  # Block Size : 1GB
                            is_exist_disk_block = False
                            for j in range(0, len(disk.sdbb_entry_type4)):
                                if disk.sdbb_entry_type4[j]['virtual_disk_block_number'] == i:
                                    partition_start_offset = self.parsed_disks[
                                        disk.sdbb_entry_type4[j]['physical_disk_id']].dp.partition_start_offset
                                    self.parsed_disks[disk.sdbb_entry_type4[j]['physical_disk_id']].dp.dp.seek((disk.sdbb_entry_type4[j]['physical_disk_block_number'] + 2) * 0x10000000 + partition_start_offset)  # SPACEDB 시작 offset을 더해줘야함
                                    disk.dp.write(
                                        self.parsed_disks[disk.sdbb_entry_type4[j]['physical_disk_id']].dp.dp.read(
                                            0x40000000))
                                    is_exist_disk_block = True
                                    break

                            if is_exist_disk_block == False:
                                skip_disk_bytes (disk.dp, 0x40000000, direct_mode)


                    elif self.level == Define.RAID_LEVEL_SIMPLE:
                        for i in range(0, disk.block_number):
                            is_exist_disk_block = False
                            for j in range(0, len(disk.sdbb_entry_type4)):
                                if disk.sdbb_entry_type4[j]['virtual_disk_block_number'] == i:
                                    partition_start_offset = self.parsed_disks[disk.sdbb_entry_type4[j]['physical_disk_id']].dp.partition_start_offset
                                    self.parsed_disks[disk.sdbb_entry_type4[j]['physical_disk_id']].dp.dp.seek((disk.sdbb_entry_type4[j]['physical_disk_block_number'] + 2) * 0x10000000 + partition_start_offset)  # SPACEDB 시작 offset을 더해줘야함
                                    disk.dp.write(self.parsed_disks[disk.sdbb_entry_type4[j]['physical_disk_id']].dp.dp.read(0x10000000))
                                    is_exist_disk_block = True
                                    break

                            if is_exist_disk_block == False:
                                skip_disk_bytes (disk.dp, 0x10000000, direct_mode)

                    elif self.level == Define.RAID_LEVEL_PARITY:
                        for i in range(0, disk.block_number, 8):
                            is_exist_disk_block = False

                            temp_entry_type4_0 = None  # Sequence 0
                            temp_entry_type4_1 = None  # Sequence 1
                            temp_entry_type4_2 = None  # Sequence 2

                            """ Search Sequence Number """
                            for j in range(0, len(disk.sdbb_entry_type4)):
                                if disk.sdbb_entry_type4[j]['virtual_disk_block_number'] == i:
                                    if disk.sdbb_entry_type4[j]['parity_sequence_number'] == 0:
                                        temp_entry_type4_0 = disk.sdbb_entry_type4[j]
                                        is_exist_disk_block = True
                                    elif disk.sdbb_entry_type4[j]['parity_sequence_number'] == 1:
                                        temp_entry_type4_1 = disk.sdbb_entry_type4[j]
                                        is_exist_disk_block = True
                                    elif disk.sdbb_entry_type4[j]['parity_sequence_number'] == 2:
                                        temp_entry_type4_2 = disk.sdbb_entry_type4[j]
                                        is_exist_disk_block = True

                            if is_exist_disk_block == False:
                                skip_disk_bytes (disk.dp, 0x80000000, direct_mode)
                                continue

                            partition_start_offset_0 = self.parsed_disks[
                                temp_entry_type4_0['physical_disk_id']].dp.partition_start_offset
                            partition_start_offset_1 = self.parsed_disks[
                                temp_entry_type4_1['physical_disk_id']].dp.partition_start_offset
                            partition_start_offset_2 = self.parsed_disks[
                                temp_entry_type4_2['physical_disk_id']].dp.partition_start_offset
                            self.parsed_disks[temp_entry_type4_0['physical_disk_id']].dp.dp.seek((temp_entry_type4_0[
                                                                                                      'physical_disk_block_number'] + 2) * 0x10000000 + partition_start_offset_0)
                            self.parsed_disks[temp_entry_type4_1['physical_disk_id']].dp.dp.seek((temp_entry_type4_1[
                                                                                                      'physical_disk_block_number'] + 2) * 0x10000000 + partition_start_offset_1)  # SPACEDB 시작 offset을 더해줘야함
                            self.parsed_disks[temp_entry_type4_2['physical_disk_id']].dp.dp.seek((temp_entry_type4_2[
                                                                                                      'physical_disk_block_number'] + 2) * 0x10000000 + partition_start_offset_2)  # SPACEDB 시작 offset을 더해줘야함
                            for j in range(0, 0x1000):
                                if j % 3 == 0:
                                    disk.dp.write(self.parsed_disks[temp_entry_type4_0['physical_disk_id']].dp.dp.read(0x40000))
                                    disk.dp.write(self.parsed_disks[temp_entry_type4_1['physical_disk_id']].dp.dp.read(0x40000))
                                    self.parsed_disks[temp_entry_type4_2['physical_disk_id']].dp.dp.seek(0x40000, os.SEEK_CUR)
                                if j % 3 == 1:
                                    disk.dp.write(self.parsed_disks[temp_entry_type4_2['physical_disk_id']].dp.dp.read(0x40000))
                                    disk.dp.write(self.parsed_disks[temp_entry_type4_0['physical_disk_id']].dp.dp.read(0x40000))
                                    self.parsed_disks[temp_entry_type4_1['physical_disk_id']].dp.dp.seek(0x40000,os.SEEK_CUR)
                                if j % 3 == 2:
                                    disk.dp.write(self.parsed_disks[temp_entry_type4_1['physical_disk_id']].dp.dp.read(0x40000))
                                    disk.dp.write(self.parsed_disks[temp_entry_type4_2['physical_disk_id']].dp.dp.read(0x40000))
                                    self.parsed_disks[temp_entry_type4_0['physical_disk_id']].dp.dp.seek(0x40000, os.SEEK_CUR)

                    elif self.level == Define.RAID_LEVEL_2PARITY:
                        for i in range(0, disk.block_number, 16):
                            is_exist_disk_block = False

                            temp_entry_type4_0 = None  # Sequence 0
                            temp_entry_type4_1 = None  # Sequence 1
                            temp_entry_type4_2 = None  # Sequence 2
                            temp_entry_type4_3 = None  # Sequence 3
                            temp_entry_type4_4 = None  # Sequence 4
                            temp_entry_type4_5 = None  # Sequence 5

                            """ Search Sequence Number """
                            for j in range(0, len(disk.sdbb_entry_type4)):
                                if disk.sdbb_entry_type4[j]['virtual_disk_block_number'] == i:
                                    if disk.sdbb_entry_type4[j]['parity_sequence_number'] == 0:
                                        temp_entry_type4_0 = disk.sdbb_entry_type4[j]
                                        is_exist_disk_block = True
                                    elif disk.sdbb_entry_type4[j]['parity_sequence_number'] == 1:
                                        temp_entry_type4_1 = disk.sdbb_entry_type4[j]
                                        is_exist_disk_block = True
                                    elif disk.sdbb_entry_type4[j]['parity_sequence_number'] == 2:
                                        temp_entry_type4_2 = disk.sdbb_entry_type4[j]
                                        is_exist_disk_block = True
                                    elif disk.sdbb_entry_type4[j]['parity_sequence_number'] == 3:
                                        temp_entry_type4_3 = disk.sdbb_entry_type4[j]
                                        is_exist_disk_block = True
                                    elif disk.sdbb_entry_type4[j]['parity_sequence_number'] == 4:
                                        temp_entry_type4_4 = disk.sdbb_entry_type4[j]
                                        is_exist_disk_block = True
                                    elif disk.sdbb_entry_type4[j]['parity_sequence_number'] == 5:
                                        temp_entry_type4_5 = disk.sdbb_entry_type4[j]
                                        is_exist_disk_block = True

                            if is_exist_disk_block == False:
                                skip_disk_bytes (disk.dp, 0x100000000, direct_mode)
                                continue

                            partition_start_offset_0 = self.parsed_disks[temp_entry_type4_0['physical_disk_id']].dp.partition_start_offset
                            partition_start_offset_1 = self.parsed_disks[temp_entry_type4_1['physical_disk_id']].dp.partition_start_offset
                            partition_start_offset_2 = self.parsed_disks[temp_entry_type4_2['physical_disk_id']].dp.partition_start_offset
                            partition_start_offset_3 = self.parsed_disks[temp_entry_type4_3['physical_disk_id']].dp.partition_start_offset
                            partition_start_offset_4 = self.parsed_disks[temp_entry_type4_4['physical_disk_id']].dp.partition_start_offset
                            partition_start_offset_5 = self.parsed_disks[temp_entry_type4_5['physical_disk_id']].dp.partition_start_offset
                            self.parsed_disks[temp_entry_type4_0['physical_disk_id']].dp.dp.seek((temp_entry_type4_0[
                                                                                                      'physical_disk_block_number'] + 2) * 0x10000000 + partition_start_offset_0)  # SPACEDB 시작 offset을 더해줘야함
                            self.parsed_disks[temp_entry_type4_1['physical_disk_id']].dp.dp.seek((temp_entry_type4_1[
                                                                                                      'physical_disk_block_number'] + 2) * 0x10000000 + partition_start_offset_1)  # SPACEDB 시작 offset을 더해줘야함
                            self.parsed_disks[temp_entry_type4_2['physical_disk_id']].dp.dp.seek((temp_entry_type4_2[
                                                                                                      'physical_disk_block_number'] + 2) * 0x10000000 + partition_start_offset_2)  # SPACEDB 시작 offset을 더해줘야함
                            self.parsed_disks[temp_entry_type4_3['physical_disk_id']].dp.dp.seek((temp_entry_type4_3[
                                                                                                      'physical_disk_block_number'] + 2) * 0x10000000 + partition_start_offset_3)  # SPACEDB 시작 offset을 더해줘야함
                            self.parsed_disks[temp_entry_type4_4['physical_disk_id']].dp.dp.seek((temp_entry_type4_4[
                                                                                                      'physical_disk_block_number'] + 2) * 0x10000000 + partition_start_offset_4)  # SPACEDB 시작 offset을 더해줘야함
                            self.parsed_disks[temp_entry_type4_5['physical_disk_id']].dp.dp.seek((temp_entry_type4_5[
                                                                                                      'physical_disk_block_number'] + 2) * 0x10000000 + partition_start_offset_5)  # SPACEDB 시작 offset을 더해줘야함

                            for j in range(0, 0x1000):
                                if j % 3 == 0:
                                    disk.dp.write(self.parsed_disks[temp_entry_type4_0['physical_disk_id']].dp.dp.read(0x40000))
                                    disk.dp.write(self.parsed_disks[temp_entry_type4_1['physical_disk_id']].dp.dp.read(0x40000))
                                    disk.dp.write(self.parsed_disks[temp_entry_type4_2['physical_disk_id']].dp.dp.read(0x40000))
                                    disk.dp.write(self.parsed_disks[temp_entry_type4_3['physical_disk_id']].dp.dp.read(0x40000))
                                    self.parsed_disks[temp_entry_type4_4['physical_disk_id']].dp.dp.seek(0x40000, os.SEEK_CUR)
                                    self.parsed_disks[temp_entry_type4_5['physical_disk_id']].dp.dp.seek(0x40000, os.SEEK_CUR)
                                if j % 3 == 1:
                                    disk.dp.write(self.parsed_disks[temp_entry_type4_4['physical_disk_id']].dp.dp.read(0x40000))
                                    disk.dp.write(self.parsed_disks[temp_entry_type4_5['physical_disk_id']].dp.dp.read(0x40000))
                                    disk.dp.write(self.parsed_disks[temp_entry_type4_0['physical_disk_id']].dp.dp.read(0x40000))
                                    disk.dp.write(self.parsed_disks[temp_entry_type4_1['physical_disk_id']].dp.dp.read(0x40000))
                                    self.parsed_disks[temp_entry_type4_2['physical_disk_id']].dp.dp.seek(0x40000, os.SEEK_CUR)
                                    self.parsed_disks[temp_entry_type4_3['physical_disk_id']].dp.dp.seek(0x40000, os.SEEK_CUR)
                                if j % 3 == 2:
                                    disk.dp.write(self.parsed_disks[temp_entry_type4_2['physical_disk_id']].dp.dp.read(0x40000))
                                    disk.dp.write(self.parsed_disks[temp_entry_type4_3['physical_disk_id']].dp.dp.read(0x40000))
                                    disk.dp.write(self.parsed_disks[temp_entry_type4_4['physical_disk_id']].dp.dp.read(0x40000))
                                    disk.dp.write(self.parsed_disks[temp_entry_type4_5['physical_disk_id']].dp.dp.read(0x40000))
                                    self.parsed_disks[temp_entry_type4_0['physical_disk_id']].dp.dp.seek(0x40000, os.SEEK_CUR)
                                    self.parsed_disks[temp_entry_type4_1['physical_disk_id']].dp.dp.seek(0x40000, os.SEEK_CUR)
                disk.dp.close()

        print("[*] Reconstruction Success.")
