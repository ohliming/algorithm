#!/usr/bin/env python
#coding=utf8
'''
@author: cuiyan
'''
import sys,urllib

class LogInfo:
    attrs = ['timestamp', 'kr_uid', 'kr_plus_uid', 'cookie_uid', 'access_info']
    def __init__(self):
        for attr in self.attrs:
            setattr(self, attr, '')
    def parse_line(self, line):
        line = line.strip()
        if len(line) == 0 or line.find('hm.gif') == -1:
            return False
        pos_begin = 0
        pos_end = 0
        seg_anchor = -1
        while True:
            seg = ''
            if line[pos_begin] == '"':
                pos_end = line.find('" ', pos_begin + 1)
                if pos_end != -1:
                    seg = line[pos_begin:pos_end + 1]
                    pos_begin = pos_end + 2
                else:
                    #raise Exception('log format invalid: %s' % line)
                    return False
            elif line[pos_begin] == '[':
                pos_end = line.find('] ', pos_begin + 1)
                if pos_end != -1:
                    seg = line[pos_begin:pos_end + 1]
                    pos_begin = pos_end + 2
                else:
                    #raise Exception('log format invalid: %s' % line)
                    return False
            else:
                pos_end = line.find(' ', pos_begin)
                if pos_end == -1:
                    pos_end = len(line)
                seg = line[pos_begin:pos_end]
                pos_begin = pos_end + 1
            if seg.startswith('['):
                self.timestamp = seg.strip('[]')
                seg_anchor = 0
            elif seg.startswith('"GET'):
                pos1 = seg.find('?')
                pos2 =seg.find(' ', pos1)
                if pos1 == -1 or pos2 == -1:
                    #raise Exception('log format invalid: %s' % line)
                    return False
                command = seg[pos1 + 1:pos2]
                self.access_info = urllib.unquote(seg[pos1 + 1:pos2])
            else:
                seg_anchor += 1
                if seg_anchor == 1:
                    self.kr_uid = seg
                elif seg_anchor == 2:
                    self.kr_plus_uid = seg
                elif seg_anchor == 5:
                    self.referer = seg.strip('"')
            if pos_begin >= len(line):
                self.cookie_uid = seg
                break
        return True

if __name__ == '__main__':
    file = open(sys.argv[1])
    for line in file:
        line = line.strip()
        if len(line) == 0: continue
        log_info = LogInfo()
        if log_info.parse_line(line):
            for attr in LogInfo.attrs:
                print '%s\t' % (getattr(log_info, attr)),
            print ''

