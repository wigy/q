import xmlrpclib
import json
import urllib
import re
import requests

from settings import QSettings
from error import QError
from ticket import Ticket
from helper import Curl
from conversions import html2markdown


class TicketingMixin:
    """
    Base class for review implementations.
    """

    def _get_user_and_password(self):
        """
        Get ticketing credentials and raise error if not defined.
        """
        user = QSettings.TICKETING_USER
        if not user:
            raise QError("Must set TICKETING_USER in .q.")
        password = QSettings.TICKETING_PASS
        if not password:
            raise QError("Must set TICKETING_PASS in .q.")
        return user, password

    def ticket_url(self, ticket):
        """
        Get the URL to view the ticket.
        """
        raise QError("Not implemented in %s: ticket_url().", self.__class__.__name__)

    def data2ticket(self, cmd, data):
        """
        Convert raw data coming from the remote server to the ticket content.
        """
        raise QError("Not implemented in %s: data2ticket().", self.__class__.__name__)

    def can_create_ticket(self):
        """
        Check if the ticketing system can create tickets.
        """
        return True

    def create_ticket(self, ticket):
        """
        Create a ticket on the ticketing system from the ticket instance.

        @return New ticket code.
        """
        raise QError("Not implemented in %s: create_ticket().", self.__class__.__name__)

    def fetch_ticket(self, cmd, code):
        """
        Get the ticket data as an instance of Ticket class.
        """
        raise QError("Not implemented in %s: fetch_ticket().", self.__class__.__name__)

    def start_work_on_ticket(self, ticket):
        """
        Claim the ownership of the ticket and mark it that work has been started.
        """
        raise QError("Not implemented in %s: start_work_on_ticket().", self.__class__.__name__)


    def done_work_on_ticket(self, ticket):
        """
        Indicate that ticket flow is now complete from the development point of view.
        """
        raise QError("Not implemented in %s: done_work_on_ticket().", self.__class__.__name__)

    def start_review_on_ticket(self, ticket):
        """
        Indicate that ticket is waiting for review.
        """
        raise QError("Not implemented in %s: start_review_on_ticket().", self.__class__.__name__)

    def change_text_of_ticket(self, ticket):
        """
        Change the text of ticket.
        """
        raise QError("Not implemented in %s: change_text_of_ticket().", self.__class__.__name__)


class TicketingByTrac(TicketingMixin):
    """
    Ticketing implementation for Trac.
    """

    def proxy(self):
        user, password = self._get_user_and_password()
        url = QSettings.TICKETING_TRAC_API
        if not url:
            raise QError("Must set TICKETING_TRAC_API in .q when using TicketingByTrac mixin.")
        parts = url.split('://')
        url = parts[0] + '://' + user + ':' + password + '@' + parts[1] + '/login/rpc'
        return xmlrpclib.ServerProxy(url)

    def _get_ticket(self, code):
        """
        Fetch the ticket data for code.
        """
        proxy = self.proxy()
        try:
            ret = proxy.ticket.get(code)
        except xmlrpclib.Fault:
            raise QError("Cannot find ticket '" + code + "'.")
        return ret

    def _set_ticket(self, code, comment, **attributes):
        """
        Fetch the ticket data for code.
        """
        from q import Q
        Q.wr('Ticketing', "Updating remote ticket %r:" % code)
        for k in attributes:
            parts = unicode(attributes[k]).split("\n")
            if len(parts) == 1:
                v = parts[0]
            else:
                v = "\\n ".join(parts)
            Q.wr('Ticketing', "  %s = %s" % (k, v))
        proxy = self.proxy()
        try:
            proxy.ticket.update(code, comment, attributes)
        except xmlrpclib.Fault:
            raise QError("Cannot find ticket '" + code + "'.")

    def ticket_url(self, ticket):
        return QSettings.TICKETING_TRAC_API + "/ticket/" + str(ticket.code)

    def data2ticket(self, cmd, data):
        code = str(data[0])
        ret = Ticket(cmd, code)
        ret['Owner'] = data[3]['owner']
        ret['Title'] = data[3]['summary'].strip()
        ret['Notes'] = data[3]['description'].strip()
        status = data[3]['status']
        substatus = data[3]['substatus']
        if status == 'implementing' and substatus == '-':
            ret.set_status("Started")
        elif status == 'new':
            ret.set_status("New")
        else:
            raise QError("Don't know how to convert Track status (%r, %r) to ticket." % (status, substatus))
        return ret

    def fetch_ticket(self, cmd, code):
        return self.data2ticket(cmd, self._get_ticket(code))

    def start_work_on_ticket(self, ticket):
        self._set_ticket(int(ticket.code), '',
                  owner=QSettings.TICKETING_USER,
                  status='implementing',
                  substatus='-',
                  branch=ticket['Branch'],
                  milestone=QSettings.TRAC_WORKING_MILESTONE)

    def done_work_on_ticket(self, ticket):
        self._set_ticket(int(ticket.code), '',
                  substatus='deploy me!')

    def create_ticket(self, ticket):
        from q import Q
        proxy = self.proxy()
        id = proxy.ticket.create(ticket['Title'], ticket['Notes'], {
            'status': '-',
            'substatus': '-',
            'milestone': QSettings.TRAC_INITIAL_MILESTONE})
        if not id:
            raise QError("Failed to create new ticket.")
        Q.wr('Ticketing', "New ticket %r created in the remote." % id)
        return str(id)

    def start_review_on_ticket(self, ticket, url):
        self._set_ticket(int(ticket.code), url, substatus='review me!')

    def change_text_of_ticket(self, ticket):
        self._set_ticket(int(ticket.code), '', description=ticket['Notes'])


