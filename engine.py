import pygame
import sys
import math
import random
from typing import Callable, Optional, Union
import socket
import pickle

# ==============================================================================
"""
BV's Pygame UI Engine
A modular, reusable UI framework for my own personal applications.

Author: scoosed [Blake Verner]
Date: July 28, 2025

Classes:
    - UIManager: Orchestrates all UI elements, handling events and drawing.
    - UIElement: The base class for all other UI components.
    - Panel: A simple colored rectangle, useful as a background or container.
    - Label: Displays static or dynamic text.
    - Button: A clickable element with different visual states and an on_click callback.
    - CheckBox: A toggleable box for boolean options.
    - Slider: An interactive control to select a numeric value within a range.
    - TextInput: A field for users to enter text.
"""
# --- Theme & Constants ---
UI_THEME = {
    "font_name": "monospace",
    "font_size": 16,
    "panel_color": (30, 40, 50),
    "label_color": (230, 240, 250),
    "border_color": (80, 90, 110),
    "button_color_idle": (60, 70, 90),
    "button_color_hover": (80, 90, 110),
    "button_color_pressed": (40, 50, 70),
    "slider_track_color": (50, 60, 80),
    "slider_handle_color": (120, 130, 150),
    "checkbox_color": (50, 60, 80),
    "checkbox_checkmark_color": (180, 220, 250),
    "text_input_bg_color": (50, 60, 80),
    "text_input_border_active": (150, 160, 180),
    "tooltip_bg_color": (20, 25, 30),
    "tooltip_alpha": 220,
}

class UIElement:
    """The foundational class for all UI components."""
    def __init__(self, rect: pygame.Rect, tooltip: Optional[str] = None):
        self.rect = rect
        self.visible = True
        self.hovered = False
        self.tooltip_text = tooltip

    def handle_event(self, event: pygame.event.Event) -> None:
        if not self.visible:
            return
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)

    def update(self) -> None: pass
    def draw(self, screen: pygame.Surface) -> None: pass

