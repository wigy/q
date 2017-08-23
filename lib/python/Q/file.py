import sys
import inspect
import re
import os
import random
import readline
import glob
import time
import shutil

from error import QError


class QFile:
    """
    Simple file format for saving ticket information and settings as key value pairs.
    """

    def __init__(self, path = None):
        self.path = path

    def read(self):
        """
        Load raw data as a string from the current path.
        """
        if not self.path:
            raise QError("Path not set for loading a file.")
        f = open(self.path,'r')
        data = f.read()
        f.close()
        return data

    def write(self, raw_data):
        """
        Write raw data string to the current path.
        """
        if not self.path:
            raise QError("Path not set for saving a file.")
        f = open(self.path,'w')
        f.write(raw_data)
        f.close()

    def load(self):
        """
        Load data from the current path and return as a dictionary.
        """
        ret = {}
        data = self.read().decode('utf-8')
        str = None
        k = None
        for line in data.split("\n"):
            if len(line)==0:
                continue
            if line[0]!=' ':
                if k != None:
                    ret[k] = str.strip()
                k = line[0:-1]
                str = ""
            else:
                str+=line[2:].rstrip()
                str+="\n"
            if k != None:
                ret[k] = str.strip()
        return ret

    def save(self, values, order=None):
        """
        Write a file from key value pair dictionary with optional key order.
        """
        key_list = order
        if not key_list:
            key_list = sorted(values.keys())
        out = ""
        for k in key_list:
            if not k in values:
                continue
            out += k + ":\n"
            lines = values[k].split("\n")
            for line in lines:
                out += "  " + line + "\n"
        self.write(out.encode('utf-8'))

    def drop(self):
        """
        Remove file.
        """
        os.unlink(self.path)
        self.path = None
