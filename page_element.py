import pygame_canvas as c
import web_utils as w
from ast import literal_eval
from utils import replace_placeholders as rep
import re
from utils import clipboard

c.pygame.font.init()

try:
    font_paragraph = c.pygame.font.SysFont("arial", 18*3)
    font_header = c.pygame.font.SysFont("arial", 35*3)
    #font_header.set_bold(1)
    font_mono = c.pygame.font.SysFont("Consolas", 18*3)
except FileNotFoundError:
    font_paragraph = c.pygame.Font(None, 25*3)
    font_header = c.pygame.Font(None, 50*3)
    font_header.set_bold(1)
    font_mono = c.pygame.Font(None, 25*3)

def render_scaled_text(text, scale_factor, font, color):
    text_surface = font.render(text, True, color)
    scaled_surface = c.pygame.transform.smoothscale(text_surface, (int(text_surface.get_width() * scale_factor), int(text_surface.get_height() * scale_factor)))
    return scaled_surface

class Element():
    def __init__(self, item, last) -> None:
        self.tag = item["tag"]
        self.margin = list(literal_eval(item["attr"]["margins"]))
        self.position = 0,0
        self.sprite = None
        
    def update(self, scrollY, zoom, margins, **kw):
        self.position = (self.offset[0] + self.margin[0]) * zoom + margins[0], (self.offset[1] + self.margin[1]) * zoom - scrollY + margins[1] + 50
    
    def get_sprite(self):
        if self.sprite:
            return self.sprite

class br(Element):
    def __init__(self, item, last) -> None:
        super().__init__(item, last)
        try:
            self.offset = 0, last.offset[1] + last.sizes[1] + last.margin[1]*2 + 1
        except AttributeError:
            self.offset = 0,0
        self.margin = 0,0
        self.sizes = 0,0

class nbr(Element):
    def __init__(self, item, last) -> None:
        super().__init__(item, last)
        try:
            self.offset = last.offset[0] + last.sizes[0] + last.margin[0]*2, 0
            if self.offset[0]:
                self.offset = self.offset[0], last.offset[1]
            else:
                self.offset = self.offset[0], last.offset[1] + last.margin[1]*2
        except AttributeError:
            self.offset = 0,0
        self.margin = 0,0
        self.sizes = 0,0

class image(nbr):
    def __init__(self, item, last) -> None:
        super().__init__(item, last)
        attr = item["attr"]
        self.sprite = c.sprite((w.get_image(attr["link"], attr["width"], attr["height"], attr["scale"]),))
        self.sprite.update()
        self.sizes = self.sprite.get_sizes()

    def update(self, scrollY, zoom, **kw):
        margins = kw["margins"]
        super().update(scrollY, zoom, margins)
        self.sprite.set_position(self.position)
        self.sprite.set_scale(zoom * 100)

class text(br):
    def __init__(self, item, text, last) -> None:
        super().__init__(item, last)
        attr = item["attr"]
        self.text = text
        font = attr["font"]
        if font:
            self.font: c.pygame.Font = c.pygame.font.SysFont(font, int(attr["scale"]))
            self.font.set_bold(attr["bold"])
        else:
            self.font: c.pygame.Font = font_header if item["tag"] == "h" else font_paragraph
        try:
            self.color = list(literal_eval(attr["color"]))
        except TypeError:
            self.color = [255, 255, 255]
        self.sizes = render_scaled_text(self.text, 1 / 3, self.font, self.color).get_size()
    
    def update(self, scrollY, zoom, **kw):
        super().update(scrollY, zoom, kw["margins"])
        c.blit(render_scaled_text(rep(self.text, kw["script"]), zoom / 3, self.font, self.color), self.position)
        
class newLine(br):
    def __init__(self, item, last) -> None:
        super().__init__(item, last)
        self.offset = self.offset[0], self.offset[1] + 25

