import base64
import re
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, Request, build_opener
import six
from resolverurl import common
from urllib.parse import *

from resolverurl.lib import jsunpack


def get_media_url(
        url, result_blacklist=None, subs=False,
        patterns=None, generic_patterns=True,
        subs_patterns=None, generic_subs_patterns=True,
        referer=True, redirect=True,
        ssl_verify=True, verifypeer=True):
    if patterns is None:
        patterns = []
    if subs_patterns is None:
        subs_patterns = []
    scheme = urlparse(url).scheme
    if result_blacklist is None:
        result_blacklist = []
    elif isinstance(result_blacklist, str):
        result_blacklist = [result_blacklist]

    result_blacklist = list(set(result_blacklist + ['.smil']))  # smil(not playable) contains potential sources, only blacklist when called from here
    net = common.Net(ssl_verify=ssl_verify)
    headers = {'User-Agent': common.RAND_UA}
    rurl = urljoin(url, '/')
    if isinstance(referer, six.string_types):
        headers.update({'Referer': referer})
    elif referer:
        headers.update({'Referer': rurl})
    response = net.http_GET(url, headers=headers, redirect=redirect)
    response_headers = response.get_headers(as_dict=True)
    cookie = response_headers.get('Set-Cookie', None)
    if cookie:
        headers.update({'Cookie': cookie})
    html = response.content
    headers.update({'Referer': rurl, 'Origin': rurl[:-1]})
    if not verifypeer:
        headers.update({'verifypeer': 'false'})
    source_list = scrape_sources(html, result_blacklist, scheme, patterns, generic_patterns, rurl)
    source = source_list[0][1]
    source = quote(source, '/:?=&') + append_headers(headers)
    return source

def scrape_sources(html, result_blacklist=None, scheme='http', patterns=None, generic_patterns=True, url=None):
    if patterns is None:
        patterns = []

    def __parse_to_list(_html, regex):
        _blacklist = ['.jpg', '.jpeg', '.gif', '.png', '.js', '.css', '.htm', '.html', '.php', '.srt', '.sub', '.xml', '.swf', '.vtt', '.mpd']
        _blacklist = set(_blacklist + result_blacklist)
        streams = []
        labels = []
        for r in re.finditer(regex, _html, re.DOTALL):
            match = r.groupdict()
            stream_url = match['url']
            if not (stream_url.startswith('http') or stream_url.startswith('/')):
                if re.search("^([A-Za-z0-9+/]{4})*([A-Za-z0-9+/]{3}=|[A-Za-z0-9+/]{2}==)?$", stream_url):
                    stream_url = b64decode(stream_url)
            if stream_url.startswith('//'):
                stream_url = scheme + ':' + stream_url
            elif not stream_url.startswith('http'):
                stream_url = urljoin(url, stream_url)
            stream_url = stream_url.replace('&amp;', '&')

            file_name = urlparse(stream_url[:-1]).path.split('/')[-1] if stream_url.endswith("/") else urlparse(stream_url).path.split('/')[-1]
            label = match.get('label', file_name)
            if label is None:
                label = file_name
            blocked = not file_name or any(item in file_name.lower() for item in _blacklist) or any(item in label for item in _blacklist)
            if '://' not in stream_url or blocked or (stream_url in streams) or any(stream_url == t[1] for t in source_list):
                continue
            labels.append(label)
            streams.append(stream_url)

        matches = zip(labels, streams) if six.PY2 else list(zip(labels, streams))
        if matches:
            print()
        return matches

    if result_blacklist is None:
        result_blacklist = []
    elif isinstance(result_blacklist, str):
        result_blacklist = [result_blacklist]

    html = html.replace(r"\/", "/")
    html += get_packed_data(html)

    source_list = []
    if generic_patterns or not patterns:
        source_list += __parse_to_list(html, r'''["']?label\s*["']?\s*[:=]\s*["']?(?P<label>[^"',]+)["']?(?:[^}\]]+)["']?\s*file\s*["']?\s*[:=,]?\s*["'](?P<url>[^"']+)''')
        source_list += __parse_to_list(html, r'''["']?\s*(?:file|src)\s*["']?\s*[:=,]?\s*["'](?P<url>[^"']+)(?:[^}>\]]+)["']?\s*label\s*["']?\s*[:=]\s*["']?(?P<label>[^"',]+)''')
        source_list += __parse_to_list(html, r'''video[^><]+src\s*[=:]\s*['"](?P<url>[^'"]+)''')
        source_list += __parse_to_list(html, r'''source\s+src\s*=\s*['"](?P<url>[^'"]+)['"](?:.*?res\s*=\s*['"](?P<label>[^'"]+))?''')
        source_list += __parse_to_list(html, r'''["'](?:file|url)["']\s*[:=]\s*["'](?P<url>[^"']+)''')
        source_list += __parse_to_list(html, r'''param\s+name\s*=\s*"src"\s*value\s*=\s*"(?P<url>[^"]+)''')
    for regex in patterns:
        source_list += __parse_to_list(html, regex)

    source_list = list(set(source_list))

    
    source_list = sort_sources_list(source_list)

    return source_list

