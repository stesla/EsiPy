# -*- encoding: utf-8 -*-
""" App entry point. Uses Esi Meta Endpoint to work """
from pyswagger import App

from .utils import check_cache


class EsiApp(object):
    """ EsiApp is an app object that'll allows us to play with ESI Meta
    API, not to have to deal with all ESI versions manually / meta """

    def __init__(self, **kwargs):
        """ Constructor.

        :param: cache if specified, use that cache, else use DictCache
        :param: min_cache_time is the minimum cache time for versions
        endpoints. If set to 0, never expires". Default 86400sec (1day)
        """
        min_cache_time = kwargs.pop('min_cache_time', 86400)
        self.expire = None if min_cache_time == 0 else min_cache_time
        self.cached_version = []

        self.cache = check_cache(kwargs.pop('cache', False))
        self.app = App.create('https://esi.tech.ccp.is/swagger.json')

    def __getattr__(self, name):
        """ Return the request object depending on its nature.

        if "op" is requested, simply return "app.op" which is a pyswagger app
        if anything else is requested, check if it exists, then if it's a
        swagger endpoint, try to create it and return it.
        """
        if name == 'op':
            return self.app.op

        try:
            op_attr = self.app.op[name]
        except KeyError:
            raise AttributeError('%s is not a valid operation' % name)

        # if the endpoint is a swagger spec
        if 'swagger.json' in op_attr.url:
            # need some caching here
            key = 'https:%s' % op_attr.url
            app = self.cache.get('https:%s' % op_attr.url, None)

            if app is None:
                app = App.create(key)
                self.cache.set(key, app, self.expire)
                self.cached_version.append(key)

            return app
        else:
            raise AttributeError('%s is not a swagger endpoint' % name)

    def force_update(self):
        """ update all endpoints by invalidating cache or reloading data """
        self.app = App.create('https://esi.tech.ccp.is/swagger.json')
        for key in self.cached_version:
            self.cache.invalidate(key)
        self.cached_version = []