class button(nbr):
    def __init__(self, item, last) -> None:
        super().__init__(item, last)
        attr = item["attr"]
        self.function = attr["function"]
        self.args = attr["args"].split(",")
        self.text = render_scaled_text(item["content"], 1/3, font_paragraph, color="white")
        sizex, sizey = self.text.get_size()
        self.text = item["content"]
        self.id = attr["id"]
        self.sprite = c.sprite((c.rectangle(sizex + 20, sizey + 20, list(literal_eval(attr["color"]))),))
        self.sizes = self.sprite.get_sizes()
        self.margin = list(literal_eval(attr["margins"]))
    
    def update(self, scrollY, zoom, **kw):
        super().update(scrollY, zoom, kw["margins"])
        self.sprite.set_position(self.position)
        self.sprite.brightness = 255 - self.sprite.touching_mouse() * 55
        self.sprite.set_scale(zoom * 100)
        c.blit(render_scaled_text(self.text, zoom / 3, font_paragraph, color="white"), (self.position[0] + 10*zoom, self.position[1] + 10*zoom))
        
        if self.sprite.clicked():
            return {"type" : "button", "function" : self.function, "args" : self.args, "id" : self.id}
            
class rh(newLine):
    def __init__(self, item, last) -> None:
        super().__init__(item, last)
        attr = item["attr"]
        self.color = literal_eval(attr["color"])
        self.thickness = int(attr["thickness"])
        self.margin = literal_eval(attr["margins"])
        self.created = 0
        self.sizes = 0,25

    def update(self, scrollY, zoom, **kw):
        margins = kw["margins"]
        screen = kw["screen"]
        super().update(scrollY, zoom, margins)
        self.position1 = self.position[0], self.position[1]
        self.position2 = self.position[0] - margins[0]*2 + screen[0] - self.margin[0]*2, self.position[1]
        if c.is_updating_sizes() or not self.created:
            self.created = 1
            if self.position2[0] - self.position1[0] > 1:
                self.rectangle = c.rectangle(self.position2[0] - self.position1[0], self.thickness, self.color)
            else:
                self.rectangle = c.rectangle(0,0,"white")
        c.blit(self.rectangle, self.position1)
    
class input_box(nbr):
    def __init__(self, item, last) -> None:
        super().__init__(item, last)
        attr = item["attr"]
        sizer = max(len(item["content"]), int(attr["width"]))
        self.text = render_scaled_text("g" * sizer, 1/3, font_mono, color="white")
        sizex, sizey = self.text.get_size()
        self.text = item["content"]
        self.textlen = sizer-1
        self.id = attr["id"]
        self.sprite = c.sprite((c.rectangle(sizex + 10, sizey + 10, list(literal_eval(attr["color"]))),))
        self.sizes = self.sprite.get_sizes()
        self.margin = list(literal_eval(attr["margins"]))
        self.selected = 0
        self.input = ""
        self.canDeploy = int(attr["canDeploy"])
    
    def update(self, scrollY, zoom, **kw):
        margins = kw["margins"]
        super().update(scrollY, zoom, margins)
        self.sprite.set_position(self.position)
        self.sprite.brightness = 255 - self.sprite.touching_mouse() * 55
        self.sprite.set_scale(zoom * 100)
        self.selected, flicking = c.flick(self.sprite.clicked(), self.selected)
        if self.selected:
            if flicking:
                for obj in list(filter(lambda x: not x is self, kw["page_objects"])):
                    if obj.tag == "input":
                        obj.selected = 0
            key = c.get_clicked_key()
            if key:
                if key == 127:
                    self.input = ""
                elif key == 8:
                    if c.ctrl():
                        self.input = " ".join(self.input.split(" ")[:-1])
                    else:
                        self.input = self.input[:-1]
                elif c.ctrl():
                    if key == c.pygame.K_c:
                        clipboard.copy(self.input)
                    elif key == c.pygame.K_v:
                        self.input += clipboard.paste()
                elif key == c.pygame.K_RETURN and int(self.canDeploy):
                    input = self.input
                    self.input = ""
                    self.selected = 0
                    return {"type" : "input", "input" : ''.join(c for c in input if c.isprintable()), "id" : self.id}
                elif key == c.pygame.K_ESCAPE:
                    self.selected = 0
                else:
                    try:
                        uni = c.get_clicked_unicode()
                        self.input = ''.join(c for c in self.input + uni if c.isprintable())
                    except ValueError:
                        pass                        
        c.blit(
            render_scaled_text(self.input[-self.textlen:] + ("_" if self.selected and (not c.get_frames() % 30 > 15) else ""), zoom / 3, font_mono, color="white"),
            (self.position[0] + 5*zoom, self.position[1] + 7*zoom)
        )
        if not any(self.input):
            c.blit(render_scaled_text(self.text, zoom / 3, font_mono, color=[100 for _ in range(3)]), (self.position[0] + 5*zoom, self.position[1] + 7*zoom))