class UIManager:
    """Manages a collection of UI elements, handling events and drawing."""
    def __init__(self):
        self.elements = []
        self.active_text_input = None
        self.tooltip_font = pygame.font.SysFont(UI_THEME["font_name"], 14)

    def add(self, element: UIElement) -> UIElement:
        self.elements.append(element)
        return element

    def handle_events(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.active_text_input and not self.active_text_input.rect.collidepoint(event.pos):
                self.active_text_input.is_active = False
                self.active_text_input = None
        for element in self.elements:
            element.handle_event(event)
            if isinstance(element, TextInput) and element.is_active:
                if self.active_text_input and self.active_text_input != element:
                    self.active_text_input.is_active = False
                self.active_text_input = element

    def update(self) -> None:
        for element in self.elements:
            element.update()

    def draw(self, screen: pygame.Surface) -> None:
        for element in self.elements:
            if element.visible:
                element.draw(screen)
        top_hovered_element = None
        for element in reversed(self.elements):
            if element.hovered and element.tooltip_text:
                top_hovered_element = element
                break
        if top_hovered_element:
            self._draw_tooltip(screen, top_hovered_element)

    def _draw_tooltip(self, screen: pygame.Surface, element: UIElement) -> None:
        if not element.tooltip_text: return
        padding = 5
        mouse_pos = pygame.mouse.get_pos()
        text_surf = self.tooltip_font.render(element.tooltip_text, True, UI_THEME["label_color"])
        tooltip_rect = text_surf.get_rect( topleft=mouse_pos, width=text_surf.get_width() + padding * 2, height=text_surf.get_height() + padding * 2)
        tooltip_rect.x += 15
        if tooltip_rect.right > screen.get_width(): tooltip_rect.right = screen.get_width()
        if tooltip_rect.bottom > screen.get_height(): tooltip_rect.bottom = screen.get_height()
        bg_surf = pygame.Surface(tooltip_rect.size, pygame.SRCALPHA)
        bg_surf.fill((*UI_THEME["tooltip_bg_color"], UI_THEME["tooltip_alpha"]))
        screen.blit(bg_surf, tooltip_rect)
        pygame.draw.rect(screen, UI_THEME["border_color"], tooltip_rect, 1)
        screen.blit(text_surf, (tooltip_rect.x + padding, tooltip_rect.y + padding))

class Panel(UIElement):
    def __init__(self, rect: pygame.Rect, color: tuple, border_width: int = 1, **kwargs):
        super().__init__(rect, **kwargs)
        self.color = color
        self.border_width = border_width
    def draw(self, screen: pygame.Surface) -> None:
        pygame.draw.rect(screen, self.color, self.rect)
        if self.border_width > 0:
            pygame.draw.rect(screen, UI_THEME["border_color"], self.rect, self.border_width)

class Label(UIElement):
    def __init__(self, pos: tuple, text: str, font_size: int = UI_THEME["font_size"], color: tuple = UI_THEME["label_color"], **kwargs):
        self.font = pygame.font.SysFont(UI_THEME["font_name"], font_size)
        self.color = color
        self._text = text
        self.text_surf = self.font.render(self._text, True, self.color)
        rect = self.text_surf.get_rect(topleft=pos)
        super().__init__(rect, **kwargs)
    @property
    def text(self) -> str: return self._text
    @text.setter
    def text(self, new_text: str) -> None:
        if self._text != new_text:
            self._text = new_text
            self.text_surf = self.font.render(self._text, True, self.color)
            self.rect.size = self.text_surf.get_size()
    def draw(self, screen: pygame.Surface) -> None:
        screen.blit(self.text_surf, self.rect)

class Button(UIElement):
    def __init__(self, rect: pygame.Rect, text: str, on_click: Optional[Callable] = None, **kwargs):
        super().__init__(rect, **kwargs)
        self.text = text
        self.on_click = on_click
        self.font = pygame.font.SysFont(UI_THEME["font_name"], UI_THEME["font_size"], bold=True)
        self.is_pressed = False
        self.colors = {"idle": UI_THEME["button_color_idle"], "hover": UI_THEME["button_color_hover"], "pressed": UI_THEME["button_color_pressed"]}
        self.text_surf = self.font.render(text, True, UI_THEME["label_color"])
        self.text_rect = self.text_surf.get_rect(center=self.rect.center)
    def handle_event(self, event: pygame.event.Event) -> None:
        super().handle_event(event)
        if not self.visible or not self.on_click: return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.hovered:
            self.is_pressed = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.hovered and self.is_pressed:
            self.on_click()
            self.is_pressed = False
        elif event.type == pygame.MOUSEMOTION and not self.hovered:
            self.is_pressed = False
    def draw(self, screen: pygame.Surface) -> None:
        color = self.colors["idle"]
        if self.is_pressed: color = self.colors["pressed"]
        elif self.hovered: color = self.colors["hover"]
        pygame.draw.rect(screen, color, self.rect, border_radius=5)
        pygame.draw.rect(screen, UI_THEME["border_color"], self.rect, 1, border_radius=5)
        screen.blit(self.text_surf, self.text_rect)

class CheckBox(UIElement):
    def __init__(self, pos: tuple, label: str, on_toggle: Optional[Callable[[bool], None]] = None, checked: bool = False, **kwargs):
        self.box_size = 16
        self.font = pygame.font.SysFont(UI_THEME["font_name"], UI_THEME["font_size"])
        self.label_surf = self.font.render(label, True, UI_THEME["label_color"])
        width, height = self.box_size + 5 + self.label_surf.get_width(), self.box_size
        rect = pygame.Rect(pos[0], pos[1], width, height)
        super().__init__(rect, **kwargs)
        self.box_rect = pygame.Rect(pos[0], pos[1], self.box_size, self.box_size)
        self.label_rect = self.label_surf.get_rect(centery=self.box_rect.centery, left=self.box_rect.right + 5)
        self.checked = checked
        self.on_toggle = on_toggle
    def handle_event(self, event: pygame.event.Event) -> None:
        super().handle_event(event)
        if not self.visible: return
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.hovered:
            self.checked = not self.checked
            if self.on_toggle: self.on_toggle(self.checked)
    def draw(self, screen: pygame.Surface) -> None:
        pygame.draw.rect(screen, UI_THEME["checkbox_color"], self.box_rect, border_radius=3)
        border_color = UI_THEME["text_input_border_active"] if self.hovered else UI_THEME["border_color"]
        pygame.draw.rect(screen, border_color, self.box_rect, 1, border_radius=3)
        if self.checked:
            points = [(self.box_rect.left + 3, self.box_rect.centery), (self.box_rect.centerx - 1, self.box_rect.bottom - 4), (self.box_rect.right - 3, self.box_rect.top + 4)]
            pygame.draw.lines(screen, UI_THEME["checkbox_checkmark_color"], False, points, 2)
        screen.blit(self.label_surf, self.label_rect)

class Slider(UIElement):
    def __init__(self, rect: pygame.Rect, min_val: float, max_val: float, on_change: Optional[Callable[[float], None]] = None, initial_val: Optional[float] = None, **kwargs):
        super().__init__(rect, **kwargs)
        self.min_val, self.max_val = min_val, max_val
        self.value = initial_val if initial_val is not None else min_val
        self.on_change = on_change
        self.is_dragging = False
        self.handle_width = 10
        self.handle_rect = pygame.Rect(0, 0, self.handle_width, self.rect.height)
        self._update_handle_pos()
    def _update_handle_pos(self) -> None:
        ratio = (self.value - self.min_val) / (self.max_val - self.min_val)
        self.handle_rect.centerx = self.rect.x + ratio * self.rect.width
        self.handle_rect.centery = self.rect.centery
    def _update_value_from_pos(self, x_pos: int) -> None:
        ratio = max(0.0, min(1.0, (x_pos - self.rect.x) / self.rect.width))
        new_value = self.min_val + ratio * (self.max_val - self.min_val)
        if self.value != new_value:
            self.value = new_value
            if self.on_change: self.on_change(self.value)
        self._update_handle_pos()
    def handle_event(self, event: pygame.event.Event) -> None:
        super().handle_event(event)
        if not self.visible: return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.hovered:
            self.is_dragging = True
            self._update_value_from_pos(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1: self.is_dragging = False
        elif event.type == pygame.MOUSEMOTION and self.is_dragging: self._update_value_from_pos(event.pos[0])
    def draw(self, screen: pygame.Surface) -> None:
        track_rect = self.rect.copy(); track_rect.height = 6; track_rect.centery = self.rect.centery
        pygame.draw.rect(screen, UI_THEME["slider_track_color"], track_rect, border_radius=3)
        handle_color = UI_THEME["text_input_border_active"] if self.is_dragging or self.hovered else UI_THEME["slider_handle_color"]
        pygame.draw.rect(screen, handle_color, self.handle_rect, border_radius=3)

class TextInput(UIElement):
    def __init__(self, rect: pygame.Rect, on_submit: Optional[Callable[[str], None]] = None, initial_text: str = "", **kwargs):
        super().__init__(rect, **kwargs); self.font = pygame.font.SysFont(UI_THEME["font_name"], UI_THEME["font_size"])
        self.text, self.is_active, self.on_submit = initial_text, False, on_submit; self.cursor_visible, self.cursor_timer = True, 0
    def handle_event(self, event: pygame.event.Event) -> None:
        super().handle_event(event)
        if not self.visible: return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: self.is_active = self.hovered
        if self.is_active and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                if self.on_submit: self.on_submit(self.text)
                self.is_active = False
            elif event.key == pygame.K_BACKSPACE: self.text = self.text[:-1]
            else: self.text += event.unicode
    def update(self) -> None:
        self.cursor_timer += 1
        if self.cursor_timer > 30: self.cursor_visible = not self.cursor_visible; self.cursor_timer = 0
    def draw(self, screen: pygame.Surface) -> None:
        pygame.draw.rect(screen, UI_THEME["text_input_bg_color"], self.rect, border_radius=3)
        border_color = UI_THEME["text_input_border_active"] if self.is_active else UI_THEME["border_color"]
        pygame.draw.rect(screen, border_color, self.rect, 1, border_radius=3)
        text_surf = self.font.render(self.text, True, UI_THEME["label_color"]); screen.blit(text_surf, (self.rect.x + 5, self.rect.y + 5))
        if self.is_active and self.cursor_visible:
            cursor_x = self.rect.x + 5 + text_surf.get_width(); cursor_y = self.rect.y + 5
            pygame.draw.line(screen, UI_THEME["label_color"], (cursor_x, cursor_y), (cursor_x, cursor_y + self.font.get_height()), 1)

# ==============================================================================
# /// 3D ENGINE ///
# ==============================================================================

# --- 3D Engine Constants ---
WIDTH, HEIGHT = 1920, 1080
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
GRASS_GREEN = (124, 252, 0)
BLUE = (0, 0, 255)
FPS = 60
NEAR_CLIP_PLANE = -0.1

prefixes = [
    "Player", "User", "Guest", "Anon", "Test", "Idle", "Sample",
    "Empty", "New", "Generic", "Temp", "Red", "Slot", "Name", "Unregistered",
    "Spawned", "Auto", "Pending", "Grey", "Backup", "Silent", "System",
    "Account", "Neutral", "Shadow", "Unknown", "Basic", "Placeholder"
]

suffixes = [
    "User", "Name", "Slot", "Avatar", "Guest", "Account", "Instance", "Login",
    "Profile", "Entry", "Person", "Node", "Bot", "Entity", "Client", "Shell",
    "Unit", "Object", "Default", "Member", "Operator", "Agent", "Process",
    "Echo", "Device", "Alias", "Draft", "Session", "Copy", "Mirror"
]

class Network:
    """ Handles client-side communication with the server. """
    def __init__(self, server_ip: str, port: int = 5555):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_ip = server_ip
        self.port = port
        self.addr = (self.server_ip, self.port)
        self.player_id = None

    def get_player_id(self) -> int:
        """Returns the ID assigned by the server."""
        return self.player_id

    def connect(self, name: str) -> int:
        """ Connects to the server, sends the player name, and retrieves the player ID. """
        try:
            self.client.connect(self.addr)
            # The first piece of data received is the player ID
            self.player_id = pickle.loads(self.client.recv(2048))
            self.client.send(pickle.dumps(name))
            return self.player_id
        except socket.error as e:
            print(f"Connection Error: {e}")
            return None

    def send(self, data: dict) -> dict:
        """Sends data to the server and returns the response."""
        try:
            self.client.send(pickle.dumps(data))
            return pickle.loads(self.client.recv(2048 * 4))
        except socket.error as e:
            print(e)
            return None
            
    def disconnect(self): self.client.close()

class Cube:
    def __init__(self, position=(0, 0, 0), size=(1, 1, 1), color=WHITE):
        self.position = list(position)
        self.size = (size, size, size) if isinstance(size, (int, float)) else size
        self.color = color
        sx, sy, sz = self.size[0] / 2, self.size[1] / 2, self.size[2] / 2
        self.base_vertices = [(-sx, -sy, -sz), (sx, -sy, -sz), (sx, sy, -sz), (-sx, sy, -sz), (-sx, -sy, sz), (sx, -sy, sz), (sx, sy, sz), (-sx, sy, sz)]
        self.faces = [(3, 2, 1, 0), (4, 5, 6, 7), (7, 3, 0, 4), (2, 6, 5, 1), (7, 6, 2, 3), (0, 1, 5, 4)]
    def get_transformed_vertices(self):
        px, py, pz = self.position
        return [(px + x, py + y, pz + z) for x, y, z in self.base_vertices]

class Camera:
    def __init__(self, position=(0, 5, -15), yaw=-90, pitch=0):
        self.position = list(position)
        self.yaw, self.pitch = yaw, pitch
        self.target = None; self.distance, self.min_distance, self.max_distance = 15, 5, 40
        self.zoom_speed = 1.0; self.pivot_point = [0, 5, 0]; self.lerp_factor = 0.08
    def update(self, mouse_dx, mouse_dy):
        sensitivity = 0.2
        self.yaw += mouse_dx * sensitivity
        self.pitch -= mouse_dy * sensitivity
        self.pitch = max(-89, min(89, self.pitch))
        if self.target:
            target_pivot_y = self.target.position[1] + 2.0
            self.pivot_point[0] += (self.target.position[0] - self.pivot_point[0]) * self.lerp_factor
            self.pivot_point[1] += (target_pivot_y - self.pivot_point[1]) * self.lerp_factor
            self.pivot_point[2] += (self.target.position[2] - self.pivot_point[2]) * self.lerp_factor
            rad_yaw, rad_pitch = math.radians(self.yaw), math.radians(self.pitch)
            offset_x = self.distance * math.cos(rad_pitch) * math.cos(rad_yaw)
            offset_y = self.distance * math.sin(rad_pitch)
            offset_z = self.distance * math.cos(rad_pitch) * math.sin(rad_yaw)
            self.position = [self.pivot_point[0] - offset_x, self.pivot_point[1] - offset_y, self.pivot_point[2] - offset_z]

class Engine3D:
    def __init__(self, width, height):
        pygame.init(); self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("3D Game"); self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 18)
        self.nametag_font = pygame.font.SysFont("Arial", 14, bold=True)

        self.game_state, self.running = 'main_menu', True
        self.net, self.players, self.player_id = None, {}, -1
        self.name_input, self.ip_input = None, None
        
        self.default_name = f"{random.choice(prefixes)}{random.choice(suffixes)}"

        self.ui_manager = UIManager(); self._setup_main_menu()

        self.gravity, self.player_y_velocity, self.is_grounded, self.jump_strength = 0.035, 0, False, 0.8
        self.player_x_velocity, self.player_z_velocity, self.friction = 0, 0, 0.9
        self.player = Cube(position=(0, 5, 0), size=2, color=BLUE)
        self.camera = Camera(); self.camera.target = self.player; self.camera.pivot_point = list(self.player.position)
        #self.platforms = [Cube((0, -2, 0), (150, 1, 150), GRASS_GREEN), Cube((12, 2.5, 12), 5), Cube((-12, 2.5, 12), 5), Cube((0, 5, -15), (8, 1, 8))]
        
        self.static_platforms = [Cube((0, -2, 0), (150, 1, 150), GRASS_GREEN)]
        self.server_cubes = []; self.world_initialized = False

    def _setup_main_menu(self):
        self.ui_manager.elements.clear(); cx, cy = WIDTH // 2, HEIGHT // 2
        self.ui_manager.add(Label((0, cy - 150), "3D GAME", font_size=48)).rect.centerx = cx
        self.ui_manager.add(Button(pygame.Rect(cx - 150, cy - 25, 300, 50), "Multiplayer", on_click=self.show_multiplayer_menu, tooltip="Connect to a server to play with others."))
        self.ui_manager.add(Button(pygame.Rect(cx - 150, cy + 35, 300, 50), "Quit", on_click=self.quit_game, tooltip="Exit the application."))

    def _setup_multiplayer_menu(self):
        self.ui_manager.elements.clear(); cx, cy = WIDTH // 2, HEIGHT // 2
        self.ui_manager.add(Label((0, cy - 150), "MULTIPLAYER", font_size=32)).rect.centerx = cx
        
        self.ui_manager.add(Label((cx - 150, cy - 95), "Name:", font_size=20))
        self.name_input = self.ui_manager.add(TextInput(pygame.Rect(cx - 150, cy - 70, 300, 30), initial_text=self.default_name))

        self.ui_manager.add(Label((cx - 150, cy - 35), "Server IP:", font_size=20))
        self.ip_input = self.ui_manager.add(TextInput(pygame.Rect(cx - 150, cy - 10, 300, 30), initial_text="127.0.0.1"))
        
        self.ui_manager.add(Button(pygame.Rect(cx - 150, cy + 40, 300, 50), "Connect", on_click=self.connect_to_server, tooltip="Attempt to connect to the server."))
        self.ui_manager.add(Button(pygame.Rect(cx - 150, cy + 100, 300, 50), "Back", on_click=self.return_to_menu, tooltip="Return to the main menu."))

    def show_multiplayer_menu(self): self.game_state = 'multiplayer_menu'; self._setup_multiplayer_menu()

    def connect_to_server(self):
        ip = self.ip_input.text
        name = self.name_input.text
        if not name.strip():
            print("Name cannot be empty.")
            return
            
        print(f"Connecting to {ip} as {name}...")
        self.net = Network(ip)
        player_id = self.net.connect(name)
        
        if player_id is not None:
            self.player_id = player_id
            print(f"Successfully connected to {ip}! Player ID is {self.player_id}")
            self.game_state = 'in_game_multiplayer'
            pygame.mouse.set_visible(False); pygame.event.set_grab(True)
        else:
            print("Failed to connect.")
            self.net = None

    def return_to_menu(self):
        if self.net: self.net.disconnect(); self.net = None
        self.game_state = 'main_menu'; pygame.mouse.set_visible(True); pygame.event.set_grab(False)
        self._setup_main_menu()
        self.world_initialized = False; self.server_cubes.clear()

    def quit_game(self): self.running = False
    def check_collision(self, c1, c2):
        x1, y1, z1 = c1.position; w1, h1, d1 = c1.size; x2, y2, z2 = c2.position; w2, h2, d2 = c2.size
        return (x1 - w1/2 < x2 + w2/2 and x1 + w1/2 > x2 - w2/2 and y1 - h1/2 < y2 + h2/2 and y1 + h1/2 > y2 - h2/2 and z1 - d1/2 < z2 + d2/2 and z1 + d1/2 > z2 - d2/2)
    
    def transform_world_to_camera_space(self, vertices):
        transformed = []
        for point in vertices:
            # 1. Translate point relative to camera
            tx, ty, tz = point[0] - self.camera.position[0], point[1] - self.camera.position[1], point[2] - self.camera.position[2]
            # 2. Rotate point around camera
            rad_yaw, rad_pitch = math.radians(-self.camera.yaw - 90), math.radians(-self.camera.pitch)
            cos_y, sin_y = math.cos(rad_yaw), math.sin(rad_yaw); cos_p, sin_p = math.cos(rad_pitch), math.sin(rad_pitch)
            x_rot = tx * cos_y - tz * sin_y; z_rot = tx * sin_y + tz * cos_y
            y_rot = ty * cos_p - z_rot * sin_p; z_rot_pitch = ty * sin_p + z_rot * cos_p
            transformed.append((x_rot, y_rot, z_rot_pitch))
        return transformed

    def project_point(self, x, y, z):
        if z >= 0: return None
        factor = 400 / -z; return (int(x * factor + WIDTH / 2), int(-y * factor + HEIGHT / 2))
    def clip_against_near_plane(self, poly_verts):
        clipped = [];
        for i in range(len(poly_verts)):
            p1, p2 = poly_verts[i], poly_verts[(i + 1) % len(poly_verts)]; p1_in, p2_in = p1[2] < NEAR_CLIP_PLANE, p2[2] < NEAR_CLIP_PLANE
            if p1_in and p2_in: clipped.append(p2)
            elif p1_in or p2_in:
                if p2[2] - p1[2] == 0: continue
                t = (NEAR_CLIP_PLANE - p1[2]) / (p2[2] - p1[2]); ix, iy = p1[0] + t * (p2[0] - p1[0]), p1[1] + t * (p2[1] - p1[1])
                if p1_in: clipped.append((ix, iy, NEAR_CLIP_PLANE))
                else: clipped.extend([(ix, iy, NEAR_CLIP_PLANE), p2])
        return clipped
    
    def _handle_game_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and self.is_grounded: self.player_y_velocity = self.jump_strength; self.is_grounded = False
            elif event.key == pygame.K_ESCAPE: self.return_to_menu()
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4: self.camera.distance -= self.camera.zoom_speed
            elif event.button == 5: self.camera.distance += self.camera.zoom_speed

    def _update_physics_and_input(self):
        keys = pygame.key.get_pressed(); mouse_dx, mouse_dy = pygame.mouse.get_rel(); self.camera.update(mouse_dx, mouse_dy)
        self.camera.distance = max(self.camera.min_distance, min(self.camera.max_distance, self.camera.distance))
        accel = 0.05; rad_yaw = math.radians(self.camera.yaw)
        if keys[pygame.K_w]: self.player_x_velocity += math.cos(rad_yaw) * accel; self.player_z_velocity += math.sin(rad_yaw) * accel
        if keys[pygame.K_s]: self.player_x_velocity -= math.cos(rad_yaw) * accel; self.player_z_velocity -= math.sin(rad_yaw) * accel
        if keys[pygame.K_a]: self.player_x_velocity += math.sin(rad_yaw) * accel; self.player_z_velocity -= math.cos(rad_yaw) * accel
        if keys[pygame.K_d]: self.player_x_velocity -= math.sin(rad_yaw) * accel; self.player_z_velocity += math.cos(rad_yaw) * accel
        self.player_x_velocity *= self.friction; self.player_z_velocity *= self.friction
        if abs(self.player_x_velocity) < 0.001: self.player_x_velocity = 0
        if abs(self.player_z_velocity) < 0.001: self.player_z_velocity = 0
        old_x, old_z = self.player.position[0], self.player.position[2]
        all_platforms = self.static_platforms + self.server_cubes
        self.player.position[0] += self.player_x_velocity
        for p in all_platforms:
            if self.check_collision(self.player, p): self.player.position[0] = old_x; self.player_x_velocity = 0; break
        
        if self.game_state == 'in_game_multiplayer':
            for p_id, p_data in self.players.items():
                if p_id != self.player_id:
                    other_player_cube = Cube(position=p_data['pos'], size=self.player.size)
                    if self.check_collision(self.player, other_player_cube):
                        self.player.position[0] = old_x
                        self.player_x_velocity = 0
                        break
            
        self.player.position[2] += self.player_z_velocity
        for p in all_platforms:
            if self.check_collision(self.player, p): self.player.position[2] = old_z; self.player_z_velocity = 0; break
        
        if self.game_state == 'in_game_multiplayer':
            for p_id, p_data in self.players.items():
                if p_id != self.player_id:
                    other_player_cube = Cube(position=p_data['pos'], size=self.player.size)
                    if self.check_collision(self.player, other_player_cube):
                        self.player.position[2] = old_z
                        self.player_z_velocity = 0
                        break
        
        self.player_y_velocity -= self.gravity; self.player.position[1] += self.player_y_velocity
        self.is_grounded = False
        for p in all_platforms:
            if self.check_collision(self.player, p):
                if self.player_y_velocity <= 0:
                    self.player.position[1] = p.position[1] + p.size[1]/2 + self.player.size[1]/2; self.player_y_velocity = 0; self.is_grounded = True
                else:
                    self.player.position[1] = p.position[1] - p.size[1]/2 - self.player.size[1]/2; self.player_y_velocity = 0
                break
        
        if self.game_state == 'in_game_multiplayer':
            for p_id, p_data in self.players.items():
                if p_id != self.player_id:
                    other_player_cube = Cube(position=p_data['pos'], size=self.player.size)
                    if self.check_collision(self.player, other_player_cube):
                        if self.player_y_velocity <= 0:
                            self.player.position[1] = other_player_cube.position[1] + other_player_cube.size[1]/2 + self.player.size[1]/2
                            self.player_y_velocity = 0
                            self.is_grounded = True
                        else:
                            self.player.position[1] = other_player_cube.position[1] - other_player_cube.size[1]/2 - self.player.size[1]/2
                            self.player_y_velocity = 0
                        break

    def _draw_scene(self, objects_to_draw):
        self.screen.fill(BLACK); all_faces = []
        for obj in objects_to_draw:
            cam_space_verts = self.transform_world_to_camera_space(obj.get_transformed_vertices())
            for face_indices in obj.faces:
                face_verts = [cam_space_verts[i] for i in face_indices]
                if face_verts: all_faces.append({"depth": min(v[2] for v in face_verts), "verts": face_verts, "color": obj.color})
        all_faces.sort(key=lambda f: f["depth"])
        for face in all_faces:
            v0, v1, v2 = face["verts"][0], face["verts"][1], face["verts"][2]
            vec1 = (v1[0]-v0[0], v1[1]-v0[1], v1[2]-v0[2]); vec2 = (v2[0]-v0[0], v2[1]-v0[1], v2[2]-v0[2])
            nx, ny, nz = vec1[1]*vec2[2] - vec1[2]*vec2[1], vec1[2]*vec2[0] - vec1[0]*vec2[2], vec1[0]*vec2[1] - vec1[1]*vec2[0]
            if (nx*v0[0] + ny*v0[1] + nz*v0[2]) >= 0: continue
            clipped_face = self.clip_against_near_plane(face["verts"]);
            if len(clipped_face) < 3: continue
            projected = [self.project_point(*v) for v in clipped_face];
            if None in projected: continue
            mag = math.sqrt(nx**2+ny**2+nz**2);
            if mag == 0: continue
            light = (0.577, -0.577, -0.577); intensity = (nx/mag * light[0] + ny/mag * light[1] + nz/mag * light[2])
            shading = max(0.1, intensity) * 0.7 + 0.3; shaded_color = tuple(min(255, int(c * shading)) for c in face["color"])
            pygame.draw.polygon(self.screen, shaded_color, projected)
            pygame.draw.polygon(self.screen, BLACK, projected, 1)

    def _draw_nametags(self):
        for p_id, p_data in self.players.items():
            # Define the 3D position for the nametag (above the player's cube)
            pos3d = p_data['pos']
            name = p_data['name']
            nametag_world_pos = [(pos3d[0], pos3d[1] + 2.0, pos3d[2])]

            # Transform this 3D point into camera space
            nametag_camera_pos = self.transform_world_to_camera_space(nametag_world_pos)[0]

            # Project the camera-space point to 2D screen coordinates
            screen_pos = self.project_point(*nametag_camera_pos)
            
            # Only draw if the point is on screen
            if screen_pos:
                text_surf = self.nametag_font.render(name, True, WHITE)
                text_rect = text_surf.get_rect(center=screen_pos)
                
                # Draw a semi-transparent background for readability
                bg_rect = text_rect.inflate(8, 4)
                bg_surf = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
                bg_surf.fill((20, 20, 40, 150))
                self.screen.blit(bg_surf, bg_rect)
                
                self.screen.blit(text_surf, text_rect)

    def run(self):
        while self.running:
            self.clock.tick(FPS); events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT: self.running = False
                if self.game_state.startswith('in_game'): self._handle_game_input(event)
                else: self.ui_manager.handle_events(event)
            
            if self.game_state in ['main_menu', 'multiplayer_menu']:
                self.ui_manager.update(); self.screen.fill((10, 20, 30)); self.ui_manager.draw(self.screen)
            
            elif self.game_state == 'in_game_multiplayer':
                self._update_physics_and_input()
                if self.net:
                    server_response = self.net.send({'pos': self.player.position})
                    if server_response:
                        self.players = server_response.get('players', {})
                        
                        if not self.world_initialized and 'cubes' in server_response:
                            self.server_cubes.clear()
                            for cube_data in server_response['cubes']:
                                self.server_cubes.append(Cube(
                                    position=cube_data['pos'],
                                    size=cube_data['size'],
                                    color=cube_data['color']
                                ))
                            self.world_initialized = True
                    else:
                        print("Connection to server lost."); self.return_to_menu()
                
                multiplayer_objects = self.static_platforms + self.server_cubes
                for p_id, p_data in self.players.items():
                    if p_id != self.player_id:
                        multiplayer_objects.append(Cube(position=p_data['pos'], size=2, color=p_data['color']))
                
                if self.player_id in self.players: self.player.color = self.players[self.player_id]['color']
                multiplayer_objects.append(self.player)
                
                self._draw_scene(multiplayer_objects)
                self._draw_nametags()
                
                my_name = self.players.get(self.player_id, {}).get('name', '')
                info_text = self.font.render(f"Connected as {my_name} | Exit: ESC", True, WHITE)
                self.screen.blit(info_text, (10, 10))

            pygame.display.flip()

        pygame.quit(); sys.exit()

if __name__ == '__main__':
    engine = Engine3D(WIDTH, HEIGHT)
    engine.run()