import hashlib
import json
from typing import Any
from bs4 import BeautifulSoup, Tag
from bs4.element import NavigableString

class AmapListParser:

    def parse(self, html: str) -> list[dict[str, Any]]:
        results: dict[str, dict[str, Any]] = {}

        soup = BeautifulSoup(html, "html.parser")
        container = soup.select_one(".liste-fiches.liste-fiches-amaps")
        if not container:
            return []

        for article in container.find_all("article", class_="fiche-amap"):
            amap_status = "completed" if self.__text(article, "statut-complet") == 'complet' else 'available_places'
            amap_name = self.__amap_name(article)  # must come after status check (mutates the tree)
            amap_website = self.__href(article, "amap-link")

            base = {
                "name": amap_name,
                "status": amap_status,
                "website": amap_website,
            }

            for partage in article.find_all(class_="partage"):
                entry = {
                    **base,
                    "contact": {
                        "name": self.__contact_name(partage),
                        "emails": self.__links(partage, "contact-email"),
                        "phones": self.__links(partage, "contact-tel"),
                    },
                    "place": {
                        "name": self.__text(partage, "partage-nom"),
                        "address": self.__text(partage, "partage-adresse", separator=", "),
                        "delivery_time": self.__text(partage, "partage-jour").replace("Jour de partage :", "").strip(),
                    },
                    "comment": self.__text(partage, "partage-commentaire"),
                }
                hashed = hashlib.sha256(json.dumps(entry, sort_keys=True).encode()).hexdigest()
                results[hashed] = entry

        return list(results.values())

    def __amap_name(self, article: Tag) -> str:
        found = article.find(class_="amap-nom")
        if not found:
            return ""
        for span in found.find_all(class_="statut-complet"):
            span.extract()
        return found.get_text(strip=True)

    def __text(self, el: Tag, css_class: str, separator: str = "") -> str:
        found = el.find(class_=css_class)
        return found.get_text(separator=separator, strip=True) if found else ""

    def __links(self, el: Tag, css_class: str) -> list[str]:
        found = el.find(class_=css_class)
        if not found:
            return []
        return [a.get_text(strip=True) for a in found.find_all("a")]

    def __href(self, el: Tag, css_class: str) -> str:
        found = el.find(class_=css_class)
        if not found:
            return ""
        href = found.get("href", "")
        return href if isinstance(href, str) else ""

    def __contact_name(self, el: Tag) -> str:
        found = el.find(class_="partage-contact")
        if not found:
            return ""
        skip = {"contact-email", "contact-tel"}
        parts = []
        for child in found.children:
            if isinstance(child, Tag):
                if not skip.intersection(child.get("class") or []):
                    text = child.get_text(strip=True)
                    if text:
                        parts.append(text)
            elif isinstance(child, NavigableString):
                text = child.strip()
                if text:
                    parts.append(text)
        return " ".join(parts).replace("Contact :", "").strip()
