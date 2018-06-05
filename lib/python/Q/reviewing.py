import os
import re
import json

from .settings import QSettings
from .error import QError
from .helper import Curl, Git, Edit, Requests


class ReviewMixin:
    """
    Base class for review implementations.
    """

    def review_start(self, ticket, file):
        """
        Resolve review ID for the ticket and launch it.
        """
        raise QError("Not implemented in %s: review_start().", self.__class__.__name__)

    def review_update(self, ticket, file):
        """
        Update the existing review.
        """
        raise QError("Not implemented in %s: review_update().", self.__class__.__name__)

    def review_url(self, review_id):
        """
        Get the URL for the given review.
        """
        raise QError("Not implemented in %s: review_url().", self.__class__.__name__)

    def review_status(self, review_id):
        """
        Fetch the review status 'Pending', 'Success', 'Fail' or percentage.
        """
        raise QError("Not implemented in %s: review_status().", self.__class__.__name__)

    def review_update_build(self, ticket):
        """
        Update build information on review.
        """
        raise QError("Not implemented in %s: review_update_build().", self.__class__.__name__)

    def get_review_title(self, ticket):
        """
        Calculate review title for a ticket.
        """
        title = QSettings.REVIEW_TITLE
        title = title.replace('%c', str(ticket.code))
        title = title.replace('%t', ticket['Title'])
        return title

    def edit_review_comments(self, ticket):
        path = os.path.join(ticket.path(), "review_text.txt")
        Edit()(path, light=True)
        return file(path, 'r').read()

class NoReview(ReviewMixin):
    """
    Automatically successful review.
    """
    def review_start(self, ticket, file):
        return 'AutoSuccess'

    def review_status(self, review_id):
        return 'Success'

    def review_url(self, review_id):
        return None

    def review_update_build(self, ticket):
        return


class ReviewByReviewBoard(ReviewMixin):
    """
    Implementation for Review Board by Beanbag Inc.

    https://www.reviewboard.org/docs/manual/2.0/webapi/2.0/
    """

    def _review_api(self, url, post=None, put=None, quiet=False, upload=None):
        """
        Call the review board API and return JSON response.
        """
        from q import Q
        base = QSettings.REVIEW_SERVER
        if base[-1] == '/':
            base = base[0:-1]
        if url == '' or url[0] != '/':
            url = '/' + url
        content = Curl()(base +  "/api" + url, post=post, put=put, quiet=quiet, upload=upload, user=QSettings.REVIEW_USER, password=QSettings.REVIEW_PASS)
        try:
            ret = json.loads(content)
        except ValueError, e:
            raise QError("Review API call failed: %r.", e.message)
        if ret['stat'] != 'ok':
            raise QError("Review API call failed with result %r.", ret)
        return ret

    def _review_repository_id(self, name):
        """
        Look for repository id by its name.
        """
        if not name:
            return None
        for repo in self._review_api('/repositories/')['repositories']:
            if repo['name'].lower() == name.lower():
                return repo['id']
        raise QError('No such review repository as %r.', name)

    def _create_review_draft(self, repo_id):
        """
        Initialize new draft review.
        """
        ret = self._review_api('/review-requests/', post = {'repository' : repo_id})
        return ret['review_request']['id']

    def _update_review_draft(self, id, attrs):
        """
        Set initial attributes for review request draft.
        """
        self._review_api('/review-requests/' + str(id) + '/draft/', put=attrs)

    def _upload_initial_review_diff(self, id, path):
        """
        Upload initial diff.
        """
        self._review_api('/review-requests/' + str(id) + '/draft/diffs/', upload={'path' : path})

    def _review_testing_section(self, ticket):
        """
        Generate review 'Testing Done' section.
        """
        testing = QSettings.REVIEW_ADDITIONAL_DESCRIPTION
        build_url = ''
        if ticket['Build ID']:
            build_url = self.build_url(ticket)
        testing = testing.replace('%b', build_url)
        return testing

    def review_start(self, ticket, file):
        """
        Create new review draft.
        """
        if not QSettings.REVIEW_GROUPS:
            raise QError("No groups defined for reviewing. Please set REVIEW_GROUPS.")

        repo_id = self._review_repository_id(QSettings.REVIEW_REPOSITORY);

        id = self._create_review_draft(repo_id)

        title = self.get_review_title(ticket)
        description = QSettings.REVIEW_DESCRIPTION
        description = description.replace('%u', ticket.url())
        testing = QSettings.REVIEW_ADDITIONAL_DESCRIPTION
        build_url = ''
        if ticket['Build ID']:
            build_url = self.build_url(ticket)
        testing = testing.replace('%b', build_url)
        # TODO: ReviewBoard: sThis seems to leave \_ in testing URL.
        self._update_review_draft(id, {'branch': ticket['Branch'],
                                       'summary': title,
                                       'description': description,
                                       'text_type': 'plain',
                                       'testing_done' : testing,
                                       'target_groups': QSettings.REVIEW_GROUPS})

        self._upload_initial_review_diff(id, file)

        # Do not publish yet and let user to improve it manually first.
        # self._update_review_draft(id, {'public': True})
        return id

    def review_url(self, review_id):
        """
        Get the URL for the given review.
        """
        if review_id:
            return (QSettings.REVIEW_SERVER +  "/r/%s/") % review_id

    def review_status(self, review_id):
        """
        Fetch the review status 'Pending', 'Success', 'Fail' or percentage.
        """
        ret = self._review_api('/review-requests/' + str(review_id) +'/')
        ship_its = int(ret['review_request']['ship_it_count'])
        if ship_its >= int(QSettings.REVIEW_SHIPITS):
            return 'Success'
        return "%d%%" % (ship_its * 100 / int(QSettings.REVIEW_SHIPITS))

    def review_update_build(self, ticket):
        """
        Update 'Testing Done' section with new build.
        """
        testing = self._review_testing_section(ticket)
        self._update_review_draft(ticket['Review ID'], {'testing_done' : testing,
                                                        'text_type': 'plain',
                                                        'public': True})


