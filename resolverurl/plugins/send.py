import re
from urllib.parse import *
from resolverurl.lib import helpers
from resolverurl import common
from resolverurl.resolver import ResolveUrl, ResolverError


class SendResolver(ResolveUrl):
    name = 'Send'
    domains = ['send.cm', 'sendit.cloud']
    pattern = r'(?://|\.)(send(?:it)?\.(?:cm|cloud))/(?:f/embed/)?((?:d/)?[0-9a-zA-Z]+)'

    def __init__(self):
        print("SendResolver loaded")

    def get_media_url(self, host, media_id):
        web_url = self.get_url(host, media_id)
        headers = {'User-Agent': common.FF_USER_AGENT}
        html = self.net.http_GET(web_url, headers=headers).content
        if "The file you were looking for doesn't exist." not in html:
            data = helpers.get_hidden(html)
            burl = 'https://{}'.format(host)
            url = helpers.get_redirect_url(burl, headers=headers, form_data=data)
            if url != burl:
                headers.update({'Referer': web_url})
                return quote(url, '/:') + helpers.append_headers(headers)
            else:
                raise ResolverError('Unable to locate File')
        else:
            raise ResolverError('File deleted')
        return

    def get_url(self, host, media_id):
        return self._default_get_url(host, media_id, template='https://send.cm/{media_id}')
    
    def get_host_and_id(self, url):
        """
        The method that converts a host and media_id into a valid url

        Args:
            url (str): a valid url on the host this resolver resolves

        Returns:
            host (str): the host the link is on
            media_id (str): the media_id the can be returned by get_host_and_id
        """
        r = re.search(self.pattern, url, re.I)
        if r:
            return r.groups()
        else:
            return False