class ManualTicketing(TicketingMixin):
    """
    Ticketing implementation for Trac.
    """

    def can_create_ticket(self):
        return False

    def fetch_ticket(self, cmd, code):
        cmd.wr("Creating a copy of the ticket manually.")
        cmd.wr("Please copy paste the title of the ticket:")
        title = raw_input()
        ret = Ticket(cmd, code)
        ret['Title'] = title.strip()
        ret.set_status("Started")
        return ret

    def start_work_on_ticket(self, ticket):
        pass

    def done_work_on_ticket(self, ticket):
        pass

    def start_review_on_ticket(self, ticket, url):
        pass

    def change_text_of_ticket(self, ticket):
        pass

    def ticket_url(self, ticket):
        url = QSettings.TICKET_URL
        if url:
            url = url.replace('%c', str(ticket.code))
            return url
        return None


class TicketingByVSTS(TicketingMixin):
    """
    Ticketing implementation for Visual Studio Team Services.

    https://www.visualstudio.com/en-us/integrate/api/overview
    """

    def can_create_ticket(self):
        return False

    def _vsts_query(self, *api, **params):
        """
        Execute query and return the result.
        """
        content_type = None
        user, password = self._get_user_and_password()
        instance = QSettings.VSTS_INSTANCE
        if not instance:
            raise QError("Must set VSTS_INSTANCE in .q.")

        if 'patch' in params:
            patch = json.dumps(params['patch'])
            params = {}
            content_type = 'application/json-patch+json'
        else:
            patch = None

        if 'post' in params:
            post = params['post']
            params = {}
            content_type = 'application/json'
        else:
            post = None

        if re.match('https?://', api[0]):
            url = api[0]
        else:
            url = 'https://%s.visualstudio.com/DefaultCollection/_apis/%s' % (instance, '/'.join(api))
            params['api-version'] = '2.0'
            if url.find('?') > 0:
                url += '&'
            else:
                url += '?'
            url += urllib.urlencode(params)

        data = Curl()(url, user=user, password=password, post=post, patch=patch, content_type=content_type)
        if not data:
            raise QError("_vsts_query() failed.")
        data = json.loads(data)
        if 'message' in data:
            raise QError('VSTS: ' + data['message'])
        return data

    def data2ticket(self, cmd, data):
        code = str(data['id'])
        ret = Ticket(cmd, code)
        ret['Ticket Info'] = data['fields'].get('System.WorkItemType')
        ret['Title'] = data['fields'].get('System.Title', '')
        if ret['Ticket Info'] == 'Bug':
            notes = data['fields'].get('Microsoft.VSTS.TCM.ReproSteps', '')
        else:
            notes = data['fields'].get('System.Description', '')
        ret['Notes'] = html2markdown(notes)
        return ret

    def fetch_ticket(self, cmd, code):
        return self.data2ticket(cmd, self._vsts_query('wit/workitems/' + code))

    def start_work_on_ticket(self, ticket):
        old = self._vsts_query('wit/workitems/' + ticket.code)
        if old.get('System.AssignedTo', None) is None:
            op = 'add'
        else:
            op = 'replace'

        if ticket['Ticket Info'] in ['Bug', 'Product Backlog Item']:
            state = 'Committed'
        else:
            state = 'In Progress'
        patch = [{'op': 'replace', 'path': '/fields/System.State', 'value': state},
                 {'op': op, 'path': '/fields/System.AssignedTo', 'value': QSettings.VSTS_FULL_NAME}]
        self._vsts_query('wit/workitems/' + ticket.code, patch=patch)

    def done_work_on_ticket(self, ticket):
        patch = [{'op': 'replace', 'path': '/fields/System.State', 'value': 'Done'}]
        self._vsts_query('wit/workitems/' + ticket.code, patch=patch)
        close_parent = True
        if ticket['Ticket Info'] not in ['Task']:
            close_parent = False
        else:
            # TODO: refactor to parent() and children() functions once sure this works like this
            data = self._vsts_query('wit/workitems/' + ticket.code + '?$expand=all')
            for link in data.get('relations'):
                rel = link['rel']
                if rel in ['System.LinkTypes.Hierarchy-Reverse']:
                    parent = self._vsts_query(link['url'] + '?$expand=all')
                    parent_id = parent['id']
                    if parent['fields']['System.WorkItemType'] in ['Bug', 'Product Backlog Item']:
                        for child_link in parent.get('relations'):
                            if child_link['rel'] in ['System.LinkTypes.Hierarchy-Forward']:
                                # TODO: Here we could skip the task we are closing
                                if self._vsts_query(child_link['url'])['fields']['System.State'] not in ['Done']:
                                    close_parent = False
                                    break
        if close_parent:
            patch = [{'op': 'replace', 'path': '/fields/System.State', 'value': 'Done'}]
            self._vsts_query('wit/workitems/' + str(parent_id), patch=patch)

    def start_review_on_ticket(self, ticket, url):
        pass

    def change_text_of_ticket(self, ticket):
        # TODO: Should check existing value and use 'add' as 'op' if None.
        if ticket['Ticket Info'] == 'Bug':
            patch = [{'op': 'replace', 'path': '/fields/Microsoft.VSTS.TCM.ReproSteps', 'value': ticket['Notes'].replace("\n", "<br>")}]
        else:
            patch = [{'op': 'replace', 'path': '/fields/System.Description', 'value': ticket['Notes'].replace("\n", "<br>")}]
        self._vsts_query('wit/workitems/' + ticket.code, patch=patch)

    def ticket_url(self, ticket):
        url = QSettings.TICKET_URL
        if url:
            url = url.replace('%c', str(ticket.code))
            return url
        return None