def b64decode(t, binary=False):
    r = base64.b64decode(t)
    return r if binary else six.ensure_str(r)

def sort_sources_list(sources):
    if len(sources) > 1:
        try:
            sources.sort(key=lambda x: int(re.sub(r"\D", "", x[0])), reverse=True)
        except:
            
            try:
                sources.sort(key=lambda x: re.sub("[^a-zA-Z]", "", x[0].lower()))
            except:
                print()
    return sources

def get_packed_data(html):
    packed_data = ''
    for match in re.finditer(r'''(eval\s*\(function\(p,a,c,k,e,.*?)</script>''', html, re.DOTALL | re.I):
        r = match.group(1)
        t = re.findall(r'(eval\s*\(function\(p,a,c,k,e,)', r, re.DOTALL | re.IGNORECASE)
        if len(t) == 1:
            if jsunpack.detect(r):
                packed_data += jsunpack.unpack(r)
        else:
            t = r.split('eval')
            t = ['eval' + x for x in t if x]
            for r in t:
                if jsunpack.detect(r):
                    packed_data += jsunpack.unpack(r)
    return packed_data

def append_headers(headers):
    return '|%s' % '&'.join(['%s=%s' % (key, quote_plus(headers[key])) for key in headers])

def get_hidden(html, form_id=None, index=None, include_submit=True):
    hidden = {}
    if form_id:
        pattern = r'''<form [^>]*(?:id|name)\s*=\s*['"]?%s['"]?[^>]*>(.*?)</form>''' % (form_id)
    else:
        pattern = '''<form[^>]*>(.*?)</form>'''

    html = cleanse_html(html)

    for i, form in enumerate(re.finditer(pattern, html, re.DOTALL | re.I)):
        if index is None or i == index:
            for field in re.finditer('''<input [^>]*type=['"]?hidden['"]?[^>]*>''', form.group(1)):
                match = re.search(r'''name\s*=\s*['"]([^'"]+)''', field.group(0))
                match1 = re.search(r'''value\s*=\s*['"]([^'"]*)''', field.group(0))
                if match and match1:
                    hidden[match.group(1)] = match1.group(1)

            if include_submit:
                match = re.search('''<input [^>]*type=['"]?submit['"]?[^>]*>''', form.group(1))
                if match:
                    name = re.search(r'''name\s*=\s*['"]([^'"]+)''', match.group(0))
                    value = re.search(r'''value\s*=\s*['"]([^'"]*)''', match.group(0))
                    if name and value:
                        hidden[name.group(1)] = value.group(1)
    return hidden

def cleanse_html(html):
    for match in re.finditer('<!--(.*?)-->', html, re.DOTALL):
        if match.group(1)[-2:] != '//':
            html = html.replace(match.group(0), '')

    html = re.sub(r'''<(div|span)[^>]+style=["'](visibility:\s*hidden|display:\s*none);?["']>.*?</\\1>''', '', html, re.I | re.DOTALL)
    return html

def get_redirect_url(url, headers={}, form_data=None):
    class NoRedirection(HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    if form_data:
        if isinstance(form_data, dict):
            form_data = urlencode(form_data)
        request = Request(url, six.b(form_data), headers=headers)
    else:
        request = Request(url, headers=headers)

    opener = build_opener(NoRedirection())
    try:
        response = opener.open(request, timeout=20)
    except HTTPError as e:
        response = e
    return response.headers.get('location') or url