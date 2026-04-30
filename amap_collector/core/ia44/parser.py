import re
import html as html_lib
from typing import Any

from bs4 import BeautifulSoup, Tag


class Ia44AmapListParser:
    """Parses .item-container cards from any amap44.org listing page.

    Used for both AMAP lists (category=258) and per-AMAP farmer lists.
    """

    def parse(self, html: str) -> list[dict[str, Any]]:
        soup = BeautifulSoup(html, 'html.parser')
        return [self.__parse_card(c) for c in soup.select('.item-container')]

    def __parse_card(self, card: Tag) -> dict[str, Any]:
        link = card.select_one('.item-title a')
        href = link['href'] if link else ''
        m = re.search(r'\?ait-item=(.+)', str(href))
        slug = m.group(1) if m else ''

        name_el = link.find('h3') if link else None
        name = name_el.get_text(strip=True) if name_el else ''

        abstract_el = card.select_one('.entry-content p')
        abstract = abstract_el.get_text(strip=True) if abstract_el else None

        address_el = card.select_one('.item-address .value')
        address = address_el.get_text(strip=True) if address_el else ''

        website_el = card.select_one('.item-web .value a')
        website = website_el['href'] if website_el else ''

        # Collect category hrefs to distinguish AMAPs from farmers
        category_hrefs = [a['href'] for a in card.select('.item-categories a[href]')]

        return {
            'slug': slug,
            'name': name,
            'abstract': abstract,
            'address': address,
            'website': website,
            'category_hrefs': category_hrefs,
        }


class Ia44AmapDetailParser:
    """Parses an AMAP detail page at ?ait-item=<slug>."""

    def parse(self, html: str) -> dict[str, Any]:
        soup = BeautifulSoup(html, 'html.parser')

        abstract = self.__parse_abstract(soup)
        address = self.__parse_address(soup)
        days = self.__parse_days(soup)
        emails = self.__parse_emails(soup)
        website = self.__parse_website(soup)
        products, farmer_list_url = self.__parse_extension(soup)

        return {
            'abstract': abstract or None,
            'address': address,
            'days': days,
            'emails': emails,
            'website': website,
            'products': products,
            'farmer_list_url': farmer_list_url,
        }

    def __parse_abstract(self, soup: BeautifulSoup) -> str:
        el = soup.select_one('.entry-content-wrap .entry-content')
        if not el:
            return ''
        # Remove img tags and get clean text
        for img in el.find_all('img'):
            img.decompose()
        return el.get_text(' ', strip=True)

    def __parse_address(self, soup: BeautifulSoup) -> str:
        el = soup.select_one('.row-postal-address .address-data p')
        return el.get_text(strip=True) if el else ''

    def __parse_days(self, soup: BeautifulSoup) -> list[dict[str, str]]:
        days = []
        for dw in soup.select('.day-wrapper'):
            day_name_el = dw.select_one('.day-title h5')
            day_name = day_name_el.get_text(strip=True) if day_name_el else ''

            day_data_el = dw.select_one('.day-data p')
            if not day_data_el:
                continue
            for meta in day_data_el.find_all('meta'):
                meta.decompose()
            raw = day_data_el.get_text(strip=True)

            hours = self.__parse_hours(raw)
            if hours and day_name:
                days.append({'weekDay': day_name, **hours})
        return days

    def __parse_hours(self, text: str) -> dict[str, str] | None:
        text = text.strip()
        if not text or text == '-':
            return None
        # Format A: "18H-19H30" or "18h30-19h"
        m = re.search(r'(\d+)[Hh](\d*)\s*[-–]\s*(\d+)[Hh](\d*)', text)
        # Format B: "de 14h à 18h" or "de 14h30 à 18h"
        if not m:
            m = re.search(
                r'de\s+(\d+)[Hh](\d*)\s+[àa]\s+(\d+)[Hh](\d*)', text, re.IGNORECASE
            )
        if not m:
            return None
        oh, om, ch, cm = m.groups()
        return {
            'openHour': f"{int(oh):02d}:{int(om) if om else 0:02d}:00.000",
            'closeHour': f"{int(ch):02d}:{int(cm) if cm else 0:02d}:00.000",
        }

    def __parse_emails(self, soup: BeautifulSoup) -> list[str]:
        el = soup.select_one('.row-email .address-data a[href]')
        if el:
            email = el.get_text(strip=True)
            if email:
                return [email]
        return []

    def __parse_website(self, soup: BeautifulSoup) -> str:
        el = soup.select_one('.row-web .address-data a[href]')
        return str(el['href']) if el else ''

    def __parse_extension(self, soup: BeautifulSoup) -> tuple[list[str], str | None]:
        products: list[str] = []
        farmer_list_url: str | None = None

        for fc in soup.select('.item-extension-container .field-container'):
            title_el = fc.select_one('.field-title h5')
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            data_el = fc.select_one('.field-data')
            if not data_el:
                continue

            if 'Liste des Produits' in title:
                link_el = data_el.select_one('a')
                if not link_el:
                    text = data_el.get_text(strip=True)
                    placeholder = 'entrez ici'
                    if text and placeholder not in text.lower():
                        products = [p.strip() for p in text.split(',') if p.strip()]

            elif 'Liste des producteurs du lieu de distribution' in title:
                link_el = data_el.select_one('a[href]')
                if link_el and 'amap44.org' in str(link_el['href']):
                    farmer_list_url = str(link_el['href'])

        return products, farmer_list_url


_PROTOCOL_FIELDS: dict[str, str] = {
    "Certification AB": "ab_certification",
    "Conversion AB": "ab_conversion",
    "Certification Bio Cohérence": "bio_coherence_certification",
    "Certification Demeter": "demeter_certification",
    "Sans Pesticides ni Engrais Chimiques": "no_pest_chemistry",
}


class Ia44FarmerDetailParser:
    """Parses a farmer detail page at ?ait-item=<slug>. Same HTML structure as AMAP detail."""

    def parse(self, html: str) -> dict[str, Any]:
        soup = BeautifulSoup(html, 'html.parser')

        meta = soup.find('meta', {'itemprop': 'name'})
        name = html_lib.unescape(meta['content']) if meta else ''

        address_el = soup.select_one('.row-postal-address .address-data p')
        address = address_el.get_text(strip=True) if address_el else ''

        m = re.search(r'\d{5}\s+(.+)$', address)
        city = m.group(1).strip() if m else ''

        email_el = soup.select_one('.row-email .address-data a[href]')
        email = email_el.get_text(strip=True) if email_el else ''

        website_el = soup.select_one('.row-web .address-data a[href]')
        website = str(website_el['href']) if website_el else ''

        return {
            'name': name,
            'address': address,
            'city': city,
            'emails': [email] if email else [],
            'website': website,
            'protocols': self.__parse_protocols(soup),
        }

    def __parse_protocols(self, soup: BeautifulSoup) -> dict[str, bool]:
        protocols: dict[str, bool] = {}
        for fc in soup.select('.item-extension-container .field-container'):
            title_el = fc.select_one('.field-title h5')
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            key = _PROTOCOL_FIELDS.get(title)
            if key is None:
                continue
            icon = fc.select_one('.field-data i')
            if not icon:
                continue
            classes = icon.get_attribute_list('class')
            if 'fa-check' in classes:
                protocols[key] = True
            elif 'fa-remove' in classes:
                protocols[key] = False
        return protocols
