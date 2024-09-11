import io
import requests
from PIL import Image
import page_element as pe
from textwrap import wrap
from ast import literal_eval
import xml.etree.ElementTree as et
import os
import server as sv
import json
import pygame_canvas as c
from datetime import datetime as dt, timedelta as timedt
import utils as u
from copy import deepcopy

domains_cache = 0
domans = []

def get_cached_domains(source, force_cache = 0):
    global domains_cache, domains
    if force_cache or dt.timestamp(dt.now()) - domains_cache >= timedt(minutes=30).total_seconds():
        domains_cache = dt.timestamp(dt.now())
        domains = u.get_domains(source)
        print("caching domains")
        cached = 1
    else:
        print("domains already cached")
        cached = 0
    return domains

def fetch_domain(domain, source): #implement github one day

    source = get_cached_domains(source)

    print("fetching domains")

    filt = list(filter(lambda x: x["domain"] == domain, source))


    if any(filt):
        return list(filt)[0]["ip"], deepcopy(source)
    print("Non existent")
    return None, deepcopy(source)

def open_link(link):
    if not link:
        print("Link does not exists")
        return link
    print("Opening link " + link)
    if os.path.exists(link):
        print("Opening from file")
        try:
            with open(link, "r") as f:
                return f.read()
        except Exception as e:
            print("Error: ", e)
            return None
    elif sv.file_exists(link):
        print("Opening from Archive")
        return sv.read_text_file(link)

    else:
        try:
            request = requests.get(link)
            if request.status_code == 200:
                print("Opening from Ip")
                return request.text
            else:
                print("Non existent")
                return None
        except Exception as e:
            print("Error: ", e)
            return None

def piliToPysu(pil_image):
    """Convert a PIL Image to a Pygame Surface."""
    if pil_image.mode != 'RGBA':
        pil_image = pil_image.convert('RGBA')
    
    with io.BytesIO() as byte_io:
        pil_image.save(byte_io, format='PNG')
        byte_io.seek(0)
        
        pygame_surface = c.pygame.image.load(byte_io)
        
    return pygame_surface

image_cache = {}

def read_xml(root):
    temp_list = []
    for item in root:
        temp = {}
        temp["tag"] = item.tag
        temp["attr"] = {"width" : 0,
                        "height" : 0,
                        "color" : ("[50,50,50]" if item.tag == "button" else "[20,20,20]" if item.tag == "input" else "[255, 255, 255]"),
                        "scale" : 1,
                        "margins" : "[0,0]",
                        "lenght" : float("inf"),
                        "args" : "",
                        "function" : "None",
                        "id" : "-1",
                        "thickness" : "1",
                        "canDeploy" : 0,
                        "script" : None,
                        "name" : "name",
                        "font" : None,
                        "bold" : 0
                        }
        temp["attr"].update(dict(item.attrib))
        if item.text:
            temp["content"] = item.text.replace("    ", "")[1:-1]
        else:
            temp["content"] = ""
        if len(item):
            temp["children"] = read_xml(item)
        temp_list.append(temp)
    return temp_list

def get_image(url, width=0, height=0, scale=1):
    scale = float(scale)
    width = int(int(width) * scale)
    height = int(int(height) * scale)

    try:
        if url in image_cache:
            # Use the cached original image
            image = image_cache[url]
        else:
            response = requests.get(url)
            if response.status_code != 200:
                image = Image.new("RGB", (2, 2))
                for y in range(2):
                    for x in range(2):
                        if (x + y) % 2 == 0:
                            image.putpixel((x, y), (0, 0, 0))
                        else:
                            image.putpixel((x, y), (255, 0, 255))
                image_cache[url] = image  # Cache the placeholder
                return piliToPysu(image.resize((width or 100, height or 75), Image.NEAREST))

            # Load and cache the original image
            image_file = io.BytesIO(response.content)
            image = Image.open(image_file)
            image_cache[url] = image

        # Adjust width and height if not provided
        if width == 0 or height == 0:
            width, height = int(image.size[0] * scale), int(image.size[1] * scale)

        return piliToPysu(image.resize((width, height), Image.NEAREST))

    except Exception as e:
        print(f"Error: {e}")
        image = Image.new("RGB", (2, 2))
        for y in range(2):
            for x in range(2):
                if (x + y) % 2 == 0:
                    image.putpixel((x, y), (0, 0, 0))
                else:
                    image.putpixel((x, y), (255, 0, 255))
        return piliToPysu(image.resize((width or 100, height or 75), Image.NEAREST))

def get_objects(xml_list):
    page_margins = [0,0]
    name = "name"
    script_link = None
    page = []
    for item in xml_list:
        attr = item["attr"]
        if len(page):
            last = sorted(page, key=lambda x: x.offset[1] + x.margin[1] + x.sizes[1])[-1]
        else:
            last = 0

        if item["tag"] == "p":
            for lines in item["content"].split("\n"):
                for string in wrap(lines, attr["lenght"]):
                    if len(page):
                        last = sorted(page, key=lambda x: x.offset[1] + x.margin[1] + x.sizes[1])[-1]
                    else:
                        last = 0
                    temp = pe.text(item, string, last)
                    page.append(temp)
                    del temp

        elif item["tag"] == "h":
            page.append(pe.text(item, item["content"], last))

        elif item["tag"] == "image":
            page.append(pe.image(item, last))

        elif item["tag"] == "br":
            page.append(pe.br(item, last))

        elif item["tag"] == "newline":
            page.append(pe.newLine(item, last))

        elif item["tag"] == "page":
            page_margins = list(literal_eval(attr["margins"]))
            script_link = attr["script"]
            name = attr["name"]

        elif item["tag"] == "button":
            page.append(pe.button(item, last))

        elif item["tag"] == "rh":
            page.append(pe.rh(item, last))

        elif item["tag"] == "input":
            page.append(pe.input_box(item, last))


    return page, page_margins, script_link, name

# the one yo looking foah

def create_site_objects(site, link):
    try:
        try:
            root = et.parse(site).getroot()
        except (FileNotFoundError, OSError):
            root = et.fromstring(site)
        xml_list = read_xml(root)
        page = get_objects(xml_list)
        for item in page[0]:
            item.update(0, 1, margins = (5,5), screen = c.screen_size(), page_objects = page, script = None)
            if hasattr(item, "created"):
                item.created = 0
    except Exception as e:
        root = et.fromstring(f"""
<root>
    <page margins = "[50,0]" name="Error" />
    <newline/>
    <p color = "[255,50,50]">
        Error: {e}
    </p>
    <rh color = "[60,60,60]"/>
    <br/>
    <button function="load" args="{link}"> Go Back </button>
</root>
                               """)
        xml_list = read_xml(root)
        page = *get_objects(xml_list), "error"
    return page