class ReviewByGerrit(ReviewMixin):
    """
    Construct a change for Gerrit using working branch.
    """

    def _make_squashed_commit(self, ticket):
        base = QSettings.BASE_BRANCH
        if ticket['Base']:
            sq = 'squash/' + ticket['Base']
            if Git().branch_exists(sq):
                base = sq
        branch = ticket.branch_name()
        review_branch = 'squash/' + ticket.branch_name()
        if Git().branch_exists(review_branch):
            Git()('branch -D ' + review_branch)
        Git()('checkout -b ' + review_branch + ' ' + base)
        out = Git()('merge --squash ' + branch, stderr=True, get_output=True)
        if out.find('CONFLICT') >= 0:
            raise QError('Merge conflict.')

    def review_start(self, ticket, file):
        from q import Q
        self._make_squashed_commit(ticket)
        branch = ticket.branch_name()
        title = self.get_review_title(ticket)
        title = title.replace('"', '\\"')

        Git()('commit', '-a', '-m "' + title + '"', '-e')

        # Find the Change-Id and store it as extra info.
        out = Git()('log -1', get_output=True)
        change_id = None
        for line in out.split("\n"):
            line = line.strip()
            match = re.match('^Change-Id: (.+)', line)
            if match:
                change_id = match.group(1)
                break
        if change_id is None:
            Git()('checkout ' + branch)
            raise QError('Cannot find Change-Id from git log: %r', out)

        out = Git()('push gerrit HEAD:refs/for/master', '--no-thin', stderr=True, get_output=True)

        # Find the ID of the review by scanning URL from output.
        revid = None
        out = out.replace("\r", "!").replace("\n", "!")
        match = re.match('remote:.+?(https?:.+?\/)(\d+)', out)
        if match:
            revid = int(match.group(2))
        else:
            Git()('checkout ' + branch)
            raise QError('Cannot find review URL and ID from Gerrit push: %r', out)

        Git()('checkout ' + branch)

        ticket['Review Info'] = change_id
        return revid

    def review_update(self, ticket, file):
        from q import Q
        self._make_squashed_commit(ticket)
        branch = ticket.branch_name()
        title = self.get_review_title(ticket)
        title = title.replace('"', '\\"')

        Git()('commit', '-a', '-m "' + title + '\n\nChange-Id: ' + ticket['Review Info'] + '"', '-e')
        Git()('push gerrit HEAD:refs/for/master', '--no-thin')
        Git()('checkout ' + branch)

    def review_status(self, review_id):
        # TODO: Gerrit: Implement review_status().
        return 'Pending'

    def review_url(self, review_id):
        """
        Get the URL for the given review.
        """
        if review_id:
            return (QSettings.REVIEW_SERVER +  "/#/c/%s/") % str(review_id)

class ReviewByVSTS(ReviewMixin):
    """
    Review creator for VSTS.

    https://www.visualstudio.com/en-us/integrate/api/overview
    """

    def _find_vsts_git_repository(self):
        """Scan repositories and find the ID of this repository."""
        repo_name = None
        for line in Git()('remote -v', get_output=True).split("\n"):
            parts = re.split('\s', line)
            if len(parts) >= 3:
                repo_name = parts[1].split('/')[-1]
                break
        for repo in self._vsts_query('git/repositories').get('value', []):
            if repo['name'] == repo_name:
                return repo['id']
        raise QError("Cannot find Git repository named %r", repo_name)

    def review_start(self, ticket, file):

        if not self._vsts_query:
            raise QError("When using ReviewByVSTS, also TicketingByVSTS must be in user.")

