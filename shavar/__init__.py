import logging
import threading
import time

import shavar.lists


__version__ = '0.12.8.5'
DEFAULT_REFRESH_LISTS_DELAY = 600  # 10m
logger = logging.getLogger('shavar')


class RefreshListsConfigThread(threading.Thread):
    def __init__(self, delay, config):
        threading.Thread.__init__(self)
        self.delay = delay
        self.config = config

    def run(self):
        logger.info("Starting RefreshListsConfigThread")
        refresh_lists_config(self.delay, self.config)


def refresh_lists_config(delay, config):
    while(delay):
        time.sleep(delay)
        logger.info("Refreshing lists config ...")
        shavar.lists.includeme(config)
        logger.info("Refreshing lists config done.")


def includeme(config):
    "Load shavar WSGI app into the provided Pyramid configurator"
    # Dependencies first
    config.include("mozsvc")
    config.include('pyramid_mako')
    # Have to get the lists loaded before the views
    shavar.lists.includeme(config)
    config.include("shavar.views")


def get_configurator(global_config, **settings):
    import mozsvc.config
    config = mozsvc.config.get_configurator(global_config, **settings)
    config.begin()
    try:
        config.include(includeme)
    finally:
        config.end()
    return config

def filter_errors(event, hint):
    if  'logentry' in event and 'message' in event['logentry']:
        message = event['logentry']['message']
        patterns = ['(Invalid RANGE "[0-9]{10})', '(Invalid LISTINFO)',
                    '(Invalid list name)']
        m = re.match('|'.join(patterns), message)
        if m is not None:
            return None
    return event

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    import sentry_sdk

    sentry_sdk.init(dsn='',
        before_send=filter_errors)
    config = get_configurator(global_config, **settings)
    app = config.make_wsgi_app()
    refreshListsConfigThread = RefreshListsConfigThread(
        config.registry.settings.get(
            'shavar.refresh_lists_delay', DEFAULT_REFRESH_LISTS_DELAY
        ),
        config
    )
    refreshListsConfigThread.daemon = True
    refreshListsConfigThread.start()
    return app
