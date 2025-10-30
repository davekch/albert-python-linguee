# -*- coding: utf-8 -*-

"""linguee extension
translate ger-eng with linguee

Synopsis: <trigger> <word>"""


from albert import *
import requests
from xml.etree import ElementTree
import os
import time
from pathlib import Path


md_iid = "4.0"
md_version = "0.5"
md_name = "Linguee"
md_description = "Translate with Linguee."
md_maintainers = "@davekch"
md_lib_dependencies = ["requests"]


class Plugin(PluginInstance, TriggerQueryHandler):

    lang = "deutsch-englisch"
    user_agent = "org.albert.linguee"
    icon = Path(__file__).parent / "linguee.svg"

    def __init__(self):
        TriggerQueryHandler.__init__(self)
        PluginInstance.__init__(self)

    def synopsis(self, query):
        return "<lin phrase>"

    def defaultTrigger(self):
        return "lin "

    def handleTriggerQuery(self, query):
        querystr = query.string.strip()
        if querystr:
            if not query.isValid:
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
                        icon_factory=lambda: makeImageIcon(self.icon),
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
                                lambda u=url: setClipBoardText(u)
                            ),
                        ],
                    )
                )
            query.add(results)

        else:
            query.add(StandardItem(
                id="lin",
                text=md_name,
                subtext="Enter a word to translate",
                icon_factory=lambda: makeImageIcon(self.icon),
            ))

    def get_suggestions(self, query):
        response = requests.get(
            "https://www.linguee.de/" + self.lang + "/search?",
            # change the ch-parameter to get more/less results
            params={"qe": query, "source": "auto", "cw": "820", "ch": "1000"},
            headers={"User-Agent": self.user_agent}
        )
        return get_results(response.text)



def clean_translation_item(item):
    # the translation_item contains information like word type etc but we're
    # only interested in placeholders (like "sth.") so we remove everything else
    if len(item) == 0:
        return

    remove = []
    for i in item:
        if i.attrib["class"] != "placeholder":
            remove.append(i)
        else:
            clean_translation_item(i)  # the structure may be nested
    for r in remove:
        item.remove(r)



def get_results(linguee_response):
    linguee_response = linguee_response.replace("<span class='sep'>&middot;</span>","")
    linguee_response = linguee_response.replace("&","#-#")
    root = ElementTree.fromstring(linguee_response)
    results = []
    for item in root:
        word = item[0][0].text.strip().encode().decode("utf-8")
        translations = []
        for translation_row in item[1:]:
            for translation_item in translation_row[0]:
                clean_translation_item(translation_item)
                translation = " ".join(tr.strip() for tr in translation_item.itertext()).strip()
                translations.append(translation)

        results.append({"word": word, "translations": translations})

    return results

