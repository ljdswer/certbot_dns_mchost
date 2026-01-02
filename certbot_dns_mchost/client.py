"""
This module provides a client for clearing, setting and receiving the TXT record for McHost domains.
"""

import logging
import re

from bs4 import BeautifulSoup
from certbot.errors import PluginError
from requests import Session

logger = logging.getLogger(__name__)

POST_HEADERS = {
    "Referer": "https://my.mchost.ru/",
}

MCHOST_SESSION_URL = "https://my.mchost.ru/login/auth"
MCHOST_LOGIN_URL = "https://my.mchost.ru/j_spring_security_check?ajax=true"
MCHOST_ORDERS_URL = "https://my.mchost.ru"
MCHOST_ZONE_FROM_ORDER_URL = "https://my.mchost.ru/dnsOrder/administration"
MCHOST_CREATE_RECORD_URL = "https://my.mchost.ru/dnsZone/createRecord"
MCHOST_ZONE_RECORDS_URL = "https://my.mchost.ru/dnsZone/records"
MCHOST_DELETE_RECORD_URL = "https://my.mchost.ru/dnsZone/deleteRecord"


class McHostClient:
    """
    Encapsulates all communication with McHost API
    """

    def __init__(self, mchost_user: str, mchost_pass: str):
        self._session: Session = McHostClient.login(mchost_user, mchost_pass)
        self._domains: dict[str, str] = self.get_domains()

    def add_txt_record(self, domain_name: str, record_name: str, record_content: str):
        (domain_base, domain_id) = self.get_id_for_domain(domain_name)
        record_name = record_name[: -(len(domain_base) + 1)]
        response = self._session.post(
            MCHOST_CREATE_RECORD_URL,
            data={
                "name": record_name,
                "type": "TXT",
                "content": record_content,
                "id": domain_id,
            },
            headers=POST_HEADERS,
        )
        if response.status_code != 200:
            logger.error(
                f"Server returned an error while creating a record: {response.content}"
            )
            raise PluginError("Unable to create a record")

    def del_txt_record(self, domain_name: str, record_name: str, record_content: str):
        (domain_base, domain_id) = self.get_id_for_domain(domain_name)
        record_name = record_name[: -(len(domain_base) + 1)]
        record = self.get_txt_records(domain_id).get((record_name, record_content))
        if not record:
            logger.error(f"Tried to delete non-existing TXT record: {record_name}")
        else:
            response = self._session.post(
                MCHOST_DELETE_RECORD_URL,
                params={"id": domain_id, "recordId": record},
                headers=POST_HEADERS,
            )
            if response.status_code != 200:
                raise PluginError("Unable to delete a record")

    @staticmethod
    def login(user: str, passwd: str) -> Session:
        session = Session()

        response = session.get(MCHOST_SESSION_URL)
        if response.status_code != 200:
            raise PluginError("Unable to retrieve a new session")

        response = session.post(
            MCHOST_LOGIN_URL,
            data={
                "j_username": user,
                "j_password": passwd,
            },
            headers=POST_HEADERS,
        )

        if "error" in str(response.content) or response.status_code != 200:
            raise PluginError("Unable to authenticate")

        return session

    def get_zone_id_from_order(self, id: int) -> int:
        response = self._session.post(
            MCHOST_ZONE_FROM_ORDER_URL, data={"id": id}, headers=POST_HEADERS
        )

        if not response.content:
            raise PluginError("Unable to get zone administration panel")

        match = re.search(r"/dnsZone/index/(\d+)", str(response.content))
        if not match:
            raise PluginError("Unable to find zone ID")
        zone_id = match.group(1)
        if not zone_id:
            raise PluginError("McHost returned an invalid zone ID")
        return int(zone_id)

    def get_id_for_domain(self, domain_name: str) -> tuple[str, int]:
        for domain in self._domains.keys():
            if domain == domain_name or domain_name.endswith(f".{domain}"):
                return (domain, self.get_zone_id_from_order(int(self._domains[domain])))
        raise PluginError(f"No such domain found for the account: {domain_name}")

    def get_domains(self) -> dict[str, str]:
        response = self._session.get(MCHOST_ORDERS_URL)
        if not response.content:
            raise PluginError("No content retured for domains")

        soup = BeautifulSoup(response.content, "html.parser")
        tags = soup.find_all("a", class_="sidelink")

        result: dict[str, str] = {}
        for tag in tags:
            href = tag.get("href")
            name = tag.get("title")
            if href and name:
                if "dnsOrder" in href:
                    result[str(name)] = str(href).split("/")[-1]
        return result

    def get_txt_records(self, zone_id: int) -> dict[tuple[str, str], int]:
        response = self._session.post(
            MCHOST_ZONE_RECORDS_URL, params={"id": zone_id}, headers=POST_HEADERS
        )
        data = response.json().get("data")
        if not data:
            raise PluginError("No content retured from server for the zone")
        records = data.get("records")
        if not records:
            raise PluginError("No content retured for records")
        return {
            (r["name"], r["content"]): r["id"]
            for r in records
            if "id" in r and r["type"] == "TXT"
        }
