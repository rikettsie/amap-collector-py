import hashlib
import json
import re
from typing import Any
from bs4 import BeautifulSoup, Tag
from bs4.element import NavigableString


class ParserError(RuntimeError):
    pass


class IdfAmapListParser:

    def parse(self, html: str) -> list[dict[str, Any]]:
        results: dict[str, dict[str, Any]] = {}

        soup = BeautifulSoup(html, "html.parser")
        container = soup.select_one(".liste-fiches.liste-fiches-amaps")
        if not container:
            if soup.find("body"):
                raise ParserError(
                    "HTML response received but '.liste-fiches.liste-fiches-amaps' "
                    "container not found — the page structure may have changed."
                )
            return []

        for article in container.find_all("article", class_="fiche-amap"):
            amap_status = "completed" if self.__text(article, "statut-complet") == "complet" else "available_places"
            amap_name = self.__amap_name(article)  # must come after status check (mutates the tree)
            amap_website = self.__href(article, "amap-link")

            base = {
                "name": amap_name,
                "status": amap_status,
                "website": amap_website,
            }

            for partage in article.find_all(class_="partage"):
                delivery_time = self.__text(partage, "partage-jour").replace("Jour de partage :", "").strip()
                entry = {
                    **base,
                    "abstract": None,
                    "contact": {
                        "name": self.__contact_name(partage),
                        "emails": self.__links(partage, "contact-email"),
                        "phones": self.__links(partage, "contact-tel"),
                    },
                    "delivery": {
                        "place_name": self.__text(partage, "partage-nom") or None,
                        "address": self.__text(partage, "partage-adresse", separator=", "),
                        "days": self.__parse_delivery_time(delivery_time),
                    },
                    "comment": self.__text(partage, "partage-commentaire"),
                    "products": [],
                    "farms": [],
                }
                hashed = hashlib.sha256(json.dumps(entry, sort_keys=True).encode()).hexdigest()
                results[hashed] = entry

        return list(results.values())

    def __amap_name(self, article: Tag) -> str:
        found = article.find(class_="amap-nom")
        if not found:
            raise ParserError(
                "Required element '.amap-nom' not found in article — "
                "the page structure may have changed."
            )
        for span in found.find_all(class_="statut-complet"):
            span.extract()
        return found.get_text(strip=True)

    def __require(self, el: Tag, css_class: str, context: str, separator: str = "") -> str:
        found = el.find(class_=css_class)
        if not found:
            raise ParserError(
                f"Required element '.{css_class}' not found in {context} — "
                "the page structure may have changed."
            )
        return found.get_text(separator=separator, strip=True)

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

    def __parse_delivery_time(self, text: str) -> list[dict[str, str]]:
        m = re.match(r'(\w+)\s+(\d+)h(\d+)\s*[-–]\s*(\d+)h(\d+)', text)
        if not m:
            return []
        week_day, open_h, open_m, close_h, close_m = m.groups()
        return [{
            'weekDay': week_day,
            'openHour': f"{open_h.zfill(2)}:{open_m.zfill(2)}:00.000",
            'closeHour': f"{close_h.zfill(2)}:{close_m.zfill(2)}:00.000",
        }]

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
