#!/usr/bin/env python3
import argparse
import requests
from urllib.parse import quote_plus
from json import dumps, decoder

import phonenumbers
from phonenumbers.phonenumberutil import (
    region_code_for_country_code,
    region_code_for_number,
)
import pycountry

def getUserId(username, sessionsId):
    headers = {"User-Agent": "iphone_ua", "x-ig-app-id": "936619743392459"}
    api = requests.get(
        f'https://i.instagram.com/api/v1/users/web_profile_info/?username={username}',
        headers=headers,
        cookies={'sessionid': sessionsId}
    )
    try:
        if api.status_code == 404:
            return {"id": None, "error": "User not found"}

        id = api.json()["data"]['user']['id']
        return {"id": id, "error": None}

    except decoder.JSONDecodeError:
        return {"id": None, "error": "Rate limit"}


def getInfo(search, sessionId, searchType="username"):
    if searchType == "username":
        data = getUserId(search, sessionId)
        if data["error"]:
            return data
        userId = data["id"]
    else:
        try:
            userId = str(int(search))
        except ValueError:
            return {"user": None, "error": "Invalid ID"}

    try:
        response = requests.get(
            f'https://i.instagram.com/api/v1/users/{userId}/info/',
            headers={'User-Agent': 'Instagram 64.0.0.14.96'},
            cookies={'sessionid': sessionId}
        )
        if response.status_code == 429:
            return {"user": None, "error": "Rate limit"}

        response.raise_for_status()

        info_user = response.json().get("user")
        if not info_user:
            return {"user": None, "error": "Not found"}

        info_user["userID"] = userId
        return {"user": info_user, "error": None}

    except requests.exceptions.RequestException:
        return {"user": None, "error": "Not found"}


def advanced_lookup(username):
    """
        Post to get obfuscated login infos
    """
    data = "signed_body=SIGNATURE." + quote_plus(dumps(
        {"q": username, "skip_recovery": "1"},
        separators=(",", ":")
    ))
    api = requests.post(
        'https://i.instagram.com/api/v1/users/lookup/',
        headers={
            "Accept-Language": "en-US",
            "User-Agent": "Instagram 101.0.0.15.120",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-IG-App-ID": "124024574287414",
            "Accept-Encoding": "gzip, deflate",
            "Host": "i.instagram.com",
            "Connection": "keep-alive",
            "Content-Length": str(len(data))
        },
        data=data
    )

    try:
        return {"user": api.json(), "error": None}
    except decoder.JSONDecodeError:
        return {"user": None, "error": "rate limit"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--sessionid', help="Instagram session ID", required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-u', '--username', help="One username")
    group.add_argument('-i', '--id', help="User ID")
    args = parser.parse_args()

    sessionsId = args.sessionid
    search_type = "id" if args.id else "username"
    search = args.id or args.username
    infos = getInfo(search, sessionsId, searchType=search_type)
    if not infos.get("user"):
        exit(infos["error"])

    infos = infos["user"]

    print("Informations about     : " + infos.get("username", "N/A"))
    print("userID                 : " + infos.get("userID", "N/A"))
    print("Verified               : " + str(infos.get('is_verified', False)) +
          " | Is business Account : " + str(infos.get("is_business", False)))
    print("Is private Account     : " + str(infos.get("is_private", False)))
    print("Follower               : " + str(infos.get("follower_count", 0)) +
          " | Following : " + str(infos.get("following_count", 0)))
    print("Number of posts        : " + str(infos.get("media_count", 0)))
    if infos.get("external_url"):
        print("External url           : " + infos["external_url"])
    print("Biography              : " + ("\n" + " " * 25).join(infos.get("biography", "").split("\n")))
    print("Linked WhatsApp        : " + str(infos.get("is_whatsapp_linked", False)))
    print("Memorial Account       : " + str(infos.get("is_memorialized", False)))
    print("New Instagram user     : " + str(infos.get("is_new_to_instagram", False)))

    if infos.get("public_email"):
        print("Public Email           : " + infos["public_email"])

    if infos.get("public_phone_number"):
        phonenr = "+" + str(infos.get("public_phone_country_code", "")) + " " + str(infos["public_phone_number"])
        try:
            pn = phonenumbers.parse(phonenr)
            countrycode = region_code_for_country_code(pn.country_code)
            country = pycountry.countries.get(alpha_2=countrycode)
            phonenr = phonenr + " ({}) ".format(country.name)
        except:
            pass
        print("Public Phone number    : " + phonenr)

    other_infos = advanced_lookup(infos.get("username", ""))

    if other_infos.get("error") == "rate limit":
        print("Rate limit, please wait a few minutes before trying again")

    elif other_infos.get("user", {}).get("message") == "No users found":
        print("The lookup did not work on this account")

    else:
        obfuscated_email = other_infos.get("user", {}).get("obfuscated_email")
        if obfuscated_email:
            print("Obfuscated email       : " + obfuscated_email)
        else:
            print("No obfuscated email found")

        obfuscated_phone = other_infos.get("user", {}).get("obfuscated_phone")
        if obfuscated_phone:
            print("Obfuscated phone       : " + str(obfuscated_phone))
        else:
            print("No obfuscated phone found")

    print("-" * 24)
    print("Profile Picture        : " + infos.get("hd_profile_pic_url_info", {}).get("url", "No picture"))


if __name__ == "__main__":
    main()
