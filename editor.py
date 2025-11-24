import tkinter as tk
from tkinter import messagebox
from components import Resistor, Inductor, Capacitor, CMOS, Pin
from circuit_utils import snap, dist, is_point_on_segment

class Wire:
    def __init__(self, canvas, p1, p2):
        self.canvas = canvas
        self.start_p = p1
        self.end_p = p2
        self.id = id(self)
        self.tags = f"wire_{self.id}"
        self.canvas.create_line(p1[0], p1[1], p2[0], p2[1], fill="blue", width=2, tags=self.tags)
        # 隱形加粗線，方便點選
        self.canvas.create_line(p1[0], p1[1], p2[0], p2[1], width=10, tags=(self.tags, "wire_hitbox"), stipple="gray25", fill="") 

class CircuitEditor:
    def __init__(self, root):
        self.root = root
        self.mode = "SELECT"
        self.components = []
        self.wires = []
        self.selected_item = None
        self.temp_wire_start = None
        self.setup_ui()
        
    def setup_ui(self):
        toolbar = tk.Frame(self.root, bd=1, relief=tk.RAISED)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        # 建立按鈕
        # 注意：為了避免點擊按鈕後焦點卡在按鈕上導致快捷鍵失效，
        # 我們在 command 中加入 canvas.focus_set()
        btns = [("R", "R"), ("L", "L"), ("C", "C"), ("N", "NMOS"), ("P", "PMOS")]
        for text, cmd in btns:
            tk.Button(toolbar, text=text, width=3, 
                      command=lambda c=cmd: self.add_comp(c)).pack(side=tk.LEFT)
        
        tk.Button(toolbar, text="PIN", bg="#ffcccc", 
                  command=lambda: self.add_comp("PIN")).pack(side=tk.LEFT, padx=5)
        
        tk.Label(toolbar, text="|", fg="gray").pack(side=tk.LEFT, padx=5)
        self.mode_label = tk.Label(toolbar, text="Mode: SELECT", fg="blue", font=("Arial", 10, "bold"))
        self.mode_label.pack(side=tk.LEFT, padx=5)

        tk.Button(toolbar, text="Help(F1)", bg="lightblue", command=self.show_help).pack(side=tk.RIGHT)
        tk.Button(toolbar, text="Netlist", bg="yellow", command=self.export_netlist).pack(side=tk.RIGHT, padx=5)
        self.del_btn = tk.Button(toolbar, text="Del Mode", bg="#ffaaaa", command=self.toggle_delete_mode)
        self.del_btn.pack(side=tk.RIGHT, padx=5)

        self.canvas = tk.Canvas(self.root, bg="white", width=800, height=600)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # 讓 Canvas 可以接收鍵盤焦點
        self.canvas.focus_set()
        
        self.draw_grid()

        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Double-Button-1>", self.on_double_click)
        self.canvas.bind("<Motion>", self.on_mouse_move)

    def draw_grid(self):
        self.canvas.delete("grid")
        for i in range(0, 2000, 20):
            self.canvas.create_line(i, 0, i, 2000, fill="#f0f0f0", tags="grid")
            self.canvas.create_line(0, i, 2000, i, fill="#f0f0f0", tags="grid")
        self.canvas.tag_lower("grid") # 確保 Grid 永遠在最底層

    def set_mode(self, mode):
        self.mode = mode
        self.mode_label.config(text=f"Mode: {mode}")
        
        if mode == "DELETE":
            self.mode_label.config(fg="red")
            self.canvas.config(cursor="X_cursor")
        elif mode == "WIRE":
            self.mode_label.config(fg="green")
            self.canvas.config(cursor="crosshair")
        else:
            self.mode_label.config(fg="blue")
            self.canvas.config(cursor="")
            
        self.temp_wire_start = None
        self.canvas.delete("preview_wire")
        self.deselect_all()
        # 切換模式後，將焦點還給 Canvas，確保快捷鍵運作
        self.canvas.focus_set()

    def add_comp(self, c_type):
        self.set_mode("SELECT")
        x, y = 300, 300
        comp = None
        if c_type == "R": comp = Resistor(self.canvas, x, y)
        elif c_type == "L": comp = Inductor(self.canvas, x, y)
        elif c_type == "C": comp = Capacitor(self.canvas, x, y)
        elif c_type == "NMOS": comp = CMOS(self.canvas, x, y, False)
        elif c_type == "PMOS": comp = CMOS(self.canvas, x, y, True)
        elif c_type == "PIN": comp = Pin(self.canvas, x, y)
        
        if comp:
            self.components.append(comp)
        self.canvas.focus_set()

    def select_item(self, item, item_type):
        self.deselect_all()
        self.selected_item = (item, item_type)
        if item_type == "comp":
            self.canvas.itemconfig(item.tags, fill="blue") 
        elif item_type == "wire":
            self.canvas.itemconfig(item.tags, fill="red")

    def deselect_all(self):
        if self.selected_item:
            item, i_type = self.selected_item
            if i_type == "comp":
                item.update_visuals() 
            elif i_type == "wire":
                self.canvas.itemconfig(item.tags, fill="blue")
        self.selected_item = None

    def toggle_delete_mode(self):
        # 修正刪除模式切換邏輯
        if self.mode == "DELETE":
            self.set_mode("SELECT")
        else:
            self.set_mode("DELETE")

    def toggle_wire_mode(self):
        if self.mode == "WIRE":
            self.set_mode("SELECT")
        else:
            self.set_mode("WIRE")

    def delete_target(self, item, i_type):
        if i_type == "comp":
            self.canvas.delete(item.tags)
            if item in self.components: self.components.remove(item)
        elif i_type == "wire":
            self.canvas.delete(item.tags)
            if item in self.wires: self.wires.remove(item)
        self.selected_item = None

    def get_closest_terminal(self, x, y, threshold=15):
        closest_pt = None
        min_dist = float('inf')
        for comp in self.components:
            for term, tx, ty in comp.get_abs_terminals():
                d = dist((x, y), (tx, ty))
                if d < min_dist and d < threshold:
                    min_dist = d
                    closest_pt = (tx, ty)
        return closest_pt 

    def on_click(self, event):
        # 關鍵：點擊畫布時，強制取得焦點，解決 W 按不出來的問題
        self.canvas.focus_set()
        
        if self.mode == "DELETE":
            item_id = self.canvas.find_closest(event.x, event.y)
            tags = self.canvas.gettags(item_id)
            for comp in self.components:
                if comp.tags in tags:
                    self.delete_target(comp, "comp")
                    return
            for wire in self.wires:
                if wire.tags in tags:
                    self.delete_target(wire, "wire")
                    return
            return

        cx, cy = snap(event.x), snap(event.y)
        
        if self.mode == "WIRE":
            term_pt = self.get_closest_terminal(event.x, event.y)
            target_pt = term_pt if term_pt else (cx, cy)
            
            if not self.temp_wire_start:
                self.temp_wire_start = target_pt
            else:
                new_wire = Wire(self.canvas, self.temp_wire_start, target_pt)
                self.wires.append(new_wire)
                self.temp_wire_start = None 
                self.canvas.delete("preview_wire")

        elif self.mode == "SELECT":
            item_id = self.canvas.find_closest(event.x, event.y)
            tags = self.canvas.gettags(item_id)
            
            # Check components
            for comp in self.components:
                if comp.tags in tags:
                    self.select_item(comp, "comp")
                    self.drag_data = {"x": event.x, "y": event.y, "comp": comp}
                    return
            
            # Check wires
            for wire in self.wires:
                if wire.tags in tags:
                    self.select_item(wire, "wire")
                    return
            
            self.deselect_all()

    def on_mouse_move(self, event):
        if self.mode == "WIRE" and self.temp_wire_start:
            sx, sy = self.temp_wire_start
            term_pt = self.get_closest_terminal(event.x, event.y)
            ex, ey = term_pt if term_pt else (snap(event.x), snap(event.y))
            self.canvas.delete("preview_wire")
            self.canvas.create_line(sx, sy, ex, ey, fill="gray", dash=(4, 4), tags="preview_wire")

    def on_drag(self, event):
        if self.mode == "SELECT" and self.selected_item and self.selected_item[1] == "comp":
            dx = event.x - self.drag_data["x"]
            dy = event.y - self.drag_data["y"]
            comp = self.drag_data["comp"]
            self.canvas.move(comp.tags, dx, dy)
            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y

    # --- 智慧吸附 (Smart Snapping) 優化版 ---
    def on_release(self, event):
        if self.mode == "SELECT" and self.selected_item and self.selected_item[1] == "comp":
            comp = self.selected_item[0]
            
            # 1. 預設：吸附到網格
            bbox = self.canvas.bbox(comp.tags)
            if not bbox: return
            cur_cx = (bbox[0] + bbox[2]) / 2
            cur_cy = (bbox[1] + bbox[3]) / 2
            
            target_x = snap(cur_cx)
            target_y = snap(cur_cy)
            
            # 2. 智慧偵測：是否靠近其他元件的端點 (優先權高於網格)
            threshold = 20 # 增加吸附半徑，讓手感更好
            
            snap_candidates = [] 
            my_terms = comp.get_abs_terminals()
            
            # A. 檢查是否靠近其他端點
            for other in self.components:
                if other == comp: continue
                for o_term, ox, oy in other.get_abs_terminals():
                    for my_term, mx, my in my_terms:
                        d = dist((mx, my), (ox, oy))
                        if d < threshold:
                            # 計算位移向量
                            shift_x = ox - mx
                            shift_y = oy - my
                            snap_candidates.append((d, cur_cx + shift_x, cur_cy + shift_y))

            # B. 檢查是否靠近電線兩端 (可擴展至中點)
            for wire in self.wires:
                check_points = [wire.start_p, wire.end_p]
                for wx, wy in check_points:
                     for my_term, mx, my in my_terms:
                        d = dist((mx, my), (wx, wy))
                        if d < threshold:
                            shift_x = wx - mx
                            shift_y = wy - my
                            snap_candidates.append((d, cur_cx + shift_x, cur_cy + shift_y))

            # 決策：若有候選點，取最近的
            if snap_candidates:
                snap_candidates.sort(key=lambda x: x[0])
                target_x = snap_candidates[0][1]
                target_y = snap_candidates[0][2]
                
            # 更新座標
            comp.x = target_x
            comp.y = target_y
            comp.update_visuals()

    def on_double_click(self, event):
        if self.selected_item and self.selected_item[1] == "comp":
            self.selected_item[0].edit_properties()

    # --- 快捷鍵功能 ---
    def rotate_selection(self):
        if self.selected_item and self.selected_item[1] == "comp": 
            self.selected_item[0].rotate()
    
    def mirror_selection(self):
        if self.selected_item and self.selected_item[1] == "comp": 
            self.selected_item[0].flip()
            
    def show_help(self):
        messagebox.showinfo("Help", "Shortcuts:\nW: Wire Mode (Click to toggle)\nR/M: Rotate/Mirror Selection\nDel: Delete Mode\nN,P,R,L,C: Add Components")

    # --- 核心連通性分析 (Connectivity) ---
    def solve_connectivity(self):
        adj_list = {} 
        def add_edge(p1, p2):
            s1 = f"{p1[0]},{p1[1]}"
            s2 = f"{p2[0]},{p2[1]}"
            if s1 not in adj_list: adj_list[s1] = []
            if s2 not in adj_list: adj_list[s2] = []
            adj_list[s1].append(s2)
            adj_list[s2].append(s1)

        # 1. Wire 連接
        for wire in self.wires:
            add_edge(wire.start_p, wire.end_p)

        # 2. Pin 咬線 與 端點蒐集
        all_terminals = [] 
        for comp in self.components:
            for term, tx, ty in comp.get_abs_terminals():
                all_terminals.append((comp, term, tx, ty))
                # Pin logic
                if isinstance(comp, Pin):
                    for wire in self.wires:
                        if is_point_on_segment(tx, ty, wire.start_p[0], wire.start_p[1], wire.end_p[0], wire.end_p[1]):
                            add_edge((tx, ty), wire.start_p)

        # 3. [重要優化] 端點直連判定
        # 將判定距離拉大到 15 (跟 Snap Threshold 一樣)，確保吸附過去的都能算短路
        connection_tolerance = 15.0 
        for i in range(len(all_terminals)):
            for j in range(i + 1, len(all_terminals)):
                t1 = all_terminals[i]
                t2 = all_terminals[j]
                # 若距離極近，視為同一個點
                if dist((t1[2], t1[3]), (t2[2], t2[3])) < connection_tolerance:
                    add_edge((t1[2], t1[3]), (t2[2], t2[3]))

        # 4. BFS 與 命名優先權 (Pin > Custom > Default)
        visited = set()
        node_map = {} 
        net_counter = 1
        
        for comp, term, tx, ty in all_terminals:
            pt_key = f"{tx},{ty}"
            if pt_key not in visited:
                group_pts = []
                queue = [pt_key]
                visited.add(pt_key)
                group_pts.append(pt_key)
                
                while queue:
                    curr = queue.pop(0)
                    if curr in adj_list:
                        for neighbor in adj_list[curr]:
                            if neighbor not in visited:
                                visited.add(neighbor)
                                group_pts.append(neighbor)
                                queue.append(neighbor)
                
                # 命名仲裁
                final_name = None
                pin_names = []
                custom_names = []
                
                for c, t, ctx, cty in all_terminals:
                    c_key = f"{ctx},{cty}"
                    if c_key in group_pts:
                        if isinstance(c, Pin):
                            pin_names.append(c.name)
                        elif t.custom_net_name.strip() != "":
                            custom_names.append(t.custom_net_name)

                if pin_names:
                    final_name = pin_names[0]
                elif custom_names:
                    final_name = custom_names[0]
                else:
                    final_name = f"N_{net_counter}"
                    net_counter += 1
                
                for pt in group_pts:
                    node_map[pt] = final_name
        
        return node_map

    def export_netlist(self):
        node_map = self.solve_connectivity()
        lines = ["* Generated by Python Circuit CAD", ".OPTIONS POST"]
        
        for comp in self.components:
            if isinstance(comp, Pin): continue 
            
            abs_terms = comp.get_abs_terminals()
            node_names = []
            for term, tx, ty in abs_terms:
                key = f"{tx},{ty}"
                if key in node_map:
                    node_names.append(node_map[key])
                else:
                    node_names.append(f"NC_{comp.name}_{term.name}")
            
            if isinstance(comp, CMOS):
                line = f"{comp.name} {' '.join(node_names)} {comp.model} W={comp.w} L={comp.l}"
            else:
                line = f"{comp.name} {' '.join(node_names)} {comp.value}"
            lines.append(line)
            
        lines.append(".END")
        
        win = tk.Toplevel(self.root)
        t = tk.Text(win, width=60, height=20)
        t.pack()
        t.insert(tk.END, "\n".join(lines))