# TODO: VSTS: Enable once this is working
#
#        repo_id = self._find_vsts_git_repository()
#        text = self.edit_review_comments(ticket)
#        params = {
#            'sourceRefName': 'refs/heads/' + ticket['Branch'],
#            'targetRefName': 'refs/heads/master',
#            'title': self.get_review_title(ticket),
#            'description': text,
#            'reviewers': []
#        }
#        print params
#        data = self._vsts_query('git/repositories/' + repo_id + '/pullrequests', post=params)
#        print data

        data = self._vsts_query('wit/workitems/'  + ticket.code)
        if 'Microsoft.VSTS.Scheduling.RemainingWork' in data['fields']:
            patch = [{'op': 'replace', 'path': '/fields/Microsoft.VSTS.Scheduling.RemainingWork', 'value': 0.0}]
            self._vsts_query('wit/workitems/' + ticket.code, patch=patch)

        from q import Q
        Q.wr('Review', 'Finish review manually:')
        Q.wr('Review', 'https://phones.visualstudio.com/DefaultCollection/PhonesSW/SWCustomizationVT/_git/Z_Neo_Service/pullrequests')
        return '1'

    def review_status(self, review_id):
        # TODO: VSTS: Implement review_status().
        return 'Pending'

    def review_url(self, review_id):
        if review_id:
            return QSettings.REVIEW_URL.replace('%c', str(review_id))

    def review_update_build(self, ticket):
        # TODO: VSTS: Implement review_update_build().
        return

    def review_update(self, ticket, file):
        """
        Update the existing review. Push made earlier before calling this is enough to update.
        """
        pass


class ReviewByBitbucket(ReviewMixin):
    """
    Create pull request to bitbucket.
    """

    def review_start(self, ticket, file):
        self._review_check()
        repo = "%s/%s" % (QSettings.BITBUCKET_PROJECT, QSettings.BITBUCKET_REPO)
        url = 'https://bitbucket.org/api/2.0/repositories/%s/pullrequests/' % repo
        out = {
            "title": self.get_review_title(ticket),
            "description": "",
            "source": {
                "branch": {
                    "repository": repo,
                    "name": ticket['Branch']
                }
            },
            "destination": {
                "branch": {
                    "name": QSettings.BITBUCKET_PR_TARGET
                }
            },
            "close_source_branch": False
        }
        resp = Requests()(url, post=out, auth=self._review_auth())
        data = resp.json()
        diff = data['links']['diff']['href']
        return int(re.match('.*/pullrequests/(.*)/diff', diff).groups()[0])

    def _review_auth(self):
        if not QSettings.BITBUCKET_USER:
            raise QError("User for Bamboo BITBUCKET_USER is not set.")
        if not QSettings.BITBUCKET_PASSWORD:
            raise QError("Password for Bamboo BITBUCKET_PASSWORD is not set.")
        return (QSettings.BITBUCKET_USER, QSettings.BITBUCKET_PASSWORD)

    def _review_check(self):
        """
        Check that all necessary settings are set.
        """
        if not QSettings.BITBUCKET_PROJECT:
            raise QError("Project name BITBUCKET_PROJECT is not set.")
        if not QSettings.BITBUCKET_REPO:
            raise QError("Repository name BITBUCKET_REPO is not set.")
        if not QSettings.BITBUCKET_PR_TARGET:
            raise QError("Bitbucket pull request target BITBUCKET_PR_TARGET is not set.")

    def review_url(self, review_id):
        repo = "%s/%s" % (QSettings.BITBUCKET_PROJECT, QSettings.BITBUCKET_REPO)
        return 'https://bitbucket.org/%s/pull-requests/%s' % (repo, review_id)

    def review_status(self, review_id):
        repo = "%s/%s" % (QSettings.BITBUCKET_PROJECT, QSettings.BITBUCKET_REPO)
        url = 'https://bitbucket.org/api/2.0/repositories/%s/pullrequests/%s' % (repo, review_id)
        resp = Requests()(url, auth=self._review_auth())
        if not resp:
            return None
        data = resp.json()
        state = data['state']
        if state == 'OPEN':
            ok = 0
            total = 0
            for person in data['participants']:
                if person['role'] == 'REVIEWER':
                    total += 1
                    if person['approved']:
                        ok += 1
                elif person['role'] == 'PARTICIPANT':
                    pass
                else:
                    raise QError('Unknown review role: %r.' % person['role'])
            if total:
                if ok == total:
                    return 'Success'
                return str(ok) + '/' + str(total)
            return 'Pending'
        elif state == 'DECLINED':
            return 'Fail'
        elif state == 'MERGED':
            return 'Success'
        else:
            raise QError('Unknown status of review: %r.' % state)

    def review_update(self, ticket, file):
        # Git push is enough.
        pass

    def review_update_build(self, ticket):
        # No need to update.
        return
