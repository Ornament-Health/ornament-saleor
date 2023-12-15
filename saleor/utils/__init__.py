from lxml import etree


class skip_signals():
    def __init__(self, instance):
        self.instance = instance

    def __enter__(self):
        self.instance.__skip_signals__ = True

    def __exit__(self, type, value, traceback):
        self.instance.__skip_signals__ = False


def get_safe_lxml_parser():
    return etree.XMLParser(resolve_entities=False)
