import tkinter as tk
from circuit_utils import snap, transform_coords

class Terminal:
    def __init__(self, name, x, y):
        self.name = name     # 元件內部的名稱 (如 D, G, S, n1)
        self.rel_x = x
        self.rel_y = y
        self.custom_net_name = "" # 使用者自定義的外部節點名稱 (如 Vin)

class Component:
    _counts = {}

    def __init__(self, canvas, x, y, prefix):
        self.canvas = canvas
        self.x = snap(x)
        self.y = snap(y)
        self.rotation = 0
        self.mirror = False
        self.id = id(self)
        self.tags = f"comp_{self.id}"
        
        if prefix not in Component._counts:
            Component._counts[prefix] = 0
        Component._counts[prefix] += 1
        self.name = f"{prefix}{Component._counts[prefix]}"
        
        self.value = "1k"
        self.shape_lines = []
        self.terminals = [] 
        self.hitbox_size = (40, 40)

    def setup_terminals(self):
        pass

    def get_abs_terminals(self):
        """回傳 List of (Terminal_Object, abs_x, abs_y)"""
        abs_terms = []
        for term in self.terminals:
            pts = transform_coords([(term.rel_x, term.rel_y)], self.x, self.y, self.rotation, self.mirror)
            # 注意：這裡回傳 term 物件本身，以便存取 custom_net_name
            abs_terms.append((term, pts[0][0], pts[0][1]))
        return abs_terms

    def update_visuals(self):
        self.canvas.delete(self.tags)
        self.draw()

    def draw(self):
        # 1. Hitbox
        hw, hh = self.hitbox_size[0]/2, self.hitbox_size[1]/2
        self.canvas.create_rectangle(self.x - hw, self.y - hh, self.x + hw, self.y + hh, 
                                     fill="white", outline="", tags=self.tags)

        # 2. Shape
        for p1, p2 in self.shape_lines:
            t_points = transform_coords([p1, p2], self.x, self.y, self.rotation, self.mirror)
            (x1, y1), (x2, y2) = t_points
            self.canvas.create_line(x1, y1, x2, y2, tags=self.tags, width=2, fill="black")
        
        # 3. Terminals
        for term_obj, tx, ty in self.get_abs_terminals():
            r = 3
            self.canvas.create_oval(tx-r, ty-r, tx+r, ty+r, fill="red", outline="red", tags=self.tags)
            # 如果有自定義名稱，顯示在端點旁
            if term_obj.custom_net_name:
                self.canvas.create_text(tx, ty-10, text=term_obj.custom_net_name, fill="brown", font=("Arial", 6), tags=self.tags)

        self.draw_text()
        
        # 4. 優化：確保元件在 Grid 之上
        self.canvas.tag_raise(self.tags)

    def draw_text(self):
        self.canvas.create_text(self.x, self.y + 30, text=f"{self.name}\n{self.value}", tags=self.tags, font=("Arial", 8))

    def rotate(self):
        self.rotation = (self.rotation + 90) % 360
        self.update_visuals()

    def flip(self):
        self.mirror = not self.mirror
        self.update_visuals()

    def edit_properties(self):
        # 通用屬性
        labels = ["Name", "Value"]
        defaults = [self.name, self.value]
        
        # 動態加入所有端點的命名欄位
        for term in self.terminals:
            labels.append(f"Node ({term.name})")
            defaults.append(term.custom_net_name)

        self.open_property_dialog(labels, defaults, self.apply_properties)

    def apply_properties(self, values):
        # 寫回基本屬性
        if values[0]: self.name = values[0]
        if values[1]: self.value = values[1]
        
        # 寫回端點屬性 (從 index 2 開始)
        for i, term in enumerate(self.terminals):
            if i + 2 < len(values):
                term.custom_net_name = values[i+2]

        self.update_visuals()

    def open_property_dialog(self, labels, defaults, callback):
        dialog = tk.Toplevel(self.canvas.winfo_toplevel())
        dialog.title("Edit Properties")
        
        entries = []
        for i, label_text in enumerate(labels):
            tk.Label(dialog, text=label_text).grid(row=i, column=0, padx=10, pady=5, sticky="e")
            entry = tk.Entry(dialog)
            entry.insert(0, str(defaults[i]))
            entry.grid(row=i, column=1, padx=10, pady=5, sticky="w")
            entries.append(entry)
            
        def on_ok(event=None):
            result = [e.get() for e in entries]
            callback(result)
            dialog.destroy()
            
        btn = tk.Button(dialog, text="OK", command=on_ok, bg="lightblue", width=10)
        btn.grid(row=len(labels), column=0, columnspan=2, pady=20)
        dialog.bind('<Return>', on_ok)
        
        dialog.transient(self.canvas.winfo_toplevel())
        dialog.grab_set()
        self.canvas.wait_window(dialog)


# --- 具體元件 ---

