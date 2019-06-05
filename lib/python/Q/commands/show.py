# -*- coding: UTF-8 -*-
import os
import glob

from ..error import QError
from ..command import AutoLoadCommand


class CommandShow(AutoLoadCommand):

    """
    Display a ticket data.
    """
    def run(self):
        """
        usage: q [show] <code>
               <code> - A ticket number.
        """
        from ..q import Q
        if not self.ticket.code:
            self.wr('No ticket')
            return
        self.wr("Path: "+Q.URL+self.ticket.path('README')+Q.END)
        file = self.ticket.path('latest.diff')
        if os.path.isfile(file):
            self.wr("Changes: "+Q.URL + file + Q.END)
        url = self.app.ticket_url(self.ticket)
        if url:
            self.wr("URL: "+Q.URL+url+Q.END)
        if self.ticket['Build ID']:
            burl = self.app.build_url(self.ticket)
            if burl:
                self.wr("Build URL: " + Q.URL + burl + Q.END)
        if self.ticket['Review ID']:
            rurl = self.app.review_url(self.ticket['Review ID'])
            if rurl:
                self.wr("Review URL: " + Q.URL + rurl + Q.END)
        files = []
        std_files = ['notes.txt', 'README', 'latest.diff', 'private.diff', 'review_text.txt']
        for f in glob.glob(self.ticket.path('*')):
            basename = os.path.split(f)[-1]
            if basename[0:7]=='review-' and basename[-5:]=='.diff':
                continue
            if f[-1] != '~' and f[-4:] != '.sql' and basename not in std_files:
                files.append(f)
        if files:
            self.wr('Additional Files:')
            for f in files:
                self.wr('  '+f)
        for k in self.ticket.keys():
            self.wr(Q.TITLE+k+':'+Q.END)
            self.wr(self.ticket[k])
