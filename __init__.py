# -*- coding: utf-8 -*-

"""linguee extension
translate ger-eng with linguee

Synopsis: <trigger> <word>"""


from albert import (
    PluginInstance,
    GeneratorQueryHandler,
    Icon,
    StandardItem,
    Action,
    openUrl,
    setClipboardText,
)
import requests
from xml.etree import ElementTree
import time
from pathlib import Path


md_iid = "5.0"
md_version = "0.6"
md_name = "Linguee"
md_description = "Translate with Linguee."
md_maintainers = ["@davekch"]
md_lib_dependencies = ["requests"]


class Plugin(PluginInstance, GeneratorQueryHandler):

    lang = "deutsch-englisch"
    user_agent = "org.albert.linguee"

    def __init__(self):
        PluginInstance.__init__(self)
        GeneratorQueryHandler.__init__(self)

    def synopsis(self, query):
        return "<lin phrase>"

    def defaultTrigger(self):
        return "lin "

    @staticmethod
    def makeIcon():
        return Icon.image(Path(__file__).parent / "linguee.svg")

    def items(self, context):
        querystr = context.query.strip()
        if querystr:
            if not context.isValid:
                return

            time.sleep(0.1)
            results = []
            for result in self.get_suggestions(querystr):
                url = "http://www.linguee.de/{}/search?source=auto&query={}".format(
                    self.lang,
                    result["word"]
                )
                results.append(
                    StandardItem(
                        id=result["word"],
                        icon_factory=Plugin.makeIcon,
                        text=result["word"],
                        subtext=", ".join(result["translations"]),
                        input_action_text=result["word"],
                        actions=[
                            Action(
                                "open",
                                "look up word on linguee",
                                lambda u=url: openUrl(u)
                            ),
                            Action(
                                "copy",
                                "Copy url to clipboard",
                                lambda u=url: setClipboardText(u)
                            ),
                        ],
                    )
                )
            yield results

        else:
            yield [StandardItem(
                id="lin",
                text=md_name,
                subtext="Enter a word to translate",
                icon_factory=Plugin.makeIcon,
            )]

    def get_suggestions(self, query):
        response = requests.get(
            "https://www.linguee.de/" + self.lang + "/search?",
            # change the ch-parameter to get more/less results
            params={"qe": query, "source": "auto", "cw": "820", "ch": "1000"},
            headers={"User-Agent": self.user_agent}
        )
        return get_results(response.text)


def get_display_text(item):
    """return the text of a html element without grammar info"""
    grammar_classes = ["grammar_info", "wordtype"]
    if any(g in item.get("class", "").split() for g in grammar_classes):
        return ""

    parts = [item.text or ""]
    for child in item:
        parts.append(get_display_text(child))
        parts.append(child.tail or "")

    return " ".join([p.strip() for p in parts if p != ""])


def get_results(linguee_response):
    linguee_response = linguee_response.replace("<span class='sep'>&middot;</span>","")
    linguee_response = linguee_response.replace("&","#-#")
    root = ElementTree.fromstring(linguee_response)
    results = []
    for item in root:
        word = get_display_text(item[0][0])
        translations = []
        for translation_row in item[1:]:
            for translation_item in translation_row[0]:
                translations.append(get_display_text(translation_item))

        results.append({"word": word, "translations": translations})

    return results
