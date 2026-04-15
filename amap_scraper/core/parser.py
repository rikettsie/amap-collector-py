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
            amap_name = self.__text(article, "amap-nom")
            amap_status = "completed" if self.__text(article, "statut-complet") == 'complet' else 'available_places'
            amap_website = self.__href(article, "amap-link")

            el = {
                "name": amap_name,
                "status": amap_status,
                "website": amap_website,
            }

            partages = article.find_all(class_="partage")
            if partages:
                for partage in partages:
                    contact_emails = self.__links(partage, "contact-email")
                    contact_tels = self.__links(partage, "contact-tel")
                    el = {
                        **el,
                        **{
                            "contact": {
                                "name": self.__contact_name(partage),
                                "emails": contact_emails,
                                "phones": contact_tels,
                            },
                            "place": {
                                "name": self.__text(partage, "partage-nom"),
                                "address": self.__text(partage, "partage-adresse", separator=", "),
                                "delivery_time": self.__text(partage, "partage-jour").replace("Jour de partage :", "").strip(),
                            },
                            "comment": self.__text(partage, "partage-commentaire"),
                        }
                    }
            
            # Dedoubling
            hashed_el = hashlib.sha256(json.dumps(el, sort_keys=True).encode()).hexdigest()
            results[hashed_el] = el

        return list(results.values())

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
