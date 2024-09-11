import server as sv
import pygame_canvas as c
import web_utils as w
import threading as t
import utils as u
from web_utils import requests
from utils import json as j
import math
from datetime import datetime as dt, timedelta as timedt

LOADING = 0 
VERSION = "Alpha 1.0.0"
bg_color = [30 for i in range(3)]
scrollY = 0
zoom = 1
DEBUG = 0
func = 0
globals = {}
prev_link = ""
current_link = "homepage.rizz"
domains = []
load_count = 0
script_string = ""

font = c.pygame.font.SysFont("consolas", 15)

print(dt.timestamp(dt.now()))
print(timedt(minutes=30).total_seconds())

c.window(1280, 690, title = f"Browser - {VERSION}", smallest_window_sizes=(1280, 690), icon="assets/icon.png")

SCREEN = c.screen_size()

def cache_domains():
    global domains
    w.domains_cache = dt.timestamp(dt.now())
    domains = u.get_domains("domains.json")
    w.domains = domains
    print("cacheng domains")

def load_browsing_page(domain_loading, search):
    link = f"gbrowser.rizzler/search/{search}"
    global pageObjects, page_margins, current_name, script, current_link, LOADING, prev_link, domains, load_count, script_string
    LOADING = 1
    load_count += 1
    gsite = f"""
<root>
    <page margins = "[200, 40]" name="Gbrowser"/>
    <h>
    Showing results for: "{search}"
    </h>
    <newline/>

"""
    for item in domain_loading:
        gsite += f"""
    <rh color = "[60, 60, 60]"/>
    <p>
    {item["domain"]}
    </p>
    <newline/>
    <button function="load" args="{item["domain"]}"> Load </button>
"""
        
    gsite += "</root>"

    close_site()
    site_parsed = w.create_site_objects(gsite, current_link)
    pageObjects = site_parsed[0]
    page_margins = site_parsed[1]
    # page_sprites = site_parsed[2]
    script_string = w.open_link(site_parsed[2])
    script = {}
    if script_string:
        try:
            if u.strings_in_string(["shutil", "mkdir", "import"], script_string):
                raise Exception("Not allowed")
            compiled_string = compile(script_string, "<string>", "exec")
            exec(compiled_string, globals, script)
        except:
            script["loop"] = u.base_script
    else:
        script["loop"] = u.base_script
    script = u.DictToAttr(script)
    current_name = site_parsed[3]
    prev_link = current_link
    current_link = link
    LOADING = 0

def start_load(domains, search = "search"):
    thread = t.Thread(target=load_browsing_page, args=(domains, search))
    thread.start()
    return thread

def close_site():
    global zoom, scrollY, topbar
    c.get_all().clear()
    topbar = u.topbar()
    zoom = 1
    scrollY = 0

def load_site_process(site):
    global pageObjects, page_margins, current_name, script, current_link, LOADING, prev_link, fetch, domains, load_count, script_string
    if LOADING:
        print("\n\nno permission")
        return
    LOADING = 1
    load_count += 1
    link = site
    fetch, domains = w.fetch_domain(site, "domains.json")
    if not fetch:
        LOADING = 0
        return
    for item in domains:
        item.__delitem__("key")
    site = w.open_link(fetch) #change source <---<-<---<
    close_site()
    if "gbrowser.rizzler/search" in current_link:
        site_parsed = w.create_site_objects(site, "homepage.rizz")
    else:
        site_parsed = w.create_site_objects(site, current_link)
    pageObjects = site_parsed[0]
    page_margins = site_parsed[1]
    # page_sprites = site_parsed[2]
    script_string = w.open_link(site_parsed[2])
    script = {}
    if script_string:
        try:
            if u.strings_in_string(["shutil", "mkdir", "import"], script_string):
                raise Exception("Not allowed")
            compiled_string = compile(script_string, "<string>", "exec")
            exec(compiled_string, globals, script)
        except:
            script["loop"] = u.base_script
    else:
        script["loop"] = u.base_script
    script = u.DictToAttr(script)
    current_name = site_parsed[3]
    prev_link = current_link
    current_link = link
    LOADING = 0

def load_site(site):
    # try:
    #     close_site()
    # except (TypeError):
    #     pass
    thread = t.Thread(target=load_site_process, args=(site,))
    thread.start()
    return thread

globals = {"load" : load_site,
           "blit" : c.blit,
           "text" : c.text,
           "debug" : c.debug_list,
           "requests" : requests,
           "math" : math,
           "r" : u.r,
           "d" : u.domains_editor,
           "browse" : u.browse,
           "load_browser" : start_load,
           "update_domain_cache" : cache_domains,
           "frames" : c.get_frames
           }

load_site_process("homepage.rizz")

while c.loop(60, bg_color):
    c.set_title(f"GBrowser - {current_link} - {VERSION}")
    if c.is_updating_sizes():
        SCREEN = c.screen_size()
        topbar.update_sizes()
    if c.ctrl():
        zoom += 0.1 * c.get_wheel()
    else:
        scrollY -= 20 * c.get_wheel() * zoom
    zoom = max(zoom, 1)
    last = pageObjects[-1]
    scrollY = min(zoom*(last.offset[1] + last.sizes[1] + last.margin[1]*2 + page_margins[1]*2) - SCREEN[1], scrollY)
    scrollY = max(scrollY, 0)

    # Debug right here bro it's literally here

    DEBUG = c.flick(c.key_clicked(c.pygame.K_F3), DEBUG)[0]
    if DEBUG:
        c.debug_list(
            f"current site: {current_name}",
            f"scroll y: {scrollY}",
            f"zoom: {zoom}",
            f"mouse position: {c.mouse_position()}",
            f"n of sprites: {len(c.get_all())}",
            f"performance: {c.get_delta() * 100}%",
            f"loads: {load_count}",
            "script: ",
            *["    "+string for string in str(script_string).split("\n")],
            
            
            font = font,
            position=(5, 55)
        )

    # topbar.bg.set_position(c.mouse_position())
    # temporary
    # this dick lol

    events = []
    passables = {
        "inputs": {},
        "events": []
    }
    for item in pageObjects:
        event = item.update(scrollY, zoom, margins = page_margins, screen = SCREEN, page_objects = pageObjects, script = script)
        if event:
            events.append(event)
            if event["type"] == "button":
                passables["events"].append(event["id"])
            elif event["type"] == "input":
                passables["inputs"].update(
                    { event["id"] : event["input"] }
                )

    if any(events):
        for event in events:
            if event["type"] == "button":
                if event["function"] == "reload":
                    load_site(current_link)
                elif event["function"] == "load":
                    load_site(*event["args"])
                elif event["function"] == "getall":
                    for object in pageObjects:
                        if object.tag == "input":
                            passables["inputs"].update(
                                { object.id : object.input }
                            )
                            object.input = ""
                            object.selected = 0

    if c.key_clicked(c.pygame.K_F5) and not "gbrowser.rizzler/search" in current_link:
        load_site(current_link)
    if c.key_clicked(c.pygame.K_F1):
        load_site("homepage.rizz")

    loading = " | Loading..." if LOADING else ""
    t_load = topbar.update(f"{current_name} | {current_link}{loading}")
    if t_load:
        load_site(t_load)

    script.__setattr__("domains", domains)
    #try:
    result = script.loop(passables["events"], passables["inputs"], script)
    # except Exception as e:
    #     result = f"Error: {e}"
    #     script.loop = u.base_script
    #     print(result)

    pass