class Pin(Component):
    def __init__(self, canvas, x, y):
        super().__init__(canvas, x, y, "PIN")
        self.shape_lines = [((-10, 0), (0, 0))]
        self.value = ""
        self.hitbox_size = (30, 30)
        self.setup_terminals()
        self.draw()

    def setup_terminals(self):
        self.terminals = [Terminal("pin", 0, 0)]

    def draw_text(self):
        self.canvas.create_text(self.x, self.y - 15, text=self.name, tags=self.tags, font=("Arial", 10, "bold"), fill="blue")

    def edit_properties(self):
        # Pin 依然只改名字
        self.open_property_dialog(["Net Name"], [self.name], self.apply_pin_props)

    def apply_pin_props(self, values):
        if values[0]: self.name = values[0]
        self.update_visuals()


class Resistor(Component):
    def __init__(self, canvas, x, y):
        super().__init__(canvas, x, y, "R")
        self.shape_lines = [
            ((-30, 0), (-20, 0)), ((-20, 0), (-15, -10)), ((-15, -10), (-5, 10)),
            ((-5, 10), (5, -10)), ((5, -10), (15, 10)), ((15, 10), (20, 0)), ((20, 0), (30, 0))
        ]
        self.hitbox_size = (70, 30)
        self.setup_terminals()
        self.draw() # 手動呼叫繪圖

    def setup_terminals(self):
        self.terminals = [Terminal("n1", -30, 0), Terminal("n2", 30, 0)]

class Inductor(Component):
    def __init__(self, canvas, x, y):
        super().__init__(canvas, x, y, "L")
        self.shape_lines = [
            ((-30, 0), (-20, 0)), ((20, 0), (30, 0)),
            ((-20, 0), (-20, -10)), ((-20, -10), (-10, -10)), ((-10, -10), (-10, 0)),
            ((-10, 0), (-10, -10)), ((-10, -10), (0, -10)), ((0, -10), (0, 0)),
            ((0, 0), (0, -10)), ((0, -10), (10, -10)), ((10, -10), (10, 0)),
            ((10, 0), (10, -10)), ((10, -10), (20, -10)), ((20, -10), (20, 0))
        ]
        self.hitbox_size = (70, 30)
        self.setup_terminals()
        self.draw()

    def setup_terminals(self):
        self.terminals = [Terminal("n1", -30, 0), Terminal("n2", 30, 0)]

class Capacitor(Component):
    def __init__(self, canvas, x, y):
        super().__init__(canvas, x, y, "C")
        self.shape_lines = [
            ((-30, 0), (-5, 0)), ((5, 0), (30, 0)),
            ((-5, -15), (-5, 15)), ((5, -15), (5, 15))
        ]
        self.hitbox_size = (70, 40)
        self.setup_terminals()
        self.draw()

    def setup_terminals(self):
        self.terminals = [Terminal("n1", -30, 0), Terminal("n2", 30, 0)]

class CMOS(Component):
    def __init__(self, canvas, x, y, p_type=False):
        self.p_type = p_type
        prefix = "M_P" if p_type else "M_N"
        super().__init__(canvas, x, y, prefix)
        self.model = "pch" if p_type else "nch"
        self.w = "1u"
        self.l = "0.18u"
        self.hitbox_size = (60, 60)
        
        self.shape_lines = [
            ((-10, -15), (-10, 15)), ((0, -15), (0, 15)),
            ((0, -10), (20, -10)), ((20, -10), (20, -25)),
            ((0, 10), (20, 10)), ((20, 10), (20, 25)),
            ((0, 0), (20, 0))
        ]
        if self.p_type:
            self.shape_lines.append(((-30, 0), (-16, 0)))
            self.shape_lines.extend([((-16, 0), (-13, -3)), ((-13, -3), (-10, 0)),
                                     ((-10, 0), (-13, 3)), ((-13, 3), (-16, 0))])
            self.shape_lines.extend([((10, 0), (15, -5)), ((10, 0), (15, 5))])
        else:
            self.shape_lines.append(((-30, 0), (-10, 0)))
            self.shape_lines.extend([((10, 0), (5, -5)), ((10, 0), (5, 5))])
        
        self.setup_terminals()
        self.draw()

    def setup_terminals(self):
        self.terminals = [
            Terminal("D", 20, -25), Terminal("G", -30, 0),
            Terminal("S", 20, 25), Terminal("B", 20, 0)
        ]

    def draw_text(self):
        info = f"{self.name}\n{self.model}\nW={self.w}\nL={self.l}"
        self.canvas.create_text(self.x, self.y + 40, text=info, tags=self.tags, font=("Arial", 7))

    def edit_properties(self):
        # CMOS 特製，加上端點命名
        labels = ["Name", "Model", "Width (W)", "Length (L)"]
        defaults = [self.name, self.model, self.w, self.l]
        
        for term in self.terminals:
            labels.append(f"Node ({term.name})")
            defaults.append(term.custom_net_name)

        self.open_property_dialog(labels, defaults, self.apply_cmos_props)

    def apply_cmos_props(self, values):
        if values[0]: self.name = values[0]
        if values[1]: self.model = values[1]
        if values[2]: self.w = values[2]
        if values[3]: self.l = values[3]
        
        for i, term in enumerate(self.terminals):
            if i + 4 < len(values):
                term.custom_net_name = values[i+4]
        
        self.update_visuals()