import pydxcc
import web
import os
import configparser

urls = (
  '/callsign', 'index',
  '/lookup/json/(.+)', 'call_json',
  '/lookup/xml/(.+)', 'call_xml',
)

CFG = configparser.ConfigParser()
CFG.read(os.path.expanduser(os.path.dirname(os.path.abspath(__file__)) + '/pydxcc.cfg'))
CTYFILES_PATH = os.path.expanduser(CFG.get('CTYFILES', 'path'))
CTYFILES_URL = CFG.get('CTYFILES', 'url')
AUTOFETCH_FILES = CFG.getboolean('CTYFILES', 'autofetch')

pydxccresolver = pydxcc.dxcc(CTYFILES_PATH, CTYFILES_URL, AUTOFETCH_FILES)


class index:
    def GET(self):
        return "Hello, world!"

class call_json:
    def GET(self, callsign):
        return (pydxccresolver.dxcc2json(pydxccresolver.call2dxcc(callsign.upper(), None)))

class call_xml:
    def GET(self, callsign):
        return (pydxccresolver.dxcc2xml(pydxccresolver.call2dxcc(callsign.upper(), None)))

app = web.application(urls, globals())
application = app.wsgifunc()

if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()
