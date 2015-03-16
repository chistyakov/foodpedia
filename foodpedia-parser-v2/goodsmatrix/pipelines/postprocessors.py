from scrapy import log

from goodsmatrix import string_processor
from goodsmatrix.agrovoc_graph import agrovoc_graph_factory


class ExtractEsl(object):
    def process_item(self, good_item, spider):
        if 'esl_as_string' in good_item:
            esl_as_string = good_item['esl_as_string']
            good_item.update(string_processor.parse_esl(esl_as_string))
        return good_item


class ExtractEAdditives(object):
    def process_item(self, good_item, spider):
        if 'ingredients' in good_item:
            ingredients_as_string = good_item['ingredients']
            extracted_e_additives = string_processor.parse_e_additives(
                ingredients_as_string)
            good_item['e_additives'] = extracted_e_additives
        return good_item


class StripMultilineStringProperties(object):
    def process_item(self, good_item, spider):
        for key in good_item:
            try:
                good_item[key] = string_processor.strip_multiline(good_item[key])
            except AttributeError:
                pass
        return good_item


class UnescapeSpecialHTMLEntities(object):
    """
    usual special html entities (e.g. &quot;) are decoded on extracting,
    but goodsmatrix.ru plays a dirty trick on some goods providing
    special entities in upper case (e.g. &QUOT;)
    """
    def process_item(self, good_item, spider):
        for key in good_item:
            try:
                good_item[key] = string_processor.unescape_html_special_entities_case_insensitive(
                    good_item[key])
            except TypeError:
                pass
        return good_item


class ExtractIngredients(object):
    def open_spider(self, spider):
        self.agrovoc_graph = agrovoc_graph_factory(local=False)
        self.not_parsed_fragments = dict()

    def process_item(self, good_item, spider):
        ingredients_as_string = good_item['ingredients']
        ingredients_as_string = string_processor.remove_substring_in_paranthesis(
            ingredients_as_string)
        ingredients_fragments = string_processor.split_ingredients(ingredients_as_string)
        log.msg("ingredients after splitting: {0}".format(ingredients_fragments))
        for fragment in ingredients_fragments:
            if not string_processor.parse_e_additives(fragment):
                fragment = string_processor.remove_weight(fragment)
                fragment = string_processor.remove_percents(fragment)
                agrovoc_match = self.agrovoc_graph.find_ingredient_by_name(fragment.strip())
                if agrovoc_match:
                    log.msg('found ingredient {0}'.format(agrovoc_match))
                    good_item['agrovoc_ingredients'] = (
                        good_item.get('agrovoc_ingredients', []) + [agrovoc_match])
                else:
                    self.not_parsed_fragments[fragment] = (
                        self.not_parsed_fragments.get(fragment, 0) + 1)
        return good_item

    def close_spider(self, spider):
        self.agrovoc_graph.clean_up()
        log.msg(self.not_parsed_fragments)
