import importlib
import inspect
import logging

from .cleaner import Cleaner
from .comparer.comparer import Comparer
from .extractors.abstract_extractor import AbstractExtractor


class Extractor:
    """This class initializes all extractors and saves the results of them. When adding a new extractor, it needs to
    be initialized here and added to list_extractor.
    """

    def __init__(self, extractor_list):
        """
        Initializes all the extractors, comparers and the cleaner.

        :param extractor_list: List of strings containing all extractors to be initialized.
        """
        def proc_instance(instance):
            if instance is not None:
                self.log.info('Extractor initialized: %s', extractor)
                self.extractor_list.append(instance)
            else:
                self.log.error("Misconfiguration: An unknown Extractor was found and"
                               " will be ignored: %s", extractor)

        self.log = logging.getLogger(__name__)
        self.extractor_list = []
        for extractor in extractor_list:

            if isinstance(extractor, tuple):
                extractor_module = extractor[0]
            else:
                extractor_module = extractor

            module = importlib.import_module(__package__ + '.extractors.' + extractor_module)

            if isinstance(extractor, tuple):
                proc_instance(getattr(module, extractor[1], None)())
            else:
                # check module for subclasses of AbstractExtractor
                for member in inspect.getmembers(module, inspect.isclass):
                    if issubclass(member[1], AbstractExtractor) and member[0] != 'AbstractExtractor':

                        # instantiate extractor
                        proc_instance(getattr(module, member[0], None)())

        self.cleaner = Cleaner()
        self.comparer = Comparer()

    def extract(self, item):
        """Runs the HTML-response trough a list of initialized extractors, a cleaner and compares the results.

        :param item: NewscrawlerItem to be processed.
        :return: An updated NewscrawlerItem including the results of the extraction
        """

        article_candidates = []

        for extractor in self.extractor_list:
            article_candidate = extractor.extract(item)
            article_candidates.append(article_candidate)

        article_candidates = self.cleaner.clean(article_candidates)
        article = self.comparer.compare(item, article_candidates)

        item['article_title'] = article.title
        item['article_description'] = article.description
        item['article_maintext'] = article.maintext
        item['article_image'] = article.topimage
        item['article_author'] = article.author
        item['article_publish_date'] = article.publish_date
        item['article_language'] = article.language

        return item