class TicketingByAtlassian(TicketingMixin):

    def fetch_ticket(self, cmd, code):
        data = self._get_ticket(code)
        ret = Ticket(cmd, code)
        ret['Owner'] = data['fields']['creator']['name']
        ret['Title'] = data['fields']['summary']
        ret['Notes'] = data['fields']['description']
        return ret

    def start_work_on_ticket(self, ticket):
        """
        Assign ticket to myself and look for transition to 'In Progress' and do it if found.
        """
        data = {"name": QSettings.TICKETING_USER.split('@')[0]}
        resp = requests.put(QSettings.ATLASSIAN_URL + '/rest/api/2/issue/' + ticket.code + '/assignee', json=data, auth=self._auth())
        if (resp.status_code != 204):
            raise QError("Claiming ownership of the ticket failed.")
        resp = requests.get(QSettings.ATLASSIAN_URL + '/rest/api/2/issue/' + ticket.code + '/transitions', auth=self._auth())
        data = resp.json()
        for tr in data['transitions']:
            if tr['name'] == 'In Progress':
                data = {"transition": {"id": tr['id']}}
                resp = requests.post(QSettings.ATLASSIAN_URL + '/rest/api/2/issue/' + ticket.code + '/transitions', json=data, auth=self._auth())
                if (resp.status_code != 204):
                    raise QError("Setting ticket 'In Progress' state failed.")
                return
        raise QError("Cannot find transition called 'In Progress'.")

    def _check(self):
        """
        Check that all necessary settings are set.
        """
        if not QSettings.ATLASSIAN_URL:
            raise QError("Base URL for Atlassian ATLASSIAN_URL is not set.")
        if not QSettings.TICKETING_USER:
            raise QError("User for Atlassian TICKETING_USER is not set.")
        if not QSettings.TICKETING_PASSWORD:
            raise QError("Password for Atlassian TICKETING_PASSWORD is not set.")

    def _auth(self):
        """
        Authentication parameter.
        """
        return (QSettings.TICKETING_USER, QSettings.TICKETING_PASSWORD)

    def _get_ticket(self, code):
        """
        Fetch the ticket data for the given ticket code.
        """
        self._check()
        auth = (QSettings.TICKETING_USER, QSettings.TICKETING_PASSWORD)
        resp = requests.get(QSettings.ATLASSIAN_URL + '/rest/api/2/issue/' + code, auth=self._auth())
        return resp.json()
